"""Reads a steer the way a person would: a very small language model, held in RAM on the CPU, turns a line
such as "let it breathe, then hit hard" into what it asks of the music and the visuals. No commands to
remember. The story itself is not touched: the steer still goes to llama word for word.

The model may only answer with a few tags from a fixed list (a grammar allows nothing else), such as
"slower, calmer" or "break"; `apply` turns the tags into settings, given how things stand now.

    steer_intent.py serve                  one JSON object per line in: {"steer": "...", "now": {...}}
                                           one per line out: {"changes": {...}, "seconds": 1.2}
    steer_intent.py try "slower, gently"   read one steer and show the result

Nothing is logged or written. The model file is a GGUF kept outside the repo (--model, or MINDSTREAM_STEER_MODEL).
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mindstream.local import pick  # noqa: E402
from mindstream.score import key_name, parse_key  # noqa: E402

DEFAULT_MODEL = pick("steer_model")        # a small GGUF chat model, chosen in models.local.json
SUFFIX = pick("steer_suffix")              # anything the chosen model needs after each instruction (e.g. to switch thinking off)

# What the model may say: a few tags from this list, or "none". Short answers keep it to about a second.
TAGS = {
    "slower": "the music slows a little", "much-slower": "a big drop in speed",
    "faster": "the music speeds up a little", "much-faster": "a big jump in speed",
    "four-on-floor": "steady kick on every beat: house, techno, driving, relentless, on the beat",
    "two-step": "skipping, swung, light on its feet: garage, 2-step",
    "broken-beat": "syncopated, off-beat, restless: breaks, broken beat",
    "drum-and-bass": "fast rolling breakbeat: drum and bass, jungle",
    "half-time": "slow and heavy: half-time, dub, trap, sludge",
    "amen": "the amen break: jungle", "rolling": "a rolling drum and bass kick pattern", "stutter": "a doubled, tripping kick under a wall of hats",
    "gabber": "a kick on every sixteenth: relentless, brutal", "happy-hardcore": "four on the floor with open hats on the backbeat: manic, euphoric",
    "shuffled-two-step": "2-step pushed off the grid", "half-step": "kick on one and three with steady hats",
    "breakbeat-hardcore": "a busy old-school rave break",
    "no-drums": "the drums stop and stay stopped: ambient, beatless, just atmosphere",
    "break": "a breakdown: the drums and bass drop out for a few bars, build, then slam back in",
    "long-break": "a long breakdown, twice the length",
    "sad": "sorrow, tension, loss", "happy": "bright, relieved, joyful, hopeful",
    "soulful": "warm, tender, human", "dark": "menace, dread, evil, filthy, nasty",
    "calmer": "gentler, softer, stripped back, quieter", "much-calmer": "almost nothing left, barely there",
    "harder": "more intense, wilder, building, heavier", "much-harder": "everything at once, frantic, mental, overwhelming",
    "more-sub": "more deep bass, low end", "less-sub": "less bass",
    "more-bells": "some high sparkle, twinkling", "lots-of-bells": "a shower of bells, glittering",
    "less-bells": "fewer bells", "no-bells": "no bells or sparkle",
    "swung": "loose, shuffling, swinging", "straight": "rigid, mechanical, strict",
    "new-tune": "a new melody, a fresh start, something different",
    "replace-pictures": "throw the present pictures away and paint new ones",
    "restart-story": "begin the same story or theme again from its start",
    "rebuild-music": "work the whole music out again from scratch",
    "sphere": "the picture wraps a ball, a world, a head, an eye", "ring": "the picture wraps a ring, a loop, a wheel",
    "ribbon": "the picture becomes cloth, water, smoke, a road",
    "no-mirrors": "plain, unreflected", "few-mirrors": "a little kaleidoscope", "many-mirrors": "shattered, kaleidoscopic, fractured",
    "short-trails": "crisp, clean, sharp", "long-trails": "smeared, dreamy, drowning in its own past, strobing",
    "alone": "the picture is by itself, lonely, empty", "crowded": "earlier pictures mob it, swarming",
    "spin-slower": "it turns slowly, drifts", "spin-faster": "it whirls, spins fast",
    "pictures-slower": "new pictures (photos, images) arrive less often", "pictures-faster": "new pictures arrive more often",
    "red": "a red cast over the picture", "orange": "an orange cast", "yellow": "a yellow cast", "green": "a green cast",
    "blue": "a blue cast", "purple": "a purple cast", "pink": "a pink cast", "white": "no colour cast",
    "cold-light": "icy, wintry, moonlit", "warm-light": "golden, firelit, sunny",
}
# Some models open every reply with a thinking block, empty when thinking is off. The grammar has to allow
# it, or such a model is pushed off the path it was trained on and answers nonsense.
# Besides the tags, an answer may name a part of the music and how it should sound: "bass dirtier", "bells mute".
PART_NAMES = ("kick", "snare", "hats", "sub", "bass", "tune", "bells", "drones", "clip")
PART_WORDS = ("louder", "quieter", "mute", "back", "dirtier", "cleaner", "wetter", "drier", "brighter", "darker", "higher", "lower",
              "longer", "shorter")
GRAMMAR = ('root ::= ("<think>\\n\\n</think>\\n\\n")? answer\nanswer ::= "none" | item (", " item)*\nitem ::= tag | part " " how\ntag ::= '
           + " | ".join(f'"{t}"' for t in TAGS) + "\npart ::= " + " | ".join(f'"{t}"' for t in PART_NAMES)
           + "\nhow ::= " + " | ".join(f'"{t}"' for t in PART_WORDS))
COLOURS = {"red": "#d01818", "orange": "#ff8020", "yellow": "#ffe040", "green": "#30c050", "blue": "#3060ff", "purple": "#8030d0",
           "pink": "#ff60b0", "white": "#ffffff", "cold-light": "#9fc4ff", "warm-light": "#ffb070"}

SYSTEM = ("""You read one instruction from someone steering a live show of dance music and moving pictures. Reply with the tags, from the list below, for what the instruction asks to change, separated by commas. Use only tags the instruction clearly asks for: usually one to three, never more than six. If it is only about the story (people, places, events) and says nothing about how the show should sound, feel or look, reply: none

Tags
""" + "\n".join(f"{t}: {d}" if d else t for t, d in TAGS.items()) + """

Parts of the music. To change how one SOUNDS (not what it plays), write its name and one word, for example: bass dirtier
The parts: kick, snare, hats (the drums); sub (the deepest bass); bass; tune (the riff or melody: the organ, the plucky or plinky thing, the stabs); bells; drones (the pads, the wash); clip (the voice or sound taken from the film).
The words: louder, quieter, mute, back (bring it back), dirtier (rougher, grittier), cleaner, wetter (more echo, more space), drier, brighter, darker (duller, warmer), higher, lower (deeper), longer, shorter (tighter).

The instruction may be loose or general. Work out what the person most likely wants and answer with the nearest tags or parts; only answer none when it is plainly just story.

Examples
Instruction: the low end is boring, rough it up
sub dirtier, bass dirtier
Instruction: that plinky thing is doing my head in
tune quieter
Instruction: give the drums some space
kick wetter, snare wetter, hats wetter
Instruction: I can't hear her
clip louder
Instruction: it's all a bit samey
new-tune, harder
Instruction: too much going on
calmer, bells mute
Instruction: make it feel like 4am
much-calmer, dark, drones louder, spin-slower
Instruction: slower, gently
slower, calmer
Instruction: make it filthy, proper jungle, bass you feel in your teeth
drum-and-bass, dark, more-sub
Instruction: she finds the letter in the drawer
none
Instruction: give me a break then bring it back
break
Instruction: go a bit mental, strobing red
much-harder, long-trails, red
Instruction: let it open out, hopeful, little bells, lose the drums for a bit
no-drums, happy, more-bells, alone
Instruction: warehouse techno, relentless
four-on-floor, harder, straight
Instruction: the old man walks into the sea
none
Instruction: shatter it, ice cold
many-mirrors, cold-light
Instruction: something completely different, lazy sunday feel
new-tune, soulful, swung, calmer
Instruction: slow the photos down, less chaotic
pictures-slower, calmer
Instruction: more pictures, keep them coming
pictures-faster
Instruction: get rid of those pictures and give me new ones, and think the music through again
replace-pictures, rebuild-music
Instruction: take it from the top
restart-story
Instruction: strip it right back, just the low end
much-calmer, more-sub, no-bells
Instruction: take the drums out for a good while, then bring them back
long-break
Instruction: this is getting boring, change it up
new-tune, harder""")


# The same tags, chosen for a beat of the story rather than for an instruction: this is the per-beat director.
SCENE = ("""You score a live show of dance music and moving pictures. You are given one beat of a story (sometimes with the viewer's own steer in brackets, which outweighs the story). Reply with the tags, from the list below, for how the show should change to fit this beat, separated by commas: usually two to four. Pick what the beat's mood, pace, place and colour call for. If the beat simply carries on the same scene and mood, reply: none

Tags
""" + "\n".join(f"{t}: {d}" if d else t for t, d in TAGS.items() if "break" not in t and "pictures" not in t and t not in ("restart-story", "rebuild-music")) + """

Examples
Beat: The door gives way and the corridor fills with smoke; she runs, coughing, toward the red light at the far end.
faster, harder, red, long-trails
Beat: He sits a long time on the cold step, turning the ring over in his fingers, while the street empties.
slower, sad, calmer, alone
Beat: They keep walking along the same road, talking quietly about nothing in particular.
none
Beat: Morning. The market wakes all at once: shutters, shouting, oranges rolling across the stones.
happy, more-bells, crowded, warm-light
Beat: Something enormous moves under the ice. The lake groans. Nobody breathes.
dark, much-calmer, more-sub, cold-light
Beat: The machines start up, one after another, until the whole floor is shaking in time.
four-on-floor, harder, straight, ring""")


def apply(tags, now):
    """Tags -> settings, given how things stand: now = {bpm, key, style, chaos, sub, twinkle, spin}."""
    out, tags = {}, [t for t in tags if t in TAGS]
    get = lambda name, default: float(now.get(name, default))   # noqa: E731
    clamp = lambda v, lo, hi: round(min(max(v, lo), hi), 3)     # noqa: E731
    key = parse_key(now.get("key", "A minor")) or ("a", "minor")
    for tag in tags:
        if tag in ("much-slower", "slower", "faster", "much-faster"):
            factor = {"much-slower": 0.72, "slower": 0.88, "faster": 1.12, "much-faster": 1.3}[tag]
            out["bpm"] = round(min(max(get("bpm", 120) * factor, 40.0), 300.0), 1)
        elif tag in ("four-on-floor", "two-step", "broken-beat", "drum-and-bass", "half-time", "no-drums"):
            style = {"four-on-floor": "four", "two-step": "twostep", "broken-beat": "broken", "drum-and-bass": "dnb",
                     "half-time": "half", "no-drums": "none"}[tag]
            if style != now.get("style"):
                out["style"] = style
        elif tag in ("amen", "rolling", "stutter", "gabber", "happy-hardcore", "shuffled-two-step", "half-step", "breakbeat-hardcore"):
            if tag.replace("-", "_") != now.get("style"):
                out["style"] = tag.replace("-", "_")
        elif tag in ("break", "long-break"):
            out["break"] = 4 if tag == "break" else 8
        elif tag in ("sad", "happy", "soulful", "dark"):
            mode = {"sad": "minor", "happy": "major", "soulful": "dorian", "dark": "phrygian"}[tag]
            if mode != key[1]:
                out["key"] = key_name((key[0], mode))
        elif tag in ("calmer", "much-calmer", "harder", "much-harder"):
            out["chaos"] = clamp({"much-calmer": 0.25, "much-harder": 1.8}.get(tag, get("chaos", 1.0) + (0.4 if tag == "harder" else -0.4)), 0, 2)
        elif tag in ("more-sub", "less-sub"):
            out["sub"] = clamp(get("sub", 0.8) + (0.35 if tag == "more-sub" else -0.35), 0, 1)
        elif tag in ("more-bells", "lots-of-bells", "less-bells", "no-bells"):
            out["twinkle"] = clamp({"no-bells": 0.0, "lots-of-bells": 1.0}.get(tag, get("twinkle", 0.3) + (0.35 if tag == "more-bells" else -0.3)), 0, 1)
        elif tag in ("swung", "straight"):
            out["swing"] = 0.3 if tag == "swung" else 0.0
        elif tag == "new-tune":
            out["rescore"] = True
        elif tag in ("sphere", "ring", "ribbon"):
            out["shape"] = "torus" if tag == "ring" else tag
        elif tag.endswith("-mirrors"):
            out["folds"] = {"no": 0.0, "few": 3.0, "many": 8.0}[tag.split("-")[0]]
        elif tag.endswith("-trails"):
            out["trails"] = 0.25 if tag.startswith("short") else 0.9
        elif tag in ("alone", "crowded"):
            out["swarm"] = 0.0 if tag == "alone" else 1.0
        elif tag in ("spin-slower", "spin-faster"):
            out["spin"] = clamp(get("spin", 1.0) * (0.5 if tag == "spin-slower" else 1.8) + (0.3 if tag == "spin-faster" else 0), 0, 3)
        elif tag in ("pictures-slower", "pictures-faster"):     # seconds between pictures; 0 = only when the story moves on
            every = get("cadence", 0.0)
            out["cadence"] = (0.0 if every == 0 or every >= 60 else round(every * 1.7)) if tag == "pictures-slower" \
                else (20.0 if every == 0 else max(12.0, round(every / 1.7)))
        elif tag in COLOURS:
            out["tint"] = COLOURS[tag]
    if out.get("style") == "dnb" and out.get("bpm", get("bpm", 120)) < 160:
        out["bpm"] = 172.0                                    # drum and bass is a tempo as much as a pattern
    if "style" in out or "key" in out:
        out["rescore"] = True                                 # a new style or key gets new riffs to go with it
    return out


class Reader:
    def __init__(self, path=DEFAULT_MODEL, threads=0):
        from llama_cpp import Llama, LlamaGrammar
        self.grammar = LlamaGrammar.from_string(GRAMMAR, verbose=False)
        threads = threads or max(2, min(6, (os.cpu_count() or 4) // 2))        # bursts only; leave cores for everything else
        self.llm = Llama(model_path=path, n_ctx=2048, n_threads=threads, n_gpu_layers=0, verbose=False)
        # a second, separate context for scoring story beats: each keeps its own instructions read and ready
        self.scene = Llama(model_path=path, n_ctx=2048, n_threads=threads, n_gpu_layers=0, verbose=False)
        self.read("warm up", {})            # reads the instructions once; later steers reuse that work
        self.read("warm up", {}, beat=True)

    def read(self, steer, now, beat=False):
        t0 = time.time()
        reply = (self.scene if beat else self.llm).create_chat_completion(
            messages=[{"role": "system", "content": SCENE if beat else SYSTEM},
                      {"role": "user", "content": f"{'Beat' if beat else 'Instruction'}: {steer}{SUFFIX}"}],
            grammar=self.grammar, temperature=0.0, max_tokens=48)
        items = [t.strip() for t in reply["choices"][0]["message"]["content"].split("</think>")[-1].split(",")]
        tags = list(dict.fromkeys(t for t in items if t in TAGS and not (beat and ("break" in t or "pictures" in t or t in ("restart-story", "rebuild-music")))))[:6]
        parts = [] if beat else [tuple(t.split()) for t in dict.fromkeys(items)
                                 if len(t.split()) == 2 and t.split()[0] in PART_NAMES and t.split()[1] in PART_WORDS][:6]
        return {"changes": apply(tags, now), "tags": tags, "parts": parts, "seconds": round(time.time() - t0, 2)}


def main():
    ap = argparse.ArgumentParser(description="Read steers with a small in-RAM model (nothing saved)")
    ap.add_argument("mode", choices=["serve", "try"])
    ap.add_argument("steers", nargs="*")
    ap.add_argument("--file", help="for try: a text file of steers, one per line")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--beat", action="store_true", help="for try: read the lines as story beats, not as steers")
    args = ap.parse_args()
    if not args.model or not os.path.exists(args.model):
        sys.exit(f"[steer-intent] no model: set \"steer_model\" in models.local.json (found: {args.model or 'nothing'})")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    t0 = time.time()
    reader = Reader(args.model, args.threads)
    if args.mode == "try":
        print(f"loaded and warmed in {time.time() - t0:.1f}s")
        now = {"bpm": 120, "key": "A minor", "style": "four", "chaos": 1.0, "sub": 0.8, "twinkle": 0.3, "spin": 1.0}
        if args.file:
            args.steers += [x.strip() for x in open(args.file, encoding="utf-8") if x.strip()]
        for steer in args.steers:
            got = reader.read(steer, now, beat=args.beat)
            print(f"{got['seconds']:5.2f}s  {steer!r}\n        tags: {', '.join(got['tags'] + [' '.join(p) for p in got['parts']]) or 'none'}\n        -> {got['changes']}")
        return
    sys.stdout.write(json.dumps({"ready": True, "seconds": round(time.time() - t0, 1)}) + "\n")
    sys.stdout.flush()
    for raw in sys.stdin:
        try:
            ask = json.loads(raw)
            got = (reader.read(str(ask["beat"])[:900], ask.get("now") or {}, beat=True) if "beat" in ask
                   else reader.read(str(ask["steer"])[:600], ask.get("now") or {}))
        except Exception as e:                       # one bad line must not end the helper
            got = {"changes": {}, "error": f"{type(e).__name__}: {e}"[:200]}
        sys.stdout.write(json.dumps(got) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
