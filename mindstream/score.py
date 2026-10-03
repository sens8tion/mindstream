"""The words of a musical score: styles, keys, and what a typed steer means for the music straight away.
No numpy here, so the story feed can use it; the sound itself is made in groove.py."""
import re

NOTES = {"c": 0, "c#": 1, "db": 1, "d": 2, "d#": 3, "eb": 3, "e": 4, "f": 5, "f#": 6, "gb": 6, "g": 7, "g#": 8,
         "ab": 8, "a": 9, "a#": 10, "bb": 10, "b": 11}
STYLE_NAMES = ("four", "twostep", "broken", "dnb", "half", "none")
STYLE_ALIASES = {"jungle": "dnb", "2step": "twostep", "2-step": "twostep", "garage": "twostep", "house": "four", "techno": "four",
                 "breaks": "broken", "syncopated": "broken", "halftime": "half", "ambient": "none", "off": "none",
                 "jungle": "dnb"}
SCORE_RANGES = {"swing": (0.0, 0.5), "sub": (0.0, 1.0), "twinkle": (0.0, 1.0)}


def parse_key(text):
    """'A minor', 'F#m', 'Cmaj', 'D dorian', 'Eb phrygian' -> ('f#', 'minor'), or None."""
    found = re.fullmatch(r"\s*([a-gA-G][#b]?)\s*[-_ ]?\s*(minor|min|m|major|maj|dorian|dor|phrygian|phr)?\s*", str(text), re.I)
    if not found or found.group(1).lower() not in NOTES:
        return None
    word = (found.group(2) or "minor").lower()
    return found.group(1).lower(), {"min": "minor", "m": "minor", "maj": "major", "dor": "dorian", "phr": "phrygian"}.get(word, word)


def key_name(key):
    return f"{key[0].capitalize()} {key[1]}"


# the composer's own archetypes can be asked for by name; without the composer they are ignored
ARCHETYPE_NAMES = ("half_step", "two_step", "four_on_the_floor", "rolling", "shuffled_two_step", "stutter", "amen",
                   "breakbeat_hardcore", "happy_hardcore", "gabber")
ARCHETYPE_ALIASES = {"shuffle": "shuffled_two_step", "breakbeat": "breakbeat_hardcore", "happy": "happy_hardcore"}


def style_name(text):
    word = str(text).strip().lower()
    word = STYLE_ALIASES.get(word, word)
    if word in STYLE_NAMES:
        return word
    word = ARCHETYPE_ALIASES.get(word.replace("-", "_"), word.replace("-", "_"))
    return word if word in ARCHETYPE_NAMES else None


def clean_score(raw):
    """Keep only known music settings, in their ranges."""
    score = {}
    if style_name(raw.get("style", "")):
        score["style"] = style_name(raw["style"])
    key = parse_key(raw["key"]) if raw.get("key") else None
    if key:
        score["key"] = key_name(key)
    for name, (low, high) in SCORE_RANGES.items():
        try:
            score[name] = round(min(max(float(raw[name]), low), high), 3)
        except (KeyError, TypeError, ValueError):
            pass
    if str(raw.get("rescore", "")).lower() in ("true", "1", "yes", "now"):
        score["rescore"] = True
    try:
        if float(raw.get("break", 0)) >= 1:
            score["break"] = int(min(float(raw["break"]), 32))        # bars with the drums and bass out
    except (TypeError, ValueError):
        pass
    return score


ARCHETYPE_WORDS = {"half_step": "half-step: kick on one and three, steady eighth hats",
                   "two_step": "2-step: a kick that skips the two, an open hat before the bar turns",
                   "shuffled_two_step": "shuffled 2-step: the kick and hats pushed off the grid",
                   "stutter": "stutter: a doubled, tripping kick under a wall of hats", "rolling": "rolling: four kicks that lean into the bar",
                   "breakbeat_hardcore": "breakbeat hardcore: a busy break with three snares",
                   "amen": "the amen: the break every jungle record is cut from",
                   "four_on_the_floor": "four on the floor, open hats between the kicks",
                   "happy_hardcore": "happy hardcore: four on the floor with open hats on the backbeat",
                   "gabber": "gabber: a kick on every sixteenth"}
STYLE_WORDS = {"four": "a steady four-on-the-floor kick", "twostep": "a skipping 2-step", "broken": "a syncopated broken beat",
               "dnb": "a fast drum-and-bass break", "half": "a slow, heavy half-time", "none": "no drums"}
MOOD_WORDS = {"minor": "sorrow", "major": "brightness", "dorian": "warmth", "phrygian": "dread"}


def differs(before, value, name=""):
    """Has this setting really moved?"""
    if isinstance(value, (int, float)) and not isinstance(value, bool) and isinstance(before, (int, float)):
        return abs(float(value) - float(before)) > (1.0 if name == "bpm" else 0.12)
    return before != value


def describe(change, before=None):
    """Settings -> what a person would hear and see, as short phrases, the music first."""
    before, parts = before or {}, []
    was = lambda name, default: float(before.get(name, default))      # noqa: E731
    if "break" in change:
        parts.append(f"the low end drops away for {int(change['break'])} bars while the drums run on, then comes back")
    if "style" in change:
        parts.append("the drums stop" if change["style"] == "none"
                     else f"the drums switch to {STYLE_WORDS.get(change['style']) or ARCHETYPE_WORDS.get(change['style']) or change['style'].replace('_', ' ')}")
    if "bpm" in change and differs(before.get("bpm"), change["bpm"], "bpm"):
        parts.append(f"the tempo {'rises' if change['bpm'] > was('bpm', 0) else 'falls'} to {change['bpm']:.0f}")
    if "key" in change:
        mood = MOOD_WORDS.get(str(change["key"]).split()[-1])
        parts.append(f"the key turns to {change['key']}" + (f" ({mood})" if mood else ""))
    if "chaos" in change and differs(was("chaos", 1.0), change["chaos"]):
        parts.append("everything gets fuller and wilder" if change["chaos"] > was("chaos", 1.0) else "everything thins out and calms")
    if "sub" in change and differs(was("sub", 0.8), change["sub"]):
        parts.append("more sub bass" if change["sub"] > was("sub", 0.8) else "less sub bass")
    if "twinkle" in change and differs(was("twinkle", 0.3), change["twinkle"]):
        parts.append("the bells stop" if change["twinkle"] < 0.03 else "more bells" if change["twinkle"] > was("twinkle", 0.3) else "fewer bells")
    if "swing" in change:
        parts.append("the off-beats swing" if change["swing"] > 0.15 else "the rhythm straightens")
    if change.get("rescore"):
        parts.append("new riffs")
    if "shape" in change and change["shape"] != "any":
        parts.append(f"the picture wraps a {'ring' if change['shape'] == 'torus' else change['shape']}")
    if "folds" in change:
        parts.append("the mirrors go" if change["folds"] < 0.5 else "a few mirrors" if change["folds"] <= 4 else "it shatters into mirrors")
    if "trails" in change:
        parts.append("long smeared trails" if change["trails"] >= 0.6 else "short, crisp trails")
    if "swarm" in change:
        parts.append("earlier pictures crowd in" if change["swarm"] >= 0.5 else "the picture is left alone")
    if "spin" in change and differs(was("spin", 1.0), change["spin"]):
        parts.append("it spins faster" if change["spin"] > was("spin", 1.0) else "it turns more slowly")
    if "tint" in change:
        parts.append("the light changes colour")
    if "cadence" in change:
        parts.append(f"a new picture every {change['cadence']:g} seconds" if change["cadence"] else "new pictures only when the story moves on")
    return parts


# What plain words in a steer mean, applied the moment they are typed (llama's own reading follows a beat later).
WORDS = (
    (r"\b(2|two)[ -]?step\b|\bgarage\b", {"style": "twostep"}),
    (r"\bfour (on|to) the floor\b|\bon[ -](the[ -])?beat\b|\bhouse\b|\btechno\b", {"style": "four"}),
    (r"\bsyncopat\w*|\bbroken[ -]?beat\b|\bbreak ?beats?\b|\bbreaks\b", {"style": "broken"}),
    (r"\bdrum (and|n|&) bass\b|\bdnb\b|\bd&b\b|\bjungle\b", {"style": "dnb"}),
    (r"\bhalf[ -]?time\b|\btrap\b|\bdub\b", {"style": "half"}),
    (r"\bno drums\b|\bdrumless\b|\bbeatless\b|\bambient\b|\bdrop the (drums|beat)\b", {"style": "none"}),
    (r"\bdark(er)?\b|\bmenac\w*|\bsinister\b|\bdread\b", {"mode": "phrygian"}),
    (r"\bsad(der)?\b|\bmelanchol\w*|\bmournful\b", {"mode": "minor"}),
    (r"\bhapp(y|ier)\b|\bbright(er)?\b|\buplift\w*|\beuphori\w*|\bjoy\w*", {"mode": "major"}),
    (r"\bsoulful\b|\bwarm(er)?\b|\bdorian\b", {"mode": "dorian"}),
    (r"\btwinkl\w*|\bsparkl\w*|\bbells?\b|\bglitter\w*|\bshimmer\w*", {"twinkle": 0.9}),
    (r"\b(no|less) (twinkl\w*|bells?|sparkl\w*)", {"twinkle": 0.0}),
    (r"\b(more|heavy|heavier|deep|deeper|big|bigger|huge) (sub|bass)\b", {"sub": 1.0}),
    (r"\b(no|less) (sub|bass)\b", {"sub": 0.15}),
    (r"\bswing\w*|\bshuffl\w*", {"swing": 0.3}),
    (r"\bstraight\b", {"swing": 0.0}),
    (r"\bgentl\w*|\bcalm(er)?\b|\bsoft(er|ly)?\b|\bquiet(er|ly)?\b|\bstrip (it )?(back|down)\b", {"chaos": 0.4}),
    (r"\bhard(er)?\b|\bintense\b|\bheav(y|ier)\b|\bwild(er)?\b|\bfrantic\b|\bbuild\b", {"chaos": 1.6}),
    (r"\bamen\b", {"style": "amen"}), (r"\brolling\b|\broller\b", {"style": "rolling"}), (r"\bstutter\w*", {"style": "stutter"}),
    (r"\bgabber\b", {"style": "gabber"}), (r"\bhappy hardcore\b", {"style": "happy_hardcore"}),
    (r"\bshuffled? (2|two)[ -]?step\b", {"style": "shuffled_two_step"}), (r"\bhalf[ -]?step\b", {"style": "half_step"}),
    (r"\bbreakbeat hardcore\b|\bhardcore breaks?\b", {"style": "breakbeat_hardcore"}),
    (r"\bmore (chaotic|chaos|manic|frantic|hectic)\b", {"chaos": 1.6}),
    (r"\bless (chaotic|chaos|busy|manic|frantic|intense|hectic|wild)\b|\b(tone|calm|settle) it down\b", {"chaos": 0.4}),
    (r"\bshatter\w*|\bkaleidoscop\w*|\bfractur\w*", {"folds": 8.0}),
    (r"\blong break\w*|\bbig break\w*", {"break": 8}),
    (r"\brescore\b|\bnew (tune|music|score|riff|melody)\b|\b(change|different) (the )?(tune|music|score)\b", {"rescore": True}),
)


def score_from_words(text, bpm, key):
    """A steer typed by the viewer -> the changes it asks of the music (and of `chaos`), given the tempo and
    (note, mode) now. Empty if it says nothing about music."""
    low, out = text.lower(), {}
    for pattern, change in WORDS:
        if re.search(pattern, low):
            out.update(change)
    if re.search(r"\b(photos?|pictures?|images?)\b", low):          # how often pictures come: handled by the caller
        if re.search(r"\bslow\w*|\bfewer\b|\bless\b|\bcalm\w*", low):
            out["pictures"] = "slower"
        elif re.search(r"\bfast\w*|\bmore\b|\bquick\w*|\bspeed\b", low):
            out["pictures"] = "faster"
    if "break" not in out and re.search(r"\bbreak ?down\b|\ba break\b|\bbreak it\b|\bdrop out\b", low):
        out["break"] = 4
    said = re.search(r"\b(\d{2,3})\s*bpm\b", low)
    if said:
        out["bpm"] = float(min(max(int(said.group(1)), 40), 300))
    elif re.search(r"\b(much|a lot|way) (faster|quicker)\b|\bdouble( |-)?time\b", low):
        out["bpm"] = min(bpm * 1.3, 300.0)
    elif re.search(r"\bfaster\b|\bquicker\b|\bspeed (it )?up\b|\bpick (it )?up\b", low):
        out["bpm"] = min(bpm * 1.12, 300.0)
    elif re.search(r"\b(much|a lot|way) slower\b", low):
        out["bpm"] = max(bpm * 0.75, 40.0)
    elif re.search(r"\bslower\b|\bslow (it )?down\b|\bslowly\b", low):
        out["bpm"] = max(bpm * 0.88, 40.0)
    elif out.get("style") == "dnb" and bpm < 160:
        out["bpm"] = 172.0                                    # drum and bass is a tempo as much as a pattern
    named = re.search(r"\bin ([a-g][#b]?)[ -]?(minor|major|dorian|phrygian)\b", low)
    if named:
        out["key"] = key_name((named.group(1), named.group(2)))
        out.pop("mode", None)
    elif "mode" in out:
        out["key"] = key_name((key[0], out.pop("mode")))
    if "bpm" in out:
        out["bpm"] = round(out["bpm"], 1)
    if ("style" in out or "key" in out) and (out.get("key") != key_name(key) or "style" in out):
        out["rescore"] = True                                 # a new style or key gets new riffs to go with it
    return out
