"""The course of a session: the edge's two dials (edge.py) and development's clocks (develop.py), worked out a bar or
a few ahead, aside from the sound, and looked up by everything that plays (docs/research/README.md, build steps 4
and 5).

The mixer keeps one Course. Its `advance(bar, layers)` is asked on the chop planner's thread at every bar line; it
steps the edge's budget one bar ahead (so a dial turned by hand is heard within two bars) and works development out
DEV_AHEAD bars ahead (so the riff, the hook and the drums of a bar are known before the rhythm section's worker makes
its notes, two bars ahead). The sound's thread only looks things up here: a dict lookup, never a calculation.

What each lane takes from it:

- the sub (the riff) and the hook: a version for bassline.riff / motif.motif, carrying the development's path,
  ((how, seed, fate), ...): every kept mutation, rewrite, new riff, transposition, B riff and A back changed, in
  order, applied with bassline.mutate / motif.mutate exactly as develop names them. "hole" bars are out (groove asks
  `hole`). groove.develop is this object (versions, hole, drums).
- the drums: (version, kept changes) for deal.held_bar, so the B drums at 32 are a new deal (the kick style and the
  carrier change with the B riff) and A at 64 is the first deal back with one thing changed; and the edge's numbers
  for that bar (edge.deal_numbers), passed in, never set on the module.
- the chopped layers: each sample layer is a development lane of its own, (name, "slices", the bar it came in),
  kept in the list after it has gone so the others' clocks do not move. Its four clocks map onto its plans: source
  -> a new deal of its chop (its seed), role -> the role it asks for, odds -> its density, processing -> its own
  rolls, stutters and reversals. The chop lane (processing) moves the chop preset as a whole on its slow clock.
  The edge's params then apply to the preset (edge.chop_preset), the density (layers) and the damage knob (filth).
- the excursion: when the budget lets one dial past its lip, its numbers go to the one lane named, and only there
  (edge.LANE_GROUPS): the drums' numbers for those bars, or the chop presets, density and damage for those bars.

The hand beats development. A riff or a hook held by hand (made or mutated by hand: groove.sub_held, hook_held), a
drum part written by hand (groove.by_hand), a layer held by hand (mutated: "held"), placed by hand ("steps"), given
a role by hand ("role_by_hand") or a density by hand ("density") is left as the hand left it until it is let go (a
new score or style, "reset"); development's clocks run on underneath, and what they say is heard again from then.
The edge's dials are a hand too, so they apply to everything that is planned, held layers excepted.
"""
from . import chopper, develop, edge
from .deal import _draw

DEV_AHEAD = 6                 # bars development is worked out ahead of the bar playing (groove plans two ahead, the chop a group)
EDGE_AHEAD = 1                # bars the edge's budget is stepped ahead: a dial is heard from the bar after next at the latest
KEEP = 48                     # bars kept behind the one playing (groove asks about the bar before, for slides)
RIFF, DRUMS, HOOK, CHOP = "sub", "drums", "hook", "chop"
CORE = ((RIFF, "riff"), (DRUMS, "drums"), (HOOK, "motif"), (CHOP, "processing"))
LAYER = "layer "              # a sample layer's lane: "layer rain" (so no layer's name can be mistaken for sub, drums ...)
SAID = ("B", "A_changed", "new", "rewrite", "transpose", "rhythm")      # the riff's fates the viewer is told of
BACK_WORDS = {"second_bass": "with the second bass under it", "other_skeleton": "on other notes", "harder": "harder"}
MOVE_WORDS = {"down_step": "down a step", "up_step": "up a step", "up_fourth": "up a fourth"}


def _walk(dev, lane, bar):
    """The development path of a riff or hook lane at `bar`: ((how, seed, fate), ...) in order. New material is made
    from what was playing (its path, and this step); a version that comes back (A at 64) carries its own path on."""
    paths, cur = {}, None
    for at, rec in zip(dev.bars[lane], dev.recs[lane]):
        if at > bar:
            break
        v = rec["version"]
        if rec["fate"] in develop.MATERIAL:
            paths[v] = (paths[v] if v in paths else paths.get(cur, ())) + ((rec["how"], rec["seed"], rec["fate"]),)
        elif v not in paths:
            paths[v] = paths.get(cur, ())
        cur = v
    return paths.get(cur, ())


def _changes(dev, lane, bar):
    """The drums at `bar`: (version, the kept changes made to that version since it was first dealt)."""
    changes, cur = {}, 0
    for at, rec in zip(dev.bars[lane], dev.recs[lane]):
        if at > bar:
            break
        v = rec["version"]
        if v not in changes:
            changes[v] = ()
        elif rec["fate"] in develop.MATERIAL and rec["how"]:
            changes[v] += (rec["how"],)
        cur = v
    return cur, changes.get(cur, ())


def _processing(dev, bar):
    """The chop lane's processing at `bar`: {how: a number 0..1} for the last change of each kind (PROCESS_HOW)."""
    out = {}
    for at, rec in zip(dev.bars[CHOP], dev.recs[CHOP]):
        if at > bar:
            break
        if rec["fate"] == "mutate" and rec["how"]:
            out[rec["how"]] = _draw(rec["seed"], "processing", rec["how"])
    return out


def processed(preset, process, own=None):
    """A chop preset (a copy) as development's processing has it. process: the chop lane's {how: u}; own: a layer's
    own processing clock's {"reverse", "stutter", "roll"} multipliers. Each change replaces the last of its kind, so
    nothing drifts away: unit finer or coarser (1 .. 4 cells), operators (rolls, empty downbeats, the reset kick, the
    drop) at half to one and a half, stutters at half to twice, reversals at a third to twice, returns at three
    quarters to one and a quarter. [The sizes are inference.]"""
    out = dict(preset)
    clamp = lambda x: min(max(x, 0.0), 1.0)                       # noqa: E731
    u = process.get("unit")
    if u is not None and "unit" in out:
        out["unit"] = max(1, out["unit"] // 2) if u < 0.5 else min(out["unit"] * 2, 4)
    for how, names, low, high in (("operators", ("roll", "roll_any", "empty", "kickback", "drop"), 0.5, 1.5),
                                  ("stutter", ("stutter",), 0.5, 2.0), ("reverse", ("reverse",), 0.33, 2.0),
                                  ("returns", ("returns",), 0.75, 1.25)):
        u = process.get(how)
        if u is not None:
            for name in names:
                if name in out:
                    out[name] = clamp(out[name] * (low + (high - low) * u))
    for name, by in (own or {}).items():
        if name in out:
            out[name] = clamp(out[name] * by)
            if name == "roll" and "roll_any" in out:
                out["roll_any"] = clamp(out["roll_any"] * by)
    return out


class Course:
    """The edge and development, a bar or a few ahead (see the module's doc). seed: the session's (development's
    draws); groove: the rhythm section (whose hand holds it reads); log: where the development lines go."""

    def __init__(self, seed=0, groove=None, log=None):
        self.seed, self.groove, self.log = seed, groove, log or (lambda msg: None)
        self.edge = edge.EdgeControl(seed)
        self.lanes = list(CORE)                   # + (LAYER + name, "slices", the bar it came in), kept after it goes
        self.layer_lanes = {}                     # layer name -> its lane
        self.rollers = [(0, develop.DEFAULT_ROLLER)]
        self.taken = len(self.edge.rollers)       # entries of the edge's roller schedule already taken into self.rollers
        self.snaps, self.edges = {}, {}           # bar -> what development says there; bar -> the edge's budget there
        self.dev_done = self.edge_done = -1
        self.latest_snap = self.latest_edge = None
        self.first = 0
        self.lines, self.said = {}, -1            # bar -> the development lines to say when it plays
        self.filth = 0.0                          # the damage added to every layer's knob now (the edge's mangle)
        self.advance(0)

    # ------------------------------------------------------------------ asked on the planner's thread, at bar lines

    def advance(self, now, layers=None):
        """Work out what is not yet known, up to the bar `now` + DEV_AHEAD (development) and `now` + EDGE_AHEAD (the
        edge); say the lines of the bars that have begun. layers: the mixer's {name: layer}, for the lanes of the
        layers that have come in. Returns what the planner should do about it: {"replan": the chop plans of the groups
        about to play are out of date, "filth": the damage offset changed (layers to be shaped again)}."""
        now = max(int(now), 0)
        for name, layer in list((layers or {}).items()):
            if layer.get("in") and name not in self.layer_lanes:  # a layer's clocks start at the first bar not yet worked out
                self.layer_lanes[name] = LAYER + name
                self.lanes.append((LAYER + name, "slices", self.dev_done + 1))
        replan, filth = False, None
        for b in range(self.edge_done + 1, now + EDGE_AHEAD + 1):
            was = self.edges.get(b - 1)
            rec = self._edge_bar(b)
            self.edges[b], self.latest_edge, self.edge_done = rec, rec, b
            if was is not None and (was["chops"] != rec["chops"] or was["numbers"] != rec["numbers"]):
                replan = True                                     # the plans played against these bars were made with other numbers
            if abs(rec["filth"] - self.filth) > 0.02:
                self.filth = filth = rec["filth"]
        for at, bars in self.edge.rollers[self.taken:]:           # the roller as the edge has it, never rewriting a bar worked out
            self.rollers.append((max(at, self.dev_done + 1), bars))
        self.taken = len(self.edge.rollers)
        dev = develop.development(self.seed, tuple(self.lanes), tuple(self.rollers))
        for b in range(self.dev_done + 1, now + DEV_AHEAD + 1):
            snap = self._snap_bar(dev, b)
            self.snaps[b], self.latest_snap, self.dev_done = snap, snap, b
        while self.first < now - KEEP:                            # older bars let go (looked up by key: never iterated)
            self.snaps.pop(self.first, None)
            self.edges.pop(self.first, None)
            self.first += 1
        for b in range(self.said + 1, now + 1):
            for line in self._said(b, layers or {}):
                self.log(line)
            self.lines.pop(b, None)
        self.said = max(self.said, now)
        return {"replan": replan, "filth": filth}

    def _edge_bar(self, b):
        """The edge at bar b: the budget's result, and what each lane takes from it there."""
        r = self.edge.step(b)
        where = {lane: dict(r["params"]) for lane in edge.LANES}
        if r["lane"]:
            for group in edge.LANE_GROUPS[r["lane"]]:
                where[r["lane"]][group] = r["excursion"][group]
        return {"bar": b, "result": r, "lane": r["lane"], "numbers": edge.deal_numbers(where["drums"]), "chops": where["chops"],
                "filth": where["chops"]["mangle"]["filth"]}

    def _snap_bar(self, dev, b):
        """What development says at bar b, as each lane takes it."""
        state = dev.state(b)
        snap = {"bar": b, "state": state,
                "riff": {"riff": 0, "side": "A", "partial": 0, "gen": 0, "path": _walk(dev, RIFF, b)},
                "hook": {"motif": 0, "gen": 0, "path": _walk(dev, HOOK, b)},
                "riff_hole": state[RIFF]["fate"] == "hole", "hook_hole": state[HOOK]["fate"] == "hole",
                "drums": _changes(dev, DRUMS, b), "processing": _processing(dev, b)}
        lines = []
        riff = state[RIFF]
        if riff["changing"] and riff["fate"] in SAID:
            lines.append(("riff", self._riff_line(riff)))
        for name, lane in self.layer_lanes.items():
            info = state.get(lane)
            if info and info["changing"] and info["aspect"] in ("role", "source"):
                lines.append((name, self._layer_line(name, lane, info)))
        if lines:
            self.lines[b] = lines
        return snap

    def _riff_line(self, info):
        fate, how = info["fate"], info["how"]
        if fate == "B" and how in BACK_WORDS:
            return "The bass: the B riff comes back, " + BACK_WORDS[how] + "."
        if fate == "B":
            return "The bass: the B riff comes in, and the kick changes with it."
        if fate == "A_changed":
            return "The bass: the first riff comes back, " + BACK_WORDS.get(how, "changed") + "."
        if fate == "new" and info["section"]:
            return "The bass: a new riff, kin to the last, and new drums with it."
        if fate == "transpose":
            return "The bass: the riff moves " + MOVE_WORDS.get(how, "") + "."
        return {"new": "The bass: a new riff.", "rewrite": "The bass: half the riff written again.",
                "rhythm": "The bass: the same notes on a new rhythm."}.get(fate, "")

    def _layer_line(self, name, lane, info):
        if info["aspect"] == "source":
            return f"The {name}: the same sound, read another way."
        return f"The {name}: it plays the {self._role(name, info['versions']['role'])} now."

    def _said(self, b, layers):
        """The development lines of bar b, less those about something held by hand."""
        out = []
        g = self.groove
        for who, line in self.lines.get(b, ()):
            if not line:
                continue
            if who == "riff":
                if g is not None and (g.sub_held or not g._written()):
                    continue                                      # the riff is the hand's, or not playing
            else:
                layer = layers.get(who)
                if layer is None or layer.get("in") is not True or layer.get("held") or layer.get("steps") is not None:
                    continue
                if "plays the" in line and layer.get("role_by_hand"):
                    continue
            out.append(line)
        return out

    # ------------------------------------------------------------------ looked up (the sound's thread among others)

    def _snap(self, bar):
        snap = self.snaps.get(bar)
        if snap is None:                      # not worked out (yet, or any more): the nearest that is
            snap = self.snaps.get(self.first) if bar < self.first else None
            snap = snap or self.latest_snap
        return snap

    def _edge(self, bar):
        rec = self.edges.get(bar)
        if rec is None:
            rec = (self.edges.get(self.first) if bar < self.first else None) or self.latest_edge
        return rec

    def versions(self, bar):
        """(riff version, hook version) for bar `bar`, as groove takes them."""
        snap = self._snap(bar)
        return snap["riff"], snap["hook"]

    def hole(self, bar, lane="riff"):
        """Is the riff ("riff") or the hook ("hook") out for this bar?"""
        return self._snap(bar)["riff_hole" if lane == "riff" else "hook_hole"]

    def drums(self, bar):
        """(material, numbers) for deal.held_bar at this bar."""
        return self._snap(bar)["drums"], self._edge(bar)["numbers"]

    def params(self, bar):
        """The edge's params as the chopped layers take them at this bar (the excursion's groups, when it is theirs)."""
        return self._edge(bar)["chops"]

    def layer(self, name, bar):
        """What development says of a layer at bar `bar` (the group's first): {"source": changes so far, "role": the
        role its clock gives it (None until it has ticked), "odds": a density offset, "own": its processing's
        multipliers}, or None for a layer with no lane (the clip, or one not yet in)."""
        lane = self.layer_lanes.get(name)
        info = self._snap(bar)["state"].get(lane) if lane else None
        if not info or not info.get("versions"):
            return None
        v = info["versions"]
        own = None
        if v.get("processing"):
            own = {what: round(0.5 + 1.3 * _draw(self.seed, name, "own", what, v["processing"]), 3) for what in ("reverse", "stutter", "roll")}
        return {"source": v.get("source", 0), "role": self._role(name, v["role"]) if v.get("role") else None,
                "odds": round(0.4 * (_draw(self.seed, name, "odds", v["odds"]) - 0.5), 3) if v.get("odds") else 0.0, "own": own}

    def _role(self, name, count):
        return chopper.ROLES[int(_draw(self.seed, name, "role", count) * len(chopper.ROLES)) % len(chopper.ROLES)]

    def presets(self, style, bar, grown=None):
        """The four bars of a group from `bar`: [(preset, density offset)], one a bar. The style's preset, as the
        chop lane's processing and the layer's own (grown: `layer`) have it, then as the edge's dials have it in that
        bar (the excursion's, on the bars it has the chopped layers). Mostly four times the same."""
        out = []
        for b in range(bar, bar + 4):
            snap, p = self._snap(b), self.params(b)
            base = processed(chopper.PRESETS.get(style) or chopper.PRESETS[chopper.DEFAULT_STYLE], snap["processing"], (grown or {}).get("own"))
            out.append((edge.chop_preset(base, p), p["layers"]["density"]))
        return out

    # ------------------------------------------------------------------ for the panels and the memories

    def stands(self):
        return {"edge": self.edge.stands(), "roller": self.edge.roller}

    def keep(self):
        """What a memory keeps of the edge: whose the dials are, where they stand, the lips, the roller."""
        e = self.edge
        return {"wanted": dict(e.wanted), "auto": e.auto, "lips": dict(e.budget.lips), "roller": e.roller}

    def restore(self, kept):
        """Back to a memory's edge (kept by `keep`; None leaves it as it is)."""
        if not isinstance(kept, dict):
            return
        e = self.edge
        e.wanted.update({d: edge._clamp(v) for d, v in (kept.get("wanted") or {}).items() if d in edge.DIALS})
        e.auto = bool(kept.get("auto", e.auto))
        if e.auto:
            e.session = None
        for dial, at in (kept.get("lips") or {}).items():
            e.budget.set_lip(dial, at)
        if kept.get("roller") is not None:
            e.take_roller(kept["roller"])
