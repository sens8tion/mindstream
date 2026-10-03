"""The parts of the rhythm section by name, and the words that change how a part SOUNDS (not what it plays):
"make the bass dirtier", "more room on the tune", "brighter hats", "mute the bells", "tune up an octave".

No numpy here: the story feed uses this to recognise such a line the moment it is typed and to say what it
did; groove.py holds the settings and applies them when it makes each sound.
"""
import re

PARTS = ("kick", "snare", "hats", "sub", "bass", "tune", "bells", "drones", "clip", "sample")
LAYERS = ("clip", "sample")       # not played by the rhythm section: the film's own sound, and a sample pulled from outside, both chopped
ALIASES = {
    "kick": ("kick", "kick drum", "bass drum", "kicks"),
    "snare": ("snare", "snares", "clap", "claps", "backbeat"),
    "hats": ("hats", "hat", "hi-hats", "hi-hat", "hihats", "hihat", "hh", "cymbals"),
    "sub": ("sub", "sub bass", "sub-bass", "subs"),
    "bass": ("bass", "bassline", "bass line"),
    "tune": ("tune", "riff", "hook", "lead", "melody", "pluck", "plucks", "organ", "synth", "keys", "stabs", "chops"),
    "bells": ("bells", "bell", "twinkles", "twinkle", "chimes"),
    "drones": ("drones", "drone", "pad", "pads", "strings", "wash"),
    "clip": ("clip", "voice", "vocal", "vocals", "film sound", "film audio", "speech"),
    "sample": ("sample", "samples", "loop", "break", "pulled sample", "pull"),
}
# how a part starts out: level, drive (0 clean .. 1 filthy), room (None = the part's own amount), tone (-1 dark .. 1 bright),
# octave, length (1 = as written), on
# pitch: semitones up or down; attack: seconds the sound takes to arrive (0 = at once); punch: how hard its front hits
# filth: the part's knob, 0 to 1: how far it is pushed into damage (mangle.py). patch: the character of that damage
DEFAULTS = {"level": 1.0, "drive": 0.0, "room": None, "tone": 0.0, "octave": 0, "length": 1.0, "on": True,
            "pitch": 0.0, "attack": 0.0, "punch": 0.0, "filth": 0.0, "patch": None, "duck_by": None, "duck": 0.7}
# duck_by: the part this one gives way to each time that part sounds. None = as it comes (most parts give way to the kick,
# the drums to nothing), "none" = to nothing, or a part of the rhythm section by name. duck: how far it gives way, 0 to 1
# the kinds of damage a knob can turn toward, and the things a damaged sound can ring in (made in mangle.py)
DAMAGE = ("tape", "tube", "clip", "fuzz", "fold", "crease", "rectify", "half", "sputter", "crush", "decimate", "harmonic", "ring", "shift")
BODIES = ("none", "box", "tin", "pipe", "spring")
# a knob's character until it is given one: the middle of the pad, an even mix of its four corners
PLAIN = {"mix": {"clip": 0.25, "fold": 0.25, "crush": 0.25, "shift": 0.25}, "movement": 0.0, "follow": 0.0, "body": "none", "body_mix": 0.0}

# word -> (setting, what to do with it). ("x", f) multiplies, ("+", d) adds, ("=", v) sets.
WORDS = {
    "louder": ("level", ("x", 1.35)), "up": ("level", ("x", 1.35)), "quieter": ("level", ("x", 0.7)), "softer": ("level", ("x", 0.7)),
    "down": ("level", ("x", 0.7)), "lower in the mix": ("level", ("x", 0.7)),
    "mute": ("on", ("=", False)), "off": ("on", ("=", False)), "kill": ("on", ("=", False)), "drop": ("on", ("=", False)),
    "lose": ("on", ("=", False)), "no": ("on", ("=", False)), "without": ("on", ("=", False)),
    "unmute": ("on", ("=", True)), "on": ("on", ("=", True)), "back": ("on", ("=", True)), "bring back": ("on", ("=", True)),
    "dirty": ("drive", ("+", 0.35)), "dirtier": ("drive", ("+", 0.35)), "gritty": ("drive", ("+", 0.35)), "grittier": ("drive", ("+", 0.35)),
    "crunchy": ("drive", ("+", 0.35)), "distorted": ("drive", ("+", 0.5)), "filthy": ("drive", ("+", 0.6)), "nasty": ("drive", ("+", 0.5)),
    "nastier": ("drive", ("+", 0.35)), "driven": ("drive", ("+", 0.35)), "fuzzy": ("drive", ("+", 0.5)), "harder": ("drive", ("+", 0.25)),
    "clean": ("drive", ("=", 0.0)), "cleaner": ("drive", ("+", -0.35)),
    "wet": ("room", ("+", 0.3)), "wetter": ("room", ("+", 0.3)), "roomy": ("room", ("+", 0.3)), "spacious": ("room", ("+", 0.4)),
    "echoey": ("room", ("+", 0.4)), "reverb": ("room", ("+", 0.3)), "echo": ("room", ("+", 0.3)), "room": ("room", ("+", 0.3)),
    "space": ("room", ("+", 0.3)), "cavernous": ("room", ("=", 0.9)), "huge": ("room", ("+", 0.5)),
    "dry": ("room", ("=", 0.03)), "drier": ("room", ("+", -0.25)), "close": ("room", ("=", 0.05)),
    "bright": ("tone", ("+", 0.5)), "brighter": ("tone", ("+", 0.5)), "sharper": ("tone", ("+", 0.5)), "crisp": ("tone", ("+", 0.5)),
    "crisper": ("tone", ("+", 0.5)), "thinner": ("tone", ("+", 0.5)), "harsh": ("tone", ("+", 0.8)),
    "dark": ("tone", ("+", -0.5)), "darker": ("tone", ("+", -0.5)), "duller": ("tone", ("+", -0.5)), "muffled": ("tone", ("+", -0.8)),
    "warm": ("tone", ("+", -0.4)), "warmer": ("tone", ("+", -0.4)), "rounder": ("tone", ("+", -0.4)), "fatter": ("tone", ("+", -0.4)),
    "higher": ("octave", ("+", 1)), "up an octave": ("octave", ("+", 1)), "lower": ("octave", ("+", -1)), "deeper": ("octave", ("+", -1)),
    "down an octave": ("octave", ("+", -1)),
    "long": ("length", ("x", 1.6)), "longer": ("length", ("x", 1.6)), "ringing": ("length", ("x", 1.8)), "sustained": ("length", ("x", 1.8)),
    "boomy": ("length", ("x", 1.6)), "tail": ("length", ("x", 1.6)), "longer tail": ("length", ("x", 1.6)), "long tail": ("length", ("x", 1.6)),
    "decay": ("length", ("x", 1.6)), "longer decay": ("length", ("x", 1.6)), "sustain": ("length", ("x", 1.6)),
    "release": ("length", ("x", 1.6)), "longer release": ("length", ("x", 1.6)),
    "shorter tail": ("length", ("x", 0.6)), "short tail": ("length", ("x", 0.6)), "shorter decay": ("length", ("x", 0.6)),
    "punchy": ("length", ("x", 0.7)), "punchier": ("length", ("x", 0.7)),
    "short": ("length", ("x", 0.6)), "shorter": ("length", ("x", 0.6)), "tight": ("length", ("x", 0.6)), "tighter": ("length", ("x", 0.6)),
    "snappy": ("length", ("x", 0.6)), "staccato": ("length", ("x", 0.5)), "clipped": ("length", ("x", 0.5)),
    "reset": ("reset", ("=", True)), "normal": ("reset", ("=", True)), "plain": ("reset", ("=", True)),
    # what a part PLAYS (its pattern), not how it sounds: handled by groove.Groove.edit_pattern
    "busier": ("pattern", ("=", "busier")), "fuller": ("pattern", ("=", "busier")),
    "sparser": ("pattern", ("=", "sparser")), "simpler": ("pattern", ("=", "sparser")), "fewer": ("pattern", ("=", "sparser")),
    "less busy": ("pattern", ("=", "sparser")), "thinner pattern": ("pattern", ("=", "sparser")),
    "double": ("pattern", ("=", "double")), "doubled": ("pattern", ("=", "double")), "double time": ("pattern", ("=", "double")),
    "half": ("pattern", ("=", "half")), "halved": ("pattern", ("=", "half")), "half time": ("pattern", ("=", "half")),
    "vary": ("pattern", ("=", "vary")), "varied": ("pattern", ("=", "vary")), "different": ("pattern", ("=", "vary")),
    "mutate": ("pattern", ("=", "mutate")), "mutated": ("pattern", ("=", "mutate")), "new pattern": ("pattern", ("=", "mutate")),
    "mixed up": ("pattern", ("=", "vary")), "fill": ("pattern", ("=", "fill")), "roll": ("pattern", ("=", "fill")),
    "as written": ("pattern", ("=", "reset")), "by the book": ("pattern", ("=", "reset")),
}
PLAYED = ("kick", "snare", "hats", "sub", "bass")       # the parts whose patterns can be edited step by step
LIMITS = {"level": (0.0, 2.5), "drive": (0.0, 1.0), "room": (0.0, 1.0), "tone": (-1.0, 1.0), "octave": (-2, 2), "length": (0.3, 3.0),
          "pitch": (-12.0, 12.0), "attack": (0.0, 0.5), "punch": (0.0, 1.0), "filth": (0.0, 1.0), "duck": (0.0, 1.0)}
STRUCTURAL = ("style", "key", "rescore", "break")      # what the music is built on: the session changes these on four-bar lines only
QUICK = frozenset(("level", "on", "duck", "duck_by"))     # settings that change how a part is mixed, not how its sounds are made

NAMES = []      # sample layers, by the names they were given: parts like any other, for as long as they exist
_FILL = r"(?:(?:a bit|a little|a lot|a touch|much|way|far|even|more|less|really|very|so|some|of|and|but|,|a|an)\s+)*"
_OPEN = r"^(?:(?:please|now|ok|okay|and|then|can you|could you|let'?s|just)[ ,]+)*"
_ONTO = r"(?:\s+(?:on|for|to|in|from))?"
_WORD = "|".join(sorted((re.escape(w) for w in WORDS), key=len, reverse=True))


def set_names(names):
    """Tell the reader which sample layers exist, so "make the rain darker" and "rain on the off-beats" are understood."""
    global _PART, _PLAYED, _PART_FIRST, _WORD_FIRST
    fixed = {a for group in ALIASES.values() for a in group}
    NAMES[:] = [n for n in dict.fromkeys(str(n).strip().lower() for n in names) if re.fullmatch(r"[a-z][a-z0-9]{1,15}", n) and n not in fixed][:12]
    every = [a for group in ALIASES.values() for a in group] + NAMES
    _PART = "|".join(sorted((re.escape(a) for a in every), key=len, reverse=True))
    _PLAYED = "|".join(sorted((re.escape(a) for a in [a for part in PLAYED for a in ALIASES[part]] + list(ALIASES["clip"]) + NAMES + ["sample"]),
                              key=len, reverse=True))
    # "make the bass dirtier and louder"  /  "bass dirtier"
    _PART_FIRST = re.compile(_OPEN + r"(?:(?:make|turn|get|set|have|take|bring|put|give)\s+)?(?:the\s+)?(" + _PART + r")\s+((?:" + _FILL
                             + r"(?:" + _WORD + r")\s*)+)$")
    # "dirtier bass"  /  "mute the bells"  /  "more room on the tune"  /  "brighter, longer hats"
    _WORD_FIRST = re.compile(_OPEN + r"(?:(?:give|put|add)\s+)?((?:" + _FILL + r"(?:" + _WORD + r")\s*)+)" + _ONTO + r"\s+(?:the\s+)?(" + _PART + r")$")


def part_named(text):
    low = text.strip().lower()
    if low in NAMES:
        return low
    for part, names in ALIASES.items():
        if low in names:
            return part
    return None


def parts_in(text):
    """A typed line -> [(part, word), ...] if it is about how parts sound, else []. Narrow on purpose: the line
    must be nothing but parts and such words ("the bells ring louder" is story, and is left alone)."""
    low = " ".join(str(text).lower().split()).strip(" .!")
    pairs = []
    for clause in re.split(r"\s*(?:;|\band then\b|\bthen\b|\.\s)\s*|\s*,\s*(?=(?:make|turn|mute|the|give|put|more|less)\b)", low):
        clause = clause.strip()
        if not clause or len(clause.split()) > 10:
            return []
        found = _PART_FIRST.match(clause)
        part, words = (found.group(1), found.group(2)) if found else (None, None)
        if not found:
            found = _WORD_FIRST.match(clause)
            if not found:
                return []
            part, words = found.group(2), found.group(1)
            if len(words.split()) > 1:                       # "more room on the tune": that "on" is not the word "on"
                words = re.sub(r"\s+(?:on|for|to|in|from)\s*$", "", words)
        negate = bool(re.search(r"\bless\b", words))
        for word in re.findall(_WORD, words):
            if negate and WORDS[word][1][0] == "+":          # "less room on the tune", "less dirty"
                word = {"room": "drier", "drive": "cleaner"}.get(WORDS[word][0], word)
            elif negate and WORDS[word][1] == ("x", 1.6) and WORDS[word][0] == "length":      # "less tail on the kick"
                word = "shorter"
            pairs.append((part_named(part), word))
    return pairs


def change(settings, word):
    """Apply one word to a part's settings (a dict like DEFAULTS), in place. Returns the setting it touched."""
    name, (how, amount) = WORDS[word]
    if name == "pattern":                              # what the part plays is not one of its sound settings
        return "pattern"
    if name == "reset":
        settings.update(DEFAULTS)                      # the knob back to nothing, and its character forgotten
        settings["fx"], settings["layers"] = [], []
        return "reset"
    if how == "=":
        settings[name] = amount
    else:
        now = settings[name] if settings[name] is not None else 0.3          # a part's own room is about this much
        settings[name] = now * amount if how == "x" else now + amount
    if name in LIMITS:
        low, high = LIMITS[name]
        settings[name] = min(max(settings[name], low), high)
    if name == "level" and settings["level"] > 0:
        settings["on"] = True
    return name


def summary(settings):
    """A part's settings as a few words, saying only what is not as it started."""
    out = []
    if not settings["on"]:
        return "muted"
    if abs(settings["level"] - 1.0) > 0.05:
        out.append("louder" if settings["level"] > 1 else "quieter")
    if settings["drive"] > 0.05:
        out.append("filthy" if settings["drive"] > 0.6 else "dirty")
    if settings["room"] is not None:
        out.append("dry" if settings["room"] < 0.1 else "cavernous" if settings["room"] > 0.7 else "roomy")
    if abs(settings["tone"]) > 0.05:
        out.append("bright" if settings["tone"] > 0 else "dark")
    if settings["octave"]:
        out.append(f"{abs(settings['octave'])} octave{'s' if abs(settings['octave']) > 1 else ''} {'up' if settings['octave'] > 0 else 'down'}")
    if abs(settings["length"] - 1.0) > 0.05:
        out.append("long" if settings["length"] > 1 else "short")
    if abs(settings.get("pitch", 0.0)) > 0.05:
        out.append("tuned " + ("up" if settings["pitch"] > 0 else "down"))
    if settings.get("attack", 0.0) > 0.01:
        out.append("soft front")
    if settings.get("punch", 0.0) > 0.05:
        out.append("punchy")
    if settings.get("filth", 0.0) > 0.005:
        out.append(f"knob {settings['filth'] * 100:.0f}")
    out += ["+" + fx["type"] for fx in settings.get("fx", ())]
    if settings.get("layers"):
        out.append(f"+{len(settings['layers'])} layer{'s' if len(settings['layers']) > 1 else ''}")
    return ", ".join(out)


# ---------------------------------------------------------------------------------------------------------------
# An open patch for each part, for instructions that no word list covers ("add a delay", "another layer on the
# sub an octave up", "make the hats sound broken"). Whoever interprets the instruction (llama) answers with a
# list of operations; `sanitize` keeps what is well formed and in range, `apply_op` puts one into effect.
#
#   {"part": "tune", "set": {"room": 0.6, "drive": 0.2, "tone": -0.3, "octave": 1, "length": 1.5, "level": 1.2, "on": true}}
#   {"part": "tune", "add_fx": {"type": "delay", "time": "3/16", "feedback": 0.45, "mix": 0.35}}
#   {"part": "sub",  "add_layer": {"wave": "saw", "octave": 1, "detune": 8, "level": 0.4, "decay": 0.5}}
#   {"part": "hats", "clear": "fx"}            ("fx", "layers" or "all")

FX = {      # effect -> its settings: (lowest, highest, usual), or ("time", usual), or ("choice", options, usual)
    "delay": {"time": ("time", "3/16"), "feedback": (0.0, 0.9, 0.4), "mix": (0.0, 1.0, 0.35)},
    "chorus": {"depth": (0.0, 1.0, 0.5), "mix": (0.0, 1.0, 0.5)},
    "crush": {"bits": (2.0, 16.0, 6.0), "rate": (0.02, 1.0, 0.3)},
    "tremolo": {"time": ("time", "1/8"), "depth": (0.0, 1.0, 0.6)},
    "filter": {"kind": ("choice", ("low", "high", "band"), "low"), "freq": (40.0, 12000.0, 1200.0), "q": (0.0, 1.0, 0.0)},
    "sweep": {"from": (40.0, 12000.0, 4000.0), "to": (40.0, 12000.0, 300.0), "time": ("time", "1/8")},
    "reverse": {},
}
WAVES = ("sine", "saw", "square", "noise")
LAYER = {"wave": ("choice", WAVES, "saw"), "octave": (-3.0, 3.0, 0.0), "detune": (-50.0, 50.0, 0.0), "level": (0.0, 1.5, 0.4),
         "decay": (0.03, 3.0, 0.4)}
TIMES = ("1/32", "1/16", "1/8", "3/16", "1/4", "3/8", "1/2", "1/1")


def fresh():
    """A part's settings as it starts out, with its own (empty) lists of effects and extra layers."""
    return {**DEFAULTS, "fx": [], "layers": []}


def _fit(spec, given):
    out = {}
    for name, rule in spec.items():
        value = given.get(name) if isinstance(given, dict) else None
        if rule[0] == "time":
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                out[name] = min(max(float(value), 0.02), 2.0)                  # seconds
            else:
                out[name] = value if value in TIMES else rule[1]
        elif rule[0] == "choice":
            out[name] = str(value).lower() if str(value).lower() in rule[1] else rule[2]
        else:
            try:
                out[name] = min(max(float(value), rule[0]), rule[1])
            except (TypeError, ValueError):
                out[name] = rule[2]
    return out


def sanitize(ops):
    """Whatever came back from the interpreter -> a list of well-formed operations (possibly empty)."""
    clean = []
    if isinstance(ops, dict):
        ops = [ops]
    for op in ops if isinstance(ops, list) else []:
        if not isinstance(op, dict):
            continue
        named = str(op.get("part", "")).strip().lower()
        part = part_named(named[4:] if named.startswith("the ") else named)
        if part is None:
            continue
        if isinstance(op.get("set"), dict):
            wanted = {}
            for name, value in op["set"].items():
                if name == "on":
                    wanted["on"] = bool(value) and str(value).lower() not in ("false", "0", "off", "no")
                elif name == "duck_by":
                    by = str(value).lower()
                    if value is None or by in ("auto", "as it comes", "default"):
                        wanted["duck_by"] = None
                    elif by in ("none", "nothing", "off"):
                        wanted["duck_by"] = "none"
                    elif part_named(by) in PARTS and part_named(by) not in LAYERS and part_named(by) != part:
                        wanted["duck_by"] = part_named(by)
                elif name in LIMITS:
                    try:
                        low, high = LIMITS[name]
                        wanted[name] = int(round(min(max(float(value), low), high))) if name == "octave" else min(max(float(value), low), high)
                    except (TypeError, ValueError):
                        pass
            if wanted:
                clean.append({"part": part, "set": wanted})
        if isinstance(op.get("add_fx"), dict) and str(op["add_fx"].get("type", "")).lower() in FX:
            kind = str(op["add_fx"]["type"]).lower()
            clean.append({"part": part, "add_fx": {"type": kind, **_fit(FX[kind], op["add_fx"])}})
        if isinstance(op.get("add_layer"), dict):
            clean.append({"part": part, "add_layer": _fit(LAYER, op["add_layer"])})
        if op.get("patch") == "another":                                       # a new character for the knob, at random
            clean.append({"part": part, "patch": another()})
        elif op.get("patch") == "mutate":                                      # the character it has, changed a little (when it is applied)
            clean.append({"part": part, "patch": "mutate"})
        elif isinstance(op.get("patch"), dict):
            given = clean_patch(op["patch"])
            if given:
                clean.append({"part": part, "patch": given})
        if op.get("when") is not None and (part in NAMES or part in LAYERS):   # which bars a layer plays in
            when = op["when"]
            if str(when).lower() in ("breaks", "break"):
                clean.append({"part": part, "when": "breaks"})
            else:
                try:
                    clean.append({"part": part, "when": int(min(max(float(when), 1), 16))})
                except (TypeError, ValueError):
                    pass
        if isinstance(op.get("steps"), list) and (part in PLAYED or part in NAMES or part in LAYERS):   # the sixteenths it plays on, 0 to 15
            steps = sorted({int(x) for x in op["steps"] if isinstance(x, (int, float)) and not isinstance(x, bool) and 0 <= int(x) <= 15})
            entry = {"part": part, "steps": steps}
            if part == "hats" and isinstance(op.get("open"), list):
                entry["open"] = sorted({int(x) for x in op["open"] if isinstance(x, (int, float)) and not isinstance(x, bool) and 0 <= int(x) <= 15})
            clean.append(entry)
        if isinstance(op.get("bring"), bool) and (part in NAMES or part in LAYERS):   # a waiting sample layer brought in, or taken out
            clean.append({"part": part, "bring": op["bring"]})
        chop = op.get("chop")
        if chop is not None and (part in NAMES or part in LAYERS):            # how a layer or the clip is cut up
            if str(chop).lower() in CHOPS:
                clean.append({"part": part, "chop": str(chop).lower()})
            elif isinstance(chop, (int, float)) and not isinstance(chop, bool) and 2 <= int(chop) <= 32:
                clean.append({"part": part, "chop": int(chop)})
        if op.get("drop") is True and part in NAMES:                          # a sample layer taken away altogether
            clean.append({"part": part, "drop": True})
        if str(op.get("drop_fx", "")).lower() in FX:                           # one effect taken away, the rest left
            clean.append({"part": part, "drop_fx": str(op["drop_fx"]).lower()})
        if str(op.get("clear", "")).lower() in ("fx", "layers", "all"):
            clean.append({"part": part, "clear": str(op["clear"]).lower()})
    return clean[:48]          # room for one change to every part and every layer at once (the super knob)


def apply_op(settings, op):
    """Put one sanitized operation into effect on a part's settings."""
    if "set" in op:
        settings.update(op["set"])
    if "add_fx" in op:
        settings["fx"] = [fx for fx in settings["fx"] if fx["type"] != op["add_fx"]["type"]][-3:] + [op["add_fx"]]
    if "add_layer" in op:
        settings["layers"] = settings["layers"][-2:] + [op["add_layer"]]
    if "patch" in op:
        settings["patch"] = mutate(settings.get("patch")) if op["patch"] == "mutate" else op["patch"]
    if "drop_fx" in op:
        settings["fx"] = [fx for fx in settings["fx"] if fx["type"] != op["drop_fx"]]
    if op.get("clear") in ("fx", "all"):
        settings["fx"] = []
    if op.get("clear") in ("layers", "all"):
        settings["layers"] = []
    if op.get("clear") == "all":
        settings.update(DEFAULTS)


def describe_op(op):
    """One operation, as a person would say it."""
    part = op["part"]
    if "set" in op:
        names = {"room": "room", "drive": "dirt", "tone": "brightness", "octave": "octave", "length": "length", "level": "level",
                 "pitch": "pitch", "attack": "attack", "punch": "punch", "filth": "knob"}
        if set(op["set"]) == {"filth"}:
            return f"the {part}'s knob is at {op['set']['filth'] * 100:.0f}"
        if "duck_by" in op["set"]:
            by = op["set"]["duck_by"]
            return (f"the {part} gives way as it comes" if by is None else f"the {part} gives way to nothing" if by == "none"
                    else f"the {part} gives way to the {by}" + (f", by {op['set']['duck'] * 100:.0f}" if "duck" in op["set"] else ""))
        names["duck"] = "ducking"
        said = ["switched " + ("on" if v else "off") if k == "on" else f"{names[k]} {v:g}" for k, v in op["set"].items()]
        return f"the {part}: " + ", ".join(said)
    if "add_fx" in op:
        fx = op["add_fx"]
        detail = ", ".join(f"{k} {v:g}" if isinstance(v, float) else f"{k} {v}" for k, v in fx.items() if k != "type")
        return f"the {part} gets {'an' if fx['type'][0] in 'aeiou' else 'a'} {fx['type']}" + (f" ({detail})" if detail else "")
    if "drop_fx" in op:
        return f"the {part} loses its {op['drop_fx']}"
    if "drop" in op:
        return f"the {part} is gone"
    if op.get("patch") == "mutate":
        return f"the {part}'s knob turns toward something a little different"
    if "patch" in op:
        mix = op["patch"]["mix"]
        return (f"the {part}'s knob now turns toward " + ", ".join(f"{name} {share:.0%}" for name, share in mix.items())
                + (f", ringing in a {op['patch']['body']}" if op["patch"]["body"] != "none" and op["patch"]["body_mix"] > 0.01 else ""))
    if "bring" in op:
        return f"the {part} comes in on the next bar" if op["bring"] else f"the {part} is taken out, and waits"
    if "chop" in op:
        how = op["chop"]
        if how in ("next", "whole"):
            return f"the {part} is cut another way" if how == "next" else f"the {part} is one whole sound again, played from its start"
        return (f"the {part} is cut into {how} equal pieces" if isinstance(how, int) else f"the {part} is cut at its obvious transients" if how == "transients"
                else f"the {part} is cut at less obvious transients too" if how == "finer" else f"the {part} is cut only at its plainest transients"
                if how == "coarser" else f"the {part} is cut on the {how}")
    if "when" in op:
        return (f"the {part} plays only in the breaks" if op["when"] == "breaks" else f"the {part} plays in every bar" if op["when"] == 1
                else f"the {part} plays in the last of every {op['when']} bars")
    if "steps" in op:
        on = ", ".join(str(x + 1) for x in op["steps"]) or "nothing"
        return f"the {part} plays on sixteenths {on}" + (f", open on {', '.join(str(x + 1) for x in op['open'])}" if op.get("open") else "")
    if "add_layer" in op:
        layer = op["add_layer"]
        where = (f"{abs(layer['octave']):g} octave{'s' if abs(layer['octave']) != 1 else ''} {'up' if layer['octave'] > 0 else 'down'}"
                 if layer["octave"] else "at pitch")
        return f"the {part} gets another layer: a {layer['wave']} {where}"
    return f"the {part}: {op['clear']} cleared"


# ---------------------------------------------------------------------------------------------------------------
# Where in the bar a part plays, said plainly: "sub on the off-beats", "kick on every beat", "hats on every sixteenth",
# "snare on the three", or exactly: "!kick 1 5 9 13" (sixteenths of the bar, counted from 1).

PLACES = (
    (r"(?:the\s+)?off[- ]?beats?", (2, 6, 10, 14)), (r"every (?:beat|quarter)|(?:the\s+)?beats?|all fours?", (0, 4, 8, 12)),
    (r"every (?:eighth|8th)s?|(?:the\s+)?eighths", tuple(range(0, 16, 2))), (r"every (?:sixteenth|16th)s?|(?:the\s+)?sixteenths", tuple(range(16))),
    (r"(?:the\s+)?(?:two and (?:the\s+)?four|2 and 4|backbeat)", (4, 12)), (r"(?:the\s+)?(?:one and (?:the\s+)?three|1 and 3)", (0, 8)),
    (r"(?:the\s+)?(?:one|1|downbeat)", (0,)), (r"(?:the\s+)?(?:three|3)", (8,)),
)
def when_in(text):
    """A typed line -> [{"part": layer, "when": ...}] if it says which bars a sample layer or the clip plays in:
    "rain only in the breaks", "crackle every fourth bar", "rain all the time"."""
    low = " ".join(str(text).lower().split()).strip(" .!")
    layers = "|".join(sorted((re.escape(a) for a in NAMES + list(ALIASES["clip"]) + ["sample"]), key=len, reverse=True))
    counts = {"other": 2, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4, "eighth": 8, "8th": 8, "sixteenth": 16, "16th": 16}
    head = _OPEN + r"(?:(?:play|put|keep|bring in|have)\s+)?(?:the\s+)?(" + layers + r")\s+"
    found = re.fullmatch(head + r"(?:only\s+)?(?:in|during|for)\s+(?:the\s+)?break(?:s|downs?)?", low)
    if found:
        return [{"part": part_named(found.group(1)), "when": "breaks"}]
    found = re.fullmatch(head + r"(?:only\s+)?(?:on\s+)?every\s+(other|second|2nd|third|3rd|fourth|4th|eighth|8th|sixteenth|16th|\d{1,2})(?:th|rd|nd)?\s+bars?", low)
    if found:
        return [{"part": part_named(found.group(1)), "when": counts.get(found.group(2)) or min(max(int(found.group(2)), 1), 16)}]
    found = re.fullmatch(head + r"(?:always|all the time|throughout|every bar|all the way through)", low)
    if found:
        return [{"part": part_named(found.group(1)), "when": 1}]
    return []


def clean_patch(given):
    """A knob's character, made well formed: {"mix": {kind of damage: share}, "movement", "follow", "body", "body_mix"}, or None."""
    mix = {}
    for name, share in (given.get("mix") or {}).items() if isinstance(given.get("mix"), dict) else ():
        try:
            if str(name).lower() in DAMAGE and float(share) > 0.004:
                mix[str(name).lower()] = float(share)
        except (TypeError, ValueError):
            pass
    mix = dict(sorted(mix.items(), key=lambda item: -item[1])[:4])
    if not mix:
        return None
    total = sum(mix.values())
    amount = lambda key: min(max(float(given.get(key) or 0.0), 0.0), 1.0) if isinstance(given.get(key), (int, float)) else 0.0     # noqa: E731
    return {"mix": {name: round(share / total, 3) for name, share in mix.items()}, "movement": amount("movement"), "follow": amount("follow"),
            "body": str(given.get("body")).lower() if str(given.get("body")).lower() in BODIES else "none", "body_mix": amount("body_mix")}


def another():
    """A character at random: two or three kinds of damage in some proportion, sometimes moving, sometimes ringing in something."""
    import random
    kinds = random.sample(DAMAGE, random.choice((2, 2, 3)))
    return clean_patch({"mix": {kind: random.uniform(0.2, 1.0) for kind in kinds}, "movement": random.choice((0.0, 0.0, random.uniform(0.2, 0.7))),
                        "follow": random.choice((0.0, random.uniform(0.3, 1.0))), "body": random.choice(BODIES),
                        "body_mix": random.uniform(0.2, 0.6)})


def mutate(patch):
    """A character changed a little: some of one kind of damage given to another, now and then a new kind let in or a
    small one dropped, and the movement, the following and the ringing nudged. Enough to hear, not enough to lose it."""
    import random
    patch = patch or PLAIN
    mix = dict(patch["mix"])
    if len(mix) < 2 or (len(mix) < 4 and random.random() < 0.3):                # let another kind of damage in, a little
        mix[random.choice([kind for kind in DAMAGE if kind not in mix])] = random.uniform(0.12, 0.3) * sum(mix.values())
    else:                                                                      # move some from one kind to another
        giver, taker = random.sample(list(mix), 2)
        moved = mix[giver] * random.uniform(0.2, 0.5)
        mix[giver], mix[taker] = mix[giver] - moved, mix[taker] + moved
    nudge = lambda value: min(max(value + random.uniform(-0.15, 0.15), 0.0), 1.0) if random.random() < 0.5 else value     # noqa: E731
    body = random.choice(BODIES) if random.random() < 0.15 else patch["body"]
    return clean_patch({"mix": {kind: share for kind, share in mix.items() if share > 0.05 * sum(mix.values())}, "movement": nudge(patch["movement"]),
                        "follow": nudge(patch["follow"]), "body": body, "body_mix": nudge(patch["body_mix"])})


def knob_in(text):
    """A typed line -> what it does to the knobs, or None:
        {"super": 0.4}                             "!super 40", "super filth 40"
        {"memorise": 2} / {"recall": 2}            "!memorise 2", "!recall 2", "back to 2" (slots 1 to 8)
        [{"part": "bass", "set": {"filth": 0.6}}]  "!knob bass 60", "bass knob 60", "!knobs 30" (every part)
        [{"part": "bass", "patch": ...}]           "!patch bass fold crush", "!patch bass another", or "!patch bass" and a mark
                                                   copied from the knob device (its drive becomes where the knob stands)"""
    low = " ".join(str(text).lower().split()).strip(" .!")
    found = re.fullmatch(r"!?\s*(memori[sz]e|remember|recall|back to|go back to)(?:\s+(?:as|slot|number))?\s+([1-8])", low)
    if found:
        return {"memorise" if found.group(1) in ("memorise", "memorize", "remember") else "recall": int(found.group(2))}
    number = r"(\d{1,3}(?:\.\d+)?)\s*%?"
    found = re.fullmatch(r"!?\s*(?:the\s+)?(" + _PART + r")\s+(?:vol|volume|level)(?:\s+(?:to|at))?\s+" + number, low) or re.fullmatch(
        r"!?\s*(?:vol|volume|level)\s+(?:of\s+)?(?:the\s+)?(" + _PART + r")(?:\s+(?:to|at))?\s+" + number, low)
    if found:                                            # "!vol bass 80", "bass volume 120": 100 is as it started
        return [{"part": part_named(found.group(1)), "set": {"level": min(float(found.group(2)) / 100.0, 2.5)}}]
    found = re.fullmatch(r"!?\s*duck\s+(?:the\s+)?(" + _PART + r")\s+(?:under|to|by|against|from|with|off)\s+(?:the\s+)?(" + _PART + r")(?:\s+(?:by\s+)?"
                         + number + r")?", low)
    if found:                                            # "duck the bass under the snare", "duck the rain to the kick 90"
        return [{"part": part_named(found.group(1)), "set": {"duck_by": part_named(found.group(2)),
                                                             **({"duck": min(float(found.group(3)) / 100.0, 1.0)} if found.group(3) else {})}}]
    found = re.fullmatch(r"!?\s*(?:no ducking on|do not duck|don'?t duck|stop ducking|unduck)\s+(?:the\s+)?(" + _PART + r")", low)
    if found:
        return [{"part": part_named(found.group(1)), "set": {"duck_by": "none"}}]
    found = re.fullmatch(r"!?\s*super[- ]?(?:filth|knob)?(?:\s+(?:to|at))?\s+" + number, low)
    if found:
        return {"super": min(float(found.group(1)) / 100.0, 1.0)}
    found = re.fullmatch(r"!?\s*(?:all\s+)?knobs(?:\s+(?:to|at))?\s+" + number, low)
    if found:
        return [{"part": part, "set": {"filth": min(float(found.group(1)) / 100.0, 1.0)}} for part in [p for p in PARTS if p not in LAYERS] + NAMES]
    for pattern in (r"!?\s*knob\s+(?:the\s+)?(" + _PART + r")(?:\s+(?:to|at))?\s+" + number,
                    r"!?\s*(?:the\s+)?(" + _PART + r")\s+(?:knob|filth)(?:\s+(?:to|at))?\s+" + number):
        found = re.fullmatch(pattern, low)
        if found:
            return [{"part": part_named(found.group(1)), "set": {"filth": min(float(found.group(2)) / 100.0, 1.0)}}]
    found = re.fullmatch(r"!?\s*patch\s+(?:the\s+)?(" + _PART + r")\s+(.+)", low)
    if not found:
        return None
    part, rest = part_named(found.group(1)), found.group(2)
    if rest.strip() in ("another", "new", "random", "dice", "roll"):
        return [{"part": part, "patch": another()}]
    if rest.strip() in ("mutate", "mutated", "vary", "nudge"):
        return [{"part": part, "patch": "mutate"}]
    damage = "|".join(DAMAGE)
    shares = {name: float(share) for name, share in re.findall(r"\b(" + damage + r")\s+(\d{1,3})\s*%", rest)}
    if not shares:
        shares = {name: 1.0 for name in re.findall(r"\b(" + damage + r")\b", rest)}
    value = lambda key: float(re.search(key + r"\s+(\d(?:\.\d+)?)", rest).group(1)) if re.search(key + r"\s+(\d(?:\.\d+)?)", rest) else 0.0   # noqa: E731
    body = re.search(r"\bbody\s+(" + "|".join(BODIES) + r")\s+(\d(?:\.\d+)?)", rest)
    patch = clean_patch({"mix": shares, "movement": value("movement"), "follow": value("follow"),
                         "body": body.group(1) if body else "none", "body_mix": float(body.group(2)) if body else 0.0})
    if patch is None:
        return None
    drive = re.search(r"\bdrive\s+(\d(?:\.\d+)?)", rest)
    return [{"part": part, "patch": patch}] + ([{"part": part, "set": {"filth": min(float(drive.group(1)), 1.0)}}] if drive else [])


# how a layer is cut. "next" is the next way in turn (a re-chop); "whole" is not cut at all: one sound, played from its start
CHOPS = ("transients", "sixteenths", "eighths", "beats", "bars", "finer", "coarser", "next", "whole")


def _layers(clip=False):
    return "|".join(sorted((re.escape(a) for a in NAMES + ["sample"] + (list(ALIASES["clip"]) if clip else [])), key=len, reverse=True))


def bring_in(text):
    """A typed line -> [{"part": layer, "bring": True or False}] if it brings a waiting sample layer in or takes one
    out: "bring in the rain", "rain in", "play the dust", "take out the rain", "dust out"."""
    low = " ".join(str(text).lower().split()).strip(" .!")
    name = r"(?:the\s+)?(" + _layers() + r"|clip)"            # "clip" is the newest film's sound
    for bring, patterns in ((True, (r"(?:bring in|bring on|drop in|cue|start|play|fire|launch|unleash|in with|let in|fade in)\s+" + name,
                                    r"(?:bring|drop|let|fade)\s+" + name + r"\s+(?:in|on|back in|back)", name + r"\s+(?:in|now|go|comes? in)")),
                            (False, (r"(?:take out|pull out|take off|stop|rest|hold|park|out with)\s+" + name,
                                     r"(?:take|pull|fade)\s+" + name + r"\s+(?:out|away|off)", name + r"\s+(?:out|stops?|waits?)"))):
        for pattern in patterns:
            found = re.fullmatch(_OPEN + pattern, low)
            if found:
                return [{"part": part_named(found.group(1)), "bring": bring}]
    return []


def chop_in(text):
    """A typed line -> [{"part": layer, "chop": ...}] if it says how a sample layer or the clip is cut up: "chop the
    rain on the eighths", "cut the dust into 8", "chop the clip finer", "chop the rain on its transients"."""
    low = " ".join(str(text).lower().split()).strip(" .!")
    again = re.fullmatch(_OPEN + r"(?:re-?chop|re-?cut|re-?slice)\s+(?:the\s+)?(" + _layers(clip=True) + r")", low)
    if again:                                            # "rechop the rain": cut another way
        return [{"part": part_named(again.group(1)), "chop": "next"}]
    whole = re.fullmatch(_OPEN + r"(?:un-?chop|un-?cut|unify|join up|make whole)\s+(?:the\s+)?(" + _layers(clip=True) + r")", low) or re.fullmatch(
        _OPEN + r"(?:the\s+)?(" + _layers(clip=True) + r")\s+(?:whole|as one|uncut|unchopped)", low)
    if whole:                                            # "unchop the rain", "rain whole": one sound again
        return [{"part": part_named(whole.group(1)), "chop": "whole"}]
    found = re.fullmatch(_OPEN + r"(?:re-?)?(?:chop|cut|slice)\s+(?:up\s+)?(?:the\s+)?(" + _layers(clip=True)
                         + r")\s+(?:up\s+)?(?:(?:on|at|by|into|in|to)\s+)?(?:(?:the|its|every|each)\s+)?(?:obvious\s+)?(.+)", low)
    if not found:
        return []
    how = found.group(2)
    kinds = ((r"transients?|hits?|onsets?|attacks?", "transients"), (r"(?:sixteenth|16th)s?(?: notes?)?", "sixteenths"),
             (r"(?:eighth|8th)s?(?: notes?)?", "eighths"), (r"(?:beat|quarter)s?(?: notes?)?", "beats"), (r"bars?", "bars"),
             (r"finer|smaller|tighter|more(?: pieces| slices)?", "finer"), (r"coarser|bigger|longer|looser|fewer(?: pieces| slices)?", "coarser"))
    for pattern, kind in kinds:
        if re.fullmatch(pattern, how):
            return [{"part": part_named(found.group(1)), "chop": kind}]
    count = re.fullmatch(r"(\d{1,2})(?:\s+equal)?(?:\s+(?:pieces|slices|parts|chops|bits))?", how)
    if count and 2 <= int(count.group(1)) <= 32:
        return [{"part": part_named(found.group(1)), "chop": int(count.group(1))}]
    return []


def drop_in(text):
    """A typed line -> [{"part": layer, "drop": True}] if it takes a sample layer away: "drop the rain", "get rid of the dust"."""
    low = " ".join(str(text).lower().split()).strip(" .!")
    if not NAMES:
        return []
    found = re.fullmatch(_OPEN + r"(?:drop|remove|lose|delete|bin|ditch|get rid of|throw away|unload)\s+(?:the\s+)?("
                         + "|".join(re.escape(n) for n in NAMES) + r")(?:\s+(?:layer|sample|loop))?", low)
    return [{"part": found.group(1), "drop": True}] if found else []


def steps_in(text):
    """A typed line -> [{"part": ..., "steps": [...]}] if it says where in the bar parts should play, else []."""
    low = " ".join(str(text).lower().split()).strip(" .!")
    out = []
    for clause in re.split(r"\s*(?:;|,|\band then\b|\bthen\b|\band (?=(?:the\s+)?(?:" + _PLAYED + r")\b))\s*", low):
        clause = clause.strip()
        exact = re.fullmatch(r"!?\s*(" + _PLAYED + r")\s+((?:\d{1,2}[ ,]*)+)", clause)
        if exact:
            out.append({"part": part_named(exact.group(1)), "steps": sorted({int(x) - 1 for x in re.findall(r"\d+", exact.group(2)) if 1 <= int(x) <= 16})})
            continue
        for place, steps in PLACES:
            found = re.fullmatch(_OPEN + r"(?:(?:put|play|keep|move|have)\s+)?(?:the\s+)?(" + _PLAYED + r")\s+(?:only\s+)?on\s+" + place, clause)
            if found:
                out.append({"part": part_named(found.group(1)), "steps": list(steps)})
                break
        else:
            return []
    return out


set_names([])
