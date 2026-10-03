"""Stand-in stages for `mindstream --demo`: the same streams as the real ones, made of test cards and
beeps. No llama, no image model, no video model. For trying the visuals and testing the launcher.

  fake_stage.py feed [--beats N] [--interval S] [--video] [--video-seconds S]
  fake_stage.py gen                      prompts on stdin -> test-card images
  fake_stage.py vid [--seconds S]        one journey request on stdin -> a test clip with a click track
"""
import argparse
import base64
import io
import json
import math
import struct
import sys
import time


def out(obj):
    sys.stdout.buffer.write((json.dumps(obj) + "\n").encode("ascii", "replace"))
    sys.stdout.buffer.flush()


def status(source, kind, text, seq=0, detail=""):
    out({"type": "status", "source": source, "kind": kind, "seq": seq, "text": text, "detail": detail})


def card(label, size, hue, variant=0):
    from PIL import Image, ImageDraw
    w, h = size
    img = Image.new("RGB", size, tuple(c // 5 for c in hue))
    d = ImageDraw.Draw(img)
    for y in range(0, h, 8):
        d.line([(0, y), (w, y)], fill=tuple(int(c * (0.25 + 0.6 * y / h)) for c in hue), width=6)
    for r in range(40, int(min(w, h) * 0.48), 46):
        d.ellipse([w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r], outline=(255, 235, 200), width=5)
    for k in range(12):
        a = k * math.pi / 6 + variant * 0.2
        d.line([(w / 2, h / 2), (w / 2 + math.cos(a) * w, h / 2 + math.sin(a) * w)], fill=(20, 20, 30), width=4)
    d.rectangle([w * 0.08, h * 0.72, w * 0.92, h * 0.9], fill=(15, 15, 20))
    d.text((w * 0.11, h * 0.76), label, fill=(255, 255, 255), font_size=int(h * 0.075))
    return img


def b64(img, fmt="PNG", **kw):
    buf = io.BytesIO()
    img.save(buf, fmt, **kw)
    return base64.b64encode(buf.getvalue()).decode("ascii")


HUES = [(200, 70, 50), (50, 120, 200), (70, 170, 90), (190, 150, 40), (150, 70, 190)]


def tell(stream, text):
    out({"type": "read", "stream": stream, "text": text})


def feed(args):
    status("llama", "idle", "demo: no llama involved")
    time.sleep(0.5)
    prev = ""
    seq = 0
    while args.beats == 0 or seq < args.beats:
        seq += 1
        started = time.time()
        status("llama", "beat", f"writing beat {seq}", seq, detail="about 60 words")
        time.sleep(0.8)
        beat = f"Demo beat {seq}: a stand-in sentence where a paragraph of story would be, long enough to wrap across the window."
        out({"type": "story", "seq": seq, "text": beat})
        bpm = [96, 128, 150, 70][seq % 4]
        out({"type": "visual", "seq": seq, "chaos": [0.6, 1.2, 1.7, 0.4][seq % 4], "bpm": bpm, "folds": [0, 5, 9, 3][seq % 4],
             "shape": ["sphere", "torus", "ribbon", "any"][seq % 4], "swarm": 0.8, "trails": 0.7,
             "style": ["four", "twostep", "broken", "half"][seq % 4], "key": ["A minor", "F# dorian", "E phrygian", "C major"][seq % 4],
             "twinkle": [0.2, 0.8, 0.4, 1.0][seq % 4], "rescore": True})
        tell("score", f"Beat {seq}: " + ["The room empties, so the beat drags and the key lifts.", "She runs, so the drums start to skip and the bells come in.",
                                        "The glass goes, so the beat breaks up and the key darkens.", "He sleeps, so it all slows and softens."][seq % 4]
             + " So: the drums switch to " + ["a steady four-on-the-floor kick", "a skipping 2-step", "a syncopated broken beat", "a slow, heavy half-time"][seq % 4]
             + f"; the tempo goes to {bpm}.")
        if seq % 3 == 0:                                       # a stand-in for something typed at steer>
            tell("steer", f'You said "give me a break then bring it back". Now: the drums and bass drop out for 4 bars, build, then slam '
                          f"back in. Beat {seq + 1} of the story takes it in next, then picture {seq + 1}.")
            out({"type": "visual", "seq": 0, "break": 4})
        status("llama", "prompt", f"writing image prompt {seq}", seq, detail="about 150 words")
        time.sleep(0.6)
        out({"type": "prompt", "target": "image", "seq": seq, "prompt": f"TEST CARD {seq}"})
        tell("picture", f"Picture {seq} is being painted for beat {seq}: a stand-in test card where the image prompt's first words would be...")
        if args.video and prev:
            status("llama", "prompt", f"writing journey {seq - 1} to {seq}", seq)
            time.sleep(0.5)
            out({"type": "prompt", "target": "video", "seq": seq, "from": seq - 1, "to": seq,
                 "prompt": f"demo journey {seq - 1} to {seq}", "bpm": bpm, "seconds": args.video_seconds})
            tell("film", f'The film from picture {seq - 1} to {seq} is written. A stand-in for its opening sentence. Heard in it: "a line of speech". '
                         f"Its music is asked for at {bpm} BPM; it is filmed when both pictures exist.")
        prev = beat
        status("llama", "idle", "pausing before the next beat")
        time.sleep(max(args.interval - (time.time() - started), 0))
    status("llama", "stop", "story ended - llama cleared")


def gen(args):
    status("image", "load", "loading the diffusion model")
    status("encoder", "load", "loading the text encoder")
    time.sleep(1.5)
    status("encoder", "idle", "ready", detail="demo")
    status("image", "idle", "ready, waiting for a prompt")
    seq = 0
    for raw in sys.stdin.buffer:
        try:
            prompt = json.loads(raw)["prompt"]
        except (ValueError, KeyError):
            continue
        seq += 1
        digits = "".join(c for c in prompt if c.isdigit()) or "0"
        hue = HUES[int(digits[:3]) % len(HUES)]
        img = card(prompt[:22], (1024, 1024), hue, variant=seq)
        status("encoder", "encode", f"encoding prompt {seq}", seq)
        time.sleep(0.2)
        status("encoder", "idle", "ready")
        for step in range(1, 10):
            status("image", "render", f"rendering image {seq}", seq, detail=f"step {step} of 9")
            if step < 9:
                small = img.resize((128, 128)).point(lambda v, s=step: int(v * s / 9))
                out({"type": "image", "seq": seq, "final": False, "step": step, "steps": 9, "mime": "image/jpeg",
                     "w": 128, "h": 128, "data": b64(small, "JPEG", quality=70)})
            time.sleep(0.2)
        status("image", "decode", f"decoding image {seq}", seq)
        out({"type": "image", "seq": seq, "final": True, "step": 9, "steps": 9, "mime": "image/png",
             "w": 1024, "h": 1024, "data": b64(img)})
        status("image", "idle", "waiting for the next prompt")
    status("image", "stop", "finished: no more prompts")
    status("encoder", "stop", "finished")


def vid(args):
    from PIL import Image
    status("video", "load", "loading the video model")
    time.sleep(1.5)
    status("video", "idle", "ready, waiting for a journey")
    for n, raw in enumerate(sys.stdin.buffer, 1):
        try:
            req = json.loads(raw)
        except ValueError:
            continue
        seconds = float(req.get("seconds", args.seconds))
        bpm = float(req.get("bpm", 120))
        first = Image.open(io.BytesIO(base64.b64decode(req["first"]))).convert("RGB").resize((640, 640))
        last = Image.open(io.BytesIO(base64.b64decode(req["last"]))).convert("RGB").resize((640, 640)) if req.get("last") else first
        count = max(5, round(seconds * 24))
        frames = []
        for i in range(count):
            if i % 12 == 0:
                status("video", "render", f"filming journey {n}", n, detail=f"frame {i} of {count}")
                time.sleep(0.15)
            frames.append(b64(Image.blend(first, last, i / max(count - 1, 1)), "JPEG", quality=80))
        rate = 22050
        samples = bytearray()
        for i in range(int(seconds * rate)):                # a click on every beat over a low drone
            t = i / rate
            beat_phase = (t * bpm / 60) % 1.0
            click = math.sin(2 * math.pi * 880 * t) * max(0.0, 1 - beat_phase * 12) * 0.5
            drone = math.sin(2 * math.pi * 110 * t) * 0.15
            v = int(max(-1, min(1, click + drone)) * 30000)
            samples += struct.pack("<hh", v, v)
        status("video", "decode", f"developing journey {n}", n)
        out({"type": "clip", "seq": n, "fps": 24, "w": 640, "h": 640, "frames": frames,
             "audio": {"rate": rate, "channels": 2, "data": base64.b64encode(bytes(samples)).decode("ascii")}})
        status("video", "idle", "waiting for the next journey")
    status("video", "stop", "finished")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["feed", "gen", "vid"])
    ap.add_argument("--beats", type=int, default=0)
    ap.add_argument("--interval", type=float, default=6.0)
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--video-seconds", type=float, default=3.0)
    ap.add_argument("--seconds", type=float, default=3.0)
    args, _ = ap.parse_known_args()
    try:
        {"feed": feed, "gen": gen, "vid": vid}[args.stage](args)
    except (BrokenPipeError, OSError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
