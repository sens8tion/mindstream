"""A bassline that is written: a riff kept as a thing, and every bar made from it.

The old sub drew a new rhythm for every bar and a new, unrelated riff every section, so nothing in it referred to
anything (docs/research/05_bass_sub_tune_progression.md, section 11). Here the riff is stored, and each bar is made
from it by rule (docs/research/README.md, build step 2; 05, section 12):

- A one-bar rhythm cell with two anchors: the one (step 0), either a long note or "short, short, held", and the second
  anchor, by default on the "and" of two (step 6), held. Around them decorations, each a chance that belongs to the
  riff: a pickup into an anchor, a push into the second snare, a note on a kick or just after one, a pickup into the
  next bar. So the riff's identity is its odds, and each bar is a fresh deal of them: anchors stay, decorations move.
- An eight-bar phrase, built as a sentence: statement, answer, the statement again (with the phrase's one high
  point), the answer closed on the root and thinnest; then two bars of fragments of the head, the statement heading
  home, and a turnaround: one low note and a gap, a hole, a pickup into the next phrase, or (now and then) a lift.
  Decorations thin across each four bars as the reference does, 29 : 25 : 27 : 19.
- The answer is the statement before it, altered: its tail re-dealt, its last notes removed, or one note moved an
  eighth; and in two riffs of three it sits a scale step lower.
- Pitch is a skeleton: the anchors' targets, three home pitches (the root and two of the seventh below, the fifth
  below, the third, the fourth), and one colour note (b2, 7, b6 or 6) that never appears in a statement, at most once
  a bar, only on a weak sixteenth or as a pickup, and is always followed within a beat by the note it leans on.
- Small moves (two semitones or less) slide, more often than not; leaps are struck, and only leave long notes.
- No note ever starts on the sixteenth after a snare (steps 5 and 13), and none sounds through a snare unless it
  started on it (or is a deep riff's one long note on the one).
- How it sits against the kick belongs to the scene: "lock" (short notes on the kicks: under a break), "answer"
  (short notes a sixteenth after them, and the second anchor off the kick: under a programmed two-step) or "free".
- The saw bass gets a job of its own (`answer`): the statement's head moved to the back half of the bar, played only
  where the sub is silent, in the turnarounds (and in the answers too, when the sub is deep). Or it rests ("off").

Steps are sixteenths counted from 0 (0 is the one, 4 and 12 the snares), so "step 6" in the research's 1-based
tables is step 5 here. Pitches are semitones above the root (negative below); the caller puts the root in its
register. No numpy and no sound here, and nothing is random that is not drawn from the numbers given: the same
arguments always make the same riff and the same bars.

What a development layer calls (one kept mutation every eight bars; at the end of a run the riff back after a hole,
partly rewritten or new; a B riff at about 32 bars; A back, changed, at 64):

    riff(seed, key=None, scale=MINOR, version=0, relation=None, kicks=(), density=None) -> a riff
        version: an int g (riff A after g kept mutations), or a dict, every key optional:
            {"riff": k, "side": "A" or "B", "partial": p, "gen": g}
        made in this order: the k-th riff of the seed (each new one keeps one thing of the one before, half the
        time); its B relative if side is "B"; then p partial rewrites; then g kept mutations, each building on the
        last. relation: "lock", "answer" or "free" (None: the seed chooses). kicks: the sixteenths the kick is
        written on. density: "deep" (long notes, few decorations) or "busy" (None: the seed chooses).
    bar(r, number, before=None, entry=False, kinds=False) -> [(step, semis, length, slide, accent)]
        number: bars since the riff began (any bar count will do): number % 8 is the place in the phrase, and the
        whole number re-deals the decorations and the turnaround. length in sixteenths. slide: None (struck) or the
        pitch the note glides in from (test it with `is not None`: the root is 0). accent: how hard, 0 to 1.
        before: the bar that was really played just before, when it was not this riff's (for the slide into the
        first note). entry: the first bar after a gap or a hole: one held root. kinds: each event gets a sixth
        field saying what it is ("A", "B", "decor", "colour", "pickup", "turn", "lift").
    answer(r, number, sub=None) -> the saw bass's events for that bar, in the same form; the caller plays them an
        octave above the sub. sub: the sub's events for the bar, if already made.
    mutate(r, how, seed=0, fate=None) -> a new riff. how: "kept" (one small mutation, kept: the next builds on it),
        "rewrite" (about half the cell and half the skeleton drawn again), "new" (a new riff that keeps one thing of
        this one, half the time), "rhythm", "B", or any `how` name develop.py gives (its MUTATIONS pick the kept
        mutation, KEEPS what a new riff keeps, TRANSPOSES move it, RETURNS_HOW bring it back changed; the drums' names
        leave it as it is). So: mutate(riff, info["how"], info["seed"], info["fate"]). hows() lists them all.
        r["transpose"] (semitones, within a fifth) is applied by bar() and answer(); home() is not moved by it.
    relative(r, seed=0) -> the B riff: the opposite density, the same home pitches, another second anchor, another
        colour note or none.
    home(r) -> the three home pitches (for motif.pitch_set: the hook shares them).

A riff is a plain dict of numbers, strings and tuples: it can be copied, kept, compared and printed, and
r["history"] says what has been done to it. Notes on the turnaround: a pickup into the next phrase leans on that
phrase's first note, which is always the root on the one; anything that puts a hole there instead should know that
its pickup (which may be the colour note) is then left hanging.
"""
import random

from .deal import _draw

MINOR = (0, 2, 3, 5, 7, 8, 10)
AFTER = (5, 13)                     # the sixteenths after the snares: nothing of the bass starts here
SNARES = (4, 12)
FORM = ("statement", "answer", "statement", "closed", "fragment", "fragment", "statement", "turnaround")
WEIGHT = (1.0, 0.86, 0.93, 0.66) * 2   # how many decorations, bar by bar of four: 29 : 25 : 27 : 19, as a share of the first
LOWER = 2.0 / 3.0                   # the answer a step lower: two riffs in three
TURNS = (("low", 0.4), ("hole", 0.2), ("pickup", 0.3), ("lift", 0.1))
SLIDE = 0.6                         # how often a small move slides
DEAL_DEEP, DEAL_BUSY = (0.5, 0.7), (0.7, 0.95)      # how often a decoration comes up, in a deep riff and a busy one
COLOURS = {"b2": (1, 0), "7": (-1, 0), "b6": (-4, -5), "6": (-3, -2)}    # the colour note, and the note it leans on
RATION = {"statement": 0.0, "answer": 0.25, "closed": 0.25, "fragment": 0.25, "turnaround": 0.5}
LOWEST, HIGHEST = -7, 7             # the line keeps within about a fifth either side of the root
RELATIONS = ("lock", "answer", "free")
RANK = {"A": 0, "B": 1, "turn": 1, "lift": 2, "colour": 2, "pickup": 3, "decor": 4}      # who keeps a sixteenth wanted twice
ACCENT = {"A": 1.0, "B": 0.85, "turn": 1.0, "lift": 0.75, "colour": 0.7, "pickup": 0.7, "decor": 0.6}


def _shift(semis, scale, by):
    """`semis` moved `by` steps along the scale (a note off the scale moves with the scale note below it)."""
    octave, within = divmod(int(semis), 12)
    degree = max(i for i, s in enumerate(scale) if s <= within)
    off = within - scale[degree]
    octaves, degree = divmod(degree + by, 7)
    return (octave + octaves) * 12 + scale[degree] + off


def _weighted(rng, items, weights):
    pick, total = rng.random() * sum(weights), 0.0
    for item, weight in zip(items, weights):
        total += weight
        if pick < total:
            return item
    return items[-1]


def _version(version):
    """A version as a dict with every key: an int is that many kept mutations of riff A."""
    out = {"riff": 0, "side": "A", "partial": 0, "gen": 0}
    if isinstance(version, dict):
        for name in ("riff", "partial", "gen"):
            out[name] = max(int(version.get(name, 0) or 0), 0)
        out["side"] = "B" if str(version.get("side", "A")).upper() == "B" else "A"
    else:
        out["gen"] = max(int(version or 0), 0)
    return out


# ------------------------------------------------------------------ making a riff

def _colour(rng, scale, home):
    """The scene's one colour note: one whose leaning note is a home pitch and which is not itself one. Now and then
    none at all."""
    pcs = {h % 12 for h in home}
    options = [name for name, (note, to) in COLOURS.items() if to in home and note % 12 not in pcs]
    if not options or rng.random() < 0.12:
        return None
    return rng.choice(sorted(options))


def _anchors(r):
    return {0, r["b_step"]} | ({2, 4} if r["a"] == "pair" else set())


def _decorations(rng, r):
    """The cell's decorations, each (step, chance, move): where it may sound, how often, and how its pitch is found
    from its neighbours. Only from the measured moves: pickups into an anchor or into the second snare, a pair an
    eighth apart, a note on or after the kick as the scene has it, a pickup into the next bar."""
    anchors, b = _anchors(r), r["b_step"]
    held = set(range(1, r["a_len"])) if r["a"] == "long" else set()          # the first anchor keeps its length
    held |= set(range(b + 1, b + 3))                                         # and the second at least three sixteenths
    pool = [(b - 2, "pickup"), (b - 1, "pickup"), (8, "pair"), (10, "push"), (11, "push"), (12, "pair"), (14, "next"), (15, "next")]
    if r["relation"] == "lock":
        kicked = [(k, "kick") for k in r["kicks"]]
    elif r["relation"] == "answer":
        kicked = [(k + 1, "kick") for k in r["kicks"]]
    else:
        kicked = []
    allowed = lambda s: 0 < s < 16 and s not in AFTER and s not in anchors and s not in held       # noqa: E731
    kicked = [c for c in kicked if allowed(c[0])]
    pool = [c for c in pool if allowed(c[0]) and c[0] not in {k for k, _ in kicked}]
    deep = r["density"] == "deep"
    count = rng.choice((0, 1, 1)) if deep else rng.choice((2, 3, 3, 4))
    rng.shuffle(pool)
    chosen = (kicked[:1] if count else []) + pool
    out, taken = [], set()
    for step, role in chosen:
        if len(out) >= count:
            break
        if step in taken:
            continue
        taken.add(step)
        chance = rng.uniform(*(DEAL_DEEP if deep else DEAL_BUSY))
        if role in ("pickup", "push", "next"):
            move = ("toward", rng.choice((-1, 1))) if rng.random() < 0.5 else ("same",)
        else:
            move = _weighted(rng, (("same",), ("step", -1), ("step", 1), ("home", 1), ("home", 2)), (0.45, 0.17, 0.13, 0.13, 0.12))
        out.append((step, round(chance, 3), move))
    return tuple(sorted(out))


def _new(key, name, scale, relation=None, kicks=(), density=None):
    """A riff from nothing but its numbers."""
    rng = random.Random(repr(("riff", key)))
    scale = tuple(int(x) for x in scale)
    deep = density == "deep" if density in ("deep", "busy") else rng.random() < 0.35
    others = [_shift(0, scale, -1), _shift(0, scale, -3), scale[2], scale[3]]       # the seventh below, the fifth below, the third, the fourth
    first = _weighted(rng, others, (0.35, 0.35, 0.15, 0.15))
    rest = [p for p in others if p != first]
    second = _weighted(rng, rest, [{others[0]: 0.35, others[1]: 0.35}.get(p, 0.15) for p in rest])
    home = (0, first, second)
    kicks = tuple(sorted({int(k) % 16 for k in kicks} - {0}))
    relation = relation if relation in RELATIONS else rng.choice(RELATIONS)
    b_step = rng.choice((6, 6, 6, 6, 10, 12))
    if relation == "answer" and b_step in kicks:            # under a two-step the held notes start off the kick
        b_step = next((s for s in (6, 12, 10) if s not in kicks), b_step)
    r = {"key": name, "scale": scale, "relation": relation, "kicks": kicks, "density": "deep" if deep else "busy",
         "a": "pair" if not deep and rng.random() < 0.3 else "long",
         "a_len": rng.choice((5, 6)) if deep else rng.choice((3, 4)),
         "b_step": b_step, "b_len": rng.choice((4, 5)) if deep else rng.choice((3, 4)),
         "home": home, "b_pitch": rng.choice((0, 0, first, second)),
         "high": rng.choice((scale[2], scale[3], scale[4])), "high_at": rng.choice((2, 2, 4, 5)),
         "lower": rng.random() < LOWER, "answer": rng.choice(("tail", "remove", "shift")),
         "colour": _colour(rng, scale, home), "ration": 1.0,
         "bass": "answer" if rng.random() < 0.65 else "off",
         "salt": rng.randrange(1 << 30), "history": ("new",), "version": ()}
    r["decor"] = _decorations(rng, r)
    return r


def _keep_one(fresh, old, rng, what=None):
    """A new riff that keeps one thing of the last, half the time: its second anchor, its answer, or its colour
    note. A part, never a whole dimension: "same rhythm, new notes" is all but absent in the reference. what: keep
    that one ("anchor", "answer", "colour", or "home": the three home pitches), always; "nothing": keep nothing."""
    if what is None:
        if rng.random() >= 0.5:
            return fresh
        what = rng.choice(("anchor", "answer", "colour"))
    if what == "nothing":
        return fresh
    out = dict(fresh)
    if what == "home":
        out["home"] = old["home"]
        out["b_pitch"] = old["home"][int(rng.random() * 3) % 3] if fresh["b_pitch"] not in old["home"] else fresh["b_pitch"]
        pcs = {h % 12 for h in old["home"]}
        if fresh["colour"] and (COLOURS[fresh["colour"]][1] not in old["home"] or COLOURS[fresh["colour"]][0] % 12 in pcs):
            out["colour"] = _colour(rng, fresh["scale"], old["home"])
    elif what == "anchor":
        out["b_step"], out["b_len"] = old["b_step"], old["b_len"]
        out["decor"] = _decorations(rng, out)
    elif what == "answer":
        out["answer"], out["lower"] = old["answer"], old["lower"]
    elif old["colour"] is None or COLOURS[old["colour"]][1] in out["home"]:
        out["colour"] = old["colour"]
    out["history"] = fresh["history"] + ("kept its " + what,)
    return out


_GROWN = {}                         # riffs part way along a development path, so the next step costs one mutate


def riff(seed, key=None, scale=MINOR, version=0, relation=None, kicks=(), density=None):
    """The riff for these numbers (see the module's notes for `version`).

    A version dict may also carry "path": what development has done to the riff so far, as ((how, seed, fate), ...)
    in order, each step applied with mutate(r, how, seed, fate) after side and partial, and before gen (so a riff
    mutated by hand from a developed one is that one, changed in one thing). A path only ever grows by a step at its
    end, so the riff of the path one step shorter is kept, and the next costs one mutate."""
    v = _version(version)
    path = tuple(tuple(step) for step in (version.get("path") or ())) if isinstance(version, dict) else ()
    r = _new((seed, v["riff"]), key, scale, relation, kicks, density)
    if v["riff"] > 0:
        r = _keep_one(r, _new((seed, v["riff"] - 1), key, scale, relation, kicks, density), random.Random(repr(("keep", seed, v["riff"]))))
    if v["side"] == "B":
        r = relative(r, seed)
    for i in range(v["partial"]):
        r = mutate(r, "rewrite", (seed, "partial", i))
    if path:
        base = (seed, key, tuple(scale), relation, tuple(kicks), density, v["riff"], v["side"], v["partial"])
        done, grown = len(path), None
        while done and grown is None:                   # (asked from more than one thread: looked up once, never in-then-get)
            grown = _GROWN.get((base, path[:done]))
            done -= grown is None
        if grown is not None:
            r = grown
        for i in range(done, len(path)):
            how, step_seed, fate = path[i]
            r = mutate(r, how, step_seed, fate)
            if len(_GROWN) > 256:
                _GROWN.clear()
            _GROWN[(base, path[:i + 1])] = r
    for i in range(v["gen"]):
        r = mutate(r, "kept", (seed, "gen", i))
    return {**r, "version": tuple(sorted(v.items())) + ((("path", path),) if path else ())}


def home(r):
    return tuple(r["home"])


def relative(r, seed=0):
    """The B riff: clearly another line and in tune with this one. The opposite density, the same home pitches, a
    different second anchor, a different colour note or none."""
    rng = random.Random(repr(("B", seed, r["salt"], r["history"])))
    b = _new(("B", seed, r["salt"]), r["key"], r["scale"], r["relation"], r["kicks"], "busy" if r["density"] == "deep" else "deep")
    b["home"] = r["home"]
    b["b_pitch"] = rng.choice((0, r["home"][1], r["home"][2]))
    b["b_step"] = rng.choice([s for s in (6, 10, 12) if s != r["b_step"] and not (r["relation"] == "answer" and s in r["kicks"])] or [6])
    pcs = {h % 12 for h in r["home"]}
    colours = [name for name, (note, to) in COLOURS.items() if name != r["colour"] and to in r["home"] and note % 12 not in pcs]
    b["colour"] = rng.choice(sorted(colours) + [None])
    b["decor"] = _decorations(rng, b)
    b["history"] = r["history"] + ("B",)
    return b


# ------------------------------------------------------------------ changing a riff

def _kept(r, rng, want=None):
    """One meaningful change, kept: the next generation builds on this one (05, 12.7). want: which change (one of
    _kept's own names, see KEPT_HOW); when that one cannot be made here, another is drawn."""
    out, decor = dict(r), list(r["decor"])
    anchors = _anchors(r) | (set(range(1, r["a_len"])) if r["a"] == "long" else set()) | set(range(r["b_step"] + 1, r["b_step"] + 3))
    free = [s for s in (r["b_step"] - 2, r["b_step"] - 1, 8, 10, 11, 14, 15)
            if 0 < s < 16 and s not in AFTER and s not in anchors and s not in {d[0] for d in decor}]
    choices = []
    if decor:
        choices += ["drop", "shift"]
    if free:
        choices.append("pickup")
    choices += ["skeleton", "high", "answer", "deeper" if r["density"] == "busy" else "busier"]
    if r["colour"] is None or r["ration"] < 2.0:
        choices.append("colour")
    what = rng.choice(choices)
    if want in choices or want in ("deeper", "busier"):          # (either way along the density dial, asked for)
        what = want
    if what == "drop":
        decor.pop(rng.randrange(len(decor)))
    elif what == "pickup":
        decor.append((rng.choice(free), round(rng.uniform(0.55, 0.85), 3), ("toward", rng.choice((-1, 1)))))
    elif what == "shift":
        i = rng.randrange(len(decor))
        step, chance, move = decor[i]
        to = [s for s in (step + 2, step - 2) if 0 < s < 16 and s not in AFTER and s not in anchors and s not in {d[0] for d in decor}]
        if to:
            decor[i] = (rng.choice(to), chance, move)
        else:
            decor.pop(i)
            what = "drop"
    elif what == "skeleton":
        out["b_pitch"] = rng.choice([p for p in r["home"] if p != r["b_pitch"]])
    elif what == "high":
        out["high_at"] = rng.choice([p for p in (2, 4, 5) if p != r["high_at"]])
    elif what == "answer":
        out["answer"] = rng.choice([a for a in ("tail", "remove", "shift") if a != r["answer"]])
    elif what == "deeper":                    # longer anchors and one decoration fewer
        out["a_len"], out["b_len"] = min(r["a_len"] + 1, 6), min(r["b_len"] + 1, 5)
        if decor:
            decor.pop(rng.randrange(len(decor)))
    elif what == "busier":
        out["a_len"], out["b_len"] = max(r["a_len"] - 1, 3), max(r["b_len"] - 1, 3)
        if free:
            decor.append((rng.choice(free), round(rng.uniform(0.55, 0.85), 3), ("same",)))
    elif what == "colour":
        if r["colour"] is None:
            out["colour"] = _colour(random.Random(rng.random()), r["scale"], r["home"]) or None
        out["ration"] = min(r["ration"] * 1.5, 2.0)
    out["decor"] = tuple(sorted(decor))
    out["history"] = r["history"] + (what,)
    return out


def _rewrite(r, rng):
    """A partial rewrite: the anchors stay, about half the decorations and half the skeleton are drawn again."""
    out = dict(r)
    decor = list(r["decor"])
    rng.shuffle(decor)
    kept = decor[:(len(decor) + 1) // 2]
    fresh = [d for d in _decorations(rng, {**r, "decor": ()}) if d[0] not in {k[0] for k in kept}]
    out["decor"] = tuple(sorted(kept + fresh[:max(len(decor) - len(kept), 1)]))
    if rng.random() < 0.5:
        out["b_pitch"] = rng.choice(r["home"])
        out["high"] = rng.choice((r["scale"][2], r["scale"][3], r["scale"][4]))
    else:
        out["high_at"] = rng.choice((2, 4, 5))
        out["lower"] = not r["lower"] if rng.random() < 0.5 else r["lower"]
    out["salt"] = rng.randrange(1 << 30)
    out["history"] = r["history"] + ("rewrite",)
    return out


def _rhythm(r, rng):
    """The same notes on a new rhythm: the skeleton (home pitches, the second anchor's pitch, the high point, the
    colour note) kept, the cell (the first anchor's shape, the second anchor's place, the decorations) drawn again."""
    out = dict(r)
    out["b_step"] = rng.choice([s for s in (6, 10, 12) if s != r["b_step"] and not (r["relation"] == "answer" and s in r["kicks"])] or [r["b_step"]])
    if r["density"] == "busy":
        out["a"] = "pair" if r["a"] == "long" else "long"
    out["a_len"] = rng.choice((5, 6)) if r["density"] == "deep" else rng.choice((3, 4))
    out["decor"] = _decorations(rng, out)
    out["salt"] = rng.randrange(1 << 30)
    out["history"] = r["history"] + ("rhythm",)
    return out


def _transpose(r, by):
    """The riff moved `by` semitones, kept within about a fifth of the root (an octave folded away)."""
    t = r.get("transpose", 0) + by
    while t > HIGHEST:
        t -= 12
    while t < LOWEST:
        t += 12
    return {**r, "transpose": t}


def _returned(r, how, rng):
    """A riff coming back changed at a section (A at 64, B at 96): the way develop names it."""
    out = dict(r)
    if how == "second_bass":                # the saw bass comes in under it, answering in more bars
        out["bass"], out["second"] = "answer", True
    elif how == "other_skeleton":           # the same rhythm, another skeleton: other targets for the second anchor and the high point
        out["b_pitch"] = rng.choice([p for p in r["home"] if p != r["b_pitch"]])
        out["high"] = rng.choice([p for p in (r["scale"][2], r["scale"][3], r["scale"][4]) if p != r["high"]] or [r["high"]])
        out["high_at"] = rng.choice([p for p in (2, 4, 5) if p != r["high_at"]])
    else:                                   # "harder": struck harder, a little busier, its colour heard more
        out = _kept(r, rng, "busier" if r["density"] == "busy" or rng.random() < 0.5 else "pickup")
        out["harder"] = min(r.get("harder", 0) + 1, 2)
        out["ration"] = min(r["ration"] * 1.5, 2.0)
    out["history"] = out["history"][:len(r["history"])] + ("back: " + how,)
    return out


# The `how` names of develop.py (MUTATIONS, KEEPS, RETURNS_HOW, TRANSPOSES, DRUM_HOW, DRUM_RETURNS, HOOK_KEEPS and the
# names it gives rewrites, rhythms and B), each mapped onto what it does to a riff.
KEPT_HOW = {"drop_decoration": "drop", "add_pickup": "pickup", "shift_decoration": "shift", "swap_pitch": "skeleton",
            "move_high_point": "high", "switch_answer": "answer", "toward_deep": "deeper", "toward_busy": "busier",
            "colour_note": "colour"}
KEEP_HOW = {"anchor_b": "anchor", "answer": "answer", "colour": "colour", "interval": "home"}   # a new riff keeping this
TRANSPOSE_HOW = {"down_step": ("step", -1), "up_step": ("step", 1), "up_fourth": ("semis", 5)}
RETURN_HOW = ("second_bass", "other_skeleton", "harder")
DRUMS_ONLY = ("carrier", "kick", "busier_carrier", "other_kick", "kick_and_carrier")      # the drums' change: the notes stay
LEAVE = ("start", "hold", "hole", "back")      # fates that change nothing of the material


def mutate(r, how, seed=0, fate=None):
    """A new riff made from this one. Deterministic in (r, how, seed, fate).

    how: "kept" (one small mutation, drawn), "rewrite" (about half drawn again), "new" (a new riff keeping one thing
    of this one, half the time), "rhythm" (the same notes on a new rhythm), "B" (the relative), or any `how` that
    develop.py gives: a MUTATIONS name (that kept mutation), a KEEPS name (a new riff keeping that), a TRANSPOSES name,
    a RETURNS_HOW name (the riff back changed that way), "half_cell_half_skeleton" (rewrite), "same_notes_new_rhythm"
    (rhythm), "opposite_density" (B), a HOOK_KEEPS name ("rhythm"; "interval": a new riff keeping the home pitches),
    a drums' name (DRUM_HOW, DRUM_RETURNS, "kick_and_carrier": the drums change, the riff is returned as it is), or
    None (a new riff keeping nothing).
    fate: develop's fate for the bar, when given, settles what `how` alone leaves open: "new" with None keeps
    nothing, "B" with a RETURNS_HOW name is B back changed, and "start", "hold", "hole" and "back" change nothing.

    So an integrator can pass develop's info straight through: mutate(riff, info["how"], info["seed"], info["fate"])."""
    if fate in LEAVE:
        return r
    rng = random.Random(repr(("mutate", how, seed, fate, r["salt"], r["history"])))
    if fate in ("mutate",) and how is None:
        how = "kept"
    if fate == "rewrite" and how is None:
        how = "rewrite"
    if fate == "rhythm" and how is None:
        how = "rhythm"
    if fate == "B" and how is None:
        how = "B"
    if fate == "transpose" and how is None:
        how = "down_step"
    if fate == "A_changed" and how is None:
        how = "harder"
    how = {"kept mutation": "kept", "mutation": "kept", "mutate": "kept", "rewrite part": "rewrite", "partial": "rewrite",
           "half_cell_half_skeleton": "rewrite", "same_notes_new_rhythm": "rhythm", "opposite_density": "B", "fresh": "new",
           "transpose": "down_step"}.get(how, how)
    if how == "kept":
        return _kept(r, rng)
    if how in KEPT_HOW:
        return _kept(r, rng, KEPT_HOW[how])
    if how == "rewrite":
        return _rewrite(r, rng)
    if how == "rhythm":
        return _rhythm(r, rng)
    if how == "B":
        return relative(r, seed)
    if how in TRANSPOSE_HOW:
        kind, by = TRANSPOSE_HOW[how]
        semis = _shift(0, r["scale"], by) if kind == "step" else by
        out = _transpose(r, semis)
        return {**out, "history": r["history"] + ("transpose " + how,)}
    if how in RETURN_HOW:
        return _returned(r, how, rng)
    if how in DRUMS_ONLY:
        return {**r, "history": r["history"] + ("drums: " + how,)}
    if how is None or how == "new" or how in KEEP_HOW:
        fresh = _new(("new", seed, r["salt"]), r["key"], r["scale"], r["relation"], r["kicks"])
        what = KEEP_HOW.get(how, "nothing" if how is None else None)
        out = _keep_one(fresh, r, rng, what)
        if r.get("transpose"):
            out = {**out, "transpose": r["transpose"]}
        return {**out, "history": r["history"] + out["history"][1:] + ("new",)}
    raise ValueError(f"mutate: {how!r} is not a way this riff knows to change")


def hows():
    """Every `how` mutate takes (develop's names among them)."""
    return (("kept", "rewrite", "new", "rhythm", "B", None) + tuple(KEPT_HOW) + tuple(KEEP_HOW) + tuple(TRANSPOSE_HOW)
            + RETURN_HOW + DRUMS_ONLY + ("half_cell_half_skeleton", "same_notes_new_rhythm", "opposite_density"))


# ------------------------------------------------------------------ the bars

def _cell(r, number, weight=1.0, part="deal"):
    """The statement as bar `number` deals it: the anchors, and the decorations that came up this time, with their
    pitches found in order. [step, semis, length, kind]."""
    scale, colour = r["scale"], COLOURS[r["colour"]][0] % 12 if r["colour"] else None
    if r["a"] == "pair":
        ev = [[0, 0, 2, "A"], [2, 0, 2, "A"], [4, 0, max(r["a_len"], 2), "A"]]
    else:
        ev = [[0, 0, r["a_len"], "A"]]
    ev.append([r["b_step"], r["b_pitch"], r["b_len"], "B"])
    moves = {}
    for step, chance, move in r["decor"]:
        if _draw(r["salt"], part, number, step) < chance * weight:
            ev.append([step, None, 2, "decor"])
            moves[step] = move
    if (10 in moves or 11 in moves) and not any(e[0] == 12 for e in ev):
        ev.append([12, r["b_pitch"], 3, "decor"])       # a push leads into a note on the second snare
    ev.sort(key=lambda e: e[0])
    for i, e in enumerate(ev):                          # each note from the one before it ...
        if e[1] is not None or moves[e[0]][0] == "toward":
            continue
        before, move = next(x for x in reversed(ev[:i]) if x[1] is not None), moves[e[0]]
        if move[0] == "step":
            p = _shift(before[1], scale, move[1])
        elif move[0] == "home":
            p = r["home"][move[1]] if before[2] >= 3 else before[1]          # a leap only leaves a long note
        else:
            p = before[1]
        e[1] = p if LOWEST <= p <= HIGHEST and (colour is None or p % 12 != colour) else before[1]
    for i in range(len(ev) - 1, -1, -1):                # ... and a pickup from the one it leads into
        e = ev[i]
        if e[1] is None:
            target = ev[i + 1][1] if i + 1 < len(ev) else 0
            p = _shift(target, scale, moves[e[0]][1])
            e[1] = p if LOWEST <= p <= HIGHEST and (colour is None or p % 12 != colour) else target
    return ev


def _answer_of(r, number, weight):
    """The answer: the statement of the bar before, altered by the riff's own operation, and a step lower in two
    riffs of three."""
    src = _cell(r, number - 1, weight)
    op = r["answer"]
    if op == "tail":                        # the head kept, the tail dealt again
        ev = [e for e in src if e[0] < 8] + [e for e in _cell(r, number, weight, "tail") if e[0] >= 8]
    else:
        ev = [list(e) for e in src]
        loose = [e for e in ev if e[3] not in ("A",)]
        moved = False
        if op == "shift":                   # one decoration moved an eighth (never into an anchor's own length)
            held = set(range(1, r["a_len"])) if r["a"] == "long" else set()
            held |= set(range(r["b_step"] + 1, r["b_step"] + 3))
            for e in [x for x in loose if x[3] == "decor"]:
                taken = {x[0] for x in ev}
                to = [s for s in (e[0] + 2, e[0] - 2) if 0 < s < 16 and s not in AFTER and s not in taken and s not in held]
                if to:
                    e[0] = to[int(_draw(r["salt"], "shift") * len(to)) % len(to)]
                    moved = True
                    break
        if not moved and loose:             # the last one or two notes taken away, leaving a gap
            count = 1 if len(loose) < 2 or _draw(r["salt"], "remove") < 0.5 else 2
            for e in loose[-count:]:
                ev.remove(e)
        ev.sort(key=lambda e: e[0])
    if r["lower"]:
        colour = COLOURS[r["colour"]][0] % 12 if r["colour"] else None
        for e in ev:
            low = _shift(e[1], r["scale"], -1)
            e[1] = low if low % 12 != colour else e[1]      # the colour note is the colour's alone
    return ev


def _turn(r, phrase):
    pick, total = _draw(r["salt"], "turn", phrase), 0.0
    for name, chance in TURNS:
        total += chance
        if pick < total:
            break
    if name == "lift" and phrase % 2 == 0:      # a lift at most once in sixteen bars
        name = "pickup"
    return name


def _tidy(ev, r):
    """The rules every bar keeps: one note a sixteenth; nothing on the sixteenth after a snare; no run of more than
    three sixteenths; each note cut by the next; nothing sounding through a snare unless it started there (or is a
    deep riff's one long note on the one); the last note let go two sixteenths before the bar line unless it is a
    pickup into the next; a short decoration never left alone (another note within an eighth)."""
    deep = r["density"] == "deep"
    keep = {}
    for e in sorted(ev, key=lambda e: (e[0], RANK[e[3]])):
        if 0 <= e[0] < 16 and e[0] not in AFTER and e[0] not in keep:
            keep[e[0]] = list(e)
    ev = [keep[s] for s in sorted(keep)]
    changed = True
    while changed:
        changed = False
        for i in range(len(ev) - 3):
            if ev[i + 3][0] - ev[i][0] == 3:
                ev.remove(max(ev[i:i + 4], key=lambda e: RANK[e[3]]))
                changed = True
                break
    for _ in range(2):
        alone = [e for e in ev if e[3] == "decor" and not any(0 < abs(o[0] - e[0]) <= 2 for o in ev if o is not e)
                 and not (e[0] >= 14)]
        for e in alone:
            ev.remove(e)
    for i, e in enumerate(ev):
        nxt = ev[i + 1][0] if i + 1 < len(ev) else 16
        length = min(e[2], nxt - e[0])
        for snare in SNARES:
            if e[0] < snare < e[0] + length and not (deep and e[3] == "A" and e[0] == 0):
                length = snare - e[0]
        if i + 1 == len(ev) and e[0] < 14:
            length = min(length, 14 - e[0])
        e[2] = max(length, 1)
    return ev


def _plain(r, number):
    """Bar `number` before its colour note and its slides."""
    pos, phrase = number % 8, number // 8
    role, weight = FORM[pos], WEIGHT[pos]
    if role == "statement":
        ev = _cell(r, number, weight)
        if pos == r["high_at"]:
            for e in ev:
                if e[3] == "B":
                    e[1] = r["high"]
    elif role in ("answer", "closed"):
        ev = _answer_of(r, number, weight)
        if role == "closed" and ev:         # the answer closed: it ends on the root
            ev[-1][1] = 0
    elif role == "fragment":                # the head, twice: the statement's in bar 5, the answer's in bar 6
        src = _cell(r, number, weight) if pos == 4 else _answer_of(r, number, weight)
        head = [e for e in src if e[0] < 8]
        ev = [list(e) for e in head] + [[e[0] + 8, e[1], e[2], e[3]] for e in head]
        if pos == r["high_at"]:
            for e in ev:
                if e[0] == 8:
                    e[1] = r["high"]
    else:
        turn = _turn(r, phrase)             # (bar 8 is an answer's place: what it keeps is the answer's head)
        head = [list(e) for e in _answer_of(r, number, weight) if e[0] < 8]
        if turn == "low":                   # one low note, and the drums alone
            ev = [[0, 0, 3, "turn"]]
        elif turn == "hole":
            ev = []
        elif turn == "pickup":              # open: a pickup into the next phrase's root
            at = 14 if _draw(r["salt"], "pickup at", phrase) < 0.5 else 15
            if r["colour"] and COLOURS[r["colour"]][1] == 0 and _draw(r["salt"], "pickup colour", phrase) < 0.6 * r["ration"]:
                ev = head + [[at, COLOURS[r["colour"]][0], 16 - at, "colour"]]
            else:
                ev = head + [[at, _shift(0, r["scale"], -3), 16 - at, "pickup"]]
        else:                               # a lift: rising by step over the back half
            ev = head + [[8, _shift(0, r["scale"], 1), 2, "lift"], [10, _shift(0, r["scale"], 2), 2, "lift"],
                         [14, _shift(0, r["scale"], 3), 2, "lift"]]
    return _tidy(ev, r)


def _coloured(r, number):
    """Bar `number` with its colour note, if this bar has one: on a weak sixteenth or as a pickup, at most an eighth
    long, and always followed within a beat by the note it leans on."""
    ev = _plain(r, number)
    role = FORM[number % 8]
    if r["colour"] is None or any(e[3] == "colour" for e in ev):
        return ev
    if role == "turnaround" and _turn(r, number // 8) in ("low", "hole"):       # a gap is a gap
        return ev
    if _draw(r["salt"], "colour", number) >= RATION[role] * r["ration"]:
        return ev
    note, to = COLOURS[r["colour"]]
    taken = {e[0] for e in ev}
    tries = []
    for e in ev:                            # leaning into a note that is already the one it resolves to
        if e[1] != to or e[0] == 0:
            continue
        for gap in (1, 2, 3):
            p = e[0] - gap
            if p <= 0 or p in AFTER or p in taken or (gap == 3 and p % 2 == 0) or any(p < x[0] < e[0] for x in ev):
                continue
            tries.append([[p, note, min(2, gap), "colour"]])
    for p in (9, 11, 7, 3, 15):             # or a pair where there is room: the colour, then the note it leans on
        q = p + 1
        if q < 16 and q not in AFTER and p not in AFTER and not any(p - 1 <= x[0] <= q + 1 for x in ev):
            tries.append([[p, note, 1, "colour"], [q, to, 2, "decor"]])
    for extra in tries:
        prior = [x for x in ev if x[0] < extra[0][0]]
        if prior and prior[-1][3] in ("A", "B") and extra[0][0] - prior[-1][0] < 2:
            continue                        # (an anchor is not cut to a blip for it)
        out = _tidy(ev + [list(x) for x in extra], r)
        if _resolved(out, note, to):
            return out
    return ev


def _resolved(ev, note, to):
    """Is the colour note in this bar followed, within a beat, by the note it leans on?"""
    for i, e in enumerate(ev):
        if e[3] == "colour":
            return i + 1 < len(ev) and ev[i + 1][0] - e[0] <= 4 and ev[i + 1][1] == to
    return False


def _slides(r, ev, number, prev):
    """Each note struck or slid: a small move slides (more often than not, and always as a pickup into a snare or out
    of the colour note) when the note before runs up to it; a leap is struck."""
    out = []
    for e in ev:
        slide = None
        if prev is not None:
            step, semis, length, kind = prev
            gap = e[0] - (step + length)
            move = abs(e[1] - semis)
            if 0 < move <= 2 and gap <= 1:
                into_snare = e[0] in SNARES and e[0] - step <= 2
                if kind == "colour" or into_snare or _draw(r["salt"], "slide", number, e[0]) < SLIDE:
                    slide = semis
        out.append((e[0], e[1], e[2], slide, ACCENT[e[3]], e[3]))
        prev = (e[0], e[1], e[2], e[3])
    return out


def bar(r, number, before=None, entry=False, kinds=False):
    """What the sub plays in bar `number` of this riff: [(step, semis, length, slide, accent)] (see the module's
    notes)."""
    number = int(number)
    if entry:                               # the first bar after a gap carries the weight: one held root
        ev = [[0, 0, 8 if r["density"] == "deep" else 6, "A"]]
    else:
        ev = _coloured(r, number)
    t = r.get("transpose", 0)                # a transposed riff: every note moved, the slide into it from what was played
    ev = [[e[0], e[1] + t, e[2], e[3]] for e in ev]
    if before is not None:
        last = list(before)[-1] if before else None
        prev = (last[0] - 16, last[1], last[2], last[5] if len(last) > 5 else "decor") if last else None
    elif number > 0:
        last = _coloured(r, number - 1)
        prev = (last[-1][0] - 16, last[-1][1] + t, last[-1][2], last[-1][3]) if last else None
    else:
        prev = None
    out = _slides(r, ev, number, prev)
    if r.get("harder"):                      # back harder: every note struck a little harder
        out = [e[:4] + (min(1.0, e[4] + 0.1 * r["harder"]),) + e[5:] for e in out]
    return out if kinds else [e[:5] for e in out]


def answer(r, number, sub=None):
    """The saw bass's line in bar `number`: its own job, not an echo. The statement's head, moved to start on the
    third beat, sounding only where the sub is silent, on one to three of the home pitches; in the turnarounds, and
    in the answers as well when the sub is deep (a busy bass under a busy sub is a fight). Nothing if the riff has
    given it the bar off, or the scene has it resting."""
    if r.get("bass") != "answer":
        return []
    pos = number % 8
    if pos not in ((1, 3, 5, 7) if r["density"] == "deep" or r.get("second") else (3, 7)):
        return []
    sub = bar(r, number) if sub is None else sub
    sounding = set()
    for e in sub:
        sounding.update(range(e[0], e[0] + max(int(-(-e[2] // 1)), 1)))
    out = []
    for step, semis, length, kind in [e for e in _cell(r, number, 1.0, "saw") if e[0] < 8]:
        s = step + 8
        if s >= 16 or s in AFTER or s in sounding:
            continue
        free = min([x for x in sounding if x > s] + [16])
        length = min(length, free - s, 16 - s)
        if length < 1:
            continue
        pitch = min(r["home"], key=lambda h: (abs(h - semis), h))
        out.append((s, pitch + r.get("transpose", 0), length, None, 0.7))
    return out
