"""A hook that belongs to the bass: a short motif with one interval of its own, made from the bass's pitches and
placed where the bass is not.

The old hook was a random shape of small steps, stated, repeated exactly four bars later and replaced by a stranger,
placed with no reference to the sub (docs/research/05_bass_sub_tune_progression.md, section 11). Here (README build
step 3; 05, section 12.8):

- Its pitches are a small set shared with the bass: the root, the third, the fourth, the fifth and the seventh of the
  scale (in minor, the minor pentatonic), with the bass's home pitches folded in. Four or five pitch classes; the
  bass's colour note is left to the bass.
- The motif is three or four notes over at most two beats, with exactly one distinctive interval (a fourth, a fifth
  or a minor sixth), everything else a repeat or a step along the set, the leap followed by a step back, one highest
  note. Stated, it ends open (not on the root).
- In each eight bars it is stated in bar 4, its leap heard again as a fragment in bar 5, and answered in bar 8, four
  bars after the statement, with the same head and its ending changed to the root or the fifth (the answer closes).
  Bars 4, 5 and 8 are where the reference's hooks cluster. Then it is replaced by a relative (the same leap, the
  contour turned over, or moved a step down the set, or the same notes on a new rhythm), never by a stranger.
- In the bar, it starts where the sub and the bass are silent, late if it can (from the third beat), never on the one
  or on a snare, and its own notes keep off the low end's onsets.

Offsets and steps are sixteenths counted from 0; pitches are semitones above the root, in one octave span chosen so
the shape keeps its intervals (the caller moves it as a whole into the register where hooks live). No numpy, no
sound, nothing random that is not drawn from the numbers given.

What a development layer calls:

    pitch_set(scale, home=()) -> the hook's pitch classes (home: bassline.home(r), the bass's home pitches)
    motif(seed, scale, pitches, version=0) -> a motif (a plain dict; m["notes"], m["leap"], m["history"])
        version: an int g (g relatives down the line from the seed's first motif), or a dict, every key optional:
            {"motif": k, "gen": g}: the k-th motif of the seed (each new one keeps the last one's rhythm or its
            leap, half the time), then g relatives of it.
    statement(m), answer(m), fragment(m, which=0) -> [(offset, semis, length)]
        fragment 0: the two notes of the leap; 1: the whole motif an eighth later.
    relative(m, seed=0) -> the motif that replaces it: the same distinctive interval, otherwise turned over, moved,
        or put on a new rhythm.
    mutate(m, how, seed=0, fate=None) -> "kept" (a small change of rhythm, the notes kept), "rewrite" (the head up to
        the leap kept, the rest drawn again), "new" (a new motif keeping this one's rhythm or its leap), "relative",
        or any `how` develop.py gives (HOOK_KEEPS "rhythm"/"interval": a new motif keeping that; None: keeping
        nothing; RETURNS_HOW: back changed; see HOW). So: mutate(m, info["how"], info["seed"], info["fate"]).
    block(m, number, low=None, bars=3) -> {bar in the eight (0 to 7): [(sixteenth, semis, length)]}
        the eight bars that bar `number` falls in. low: {bar in the eight: [(sixteenth, length)]} where the sub and
        the bass sound (or a function of the bar in the eight), so the hook is placed in their gaps. bars: how many
        bars of the eight carry it (3 as measured; 2, 4 or 6 when asked for less or more).
    place(notes, low, salt=0) -> the sixteenth the notes start on in a bar where `low` sounds.
"""
import random

from .deal import _draw

LEAPS = (5, 7, 8)                    # a fourth, a fifth, a minor sixth: the one interval that makes the shape its own
NEVER = (0, 4, 12)                   # no hook starts on the one or on a snare
LATE = (8, 10, 9, 11, 6, 7, 14, 2, 3, 1, 13, 15, 5)     # where it starts, best first: from the third beat
SLOTS = ((3, "statement"), (7, "answer"), (4, "fragment"), (5, "displaced"), (1, "relative"), (6, "fragment"), (2, "displaced"))


def pitch_set(scale, home=()):
    """The hook's pitch classes: 1, the third, 4, 5 and the seventh of the scale, and the bass's home pitches."""
    return tuple(sorted({0, scale[2] % 12, scale[3] % 12, scale[4] % 12, scale[6] % 12} | {int(h) % 12 for h in home}))


def _ladder(pitches):
    """The pitch set laid out over the octaves a motif may use: steps along it are its steps."""
    return tuple(sorted({pc + 12 * octave for pc in pitches for octave in (-1, 0, 1, 2) if -5 <= pc + 12 * octave <= 24}))


def _version(version):
    out = {"motif": 0, "gen": 0}
    if isinstance(version, dict):
        for name in out:
            out[name] = max(int(version.get(name, 0) or 0), 0)
    else:
        out["gen"] = max(int(version or 0), 0)
    return out


def _rhythm(rng, count):
    """Onsets a sixteenth to three apart, the last note held a little; all within two beats."""
    for _ in range(50):
        offsets = [0]
        for _ in range(count - 1):
            offsets.append(offsets[-1] + rng.choice((1, 2, 2, 3)))
        lengths = [min(offsets[i + 1] - offsets[i], rng.choice((1, 1, 2))) for i in range(count - 1)] + [rng.choice((1, 2, 2, 3))]
        if offsets[-1] + lengths[-1] <= 8:
            return tuple(zip(offsets, lengths))
    return tuple((i, 1) for i in range(count))


def _contour(rng, ladder, count, leap, leap_at, up, start=None):
    """Pitches along the ladder: repeats and steps, the one leap at `leap_at`, and a step back after it."""
    where = {p: i for i, p in enumerate(ladder)}
    starts = [p for p in ladder if 0 <= p < 12] if start is None else [start]
    out = [rng.choice(starts)]
    for i in range(count - 1):
        here = where[out[-1]]
        if i == leap_at:
            nxt = out[-1] + (leap if up else -leap)
            if nxt not in where:
                return None
        elif i == leap_at + 1:
            j = here - 1 if up else here + 1
            if not 0 <= j < len(ladder):
                return None
            nxt = ladder[j]
        elif rng.random() < 0.35:
            nxt = out[-1]
        else:
            j = here + rng.choice((-1, 1))
            if not 0 <= j < len(ladder):
                return None
            nxt = ladder[j]
        out.append(nxt)
    return out


def _good(pitches, leap, open_end=True):
    """One distinctive interval and no other leap; one highest note; stated, it ends off the root."""
    if not pitches:
        return False
    moves = [b - a for a, b in zip(pitches, pitches[1:])]
    big = [m for m in moves if abs(m) >= 5]
    top = max(pitches)
    return (len(big) == 1 and abs(big[0]) == leap and pitches.count(top) == 1
            and (not open_end or pitches[-1] % 12 != 0))


def _make(rng, scale, pitches, rhythm=None, leap=None, history=("new",)):
    ladder = _ladder(pitches)
    for attempt in range(300):
        size = leap or rng.choice(LEAPS)
        count = len(rhythm) if rhythm else rng.choice((3, 3, 4))
        if count < 3:
            count = 3
        leap_at = 0 if count == 3 else rng.choice((0, 1))
        up = rng.random() < 0.7
        notes = _contour(rng, ladder, count, size, leap_at, up)
        if _good(notes, size):
            beat = rhythm if rhythm and len(rhythm) == count else _rhythm(rng, count)
            return {"notes": tuple((off, p, length) for (off, length), p in zip(beat, notes)), "leap": size, "leap_at": leap_at,
                    "up": up, "scale": tuple(scale), "pitches": tuple(pitches), "salt": rng.randrange(1 << 30), "history": tuple(history)}
        if attempt > 150:
            leap = None                    # this leap has no room in this set: let another be tried
    raise ValueError("no motif fits this pitch set")


def motif(seed, scale, pitches, version=0):
    """The motif for these numbers (see the module's notes for `version`). A version dict may also carry "path":
    what development has done to the hook so far, ((how, seed, fate), ...) in order, each applied with
    mutate(m, how, seed, fate) before gen (as bassline.riff takes it)."""
    v = _version(version)
    path = tuple(tuple(step) for step in (version.get("path") or ())) if isinstance(version, dict) else ()
    m = _make(random.Random(repr(("motif", seed, v["motif"]))), scale, pitches)
    if v["motif"] > 0:
        m = mutate(_make(random.Random(repr(("motif", seed, v["motif"] - 1))), scale, pitches), "new", (seed, v["motif"]))
    for how, step_seed, fate in path:
        m = mutate(m, how, step_seed, fate)
    for g in range(v["gen"]):
        m = relative(m, (seed, "gen", g))
    return {**m, "version": tuple(sorted(v.items())) + ((("path", path),) if path else ())}


def statement(m):
    return list(m["notes"])


def answer(m):
    """The same head, the ending changed: the last note brought to the root or the fifth, by a step at most, and held
    a little longer. The answer closes where the statement stayed open."""
    *head, (off, p, length) = m["notes"]
    before = head[-1][1]
    ladder = _ladder(m["pitches"])
    ends = [q for q in ladder if q % 12 in (0, 7) and q != p and 1 <= abs(q - before) <= 4] or \
           [q for q in ladder if q % 12 in (0, 7) and abs(q - before) <= 4] or [p]
    end = min(ends, key=lambda q: (abs(q - p), q))
    return head + [(off, end, max(length, 2))]


def fragment(m, which=0):
    """A piece of it: 0, the two notes of its leap (from the first of them); 1, the whole of it an eighth later."""
    notes = list(m["notes"])
    if which == 1:
        return [(off + 2, p, length) for off, p, length in notes]
    i = m["leap_at"]
    start = notes[i][0]
    return [(off - start, p, length) for off, p, length in notes[i:i + 2]]


def relative(m, seed=0):
    """The motif that takes this one's place: the same distinctive interval, and one of: its contour turned over,
    the whole moved a step down (or up) the set, or the same notes on a new rhythm."""
    rng = random.Random(repr(("relative", seed, m["salt"], m["history"])))
    ladder = _ladder(m["pitches"])
    rhythm = tuple((off, length) for off, _, length in m["notes"])
    pitches = [p for _, p, _ in m["notes"]]
    ways = ["invert", "sequence", "rhythm"]
    rng.shuffle(ways)
    for attempt in range(60):
        how = ways[attempt % 3]
        if how == "rhythm":
            new = pitches
            beat = _rhythm(rng, len(pitches))
            if beat == rhythm:
                continue
        else:
            beat = rhythm
            up = not m["up"] if how == "invert" else m["up"]
            start = None
            if how == "sequence":
                i = ladder.index(pitches[0])
                j = i - 1 if i > 0 and rng.random() < 0.7 else i + 1
                start = ladder[min(max(j, 0), len(ladder) - 1)]
            new = _contour(rng, ladder, len(pitches), m["leap"], m["leap_at"], up, start)
        if _good(new, m["leap"]):
            return {**m, "notes": tuple((off, p, length) for (off, length), p in zip(beat, new)),
                    "up": (new[m["leap_at"] + 1] > new[m["leap_at"]]), "salt": rng.randrange(1 << 30), "history": m["history"] + (how,)}
    return {**m, "notes": tuple((off + 2, p, length) for off, p, length in m["notes"]) if m["notes"][-1][0] + m["notes"][-1][2] <= 6 else m["notes"],
            "salt": rng.randrange(1 << 30), "history": m["history"] + ("displaced",)}


HOW = {   # develop.py's `how` names, each onto one of this module's own changes
    "rhythm": "new same rhythm", "interval": "new same leap",                          # HOOK_KEEPS: what a new hook keeps
    "second_bass": "relative", "other_skeleton": "rewrite", "harder": "kept",           # RETURNS_HOW: the hook back changed
    "opposite_density": "relative", "half_cell_half_skeleton": "rewrite", "same_notes_new_rhythm": "new same rhythm",
    "down_step": "relative", "up_step": "relative", "up_fourth": "relative",            # TRANSPOSES: a sequence of it
    "anchor_b": "new same rhythm", "answer": "kept", "colour": "new same leap",         # KEEPS, as a hook can keep them
}
# MUTATIONS (develop's kept changes of a riff) are all a kept change here; the drums' names leave the hook alone
DRUMS_ONLY = ("carrier", "kick", "busier_carrier", "other_kick", "kick_and_carrier")
LEAVE = ("start", "hold", "hole", "back")


def mutate(m, how, seed=0, fate=None):
    """A new motif from this one: "kept" (one onset moved a sixteenth, or the last note held longer or shorter: the
    notes stay), "rewrite" (the notes up to and through the leap kept, the rest drawn again), "new" (a new motif
    that keeps this one's rhythm or its leap), "relative"; or any `how` develop.py gives (see HOW; its riff
    MUTATIONS are a kept change, its drums' names change nothing, None a new motif keeping nothing). fate: develop's
    fate, when given: "start", "hold", "hole" and "back" change nothing."""
    if fate in LEAVE or how in DRUMS_ONLY:
        return m
    if how is None:
        how = {"mutate": "kept", "rewrite": "rewrite", "A_changed": "kept", "transpose": "relative"}.get(fate, "new nothing")
    how = HOW.get(how, how)
    if how in ("drop_decoration", "add_pickup", "shift_decoration", "swap_pitch", "move_high_point", "switch_answer",
               "toward_deep", "toward_busy", "colour_note", "mutate"):
        how = "kept"
    if how == "relative":
        return relative(m, ("mutate", seed))
    rng = random.Random(repr(("mutate motif", how, seed, m["salt"], m["history"])))
    notes = list(m["notes"])
    if how == "new nothing":
        return _make(rng, m["scale"], m["pitches"], history=m["history"] + ("new",))
    if how == "new same rhythm":
        return _make(rng, m["scale"], m["pitches"], rhythm=tuple((off, length) for off, _, length in notes), history=m["history"] + ("new, same rhythm",))
    if how == "new same leap":
        return _make(rng, m["scale"], m["pitches"], leap=m["leap"], history=m["history"] + ("new, same leap",))
    if how in ("kept", "kept mutation"):
        for _ in range(20):
            i = rng.randrange(1, len(notes))
            off, p, length = notes[i]
            if rng.random() < 0.5 and i == len(notes) - 1:
                length = min(max(length + rng.choice((-1, 1)), 1), 8 - off)
            else:
                off += rng.choice((-1, 1))
            low = notes[i - 1][0] + 1
            high = notes[i + 1][0] - 1 if i + 1 < len(notes) else 8 - length
            if low <= off <= high and (off, length) != notes[i][::2]:
                notes[i] = (off, p, length)
                notes = [(o, q, min(n, (notes[k + 1][0] - o) if k + 1 < len(notes) else n)) for k, (o, q, n) in enumerate(notes)]
                return {**m, "notes": tuple(notes), "history": m["history"] + ("kept",)}
        return {**m, "history": m["history"] + ("kept",)}
    if how in ("rewrite", "rewrite part"):
        keep = m["leap_at"] + 2
        ladder = _ladder(m["pitches"])
        where = {p: i for i, p in enumerate(ladder)}
        for _ in range(60):
            pitches = [p for _, p, _ in notes[:keep]]
            for _ in notes[keep:]:
                j = where[pitches[-1]] + rng.choice((-1, 0, 1))
                pitches.append(ladder[min(max(j, 0), len(ladder) - 1)])
            if _good(pitches, m["leap"]):
                return {**m, "notes": tuple((off, p, length) for (off, _, length), p in zip(notes, pitches)),
                        "salt": rng.randrange(1 << 30), "history": m["history"] + ("rewrite",)}
        return relative(m, ("rewrite", seed))
    if how == "new":
        if rng.random() < 0.5:
            return _make(rng, m["scale"], m["pitches"], rhythm=tuple((off, length) for off, _, length in notes), history=m["history"] + ("new, same rhythm",))
        return _make(rng, m["scale"], m["pitches"], leap=m["leap"], history=m["history"] + ("new, same leap",))
    raise ValueError(f"mutate: {how!r} is not kept, rewrite or new")


def place(notes, low, salt=0):
    """Where in the bar the notes start: where they meet the fewest of the low end's onsets and sounding notes, late
    in the bar if it can be, never on the one or a snare. low: [(sixteenth, length)]."""
    onsets = {int(s) for s, _ in low}
    sounding = {int(s) + i for s, length in low for i in range(max(int(-(-length // 1)), 1))}
    best, chosen = None, LATE[0]
    for rank, start in enumerate(LATE):
        if start in NEVER:
            continue
        hits = [start + off for off, _, _ in notes]
        if hits[-1] >= 16:
            continue
        cost = (10 * sum(h in onsets for h in hits) + sum(h in sounding for h in hits) + 3 * sum(h in NEVER for h in hits[1:])
                + 0.15 * rank + 0.1 * _draw(salt, "place", start))
        if best is None or cost < best:
            best, chosen = cost, start
    return chosen


def block(m, number, low=None, bars=3):
    """The hook's eight bars, the ones bar `number` falls in: {bar in the eight: [(sixteenth, semis, length)]}.
    Stated in bar 4, its leap again in bar 5, answered in bar 8; further bars, when more are asked for, get its
    cousins (the whole an eighth later, or its relative), never a stranger."""
    count = int(min(max(bars, 1), 7))
    slots = SLOTS[:count] if count != 2 else SLOTS[:2]
    group = int(number) // 8
    lows = (lambda pos: low(pos)) if callable(low) else (lambda pos: (low or {}).get(pos, ()))
    shapes = {"statement": statement(m), "answer": answer(m), "fragment": fragment(m, 0), "displaced": fragment(m, 1)}
    home = place(shapes["statement"], lows(3), (m["salt"], group))
    out = {}
    for pos, kind in slots:
        shape = shapes.get(kind) or statement(relative(m, group))
        under = lows(pos)
        start = home if kind != "displaced" else home + 2
        onsets = {int(s) for s, _ in under}
        if start + shape[-1][0] >= 16 or start in NEVER or any(start + off in onsets for off, _, _ in shape):
            start = place(shape, under, (m["salt"], group, pos))     # where it sat does not suit this bar: placed again
        out[pos] = [(start + off, p, min(length, 16 - start - off)) for off, p, length in shape if start + off < 16]
    return out
