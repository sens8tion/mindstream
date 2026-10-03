"""img-view: shows a mindstream from stdin in a window. Nothing is written to disk.

Reads one JSON object per line:
  image frames   a finished image fades in and then holds; while the next one is being made, its step
                 previews are blended over the held image with increasing strength, so the new picture
                 grows out of the old one instead of flashing up as noise
  text frames    shown as a caption under the picture
  status frames  what each resource is doing (llama writing, the text encoder, the image GPU); drawn as a
                 strip of lanes along the bottom: the current activity with a running clock, and bars
                 flowing right to left showing who was busy with what over the last few minutes

Keys: F fullscreen, M show/hide the flow strip, Esc or Q quit.
"""
import argparse
import base64
import io
import json
import queue
import sys
import threading
import time
import tkinter as tk

from PIL import Image, ImageTk

EOF = object()
LANES = (("llama", "llama"), ("encoder", "text enc"), ("image", "image gpu"), ("video", "video gpu"))
COLOURS = {"load": "#55556a", "beat": "#3b6ea5", "prompt": "#2f8f83", "encode": "#c08a2b",
           "render": "#4f9a4f", "decode": "#9acd32", "error": "#b03030", "stop": "#444444"}
LANE_H = 20


def reader(frames, texts, statuses):
    for raw in sys.stdin.buffer:
        try:
            frame = json.loads(raw)
            kind = frame.get("type")
            if kind == "text":
                texts.put(str(frame.get("text", "")))
            elif kind == "status":
                statuses.put((frame.get("source", "?"), frame.get("kind", "idle"), frame.get("seq", 0),
                              str(frame.get("text", "")), str(frame.get("detail", ""))))
            elif kind == "image":
                image = Image.open(io.BytesIO(base64.b64decode(frame["data"]))).convert("RGB")
                frames.put((image, bool(frame.get("final", True)), frame.get("seq", 0),
                            frame.get("step", 1), frame.get("steps", 1)))
        except (ValueError, KeyError, OSError):
            continue   # not a frame we understand: skip it
    frames.put(EOF)


def next_item(frames):
    """Newest step preview, unless a finished image (or the end) is waiting: those are never skipped."""
    item = None
    while True:
        try:
            got = frames.get_nowait()
        except queue.Empty:
            return item
        if got is EOF or got[1]:
            return got
        item = got


class Viewer:
    def __init__(self, args):
        self.args = args
        self.frames, self.texts, self.statuses = queue.Queue(), queue.Queue(), queue.Queue()
        self.shown = None        # what is on screen now (window-sized)
        self.base = None         # the last finished image (window-sized)
        self.base_source = None  # the same image at its original resolution, for window resizes
        self.fade = None         # (from, to, index, length, is_final)
        self.hold_until = 0.0
        self.ended = False
        self.count = 0
        # per resource: its activity segments [start, end or None, kind, seq] and what it is doing now
        self.lanes = {key: {"segments": [], "text": "", "detail": "", "since": time.time(), "kind": "idle"}
                      for key, _ in LANES}

        self.root = tk.Tk()
        self.root.title("mindstream")
        self.root.configure(bg="black")
        self.root.geometry(f"{args.size}x{args.size}")
        self.flow = tk.Canvas(self.root, bg="#0b0b0d", height=len(LANES) * LANE_H + 6, highlightthickness=0)
        if not args.no_flow:
            self.flow.pack(side="bottom", fill="x")
        self.caption = tk.Label(self.root, bg="black", fg="#d8d8d8", bd=0, justify="center", padx=24, pady=12,
                                font=("Segoe UI", args.text_size), wraplength=args.size - 48)
        self.label = tk.Label(self.root, bg="black", bd=0)
        self.label.pack(fill="both", expand=True)
        self.label.bind("<Configure>", self.on_resize)
        self.root.bind("<Configure>", lambda e: self.caption.configure(wraplength=max(self.root.winfo_width() - 48, 100)))
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("q", lambda e: self.root.destroy())
        self.root.bind("f", lambda e: self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen")))
        self.root.bind("m", self.toggle_flow)
        if args.fullscreen:
            self.root.attributes("-fullscreen", True)
        threading.Thread(target=reader, args=(self.frames, self.texts, self.statuses), daemon=True).start()
        self.root.after(30, self.tick)
        self.root.after(100, self.draw_flow)

    def trace(self, msg):
        if self.args.trace:
            print(f"[img-view] {msg}", file=sys.stderr, flush=True)

    # ------------------------------------------------------------------ the flow strip

    def toggle_flow(self, event=None):
        if self.flow.winfo_ismapped():
            self.flow.pack_forget()
        else:   # must sit below everything else: re-pack in order
            for widget in (self.caption, self.label):
                widget.pack_forget()
            self.flow.pack(side="bottom", fill="x")
            if self.caption.cget("text"):
                self.caption.pack(side="bottom", fill="x")
            self.label.pack(fill="both", expand=True)

    def take_statuses(self):
        while True:
            try:
                source, kind, seq, text, detail = self.statuses.get_nowait()
            except queue.Empty:
                return
            lane = self.lanes.get(source)
            if lane is None:
                continue
            now = time.time()
            last = lane["segments"][-1] if lane["segments"] else None
            if last is not None and last[1] is None and (last[2], last[3]) == (kind, seq):
                lane["text"], lane["detail"] = text, detail      # same activity: just refresh the words
                continue
            if last is not None and last[1] is None:
                last[1] = now
            if kind != "idle":
                lane["segments"].append([now, None, kind, seq])
            lane.update(text=text, detail=detail, since=now, kind=kind)
            self.trace(f"status {source}: {text}" + (f" ({detail})" if detail else ""))

    def draw_flow(self):
        self.take_statuses()
        if self.flow.winfo_ismapped():
            c, now, span = self.flow, time.time(), self.args.flow_span
            width, left = max(c.winfo_width(), 200), 78
            c.delete("all")
            for seconds in range(0, int(span) + 1, 30):                       # faint time marks every 30 s
                x = width - seconds / span * (width - left)
                c.create_line(x, 0, x, len(LANES) * LANE_H + 6, fill="#18181c")
            for row, (key, name) in enumerate(LANES):
                lane, y = self.lanes[key], 3 + row * LANE_H
                c.create_text(6, y + LANE_H / 2, text=name, anchor="w", fill="#70707a", font=("Consolas", 9))
                lane["segments"] = [s for s in lane["segments"] if (s[1] or now) > now - span]
                for start, end, kind, seq in lane["segments"]:
                    x0 = max(width - (now - start) / span * (width - left), left)
                    x1 = width - (now - (end or now)) / span * (width - left)
                    if x1 - x0 < 1:
                        x1 = x0 + 1
                    c.create_rectangle(x0, y + 2, x1, y + LANE_H - 3, fill=COLOURS.get(kind, "#666666"), outline="")
                    if seq and x1 - x0 > 16:
                        c.create_text(x0 + 4, y + LANE_H / 2, text=str(seq), anchor="w", fill="#0b0b0d", font=("Consolas", 8, "bold"))
                if lane["text"]:
                    words = lane["text"] + (f"  ·  {lane['detail']}" if lane["detail"] else "")
                    if lane["kind"] not in ("idle", "stop"):
                        words += f"  ·  {int(now - lane['since'])} s"
                    c.create_text(left + 6, y + LANE_H / 2, text=words, anchor="w", font=("Consolas", 9),
                                  fill="#ff8080" if lane["kind"] == "error" else "#c8c8d0")
        self.root.after(250, self.draw_flow)

    # ------------------------------------------------------------------ the picture

    def fit(self, image):
        """The image scaled to fit the window, centred on black, so every frame is the same size."""
        w, h = max(self.label.winfo_width(), 2), max(self.label.winfo_height(), 2)
        scale = min(w / image.width, h / image.height)
        size = (max(int(image.width * scale), 1), max(int(image.height * scale), 1))
        canvas = Image.new("RGB", (w, h))
        canvas.paste(image.resize(size, Image.BILINEAR), ((w - size[0]) // 2, (h - size[1]) // 2))
        return canvas

    def draw(self, image):
        self.shown = image
        self.photo = ImageTk.PhotoImage(image)
        self.label.configure(image=self.photo)

    def start_fade(self, target, length, final):
        if self.shown is None or length < 2:
            self.draw(target)
            self.finish(final)
            return
        start = self.shown if self.shown.size == target.size else self.shown.resize(target.size, Image.BILINEAR)
        self.fade = (start, target, 0, length, final)

    def finish(self, final):
        if final:
            self.base = self.shown
            self.hold_until = time.time() + self.args.hold

    def on_resize(self, event):
        """Window resized (or went fullscreen): redraw the held image at the new size."""
        if event.widget is self.label and self.base_source is not None and self.fade is None:
            if self.base is None or self.base.size != (max(event.width, 2), max(event.height, 2)):
                self.base = self.fit(self.base_source)
                self.draw(self.base)

    def tick(self):
        try:
            text = self.texts.get_nowait()
            if text and not self.caption.winfo_ismapped():
                self.label.pack_forget()                     # caption strip under the picture
                self.caption.pack(side="bottom", fill="x")
                self.label.pack(fill="both", expand=True)
            self.caption.configure(text=text)
            self.trace(f"caption: {len(text.split())} words")
        except queue.Empty:
            pass
        if self.fade is not None:
            a, b, i, n, final = self.fade
            i += 1
            self.draw(Image.blend(a, b, i / n))
            self.fade = (a, b, i, n, final) if i < n else None
            if self.fade is None:
                self.finish(final)
        elif time.time() >= self.hold_until:
            item = None if self.ended else next_item(self.frames)
            if item is EOF:
                self.ended = True
                self.trace(f"stream ended after {self.count} finished image(s)")
                now = time.time()
                for lane in self.lanes.values():      # nothing is running any more: say so, but keep any reason given
                    if lane["segments"] and lane["segments"][-1][1] is None:
                        lane["segments"][-1][1] = now
                    if lane["kind"] not in ("error", "stop"):
                        lane.update(kind="stop", text="ended", detail="")
                    elif lane["kind"] == "stop" and not lane["text"]:
                        lane["text"] = "ended"
                if self.args.exit_on_eof:
                    self.root.after(int(self.args.linger * 1000), self.root.destroy)
            elif item is not None:
                image, final, seq, step, steps = item
                picture = self.fit(image)
                if final:
                    self.count += 1
                    self.base_source = image
                    self.trace(f"finished image {seq}: fade in, then hold {self.args.hold:g}s")
                    self.start_fade(picture, self.args.fade_frames, True)
                else:
                    if self.base_source is not None and (self.base is None or self.base.size != picture.size):
                        self.base = self.fit(self.base_source)   # window changed size since the last finished image
                    if self.base is not None and self.base.size == picture.size:
                        strength = min((step / max(steps, 1)) ** 1.5, 0.85)
                        picture = Image.blend(self.base, picture, strength)
                        self.trace(f"image {seq} step {step}/{steps}: blended over the held image at {strength:.0%}")
                    else:
                        self.trace(f"image {seq} step {step}/{steps}: shown alone (no finished image yet)")
                    self.start_fade(picture, max(self.args.fade_frames // 3, 2), False)
        self.root.after(33, self.tick)

    def run(self):
        self.root.mainloop()


def main():
    ap = argparse.ArgumentParser(description="Show a mindstream from stdin in a window (nothing saved)")
    ap.add_argument("--size", type=int, default=900, help="initial window size in pixels")
    ap.add_argument("--fullscreen", action="store_true")
    ap.add_argument("--fade-frames", type=int, default=24, help="length of the crossfade to a finished image, in 1/30 s frames")
    ap.add_argument("--hold", type=float, default=4.0, help="seconds a finished image stays untouched before the next one starts to show through")
    ap.add_argument("--text-size", type=int, default=13, help="caption font size")
    ap.add_argument("--no-flow", action="store_true", help="start with the flow strip hidden (M toggles it)")
    ap.add_argument("--flow-span", type=float, default=240.0, help="seconds of history shown in the flow strip")
    ap.add_argument("--exit-on-eof", action="store_true", help="close when the stream ends (default: stay open)")
    ap.add_argument("--linger", type=float, default=5.0, help="seconds to keep the last image up after the stream ends, with --exit-on-eof")
    ap.add_argument("--trace", action="store_true", help="print what is being displayed to stderr")
    args = ap.parse_args()
    if sys.stdin.isatty():
        sys.exit("img-view reads a stream from stdin; use img-gen --view or mindstream")
    Viewer(args).run()


if __name__ == "__main__":
    main()
