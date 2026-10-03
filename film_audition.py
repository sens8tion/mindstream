"""Hear what the film model's music field can do. A fixed, simple scene (one singer, one short line) is filmed
several times, each with a different `non_diegetic_music:` line: four on the floor, syncopated, 2-step, drum
and bass, twinkly without drums, and one with no voice at all. Each clip is played as soon as it is made and
measured (tempo heard against tempo asked, how much sub, how much sparkle). Everything stays in memory:
nothing is written to disk, and the clips are gone when this ends.

    film-audition               all of them, in order
    film-audition 3 5           only those
    film-audition --list        show the menu and stop
    film-audition --music "at 150 BPM, ..." [--voice none]    try a music line of your own

While it runs: type a clip's number and Enter to hear it again, q to stop.
"""
import argparse
import base64
import ctypes
import json
import os
import subprocess
import sys
import threading
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mindstream import tempo  # noqa: E402
from mindstream.local import comfy_python  # noqa: E402

COMFY_PYTHON = comfy_python()     # vid-gen runs in ComfyUI's environment (models.local.json, or MINDSTREAM_COMFY_PYTHON)

SCENE = ("integrated_multimodal_description: A dim basement club lit by one amber lamp; a singer stands at a microphone, "
         "close to the camera, swaying in time with the music. [Shot 1] The camera holds a slow push-in on her face{voice}\n"
         "overall_soundscape: The faint hum of an amplifier and the soft shuffle of feet on a concrete floor.\n"
         "non_diegetic_music: {music}")
SUNG = (" as she sings. (S1), a woman in her thirties, on screen, low warm voice, unhurried, London accent, sings, "
        "a simple falling melody that sits on the beat, <d>en Hold me till morning</d>")
SPOKEN = (" as she speaks. (S1), a woman in her thirties, on screen, low warm voice, unhurried, London accent, says "
          "<d>en Hold me till morning</d>")
SILENT = " as she listens with her eyes closed, lips together, nodding on every beat."

# name, tempo, voice, the music line
MENU = [
    ("four on the floor", 124, SUNG,
     "House music at 124 BPM: a punchy kick drum on every beat, a deep sustained sub bass note under it, a crisp open "
     "hi-hat on every off-beat, a clap on beats two and four. Steady, driving, unchanged from start to finish."),
    ("syncopated", 110, SUNG,
     "A syncopated broken-beat groove at 110 BPM: the kick drum lands off the beat, pushing ahead of each bar, rimshots "
     "answer between the kicks, a rubbery sub bass line slides between two low notes, shakers keep steady sixteenths."),
    ("2-step", 132, SUNG,
     "UK garage 2-step at 132 BPM: a skipping kick on the first beat and just before the third, a tight snare on beats two "
     "and four, swung shuffling hi-hats, a warm rolling sub bass, and bright twinkling bell arpeggios high above."),
    ("drum and bass", 174, SUNG,
     "Drum and bass at 174 BPM: a fast rolling breakbeat with a snare cracking on beats two and four, a huge deep sub "
     "bass holding long notes, and a glittering high arpeggio of glassy synth notes cascading downward."),
    ("twinkly, no drums", 100, SUNG,
     "Ambient music at 100 BPM, with a pulse but no drums: a music box and a glockenspiel play a sparkling, twinkling "
     "arpeggio in even eighth notes, over one very low, soft, sustained sub bass drone."),
    ("spoken over 2-step", 132, SPOKEN,
     "UK garage 2-step at 132 BPM: a skipping kick on the first beat and just before the third, a tight snare on beats two "
     "and four, swung shuffling hi-hats, a warm rolling sub bass, and bright twinkling bell arpeggios high above."),
    ("music only", 124, SILENT,
     "House music at 124 BPM: a punchy kick drum on every beat, a deep sustained sub bass note under it, a crisp open "
     "hi-hat on every off-beat, a clap on beats two and four, and a bright plucked synth melody that repeats every bar."),
]


def measure(pcm, rate, channels, bpm):
    """What can be said about a soundtrack without hearing it."""
    x = np.frombuffer(pcm, "<i2").astype(np.float32).reshape(-1, max(channels, 1)).mean(axis=1) / 32768.0
    if len(x) < rate // 2 or float(np.abs(x).max()) < 1e-4:
        return "silent"
    found = tempo.detect(pcm, rate, channels, hint=float(bpm)) if bpm else None
    power = np.abs(np.fft.rfft(x)) ** 2
    freqs = np.fft.rfftfreq(len(x), 1.0 / rate)
    total = float(power[freqs >= 20].sum()) or 1.0
    share = lambda lo, hi: 100.0 * float(power[(freqs >= lo) & (freqs < hi)].sum()) / total   # noqa: E731
    heard = (f"tempo heard {found['bpm']:.1f} (asked {bpm}; confidence {found['confidence']:.1f}, 2.5 or more is a clear beat)"
             if found else f"no steady beat found (asked {bpm})") if bpm else "tempo not checked"
    return (f"{len(x) / rate:.1f}s, {heard}; energy: sub below 100 Hz {share(20, 100):.0f}%, "
            f"100 Hz to 2 kHz {share(100, 2000):.0f}%, 2 to 6 kHz {share(2000, 6000):.0f}%, sparkle above 6 kHz {share(6000, 30000):.1f}%; "
            f"peak {float(np.abs(x).max()):.2f}")


def main():
    ap = argparse.ArgumentParser(description="Audition the film model's music field (nothing saved)")
    ap.add_argument("which", nargs="*", type=int, help="numbers from the menu (default: all)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--seconds", type=float, default=6.0, help="length of each clip")
    ap.add_argument("--megapixels", type=float, default=0.15, help="frame area: small, because only the sound matters here")
    ap.add_argument("--music", help="a non_diegetic_music line of your own (include 'at N BPM')")
    ap.add_argument("--voice", choices=["sung", "spoken", "none"], default="sung", help="for --music")
    ap.add_argument("--silent", action="store_true", help="measure only; play nothing")
    ap.add_argument("--show", action="store_true", help="print each full prompt")
    args = ap.parse_args()

    menu = list(MENU)
    if args.music:
        import re
        asked = re.search(r"(\d{2,3})\s*BPM", args.music, re.I)
        menu = [("your own", int(asked.group(1)) if asked else 0, {"sung": SUNG, "spoken": SPOKEN, "none": SILENT}[args.voice], args.music)]
    if args.list:
        for i, (name, bpm, voice, music) in enumerate(menu, 1):
            print(f"{i}. {name} ({bpm} BPM, {'sung' if voice is SUNG else 'spoken' if voice is SPOKEN else 'no voice'})\n   {music}")
        return
    chosen = [n for n in (args.which or range(1, len(menu) + 1)) if 1 <= n <= len(menu)]
    if not chosen:
        sys.exit("nothing chosen; see --list")
    if not COMFY_PYTHON:
        sys.exit('no ComfyUI Python chosen: set "comfy_python" (or "comfy_dir") in models.local.json (see models.example.json)')

    # the same lock as a mindstream session: the video model needs the whole GPU and most of the RAM
    lock = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\mindstream-session")
    if ctypes.windll.kernel32.GetLastError() == 183:
        sys.exit("a mindstream session (or another audition) is running; stop it first")

    play = None
    if not args.silent:
        try:
            import sounddevice as sd
            play = lambda pcm, rate, ch: sd.play(np.frombuffer(pcm, "<i2").reshape(-1, ch), rate)   # noqa: E731
        except Exception as e:
            print(f"no sound output ({e}); measuring only", flush=True)

    gen = subprocess.Popen([COMFY_PYTHON, "-B", "-W", "ignore", os.path.join(HERE, "vid_gen.py"), "--quiet",
                            "--megapixels", str(args.megapixels)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for n in chosen:
        name, bpm, voice, music = menu[n - 1]
        prompt = SCENE.format(voice=voice, music=music)
        if args.show:
            print(f"--- {n}. {name}\n{prompt}\n", flush=True)
        gen.stdin.write((json.dumps({"prompt": prompt, "seconds": args.seconds}) + "\n").encode())
    gen.stdin.flush()
    print(f"{len(chosen)} clip(s) of {args.seconds:g}s to make: " + ", ".join(f"{n}. {menu[n - 1][0]}" for n in chosen), flush=True)

    clips, done = {}, threading.Event()

    def collect():
        last = ""
        started = time.time()
        for raw in gen.stdout:
            try:
                item = json.loads(raw)
            except ValueError:
                continue
            if item.get("type") == "status":
                line = f"{item.get('text', '')} {item.get('detail', '')}".strip()
                if line != last and item.get("kind") != "render" or line != last and "step" in line:
                    print(f"  [{time.time() - started:4.0f}s] {line}", flush=True)
                last = line
            elif item.get("type") == "clip":
                n = chosen[item["seq"] - 1] if item["seq"] <= len(chosen) else item["seq"]
                audio = item.get("audio") or {}
                pcm = base64.b64decode(audio.get("data", ""))
                rate, ch = int(audio.get("rate", 44100)), int(audio.get("channels", 2))
                clips[n] = (pcm, rate, ch)
                print(f"\n=== {n}. {menu[n - 1][0]}: {measure(pcm, rate, ch, menu[n - 1][1])}"
                      + ("" if play is None else f"   (playing; type {n} to hear it again)") + "\n", flush=True)
                if play is not None:
                    play(pcm, rate, ch)
                if len(clips) == len(chosen):
                    break
        done.set()

    threading.Thread(target=collect, daemon=True).start()

    def typed():
        for line in sys.stdin:
            word = line.strip().lower()
            if word in ("q", "quit", "/bye"):
                done.set()
                os._exit(0 if gen.poll() is not None else (gen.kill() or 0))
            if word.isdigit() and int(word) in clips and play is not None:
                play(*clips[int(word)])

    if sys.stdin.isatty():
        threading.Thread(target=typed, daemon=True).start()
    done.wait()
    try:
        gen.stdin.close()            # the video model unloads and its process ends
    except OSError:
        pass
    gen.wait()
    if len(clips) < len(chosen):
        print(f"only {len(clips)} of {len(chosen)} clip(s) were made (see the messages above)", flush=True)
    if play is not None and sys.stdin.isatty() and clips:
        print("all made. Type a number to hear one again, q to finish (the clips are then gone).", flush=True)
        threading.Event().wait()


if __name__ == "__main__":
    main()
