"""The edge: two dials over the whole engine, and the budget that keeps it on the lip (docs/research/README.md, build
step 5; 04_legibility_beyond_repetition.md section 5, "Dials for the edge").

A dry sample is legible. Damage pushes it to a lip where legibility is partial and interest peaks; further is noise,
tolerable only briefly. Dwelling moves the edge, so there must be other edges to move to. Two dials:

    lock      0 locked .. 1 restless: how much returns, how long things are held, how much of the frame is filled
    derange   0 composed .. 1 deranged: how far the material is cut up, scrambled and processed

Each is an instrument, not a claim. Every row of _TABLE says what one engine parameter does along a dial: its value at
0, at REFERENCE (0.5: the engine exactly as it is, so a session that never touches the dials sounds as it did) and at
1, with straight lines between. The ends come from the research's "fully legible" and "noise" columns where it has
them, and are inference where it does not; none is calibrated toward anybody's records. Where the lip sits on a dial
is the owner's ear, so it is a parameter (`lips`, default REFERENCE), not a number this file believes in.

The budget (Edge.step), from 04 section 5, "How to turn them":
- one dial past its lip at a time; the other is held at its lip;
- past the lip for one or two bars, and back on a four-bar line: an excursion starts only on the third or fourth bar of
  a four-bar group and ends at the group's end, where the spine and the low end are back as they were;
- on one lane at a time: the excursion's numbers go to one lane (the drums, or the chopped layers), never to the
  low end; every other lane keeps the dials as held;
- dwell before disturbing: none within DWELL bars of the last; a state held EARNED bars (eight) earns the whole
  of what is asked, and two bars of it; one held less earns a share (bars held / EARNED) and one bar.

    params(lock, derange) -> {group: {name: value}}   multipliers (1.0 = as now) and offsets (0.0 = as now), by group:
                                                      drums, chop, develop, mangle, layers, look (see _TABLE)
    deal_numbers(p) -> {...}        deal.py's constants with p applied: RETURNS, WRITTEN, EIGHTH, ODD, FILL, SNARE_SPINE, GHOST
    chop_preset(preset, p) -> dict  a chopper.PRESETS entry with p applied (a copy)
    roller(bars, p) -> int          the development roller with p applied (develop.roller_bars)
    filth(knob, p) -> float         a part's damage knob with p applied
    Edge(seed, lips, lanes, dwell, earned).step(bar, {"lock": x, "derange": y}) -> result (Edge.step's doc)
    autopilot(seed, bar, lips) -> {"lock", "derange"}   the dials as the session moves them when nobody else does
    from_feel(state) -> {"lock", "derange"}            the feel pad's lock and derangement rungs as dial positions
    EdgeControl(seed)               what the mixer keeps: the wanted dials, whose they are, lips, roller, the budget;
                                    .take(message, bar, session) and .take_roller(n, bar) for the viewer's messages,
                                    .step(bar) once a bar, .stands() for the panels, .schedule() for develop.state

Pure and numpy-free.
"""
from . import develop
from .deal import EIGHTH, FILL, ODD, RETURNS, WRITTEN, _draw
from .feel import amount

DIALS = ("lock", "derange")
WORDS = {"lock": ("locked", "restless"), "derange": ("composed", "deranged")}
REFERENCE = 0.5               # where a dial leaves the engine exactly as it is
DEFAULT_LIPS = {"lock": REFERENCE, "derange": REFERENCE}
LANES = ("drums", "chops")    # the lanes an excursion may go to; never the low end (sub, the kick on the one) [04 5.5]
LANE_GROUPS = {"drums": ("drums",), "chops": ("chop", "mangle", "layers")}     # which groups of params each lane takes
DWELL = 4                     # bars held within the lips before any excursion [04 5.4: "about four cycles"]
EARNED = 8                    # bars held that earn the whole excursion, and two bars of it [04 5.4]
MOVED = 0.2                   # a held state is held: the dials within the lips moving more than this starts it again [inf]

# (dial, group, name, how, at 0, at REFERENCE, at 1, where it comes from). how: "mul" multiplies what the engine has
# (1.0 = as now), "add" is added (0.0 = as now); a name on both dials combines (product, or sum).
_TABLE = (
    # lock: locked .. restless. "Lock raises spine chance, return share, change periods and carrier coverage" [04 5.5]
    ("lock", "drums", "returns", "mul", 2.0, 1.0, 0.0, "deal.RETURNS 0.5: 1.0 a loop, 0 nothing returns [04 4.3 edge]"),
    ("lock", "drums", "written", "mul", 1.12, 1.0, 0.8, "deal.WRITTEN 0.88 -> 0.99 / 0.70 [inf]"),
    ("lock", "drums", "carrier", "mul", 1.25, 1.0, 0.45, "the carrier's chances: 7 bars in 10 covered -> under 3 [04 5 table]"),
    ("lock", "drums", "fill", "mul", 0.0, 1.0, 3.0, "deal.FILL 0.25: none / one group in four / most [04 5 phrase-end events]"),
    ("lock", "drums", "snare_spine", "mul", 1.0, 1.0, 0.8, "the snares on 5 and 13 only; the kick on the one never [04 4.1, 5.5]"),
    ("lock", "chop", "returns", "mul", 1.6, 1.0, 0.2, "the preset's group return share [04 4.3]"),
    ("lock", "chop", "hold", "mul", 2.0, 1.0, 0.25, "bars a skeleton is held [04 5 layer change period]"),
    ("lock", "develop", "roller", "mul", 2.0, 1.0, 0.25, "bars a riff is held [05 5.4; 04 5 layer change period]"),
    ("lock", "layers", "density", "add", -0.2, 0.0, 0.15, "feel.py: lock asks layers density -0.2"),
    ("lock", "look", "calm", "add", 0.3, 0.0, -0.2, "feel.py: lock asks look calm 0.3"),
    # derange: composed .. deranged. "Shortens the cut unit and run length, raises syncopation, allows stacked
    # processing" [04 5.5]
    ("derange", "chop", "true", "mul", 1.25, 1.0, 0.15, "position-true share: source-order runs of 2-4 slices -> 1 [04 5 table]"),
    ("derange", "chop", "short", "add", -0.6, 0.0, 0.8, "block weights leaned to the long (-1) or the short (+1) [04 5 cut unit]"),
    ("derange", "chop", "unit", "mul", 1.0, 1.0, 0.5, "cut unit: eighths -> sixteenths past three quarters [04 5 cut unit]"),
    ("derange", "chop", "reps", "add", 0.0, 0.0, 2.0, "more replays of a block [inf]"),
    ("derange", "chop", "stutter", "mul", 0.3, 1.0, 3.0, "stutters [inf]"),
    ("derange", "chop", "roll", "mul", 0.3, 1.0, 3.0, "rolls, at the phrase end and inside it [inf]"),
    ("derange", "chop", "reverse", "mul", 0.0, 1.0, 3.0, "reversed slices [04 3.6 reversal]"),
    ("derange", "chop", "empty", "mul", 0.3, 1.0, 2.0, "emptied downbeats [inf]"),
    ("derange", "drums", "odd", "mul", 0.5, 1.0, 2.2, "deal.ODD 0.34 -> 0.17 / 0.75: the even-odd contrast flattened [04 5 table]"),
    ("derange", "drums", "ghost", "mul", 0.5, 1.0, 2.0, "ghost snares [inf]"),
    ("derange", "mangle", "filth", "add", -0.15, 0.0, 0.35, "added to every layer's damage knob [inf]"),
    ("derange", "mangle", "stack", "add", 0.0, 0.0, 2.0, "transformations allowed at once, beyond one [04 4.4]"),
    ("derange", "layers", "density", "add", -0.2, 0.0, 0.5, "feel.py: derangement asks layers density 0.5"),
    ("derange", "look", "chaos", "add", -0.3, 0.0, 0.6, "feel.py: derangement asks look chaos 0.6"),
    ("derange", "look", "spin", "add", 0.0, 0.0, 0.4, "feel.py: derangement asks look spin 0.4"),
)


def _clamp(x, low=0.0, high=1.0):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return low
    return low if x != x else min(max(x, low), high)


def _along(d, low, mid, high):
    """A row's value at dial position d: straight lines through (0, low), (REFERENCE, mid), (1, high)."""
    if d <= REFERENCE:
        return low + (mid - low) * d / REFERENCE
    return mid + (high - mid) * (d - REFERENCE) / (1.0 - REFERENCE)


def params(lock=REFERENCE, derange=REFERENCE):
    """What the two dials ask of the engine: {group: {name: value}}. Every name is there; at REFERENCE on both dials
    every multiplier is 1.0 and every offset 0.0."""
    at = {"lock": _clamp(lock), "derange": _clamp(derange)}
    out = {}
    for dial, group, name, how, low, mid, high, _ in _TABLE:
        value = _along(at[dial], low, mid, high)
        held = out.setdefault(group, {})
        if name in held:
            held[name] = held[name] * value if how == "mul" else held[name] + value
        else:
            held[name] = value
    return {group: {name: round(v, 4) for name, v in held.items()} for group, held in out.items()}


def deal_numbers(p):
    """deal.py's chances with the dials applied, for whoever deals the drums: {"RETURNS", "WRITTEN", "EIGHTH", "ODD",
    "FILL", "SNARE_SPINE", "GHOST" (a multiplier on the ghost snares' chances)}."""
    d = p["drums"]
    return {"RETURNS": _clamp(RETURNS * d["returns"]), "WRITTEN": _clamp(WRITTEN * d["written"]),
            "EIGHTH": _clamp(EIGHTH * d["carrier"]), "ODD": _clamp(ODD * d["carrier"] * d["odd"]),
            "FILL": _clamp(FILL * d["fill"]), "SNARE_SPINE": _clamp(d["snare_spine"]), "GHOST": max(d["ghost"], 0.0)}


def chop_preset(preset, p):
    """A chopper preset (one column of chopper._TABLE, as chopper.PRESETS[style]) with the dials applied: a copy."""
    c, out = p["chop"], dict(preset)
    for name, by in (("true", "true"), ("returns", "returns"), ("stutter", "stutter"), ("roll", "roll"), ("roll_any", "roll"),
                     ("reverse", "reverse"), ("empty", "empty")):
        if name in out:
            out[name] = _clamp(out[name] * c[by])
    if "hold" in out:
        out["hold"] = max(4, 4 * int(round(out["hold"] * c["hold"] / 4.0)))
    if "reps" in out:
        out["reps"] = max(1, int(round(out["reps"] + c["reps"])))
    if "unit" in out:
        out["unit"] = max(1, int(round(out["unit"] * c["unit"] + 1e-9)))
    blocks = out.get("blocks")
    if blocks and len(blocks) > 1 and abs(c["short"]) > 1e-6:
        ranked = sorted(range(len(blocks)), key=lambda i: blocks[i][0])
        lean = {i: 1.0 - 2.0 * r / (len(blocks) - 1) for r, i in enumerate(ranked)}         # +1 the shortest .. -1 the longest
        weights = [max(w * (1.0 + c["short"] * lean[i]), 0.01) for i, (_, w) in enumerate(blocks)]
        total = sum(weights)
        out["blocks"] = tuple((length, round(w / total, 4)) for (length, _), w in zip(blocks, weights))
    return out


def roller(bars, p):
    """The development roller (bars a riff is held) with the dials applied."""
    return develop.roller_bars(float(bars) * p["develop"]["roller"])


def filth(knob, p):
    """A layer's damage knob (mangle) with the dials applied."""
    return _clamp(float(knob) + p["mangle"]["filth"])


# ---------------------------------------------------------------------------------------------------------------
# The budget


class Edge:
    """The one-dial-past-the-lip budget, a bar at a time. `lips`: where each dial's lip is, by ear ({"lock": 0.5, ...});
    `lanes`: the lanes an excursion may go to; `dwell`, `earned`: bars (see the module's doc)."""

    def __init__(self, seed=0, lips=None, lanes=LANES, dwell=DWELL, earned=EARNED):
        self.seed, self.lanes = seed, tuple(lanes) or LANES
        self.dwell, self.earned = max(int(dwell), 0), max(int(earned), 1)
        self.lips = dict(DEFAULT_LIPS)
        for dial, at in (lips or {}).items():
            self.set_lip(dial, at)
        self.reset()

    def reset(self):
        self.last, self.trip, self.calm_from, self.anchor = None, None, None, None

    def set_lip(self, dial, value):
        """Where a dial's lip sits (0 .. 1): past it, the dial is rationed. Returns the value taken, or None."""
        if dial not in DIALS:
            return None
        self.lips[dial] = _clamp(value)
        return self.lips[dial]

    def step(self, bar, dials):
        """The budget at `bar`, for the dials as wanted ({"lock": x, "derange": y}; a missing dial is at REFERENCE).
        Asked again for the same bar, the same answer; asked for an earlier bar, it starts again. Returns:

            bar, wanted, lips
            base        the dials in force everywhere: each wanted value, held at its lip
            past        the dial past its lip this bar, or None
            lane        the one lane the excursion goes to ("drums" or "chops"), or None
            over        the dials on that lane: base, with the past dial at its granted value (None: no excursion)
            left        bars of the excursion left, this one included (0: none)
            size        the share of what was asked past the lip that was granted (bars held / earned, at most 1)
            calm        bars held within the lips before this bar (the credit)
            returning   True on the first bar back from an excursion (a four-bar line)
            waiting     dials asked past their lips and held back this bar
            params      params(base): for every lane
            excursion   params(over) for the lane named (apply LANE_GROUPS[lane] of it there), or None
            look        the look's offsets: the excursion's when there is one (the picture shows it), else the base's
        """
        bar = int(bar)
        wanted = {d: _clamp((dials or {}).get(d, REFERENCE)) for d in DIALS}
        if self.last is not None:
            if bar == self.last["bar"]:
                return self.last
            if bar < self.last["bar"]:
                self.reset()
        lips = dict(self.lips)
        base = {d: min(wanted[d], lips[d]) for d in DIALS}
        if self.calm_from is None:
            self.calm_from, self.anchor = bar, dict(base)
        if any(abs(base[d] - self.anchor[d]) > MOVED for d in DIALS):      # the held state has moved: held from now
            self.calm_from, self.anchor = bar, dict(base)
        calm = max(bar - self.calm_from, 0)
        trip, was = self.trip, self.trip
        if trip and (bar >= trip["end"] or wanted[trip["dial"]] <= lips[trip["dial"]]):
            trip = None                                           # over: at its four-bar line, or pulled back by hand
        if trip is None and bar % 4 in (2, 3):
            asked = [d for d in DIALS if wanted[d] > lips[d] + 1e-9]
            if asked and calm >= self.dwell and (bar % 4 == 3 or calm >= self.earned):
                dial = max(asked, key=lambda d: ((wanted[d] - lips[d]) / max(1.0 - lips[d], 1e-9), _draw(self.seed, "first", bar, d)))
                trip = {"dial": dial, "lane": self.lanes[int(_draw(self.seed, "lane", bar) * len(self.lanes)) % len(self.lanes)],
                        "start": bar, "end": bar + 4 - bar % 4, "size": min(1.0, calm / float(self.earned))}
        self.trip = trip
        over = None
        if trip:
            d = trip["dial"]
            over = dict(base, **{d: lips[d] + (wanted[d] - lips[d]) * trip["size"]})
            self.calm_from, self.anchor = bar + 1, dict(base)        # held again from the bar after it
        p = params(base["lock"], base["derange"])
        excursion = params(over["lock"], over["derange"]) if over else None
        self.last = {"bar": bar, "wanted": wanted, "lips": lips, "base": base, "past": trip["dial"] if trip else None,
                     "lane": trip["lane"] if trip else None, "over": over, "left": trip["end"] - bar if trip else 0,
                     "size": round(trip["size"], 3) if trip else 0.0, "calm": calm,
                     "returning": bool(was and not trip and bar % 4 == 0),
                     "waiting": [d for d in DIALS if wanted[d] > lips[d] + 1e-9 and not (trip and trip["dial"] == d)],
                     "params": p, "excursion": excursion, "look": (excursion or p)["look"]}
        return self.last


def describe(result):
    """A result of Edge.step in a few words: "derange past the lip on the chops, 2 bars" / "within the lips"."""
    if not result or not result.get("past"):
        waiting = (result or {}).get("waiting")
        return "within the lips" + (f" ({', '.join(waiting)} waits for a bar of its own)" if waiting else "")
    return f"{result['past']} past the lip on the {result['lane']}, {result['left']} bar{'s' if result['left'] != 1 else ''}"


def autopilot(seed, bar, lips=None):
    """The dials as the session moves them when no hand and no director does: within the lips, moving on sixteen-bar
    lines; and in about one eight-bar stretch in two, one dial asked past its lip for the stretch's last two bars
    (the budget decides how much of that is granted)."""
    lips = dict(DEFAULT_LIPS, **(lips or {}))
    block, out = int(bar) // 16, {}
    for d in DIALS:
        out[d] = round(lips[d] * (0.45 + 0.55 * _draw(seed, "auto", d, block)), 3)
    stretch = int(bar) // 8
    if int(bar) % 8 >= 6 and _draw(seed, "auto push", stretch) < 0.5:
        d = DIALS[int(_draw(seed, "auto which", stretch) * len(DIALS)) % len(DIALS)]
        out[d] = round(lips[d] + (1.0 - lips[d]) * (0.35 + 0.65 * _draw(seed, "auto how far", stretch)), 3)
    return out


def from_feel(state):
    """The feel pad's lock and derangement (feel.py rungs, -4 .. 5) as dial positions: lock's own pole is locked (dial
    toward 0), its inverse restless; derangement's own pole is deranged (dial toward 1)."""
    state = state or {}
    return {"lock": _clamp(REFERENCE - 0.5 * amount(state.get("lock", 0))),
            "derange": _clamp(REFERENCE + 0.5 * amount(state.get("derangement", 0)))}


# ---------------------------------------------------------------------------------------------------------------
# What the mixer keeps


class EdgeControl:
    """The edge as the mixer holds it. Messages from the viewer go to `take` ({"edge": {...}}) and `take_roller`
    ({"roller": n}); `step(bar)` is asked once a bar; `stands()` is what the panels follow; `schedule()` is the roller
    as develop.state takes it.

    Whose the dials are: "auto" (the session's: the director's values when it sends them, else autopilot) until a
    hand or a typed line sets one; "!edge auto" gives them back."""

    def __init__(self, seed=0, lips=None):
        self.seed = seed
        self.budget = Edge(seed, lips)
        self.wanted = {d: REFERENCE for d in DIALS}
        self.auto, self.session = True, None
        self.roller, self.rollers, self.applied = develop.DEFAULT_ROLLER, [(0, develop.DEFAULT_ROLLER)], develop.DEFAULT_ROLLER
        self.bar, self.now = 0, None

    def take(self, message, bar=None, session=False):
        """An {"edge": ...} message: {"lock": 0.7}, {"derange": 0.3}, {"auto": true}, {"lip": {"lock": 0.6}}, or several
        at once. session: sent by the session (seq > 0), which moves the dials only while they are its own. Returns
        what happened, as text ("" for nothing)."""
        if not isinstance(message, dict):
            return ""
        if bar is not None:
            self.bar = int(bar)
        said = []
        if message.get("auto"):
            self.auto, self.session = True, None
            said.append("the session's again")
        for dial, at in (message.get("lip") or {}).items() if isinstance(message.get("lip"), dict) else ():
            if isinstance(at, (int, float)) and self.budget.set_lip(dial, at) is not None:
                said.append(f"{dial}'s lip at {self.budget.lips[dial]:.2f}")
        values = {d: _clamp(message[d]) for d in DIALS if isinstance(message.get(d), (int, float)) and not isinstance(message.get(d), bool)}
        if values and session:
            if self.auto:
                self.session = {**{d: REFERENCE for d in DIALS}, **(self.session or {}), **values}
                said += [f"{d} {v:.2f}" for d, v in values.items()]
        elif values:
            self.wanted.update(values)
            if self.auto:                                         # a hand on one dial takes both: the other stays where it stood
                self.wanted.update({d: v for d, v in self.current().items() if d not in values})
            self.auto = False
            said += [f"{d} {v:.2f} ({WORDS[d][0] if v < self.budget.lips[d] else 'past the lip: ' + WORDS[d][1]})" for d, v in values.items()]
        return ", ".join(said)

    def take_roller(self, bars, bar=None):
        """A {"roller": n} message: bars a riff is held before it changes, 2 (switch-up) .. 32 (roller), from the next
        run. Returns what happened, as text."""
        if bar is not None:
            self.bar = int(bar)
        self.roller = develop.roller_bars(bars)
        return f"riffs held {self.roller} bars" + (" (a roller)" if self.roller >= 32 else " (a switch-up)" if self.roller <= 4 else "")

    def current(self):
        """The dials as wanted now: by hand, or the session's."""
        if not self.auto:
            return dict(self.wanted)
        return dict(self.session) if self.session else autopilot(self.seed, self.bar, self.budget.lips)

    def step(self, bar):
        """The budget's result for `bar` (Edge.step), with the dials as wanted now. Also keeps the roller schedule:
        the roller asked for, times what the lock dial asks, from the next bar when that changes."""
        self.bar = int(bar)
        self.now = self.budget.step(self.bar, self.current())
        held = roller(self.roller, self.now["params"])
        if held != self.applied:
            self.applied = held
            self.rollers.append((self.bar + 1, held))
        return self.now

    def schedule(self):
        """The roller as develop.state takes it: [(from_bar, bars), ...]."""
        return tuple(self.rollers)

    def stands(self):
        """For the panels: {"lock", "derange" (as wanted), "auto", "lips", "past", "lane", "left", "base", "over"}."""
        now, want = self.now or {}, self.current()
        return {"lock": round(want["lock"], 3), "derange": round(want["derange"], 3), "auto": self.auto,
                "lips": {d: round(v, 3) for d, v in self.budget.lips.items()}, "past": now.get("past"), "lane": now.get("lane"),
                "left": now.get("left", 0), "base": now.get("base"), "over": now.get("over")}
