"""vid-gen: a journey between two pictures, as video with sound (the film model). Nothing is written to disk.

Licence: this file loads ComfyUI as a library, and ComfyUI is under the GNU General Public License. So this file,
unlike the rest of the repository, is licensed under the GNU General Public License, version 3 or (at your option)
any later version: see LICENSES/GPL-3.0.txt. Copyright (c) 2026 sens8tion. It is run as a program of its own and
speaks to the rest only in lines of JSON over a pipe.

The film model's quantised files only load through ComfyUI's code, so this script uses ComfyUI as a
library: no server, no browser, no node graph, no output folder. It runs in ComfyUI's Python
environment and needs the whole machine: the image generator must not be loaded at the same time.
Where ComfyUI is, and which of its node modules, node class and text-encoder type the film model uses,
are chosen in models.local.json (mindstream/local.py).

Input   one JSON object per line on stdin:
        {"prompt": "...", "first": "<base64 image>", "last": "<base64 image, optional>",
         "seconds": 5, "seed": 7}
        "first" is where the journey starts and "last" where it arrives; with neither it is text-to-video.
Output  one JSON object per line on stdout:
        {"type": "status", "source": "video", ...}                          progress, for the flow strip
        {"type": "clip", "seq": 1, "fps": 24, "w": 832, "h": 480,
         "frames": ["<base64 jpeg>", ...],
         "audio": {"rate": 44100, "channels": 2, "data": "<base64 16-bit PCM>"}}
Status  also goes to stderr unless --quiet.

Expect about a minute of work per second of video on a 12 GB card.

NOT YET RUN: written from ComfyUI's node code and the working reference-to-video workflow; it has
never loaded the model. Treat the first run as a test.
"""
import argparse
import base64
import io
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mindstream.local import need, pick  # noqa: E402

COMFY = pick("comfy_dir", env="MINDSTREAM_COMFY")     # the ComfyUI folder (MINDSTREAM_COMFY still works)
QUIET = False


def say(msg, always=False):
    if always or not QUIET:
        print(f"[vid-gen] {msg}", file=sys.stderr, flush=True)


def emit(obj):
    sys.stdout.buffer.write((json.dumps(obj) + "\n").encode("ascii", "replace"))
    sys.stdout.buffer.flush()


def status(kind, text, seq=0, detail=""):
    emit({"type": "status", "source": "video", "kind": kind, "seq": seq, "text": text, "detail": detail})


def deadline(seconds, what):
    """Time cap: end the process if `what` is still running after `seconds`. Returns a cancel function."""
    def expire():
        try:
            say(f"time cap hit: {what} exceeded {seconds:.0f}s - stopping", always=True)
            status("error", f"{what} took too long", detail=f"over {seconds:.0f} s")
        finally:
            os._exit(3)
    timer = threading.Timer(seconds, expire)
    timer.daemon = True
    timer.start()
    return timer.cancel


def canvas_for(width, height, megapixels):
    """A size with the picture's proportions and about `megapixels` of area, both sides multiples of 32."""
    scale = (megapixels * 1e6 / (width * height)) ** 0.5
    return max(32, round(width * scale / 32) * 32), max(32, round(height * scale / 32) * 32)


def main():
    ap = argparse.ArgumentParser(description="Film-model journeys between pictures -> video+audio stream (nothing saved)")
    ap.add_argument("--model", default=pick("video_model"), help="diffusion model, in ComfyUI's diffusion_models folder")
    ap.add_argument("--lora", default=pick("video_lora"), help="turbo LoRA ('' for none)")
    ap.add_argument("--te", default=pick("video_te"), help="text encoder, in ComfyUI's text_encoders folder")
    ap.add_argument("--vae", default=pick("video_vae"))
    ap.add_argument("--audio-vae", default=pick("video_audio_vae"))
    ap.add_argument("--steps", type=int, default=0, help="sampling steps (default: 8 with the turbo LoRA, 20 without)")
    ap.add_argument("--sampler", default="res_multistep")
    ap.add_argument("--scheduler", default="simple")
    ap.add_argument("--seconds", type=float, default=5.0, help="length of each clip (the model snaps it to its own grid)")
    ap.add_argument("--megapixels", type=float, default=0.4, help="frame area; 0.4 is about 832x480")
    ap.add_argument("--jpeg-quality", type=int, default=88)
    ap.add_argument("--reserve-vram", type=float, default=0.4, help="GB of VRAM left for the desktop")
    ap.add_argument("--max-seconds-per-second", type=float, default=150, help="time cap: seconds of work allowed per second of video")
    ap.add_argument("--load-max-seconds", type=float, default=600)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="verify the model files and ComfyUI code are in place, without loading any model")
    args = ap.parse_args()
    global QUIET
    QUIET = args.quiet
    steps = args.steps or (8 if args.lora else 20)

    # ---- ComfyUI as a library ------------------------------------------------------------------
    # every choice is checked before anything is imported, so a missing one is a plain message
    need("comfy_dir", "ComfyUI folder", env="MINDSTREAM_COMFY")
    nodes_module_name = need("video_nodes_module", "ComfyUI node module for the film model")
    node_class_name = need("video_node_class", "ComfyUI node class for the film model")
    clip_type = need("video_clip_type", "text encoder type for ComfyUI's CLIPLoader")
    for key, value in (("video_model", args.model), ("video_te", args.te), ("video_vae", args.vae),
                       ("video_audio_vae", args.audio_vae)):
        if not value:
            sys.exit(f'[vid-gen] no {key.replace("_", " ")} chosen: set "{key}" in models.local.json '
                     f'(see models.example.json), or pass it on the command line')
    if not os.path.isdir(COMFY):
        sys.exit(f"[vid-gen] ComfyUI not found at {COMFY}")
    os.chdir(COMFY)
    sys.path.insert(0, COMFY)
    sys.argv = ["comfy", "--reserve-vram", str(args.reserve_vram), "--disable-smart-memory", "--disable-metadata"]
    # (--check imports ComfyUI's code but loads no weights. It cannot hide the GPU: ComfyUI's
    # attention code refuses to import without one, so the check opens a small GPU context.)
    cancel = deadline(args.load_max_seconds, "loading the video model")
    if not args.check:
        status("load", "loading the video model")
    t0 = time.time()
    # The same start-up steps as ComfyUI's own main.py, in the same order. Skipping them works but is
    # ruinously slow: without its dynamic VRAM management ("aimdo") the 15.7 GB text encoder is handled
    # by the legacy loader, and a prompt that should take seconds took over ten minutes.
    import comfy.options
    comfy.options.enable_args_parsing()
    from comfy.cli_args import args as comfy_args, enables_dynamic_vram
    import cuda_malloc  # noqa: F401  sets the GPU allocator; has to happen before torch is imported
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
    import comfy_aimdo.control
    if enables_dynamic_vram():
        headroom = None if comfy_args.reserve_vram is None else int(comfy_args.reserve_vram * 1024 ** 3)
        try:
            comfy_aimdo.control.init(simple_vram_headroom=headroom, nvml_pressure=not comfy_args.disable_nvml_pressure)
        except TypeError:
            try:
                comfy_aimdo.control.init(simple_vram_headroom=headroom)
            except TypeError:
                comfy_aimdo.control.init()
    os.environ["MIMALLOC_PURGE_DELAY"] = "0"
    import comfy.utils
    import folder_paths
    import nodes
    import comfy.memory_management
    import comfy.model_management
    import comfy.model_patcher
    dynamic = False
    if enables_dynamic_vram() and comfy.model_management.is_nvidia() and comfy.model_management.torch_version_numeric >= (2, 8):
        devices = comfy.model_management.get_all_torch_devices()
        try:
            dynamic = comfy_aimdo.control.init_devices((d.index, int(comfy_args.vram_headroom * 1024 ** 3)) for d in devices)
        except TypeError:
            dynamic = comfy_aimdo.control.init_devices(d.index for d in devices)
        if dynamic:
            comfy_aimdo.control.set_log_warning()
            comfy.model_patcher.CoreModelPatcher = comfy.model_patcher.ModelPatcherDynamic
            comfy.memory_management.aimdo_enabled = True
    say("dynamic VRAM management: " + ("on" if dynamic else "OFF - expect it to be very slow"), always=not dynamic)
    import numpy as np
    import torch
    from PIL import Image
    import importlib
    from comfy_extras import nodes_audio, nodes_custom_sampler
    try:
        film_node = getattr(importlib.import_module(nodes_module_name), node_class_name)
    except (ImportError, AttributeError) as e:
        sys.exit(f'[vid-gen] the film model\'s node ("video_nodes_module" {nodes_module_name}, '
                 f'"video_node_class" {node_class_name}) is not in this ComfyUI: {e}')

    if args.check:
        cancel()
        problems = []
        for folder, name in (("diffusion_models", args.model), ("loras", args.lora), ("text_encoders", args.te),
                             ("vae", args.vae), ("vae", args.audio_vae)):
            if name:
                path = folder_paths.get_full_path(folder, name)
                print(f"  {folder:17s} {name}: " + (f"{os.path.getsize(path) / 1e9:.1f} GB" if path else "NOT FOUND"))
                problems += [] if path else [name]
        for cls in (film_node, nodes_custom_sampler.BasicScheduler, nodes_custom_sampler.KSamplerSelect,
                    nodes_custom_sampler.BasicGuider, nodes_custom_sampler.RandomNoise, nodes_custom_sampler.SamplerCustomAdvanced,
                    nodes_audio.VAEDecodeAudio):
            if not hasattr(cls, "execute"):
                problems.append(cls.__name__)
        import comfy.samplers
        for label, value, known in (("sampler", args.sampler, comfy.samplers.SAMPLER_NAMES), ("scheduler", args.scheduler, comfy.samplers.SCHEDULER_NAMES)):
            print(f"  {label} {value}: " + ("known" if value in known else "UNKNOWN"))
            problems += [] if value in known else [value]
        print(f"  dynamic VRAM management: {'on' if dynamic else 'OFF (video would be very slow)'}")
        problems += [] if dynamic else ["dynamic VRAM management"]
        print(f"  ComfyUI code imported in {time.time() - t0:.0f}s, no model loaded; {steps} steps per clip")
        print("check passed" if not problems else f"check FAILED: {problems}")
        sys.exit(0 if not problems else 1)

    def picture(b64):
        """base64 image -> ComfyUI image tensor [1, H, W, 3] in 0..1, and its (width, height)"""
        img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
        return torch.from_numpy(np.asarray(img).astype(np.float32) / 255.0)[None], img.size

    with torch.inference_mode():
        model = nodes.UNETLoader().load_unet(args.model, "default")[0]
        if args.lora:
            model = nodes.LoraLoaderModelOnly().load_lora_model_only(model, args.lora, 1.0)[0]
        clip = nodes.CLIPLoader().load_clip(args.te, type=clip_type, device="default")[0]
        vae = nodes.VAELoader().load_vae(args.vae)[0]
        audio_vae = nodes.VAELoader().load_vae(args.audio_vae)[0]
    cancel()
    say(f"models referenced in {time.time() - t0:.0f}s (weights load on first use); {steps} steps per clip")
    status("idle", "ready, waiting for a journey")

    seq = 0
    for raw in sys.stdin.buffer:
        try:
            req = json.loads(raw)
            prompt = req["prompt"]
        except (ValueError, KeyError):
            continue
        seq += 1
        seconds = float(req.get("seconds", args.seconds))
        length = max(5, round(seconds * 24))
        # the first clip also pays for reading 37 GB of model files from disk
        cancel = deadline(max(seconds, 1.0) * args.max_seconds_per_second + (900 if seq == 1 else 300), f"clip {seq}")
        t0 = time.time()
        try:
            with torch.inference_mode():
                first = last = None
                size = (1344, 768)
                if req.get("first"):
                    first, size = picture(req["first"])
                if req.get("last"):
                    last, last_size = picture(req["last"])
                    size = size if req.get("first") else last_size
                width, height = canvas_for(size[0], size[1], args.megapixels)
                status("encode", f"reading the journey {seq}", seq)
                positive, latent = film_node.execute(
                    clip, vae, prompt, width, height, length, first_frame=first, last_frame=last).result

                def progress(value, total, preview=None, **kwargs):   # called by ComfyUI after every sampling step
                    status("render", f"filming journey {seq}", seq, detail=f"step {value} of {total}")
                comfy.utils.set_progress_bar_global_hook(progress)
                status("render", f"filming journey {seq}", seq)
                sigmas = nodes_custom_sampler.BasicScheduler.execute(model, args.scheduler, steps, 1.0).result[0]
                sampler = nodes_custom_sampler.KSamplerSelect.execute(args.sampler).result[0]
                guider = nodes_custom_sampler.BasicGuider.execute(model, positive).result[0]
                seed = int(req.get("seed") or int.from_bytes(os.urandom(6), "little"))
                noise = nodes_custom_sampler.RandomNoise.execute(seed).result[0]
                sampled = nodes_custom_sampler.SamplerCustomAdvanced.execute(noise, guider, sampler, sigmas, latent).result[0]

                status("decode", f"developing journey {seq}", seq)
                images = nodes.VAEDecode().decode(vae, sampled)[0]                     # [frames, H, W, 3] in 0..1
                audio = nodes_audio.VAEDecodeAudio.execute(audio_vae, sampled).result[0]

            frames = []
            for frame in (images.clamp(0, 1) * 255).round().to(torch.uint8).cpu().numpy():
                buf = io.BytesIO()
                Image.fromarray(frame).save(buf, "JPEG", quality=args.jpeg_quality)
                frames.append(base64.b64encode(buf.getvalue()).decode("ascii"))
            wave = audio["waveform"][0].float().clamp(-1, 1).cpu()                     # [channels, samples]
            pcm = (wave.t().contiguous() * 32767.0).round().to(torch.int16).numpy().tobytes()
            emit({"type": "clip", "seq": seq, "fps": 24, "w": int(images.shape[2]), "h": int(images.shape[1]),
                  "frames": frames,
                  "audio": {"rate": int(audio["sample_rate"]), "channels": int(wave.shape[0]),
                            "data": base64.b64encode(pcm).decode("ascii")}})
            took = time.time() - t0
            say(f"clip {seq}: {len(frames)} frames ({len(frames) / 24:.1f}s) in {took:.0f}s, "
                f"{took / max(len(frames) / 24, 0.1):.0f}s per second of video, seed {seed}")
            status("idle", "waiting for the next journey")
        except torch.OutOfMemoryError:
            say(f"clip {seq} skipped: out of GPU memory", always=True)
            status("error", f"journey {seq} skipped", seq, detail="out of GPU memory")
        except (BrokenPipeError, OSError):
            break
        finally:
            cancel()
    status("stop", "finished")


if __name__ == "__main__":
    main()
