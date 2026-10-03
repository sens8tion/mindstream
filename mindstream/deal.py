"""How a bar is dealt: what the drums, the sub and the tune play, by the measured habits of the music and not by loop.

The numbers here come from the jungle research kept in the thelmic project (tracks/2026-09-16_reaper/README.md:
seven measurements of a twenty-one minute reference set; tracks/2026-09-16_jungle_scene_rules.md: the working
rules drawn from them). What they say, and what is done about each here:

- Nothing is a loop. Each bar is dealt afresh from a set of chances: the spine (the kick on the one, the snares on
  two and four) always plays; a style's other written hits nearly always; the other eighths about two times in
  three; the odd sixteenths about one in three. Neighbouring bars are as unlike as chance makes them, but the
  four-bar group comes back half the same (`bar`).
- A fill closes a four-bar group about one time in four, and it is short (`fill`). "Three bars and a fill" is not
  what the music does.
- The sub and the hook are no longer dealt here: the sub plays a stored riff (bassline.py) and the tune a motif
  that belongs to it (motif.py). HOOK_LOW and HOOK_BARS, where hooks sit and how many bars of eight carry one,
  are still kept here.
- A break is taking the low end away while the drums keep running, with no riser; it is preceded by a roll about
  one time in four and by a gap about one time in four, and the gap is one sixteenth (`break_ending`).

No numpy and no sound here: only what is played when. Everything is dealt from numbers given in (a seed and the
bar), so the same moment always deals the same way and a memory can bring a bar back.
"""
import random
import zlib

SPINE, WRITTEN, EIGHTH, ODD = 1.0, 0.88, 0.67, 0.34     # the chance of a hit: on the spine, written in the style, on another eighth, on an odd sixteenth
RETURNS = 0.5                 # how much of a bar's deal is the four-bar group's own (the rest is dealt for that bar alone)
FILL, ROLL, GAP = 0.25, 0.27, 0.27
HOOK_LOW, HOOK_SPAN = 58, 10  # hooks sit from A#3 (233 Hz) up to about G4 (392 Hz): as a MIDI note and the semitones above it
HOOK_BARS = 3                 # of every eight
# the styles played as breaks: dealt as above, with ghost snares and a carrier of hats on the sixteenths. The rest
# (four on the floor and its kin, half time) keep their written hats and take only a little of the dealing.
BREAKS = frozenset(("dnb", "twostep", "broken", "two_step", "shuffled_two_step", "stutter", "rolling", "breakbeat_hardcore", "amen"))
SPINE_STEPS = {"kick": (0,), "snare": (4, 12)}
SURE = {"dnb": {"kick": {10: 0.7}}}      # the second kick of the spine, on the "and" of three: in two bars of three


def _draw(*key):
    """A number from 0 to 1 that depends only on what it is given. (Quick: this is asked a few hundred times a bar,
    from the thread that makes the sound.) The checksum's bits are stirred after it: a checksum alone gives
    neighbouring keys (bar 1, bar 2 ...) numbers that sit close together, so the deals clustered."""
    h = zlib.crc32(repr(key).encode())
    h = ((h ^ h >> 16) * 0x85EBCA6B) & 0xFFFFFFFF
    h = ((h ^ h >> 13) * 0xC2B2AE35) & 0xFFFFFFFF
    return (h ^ h >> 16) / 4294967296.0


def _hit(chance, seed, bar, part, slot, returns=None):
    """Does this slot sound in this bar? Half the time by the four-bar group's own deal for that place in the group,
    half by a deal for this bar alone: so bar five is like bar one, and bar two is not. (returns: the group's share as
    the edge has moved it; None is RETURNS.)"""
    if chance >= 1.0:
        return True
    own = _draw(seed, "bar", bar, part, slot)
    source = own if _draw(seed, "which", bar, part, slot) >= (RETURNS if returns is None else returns) else _draw(seed, "group", bar % 4, part, slot)
    return source < chance


def bar(pattern, style, energy, number, seed, exact=(), busier=0.0, numbers=None):
    """One bar of drums: {"kick": {sixteenth: how hard, 0 to 1}, "snare": {...}, "ghost": {...}, "hats": {...}, "open": {...}}.

    pattern: the sixteenths written for each drum ({"kick": [...], "snare": [...], "hats": [...], "open": [...]}).
    exact: parts whose pattern was written by hand; they play exactly as written, every bar.
    busier: added to the energy for the hats and ghosts (a break is busier, not emptier).
    numbers: the chances as the edge's dials have them (edge.deal_numbers: RETURNS, WRITTEN, EIGHTH, ODD,
    SNARE_SPINE, GHOST); None, or any left out, as written at the top of this file. They are passed in and never
    set here, so a bar is never dealt half by one set of numbers and half by another."""
    n = numbers or {}
    returns, written_chance = n.get("RETURNS", RETURNS), n.get("WRITTEN", WRITTEN)
    eighth, odd, snare_spine, ghosts = n.get("EIGHTH", EIGHTH), n.get("ODD", ODD), n.get("SNARE_SPINE", SPINE), n.get("GHOST", 1.0)
    breaks, e = style in BREAKS, min(max(float(energy), 0.0), 1.0)
    sure = SURE.get(style, {})
    out = {"kick": {}, "snare": {}, "ghost": {}, "hats": {}, "open": {}}
    for part in ("kick", "snare"):
        for slot in pattern.get(part, ()):
            if part in exact:
                chance = SPINE
            elif slot in SPINE_STEPS[part]:                 # the kick on the one never moves; the backbeat only at the restless end
                chance = SPINE if part == "kick" else snare_spine
            else:
                chance = sure.get(part, {}).get(slot, written_chance)
            if _hit(chance, seed, number, part, slot, returns):
                out[part][slot] = 1.0
    if "kick" not in exact and pattern.get("kick"):          # now and then a pickup into the next beat, never a fast double
        for slot in (6, 14):
            if slot not in out["kick"] and slot - 1 not in out["kick"] and (slot + 1) % 16 not in pattern["kick"] and _hit(0.1 * e, seed, number, "pickup", slot, returns):
                out["kick"][slot] = 0.6
    lively = min(max(e + busier, 0.0), 1.0)
    if breaks and "snare" not in exact and pattern.get("snare"):                  # ghost snares: quiet, uneven, in the gaps
        for slot in (1, 3, 7, 9, 11, 15, 6, 10, 14):
            if slot in out["snare"] or slot in out["kick"]:
                continue
            if _hit((0.20 if slot % 2 else 0.10) * (0.4 + lively) * ghosts, seed, number, "ghost", slot, returns):
                out["ghost"][slot] = 0.22 + 0.3 * _draw(seed, "soft", number, slot)
    written, opens = set(pattern.get("hats", ())), set(pattern.get("open", ()))
    for slot in range(16):
        if slot in opens:
            if "hats" in exact or _hit(written_chance, seed, number, "open", slot, returns):
                out["open"][slot] = 1.0
            continue
        if "hats" in exact:
            chance = 1.0 if slot in written else 0.0
        elif slot in written:
            chance = written_chance
        elif breaks:                                         # the carrier: the sixteenths filled in, the eighths more than the ones between
            chance = (eighth if slot % 2 == 0 else odd) * (0.35 + 0.65 * lively) * (0.6 if slot in out["snare"] or slot in out["kick"] else 1.0)
        else:
            chance = 0.08 * lively if slot % 2 == 0 else 0.0
        if chance > 0 and _hit(chance, seed, number, "hats", slot, returns):
            accent = 1.0 if slot % 4 == 0 else 0.8 if slot % 2 == 0 else 0.55
            out["hats"][slot] = accent if "hats" in exact else accent * (0.8 + 0.4 * _draw(seed, "tick", number, slot))
    return out


SECTION = 32                  # bars that hold one identity: the drums' variants, the sub's riff, the hook, the lead's voice
FORMS = ("AABA", "ABAC", "AABC", "ABAB")      # the order a four-bar group takes its bars in, chosen once a section


def held_bar(pattern, style, energy, number, seed, exact=(), busier=0.0, material=None, numbers=None):
    """One bar of drums, from a section's own small set of bars instead of a fresh deal every bar.

    At the start of each section of thirty-two bars three bars are dealt (A, B and C, by the chances in `bar`) and an
    order for the four-bar group is chosen once (A A B A, A B A C, A A B C or A B A B); every group in the section then
    plays that order. Only the quiet ghost snares are dealt afresh each bar: the small decorations. So the drums have
    an identity that is held, and a few written alternatives on a fixed cycle, which is what producers' variation
    looks like, where chance choosing every hit read as random (docs/research/07_good_edm.md).

    material: which drums these are when development (develop.py) says so, instead of the section count:
    (version, changes). A version is a set of bars and its order: the B drums at 32 are a new version, so the kick and
    the carrier are dealt again with everything else; A back at 64 is the first version again. changes: the kept
    changes made to that version since it was first dealt, in order (develop's DRUM_HOW and DRUM_RETURNS): "kick" and
    "other_kick" deal the kick again, "carrier" and "busier_carrier" the hats (the second busier), "harder" makes the
    hats and the ghosts busier from there on. numbers: the edge's chances, as `bar` takes them."""
    if material is None:
        section = number // SECTION
        form = FORMS[int(_draw(seed, "form", section) * len(FORMS)) % len(FORMS)]
        key = lambda which: (section * 7 + which) * 1000003 + 11                                   # noqa: E731
        changes = ()
    else:
        version, changes = int(material[0]), tuple(material[1] or ())
        form = FORMS[int(_draw(seed, "form", "drums", version) * len(FORMS)) % len(FORMS)]
        key = lambda which, *more: int(_draw(seed, "drums", version, which, *more) * 2 ** 40) * 4 + which     # noqa: E731
    which = "ABC".index(form[number % 4])
    held = bar(pattern, style, energy, key(which), seed, exact, busier, numbers)
    lift = 0.0
    for i, how in enumerate(changes):                        # each kept change, on top of the ones before it
        if how == "harder":
            lift += 0.15
            held["hats"] = bar(pattern, style, energy, key(which), seed, exact, busier + lift, numbers)["hats"]
        elif how in ("kick", "other_kick"):
            held["kick"] = bar(pattern, style, energy, key(which, "kick", i), seed, exact, busier + lift, numbers)["kick"]
        elif how in ("carrier", "busier_carrier"):
            lift += 0.15 if how == "busier_carrier" else 0.0
            again = bar(pattern, style, energy, key(which, "carrier", i), seed, exact, busier + lift, numbers)
            held["hats"], held["open"] = again["hats"], again["open"]
    held["ghost"] = bar(pattern, style, energy, number, seed, exact, busier + lift, numbers)["ghost"] if "snare" not in exact else {}
    for slot in list(held["ghost"]):
        if slot in held["snare"] or slot in held["kick"]:
            del held["ghost"][slot]
    return held


def acid_line(seed, scale_steps=(0, 0, 0, 2, 4, -1, 4, 7)):
    """A sixteen-step line for the acid voice: which steps sound, at what scale step, which are accented, which slide
    in from the note before, and which are held into the next step. Drawn once and kept: the line stays, the filter
    moves. [(step, scale step, accent, slide, held)]"""
    rng = random.Random(repr(("acid", seed)))
    out, last = [], None
    for step in range(16):
        if rng.random() > (0.85 if step % 4 == 0 else 0.62):
            last = None
            continue
        degree = rng.choice(scale_steps) if last is None or rng.random() < 0.55 else last
        out.append((step, degree, rng.random() < (0.45 if step % 4 == 0 else 0.22), last is not None and rng.random() < 0.25, rng.random() < 0.15))
        last = degree
    return out


FILLS = (((14, 0.6), (15, 0.85)), ((13, 0.5), (14, 0.65), (15, 0.85)), ((11, 0.5), (14, 0.7)), ((12, 0.6), (13, 0.45), (15, 0.8)), ((10, 0.5), (11, 0.6), (15, 0.8)))


def fill(number, seed, numbers=None):
    """The fill that closes this bar, if it has one: [(sixteenth, how hard)] on the snare. Only the last bar of a
    four-bar group can have one, and about one in four does (numbers: the edge's FILL, as `bar` takes them)."""
    if number % 4 != 3 or _draw(seed, "fill", number) >= (numbers or {}).get("FILL", FILL):
        return []
    return list(FILLS[int(_draw(seed, "which fill", number) * len(FILLS)) % len(FILLS)])


def break_ending(seed, started):
    """How a break ends: (is there a short roll into the return, is the last sixteenth left empty). Each about one
    time in four; never a riser."""
    return _draw(seed, "roll", started) < ROLL, _draw(seed, "gap", started) < GAP
