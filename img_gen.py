"""img-gen: prompts in on stdin, images out on stdout. Nothing is written to disk.

Input   one prompt per line. A line that is a JSON object can override settings for that image:
        {"prompt": "...", "negative": "...", "seed": 7, "steps": 9, "cfg": 1, "shift": 6, "width": 768, "height": 1344}
Output  one JSON object per line (text-safe, so it survives any shell pipe):
        {"type": "image", "seq": 1, "final": true, "step": 9, "steps": 9, "mime": "image/png", "w": 1024, "h": 1024, "data": "<base64>"}
        With --previews, a small rough picture is also sent after every step ("final": false).
Status  goes to stderr.

Usual use:  img-gen --view --previews      (opens the viewer; type prompts, nothing is saved)

Windows PowerShell does not stream between two programs: `img-gen | img-view` there delivers
every frame in one lump when img-gen exits. Use --view, or run the pipe through cmd.exe.
"""
import argparse
import base64
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


QUIET = False   # set by --quiet: progress goes to the viewer's flow strip instead of the terminal


def say(msg, always=False):
    if always or not QUIET:
        print(f"[img-gen] {msg}", file=sys.stderr, flush=True)


OUT = None   # where frames go: the viewer's stdin with --view, else our stdout


def emit(image, seq, final, step, steps, fmt, quality):
    buf = io.BytesIO()
    if fmt == "png":
        image.save(buf, "PNG", compress_level=1)
    else:
        image.convert("RGB").save(buf, fmt.upper(), quality=quality)
    frame = {"type": "image", "seq": seq, "final": final, "step": step, "steps": steps,
             "mime": f"image/{fmt}", "w": image.width, "h": image.height,
             "data": base64.b64encode(buf.getvalue()).decode("ascii")}
    OUT.write((json.dumps(frame) + "\n").encode("ascii"))
    OUT.flush()


def read_requests(one_prompt):
    if one_prompt:
        yield one_prompt
        return
    typed = sys.stdin.isatty()
    if typed:
        say("type a prompt and press Enter (Ctrl+Z then Enter to finish). Typed prompts are not saved in shell history.")
    while True:
        if typed:
            print("prompt> ", end="", file=sys.stderr, flush=True)
        raw = sys.stdin.buffer.readline()
        if not raw:
            return
        try:
            line = raw.decode("utf-8-sig").strip()
        except UnicodeDecodeError:
            line = raw.decode(sys.stdin.encoding or "utf-8", errors="replace").strip()
        if line:
            yield line


def main():
    from mindstream import painter

    ap = argparse.ArgumentParser(description="Picture prompts -> image stream (stdin to stdout, nothing saved)")
    ap.add_argument("--model", default=painter.DEFAULT_MODEL, help="diffusion model .safetensors")
    ap.add_argument("--vae", default=painter.DEFAULT_VAE, help="vae .safetensors")
    ap.add_argument("--te", default=painter.DEFAULT_TE, help="text encoder .safetensors (plain or scaled fp8)")
    ap.epilog = "Defaults for --model, --vae, --te and --config come from models.local.json."
    ap.add_argument("--te-device", choices=["auto", "amd", "cpu"], default="auto",
                    help="where the text encoder runs: the AMD GPU (needs a one-off te-export), or the CPU; "
                         "auto uses the AMD GPU when the conversion exists")
    ap.add_argument("--config", default=painter.DEFAULT_CONFIG, help="folder with the architecture's config and tokenizer files")
    ap.add_argument("--steps", type=int, default=9)
    ap.add_argument("--cfg", type=float, default=1.0, help="1 = no guidance; above 1 uses the negative prompt (twice the time)")
    ap.add_argument("--shift", type=float, default=3.0)
    ap.add_argument("--scheduler", choices=["beta", "simple"], default="beta")
    ap.add_argument("--negative", default="", help="negative prompt, used when cfg > 1")
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--seed", type=int, help="fixed seed for every image (default: a new random seed each time)")
    ap.add_argument("--previews", action="store_true", help="also stream a rough picture after each step")
    ap.add_argument("--format", choices=["png", "jpeg", "webp"], default="png", help="encoding of finished images")
    ap.add_argument("--quality", type=int, default=92, help="jpeg/webp quality")
    ap.add_argument("--prompt", help="generate this one prompt and exit (note: your shell may record it in its history)")
    ap.add_argument("--max-seconds", type=float, default=120, help="time cap per image; the process stops if exceeded")
    ap.add_argument("--load-max-seconds", type=float, default=240, help="time cap for loading the models")
    ap.add_argument("--vram-room", type=float, default=3.2,
                    help="GB of GPU working memory allowed per megapixel on top of the model (0 = no ceiling)")
    ap.add_argument("--verbose", action="store_true", help="print per-image timings to stderr")
    ap.add_argument("--quiet", action="store_true", help="no progress messages on the terminal (errors still shown)")
    ap.add_argument("--view", action="store_true",
                    help="open the viewer and send frames straight to it (no shell pipe needed)")
    ap.add_argument("--view-args", default="", help='options for the viewer, e.g. --view-args "--fullscreen --hold 6"')
    # "--view-args --fullscreen": glue the value on with "=", or argparse mistakes it for another option
    argv, raw = [], sys.argv[1:]
    while raw:
        a = raw.pop(0)
        argv.append(f"{a}={raw.pop(0)}" if a == "--view-args" and raw else a)
    args = ap.parse_args(argv)
    global OUT, QUIET
    QUIET = args.quiet
    viewer = None
    if args.view:
        import shlex
        import subprocess
        viewer = subprocess.Popen([sys.executable, "-B", os.path.join(os.path.dirname(os.path.abspath(__file__)), "img_view.py"),
                                   *shlex.split(args.view_args)], stdin=subprocess.PIPE)
        OUT = viewer.stdin
    elif sys.stdout.isatty():
        sys.exit("img-gen writes an image stream to stdout: add --view to open the viewer, or pipe it into another program")
    else:
        OUT = sys.stdout.buffer

    def status(source, kind, text, seq=0, detail=""):
        """Tell whoever is watching what this stage is doing right now (drawn by the viewer)."""
        try:
            OUT.write((json.dumps({"type": "status", "source": source, "kind": kind, "seq": seq,
                                   "text": text, "detail": detail}) + "\n").encode("ascii", "replace"))
            OUT.flush()
        except (OSError, ValueError):
            pass

    def loading(msg):
        say(msg)
        if msg.startswith("waiting for the text encoder"):
            status("encoder", "load", "loading on the AMD GPU")
        elif "text encoder" in msg:
            status("encoder", "idle", "ready", detail=msg.replace("text encoder on ", ""))
        else:
            status("image", "load", "loading", detail=msg)

    cancel = painter.deadline(args.load_max_seconds, "loading the models", say)
    t = time.time()
    status("image", "load", "loading the diffusion model")
    status("encoder", "load", "loading the text encoder")
    try:
        engine = painter.Painter(args.model, args.vae, args.te, args.config, log=loading, te_device=args.te_device,
                         vram_room_gb=args.vram_room or None)
    except (painter.ResourceError, FileNotFoundError, RuntimeError) as e:
        status("image", "error", "cannot start", detail=str(e)[:140])
        if viewer is not None:
            viewer.stdin.close()
        sys.exit(f"[img-gen] cannot start: {e}")
    cancel()
    say(f"ready in {time.time() - t:.0f}s")
    status("image", "idle", "ready, waiting for a prompt")

    defaults = {"negative": args.negative, "steps": args.steps, "cfg": args.cfg, "shift": args.shift,
                "width": args.width, "height": args.height, "seed": args.seed}
    seq = 0
    for line in read_requests(args.prompt):
        req = dict(defaults)
        if line.startswith("{"):
            try:
                req.update({k: v for k, v in json.loads(line).items() if k in defaults or k == "prompt"})
            except ValueError:
                req["prompt"] = line
        else:
            req["prompt"] = line
        if not req.get("prompt"):
            continue
        seq += 1
        def on_step(i, n, picture, seq=seq):
            status("image", "render", f"rendering image {seq}", seq, detail=f"step {i} of {n}")
            if args.previews and i < n:
                emit(picture, seq, False, i, n, "jpeg", 80)

        def on_stage(stage, seq=seq):
            if stage == "encode":
                status("encoder", "encode", f"encoding prompt {seq}", seq)
            elif stage == "denoise":
                status("encoder", "idle", "ready")
                status("image", "render", f"rendering image {seq}", seq)
            elif stage == "decode":
                status("image", "decode", f"decoding image {seq}", seq)

        cancel = painter.deadline(args.max_seconds, f"image {seq}", say)
        try:
            image, seed = engine.generate(req["prompt"], negative=req["negative"], steps=int(req["steps"]),
                                          cfg=float(req["cfg"]), shift=float(req["shift"]), scheduler=args.scheduler,
                                          width=int(req["width"]), height=int(req["height"]), seed=req["seed"],
                                          on_step=on_step, on_stage=on_stage)
        except painter.ResourceError as e:
            cancel()
            say(f"image {seq} skipped: {e}", always=True)
            status("image", "error", f"image {seq} skipped", seq, detail=str(e)[:140])
            continue
        cancel()
        status("image", "idle", "waiting for the next prompt")
        try:
            emit(image, seq, True, int(req["steps"]), int(req["steps"]), args.format, args.quality)
        except (BrokenPipeError, OSError):
            break   # the viewer went away
        if args.verbose:
            tm = engine.timing
            say(f"image {seq}: encode {tm['encode']:.1f}s, denoise {tm['denoise']:.1f}s, decode {tm['decode']:.1f}s, seed {seed}")
    status("image", "stop", "finished: no more prompts")
    status("encoder", "stop", "finished")
    engine.close()
    if viewer is not None:
        try:
            viewer.stdin.close()   # end of stream: the viewer holds the last image until it is closed
        except OSError:
            pass
        viewer.wait()


if __name__ == "__main__":
    main()
