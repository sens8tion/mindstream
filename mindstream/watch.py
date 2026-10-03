"""The program measures itself (docs/research/README.md, build step 6): the checks of steps 1 to 5 run on what was
played, bar by bar, so that a session that has drifted into a loop, or into noise, can be seen.

It only reads what it is given. The mixer hands it one finished bar at a time from a thread of its own (never the
sound's), and asks for the report; nothing here touches sound.

What goes in: `Watch.add_bar(bar, lanes, edge=None)`

    bar     the bar's number (an int that only rises; bars skipped are taken as silent; an older one is ignored)
    lanes   {lane name: [event, ...]}, the onsets that bar, one entry per onset. An event is
                step                  0 to 15 (the sixteenth in the bar; 0 is the one)
                (step, value)
                (step, value, kind)
            value: for "sub", "bass" and "tune" the note's pitch in semitones (MIDI or relative to the root: only
            its pitch class and the steps between notes are used), or None; for a sample layer the slice's index;
            for "kick" and "snare" anything (ignored). kind: a sample layer's slice class from chopper.classify
            ("heavy", "sharp", "ghost", "tone", "other"), when known.
            The names "kick", "snare" (the drums), "sub", "bass" (the low end) and "tune" (the hook) are the
            rhythm section's; any other name is a sample layer (chopped, or the clip).
    edge    the edge's state that bar (edge.EdgeControl.stands()), when there is an edge; else the edge check is
            skipped (None)

What comes out: `Watch.report()`, a dict (numbers rounded; None where there was too little to measure)

    {"bar": last bar given, "window": bars judged (32),
     "verdict": "healthy" | "looping" | "noise" | "quiet",
     "why": one short plain reason,
     "lanes": {lane: {"v": verdict of the lane ("healthy" | "looping" | "noise" | "quiet"),
                      "bars": bars of the window it sounded in,
                      "lag1", "lag4": bar-to-bar similarity 1 and 4 bars apart, less the window's baseline,
                      "base": the baseline (mean similarity of every pair of bars in the window),
                      "rep1", "rep4": share of bars exactly the same as the bar 1 / 4 before,
                      "distinct": different bars / bars sounded,
                      "change": cells changed bar to bar against independent dealing from the lane's own odds
                                (0 still, about 0.8 the reference's lip, 1 independent: noise),
                      sub and bass also: "agree1", "agree2", "agree4" (agreement of the line with itself 1, 2
                                and 4 bars back), "step6" (share of onsets on step 6, 1-based), "colour"
                                (share of colour notes resolved),
                      tune also: "coincide" (onsets on the low end's onsets, against chance: 1 is chance)}},
     "spine": [share of bars with steps 1, 5 and 13 (or its stand-ins 15 and 11) sounding],
     "mix": [the whole bar, every lane together: share the same as 1 back, as 4 back, different bars / bars],
     "overlap": [worst share of cells two sample layers start on together, "a+b"] or None,
     "came_back": True | False | None (None until 64 bars have been heard),
     "past_lip": [lanes that sound past the lip over the last 8 bars, measured: they change as much as dealing
                  afresh would and nothing comes back at four bars] (shown, not a check: the edge's own word is),
     "edge": {"most": most dials past their lips in one bar of the last 8, "now": [dials past this bar],
              "bars_past": bars of the last 8 with one past, "of": bars of the last 8 the edge was given} or None,
     "checks": {name: True | False | None}: the README's checks, one by one (see CHECKS)}

`Watch.compact()` (or `compact(report)`): the report cut down for Mixer.stands() and the panels (see `compact`).

`Watch.says()`: one short line of plain English when the overall verdict has changed (and held for `hold` bars),
or every `say_every` bars if that is set; "" otherwise. Lines look like
    watch: going round in a loop - the whole bar comes round again: 100% of bars the same as 4 back
    watch: drifting into noise - the spine has gone: step 1 sounds in 56% of bars
    watch: healthy again - bars change and come back (lag 4 +0.16 over the baseline)

The verdicts. A lane: "quiet" under 8 bars of 32; "looping" when half its bars are the same as 1 or 4 back, or a
quarter or fewer of its bars differ (the low end may hold its riff longer: 3 in 4 the same as 4 back, or a fifth
different); "noise" when it changes as much as dealing each bar afresh would and lag 4 is no more similar than any
two bars (or, for the low end, it agrees with itself neither 2 nor 4 bars back); else "healthy". The session:
"noise" when the spine has gone or two lanes are noise (one is the edge, allowed); "looping" when the whole bar
comes round again, or every lane but the drums loops (the drums alone looping is the frame: it shows in their
lanes); else "healthy".

The measures, and where their numbers come from:
- Similarity of two bars: the Pearson correlation of 16 steps x 3 bands (a sample layer by slice class, heavy /
  tone and other / sharp and ghost, as demo/chop_check.py; a pitched lane by pitch class in thirds of the octave).
  Lag 1 should sit at the baseline and lag 4 about 0.13 above it [README step 1; 04 section 5]. A lane whose lag 4
  is at the baseline has no phrase; one whose lag 1 is well above it is repeating [04 "What to measure"].
- Exact repeats: near zero for chopped lanes [README step 1], where the old four-bar plan gave 0.73 to 0.86.
- Cells changed bar to bar, against dealing each bar independently from the lane's own odds: 15 of 19 at the
  reference's lip, 19 of 19 is independent dealing, "noise" [04 section 5, the dial table].
- The spine: steps 1, 5, 13 above 0.9 [README step 1]; under about 0.6 is noise [04 section 5].
- The low end: agreement at 2 and 4 bars over half with lag 1 lower; under 4% of onsets on step 6; every colour
  note resolved [README step 2]. A colour note is one outside the three commonest pitch classes of the window; it
  is resolved when the next note of the line is one of those three, within two semitones.
- The hook: its onsets coincide with the low end's less than chance [README step 3].
- Development: after 64 bars, a four-bar group heard 32 or more bars earlier is back, changed (similar, not the
  same) after the lane had moved away from it [README step 4].
- The edge: one dial past the lip at a time [README step 5; 04 section 5 "how to turn them"], from the edge's own
  state (edge.py) over the last 8 bars; skipped when there is no edge.
"""
import collections

import numpy as np

STEPS, BANDS = 16, 3
WINDOW = 32            # bars judged
SHORT = 8              # bars for the edge (who is past the lip now)
HISTORY = 128          # bars kept
MIN_BARS = 8           # a lane must sound in this many bars of the window to be judged
MIN_PAIRS = 6          # and in this many pairs of bars four apart before it can be said to have no phrase
DENSE = 0.75           # a sample layer sounding in this share of the window's bars is held to the chop checks
                       # (a hook or a stab, in three bars of eight, is not: its numbers rest on too few bars)
DEVELOP = 64           # bars heard before "has something come back changed" is asked

# the thresholds (see the module's doc for where they come from)
LOOP_REPEAT = 0.5      # share of bars the same as 1 or 4 back that is a loop
LOOP_DISTINCT = 0.25   # different bars / bars at or below which it is a loop (a four-bar loop in 32 bars is 0.125)
LOW_LOOP_REPEAT4 = 0.75    # the low end may repeat its riff more (a riff runs a median 11 bars) [05]
LOW_LOOP_DISTINCT = 0.2
NO_PHRASE = 0.03       # lag 4 less the baseline at or below which there is no four-bar relation
CHANGE_NOISE = 0.9     # cells changed against independent dealing at or above which a lane is noise
CHANGE_LIP = 0.95      # the same over the last 8 bars against the lane's 32-bar odds: past the lip
SPINE_OK, SPINE_NOISE = 0.9, 0.6
LAG1_NEAR = 0.1        # lag 1 within this of the baseline [README step 1: chop_check's 0.05 over 128 bars and four
                       # seeds; doubled for one 32-bar window]
REPEAT1_MAX, REPEAT4_MAX = 0.05, 0.10   # exact repeats "near zero" [README step 1, chop_check]
LAG4_LIFT = 0.07       # lag 4 at least this above the baseline (0.13 +/- 0.06)
OVERLAP_MAX = 0.5
AGREE_MIN = 0.5
STEP6_MAX = 0.04

DRUMS, LOW, HOOK = ("kick", "snare"), ("sub", "bass"), ("tune",)
SECTION_LANES = DRUMS + LOW + HOOK
CHECKS = ("lag1_at_base", "lag4_above", "few_repeats", "spine", "overlap", "low_agrees", "low_step6", "colour_resolved",
          "hook_off_bass", "came_back", "one_past_lip")


def kind_of(lane):
    """"drum", "low", "hook" or "layer"."""
    return "drum" if lane in DRUMS else "low" if lane in LOW else "hook" if lane in HOOK else "layer"


def _band(lane_kind, value, slice_kind):
    if lane_kind == "layer":
        if slice_kind is not None:
            return 0 if slice_kind == "heavy" else 2 if slice_kind in ("sharp", "ghost") else 1
        return int(value) % BANDS if isinstance(value, (int, np.integer)) else 0
    if lane_kind in ("low", "hook") and value is not None:
        return pitch_class(value) // 4
    return 0


def pitch_class(value):
    return int(round(float(value))) % 12


def normalise(events):
    """[(step, value, kind)] from any of the event forms, the steps checked (0 to 15), one per step and value."""
    out, seen = [], set()
    for e in events or ():
        if isinstance(e, (tuple, list)):
            step, value, kind = (list(e) + [None, None])[:3]
        else:
            step, value, kind = e, None, None
        try:
            step = int(step)
        except (TypeError, ValueError):
            continue
        if not 0 <= step < STEPS:
            continue
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        key = (step, value)
        if key not in seen:
            seen.add(key)
            out.append((step, value, kind))
    return sorted(out, key=lambda e: (e[0], str(e[1])))


def bar_record(lane, events):
    """What is kept of one lane's bar: onsets, the exact signature, the vector, and the notes (for pitched lanes)."""
    evs = normalise(events)
    if not evs:
        return None
    k = kind_of(lane)
    vec = np.zeros(STEPS * BANDS, np.float32)
    for step, value, slice_kind in evs:
        vec[step * BANDS + _band(k, value, slice_kind)] = 1.0
    sig = frozenset((s, None if k == "drum" else v) for s, v, _ in evs)
    notes = tuple((s, None if v is None else float(v)) for s, v, _ in evs) if k in ("low", "hook") else ()
    return {"on": frozenset(s for s, _, _ in evs), "sig": sig, "vec": vec, "notes": notes}


# ---- the measures (pure: lists of bar records, None for a silent bar) ---------------------------------------

def lag_similarity(vectors, lags=(1, 2, 4)):
    """Mean correlation of bars `lag` apart, and the baseline (every pair in the list); None where no pair counts."""
    out = {lag: None for lag in lags}
    out.update({f"n{lag}": 0 for lag in lags}, base=None)
    idx =[i for i, v in enumerate(vectors) if v is not None]
    if len(idx) < 2:
        return out
    m = np.stack([vectors[i] for i in idx]).astype(np.float64)
    m -= m.mean(axis=1, keepdims=True)
    norms = np.sqrt(np.einsum("ij,ij->i", m, m))
    keep = norms > 1e-12                                # a bar sounding on every cell of its bands has no shape
    if keep.sum() < 2:
        return out
    idx, m = np.array(idx)[keep], m[keep] / norms[keep, None]
    c = m @ m.T
    n = len(idx)
    out["base"] = float((c.sum() - np.trace(c)) / (n * (n - 1)))
    row = np.full(len(vectors) + max(lags), -1)
    row[idx] = np.arange(n)
    for lag in lags:
        other = row[idx + lag]
        has = other >= 0
        if has.any():
            out[lag] = float(c[np.arange(n)[has], other[has]].mean())
        out[f"n{lag}"] = int(has.sum())
    return out


def repeat_shares(sigs):
    """(share the same as the bar before, as 4 bars before, different bars / bars sounded); None for too few."""
    def share(lag):
        pairs = [(sigs[b], sigs[b - lag]) for b in range(lag, len(sigs)) if sigs[b] is not None and sigs[b - lag] is not None]
        return sum(a == b for a, b in pairs) / len(pairs) if pairs else None
    sounded = [s for s in sigs if s is not None]
    return share(1), share(4), (len(set(sounded)) / len(sounded) if sounded else None)


def odds(onsets):
    """Per step, the share of bars it sounds in (silent bars count)."""
    p = np.zeros(STEPS)
    for on in onsets:
        for s in on or ():
            p[s] += 1
    return p / max(len(onsets), 1)


def change_ratio(onsets, chances=None):
    """Mean cells changed between consecutive bars, against what dealing every bar independently from `chances`
    (default: the bars' own odds) would change. 0 still, about 0.8 the reference's lip, 1 independent."""
    if len(onsets) < 2:
        return None
    p = odds(onsets) if chances is None else chances
    expected = float(np.sum(2 * p * (1 - p)))
    if expected <= 1e-9:
        return 0.0
    changed = [len((a or frozenset()) ^ (b or frozenset())) for a, b in zip(onsets, onsets[1:])]
    return float(np.mean(changed)) / expected


def agreement(a, b):
    """How much two bars of a line agree: an onset on the same step counts 1 with the same pitch class (or a pitch
    unknown), a half with another; over the mean number of onsets. 1 is the same bar, 0 nothing shared."""
    if not a or not b:
        return None
    pa = {}
    for s, p in a:
        pa.setdefault(s, set()).add(None if p is None else pitch_class(p))
    got = 0.0
    for s, p in b:
        if s in pa:
            pc = None if p is None else pitch_class(p)
            got += 1.0 if pc is None or None in pa[s] or pc in pa[s] else 0.5
    return 2 * got / (len(a) + len(b))


def low_checks(notes):
    """The low end's checks over bars of notes ([(step, pitch)] or None): agreement 1, 2, 4 bars back, the share on
    step 6 (1-based), and the share of colour notes resolved (None if there were none)."""
    out = {}
    for lag in (1, 2, 4):
        vals = [agreement(notes[b], notes[b - lag]) for b in range(lag, len(notes)) if notes[b] and notes[b - lag]]
        out[f"agree{lag}"] = float(np.mean(vals)) if vals else None
    flat = [(b, s, p) for b, bar in enumerate(notes) for s, p in (bar or ())]
    out["step6"] = sum(s == 5 for _, s, _ in flat) / len(flat) if flat else None
    pitched = [(b, s, p) for b, s, p in flat if p is not None]
    count = collections.Counter(pitch_class(p) for _, _, p in pitched)
    home = {pc for pc, _ in sorted(count.items(), key=lambda kv: (-kv[1], kv[0]))[:3]}
    colour = resolved = 0
    for i, (_, _, p) in enumerate(pitched[:-1]):          # the last note's next is not heard yet
        if pitch_class(p) not in home:
            colour += 1
            a, b = pitch_class(p), pitch_class(pitched[i + 1][2])
            resolved += b in home and min((a - b) % 12, (b - a) % 12) <= 2
    out["colour"] = resolved / colour if colour else None
    return out


def coincide_ratio(hook, low):
    """The hook's onsets that land on the low end's onsets, against chance (1 = chance); bars where both sound."""
    hit = chance = 0.0
    for h, lo in zip(hook, low):
        if h and lo:
            hit += len(h & lo)
            chance += len(h) * len(lo) / STEPS
    return hit / chance if chance else None


def spine_shares(kick, snare, layers):
    """Share of bars (with any drums or layers) where step 1 has a kick or a layer, step 5 a snare or a layer, and
    step 13 (or its stand-ins 15 and 11, as chop_check takes the second backbeat) a snare or a layer."""
    n, got = 0, [0, 0, 0]
    for b in range(len(kick)):
        lay = frozenset().union(*[lane[b] or frozenset() for lane in layers]) if layers else frozenset()
        k, s = (kick[b] or frozenset()) | lay, (snare[b] or frozenset()) | lay
        if not k and not s:
            continue
        n += 1
        got[0] += 0 in k
        got[1] += 4 in s
        got[2] += bool(s & {12, 14, 10})
    return [g / n for g in got] if n else None


def layer_overlap(layers, first_bar):
    """Worst share of cells two sample layers start on together, per four-bar group (|A and B| / the smaller),
    averaged over the groups both sound in: (share, "a+b") or None. `layers`: {name: [onsets per bar]}."""
    names, worst = sorted(layers), None
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b, shares = layers[names[i]], layers[names[j]], []
            start = (-first_bar) % 4
            for g in range(start, len(a) - 3, 4):
                A = {16 * k + s for k in range(4) for s in a[g + k] or ()}
                B = {16 * k + s for k in range(4) for s in b[g + k] or ()}
                if A and B:
                    shares.append(len(A & B) / min(len(A), len(B)))
            if shares:
                share = float(np.mean(shares))
                if worst is None or share > worst[0]:
                    worst = (share, f"{names[i]}+{names[j]}")
    return worst


def came_back(vectors, sigs, first_bar, last_bar):
    """Has a four-bar group heard 32 or more bars earlier come back changed: similar (correlation 0.5 or more) but
    not the same, after the lane had moved away from it (a group between less similar by 0.2)? (bool, similarity)."""
    zero = np.zeros(STEPS * BANDS, np.float32)
    starts = list(range((-first_bar) % 4, len(vectors) - 3, 4))
    if len(starts) < 2:
        return False, None
    m = np.stack([np.concatenate([x if x is not None else zero for x in vectors[g:g + 4]]) for g in starts]).astype(np.float64)
    m -= m.mean(axis=1, keepdims=True)
    norms = np.sqrt(np.einsum("ij,ij->i", m, m))
    ok = [n > 1e-12 and sum(v is not None for v in vectors[g:g + 4]) >= 2 for g, n in zip(starts, norms)]
    m /= np.where(norms > 1e-12, norms, 1.0)[:, None]
    c = m @ m.T
    at = [first_bar + g for g in starts]
    best = (False, None)
    for r in range(len(starts)):
        if not ok[r] or at[r] < last_bar - 15:
            continue
        for e in range(r):
            if not ok[e] or at[e] > at[r] - 32:
                continue
            s = float(c[r, e])
            if s < 0.5 or sigs[starts[r]:starts[r] + 4] == sigs[starts[e]:starts[e] + 4]:
                continue
            between = [c[e, k] for k in range(e + 1, r) if ok[k]]
            if between and min(between) <= s - 0.2 and (best[1] is None or s > best[1]):
                best = (True, s)
    return best


def lane_verdict(m, kind):
    """A lane's verdict from its numbers (see the thresholds above)."""
    if m["bars"] < MIN_BARS:
        return "quiet"
    rep1, rep4, distinct = m["rep1"] or 0.0, m["rep4"] or 0.0, m["distinct"] if m["distinct"] is not None else 1.0
    if kind == "low":
        if rep1 >= LOOP_REPEAT or rep4 >= LOW_LOOP_REPEAT4 or distinct <= LOW_LOOP_DISTINCT:
            return "looping"
    elif rep1 >= LOOP_REPEAT or rep4 >= LOOP_REPEAT or distinct <= LOOP_DISTINCT:
        return "looping"
    restless = m["change"] is not None and m["change"] >= CHANGE_NOISE
    if kind == "low" and restless and (m.get("agree2") or 0) < 0.3 and (m.get("agree4") or 0) < 0.3:
        return "noise"                                  # no riff: the line agrees with itself at no distance
    if restless and m.get("n4", 0) >= MIN_PAIRS and m["lag4"] is not None and m["lag4"] <= NO_PHRASE:
        return "noise"                                  # no phrase: four bars back says no more than any bar
    return "healthy"


def mix_shares(win):
    """The whole bar, every lane together: (same as 1 back, as 4 back, different bars / bars sounded)."""
    sigs = [frozenset((lane, x) for lane, r in rec.items() for x in r["sig"]) or None for _, rec in win]
    return repeat_shares(sigs)


def past_the_lip(vecs, ons, base, chances):
    """Over the last bars given: does the lane change as much as dealing every bar afresh from its own odds would,
    with nothing coming back at four bars (no exact return, and lag 4 no more similar than the baseline)?"""
    if sum(o is not None for o in ons) < len(ons) // 2 or base is None:
        return False
    c = change_ratio(ons, chances)
    lags = lag_similarity(vecs, (4,))
    back = any(a is not None and a == b for a, b in zip(ons[4:], ons))
    return c is not None and c >= CHANGE_LIP and not back and (lags[4] is None or lags[4] - base <= NO_PHRASE)


def dials_past(edge):
    """The dials past their lips in what is in force, from edge.EdgeControl.stands(): the excursion's dials ("over")
    when there is one, else the held ones ("base"), against "lips". A sorted list (the budget allows one)."""
    lips = edge.get("lips") or {}
    force = edge.get("over") or edge.get("base") or {}
    return sorted(d for d, v in force.items() if isinstance(v, (int, float)) and d in lips and v > lips[d] + 1e-9)


def compact(report):
    """The report cut down for Mixer.stands() and the panels:
        {"bar", "verdict", "why", "lanes": {lane: verdict}, "failed": [checks that failed], "passed": n,
         "spine": [3], "lag4": the sample layers' mean lag 4 over the baseline, "came_back", "past": [dials past now]}"""
    if not report:
        return None
    lanes = report.get("lanes") or {}
    lag = [m["lag4"] for lane, m in lanes.items() if kind_of(lane) == "layer" and m.get("v") != "quiet" and m.get("lag4") is not None]
    checks = report.get("checks") or {}
    return {"bar": report.get("bar"), "verdict": report.get("verdict"), "why": report.get("why"),
            "lanes": {lane: m.get("v") for lane, m in lanes.items()},
            "failed": [c for c, ok in checks.items() if ok is False], "passed": sum(ok is True for ok in checks.values()),
            "spine": report.get("spine"), "lag4": _r(np.mean(lag)) if lag else None, "came_back": report.get("came_back"),
            "past": (report.get("edge") or {}).get("now", [])}


def _r(x, n=3):
    return None if x is None else round(float(x), n)


class Watch:
    """A rolling monitor of what was played (see the module's doc for the formats)."""

    def __init__(self, window=WINDOW, say_every=0, hold=2):
        self.window, self.say_every, self.hold = window, say_every, hold
        self.bars = collections.deque(maxlen=HISTORY)      # (bar, {lane: record}) in order, silent bars included
        self.order = list(SECTION_LANES)                   # lanes in the order they were first heard (the band first)
        self.last = None
        self._cache, self._back = (None, None), (None, None)
        self._recent = collections.deque(maxlen=max(hold, 1))
        self._seen, self._said, self._said_at = None, None, None
        self.edges = collections.deque(maxlen=SHORT)       # (bar, dials past their lips, the dial past by the edge's word)

    def add_bar(self, bar, lanes, edge=None):
        """One finished bar (see the module's doc). `edge`, if given: the edge's state that bar, as
        edge.EdgeControl.stands() gives it (its "lips", "base" and "over" are used); the edge check is judged from it,
        and skipped (None) while none has been given. Returns False if the bar was older than the last one given."""
        bar = int(bar)
        if self.last is not None and bar <= self.last:
            return False
        if edge is not None:
            self.edges.append((bar, dials_past(edge), edge.get("past")))
        if self.last is not None:
            for gap in range(max(self.last + 1, bar - HISTORY), bar):
                self.bars.append((gap, {}))
        rec = {}
        for lane, events in (lanes or {}).items():
            lane = str(lane)
            r = bar_record(lane, events)
            if r is not None:
                rec[lane] = r
                if lane not in self.order:
                    self.order.append(lane)
        self.bars.append((bar, rec))
        self.last = bar
        return True

    def _series(self, bars, lane, what):
        return [rec[lane][what] if lane in rec else None for _, rec in bars]

    def report(self, pause=None):
        """The numbers and the verdicts, worked out once per bar given (see the module's doc). `pause`, if given, is
        called between the pieces of the work (see `steps`)."""
        for _ in self.steps():
            if pause is not None:
                pause()
        return self._cache[1]

    def steps(self):
        """The report's work a piece at a time (a generator; each piece well under a millisecond), so that a thread
        doing it can step aside for the sound's between pieces. When it is used up, `report()` returns the result
        at once."""
        if self._cache[0] == self.last and self._cache[1] is not None:
            return
        allbars = list(self.bars)
        win = allbars[-self.window:]
        short = allbars[-SHORT:]
        out = {"bar": self.last, "window": self.window, "verdict": "quiet", "why": "nothing has played yet", "lanes": {},
               "spine": None, "mix": None, "overlap": None, "came_back": None, "past_lip": [], "edge": None,
               "checks": {c: None for c in CHECKS}}
        if not win:
            self._cache = (self.last, out)
            return
        heard = [lane for lane in self.order if any(lane in rec for _, rec in win)]
        lanes, past = {}, []
        for lane in heard:
            yield
            k = kind_of(lane)
            vecs, sigs, ons = (self._series(win, lane, w) for w in ("vec", "sig", "on"))
            lags = lag_similarity(vecs)
            yield
            rep1, rep4, distinct = repeat_shares(sigs)
            base = lags["base"]
            m = {"bars": sum(s is not None for s in sigs), "base": base,
                 "lag1": None if lags[1] is None or base is None else lags[1] - base,
                 "lag4": None if lags[4] is None or base is None else lags[4] - base,
                 "rep1": rep1, "rep4": rep4, "distinct": distinct, "change": change_ratio(ons), "n4": lags["n4"]}
            if k == "low":
                yield
                m.update(low_checks(self._series(win, lane, "notes")))
            m["v"] = lane_verdict(m, k)
            yield
            if past_the_lip(self._series(short, lane, "vec"), self._series(short, lane, "on"), base, odds(ons)):
                past.append(lane)
            lanes[lane] = m
        if "tune" in lanes:
            low = [frozenset().union(*[x or frozenset() for x in xs]) or None
                   for xs in zip(*[self._series(win, lane, "on") for lane in LOW])]
            lanes["tune"]["coincide"] = coincide_ratio(self._series(win, "tune", "on"), low)
        layer_lanes = [lane for lane in heard if kind_of(lane) == "layer"]
        spine = spine_shares(self._series(win, "kick", "on"), self._series(win, "snare", "on"),
                             [self._series(win, lane, "on") for lane in layer_lanes])
        overlap = layer_overlap({lane: self._series(win, lane, "on") for lane in layer_lanes}, win[0][0]) if len(layer_lanes) > 1 else None
        back = None
        if len(allbars) >= DEVELOP:                      # asked again as each four-bar group ends
            group = (self.last + 1) // 4
            if self._back[0] == group:
                back = self._back[1]
            else:
                back = False
                for lane in heard:
                    yield
                    got, _ = came_back(self._series(allbars, lane, "vec"), self._series(allbars, lane, "sig"), allbars[0][0], self.last)
                    back = back or got
                self._back = (group, back)
        yield
        mix = mix_shares(win)
        edge = None
        if self.edges and self.edges[-1][0] > self.last - SHORT:
            recent = [e for e in self.edges if e[0] > self.last - SHORT]
            edge = {"most": max(len(e[1]) for e in recent), "now": self.edges[-1][1] if self.edges[-1][0] == self.last else [],
                    "bars_past": sum(bool(e[1]) for e in recent), "of": len(recent)}
        out.update(edge=edge, spine=[_r(x, 2) for x in spine] if spine else None, mix=[_r(x) for x in mix],
                   overlap=[_r(overlap[0], 2), overlap[1]] if overlap else None, came_back=back, past_lip=past)
        out["checks"] = self._checks(lanes, spine, overlap, back, edge, len(win))
        out["verdict"], out["why"] = self._overall(lanes, spine, mix)
        out["lanes"] = {lane: {key: (_r(v) if isinstance(v, float) else v) for key, v in m.items() if key != "n4"}
                        for lane, m in lanes.items()}
        self._cache = (self.last, out)

    @staticmethod
    def _checks(lanes, spine, overlap, back, edge, bars):
        judged = {lane: m for lane, m in lanes.items() if m["v"] != "quiet"}
        chopped = {lane: m for lane, m in judged.items() if kind_of(lane) == "layer" and m["bars"] >= DENSE * bars}
        low = {lane: m for lane, m in judged.items() if kind_of(lane) == "low"}

        def every(ms, f):
            vals = [f(m) for m in ms.values()]
            vals = [v for v in vals if v is not None]
            return all(vals) if vals else None
        hook = lanes.get("tune", {}).get("coincide")
        return {
            "lag1_at_base": every(chopped, lambda m: None if m["lag1"] is None else abs(m["lag1"]) <= LAG1_NEAR),
            "lag4_above": every(chopped, lambda m: None if m["lag4"] is None else m["lag4"] >= LAG4_LIFT),
            "few_repeats": every(chopped, lambda m: None if m["rep1"] is None else m["rep1"] <= REPEAT1_MAX and (m["rep4"] or 0) <= REPEAT4_MAX),
            "spine": None if not spine else min(spine) > SPINE_OK,
            "overlap": None if not overlap else overlap[0] <= OVERLAP_MAX,
            "low_agrees": every(low, lambda m: None if m.get("agree2") is None or m.get("agree4") is None else
                                max(m["agree2"], m["agree4"]) > AGREE_MIN and (m.get("agree1") or 0) < max(m["agree2"], m["agree4"])),
            "low_step6": every(low, lambda m: None if m.get("step6") is None else m["step6"] < STEP6_MAX),
            "colour_resolved": every(low, lambda m: None if m.get("colour") is None else m["colour"] >= 0.999),
            "hook_off_bass": None if hook is None else hook < 1.0,
            "came_back": back,
            "one_past_lip": None if edge is None else edge["most"] <= 1,
        }

    @staticmethod
    def _overall(lanes, spine, mix):
        """Noise: the spine has gone (a cell under 0.6), or two lanes are noise (one past the lip is the edge, not
        noise). Looping: the whole bar, every lane together, repeats (1 or 4 back in half the bars, or a quarter of
        the bars different), or every lane but the drums loops. The drums alone looping is the frame, not a loop:
        it shows in their lanes. Else healthy."""
        judged = {lane: m for lane, m in lanes.items() if m["v"] != "quiet"}
        if not judged:
            return "quiet", "too little has played to judge"
        noise = [lane for lane, m in judged.items() if m["v"] == "noise"]
        loop = [lane for lane, m in judged.items() if m["v"] == "looping"]
        if spine and min(spine) < SPINE_NOISE:
            cell = ("1", "5", "13")[int(np.argmin(spine))]
            return "noise", f"the spine has gone: step {cell} sounds in {min(spine):.0%} of bars"
        if len(noise) >= 2:
            lag4 = [judged[lane]["lag4"] for lane in noise if judged[lane]["lag4"] is not None]
            return "noise", (f"{', '.join(noise)} keep no shape from bar to bar"
                             + (f" (lag 4 {np.mean(lag4):+.2f} over the baseline)" if lag4 else ""))
        rep1, rep4, distinct = mix[0] or 0.0, mix[1] or 0.0, mix[2]
        tune = [lane for lane in judged if kind_of(lane) != "drum"]
        if rep1 >= LOOP_REPEAT or rep4 >= LOOP_REPEAT or distinct is not None and distinct <= LOOP_DISTINCT:
            return "looping", (f"the whole bar comes round again: {max(rep1, rep4):.0%} of bars the same as "
                               f"{'1' if rep1 >= rep4 else '4'} back" + (f" ({', '.join(loop)} each a loop)" if loop else ""))
        if tune and all(judged[lane]["v"] == "looping" for lane in tune):
            rep = max(max(judged[lane]["rep1"] or 0, judged[lane]["rep4"] or 0) for lane in loop)
            return "looping", f"{', '.join(loop)} repeat exactly ({rep:.0%} of bars the same as 1 or 4 back)"
        lag = [m["lag4"] for lane, m in judged.items() if m["lag4"] is not None and kind_of(lane) == "layer"]
        return "healthy", ("bars change and come back" + (f" (lag 4 {np.mean(lag):+.2f} over the baseline)" if lag else "")
                           + (f"; {noise[0]} past the lip" if noise else "")
                           + (f"; {', '.join(loop)} looping" if loop else ""))

    def compact(self):
        """The report cut down (see `compact`)."""
        return compact(self.report())

    def says(self, pause=None):
        """One short line when the overall verdict has changed and held for `hold` bars (or every `say_every` bars);
        "" otherwise. A quiet stretch is not announced."""
        r = self.report(pause)
        if r["bar"] is None:
            return ""
        if r["bar"] != self._seen:
            self._seen = r["bar"]
            self._recent.append(r["verdict"])
        v = r["verdict"]
        due = self.say_every and self._said_at is not None and r["bar"] - self._said_at >= self.say_every
        steady = len(self._recent) == self._recent.maxlen and all(x == v for x in self._recent)
        if v == "quiet" or not (steady and v != self._said or due):
            return ""
        again = self._said is not None and self._said != "healthy" and v == "healthy"
        self._said, self._said_at = v, r["bar"]
        words = {"looping": "going round in a loop", "noise": "drifting into noise",
                 "healthy": "healthy again" if again else "healthy"}[v]
        return f"watch: {words} - {r['why']}"
