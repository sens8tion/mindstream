"""The chop engine: how a sound that has been cut into slices is played, four bars at a time, against the drums and
the other layers (docs/research/README.md, build step 1; 01_amen_chopping.md, 03_sample_placement.md,
04_legibility_beyond_repetition.md).

This replaces `chop.plan`'s fixed A A' A B, which the research measured and rejected.

How a group of four bars is made, for a break (the anchor) or a second break under it (the carrier):

- The four bars are one phrase, cut in units (an eighth in jungle) taken in blocks of one or three units, now and
  then five, each block played once or twice. A new block reads the sound at the place the phrase has reached, so
  what was on step 5 in the source lands on step 5 here; a replay reads the same place again, which is the break
  restarting on an offbeat (Collins's cutter, the 3+3+2 figure). Blocks are long early in the phrase and short,
  and more often replayed, late; about one phrase in five closes with one unit stuttered.
- The first bar of every group is played as it is in the sound: the plain bar the edits are measured against.
- The heaviest kind of slice is on the one in at least three bars of four, the sharpest on beat two always and on
  13, 15 or 11 for the second backbeat; a ghost stays only when the hit it leads to follows it; every slice keeps
  its own loudness, and the first downbeat of the phrase is the loudest.
- The edits are rationed per group: at most one roll (rising into the bar line), one reversed slice into a one,
  one empty downbeat; a reset kick, a half-time bar, the last snare pitched up, a drop-out at bar 8 of 8.
- The block partition and the backbeat choices are held for a section; inside it each group re-deals about half
  of the rest, as the drums do (deal.py): the group comes back half the same, the bar next door does not.

The other roles take the places the research gives them (the overlay in docs/research/README.md): a hook is a run
of a few slices in their own order, stated, back exactly four bars later, from step 9 on or in the gap at 6; a
stab sits off the beat, and on the one only at the start of a section; colour is quiet ghost accents in the back
half of the bar and a reversed lead-in at bar 8; a bed is a long slice, sparse. None of them takes the one when the
kick has it, or a snare's step, or a cell another layer already holds.

No numpy here: everything works on what `chop.measure` measured about each slice. Everything is drawn from the
seed and the bar with deal.py's stable hashing, so the same arguments always give the same plan.

Terms
    cut      one entry of `chop.measure`: {"pos", "len", "level", "punch", "tonal", ...} (samples, at the mixer's rate)
    group    four bars, 64 sixteenths, numbered 0..63 within the group
    event    what a layer does on one sixteenth of the group:
                 None                      carry on as you are
                 "rest"                    stop sounding here (a short fade)
                 {"slice": i,              play cut i from its start (or from its end, backwards, if "reverse")
                  "gain": g,               its loudness, 1.0 = as measured; the phrase's first downbeat is the loudest
                  "reverse": False,        played backwards
                  "semis": 0.0,            repitched by this many semitones
                  "gate": n or None}       cut off (short fade) after n sixteenths; None = its own length
"""
import math
import zlib

from .deal import SECTION, EIGHTH, ODD

ROLES = ("anchor", "carrier", "colour", "hook", "stab", "bed")
STYLES = ("jungle", "atmospheric", "drumfunk", "techstep", "breakcore", "footwork")
DEFAULT_STYLE = "jungle"

# The presets, one column per style. Sources: "01 R1" etc. are rules in docs/research/01_amen_chopping.md section 7,
# "01 7.6" its preset table (where a starred value is sourced and the rest is inference), "04" and "03" the other
# reports, "ref" the measured reference set (04 section 2.2). "inf" = inference, to be tuned by ear.
_TABLE = (
    #               jungle  atmos   drumfunk techstep breakcore footwork
    # cells in one cut unit. jungle 2 = eighths [01 R1, strong]; atmospheric eighths [01 7.6, inf]; drumfunk 1 =
    # per hit, taken as sixteenths [01 7.6*]; techstep per hit [01 7.6*]; breakcore 32nds [01 7.6*], floored at
    # the sixteenth grid a plan works on; footwork eighths [01 7.6, inf]
    ("unit",        2,      2,      1,       1,       1,        2),
    # block lengths in units, with weights. jungle 1 or 3, 5 rarely [01 R2, Collins; the 0.1 for 5 is inf];
    # atmospheric 3 or 4, drumfunk 1-3, breakcore 1-3, footwork 1 or 3 [01 7.6, inf]; techstep a fixed skeleton,
    # read a beat at a time [01 7.6 "fixed skeleton", inf]. All weights inf.
    ("blocks",      ((1, .45), (3, .45), (5, .1)), ((3, .6), (4, .4)), ((1, .3), (2, .3), (3, .4)), ((4, 1.0),),
                    ((1, .4), (2, .3), (3, .3)), ((1, .5), (3, .5))),
    # most times a block is played. jungle 2 [01 R3*]; atmospheric 1, drumfunk 2, techstep 1, breakcore 8,
    # footwork 2 [01 7.6, inf]
    ("reps",        2,      1,      2,       1,       8,        2),
    # chance a new block reads the sound where the phrase is; else it reads another beat of it, at the same place in
    # the beat. jungle 0.8: Collins reads in place [01 R4, strong], and now and then a bar is built from two source
    # bars [01 2.2, from [13]]; atmospheric 0.85, drumfunk 0.6, techstep 1.0, breakcore 0.1, footwork 1.0 [inf], set
    # so the share of slices off the spine that land where they were in the sound comes out near 01 7.6's
    # "position-true share" (0.6 / 0.85 / 0.5 / 1.0 / 0.2 / 0.6; chop_check measures it)
    ("true",        0.8,    0.85,   0.6,     1.0,     0.1,      1.0),
    # does a block read from elsewhere land at the same place in the beat (moves by a beat keep the feel [04 3.4]),
    # or anywhere? Anywhere only in breakcore ("no stable loop" [01 7.6*])
    ("anywhere",    False,  False,  False,   False,   True,     False),
    # where the second backbeat goes: weights for steps 13 / 15 / 11 [01 R10 and 7.6, inf]; breakcore "free"
    ("backbeat",    (.5, .3, .2), (.8, .2, 0), (.5, .3, .2), (.8, .1, .1), (.34, .33, .33), (.5, .3, .2)),
    # chance a phrase closes with one unit stuttered. jungle 0.2 [01 R6, Collins*]; atmospheric 0.1, drumfunk 0.2,
    # techstep 0.1, breakcore 0.8, footwork 0.2 [01 7.6, inf]
    ("stutter",     0.2,    0.1,    0.2,     0.1,     0.8,      0.2),
    # chance of a roll into the group's last bar line, when it did not stutter. 0.1 in jungle puts a fill at the
    # end of about one group in four with the stutter, as the reference measured [04 2.2: 6.5% of bars, one
    # opportunity in four]; the rest [inf, from 01 7.6's "rolls" row]
    ("roll",        0.1,    0.1,    0.15,    0.15,    0.5,      0.1),
    # chance per bar of a roll ending bar 2 or 3 instead (outside the phrase end). jungle "rare", atmospheric "no",
    # drumfunk "drummer fills", techstep "no", breakcore "yes", footwork "no" [01 7.6*; the numbers inf]
    ("roll_any",    0.05,   0.0,    0.15,    0.0,     0.4,      0.0),
    # chance of a reversed slice into a downbeat. jungle "sometimes", atmospheric "rare", drumfunk "tails*",
    # techstep "no", breakcore "yes*", footwork "rare" [01 7.6; the numbers inf]
    ("reverse",     0.2,    0.05,   0.3,     0.0,     0.5,      0.05),
    # chance of a half-time bar (one snare, on step 9). jungle "rare", techstep "sections*", footwork
    # "alternate*", the rest "no" [01 7.6, 01 O9; the numbers inf]
    ("half",        0.05,   0.0,    0.0,     0.1,     0.0,      0.5),
    # chance the last snare of the group is pitched up, and by how much. jungle +1 [01 O7, from [36]]; breakcore
    # an octave [01 O7, from [16]; 7.6 "wide*"]; the others "none" [01 7.6]; the chances inf
    ("pitch",       0.3,    0.0,    0.0,     0.0,     0.5,      0.0),
    ("semis",       1.0,    0.0,    0.0,     0.0,     12.0,     0.0),
    # chance of an empty downbeat (by preference the group's last bar) [01 R8: "allowed once per group"; numbers inf]
    ("empty",       0.25,   0.1,    0.25,    0.0,     0.4,      0.25),
    # bars a skeleton is held. jungle a section (deal.SECTION) [01 2.2 "per section"; ref: carrier changes in
    # blocks of 32]; atmospheric 32 [inf]; drumfunk 16 ["reset at 8 or 16", 01 7.6*]; techstep 32 ["16-32*"];
    # breakcore 4 ["continuous*", rewritten as it goes]; footwork 32 [inf]
    ("hold",        SECTION, SECTION, 16,    SECTION, 4,        SECTION),
    # how much of a group's deal comes back in the next group: jungle 0.5 [ref, as deal.RETURNS: lag 4 = 0.486];
    # atmospheric 0.7 ("3 of 4 alike"), drumfunk 0.4, techstep 0.8 ("all alike"), breakcore 0.15 ("none"),
    # footwork 0.5 [01 7.6 "bars alike within group", turned into a share: inf]
    ("returns",     0.5,    0.7,    0.4,     0.8,     0.15,     0.5),
    # chance of a reset kick at bar 8 of 8. drumfunk 0.5 (Paradox: "essential" [01 O3]); the rest [inf]
    ("kickback",    0.2,    0.1,    0.5,     0.0,     0.1,      0.1),
    # chance of a drop-out at bar 8 of 8: one of the four turnarounds 01 F4 names, so about one in four [inf]
    ("drop",        0.25,   0.3,    0.15,    0.3,     0.2,      0.3),
)
PRESETS = {style: {row[0]: row[1 + i] for row in _TABLE} for i, style in enumerate(STYLES)}

WINDOW = 0.1                 # chance a group's phrase starts half way through the sound: a two-bar phrase in effect [01 R5]; 0.1 puts lag 4 near the reference's +0.13 [tuned]
REPLAY = (0.25, 0.5)         # chance a block is played twice: at the phrase's start, and how much it grows by the end [01 R3, R7: Collins's 1 or 2 evenly, ramped; ramp inf]
SHAPE = 0.8                  # how hard a phrase leans to long blocks early and short ones late [01 R7: audible; size inf]
RAMP = (-12, -9, -6, -3)     # a roll's level hit by hit into the bar line, in dB [01 O4, from [36]]
BAR8 = (0.6, 0.6, 0.6, 1.5, 1.5, 0.8, 0.9, 1.5)    # how likely each bar of eight is to carry a hook or stab [03 R2]
HIT, QUIET, LOW = 1.3, 0.45, 0.3   # classify: attack ratio of a hit; level of a ghost against the loud ones; low share of a heavy one [inf]


def classify(cuts, slot_len):
    """Name each slice's class from what was measured, in place, and return `cuts`: adds "kind" (one of "heavy",
    "sharp", "ghost", "tone", "other") and "home" (the sixteenth, 0..15, its start falls on in the source when the
    source is read at the session's tempo).

    A hit (it peaks at once and its front is louder than its body) is a ghost when it is quiet against the loud
    ones, heavy when much of it is low (a kick, a thump, a heavy syllable), sharp otherwise (a snare, a clap, a
    consonant). A sound that is not a hit is a tone when it is mostly pitch, and other when mostly noise. Also adds
    "steps" (its length in sixteenths), "weight" and "edge" (how heavy and how sharp it is, for ranking)."""
    if not cuts:
        return cuts
    slot = max(float(slot_len), 1.0)
    levels = sorted(c["level"] for c in cuts)
    ref = levels[min(len(levels) - 1, int(0.9 * len(levels)))] or 1e-9
    for c in cuts:
        level = c["level"] + 1e-9
        loud = c["level"] / ref
        attack = c.get("attack", c["punch"] / level / 2.0)      # older cuts: peak over RMS, roughly on the same scale
        low = c.get("low", 0.0)
        bright = c.get("bright", 2000.0)
        hit = attack >= HIT and c.get("rise", 0.0) <= 0.03
        if hit:
            c["kind"] = "ghost" if loud < QUIET else "heavy" if low >= LOW else "sharp"
        else:
            c["kind"] = "tone" if c["tonal"] / level >= 0.5 else "other"
        c["home"] = int(round(c["pos"] / slot)) % 16
        c["steps"] = c["len"] / slot
        c["weight"] = loud * low
        c["edge"] = loud * min(bright / 4000.0, 1.5) * min(attack, 3.0)
    return cuts


def role_of(cuts, film=False):
    """The role a source would take by itself, from its slices: one of ROLES. A break (mostly hits, with heavy and
    sharp ones among them) is an anchor; hits without both are a carrier; a sound that is mostly pitch is a bed
    when its slices are long, a stab when they are few and short, a hook otherwise; noise is colour, or a bed when
    long [03 R0, R10]. A film's own sound is a hook unless it is drums or a bed."""
    if not cuts:
        return "colour"
    kinds = [c.get("kind", "other") for c in cuts]
    n = len(kinds)
    steps = sorted(c.get("steps", 4.0) for c in cuts)[n // 2]
    if sum(k in ("heavy", "sharp", "ghost") for k in kinds) >= 0.5 * n:
        return "anchor" if "heavy" in kinds and "sharp" in kinds and not film else "carrier"
    if sum(k == "tone" for k in kinds) >= 0.5 * n:
        return "bed" if steps >= 8 or n <= 2 else "stab" if n <= 4 and steps <= 3 and not film else "hook"
    if film:
        return "bed" if steps >= 8 else "hook"
    return "colour" if steps <= 4 else "bed"


_NEAREST = {"anchor": ("anchor", "carrier", "colour"), "carrier": ("carrier", "colour")}


def assign_roles(wants):
    """{layer name: role it wants} -> {layer name: role it gets}: one anchor and one carrier at a time, the others
    moved to the nearest free role. Stable: a layer that already holds anchor keeps it.

    First come, first served in the mapping's order, so pass the layers oldest first (as the mixer keeps them): the
    layer that took the anchor keeps it while newer ones that want it become the carrier, then colour."""
    out, held = {}, set()
    for name, want in wants.items():
        want = want if want in ROLES else "colour"
        role = next((r for r in _NEAREST.get(want, (want,)) if r not in held), "colour")
        if role in _NEAREST:
            held.add(role)
        out[name] = role
    return out


def _draw(*key):
    """A number from 0 to 1 that depends only on what it is given, as deal._draw, with the bits stirred after the
    checksum: a checksum alone gives neighbouring keys (bar 1, bar 2, ...) numbers that sit close together."""
    h = zlib.crc32(repr(key).encode())
    h = ((h ^ h >> 16) * 0x85EBCA6B) & 0xFFFFFFFF
    h = ((h ^ h >> 13) * 0xC2B2AE35) & 0xFFFFFFFF
    return (h ^ h >> 16) / 4294967296.0


def _pick(u, weights):
    """The index a number from 0 to 1 falls on, by weights."""
    x = u * sum(weights)
    for i, w in enumerate(weights):
        x -= w
        if x < 0:
            return i
    return len(weights) - 1


def _ev(i, gain=1.0, reverse=False, semis=0.0, gate=None):
    return {"slice": i, "gain": round(gain, 3), "reverse": reverse, "semis": float(semis), "gate": gate}


class _Layer:
    """What one plan needs, worked out once: the sound laid out on its own sixteenths, its slices by class, the
    keys the section's and the group's deals are drawn from."""

    def __init__(self, cuts, role, style, drums, taken, bar, seed, density, slot_len, turn, preset=None):
        self.cuts, self.n, self.role, self.turn, self.bar = cuts, len(cuts), role, turn, bar
        self.P = preset or PRESETS.get(style) or PRESETS[DEFAULT_STYLE]
        self.slot = max(float(slot_len), 1.0)
        self.density = min(max(float(density), 0.0), 1.0)
        self.taken = set(taken or ())
        rows = [d or {} for d in list(drums or ())[:4]]
        rows += [{}] * (4 - len(rows))
        self.kick = [set(d.get("kick", ())) for d in rows]
        self.snare = [set(d.get("snare", ())) for d in rows]
        self.kind = [c.get("kind", "other") for c in cuts]
        self.step = [int(round(c["pos"] / self.slot)) for c in cuts]
        self.L = 16 * max(1, round(max(c["pos"] + c["len"] for c in cuts) / self.slot / 16))   # the sound, in whole bars
        self.at = {}                                                                           # source sixteenth -> slice starting there
        for i, s in enumerate(self.step):
            s %= self.L
            if s not in self.at or cuts[self.at[s]]["level"] < cuts[i]["level"]:
                self.at[s] = i
        ranked = [i for i in range(self.n) if self.kind[i] != "ghost"] or list(range(self.n))
        self.heavy = sorted([i for i in ranked if self.kind[i] == "heavy"] or ranked, key=lambda i: -cuts[i].get("weight", 0.0))
        self.sharp = sorted([i for i in ranked if self.kind[i] == "sharp"] or ranked, key=lambda i: -cuts[i].get("edge", 0.0))
        self.hold = bar // self.P["hold"]
        self.sk = (seed, "chop", role, style, self.hold, turn)        # the section's skeleton: held
        self.gk = (seed, "chop", role, style, bar // 4, turn)         # this group's own deal
        self.lk = (seed, "lane", role, bar // SECTION, turn)          # a lane's template, held a section
        self.rolls, self.plain = 0, 0
        self.lift = {}                                                # cells whose gain is set by a figure (the stutter's crescendo)
        self.figure = set()                                           # cells of the group's one roll or stutter
        self.spine = {16 * j + s for j in range(4) for s in (0, 4, 12)}

    def deal(self, chance, what, c):
        """Does cell c sound? Half the time (by the style's share) by the section's deal for that place in the group,
        otherwise by this group's own: so a group is like the one before it, and the bars inside it are not."""
        if chance >= 1.0:
            return True
        key = self.gk if _draw(*self.gk, "which", what, c) >= self.P["returns"] else self.sk
        return _draw(*key, what, c) < chance

    def best(self, pool, home, near):
        """A slice of the class wanted: one that sat on this step in the source, nearest to where the plan is reading
        there, else the strongest of the class."""
        found = None
        for i in pool:
            if self.cuts[i]["home"] == home:
                d = abs(self.step[i] % self.L - near) if near is not None else 0
                if found is None or d < found[0]:
                    found = (d, i)
        return found[1] if found else pool[0]

    def lane_free(self, c):
        """Can a hook, stab, colour or bed start here? Not on a cell another layer holds, not on a snare, not on the
        one when the kick has it, not on the snare's beat two (kept clear in any case)."""
        j, s = divmod(c, 16)
        return c not in self.taken and s not in self.snare[j] and not (s == 0 and 0 in self.kick[j]) and s != 4

    def own(self, i):
        return max(1, int(math.ceil(self.cuts[i].get("steps", self.cuts[i]["len"] / self.slot) - 0.25)))


def _roll(x, ev, end, length, semis_step):
    """A roll: the sharpest slice retriggered on each sixteenth up to the bar line, rising -12, -9, -6, -3 dB."""
    before = ev[end - length - 1]
    before = before if isinstance(before, int) else before["slice"] if isinstance(before, dict) else None
    i = x.sharp[0] if x.sharp[0] != before or len(x.sharp) < 2 else x.sharp[1]
    for k, c in enumerate(range(end - length, end)):
        ev[c] = _ev(i, 10 ** (RAMP[4 - length + k] / 20.0), semis=semis_step * k, gate=1)
        x.figure.add(c)
    x.rolls += 1


def _break(x):
    """Four bars for the anchor or the carrier: blocks read in place, then the spine, then the rationed edits."""
    P, anchor = x.P, x.role == "anchor"
    unit = P["unit"]
    U, upb = 64 // unit, 16 // unit
    offset = 16 * ((x.hold + x.turn) % (x.L // 16))           # the window walks on through the sound, a section at a time
    if WINDOW and x.L >= 32 and _draw(*x.gk, "window") < WINDOW:
        offset += x.L // 32 * 16                              # some groups start half way through the sound
    if not anchor:                                            # the carrier: shifted a beat or a beat and a half, to interlock [01 O11]
        offset += (4, 6)[_draw(*x.sk, "shift") < 0.5]
    src, head, stut = [None] * 64, [False] * 64, [False] * 64
    lens = [b for b, _ in P["blocks"]]
    mean = sum(lens) / len(lens)
    # the plain bar: the first of every eight, otherwise dealt among the first three of the group [01 F5]
    x.plain = 0 if x.bar % 8 == 0 else int(_draw(*x.gk, "plain") * 3)
    plain = (x.plain * upb, x.plain * upb + upb)
    pos = k = 0
    closing, stutter = False, None
    while pos < U:
        left = U - pos
        if not closing and left < upb:                       # less than a bar to go: about one phrase in five stutters out
            closing = True
            if not x.rolls and _draw(*x.gk, "stutter") < P["stutter"]:     # after the last bar's step-5 snare
                stutter = max(pos, -(-53 // unit))
                x.rolls += 1
        if stutter is not None and pos >= stutter:
            c0 = pos * unit
            for c in range(c0, 64):
                fast = 64 - c <= 4 or unit == 1               # quickening to sixteenths on the last beat
                src[c] = (offset + c0 + (0 if fast else (c - c0) % unit)) % x.L
                head[c], stut[c] = fast or (c - c0) % unit == 0, True
            break
        if stutter is not None:
            left = stutter - pos
        if pos < plain[0]:                                    # nothing runs over into the plain bar
            left = min(left, plain[0] - pos)
        frac = pos / U
        w = [wt * max(0.05, 1 + SHAPE * (1 - 2 * frac) * ((l > mean) - (l < mean))) for l, wt in P["blocks"]]
        size = lens[_pick(_draw(*x.sk, k, "size"), w)]
        reps, true, key = 1, True, x.sk
        if not plain[0] <= pos < plain[1]:
            key = x.gk if _draw(*x.gk, k, "which") >= P["returns"] else x.sk
            if P["reps"] > 1 and _draw(*key, k, "rep") < REPLAY[0] + REPLAY[1] * frac:
                reps = 2 + int(_draw(*key, k, "more") * (P["reps"] - 1))
                if size * unit <= 2 and reps > 2:             # an eighth or less over and over is a roll: one a group,
                    span = range(pos * unit, min(pos + size * reps, U) * unit)     # and never over the spine
                    if x.rolls or any(c % 16 in (0, 4, 12) for c in span):
                        reps = 2
                    else:
                        x.rolls += 1
            true = _draw(*key, k, "true") < P["true"]
        if size * reps > left:                                # overshoot: one block fills the rest [01 R3]
            size, reps, true = left, 1, True
        here = pos * unit
        read = here
        if not true:                                          # from another beat of the sound, at the same place in the beat
            beats = x.L // 4
            b = int(_draw(*key, k, "where") * max(beats - 1, 1))
            b += b >= (here // 4) % beats
            read = 4 * (b % beats) + here % 4
            if P["anywhere"]:                                 # breakcore: no stable loop, any sixteenth of the sound
                read = int(_draw(*key, k, "anywhere") * x.L)
        for r in range(reps):
            c0 = (pos + r * size) * unit
            head[c0] = True
            if reps > 2 and size * unit <= 2:                 # the roll rises into where it ends
                x.lift[c0] = 0.55 + 0.45 * r / (reps - 1)
                x.figure.add(c0)
            for y in range(size * unit):
                src[c0 + y] = (offset + read + y) % x.L
        pos += size * reps
        k += 1

    ev, stutter_slice, lively = [None] * 64, None, x.density
    for c in range(64):
        if src[c] is None or (stut[c] and not head[c]):
            continue
        i = x.at.get(src[c])
        if stut[c]:
            if stutter_slice is None:
                stutter_slice = i if i is not None and (anchor or x.kind[i] != "heavy") else x.sharp[0]
            ev[c] = stutter_slice
            heads = [m for m in range(64) if stut[m] and head[m]]
            x.lift[c] = 0.55 + 0.45 * heads.index(c) / max(len(heads) - 1, 1)     # rising into the bar line
            x.figure.add(c)
            continue
        if i is None:
            continue
        kind = x.kind[i]
        if anchor:
            chance = 1.0 if kind in ("heavy", "sharp") else 0.45 + 0.45 * lively if kind == "ghost" else 0.55 + 0.4 * lively
        else:
            j, s = divmod(c, 16)
            if kind == "heavy" or c in x.spine or s in x.kick[j] or s in x.snare[j]:
                continue                                      # the carrier leaves the low end and the spine alone
            chance = (EIGHTH if c % 2 == 0 else ODD) * (0.35 + 0.65 * lively) * 1.4
        if x.deal(chance, "deal", c):
            ev[c] = i

    # the edits, rationed for the group [01 F5]
    g = lambda *what: _draw(*x.gk, *what)
    turnaround = (x.bar + 3) % 8 == 7                         # the group's last bar is bar 8 of 8
    drop = turnaround and g("drop") < P["drop"]
    kickback = turnaround and not drop and stutter is None and g("kickback") < P["kickback"]
    empty = anchor and not kickback and g("empty") < P["empty"]
    half = (1 + (g("half bar") < 0.5)) if anchor and g("half") < P["half"] else None
    half = None if half == x.plain else half
    backbeat = [12] * 4
    if anchor:
        for j in range(4):                                    # the spine: heavy on the one, sharp on 5 and on 13, 15 or 11
            c0, near = 16 * j, src[16 * j]
            if not (j == 3 and empty) and (ev[c0] is None or x.kind[ev[c0]] != "heavy"):
                ev[c0] = x.best(x.heavy, 0, near)
            if j == half:
                for s in (4, 10, 12, 14):
                    if ev[c0 + s] is not None and not isinstance(ev[c0 + s], str) and x.kind[ev[c0 + s]] == "sharp":
                        ev[c0 + s] = None
                ev[c0 + 8] = x.best(x.sharp, 8, src[c0 + 8])
                continue
            if ev[c0 + 4] is None or x.kind[ev[c0 + 4]] != "sharp":
                ev[c0 + 4] = x.best(x.sharp, 4, src[c0 + 4])
            here = [s for s in (12, 14, 10) if ev[c0 + s] is not None and x.kind[ev[c0 + s]] == "sharp"]
            if j == x.plain:                                  # the plain bar keeps the source's own backbeat
                backbeat[j] = here[0] if here else 12
            else:                                             # displaced more in bars 3 and 4, as in the Amen itself
                w13, w15, w11 = P["backbeat"]
                lean = 0.5 if j == 1 else 1.5
                backbeat[j] = (12, 14, 10)[_pick(_draw(*x.sk, "backbeat", j), (w13, w15 * lean, w11 * lean))]
            t = backbeat[j]
            if t not in here and not stut[c0 + t] and not (x.figure and min(x.figure) <= c0 + t <= max(x.figure)):
                ev[c0 + t] = x.best(x.sharp, t, src[c0 + t])
            if t != 12 and 12 in here and not stut[c0 + 12]:
                ev[c0 + 12] = None
        if empty:
            ev[48] = "rest"
    if drop:                                                  # the turnaround: the last beat or two left empty [01 O10]
        cut = 56 if g("drop len") < 0.5 else 60
        ev[cut:] = ["rest"] + [None] * (63 - cut)
    if kickback and anchor:                                   # one plain kick resets the loop [01 O3]
        ev[56:60] = [_ev(x.best(x.heavy, 0, None), 0.95, gate=4), None, None, None]
    if not x.rolls and not drop:
        for j in (1, 2):
            if not x.rolls and j != x.plain and g("roll any", j) < P["roll_any"]:
                _roll(x, ev, 16 * j + 16, 3, 0)
        if not x.rolls and g("roll") < P["roll"]:
            _roll(x, ev, 64, 3 + (g("roll len") < 0.5), 1 if P["semis"] and g("roll pitch") < 0.3 else 0)
    if g("reverse") < P["reverse"]:                           # a reversed slice ending on a downbeat [01 O6]
        short = [i for i in x.sharp if x.own(i) <= 3] or [i for i in range(x.n) if x.own(i) <= 3]
        for j in (3, 1):
            end = 16 * j + 16
            if not short or j == x.plain or drop and j == 3 or any(isinstance(e, dict) and e["gate"] == 1 for e in ev[end - 4:end]) or any(stut[end - 4:end]):
                continue
            i = short[0]
            start = end - x.own(i)
            if start - 16 * j <= backbeat[j]:
                continue
            ev[start:end] = [_ev(i, 0.9, reverse=True, gate=x.own(i))] + [None] * (end - start - 1)
            break
    if P["semis"] and g("pitch") < P["pitch"]:               # the last snare of the group pitched up [01 O7]
        for c in range(63, 47, -1):
            if isinstance(ev[c], int) and x.kind[ev[c]] == "sharp" and c not in x.lift and not stut[c]:
                ev[c] = _ev(ev[c], 0.95, semis=P["semis"])
                break
    if not anchor:                                            # the carrier keeps off the spine and the kit's hits, edits included
        for c in range(64):
            j, s = divmod(c, 16)
            if c in x.spine or s in x.kick[j] or s in x.snare[j]:
                ev[c] = None
    return ev


def _lanes(x):
    """Four bars for a hook, stab, colour or bed, in the places the overlay gives them."""
    ev, n, d, role = [None] * 64, x.n, x.density, x.role
    l = lambda *what: _draw(*x.lk, *what)
    if role == "hook":                                        # a run of slices in their own order, stated and answered [03 R6, 04 #9]
        k = min(n, 2 + int(l("length") * 3))
        w = int(l("from") * n)
        run, at = [], 0
        for m in range(k):
            i = (w + m) % n
            if m:
                at += min(max(int(round((x.cuts[i]["pos"] - x.cuts[run[-1][0]]["pos"]) / x.slot)), 1), 3)
            run.append((i, at))
        start = (8, 9, 10, 5, 11)[(_pick(l("start"), (1.0, 0.8, 0.7, 0.6, 0.5)) + x.turn) % 5]   # from step 9 on, or in the gap at 6
        for j in range(4):
            b, b8 = x.bar + j, (x.bar + j) % 8
            first = _pick(l("first", b // 8), BAR8[:4])
            extra = [e for e in range(8) if e not in (first, first + 4) and abs(e - first) > 1 and abs(e - first - 4) > 1]
            extra = sorted(extra, key=lambda e: -BAR8[e] * l("extra", b // 8, e))[:(d >= 0.4) + (d >= 0.8)]
            if b8 in (first, first + 4):
                shape = run                                   # the statement, and four bars later the same exactly
            elif b8 in extra:
                shape = run[:2]                               # a fragment of it
            else:
                continue
            best = []
            for at0 in (start,) + tuple(a for a in (8, 9, 10, 11, 5) if a != start):   # the section's place, else the nearest that fits
                placed, last = [], -1
                for i, at in (shape[:1] if at0 == 5 else shape):  # the gap at 6 holds one short answer, no more
                    c = 16 * j + at0 + at
                    for c in (c, c + 1, c + 2):               # each slice may slip a sixteenth or two past a held cell
                        if c > last and c <= 16 * j + 15 and x.lane_free(c):
                            placed.append((c, i))
                            last = c
                            break
                if len(placed) > len(best):
                    best = placed
                if len(placed) == len(shape):
                    break
            for c, i in best:
                ev[c] = _ev(i)
    elif role == "stab":                                     # off the beat, held for a section, varied by leaving out [03 R3, R5]
        cand, wts = (6, 5, 10, 14, 2, 7, 11, 13, 15, 3), [1.0, 0.9, 0.9, 0.8, 0.6, 0.5, 0.6, 0.5, 0.5, 0.4]
        places = []
        for m in range(1 + round(2 * d)):
            p = _pick(l("place", m), wts)
            places.append(cand[p])
            wts[p] = 0.0
        punchy = sorted(range(n), key=lambda i: -x.cuts[i]["punch"])[:2]
        for j in range(4):
            b = x.bar + j
            if b % SECTION == 0 and 16 * j not in x.taken:   # the one is a stab's only at the start of a section
                ev[16 * j] = _ev(punchy[0], gate=2)
            if not x.deal(BAR8[b % 8] / 1.5 * (0.5 + 0.5 * d), "bar", j):
                continue
            for s in places:
                c = 16 * j + s
                if x.lane_free(c) and _draw(*x.gk, "omit", c) < 0.85:
                    ev[c] = _ev(punchy[_draw(*x.gk, "which stab", c) < 0.3 and len(punchy) > 1], gate=4 if _draw(*x.gk, "long", c) < 0.25 else 2)
    elif role == "colour":                                   # quiet accents on the weak steps at the back of the bar [03 R10]
        cand, wts = (9, 11, 13, 15, 10, 14, 7, 3), [1.0, 1.0, 0.8, 1.0, 0.6, 0.6, 0.5, 0.4]
        places = []
        for m in range(2 + (d > 0.6)):
            p = _pick(l("place", m), wts)
            places.append(cand[p])
            wts[p] = 0.0
        light = [i for i in range(n) if x.kind[i] != "heavy"] or list(range(n))     # the low end is the kick's and the sub's
        short = sorted(light, key=lambda i: x.cuts[i]["len"])[:max(2, len(light) // 3)]
        for j in range(4):
            if not x.deal(0.5 + 0.4 * d, "bar", j):
                continue
            for s in places:
                c = next((16 * j + t for t in (s, s + 1, s - 1) if 0 < t < 16 and x.lane_free(16 * j + t) and ev[16 * j + t] is None), None)
                if c is not None and x.deal(0.6, "place", 16 * j + s):
                    ev[c] = _ev(short[int(_draw(*x.gk, "slice", c) * len(short))], 0.6 + 0.1 * _draw(*x.gk, "gain", c), gate=1)
        if (x.bar + 3) % 8 == 7 and _draw(*x.gk, "lead in") < 0.5:   # a reversed lead-in ending on the next one [03 R8]
            fit = sorted(range(n), key=lambda i: abs(x.own(i) - 4))
            i = fit[0]
            start = 64 - min(x.own(i), 8)
            if start not in x.taken:
                ev[start:] = [_ev(i, 0.8, reverse=True, gate=64 - start)] + [None] * (63 - start)
    else:                                                    # bed: one long slice now and then, walking through the sound [03 R4]
        every = 1 if d >= 0.6 else 2 if d >= 0.3 else 4
        long = sorted(range(n), key=lambda i: -x.cuts[i]["len"])[:max(1, n // 2)]
        long.sort()
        for j in range(4):
            b = x.bar + j
            if b % every:
                continue
            c = next((16 * j + s for s in (0, 2, 1, 3, 6) if x.lane_free(16 * j + s)), None)
            if c is not None:
                ev[c] = _ev(long[(b // every + int(l("from") * len(long))) % len(long)], 0.6)
    return ev


def plan(cuts, *, role, style, drums, taken, bar, seed, density, slot_len, turn=0, held=False, preset=None):
    """Four bars of events (a list of 64) for one layer.

    cuts      classified cuts (`classify` already run)
    role      one of ROLES
    style     one of STYLES (the chop preset)
    drums     four dicts, one per bar of the group: {"kick": [sixteenths], "snare": [sixteenths]}
    taken     set of cells (0..63) that layers already planned for this group hold: this layer keeps off them
    bar       the absolute number of the group's first bar (a multiple of 4); its section is bar // deal.SECTION
    seed      a stable key for this layer (its name), so two layers with the same sound still differ
    density   0 sparse .. 1 dense
    slot_len  samples in a sixteenth
    turn      mutated by hand: the same material put in other places (0 = as dealt)
    held      held by hand: the group's plan does not change from group to group until it is mutated again
    preset    the style's column of _TABLE as something else has it (edge.chop_preset: the dials applied; the
              development's processing clock): a dict with every key of PRESETS[style]. None: PRESETS[style].
              The keys the deals are drawn from still name the style, so a preset equal to the style's own plans
              exactly as no preset does

    The same arguments always give the same plan.

    Plan the anchor first, then the carrier, then the others, each with the cells of those before it in `taken`:
    the anchor keeps its spine only on cells nobody holds. When held, `bar` is not read: the plan is the one dealt
    for the first group (bar 0) with this seed and turn."""
    if not cuts:
        return [None] * 64
    if "kind" not in cuts[0]:
        classify(cuts, slot_len)
    bar = 0 if held else int(bar) - int(bar) % 4
    role = role if role in ROLES else "colour"
    x = _Layer(cuts, role, style, drums, taken, bar, seed, density, slot_len, int(turn), preset)
    ev = _break(x) if role in ("anchor", "carrier") else _lanes(x)
    for c in x.taken:
        if 0 <= c < 64:
            ev[c] = None
    if role in ("anchor", "carrier"):
        _unroll(x, ev)
        _ghosts(x, ev)
        _differ(x, ev)
    return _finish(x, ev)


def _unroll(x, ev):
    """Only the group's one roll or stutter may retrigger a slice: three starts of the same slice close together,
    met by chance (a replay next to a block read from elsewhere), lose the ones that are not the figure's."""
    starts = [(c, e if isinstance(e, int) else e["slice"]) for c, e in enumerate(ev) if isinstance(e, (int, dict))]
    k = 0
    while k < len(starts):
        m = k
        while m + 1 < len(starts) and starts[m + 1][1] == starts[k][1] and starts[m + 1][0] - starts[m][0] <= 2:
            m += 1
        run = [c for c, _ in starts[k:m + 1]]
        loose = [c for c in run if c not in x.figure]
        if len(run) >= 3 and loose:
            kept = [c for c in loose if x.role == "anchor" and c in x.spine]       # the spine stays
            spare = [c for c in loose if c not in kept]
            for c in spare[1::2] if spare and len(spare) == len(run) else spare:
                ev[c] = None
            if kept and len(loose) < len(run):                # a spine hit next to the figure: the figure takes another slice
                other = next((i for i in x.sharp if i != starts[k][1]), None)
                for c in run:
                    if c in x.figure and other is not None:
                        ev[c] = other if isinstance(ev[c], int) else dict(ev[c], slice=other)
        k = m + 1


def _ghosts(x, ev):
    """A ghost stays only with the hit it leads to: the next thing within two sixteenths is a hit, or another
    ghost that stays [01 7.1, from [44]]."""
    keep = False
    for c in range(63, -1, -1):
        e = ev[c]
        i = e if isinstance(e, int) else e["slice"] if isinstance(e, dict) else None
        if i is None:
            continue
        if x.kind[i] == "ghost" and isinstance(e, int):
            nxt = next((m for m in range(c + 1, c + 3) if ev[m % 64] is not None), None)
            ok = nxt is not None and (nxt >= 64 or isinstance(ev[nxt], (int, dict)) and _accent(x, ev[nxt], keep))
            if not ok:
                ev[c] = None
                continue
            keep = True
        else:
            keep = False


def _accent(x, e, ghost_kept):
    i = e if isinstance(e, int) else e["slice"]
    return x.kind[i] in ("heavy", "sharp") or x.kind[i] == "ghost" and ghost_kept


def _differ(x, ev):
    """Four different bars: a bar that came out the same as another in the group loses one of its lighter hits
    (never on the spine, never in the plain bar)."""
    sig = lambda j: tuple(e if not isinstance(e, dict) else (e["slice"], e["reverse"], e["semis"]) for e in ev[16 * j:16 * j + 16])
    for j in range(1, 4):
        for i in range(j):
            if sig(i) != sig(j):
                continue
            m = i if j == x.plain else j
            spare = [16 * m + s for s in range(16) if 16 * m + s not in x.spine and isinstance(ev[16 * m + s], int)]
            if spare:
                ev[spare[int(_draw(*x.gk, "differ", m) * len(spare))]] = None


def _finish(x, ev):
    """Every slice as an event at its own loudness, the phrase's first downbeat the loudest, each gated where it
    would run into the next thing this layer does."""
    anchor, carrier = x.role == "anchor", x.role == "carrier"
    for c, e in enumerate(ev):
        if isinstance(e, int):
            spread = 0.85 + 0.15 * _draw(*x.gk, "gain", c) if x.kind[e] in ("heavy", "sharp") else 0.9 + 0.1 * _draw(*x.gk, "gain", c)
            ev[c] = _ev(e, x.lift.get(c, spread) * (0.7 if carrier else 1.0))
    if anchor and isinstance(ev[0], dict):                    # the first downbeat of the phrase is the loudest [01 R13]
        level = lambda e: x.cuts[e["slice"]]["level"] * e["gain"]
        others = max((level(e) for e in ev[1:] if isinstance(e, dict)), default=0.0)
        ev[0]["gain"] = round(max(ev[0]["gain"], min(2.5, 1.05 * others / (x.cuts[ev[0]["slice"]]["level"] + 1e-9))), 3)
    cap = {"hook": 8, "carrier": 1, "colour": 1}.get(x.role)
    first = next((c for c in range(64) if ev[c] is not None), None)
    nxt = None
    for c in range(63, -1, -1):
        e = ev[c]
        if e is None:
            continue
        if isinstance(e, dict):
            room = (nxt if nxt is not None else 64 + first) - c
            own = x.cuts[e["slice"]].get("steps", x.own(e["slice"]))
            gates = [g for g in (e["gate"], room if own > room else None, cap if cap and own > cap else None) if g]
            e["gate"] = min(gates) if gates else None
        nxt = c
    return ev


def cells(events):
    """The cells (0..63) where a plan starts a slice: what it holds, for `taken`."""
    return {i for i, e in enumerate(events) if isinstance(e, dict)}
