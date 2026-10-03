"""The picture model driven directly with diffusers, loaded from Forge/Comfy-style single files.

No web UI and no node graph: three model files in, PIL images out, nothing written to disk. Which model it is,
and which diffusers and transformers classes it needs, are chosen in models.local.json (mindstream/local.py).

Settings follow Forge/Comfy conventions so known-good recipes carry over:
  cfg       1 means no guidance; above 1 uses the negative prompt (costs two model passes per step)
  shift     the flow shift (3 is the picture model's default; higher spends more steps on composition)
  scheduler "beta" or "simple", computed the way Comfy computes them
The sampler is Euler.
"""
import os
import time

import numpy as np
import torch

from .local import code, pick

# the Forge install whose model folders hold the files (MINDSTREAM_FORGE still works)
FORGE = pick("forge_dir", env="MINDSTREAM_FORGE")


def _in(folder, name):
    """A chosen file: a bare name is looked for in Forge's folder for that kind of model."""
    return name if not name or os.path.isabs(name) or not FORGE else os.path.join(FORGE, "models", folder, name)


# Which files are used is this machine's business: see models.local.json (mindstream/local.py).
DEFAULT_MODEL = _in("Stable-diffusion", pick("image_model"))
DEFAULT_VAE = _in("VAE", pick("image_vae"))
DEFAULT_TE = _in("text_encoder", pick("image_te"))       # a full-precision or scaled fp8 encoder file
# configs and tokenizer for the architecture (small JSON/vocab files that Forge ships; no weights); a relative
# path is taken inside the Forge folder
_CONFIG = pick("image_config_dir")
DEFAULT_CONFIG = _CONFIG if not _CONFIG or os.path.isabs(_CONFIG) or not FORGE else os.path.join(FORGE, _CONFIG)
# what each setting is called in models.local.json, for the message when one is missing
CHOSEN_AS = {"model": "image_model", "vae": "image_vae", "text encoder": "image_te", "config": "image_config_dir"}

# the AMD text-encoder helper runs in its own environment (ONNX Runtime + DirectML)
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DML_PYTHON = os.environ.get("MINDSTREAM_DML_PYTHON", os.path.join(PROJECT, ".venv-dml", "Scripts", "python.exe"))
TE_AMD_SCRIPT = os.path.join(PROJECT, "te_amd.py")

# Comfy's latent -> RGB approximation for the picture model's 16-channel autoencoder, used for cheap step previews
LATENT_RGB = [[-0.0346, 0.0244, 0.0681], [0.0034, 0.0210, 0.0687], [0.0275, -0.0668, -0.0433],
              [-0.0174, 0.0160, 0.0617], [0.0859, 0.0721, 0.0329], [0.0004, 0.0383, 0.0115],
              [0.0405, 0.0861, 0.0915], [-0.0236, -0.0185, -0.0259], [-0.0245, 0.0250, 0.1180],
              [0.1008, 0.0755, -0.0421], [-0.0515, 0.0201, 0.0011], [0.0428, -0.0012, -0.0036],
              [0.0817, 0.0765, 0.0749], [-0.1264, -0.0522, -0.1103], [-0.0280, -0.0881, -0.0499],
              [-0.1262, -0.0982, -0.0778]]
LATENT_RGB_BIAS = [-0.0329, -0.0718, -0.0851]


def flow_sigma_table(shift):
    """Comfy's ModelSamplingDiscreteFlow table: sigma for t = 1/1000 .. 1."""
    t = np.arange(1, 1001) / 1000.0
    return shift * t / (1 + (shift - 1) * t)


def sigmas_for(scheduler, steps, shift):
    """Sigma schedule as Comfy computes it (without the trailing 0, which the sampler appends)."""
    table = flow_sigma_table(shift)
    if scheduler == "beta":
        from scipy.stats import beta
        ts = np.rint(beta.ppf(1 - np.linspace(0, 1, steps, endpoint=False), 0.6, 0.6) * (len(table) - 1))
        out, last = [], -1
        for t in ts:
            if t != last:
                out.append(float(table[int(t)]))
            last = t
        return out
    if scheduler == "simple":
        ss = len(table) / steps
        return [float(table[-(1 + int(x * ss))]) for x in range(steps)]
    raise ValueError(f"unknown scheduler {scheduler!r} (use beta or simple)")


def load_text_encoder(path, config_dir):
    """The text encoder from a single .safetensors file, plain or Comfy 'scaled fp8'."""
    from accelerate import init_empty_weights
    from safetensors import safe_open
    config_class = code("image_te_config_class", "text encoder config class")
    model_class = code("image_te_model_class", "text encoder model class")

    sd = {}
    with safe_open(path, "pt") as f:
        keys = set(f.keys())
        for k in keys:
            if k == "scaled_fp8" or k.endswith((".scale_weight", ".scale_input")):
                continue
            t = f.get_tensor(k)
            if t.dtype == torch.float8_e4m3fn:
                t = t.to(torch.float32)
                scale_key = k[: -len("weight")] + "scale_weight"
                if scale_key in keys:  # stored value is weight / scale
                    t = t * f.get_tensor(scale_key).to(torch.float32)
            sd[k.removeprefix("model.")] = t.to(torch.bfloat16)
    with init_empty_weights():
        model = model_class(config_class.from_pretrained(os.path.join(config_dir, "text_encoder")))
    missing, unexpected = model.load_state_dict(sd, assign=True, strict=False)
    if missing:
        raise RuntimeError(f"text encoder file is missing {len(missing)} tensors, e.g. {missing[:3]}")
    if unexpected:
        raise RuntimeError(f"text encoder file has {len(unexpected)} unknown tensors, e.g. {unexpected[:3]}")
    return model.eval()


def load_transformer(path, config_dir):
    """The diffusion model from a single fp8 .safetensors file, straight onto the GPU.

    The weights stay fp8 from disk to card (about 6 GB) and are cast to bf16 one layer at a time
    while computing. This avoids ever holding a 12 GB bf16 copy in RAM."""
    from accelerate import init_empty_weights
    from safetensors.torch import load_file
    transformer_class = code("image_transformer_class", "diffusion model class")
    convert = code("image_checkpoint_converter", "single-file checkpoint converter")

    fp8, bf16 = torch.float8_e4m3fn, torch.bfloat16
    sd = convert(load_file(path))
    with init_empty_weights():
        model = transformer_class.from_config(transformer_class.load_config(config_dir, subfolder="transformer"))
    missing, unexpected = model.load_state_dict(sd, assign=True, strict=False)
    del sd
    if missing or unexpected:
        raise RuntimeError(f"model file does not match the chosen model class: {len(missing)} missing, "
                           f"{len(unexpected)} unknown tensors, "
                           f"e.g. {(missing + unexpected)[:3]}")
    model.to("cuda")
    if any(p.dtype == fp8 for p in model.parameters()):
        model.enable_layerwise_casting(storage_dtype=fp8, compute_dtype=bf16)
        # layers the casting hooks skip (norms, embedders, single tensors) are small: hold them in bf16
        hooked = set()
        for module in model.modules():
            registry = getattr(module, "_diffusers_hook", None)
            if registry is not None and registry.get_hook("layerwise_casting") is not None:
                hooked.add(id(module))
        for module in model.modules():
            if id(module) in hooked:
                continue
            for name, p in module._parameters.items():
                if p is not None and p.dtype == fp8:
                    p.data = p.data.to(bf16)
    else:
        model.to(bf16)
    return model.eval()


class ResourceError(RuntimeError):
    """Not enough free RAM or VRAM to load safely."""


# What loading needs, measured on the 12 GB card with the fp8 model:
NEED_RAM_GB = 12.0    # the 8 GB text encoder lives in RAM; the rest is transient while files are read
NEED_VRAM_GB = 9.0    # 6.3 GB of weights resident + ~2 GB working memory at 1024x1024


def deadline(seconds, what, log=None):
    """Time cap: if `what` is still running after `seconds`, end the whole process.

    A model that has overflowed VRAM on Windows does not fail, it crawls; a time cap is the
    reliable way to stop that from eating the machine. Returns a function that cancels the cap."""
    import threading

    def expire():
        try:
            (log or print)(f"time cap hit: {what} exceeded {seconds:.0f}s - stopping")
        finally:
            os._exit(3)

    timer = threading.Timer(seconds, expire)
    timer.daemon = True
    timer.start()
    return timer.cancel


class Painter:
    """Layout chosen for an eGPU, where moving models across the link costs seconds:
    the diffusion model and vae stay on the GPU; the text encoder stays on the CPU (bf16).
    Per image, only the prompt embeddings cross the link."""

    def __init__(self, model=DEFAULT_MODEL, vae=DEFAULT_VAE, te=DEFAULT_TE, config_dir=DEFAULT_CONFIG, log=None,
                 te_device="auto", vram_room_gb=3.2):
        """te_device: "cpu" runs the text encoder in this process on the CPU (bf16);
        "amd" runs it on the AMD GPU through the te_amd helper (needs a one-off te-export of the encoder);
        "auto" uses the AMD GPU when that conversion exists."""
        import psutil
        from diffusers import AutoencoderKL, FlowMatchEulerDiscreteScheduler
        from transformers import AutoTokenizer

        log = log or (lambda msg: None)
        for label, path in (("model", model), ("vae", vae), ("text encoder", te), ("config", config_dir)):
            if not path:
                raise FileNotFoundError(f"no {label} chosen: set \"{CHOSEN_AS[label]}\" in models.local.json "
                                        f"(see models.example.json), or pass it on the command line")
            if not os.path.exists(path):
                raise FileNotFoundError(f"{label} not found: {path}")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")  # everything is local; never phone home
        # the model's own classes, named in models.local.json: looked up now, so a missing name stops this
        # before minutes of loading rather than after
        pipeline_class = code("image_pipeline", "picture pipeline class")
        for key, what in (("image_transformer_class", "diffusion model class"),
                          ("image_checkpoint_converter", "single-file checkpoint converter"),
                          ("image_te_config_class", "text encoder config class"),
                          ("image_te_model_class", "text encoder model class")):
            code(key, what)

        # What to do with the GPU's working memory between stages: "keep" it, release it "after" each
        # image, or release it "before" the decode. Measured on this eGPU; see the note in generate().
        self.cache_policy = "keep"
        self.helper = None
        onnx_dir =os.path.splitext(te)[0] + "_onnx_fp16"
        converted = os.path.exists(os.path.join(onnx_dir, "te.onnx")) and os.path.exists(DML_PYTHON)
        if te_device == "amd" and not converted:
            raise FileNotFoundError(f"no AMD conversion of this encoder at {onnx_dir}; run: te-export \"{te}\"")
        use_amd = te_device == "amd" or (te_device == "auto" and converted)

        # refuse to start rather than push the machine into swapping or shared-memory fallback
        ram = psutil.virtual_memory().available / 1e9
        free, total = (x / 1e9 for x in torch.cuda.mem_get_info())
        if ram < NEED_RAM_GB:
            raise ResourceError(f"only {ram:.1f} GB RAM available; loading needs about {NEED_RAM_GB:.0f} GB")
        if free < NEED_VRAM_GB:
            raise ResourceError(f"only {free:.1f} GB VRAM free; this model needs about {NEED_VRAM_GB:.0f} GB")
        log(f"{ram:.1f} GB RAM available, {free:.1f} GB VRAM free of {total:.1f} GB")

        if use_amd:   # started first: it loads on the other GPU while the diffusion model loads on this one
            import atexit
            import subprocess
            self.helper = subprocess.Popen([DML_PYTHON, "-B", "-W", "ignore", TE_AMD_SCRIPT, "serve", onnx_dir,
                                            "--config", config_dir], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            atexit.register(self.close)

        t = time.time()
        transformer = load_transformer(model, config_dir)
        log(f"diffusion model on GPU in {time.time() - t:.1f}s")

        t = time.time()
        autoencoder = AutoencoderKL.from_single_file(vae, config=config_dir, subfolder="vae", torch_dtype=torch.bfloat16)
        autoencoder.enable_tiling()   # decode in tiles: avoids a multi-GB VRAM spike at the end of each image
        autoencoder.to("cuda")
        log(f"vae on GPU in {time.time() - t:.1f}s")

        t = time.time()
        if self.helper is not None:
            import json
            log("waiting for the text encoder to finish loading on the AMD GPU")
            ready = self.helper.stdout.readline()
            if not ready:
                raise RuntimeError("the AMD text-encoder helper failed to start (see its messages above)")
            info = json.loads(ready)
            log(f"text encoder on {info['adapter']} (loaded in {info['load_s']}s)")
        else:   # loaded last, so its 8 GB never overlaps the diffusion model's loading peak
            self.text_encoder = load_text_encoder(te, config_dir)
            self.tokenizer = AutoTokenizer.from_pretrained(os.path.join(config_dir, "tokenizer"))
            log(f"text encoder on CPU in {time.time() - t:.1f}s")

        # shift is baked into the sigmas we pass, so the scheduler itself applies none
        scheduler = FlowMatchEulerDiscreteScheduler(num_train_timesteps=1000, shift=1.0, use_dynamic_shifting=False)
        self.pipe = pipeline_class(scheduler=scheduler, vae=autoencoder, text_encoder=None,
                                   tokenizer=None, transformer=transformer)
        self.pipe.set_progress_bar_config(disable=True)
        self._weights = torch.cuda.memory_allocated()                   # resident model weights
        self._vram_total = torch.cuda.mem_get_info()[1]
        self._vram_max = self._weights + torch.cuda.mem_get_info()[0] - 0.4e9   # everything that is free right now
        self.vram_room_gb = vram_room_gb                                # working memory allowed per megapixel
        self._rgb = torch.tensor(LATENT_RGB)
        self._rgb_bias = torch.tensor(LATENT_RGB_BIAS)

    def close(self):
        if self.helper is not None and self.helper.poll() is None:
            try:
                self.helper.stdin.close()   # end of input: the helper exits and frees the AMD GPU's memory
                self.helper.wait(timeout=10)
            except Exception:
                self.helper.kill()
        self.helper = None

    @torch.inference_mode()
    def encode(self, text):
        """Prompt -> embeddings, off the NVIDIA card, so it can run while that GPU is busy with an image."""
        if self.helper is not None:
            import json
            self.helper.stdin.write((json.dumps({"text": text}) + "\n").encode("utf-8"))
            self.helper.stdin.flush()
            header = self.helper.stdout.readline()
            if not header:
                raise RuntimeError("the AMD text-encoder helper stopped")
            head = json.loads(header)
            data = bytearray(self.helper.stdout.read(head["tokens"] * head["dim"] * 2))
            hidden = torch.frombuffer(data, dtype=torch.float16).reshape(head["tokens"], head["dim"])
            return hidden.to("cuda", torch.bfloat16)
        chat = self.tokenizer.apply_chat_template([{"role": "user", "content": text}], tokenize=False,
                                                  add_generation_prompt=True, enable_thinking=True)
        tokens = self.tokenizer(chat, truncation=True, max_length=512, return_tensors="pt")
        hidden = self.text_encoder(**tokens, output_hidden_states=True).hidden_states[-2][0]
        return hidden.to("cuda", torch.bfloat16)

    def preview(self, latents):
        """Rough RGB picture of the current latents (1/8 size), as a PIL image."""
        from PIL import Image
        x = latents[0].detach().float().cpu()                       # [16, h, w]
        rgb = torch.einsum("chw,cr->rhw", x, self._rgb) + self._rgb_bias[:, None, None]
        rgb = ((rgb + 1) / 2).clamp(0, 1).mul(255).byte().permute(1, 2, 0).numpy()
        return Image.fromarray(rgb)

    @torch.inference_mode()
    def generate(self, prompt, negative="", steps=9, cfg=1.0, shift=3.0, scheduler="beta",
                 width=1024, height=1024, seed=None, on_step=None, on_stage=None):
        """Returns (PIL image, seed). on_step(step_index, total_steps, preview_image) is called after each step;
        on_stage(name) is called as each stage starts: "encode", "denoise", "decode"."""
        self._on_stage = on_stage or (lambda name: None)
        sigmas = sigmas_for(scheduler, steps, shift)
        if seed is None:
            seed = int.from_bytes(os.urandom(4), "little")
        callback = None
        if on_step is not None:
            def callback(pipe, i, t, kwargs):
                on_step(i + 1, len(sigmas), self.preview(kwargs["latents"]))
                return {}
        self.timing = timing = {}   # seconds per stage of the most recent image
        t = time.time()
        self._on_stage("encode")
        embeds = prompt if torch.is_tensor(prompt) else self.encode(prompt)
        negative_embeds = None
        if cfg > 1:
            negative_embeds = [negative if torch.is_tensor(negative) else self.encode(negative or "")]
        timing["encode"] = time.time() - t
        import gc
        # Working-memory ceiling. Measured on this eGPU (five images per policy, fresh process each):
        #   release after each image    decode 5-17 s every time (every fresh GPU allocation is slow)
        #   keep, no ceiling            decode 0.3 s, but the pool grows until the card is full
        #   keep, under a ceiling       decode 0.4 s, and over 1 GB of the card stays free
        # So memory is kept and reused, under a ceiling sized to the image. If an image does not fit,
        # the ceiling is lifted and it is retried once.
        room = self.vram_room_gb * max(1.0, width * height / (1024 * 1024)) if self.vram_room_gb else None
        self._set_ceiling(room)
        try:
            try:
                return self._run(embeds, negative_embeds, cfg, sigmas, width, height, seed, callback, timing), seed
            except torch.OutOfMemoryError:
                if room is None:
                    raise
                gc.collect()
                torch.cuda.empty_cache()
                self._set_ceiling(None)
                return self._run(embeds, negative_embeds, cfg, sigmas, width, height, seed, callback, timing), seed
        except torch.OutOfMemoryError:
            gc.collect()
            torch.cuda.empty_cache()
            raise ResourceError(f"out of VRAM at {width}x{height}; try a smaller size or free the GPU") from None
        finally:
            if self.cache_policy == "after":
                gc.collect()
                torch.cuda.empty_cache()

    def _set_ceiling(self, room_gb):
        limit = self._vram_max if room_gb is None else min(self._weights + room_gb * 1e9, self._vram_max)
        torch.cuda.set_per_process_memory_fraction(min(limit / self._vram_total, 1.0))

    def _run(self, embeds, negative_embeds, cfg, sigmas, width, height, seed, callback, timing):
        t = time.time()
        self._on_stage("denoise")
        latents = self._denoise(embeds, negative_embeds, cfg, sigmas, width, height, seed, callback)
        torch.cuda.synchronize()
        timing["denoise"] = time.time() - t
        if self.cache_policy == "before":
            import gc
            gc.collect()
            torch.cuda.empty_cache()
        t = time.time()
        self._on_stage("decode")
        vae = self.pipe.vae
        latents = latents.to(vae.dtype) / vae.config.scaling_factor + vae.config.shift_factor
        image = vae.decode(latents, return_dict=False)[0]
        torch.cuda.synchronize()
        timing["decode"] = time.time() - t
        t = time.time()
        image = self.pipe.image_processor.postprocess(image.float(), output_type="pil")[0]
        timing["to_image"] = time.time() - t
        return image

    def _denoise(self, embeds, negative_embeds, cfg, sigmas, width, height, seed, callback):
        return self.pipe(
            output_type="latent",
            prompt_embeds=[embeds],
            negative_prompt_embeds=negative_embeds,
            guidance_scale=max(cfg - 1.0, 0.0),   # diffusers adds g*(pos-neg) to pos; Comfy's cfg is g+1
            cfg_normalization=False,
            num_inference_steps=len(sigmas),
            sigmas=sigmas,
            width=width, height=height,
            generator=torch.Generator("cpu").manual_seed(seed),
            callback_on_step_end=callback,
        ).images   # latents, with the batch dimension kept for the vae
