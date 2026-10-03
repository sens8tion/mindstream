"""Development: what each lane is playing at any bar, and when it changes (docs/research/README.md, build step 4;
05_bass_sub_tune_progression.md section 12.7; 04_legibility_beyond_repetition.md, source 7, "nested clocks").

Progress is turnover, not level. Each lane keeps its material as a stored thing with a version, changes one thing
at a time on its own slow clock, and brings earlier material back changed. This file says only WHEN and WHAT KIND:
which version of its material a lane plays at a bar, and what happens to it there. It makes no notes; whoever owns
the material (the riff, the hook, the drums' deal, a layer's chop) maps a fate onto it.

The clocks, as the research gives them:

- the riff (sub/bass): held for a run of `roller` bars, then its fate is drawn as the reference measured it [05
  12.7, R-bass 11.2]: the same riff back after a one-bar hole 0.36, a partial rewrite 0.21, a new riff 0.39, a
  transposition 0.03, and the remainder ("same notes, new rhythm", 1 in 67) 0.01. And one kept mutation on every
  eight-bar line that no fate has taken: with a roller of 8 or more the riff takes exactly one kept change per eight
  bars.
- sections of 32 bars (deal.SECTION) [05 12.7, R-align]: at 32 the B riff, with the kick style and the carrier
  changing on the same bar (the one co-change allowed: "three or four layers turning over together marks a real
  section"); at 64 riff A back in a later generation, preceded by one or two bars with no low end; at 96 B back
  changed; at 128 a new A, and round again (a cycle of four sections).
- the drums: their section turnovers with the riff's, and one time in four one thing changed mid-section.
- the hook (motif): follows the riff's sections a four-bar line later (hook A comes back when riff A does), and in
  between is replaced by a relative every 16 bars or so (about three appearances, then retired); one time in four
  the lane is left empty for 4 or 8 bars first [05 12.8.7-8].
- a slice layer: four clocks of its own, on four-bar lines: its source (what of its sound it reads), its role, its
  odds table, its processing [04 source 7]. Processing (the chop as a whole): one slow clock, 32 to 64 bars.

"One layer changes at a time" is enforced. Lanes are scheduled in priority order: the riff, then the drums, then the
hook; a change that lands on a bar another lane already changes on moves on to the next free four-bar line (within
MAX_DEFER), and the hook's and drums' lesser changes give way altogether when there is none. Slice layers and
processing then share the four-bar lines that are left: at each free line the change that has waited longest is
made, one per line, so every layer gets a turn and none can crowd another. The capacity is real: with the riff on
every eight-bar line and the hook on some of the lines between, about seven lines in 128 bars are left for all of
them, so the more layers there are, the slower each turns over. Only the leading riff and drums may share a bar (a
section turnover); anything else that shares one is marked "crowded" and counted.

The roller <-> switch-up dial (the README's open choice) is `roller`: bars a riff is held before its fate is drawn,
32 (a roller: held a section, only mutated) down to 2 (a switch-up). It also sets the hook's replacement period and
halves or doubles the slice clocks at its ends. It may be a schedule, so a change made live never rewrites the past:
a new value counts from the next run.

Pure and numpy-free: the same seed, bar, lanes and roller always give the same answer, by deal.py's stable hash.

    state(seed, bar, lanes=DEFAULT_LANES, roller=DEFAULT_ROLLER, section=SECTION) -> {lane: info}
    events(seed, start, end, lanes=..., roller=..., section=...) -> [(bar, lane, info)]   every bar where a lane does
                                                                                          something other than hold
    Development(seed, lanes, roller, section)       the same, as an object: .state(bar), .events(start, end),
                                                    .crowded (bars shared that should not be), .skipped (changes
                                                    that gave way), .roller_at(bar)
    roller_bars(value) -> int                        a roller value as it is used: 2, or a multiple of 4 up to 32
    kind_of(name) -> one of KINDS                    a lane's kind, from its name, when only names are given

lanes: names ("sub", "drums", "hook", "chop", "rain" ...), (name, kind) pairs, (name, kind, from_bar), or
    {name: kind}. A name's kind is guessed (kind_of) when not given: sub/bass/riff -> riff, drums/break -> drums,
    hook/tune/lead/motif -> motif, chop/processing -> processing, anything else (a layer's name) -> slices.
    from_bar (slices and processing): the bar the layer came in. Give it, and keep a layer in the list after it has
    gone, so that the others' clocks are not moved: the lanes are worked out together from bar 0.
roller: an int (2..32), or a schedule [(from_bar, roller), ...]; each run's length is the roller in force where the
    run starts.

info, for every lane at every bar (the same keys for every kind; a key that means nothing for a kind is None):
    kind        the lane's kind
    version     which material: an id, counted up per lane from 0 as new material is made. Material that comes
                back (A at 64) comes back with its old id
    generation  kept mutations of that material so far (0 = as first made); A back at 64 is a later generation
    family      "A" or "B" (riff, drums, motif: which half of the cycle the material belongs to), else None
    parent      the version new material was made from (a rewrite, a new riff that keeps a part, B), else None
    fate        what happens at this bar:
                  "start"      the material as first made (bar 0, or the bar a layer came in)
                  "hold"       nothing: play the version as it stands (decorations re-dealt as ever)
                  "mutate"     one kept change to this version (generation + 1); `how` names which
                  "hole"       this lane is out for the bar (the riff's turnaround hole, the low end out before A
                               returns, a hook withheld); the version is what comes back
                  "back"       the same riff back after its hole, unchanged (off the eight-bar line)
                  "rewrite"    a partial rewrite: new version, about half the cell and half the skeleton kept
                  "new"        new material (a relative: `how` names the one thing kept, if any)
                  "transpose"  the same riff moved (generation + 1); `how` says where
                  "rhythm"     the same notes on a new rhythm (new version)
                  "B"          the B material, at a section start (new, or B back changed)
                  "A_changed"  A back, a later generation, at a section start
    changing    True when what is heard changes here (fates other than hold, back and start; the first bar of a hole)
    how         the kind of change, from the research's lists (MUTATIONS, KEEPS, RETURNS_HOW ...), or None
    seed        a stable int for this change, for whoever makes it (mutate(riff, how, seed))
    drawn       at the end of a riff's run: the fate as drawn ("return", "rewrite", "new", "transpose",
                "rhythm"), else None. ("return" shows as a hole on the bar before, and "mutate" or "back" here.)
    section     True on a section turnover (B, A_changed, a new A, and the hook and drums following them)
    crowded     True when this change had to share its bar with another lane's
    aspect      slices: which clock ticked here ("source", "role", "odds", "processing"), else None
    versions    slices: {aspect: how many times it has changed}, else None
    since       bars since this lane last changed (0 when changing now)
"""
import bisect

from .deal import SECTION, _draw

KINDS = ("riff", "drums", "motif", "processing", "slices")       # also the order lanes are scheduled in
DEFAULT_LANES = ("sub", "drums", "hook", "chop")
DEFAULT_ROLLER = 16           # a riff held 16 bars, mutated at 8: the reference's runs are 7 to 15, median 11 [05 12.9]; inf
ROLLERS = (2, 4, 8, 16, 32)   # the choices the panel offers; any value 2..32 is taken (see roller_bars)
MUTATE_EVERY = 8              # one kept mutation per eight bars [05 12.7, sourced [81b][57][22]]
CYCLE = 4                     # sections per cycle: A, B, A changed, B changed, then a new A [inf from 05 12.7]
FATES = (("return", 0.36), ("rewrite", 0.21), ("new", 0.39), ("transpose", 0.03), ("rhythm", 0.01))   # [05 12.7, measured R-bass 11.2]
FATE_NAMES = ("start", "hold", "mutate", "hole", "back", "rewrite", "new", "transpose", "rhythm", "B", "A_changed")
MATERIAL = frozenset(("mutate", "rewrite", "new", "transpose", "rhythm", "B", "A_changed"))      # fates that change the material
# the mutations of a stored riff [05 12.7; the list is inference there]
MUTATIONS = ("drop_decoration", "add_pickup", "shift_decoration", "swap_pitch", "move_high_point", "switch_answer",
             "toward_deep", "toward_busy", "colour_note")
KEEPS = ("anchor_b", "answer", "colour")        # what a new riff keeps of the last, with KEEP_CHANCE [05 12.7, inf]
KEEP_CHANCE = 0.5
TRANSPOSES = ("down_step", "up_step", "up_fourth")
RETURNS_HOW = ("second_bass", "other_skeleton", "harder")      # how A (or B) comes back changed [05 12.7, sourced [19][22][23]]
TWO_HOLES = 0.5               # chance the low end is out two bars before A comes back, not one [05 12.7: "1 to 2 bars"]
DRUM_MID = 0.25               # chance the drums change one thing mid-section: 23% of kick changes are off a riff change [R-align]
DRUM_HOW = ("carrier", "kick")
DRUM_RETURNS = ("harder", "busier_carrier", "other_kick")     # the A drums back changed [05 12.7 "second drop harder"; inf]
HOOK_KEEPS = ("rhythm", "interval")             # what a replacement hook keeps, with KEEP_CHANCE [05 12.8.7]
WITHHOLD, WITHHOLD_BARS = 0.25, (4, 8)          # after a hook is retired, the lane left empty one time in four [05 12.8.8]
PROCESS_PERIODS = ((32, 0.5), (48, 0.2), (64, 0.3))           # [04 3.5: carrier and timbre every 25 to 32; inf]
PROCESS_HOW = ("unit", "operators", "stutter", "reverse", "returns")
# a slice layer's four clocks [04 source 7: "a period drawn from 8, 16, 32 and a phase"; 04 3.5: 25 to 32 bars per
# lane]. Slower than the research's 8, since every layer shares the few four-bar lines the riff and hook leave [inf]
ASPECTS = (("source", ((32, 0.4), (64, 0.4), (128, 0.2))),
           ("role", ((64, 0.6), (128, 0.4))),
           ("odds", ((16, 0.4), (32, 0.4), (64, 0.2))),
           ("processing", ((32, 0.5), (64, 0.5))))
MAX_DEFER = 12                # bars a change may wait for a bar of its own (three four-bar lines)
MAX_WAIT = 32                 # bars a slice layer's change may wait for a free line before it gives way to its next tick
MARGIN = 96                   # bars at the end of what has been worked out that are not trusted (they are worked out again)


def roller_bars(value):
    """A roller as it is used: 2..32, and on a four-bar line from 4 up (a riff's changes keep to four-bar lines)."""
    try:
        r = min(max(int(round(float(value))), 2), 32)
    except (TypeError, ValueError, OverflowError):
        return DEFAULT_ROLLER
    return 2 if r < 4 else min(32, max(4, 4 * int(round(r / 4.0))))


def kind_of(name):
    """A lane's kind, guessed from its name."""
    n = str(name).strip().lower()
    if n in ("sub", "bass", "riff", "bassline"):
        return "riff"
    if n in ("drums", "drum", "break", "breaks", "kick"):
        return "drums"
    if n in ("hook", "tune", "lead", "motif"):
        return "motif"
    if n in ("chop", "processing", "chop_style"):
        return "processing"
    return "slices"


def _lanes(lanes):
    """lanes as ((name, kind, from_bar), ...)."""
    if isinstance(lanes, str):
        lanes = (lanes,)
    if isinstance(lanes, dict):
        lanes = tuple(lanes.items())
    out, seen = [], set()
    for lane in lanes:
        lane = tuple(lane) if isinstance(lane, (tuple, list)) else (lane,)
        name = str(lane[0])
        kind = lane[1] if len(lane) > 1 and lane[1] in KINDS else kind_of(name)
        try:
            start = max(int(lane[2]), 0) if len(lane) > 2 and kind in ("slices", "processing") else 0
        except (TypeError, ValueError):
            start = 0
        if name not in seen:
            seen.add(name)
            out.append((name, kind, start))
    return tuple(out)


def _rollers(roller):
    if isinstance(roller, (int, float, str)):
        return ((0, roller_bars(roller)),)
    by_bar = {}
    for at, value in roller or ():
        by_bar[max(int(at), 0)] = roller_bars(value)
    by_bar.setdefault(0, DEFAULT_ROLLER)
    return tuple(sorted(by_bar.items()))


def _pick(weights, u):
    total = sum(w for _, w in weights)
    u *= total
    for value, w in weights:
        if u < w:
            return value
        u -= w
    return weights[-1][0]


def _choice(options, u):
    return options[min(int(u * len(options)), len(options) - 1)]


class Development:
    """The clocks of a set of lanes, worked out from bar 0 as far as has been asked (and further, as it is asked)."""

    def __init__(self, seed, lanes=DEFAULT_LANES, roller=DEFAULT_ROLLER, section=SECTION):
        self.seed, self.lanes, self.rollers = seed, _lanes(lanes), _rollers(roller)
        self.names = [name for name, _, _ in self.lanes]
        self.section = max(16, 8 * int(round(int(section) / 8.0)))
        self._at = [at for at, _ in self.rollers]
        self.horizon, self.trusted = 0, 0
        self._build(256)

    # ------------------------------------------------------------------ asking

    def roller_at(self, bar):
        return self.rollers[max(bisect.bisect_right(self._at, bar) - 1, 0)][1]

    def state(self, bar):
        """{lane: info} at `bar` (see the module's doc)."""
        bar = max(int(bar), 0)
        if bar >= self.trusted:
            self._build(max(2 * self.horizon, bar + 256))
        return {name: self._info(name, bar) for name in self.names}

    def events(self, start, end):
        """[(bar, lane, info)] for every bar in start..end-1 where a lane does something other than hold, in order."""
        start, end = max(int(start), 0), int(end)
        if end >= self.trusted:
            self._build(max(2 * self.horizon, end + 256))
        out = []
        for name in self.names:
            bars = self.bars[name]
            for i in range(bisect.bisect_left(bars, start), bisect.bisect_left(bars, end)):
                out.append((bars[i], name, self._info(name, bars[i])))
        return sorted(out, key=lambda e: (e[0], self.names.index(e[1])))

    def _info(self, name, bar):
        bars, recs = self.bars[name], self.recs[name]
        i = max(bisect.bisect_right(bars, bar) - 1, 0)
        out = dict(recs[i])
        if bars[i] != bar:                                        # nothing here: as it was (and a hole stays a hole till what ends it)
            out.update(fate="hole" if out["fate"] == "hole" else "hold", changing=False, how=None, drawn=None, section=False,
                       crowded=False, aspect=None)
        moved = self.moved[name]
        j = bisect.bisect_right(moved, bar) - 1
        out["since"] = bar - moved[j] if j >= 0 else bar
        return out

    # ------------------------------------------------------------------ working it out

    def _build(self, horizon):
        """Every lane from bar 0 to `horizon`: the riff, drums and hook in priority order, each keeping off the bars of
        those before it; then the slice layers and processing together, on the four-bar lines that are left."""
        self.horizon, self.busy, self.skipped, self.crowded = int(horizon), {}, 0, 0
        self.bars, self.recs, self.moved, self._all = {}, {}, {}, {}
        leaders, pooled = {}, []
        for index, (name, kind, start) in sorted(enumerate(self.lanes), key=lambda e: (KINDS.index(e[1][1]), e[0])):
            if kind in ("slices", "processing"):
                pooled.append((name, kind, start, index))
                continue
            self._lane(name, kind, kind in ("riff", "drums") and leaders.setdefault(kind, name) == name)
            getattr(self, "_" + kind)()
        if pooled:
            self._pool(pooled)
        for name in self.names:
            recs = self._all[name]
            self.bars[name] = sorted(recs)
            self.recs[name] = [recs[b] for b in self.bars[name]]
            self.moved[name] = [b for b in self.bars[name] if recs[b]["changing"]]
        self.trusted = self.horizon - MARGIN

    def _lane(self, name, kind, leader=False):
        """From here on, records and draws are this lane's."""
        self._name, self._kind, self._leader = name, kind, leader
        self._recs = self._all.setdefault(name, {})

    def _u(self, *key):
        return _draw(self.seed, self._name, *key)

    def _place(self, bar, before, section=False, skip=False, defer=MAX_DEFER):
        """The bar a change lands on: `bar`, or the next free four-bar line before `before` and within `defer`. If
        there is none: None when it may give way (`skip`), else `bar` itself, shared (crowded). Section turnovers of
        the leading riff and drums may share a bar with each other."""
        at, crowded = bar, False
        while True:
            here = self.busy.get(at, ())
            if not here or (section and self._leader and all(s and lead for _, s, lead in here)):
                break
            at += 4
            if at >= before or at - bar > defer:
                if skip:
                    self.skipped += 1
                    return None, False
                at, crowded = bar, True
                self.crowded += 1
                break
        self.busy.setdefault(at, []).append((self._name, section, self._leader))
        return at, crowded

    def _put(self, bar, state, fate, changing, how=None, drawn=None, section=False, crowded=False, aspect=None, versions=None):
        self._recs[bar] = {"kind": self._kind, "version": state["version"], "generation": state["generation"],
                           "family": state.get("family"), "parent": state.get("parent"), "fate": fate, "changing": bool(changing),
                           "how": how, "seed": int(self._u("seed", bar) * 2 ** 31), "drawn": drawn, "section": bool(section),
                           "crowded": bool(crowded), "aspect": aspect, "versions": dict(versions) if versions is not None else None}

    def _change(self, bar, before, state, fate, skip=False, defer=MAX_DEFER, **kw):
        """A change, placed so that it keeps off other lanes' bars. Returns the bar it landed on (None: it gave way)."""
        at, crowded = self._place(bar, before, kw.get("section", False), skip, defer)
        if at is not None:
            self._put(at, state, fate, True, crowded=crowded, **kw)
        return at

    def _keeps(self, key, options):
        return _choice(options, self._u(key, "what")) if self._u(key, "keeps") < KEEP_CHANCE else None

    def _section_material(self, k, cur, lineage, openers, ids, how_new, returns=RETURNS_HOW):
        """What a lane plays from section k on: (state, fate, how). Sections go A, B, A back changed, B back changed,
        then a new A."""
        pos = k % CYCLE
        if pos in (2, 3) and (k - 2) in openers:                # A (or B) back, a later generation
            version = openers[k - 2]
            lineage[version] += 1
            state = {"version": version, "generation": lineage[version], "family": "A" if pos == 2 else "B", "parent": None}
            fate, how = ("A_changed" if pos == 2 else "B"), _choice(returns, self._u("returns how", k))
        else:                                                     # a new A, or the first B: new material, a relative
            version = ids[0] = ids[0] + 1
            lineage[version] = 0
            state = {"version": version, "generation": 0, "family": "B" if pos % 2 else "A", "parent": cur["version"]}
            fate, how = ("B" if pos % 2 else "new"), how_new(k)
        openers[k] = version
        return state, fate, how

    @staticmethod
    def _mutated(cur, lineage):
        cur = dict(cur, generation=cur["generation"] + 1)
        lineage[cur["version"]] = cur["generation"]
        return cur

    # ------------------------------------------------------------------ the kinds

    def _riff(self):
        S, ids, lineage, openers = self.section, [0], {0: 0}, {0: 0}
        cur = {"version": 0, "generation": 0, "family": "A", "parent": None}
        self._put(0, cur, "start", False)
        holes_before = lambda k: 0 if k % CYCLE != 2 else (2 if self._u("two holes", k) < TWO_HOLES else 1)   # noqa: E731
        k = 0
        while k * S < self.horizon:
            s = k * S
            if k > 0:
                cur, fate, how = self._section_material(k, cur, lineage, openers, ids,
                                                        lambda k: "opposite_density" if k % 2 else self._keeps(("section", k), KEEPS))
                self._change(s, s + S, cur, fate, how=how, section=True)
            end = s + S - holes_before(k + 1)
            plan, b = {}, s
            while True:                                           # the runs: each as long as the roller where it starts
                b += min(self.roller_at(b), S)
                if b >= s + S:
                    break
                plan[b] = "end of run"
            for m in range(s + MUTATE_EVERY, s + S, MUTATE_EVERY):
                plan.setdefault(m, "mutate")
            due = sorted(b for b in plan if b < end)
            for i, b in enumerate(due):
                before = due[i + 1] if i + 1 < len(due) else end
                if plan[b] == "mutate":
                    cur = self._mutated(cur, lineage)
                    self._change(b, before, cur, "mutate", how=_choice(MUTATIONS, self._u("mutation", b)))
                    continue
                drawn = _pick(FATES, self._u("fate", b))
                if drawn == "return":                             # a hole at the run's last bar, and the same riff back
                    self._change(b - 1, b, cur, "hole")
                    if b % MUTATE_EVERY == 0:
                        cur = self._mutated(cur, lineage)
                        self._change(b, before, cur, "mutate", how=_choice(MUTATIONS, self._u("mutation", b)), drawn=drawn)
                    else:
                        self._put(b, cur, "back", False, drawn=drawn)
                elif drawn == "transpose":
                    cur = self._mutated(cur, lineage)
                    self._change(b, before, cur, "transpose", how=_choice(TRANSPOSES, self._u("transpose", b)), drawn=drawn)
                else:                                             # rewrite, new, rhythm: new material, made from this
                    ids[0] += 1
                    lineage[ids[0]] = 0
                    cur = {"version": ids[0], "generation": 0, "family": cur["family"], "parent": cur["version"]}
                    how = {"rewrite": "half_cell_half_skeleton", "rhythm": "same_notes_new_rhythm"}.get(drawn) or self._keeps(("new", b), KEEPS)
                    self._change(b, before, cur, drawn, how=how, drawn=drawn)
            nxt = (k + 1) * S
            for i, h in enumerate(range(end, nxt)):               # the low end out before A comes back
                if i == 0:
                    self._change(h, nxt, cur, "hole")
                else:
                    self._put(h, cur, "hole", False)
            k += 1

    def _drums(self):
        S, ids, lineage, openers = self.section, [0], {0: 0}, {0: 0}
        cur = {"version": 0, "generation": 0, "family": "A", "parent": None}
        self._put(0, cur, "start", False)
        k = 0
        while k * S < self.horizon:
            s = k * S
            if k > 0:                                             # the kick style and the carrier change with the riff
                cur, fate, how = self._section_material(k, cur, lineage, openers, ids, lambda k: "kick_and_carrier", DRUM_RETURNS)
                self._change(s, s + S, cur, fate, how=how, section=True)
            if self._u("middle", k) < DRUM_MID:
                changed = self._mutated(cur, lineage)
                if self._change(s + S // 2, s + S, changed, "mutate", skip=True, how=_choice(DRUM_HOW, self._u("middle how", k))) is not None:
                    cur = changed
                else:
                    lineage[cur["version"]] = cur["generation"]
            k += 1

    def _motif(self):
        S, ids, lineage, openers = self.section, [0], {0: 0}, {0: 0}
        cur = {"version": 0, "generation": 0, "family": "A", "parent": None}
        self._put(0, cur, "start", False)
        k, t = 0, 0
        while k * S < self.horizon:
            s = k * S
            limit = s + S + 4                                     # the next section's hook comes in here
            if k > 0:                                             # a four-bar line after the riff turns over
                cur, fate, how = self._section_material(k, cur, lineage, openers, ids,
                                                        lambda k: self._keeps(("section", k), HOOK_KEEPS))
                t = self._change(s + 4, limit, cur, fate, how=how, section=True, defer=S - 8)
            while True:
                t_next = t + min(16, max(8, 2 * self.roller_at(t)))
                if t_next >= limit:
                    break
                withhold = self._u("withhold", t_next) < WITHHOLD
                at = self._change(t_next, limit, cur, "hole" if withhold else "new", skip=True)
                if at is None:                                    # no bar of its own: the hook stays, till its next tick
                    t = t_next
                    continue
                was = cur
                ids[0] += 1
                lineage[ids[0]] = 0
                cur = {"version": ids[0], "generation": 0, "family": cur["family"], "parent": cur["version"]}
                how = self._keeps(("new", t_next), HOOK_KEEPS)
                if not withhold:
                    self._put(at, cur, "new", True, how=how, crowded=self._recs[at]["crowded"])
                    t = at
                    continue
                back = at + _choice(WITHHOLD_BARS, self._u("withhold bars", t_next))      # retired, and the lane left empty a while
                t = self._change(back, limit, cur, "new", skip=True, how=how) if back < limit else None
                if t is None:                                     # no bar of its own for the new one: empty until the next section's
                    cur = was
                    break
            k += 1

    def _pool(self, members):
        """The slice layers and processing, together, on the four-bar lines nobody else has: at each free line the change
        that has waited longest is made (on a tie, the lane that changed least lately; then the earlier in the list),
        one a line. A change that has waited MAX_WAIT bars gives way to its clock's next tick."""
        def period(name, aspect, at):
            self._lane(name, kinds[name])
            if kinds[name] == "processing":
                return _pick(PROCESS_PERIODS, self._u("period", at))
            r = self.roller_at(at)
            scale = 0.5 if r < 8 else 2.0 if r >= 32 else 1.0
            return max(4, 4 * int(round(_pick(weights[aspect], self._u(aspect, "period", at)) * scale / 4.0)))

        weights = dict(ASPECTS)
        weights["processing"] = PROCESS_PERIODS
        kinds = {name: kind for name, kind, _, _ in members}
        order = {name: index for name, _, _, index in members}
        due, state, versions, lately = {}, {}, {}, {}
        for name, kind, start, _ in members:
            self._lane(name, kind)
            aspects = ("processing",) if kind == "processing" else tuple(a for a, _ in ASPECTS)
            state[name], versions[name], lately[name] = {"version": 0, "generation": 0}, {a: 0 for a in aspects}, start
            self._put(start, state[name], "start", False, versions=versions[name] if kind == "slices" else None)
            base = 4 * -(-start // 4)
            for a in aspects:
                first = 4 * (2 + int(self._u("first") * 5)) if kind == "processing" else 4 * (1 + int(self._u(a, "phase") * period(name, a, base) / 4))
                due[(name, a)] = base + first
        line = 4
        while line < self.horizon:
            for key in due:                                       # waited too long: given up, until the clock comes round
                while line - due[key] > MAX_WAIT:
                    due[key] += period(key[0], key[1], due[key])
                    self.skipped += 1
            ready = [key for key in due if due[key] <= line]
            if ready and not self.busy.get(line):
                name, aspect = min(ready, key=lambda key: (due[key], lately[key[0]], order[key[0]], key[1]))
                lately[name] = line
                self._lane(name, kinds[name])
                state[name] = {"version": state[name]["version"] + 1, "generation": 0}
                if kinds[name] == "processing":
                    self._put(line, state[name], "mutate", True, how=_choice(PROCESS_HOW, self._u("how", line)))
                else:
                    versions[name][aspect] += 1
                    self._put(line, state[name], "new" if aspect == "source" else "mutate", True, how=aspect, aspect=aspect,
                              versions=versions[name])
                self.busy.setdefault(line, []).append((name, False, False))
                due[(name, aspect)] = line + period(name, aspect, line)
            line += 4


_CACHE = {}


def development(seed, lanes=DEFAULT_LANES, roller=DEFAULT_ROLLER, section=SECTION):
    """The Development for these arguments, kept (a few at a time) so that asking bar after bar is cheap."""
    key = (repr(seed), _lanes(lanes), _rollers(roller), int(section))
    if key not in _CACHE:
        if len(_CACHE) >= 16:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[key] = Development(seed, lanes, roller, section)
    return _CACHE[key]


def state(seed, bar, lanes=DEFAULT_LANES, roller=DEFAULT_ROLLER, section=SECTION):
    """{lane: info} at `bar`: each lane's version of its material and what happens to it there (module doc)."""
    return development(seed, lanes, roller, section).state(bar)


def events(seed, start, end, lanes=DEFAULT_LANES, roller=DEFAULT_ROLLER, section=SECTION):
    """[(bar, lane, info)] for every bar in start..end-1 where a lane does something other than hold."""
    return development(seed, lanes, roller, section).events(start, end)
