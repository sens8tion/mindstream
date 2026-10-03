"""An experiment, not part of a session: one sample on a loop and a pad, to find by ear where "filthy" is.

    .venv-dml\\Scripts\\python.exe demo\\knobs.py              a window; the sample loops on the default output
    .venv-dml\\Scripts\\python.exe demo\\knobs.py --selftest   render everything silently and report (no window, no sound)

The pad is the two knobs. Each corner holds one kind of damage (mindstream/mangle.py has fourteen), and where the
dot stands is the blend between the four: moving it is heard at once. Choose what sits in each corner from the
menus, or roll the dice. Under the pad:

    Drive       how hard the sound is pushed into the damage (0 = untouched)
    Movement    a ringing filter sweeping in time with the loop, before the damage
    Follow      the louder moments are driven harder than the quiet ones
    Body        how much the result rings in the thing chosen beside it: a box, a tin, a pipe, a spring, a drum
    Filter      a filter of your own over all of it, after the damage: low, high or band, with cutoff and resonance.
                It is heard as you turn it.

Below 90 Hz the sound is left alone, and the result is brought back to the loudness of the untouched sample, so
that louder is never mistaken for filthier.

"That's it" marks where everything stands for the sample playing; "Next sample" moves on with nothing changed, to
hear whether one setting holds across sounds; "Copy marks" puts the marks on the clipboard. Nothing is written
to disk.
"""
import argparse
import os
import random
import sys
import threading
import time

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from mindstream import mangle  # noqa: E402

# a spread, because filth is not only bass: a bass note, a break, a voice, a siren, a brass stab
WANTED = ("bass_synth_one_shot_massif", "drum_thick_break", "mc_multiplex_hold_tight", "Dub_Siren", "brass_one_shot_chord")
BODIES = {"snare": "Drum_Snare_One_Shot", "cymbal": "cymbal_one_shot", "kick": "kick_one_shot"}       # short sounds to ring in, if they are there
LONGEST = 6.0
START = ("clip", "fold", "crush", "shift")        # bottom-left, bottom-right, top-left, top-right


def library():
    import sample_pull
    return [p for p, _ in sample_pull.library()]


def find(files, want):
    return next((p for p in files if want.lower() in os.path.basename(p).lower()), None)


def load(path, rate, longest=LONGEST):
    import soundfile as sf
    from mindstream.samples import to_rate
    data, was = sf.read(path, dtype="float32", always_2d=True, frames=int(longest * 48000))
    x = to_rate(data, was, rate).mean(axis=1)[:int(longest * rate)]
    edge = min(int(rate * 0.01), len(x) // 4)                      # the loop point must not click
    x[:edge] *= np.linspace(0, 1, edge, dtype=np.float32)
    x[-edge:] *= np.linspace(1, 0, edge, dtype=np.float32)
    return (x / (float(np.abs(x).max()) + 1e-9)).astype(np.float32)


class Player:
    def __init__(self, device=None, silent=False):
        files = library()
        self.paths = [p for p in (find(files, want) for want in WANTED) if p] or files[:5]
        if not self.paths:
            sys.exit("no samples found in the local library")
        self.index, self.rate = 0, 44100
        if not silent:
            import sounddevice as sd
            self.rate = int(sd.query_devices(device, "output")["default_samplerate"])
        self.bodies = mangle.bodies(self.rate, {name: load(path, self.rate, 0.4) for name, path in
                                                ((name, find(files, want)) for name, want in BODIES.items()) if path})
        self.names, self.x, self.y = list(START), 0.0, 0.0
        self.drive, self.movement, self.follow, self.body, self.body_mix, self.bypass = 0.5, 0.0, 0.0, "none", 0.0, False
        self.filter_kind, self.filter_at, self.filter_res, self.filter = "off", 1.0, 0.2, mangle.Filter(self.rate)
        self.filter = mangle.Filter(self.rate)
        self.dry = load(self.paths[0], self.rate)
        self.made, self.next_made, self.wanted, self.pos, self.stream = [self.dry] * 4, None, None, 0, None
        self.ask()
        if not silent:
            import sounddevice as sd
            self.stream = sd.OutputStream(samplerate=self.rate, channels=2, dtype="float32", blocksize=1024, device=device,
                                          callback=self.callback)
            self.stream.start()
            threading.Thread(target=self.renderer, daemon=True).start()

    def name(self):
        return os.path.splitext(os.path.basename(self.paths[self.index]))[0]

    def ask(self):
        self.wanted = (self.index, tuple(self.names), self.drive, self.movement, self.follow, self.body, self.body_mix)

    def render(self):
        return mangle.corners(self.dry, self.rate, self.names, self.drive, self.movement, self.follow,
                              self.bodies.get(self.body), self.body_mix)

    def next(self):
        self.index = (self.index + 1) % len(self.paths)
        self.dry = load(self.paths[self.index], self.rate)
        self.pos, self.made = 0, [self.dry] * 4
        self.ask()

    def renderer(self):
        done = None
        while True:
            want = self.wanted
            if want is None or want == done:
                time.sleep(0.02)
                continue
            made = self.render()
            if want[0] == self.index and len(made[0]) == len(self.dry):
                self.next_made = made
            done = want

    def mixed(self, made, where):
        if self.bypass:
            return self.dry[where] if len(self.dry) == len(made[0]) else made[0][where]
        shares = mangle.weights(self.x, self.y)
        return sum(w * c[where] for w, c in zip(shares, made) if w > 0) * mangle.evened(shares)

    def callback(self, out, frames, when, status):
        try:
            made, fresh = self.made, self.next_made
            where = (self.pos + np.arange(frames)) % len(made[0])
            block = self.mixed(made, where)
            if fresh is not None and len(fresh[0]) == len(made[0]):      # new corners: fade to them over this block
                ramp = np.linspace(0, 1, frames, dtype=np.float32)
                block = block * (1 - ramp) + self.mixed(fresh, where) * ramp
                self.made, self.next_made = fresh, None
            self.pos = (self.pos + frames) % len(made[0])
            if not self.bypass:
                block = self.filter.run(np.asarray(block, dtype=np.float32), self.filter_kind, self.cutoff(), self.filter_res)
            out[:] = (np.tanh(block * 0.9) * 0.7)[:, None]
        except Exception:
            out[:] = 0

    def cutoff(self):
        """Where the filter's slider stands, in Hz: 40 at the bottom, 16,000 at the top."""
        return 40.0 * 400.0 ** self.filter_at

    def mark(self):
        w = mangle.weights(self.x, self.y)
        return (f"{self.name()}: " + ", ".join(f"{name} {share:.0%}" for name, share in zip(self.names, w) if share >= 0.005)
                + f" | drive {self.drive:.2f}, movement {self.movement:.2f}, follow {self.follow:.2f}, body {self.body} {self.body_mix:.2f}, filter "
                + (f"{self.filter_kind} at {self.cutoff():.0f} Hz, resonance {self.filter_res:.2f}" if self.filter_kind != "off" else "off"))


def window(player):
    import tkinter as tk
    size, marks = 300, []
    root = tk.Tk()
    root.title("Where is filthy?")
    root.configure(padx=18, pady=14)
    title = tk.Label(root, text=player.name(), font=("Segoe UI", 11, "bold"), wraplength=560)
    title.grid(row=0, column=0, columnspan=3, sticky="w")
    count = tk.Label(root, text="", fg="#666")
    count.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 8))
    canvas = tk.Canvas(root, width=size, height=size, bg="#15151a", highlightthickness=1, highlightbackground="#555")
    canvas.grid(row=3, column=0, columnspan=3, pady=4)
    dot = canvas.create_oval(0, 0, 0, 0, fill="#ff5a3c", outline="")
    choice = [tk.StringVar(value=name) for name in player.names]
    what = tk.Label(root, text="", fg="#666", wraplength=560, justify="left")

    def show():
        px, py = player.x * size, (1 - player.y) * size
        canvas.coords(dot, px - 9, py - 9, px + 9, py + 9)
        count.configure(text=f"sample {player.index + 1} of {len(player.paths)}, on a loop")
        what.configure(text="   ".join(f"{name}: {mangle.CURVES[name][1]}." for name in dict.fromkeys(player.names)))

    def drag(event):
        player.x, player.y = min(max(event.x / size, 0.0), 1.0), 1.0 - min(max(event.y / size, 0.0), 1.0)
        show()

    def chosen(*_):
        player.names = [c.get() for c in choice]
        player.ask()
        show()

    canvas.bind("<Button-1>", drag)
    canvas.bind("<B1-Motion>", drag)
    for i, (row, column, stick) in enumerate(((4, 0, "w"), (4, 2, "e"), (2, 0, "w"), (2, 2, "e"))):      # the corners, as in mangle.weights
        tk.OptionMenu(root, choice[i], *mangle.CURVES, command=chosen).grid(row=row, column=column, sticky=stick)

    def dice():
        for c, name in zip(choice, random.sample(list(mangle.CURVES), 4)):
            c.set(name)
        chosen()

    tk.Button(root, text="Roll the dice", command=dice).grid(row=4, column=1)
    what.grid(row=5, column=0, columnspan=3, sticky="w", pady=(6, 0))
    for row, (key, label, start) in enumerate((("drive", "Drive", 50), ("movement", "Movement", 0), ("follow", "Follow", 0), ("body_mix", "Body", 0)), 6):
        tk.Label(root, text=label, width=10, anchor="w").grid(row=row, column=0, sticky="w")
        scale = tk.Scale(root, from_=0, to=100, orient="horizontal", length=360, showvalue=False,
                         command=lambda value, key=key: (setattr(player, key, float(value) / 100.0), player.ask()))
        scale.set(start)
        scale.grid(row=row, column=1, columnspan=2, sticky="e")
    body = tk.StringVar(value=player.body)
    tk.Label(root, text="rings in a").grid(row=10, column=0, sticky="w")
    tk.OptionMenu(root, body, *player.bodies, command=lambda value: (setattr(player, "body", value), player.ask())).grid(row=10, column=1, sticky="w")
    kind = tk.StringVar(value=player.filter_kind)
    tk.Label(root, text="Filter").grid(row=11, column=0, sticky="w")
    tk.OptionMenu(root, kind, *mangle.Filter.KINDS, command=lambda value: setattr(player, "filter_kind", value)).grid(row=11, column=1, sticky="w")
    for at, (key, label, start) in enumerate((("filter_at", "Cutoff", 100), ("filter_res", "Resonance", 20)), 12):
        tk.Label(root, text=label, width=10, anchor="w").grid(row=at, column=0, sticky="w")
        scale = tk.Scale(root, from_=0, to=100, orient="horizontal", length=360, showvalue=False,
                         command=lambda value, key=key: setattr(player, key, float(value) / 100.0))
        scale.set(start)
        scale.grid(row=at, column=1, columnspan=2, sticky="e")
    row = tk.Frame(root)
    row.grid(row=14, column=0, columnspan=3, pady=12, sticky="w")
    listing = tk.Text(root, height=7, width=92, font=("Consolas", 8))

    def text():
        return "\n".join(marks)

    def mark(_=None):
        marks.append(player.mark())
        listing.delete("1.0", "end")
        listing.insert("end", text())

    def following(_=None):
        player.next()
        title.configure(text=player.name())
        show()

    def untouched(_=None):
        player.bypass = not player.bypass
        dry.configure(relief="sunken" if player.bypass else "raised", text="Hearing: untouched" if player.bypass else "Compare with untouched  (b)")

    def copy(_=None):
        root.clipboard_clear()
        root.clipboard_append(text())

    tk.Button(row, text="That's it  (space)", command=mark, width=16).pack(side="left", padx=(0, 8))
    tk.Button(row, text="Next sample  (n)", command=following, width=16).pack(side="left", padx=(0, 8))
    dry = tk.Button(row, text="Compare with untouched  (b)", command=untouched, width=26)
    dry.pack(side="left", padx=(0, 8))
    tk.Button(row, text="Copy marks", command=copy, width=12).pack(side="left")
    listing.grid(row=15, column=0, columnspan=3)
    root.bind("<space>", mark)
    root.bind("n", following)
    root.bind("b", untouched)
    show()
    root.mainloop()
    return text()


def selftest():
    player = Player(silent=True)
    names, rate, bad = list(mangle.CURVES), player.rate, 0
    print(f"{len(player.paths)} samples, {len(names)} curves, bodies: {', '.join(player.bodies)}")
    spectrum = lambda y: np.abs(np.fft.rfft(y))      # noqa: E731
    print("\nwhat each curve does to the first sample at drive 0.6 (so they can be seen to differ):")
    x = player.dry
    freqs = np.fft.rfftfreq(len(x), 1.0 / rate)
    for i in range(0, len(names), 4):
        group = (names[i:i + 4] + names[:4])[:4]
        for name, y in list(zip(group, mangle.corners(x, rate, group, 0.6)))[:len(names[i:i + 4])]:
            s = spectrum(y)
            ok = bool(np.isfinite(y).all()) and len(y) == len(x)
            bad += not ok
            print(f"  {'ok  ' if ok else 'FAIL'} {name:9s} centre {np.sum(freqs * s) / s.sum():5.0f} Hz, above 4 kHz {s[freqs > 4000].sum() / s.sum():4.0%}, "
                  f"crest {np.abs(y).max() / np.sqrt((y ** 2).mean()):4.1f}, level {np.sqrt((y ** 2).mean()) / np.sqrt((x ** 2).mean()):.2f}x")
    print("\nevery sample, a few settings, with timing:")
    for _ in player.paths:
        for drive, movement, follow, body, mix in ((0, 0, 0, "none", 0), (0.5, 0, 0, "none", 0), (1, 1, 1, "tin", 1), (0.7, 0.5, 0.5, "pipe", 0.5),
                                                   (0.6, 0, 0, next(reversed(player.bodies)), 0.8)):
            player.drive, player.movement, player.follow, player.body, player.body_mix = drive, movement, follow, body, mix
            t = time.perf_counter()
            made = player.render()
            took = (time.perf_counter() - t) * 1000
            y = mangle.blend(made, 0.3, 0.7)
            ok = all(np.isfinite(c).all() and len(c) == len(player.dry) for c in made)
            same = drive == 0 and np.allclose(made[0], player.dry, atol=2e-3)
            bad += not ok or (drive == 0 and not same)
            print(f"  {'ok  ' if ok and (drive > 0 or same) else 'FAIL'} {player.name()[:40]:40s} drive {drive:.1f} movement {movement:.1f} follow {follow:.1f} "
                  f"body {body:6s} {mix:.1f}: level {np.sqrt((y ** 2).mean()) / np.sqrt((player.dry ** 2).mean()):.2f}x, {took:4.0f} ms"
                  + ("  (untouched at drive 0)" if same else ""))
        player.next()
    print("\nFAILED" if bad else "\nall passed")


def main():
    ap = argparse.ArgumentParser(description="One sample and a pad: find where filthy is, by ear")
    ap.add_argument("--selftest", action="store_true", help="render silently and report; no window, no sound")
    ap.add_argument("--device", default=None, help="output device (default: the system's)")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    player = Player(device=int(args.device) if args.device and args.device.isdigit() else args.device)
    marks = window(player)
    player.stream.stop()
    print(marks or "no marks made")


if __name__ == "__main__":
    main()
