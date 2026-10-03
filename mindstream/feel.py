"""The canon of feel: the words for how heavy dance music takes hold of someone, fixed so they can be a control pad.

Nine feels. Each is one kind of engagement, and each has an INVERSE: its opposite pole, with words of its own.
A feel stands on a rung from -4 (deep in its inverse) through 0 (not in play) to 5 (as far as it goes), and every
rung has one canonical word. Other words people use are aliases of a rung. Nothing here is a matter of taste at
run time: a word is in the canon, with one meaning, or it is not a feel word.

Inversion does three jobs in this vocabulary, and the canon fixes all three:

1. INVERTED PRAISE. On the dirty side a word that would be a complaint anywhere else asks for MORE. "filthy",
   "disgusting", "punishing", "sick": none of them is ever read as a complaint.
2. THE INVERSE POLE. To have less you say "less", "too", or use the other pole's words: "cleaner", "gentler",
   "no menace". The inverse is not weakness. It is the breakdown, the held breath, what the drop is measured against.
3. THE FLIP. "invert menace" swaps a feel for its inverse at the same depth; "invert" alone flips the whole pad,
   and again brings it back. That is the breakdown and the drop as one move.

`read` turns a typed line (or a pad press, which sends the same words) into moves on a state; `render` says what
a state asks of the engine, in the engine's own terms. No numpy here, and nothing outside this file is needed.
"""
import re

RUNGS_UP, RUNGS_DOWN = 5, 4

# name: (who is listening,
#        the rungs of the feel, mild to extreme,       aliases of each rung,
#        the inverse's name, its rungs mild to extreme, aliases of each of those,
#        nouns for the feel, nouns for the inverse)
CANON = {
    "weight": ("Felt in the chest, not heard in the ears.",
               ("solid", "heavy", "thick", "crushing", "tectonic"),
               (("grounded", "sturdy"), ("weighty", "subby", "fat", "deep"), ("dense", "swollen", "massive", "leaden"),
                ("chest-rattling", "colossal", "monolithic"), ("seismic", "planetary")),
               "weightless", ("light", "airy", "floating", "weightless"),
               (("lean", "slim"), ("thin", "hollow", "breezy"), ("buoyant", "drifting", "hovering"), ("featherlight", "zero-gravity")),
               ("weight", "heft", "pressure", "bottom end", "low end"), ("lightness", "air")),
    "violence": ("Taking a beating and wanting more.",
                 ("hard", "bruising", "punishing", "brutal", "merciless"),
                 (("banging", "slamming", "pounding"), ("battering", "hammering", "thumping"), ("pummelling", "pummeling", "savage", "vicious"),
                  ("ferocious", "barbaric", "murderous"), ("annihilating", "obliterating", "pitiless")),
                 "tender", ("soft", "gentle", "tender", "caressing"),
                 (("easy", "mild"), ("kind", "light-handed"), ("soothing", "delicate"), ("cradling", "stroking")),
                 ("violence", "aggression", "punishment", "force"), ("tenderness", "gentleness")),
    "grit": ("The surface of the sound itself: dry, mineral, damaged.",
             ("rough", "gritty", "abrasive", "corroded", "blown-out"),
             (("raw", "coarse", "lo-fi"), ("crunchy", "fuzzy", "distorted", "grainy"), ("serrated", "harsh", "metallic", "industrial", "rasping"),
              ("rusty", "scorched", "eroded"), ("shredded", "destroyed", "pulverised", "pulverized")),
             "polish", ("smooth", "silky", "polished", "glassy"),
             (("even", "rounded"), ("sleek", "velvet", "satin"), ("glossy", "hi-fi", "lacquered"), ("crystalline", "mirror-finished")),
             ("grit", "dirt", "crunch", "distortion", "texture"), ("polish", "sheen", "gloss")),
    "menace": ("Unease: something is coming.",
               ("uneasy", "brooding", "ominous", "sinister", "dread"),
               (("moody", "shadowy", "dark", "cold"), ("looming", "bleak", "murky", "haunted"), ("menacing", "threatening", "paranoid", "cavernous"),
                ("evil", "claustrophobic", "dystopian", "malevolent"), ("dreadful", "doom-laden", "apocalyptic", "nightmarish")),
               "safe", ("calm", "warm", "friendly", "safe"),
               (("settled", "untroubled"), ("cosy", "cozy", "comforting"), ("sunny", "benign", "welcoming"), ("sheltered", "innocent")),
               ("menace", "dread", "threat", "darkness", "doom"), ("safety", "warmth", "comfort")),
    "lock": ("Hypnotised: no longer counting bars.",
             ("steady", "rolling", "driving", "hypnotic", "relentless"),
             (("even-paced", "constant"), ("chugging", "cruising", "motoring"), ("grinding", "insistent", "motorik", "locked"),
              ("mesmeric", "tunnelling", "tunneling", "trance-like", "locked in"), ("unrelenting", "endless", "unstoppable", "remorseless")),
             "restless", ("loose", "shifting", "restless", "scattered"),
             (("relaxed", "slack"), ("wandering", "changing"), ("fidgety", "twitchy", "skittish"), ("broken", "fractured", "all over the place")),
             ("lock", "hypnosis", "roll", "drive", "the groove"), ("restlessness", "variation")),
    "release": ("The drop as catharsis: hands up, eyes shut.",
                ("lifting", "rushing", "euphoric", "ecstatic", "rapturous"),
                (("uplifting", "rising", "hopeful"), ("soaring", "surging", "swelling"), ("cathartic", "blissful", "elated", "purging"),
                 ("delirious", "tearful", "overwhelming"), ("transcendent", "heavenly", "religious")),
                "tension", ("held", "tense", "coiled", "unbearable"),
                (("waiting", "suspended"), ("taut", "withheld", "on edge", "teasing"), ("clenched", "wound up", "straining"),
                 ("agonising", "agonizing", "excruciating")),
                ("release", "euphoria", "lift", "catharsis", "the rush"), ("tension", "suspense", "the wait")),
    "filth": ("Disgust as praise: the bass face.",
              ("dirty", "grimy", "filthy", "dutty", "rancid"),
              (("mucky", "grubby", "naughty-sounding"), ("grotty", "greasy", "slimy", "sleazy-sounding"), ("nasty", "disgusting", "gross", "foul", "minging"),
               ("rank", "stinking", "vile", "rotten"), ("putrid", "revolting", "septic", "unholy")),
              "clean", ("decent", "clean", "tasteful", "pristine"),
              (("tidy", "polite"), ("proper-sounding", "wholesome", "fresh"), ("refined", "elegant", "classy"), ("spotless", "immaculate", "hygienic")),
              ("filth", "stank", "stink", "muck", "nastiness"), ("cleanliness", "taste", "hygiene")),
    "swagger": ("Grinning: mischief and attitude.",
                ("cheeky", "naughty", "rude", "sleazy", "lairy"),
                (("playful", "bouncy", "jaunty"), ("saucy", "cocky", "wonky", "slinky"), ("swaggering", "strutting", "bolshy"),
                 ("louche", "lewd", "seedy"), ("shameless", "outrageous-sounding", "gobby")),
                "earnest", ("plain", "straight", "earnest", "solemn"),
                (("simple", "modest"), ("sober", "sincere"), ("serious", "stiff"), ("po-faced", "grave", "austere")),
                ("swagger", "attitude", "cheek", "mischief", "sleaze"), ("earnestness", "sincerity")),
    "derangement": ("Losing the plot on purpose.",
                    ("odd", "twisted", "unhinged", "feral", "demented"),
                    (("strange", "skewed", "off"), ("warped", "bent", "mangled"), ("mental", "manic", "frenzied", "wild", "chaotic"),
                     ("rabid", "berserk", "crazed", "deranged"), ("psychotic", "insane", "possessed")),
                    "composed", ("sane", "orderly", "composed", "disciplined"),
                    (("sensible", "level"), ("neat", "measured"), ("controlled", "rational"), ("regimented", "clinical")),
                    ("derangement", "madness", "chaos", "mayhem", "insanity"), ("composure", "order", "sanity")),
}
FEELS = tuple(CANON)

# The pad: three rows of three. The body, the head, the attitude.
PAD = (("weight", "violence", "grit"), ("menace", "lock", "release"), ("filth", "swagger", "derangement"))

# Praise by insult with no feel of its own: it pushes whichever feel was last touched one rung further.
PRAISE = ("sick", "wicked", "ill", "bad", "stupid", "silly", "ridiculous", "ignorant", "criminal", "illegal", "obscene", "offensive",
          "wrong", "outrageous", "absurd", "dumb", "daft", "shocking", "unreasonable", "uncalled for", "a disgrace", "disgraceful")
STRONGER = ("really", "very", "proper", "properly", "absolutely", "utterly", "totally", "well", "dead", "way", "much", "far", "even",
            "a lot", "so", "bloody", "fucking", "seriously", "completely")
SLIGHTER = ("a bit", "a little", "a touch", "slightly", "somewhat", "a tad", "kind of", "sort of")


def _comparative(word):
    """"filthy" -> "filthier", "rude" -> "ruder", "grim" -> "grimmer", "hard" -> "harder"."""
    if " " in word or "-" in word or len(word) > 9:
        return None
    if word.endswith("y") and len(word) > 2 and word[-2] not in "aeiou":
        return word[:-1] + "ier"
    if word.endswith("e"):
        return word + "r"
    if len(word) <= 4 and re.fullmatch(r"[a-z]*[^aeiou][aeiou][^aeiouwxy]", word):
        return word + word[-1] + "er"
    return word + "er"


def _build():
    words, nouns = {}, {}
    for feel, (_, up, up_alias, inverse, down, down_alias, noun_up, noun_down) in CANON.items():
        for sign, ladder, aliases in ((1, up, up_alias), (-1, down, down_alias)):
            for i, word in enumerate(ladder):
                for w in (word,) + tuple(aliases[i]):
                    assert w not in words, f"{w!r} is in the canon twice"
                    words[w] = (feel, sign * (i + 1))
        for sign, group in ((1, noun_up + (feel,)), (-1, noun_down + (inverse,))):
            for n in dict.fromkeys(group):
                assert nouns.get(n, (feel, sign)) == (feel, sign), f"{n!r} names two things"
                nouns[n] = (feel, sign)
    comparatives = {}
    for word, (feel, rung) in words.items():
        more = _comparative(word)
        if more and more not in words and more not in comparatives:
            comparatives[more] = (feel, 1 if rung > 0 else -1)
    return words, nouns, comparatives


WORDS, NOUNS, COMPARATIVES = _build()     # word -> (feel, rung); noun -> (feel, sign); "filthier" -> (feel, sign)


def fresh():
    """A pad with nothing in play."""
    return {**{feel: 0.0 for feel in FEELS}, "last": None}


def clamp(rung):
    return min(max(float(rung), -RUNGS_DOWN), RUNGS_UP)


def word_for(feel, rung):
    """The canonical word for where a feel stands: "filthy", "pristine", or "" when it is not in play."""
    step = int(round(abs(rung)))
    if step == 0:
        return ""
    return CANON[feel][1][min(step, RUNGS_UP) - 1] if rung > 0 else CANON[feel][4][min(step, RUNGS_DOWN) - 1]


def amount(rung):
    """A rung as -1 .. 1: how far toward the feel's extreme, or its inverse's."""
    return rung / RUNGS_UP if rung >= 0 else rung / RUNGS_DOWN


def _alternation(words):
    return "|".join(sorted((re.escape(w) for w in words), key=len, reverse=True))


_OPEN = (r"^(?:(?:please|now|ok|okay|and|then|just|go|get|make it|make this|make that|keep it|i want it|it'?s|that'?s|that is|this is|"
         r"oh that'?s|give me|give it|let'?s have|let'?s go)[ ,]+)*")
_HOW = r"((?:(?:" + _alternation(STRONGER + SLIGHTER) + r")\s+)*)"
_ADJ, _NOUN, _COMP, _PRAISE = (_alternation(x) for x in (WORDS, NOUNS, COMPARATIVES, PRAISE))


def _clause(clause, state):
    """One clause -> (feel, new rung) or ("*", None) for a flip of the whole pad, or None if it is not feel talk."""
    exact = re.fullmatch(r"!?\s*(" + _NOUN + r")\s+(-?\d)", clause)
    if exact:                                                   # "!filth 3", "menace -2"
        feel, sign = NOUNS[exact.group(1)]
        return feel, clamp(sign * int(exact.group(2)))
    flip = re.fullmatch(r"!?\s*(?:invert|flip|reverse)(?:\s+(?:it|all|everything|the lot|the pad|the whole thing))?", clause)
    if flip:
        return "*", None
    flip = re.fullmatch(r"!?\s*(?:invert|flip|reverse)\s+(?:the\s+)?(" + _NOUN + "|" + _ADJ + r")", clause)
    if flip:
        feel = (NOUNS.get(flip.group(1)) or WORDS[flip.group(1)])[0]
        return feel, -state[feel] if state[feel] > 0 else clamp(-state[feel])
    found = re.fullmatch(r"!?\s*(more|less|no|not|too|too much|less of the|more of the|not so|not as)?\s*" + _HOW
                         + r"(?:(" + _ADJ + r")|(" + _COMP + r")|(" + _NOUN + r")|(" + _PRAISE + r"))", clause)
    if not found:
        return None
    lead, how, adjective, comparative, noun, praise = found.groups()
    how = " " + " ".join(how.split()) + " "
    step = 1.0 + (1.0 if any(f" {w} " in how for w in STRONGER) else 0.0) - (0.5 if any(f" {w} " in how for w in SLIGHTER) else 0.0)
    if praise:                                                  # "sick", "that's just wrong": more of whatever was last touched
        feel = state.get("last") or max(FEELS, key=lambda f: abs(state[f]))
        if lead or state[feel] == 0 and not state.get("last"):
            return None
        return feel, clamp(state[feel] + step * (1 if state[feel] >= 0 else -1))
    feel, rung = WORDS[adjective] if adjective else (COMPARATIVES.get(comparative) or NOUNS[noun])
    sign = 1 if rung > 0 else -1
    now = state[feel]
    if lead == "no":                                            # "no menace": out of play
        return feel, 0.0
    if lead in ("not", "not so", "not as"):                     # "not filthy": the first rung of the other pole
        return feel, clamp(-sign) if now * sign >= 0 else now
    if lead in ("less", "too", "too much", "less of the"):      # "less menace", "too filthy": a rung back toward the other pole
        return feel, clamp(now - sign * step)
    if adjective and lead is None:                              # "filthy": to that rung; said again when already there, a rung further
        target = rung + sign * (step - 1.0)
        return feel, clamp(target if now * sign < abs(target) else now + sign)
    return feel, clamp(now + sign * step)                       # "filthier", "more filth", "more menace"


def read(text, state):
    """A typed line -> the moves it makes, [(feel, new rung)], or [] if the line is not wholly feel talk (a line of
    story that merely contains such words is left alone). The state is not changed; see `move`."""
    low = re.sub(_OPEN, "", " ".join(str(text).lower().split()).strip(" .!?"))
    if not low:
        return []
    moves, trial = [], dict(state)
    for clause in re.split(r"\s*(?:,|;|\band\b|\bbut\b|\bthen\b|&)\s*", low):
        got = _clause(clause.strip(), trial) if clause.strip() else None
        if got is None:
            return []
        for feel, rung in ([(f, clamp(-trial[f])) for f in FEELS if trial[f]] if got[0] == "*" else [got]):
            trial[feel], trial["last"] = rung, feel
            moves.append((feel, rung))
    return moves


def move(state, text):
    """Apply a typed line to a state. Returns what changed as phrases ("filth: filthy (3)"), or [] if it was not feel talk."""
    said = []
    for feel, rung in read(text, state):
        state[feel], state["last"] = rung, feel
        said.append(f"{feel}: {word_for(feel, rung) or 'out of play'} ({rung:+g})")
    return said


def summary(state):
    """Where the pad stands, in its own words: "filthy, ominous, weightless"."""
    return ", ".join(word_for(f, state[f]) for f in sorted(FEELS, key=lambda f: -abs(state[f])) if word_for(f, state[f]))


# ---------------------------------------------------------------------------------------------------------------
# What each feel asks of the engine, as offsets on top of whatever is set: (where, what, how much at the extreme).
# "where" is a part of the rhythm section, "layers" (every film's sound and pulled sample), "score" or "look".
# An amount is scaled by how far the feel stands (-1 .. 1), so the inverse pole pulls the other way. SWITCHES come
# on only past a threshold. This is the canon's side of the bargain; the engine applies it.

OFFSETS = {
    "weight": (("sub", "level", 0.7), ("sub", "length", 0.6), ("kick", "length", 0.5), ("kick", "tone", -0.3), ("bass", "tone", -0.3),
               ("score", "sub", 0.3)),
    "violence": (("kick", "punch", 0.7), ("kick", "drive", 0.3), ("kick", "level", 0.3), ("snare", "punch", 0.6), ("snare", "level", 0.25),
                 ("hats", "length", -0.2), ("score", "energy", 0.3)),
    "grit": (("bass", "drive", 0.5), ("tune", "drive", 0.4), ("snare", "drive", 0.3), ("hats", "drive", 0.3), ("layers", "drive", 0.4),
             ("hats", "tone", 0.2)),
    "menace": (("tune", "tone", -0.5), ("drones", "tone", -0.4), ("drones", "level", 0.4), ("bells", "level", -0.5), ("snare", "room", 0.4),
               ("tune", "room", 0.3), ("layers", "room", 0.3), ("score", "twinkle", -0.3), ("look", "trails", 0.15)),
    "lock": (("layers", "density", -0.2), ("score", "swing", -0.2), ("score", "twinkle", -0.2), ("hats", "level", 0.2), ("look", "calm", 0.3)),
    "release": (("tune", "level", 0.3), ("tune", "tone", 0.3), ("bells", "level", 0.4), ("drones", "room", 0.3), ("score", "twinkle", 0.4),
                ("sub", "level", 0.2), ("look", "chaos", 0.4)),
    "filth": (("bass", "drive", 0.4), ("bass", "tone", -0.2), ("sub", "drive", 0.25), ("layers", "pitch", -3.0), ("tune", "pitch", -1.0)),
    "swagger": (("score", "swing", 0.3), ("bass", "length", -0.3), ("hats", "level", -0.15), ("snare", "length", 0.2)),
    "derangement": (("layers", "density", 0.5), ("look", "chaos", 0.6), ("look", "spin", 0.4), ("tune", "pitch", 2.0)),
}
# (feel, past this amount, where, what comes on)
SWITCHES = (
    ("grit", 0.6, "tune", {"add_fx": {"type": "crush", "bits": 6, "rate": 0.3}}),
    ("grit", 0.8, "layers", {"add_fx": {"type": "crush", "bits": 5, "rate": 0.25}}),
    ("menace", 0.4, "score", {"mode": "minor"}),
    ("menace", -0.5, "score", {"mode": "major"}),
    ("lock", 0.6, "layers", {"vary": False}),                 # the same phrase, again and again
    ("lock", -0.5, "layers", {"vary": True}),                 # a new phrase every time
    ("release", 0.6, "tune", {"set": {"octave": 1}}),
    ("release", -0.5, "all", {"add_fx": {"type": "filter", "kind": "high", "freq": 400, "q": 0.3}}),      # tension: the floor taken away
    ("release", -0.75, "kick", {"set": {"on": False}}),
    ("filth", 0.4, "bass", {"add_fx": {"type": "sweep", "from": 2400, "to": 180, "time": "1/8"}}),
    ("filth", 0.4, "bass", {"add_fx": {"type": "filter", "kind": "low", "freq": 900, "q": 0.8}}),
    ("filth", 0.8, "bass", {"add_fx": {"type": "chorus", "depth": 0.8, "mix": 0.5}}),
    ("swagger", 0.6, "score", {"style": "two_step"}),
    ("derangement", 0.4, "layers", {"chop": "finer"}),
    ("derangement", 0.6, "layers", {"add_fx": {"type": "reverse"}}),
    ("derangement", 0.8, "tune", {"add_fx": {"type": "tremolo", "time": "1/16", "depth": 0.8}}),
)


def render(state):
    """What a state asks of the engine: ({(where, what): offset}, [(where, what comes on)])."""
    offsets, on = {}, []
    for feel in FEELS:
        a = amount(state[feel])
        if not a:
            continue
        for where, what, most in OFFSETS[feel]:
            offsets[(where, what)] = round(offsets.get((where, what), 0.0) + a * most, 3)
        on += [(where, thing) for f, past, where, thing in SWITCHES if f == feel and (a >= past if past > 0 else a <= past)]
    return offsets, on


def document():
    """The canon as a page to read (FEEL.md is this, written out)."""
    out = ["# The canon of feel", "",
           "The words for how heavy dance music takes hold of someone, fixed so they can be a control pad. This page is",
           "written out from `mindstream/feel.py` (`python -m mindstream.feel > FEEL.md`); change the canon there, not here.", "",
           "Where it stands: the words, the rungs, how a line is read and what each feel asks of the engine are fixed here.",
           "The engine does not act on them yet, and there is no pad on screen yet.", "",
           "## Inversion", "",
           "1. **Inverted praise.** On the dirty side, a word that would be a complaint anywhere else asks for *more*.",
           "   \"filthy\", \"disgusting\", \"punishing\", \"sick\": none is ever read as a complaint.",
           "2. **The inverse pole.** Every feel has an opposite with words of its own. To have less, say \"less\" or \"too\",",
           "   or use the other pole: \"cleaner\", \"gentler\", \"no menace\". The inverse is not weakness: it is the breakdown,",
           "   the held breath, what the drop is measured against.",
           "3. **The flip.** \"invert menace\" swaps a feel for its inverse at the same depth. \"invert\" alone flips the whole",
           "   pad, and again brings it back: the breakdown and the drop as one move.", "",
           "## The pad", "", "| | | |", "|---|---|---|"]
    out += ["| " + " | ".join(f"**{f}** / {CANON[f][3]}" for f in row) + " |" for row in PAD]
    out += ["", "Rows: the body, the head, the attitude. Each pad stands on a rung from -4 (deep in its inverse) through 0 (not in",
            "play) to 5. A press is a rung up; the inverse is a rung down; invert flips the sign.", ""]
    for feel in FEELS:
        who, up, up_alias, inverse, down, down_alias, noun_up, noun_down = CANON[feel]
        out += [f"## {feel} / {inverse}", "", who, "", "| Rung | Word | Also |", "|---|---|---|"]
        out += [f"| +{i + 1} | **{w}** | {', '.join(up_alias[i])} |" for i, w in reversed(list(enumerate(up)))]
        out += ["| 0 | | not in play |"]
        out += [f"| -{i + 1} | **{w}** | {', '.join(down_alias[i])} |" for i, w in enumerate(down)]
        out += ["", f"Nouns: {', '.join(dict.fromkeys(noun_up + (feel,)))}; for the inverse, {', '.join(dict.fromkeys(noun_down + (inverse,)))}.", "",
                "Asks of the engine, at the extreme: " + "; ".join(f"{where} {what} {most:+g}" for where, what, most in OFFSETS[feel]) + ".",
                *[f"Past {abs(past):g} toward {'the feel' if past > 0 else 'the inverse'}: {where} "
                  + ", ".join(f"{k} {v}" for k, v in thing.items()) + "." for f, past, where, thing in SWITCHES if f == feel], ""]
    out += ["## Praise by insult", "",
            "These have no feel of their own. Said alone, they push whichever feel was last touched one rung further:", "",
            ", ".join(PRAISE) + ".", "",
            "## Saying it", "",
            "    filthy                    to that rung; said again when already there, a rung further",
            "    filthier / more filth     a rung up",
            "    proper filthy             a rung further than the word (also: really, very, absolutely, well, dead ...)",
            "    a bit filthier            half a rung",
            "    less filth / too filthy   a rung back toward clean",
            "    cleaner / pristine        the inverse pole, by its own words",
            "    not filthy                the first rung of the inverse",
            "    no filth                  out of play",
            "    invert filth              the same depth, the other pole",
            "    invert                    the whole pad",
            "    !filth 3 / !menace -2     an exact rung",
            "    filthier and heavier, less swagger       several at once", "",
            "A line is feel talk only if every part of it is. A line of story that merely contains such words is left alone.", ""]
    return "\n".join(out)


def check():
    """The canon's own rules, checked: every word once, every offset aimed at something the engine has."""
    from .parts import FX, LIMITS, PARTS
    places = set(PARTS) | {"layers", "score", "look", "all"}
    for feel in FEELS:
        assert len(CANON[feel][1]) == len(CANON[feel][2]) == RUNGS_UP and len(CANON[feel][4]) == len(CANON[feel][5]) == RUNGS_DOWN, feel
        for where, what, _ in OFFSETS[feel]:
            assert where in places and (where in ("score", "look") or what in LIMITS or what == "density"), (feel, where, what)
    for feel, _, where, thing in SWITCHES:
        assert feel in FEELS and where in places and (thing.get("add_fx", {}).get("type", "delay") in FX), (feel, where, thing)
    assert sorted(f for row in PAD for f in row) == sorted(FEELS)
    assert not set(WORDS) & set(PRAISE) and not set(NOUNS) & set(PRAISE)
    for word in set(NOUNS) & set(WORDS):                       # an inverse's name is also one of its rungs: it must point the same way
        assert NOUNS[word][0] == WORDS[word][0] and NOUNS[word][1] * WORDS[word][1] > 0, word
    return len(WORDS), len(NOUNS), len(COMPARATIVES)


if __name__ == "__main__":
    import sys
    if "--check" in sys.argv:
        print("%d adjectives, %d nouns, %d comparatives: the canon holds" % check())
    else:
        sys.stdout.write(document())
