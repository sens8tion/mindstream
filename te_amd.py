"""te-amd: the picture model's text encoder on the AMD integrated GPU, via ONNX Runtime + DirectML.

Runs in its own environment (.venv-dml), separate from the image generator's. The encoder's config and model
classes, and the folder of its config files, are chosen in models.local.json (mindstream/local.py).

  te_amd.py export <encoder.safetensors> [--out DIR]
        One-off conversion to a folder of ONNX files (fp16), kept beside the encoder with the other models.
        About two and a half minutes and a 14 GB RAM peak. Needed once per encoder file.

  te_amd.py serve <onnx-folder>
        Loads the converted encoder on the AMD GPU and answers requests on stdin/stdout:
          in   one JSON line: {"text": "..."}
          out  one JSON line: {"tokens": n, "dim": 2560, "dtype": "float16"} followed by n*dim*2 raw bytes
        img-gen starts this itself (--te-device amd); it is not meant to be run by hand.

Nothing but the one-off converted model is ever written to disk.
"""
import argparse
import ctypes
import json
import os
import sys
import threading
import time

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ.setdefault("HF_HUB_OFFLINE", "1")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mindstream.local import code, pick  # noqa: E402

# the same config folder the picture generator uses (mindstream/painter.py): a relative path is inside Forge's folder
FORGE = pick("forge_dir", env="MINDSTREAM_FORGE")
DEFAULT_CONFIG = pick("image_config_dir")
if DEFAULT_CONFIG and FORGE and not os.path.isabs(DEFAULT_CONFIG):
    DEFAULT_CONFIG = os.path.join(FORGE, DEFAULT_CONFIG)
BUCKET = 32                              # prompt lengths are padded up to a multiple of this
WARM_LENGTHS = (64, 96, 128, 160, 192, 224, 256, 288, 320)   # lengths prepared at start-up (prompts of 80-200 words)


def say(msg):
    print(f"[te-amd] {msg}", file=sys.stderr, flush=True)


def deadline(seconds, what):
    """Time cap: end the process if `what` is still running after `seconds`. Returns a cancel function."""
    def expire():
        try:
            say(f"time cap hit: {what} exceeded {seconds:.0f}s - stopping")
        finally:
            os._exit(3)
    timer = threading.Timer(seconds, expire)
    timer.daemon = True
    timer.start()
    return timer.cancel


def onnx_folder_for(te_path):
    return os.path.splitext(te_path)[0] + "_onnx_fp16"


def find_adapter(want=("radeon", "amd")):
    """Index and name of the AMD adapter in DXGI order, which is the order DirectML's device_id uses."""
    from ctypes import POINTER, Structure, byref, c_long, c_size_t, c_uint, c_void_p, c_wchar, HRESULT
    from ctypes.wintypes import DWORD

    class GUID(Structure):
        _fields_ = [("a", DWORD), ("b", ctypes.c_ushort), ("c", ctypes.c_ushort), ("d", ctypes.c_ubyte * 8)]

    class LUID(Structure):
        _fields_ = [("LowPart", DWORD), ("HighPart", c_long)]

    class DESC1(Structure):
        _fields_ = [("Description", c_wchar * 128), ("VendorId", c_uint), ("DeviceId", c_uint), ("SubSysId", c_uint),
                    ("Revision", c_uint), ("DedicatedVideoMemory", c_size_t), ("DedicatedSystemMemory", c_size_t),
                    ("SharedSystemMemory", c_size_t), ("AdapterLuid", LUID), ("Flags", c_uint)]

    def method(obj, index, *argtypes):
        vtbl = ctypes.cast(ctypes.cast(obj, POINTER(c_void_p))[0], POINTER(c_void_p))
        return ctypes.WINFUNCTYPE(HRESULT, c_void_p, *argtypes)(vtbl[index])

    iid = GUID()
    ctypes.oledll.ole32.CLSIDFromString(ctypes.c_wchar_p("{770aae78-f26f-4dba-a829-253c83d1b387}"), byref(iid))
    factory = c_void_p()
    ctypes.oledll.dxgi.CreateDXGIFactory1(byref(iid), byref(factory))
    names, i = [], 0
    while True:
        adapter = c_void_p()
        try:
            method(factory, 12, c_uint, POINTER(c_void_p))(factory, i, byref(adapter))   # EnumAdapters1
        except OSError:
            break
        d = DESC1()
        method(adapter, 10, POINTER(DESC1))(adapter, byref(d))                            # GetDesc1
        names.append(d.Description)
        i += 1
    for index, name in enumerate(names):
        if any(w in name.lower() for w in want) and "nvidia" not in name.lower():
            return index, name
    raise RuntimeError(f"no AMD adapter found among: {names}")


# ---------------------------------------------------------------------------------------------- export

def export(te_path, out, config_dir):
    import psutil
    import torch
    from accelerate import init_empty_weights
    from safetensors import safe_open
    config_class = code("image_te_config_class", "text encoder config class")
    model_class = code("image_te_model_class", "text encoder model class")

    if os.path.exists(os.path.join(out, "te.onnx")):
        sys.exit(f"[te-amd] already converted: {out}")
    free = psutil.virtual_memory().available / 1e9
    if free < 15:
        sys.exit(f"[te-amd] only {free:.1f} GB RAM available; the conversion peaks at about 14 GB. Close something and retry.")
    cancel = deadline(600, "conversion")
    t0 = time.time()
    say(f"reading {os.path.basename(te_path)}")
    sd = {}
    with safe_open(te_path, "pt") as f:
        keys = set(f.keys())
        for k in sorted(keys):
            if k == "scaled_fp8" or k.endswith((".scale_weight", ".scale_input")):
                continue
            t = f.get_tensor(k)
            if t.dtype == torch.float8_e4m3fn:     # Comfy "scaled fp8": the stored value is weight / scale
                t = t.to(torch.float32)
                scale_key = k[: -len("weight")] + "scale_weight"
                if scale_key in keys:
                    t = t * f.get_tensor(scale_key).to(torch.float32)
            sd[k.removeprefix("model.")] = t.to(torch.float16)
    config = config_class.from_pretrained(os.path.join(config_dir, "text_encoder"))
    with init_empty_weights():
        model = model_class(config)
    missing, unexpected = model.load_state_dict(sd, assign=True, strict=False)
    if missing or unexpected:
        sys.exit(f"[te-amd] this file does not match the chosen text encoder:{len(missing)} missing, {len(unexpected)} unknown tensors")
    del sd
    model.eval()

    class Wrap(torch.nn.Module):
        def __init__(self, model):
            super().__init__()
            self.model = model

        def forward(self, input_ids):
            # explicit causal mask (prompts are unpadded): transformers' own mask builder does not export
            n = input_ids.shape[1]
            dtype = self.model.embed_tokens.weight.dtype
            mask = torch.triu(torch.full((n, n), torch.finfo(dtype).min, dtype=dtype), diagonal=1)[None, None]
            return self.model(input_ids=input_ids, attention_mask={"full_attention": mask},
                              output_hidden_states=True, use_cache=False).hidden_states[-2][0]

    # this torch's exporter cannot translate scaled_dot_product_attention with a scale argument
    model.config._attn_implementation = "eager"
    # the `onnx` package is not installed; this exporter step only merges onnxscript functions (none here)
    from torch.onnx._internal import onnx_proto_utils
    onnx_proto_utils._add_onnxscript_fn = lambda proto, custom_opsets: proto

    os.makedirs(out, exist_ok=True)
    say(f"converting to {out} (a couple of minutes)")
    try:
        with torch.no_grad():
            torch.onnx.export(Wrap(model), (torch.randint(0, config.vocab_size, (1, 24)),), os.path.join(out, "te.onnx"),
                              input_names=["input_ids"], output_names=["hidden"],
                              dynamic_axes={"input_ids": {1: "seq"}, "hidden": {0: "seq"}},
                              opset_version=17, do_constant_folding=False)
    except BaseException:
        for name in os.listdir(out):          # do not leave half a model behind
            os.remove(os.path.join(out, name))
        os.rmdir(out)
        raise
    cancel()
    files = os.listdir(out)
    size = sum(os.path.getsize(os.path.join(out, f)) for f in files) / 1e9
    say(f"done in {time.time() - t0:.0f}s: {len(files)} files, {size:.2f} GB")


# ----------------------------------------------------------------------------------------------- serve

def serve(folder, config_dir, adapter):
    import numpy as np
    import onnxruntime as ort
    from transformers import AutoTokenizer

    out = sys.stdout.buffer
    if not os.path.exists(os.path.join(folder, "te.onnx")):
        sys.exit(f"[te-amd] no converted encoder at {folder}; run: te-export <encoder.safetensors>")
    index, name = (adapter, f"adapter {adapter}") if adapter is not None else find_adapter()
    cancel = deadline(240, "loading the encoder on the AMD GPU")
    t = time.time()
    tokenizer = AutoTokenizer.from_pretrained(os.path.join(config_dir, "tokenizer"))
    options = ort.SessionOptions()
    options.enable_mem_pattern = False
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.log_severity_level = 3
    session = ort.InferenceSession(os.path.join(folder, "te.onnx"), options,
                                   providers=[("DmlExecutionProvider", {"device_id": index})])
    if "DmlExecutionProvider" not in session.get_providers():
        sys.exit("[te-amd] DirectML is not available in this environment")
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
    for length in WARM_LENGTHS:   # pay the per-length set-up cost now, not on the first prompts
        session.run(None, {"input_ids": np.full((1, length), pad_id, dtype=np.int64)})
    cancel()
    out.write((json.dumps({"ready": True, "adapter": name, "load_s": round(time.time() - t, 1)}) + "\n").encode())
    out.flush()

    for raw in sys.stdin.buffer:
        try:
            text = json.loads(raw)["text"]
        except (ValueError, KeyError):
            continue
        chat = tokenizer.apply_chat_template([{"role": "user", "content": text}], tokenize=False,
                                             add_generation_prompt=True, enable_thinking=True)
        ids = tokenizer(chat, truncation=True, max_length=512, return_tensors="np")["input_ids"].astype(np.int64)
        # DirectML pays a multi-second set-up cost for every new input length. Pad up to a multiple of
        # 32 so lengths repeat. The model reads left to right, so padding on the right cannot change the
        # values for the real tokens, and the padded positions are cut off again below.
        n = ids.shape[1]
        padded = np.full((1, -(-n // BUCKET) * BUCKET), pad_id, dtype=np.int64)
        padded[0, :n] = ids[0]
        cancel = deadline(60, "one prompt")
        hidden = np.ascontiguousarray(session.run(None, {"input_ids": padded})[0][:n], dtype=np.float16)
        cancel()
        out.write((json.dumps({"tokens": hidden.shape[0], "dim": hidden.shape[1], "dtype": "float16"}) + "\n").encode())
        out.write(hidden.tobytes())
        out.flush()


def main():
    ap = argparse.ArgumentParser(description="The picture model's text encoder on the AMD GPU (ONNX Runtime + DirectML)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export", help="one-off conversion of an encoder .safetensors to ONNX fp16")
    e.add_argument("encoder")
    e.add_argument("--out", help="output folder (default: beside the encoder, <name>_onnx_fp16)")
    s = sub.add_parser("serve", help="answer encode requests on stdin/stdout (started by img-gen)")
    s.add_argument("folder")
    s.add_argument("--adapter", type=int, help="DirectML adapter index (default: find the AMD one by name)")
    for p in (e, s):
        p.add_argument("--config", default=DEFAULT_CONFIG, help="folder with the architecture's config and tokenizer files")
    args = ap.parse_args()
    if not args.config:
        sys.exit('[te-amd] no config folder chosen: set "image_config_dir" in models.local.json '
                 '(see models.example.json), or pass --config')
    if args.cmd == "export":
        export(os.path.abspath(args.encoder), args.out or onnx_folder_for(os.path.abspath(args.encoder)), args.config)
    else:
        serve(args.folder, args.config, args.adapter)


if __name__ == "__main__":
    main()
