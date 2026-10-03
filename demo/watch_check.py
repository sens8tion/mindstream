"""Offline checks of the self-measurement (mindstream/watch.py, docs/research/README.md build step 6). Nothing is
played and nothing running is touched.

    python -B demo/watch_check.py            (from the repo root; needs numpy)

Three made-up sessions are fed to `Watch` a bar at a time:
- a literal four-bar loop (every lane the same four bars over and over): it must say "looping";
- uniform random onsets in every lane (random pitches and slices): it must say "noise";
- a plan from the real chop engine (chopper.plan over 96 bars against the held drums, as demo/chop_check.py makes
  them: an Amen-like break as the anchor and a voice as the hook layer), the drums themselves, a written sub riff (two
  anchors, bar 2 derived from bar 1, a thin fourth bar, a colour note that resolves, a B riff at 32 and A back,
  changed, at 64) and a hook in the sub's gaps: it must say "healthy", and pass the README's checks.
The edge check is judged from the edge's own state (edge.EdgeControl, on its autopilot): passed with one dial past at
a time, failed when two are, skipped with no edge. The compact report (for stands()) is checked for its shape.

Then the mixer itself, offline (`Mixer(open_stream=False)` and `fill`), with two sample layers brought in, for 72
bars, paced at four times the speed it would be heard at: the watch is fed from its own thread (never the one
calling fill), the compact report is in `stands()`, the edge is judged when the mixer has one (`mixer.edge`), the
fill blocks made while the watch works are no slower than those made while it does not by more than about 0.3 ms
(worst of each three-bar stretch, median, and p99; compared inside each run, the watch's work let through in
alternate stretches, since whole runs swing by milliseconds with the machine's load), and hardly a block (1% at most)
is made while a piece of the watch's work is being done.
"""
import bisect
import os
import sys
import threading
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import chop_check as cc                                  # noqa: E402  (the sounds and the drums the chop checks use)
from mindstream import chop, chopper, watch              # noqa: E402
from mindstream.watch import Watch                       # noqa: E402

BARS = 96
ROUNDS = 3               # mixer runs with the watch off, and on, taken in turn
AB = 48                  # sixteenths in each stretch of the in-run comparison (three bars: across the planner's four)
PACE = 4                 # how many times faster than it would be heard the mixer is run
rows, failures = [], []


def check(name, value, target, ok):
    rows.append((name, value, target, "ok" if ok else "OUT"))
    if not ok:
        failures.append(name)


def info(name, value, target=""):
    rows.append((name, value, target, "info"))


# ---- the sessions ---------------------------------------------------------------------------------------------

def layer_lane(cuts, events, bar):
    return [(s, e["slice"], cuts[e["slice"]]["kind"]) for s, e in enumerate(events[16 * bar:16 * bar + 16]) if isinstance(e, dict)]


def sub_riff(bar, rng):
    """A written sub: anchors on step 1 and 7 (1-based), decorations re-dealt every bar from the ruled moves, bar 2
    the statement with its second anchor a step lower, bar 4 thin (one low note and a gap), now and then a colour
    note (b2) on step 15 resolving to the root on the next one. A B riff from bar 32; A back, changed, from 64."""
    riff = "B" if 32 <= bar < 64 else "A"
    first, second = (0, 7) if riff == "A" else (5, 0)
    at2 = 6 if riff == "A" else 10
    if bar >= 64:                                       # A again, changed: its second anchor moved and a fifth higher
        at2, second = 8, 7
    k = bar % 4
    if k == 3:
        return [(0, first - 12)] + ([(14, 1)] if rng.random() < 0.5 else [])
    notes = [(0, first), (at2, second if k != 1 else second - 2)]
    for s in rng.choice([2, 3, 10, 11, 12, 14], size=rng.integers(1, 3), replace=False):
        if s != at2:
            notes.append((int(s), first if rng.random() < 0.6 else 7))
    if k == 2 and rng.random() < 0.3:
        notes = [n for n in notes if n[0] != 14] + [(14, 1)]
    return sorted(notes)


def hook(bar, low_steps):
    """A hook in bars 4, 5 and 8 of eight (1-based), late in the bar and off the sub's onsets: stated, answered with
    its end changed, then a fragment; each eight bars a relative of the last (transposed, moved a step)."""
    block, k = bar // 8, bar % 8
    if k not in (3, 4, 7):
        return []
    shift, move = (0, 3, 7, 5)[block % 4], block % 3
    shape = [(8 + move, 0), (11 + move % 2, 3), (13, 7)]
    if k == 7:
        shape = shape[:2]
    elif k == 4:
        shape = shape[:2] + [(15, 5)]
    return [(s, p + shift) for s, p in shape if s not in low_steps]


SOUNDS = {}


def sounds():
    if not SOUNDS:
        brk, starts, _ = cc.make_break()
        SOUNDS["amen"] = chopper.classify(chop.measure(brk, cc.RATE, starts), cc.SLOT)
        voice_mono, vstarts = cc.make_voice()
        SOUNDS["voice"] = chopper.classify(chop.measure(voice_mono, cc.RATE, vstarts), cc.SLOT)
    return SOUNDS["amen"], SOUNDS["voice"]


def healthy_session(seed="amen"):
    """The chop engine's anchor (seeded `seed`) and hook layers, the held drums with their fills, the sub, the hook.
    Returns the bars as `Watch.add_bar` takes them, and the anchor's events (for chop_check's own measures)."""
    amen, voice = sounds()
    anchor = cc.run(amen, "anchor", "jungle", seed, bars=BARS)
    taken = lambda bar: chopper.cells(anchor[16 * bar:16 * bar + 64])
    talk = cc.run(voice, "hook", "jungle", "talk", taken_of=taken, bars=BARS)
    rng = np.random.default_rng(166)
    out = []
    for bar in range(BARS):
        drums = cc.drums_for(bar - bar % 4)[bar % 4]          # the group's bars as dealt, the fill in its last
        sub = sub_riff(bar, rng)
        out.append({"kick": list(drums["kick"]), "snare": list(drums["snare"]), "sub": sub,
                    "tune": hook(bar, {s for s, _ in sub}),
                    "amen": layer_lane(amen, anchor, bar), "talk": layer_lane(voice, talk, bar)})
    return out, anchor


def loop_session(healthy):
    return [healthy[bar % 4] for bar in range(64)]


def noise_session():
    rng = np.random.default_rng(7)
    out = []
    for _ in range(64):
        bar = {}
        for lane in ("kick", "snare", "sub", "tune", "amen", "talk"):
            steps = [s for s in range(16) if rng.random() < 0.3]
            bar[lane] = [(s, int(rng.integers(0, 12)) if lane in ("sub", "tune") else int(rng.integers(0, 12)) if lane in ("amen", "talk") else None)
                         for s in steps]
        out.append(bar)
    return out


def feed(session):
    w = Watch()
    said = []
    for bar, lanes in enumerate(session):
        w.add_bar(bar, lanes)
        line = w.says()
        if line:
            said.append((bar, line))
    return w.report(), said


def lane_table(r):
    for lane, m in r["lanes"].items():
        extra = ""
        if "agree2" in m:
            extra = f" agree 1/2/4 {m['agree1']}/{m['agree2']}/{m['agree4']} step6 {m['step6']} colour {m['colour']}"
        if "coincide" in m:
            extra = f" coincide {m['coincide']}"
        info(f"  {lane}", f"{m['v']}: bars {m['bars']} lag1 {m['lag1']} lag4 {m['lag4']} rep {m['rep1']}/{m['rep4']} "
             f"distinct {m['distinct']} change {m['change']}{extra}")


# ---- the mixer, offline ------------------------------------------------------------------------------------------

def mixer_run(bars, watching, with_edge=False, ab=False):
    """`ab`: the watch works only in alternate stretches of AB sixteenths (see main). Returns the mixer, the fill
    blocks [(start, end)], which stretch each was made in (0 the watch working, 1 not), the pieces of the watch's
    work [(start, end)], the threads add_bar was called on, and what was logged."""
    from mindstream import mixer as mixmod
    from mindstream.mixer import Mixer
    rate, bpm = 44100, 170.0
    six = 15.0 * rate / bpm
    rng = np.random.default_rng(3)

    def pcm(x):
        x = np.clip(x, -1, 1)
        return (np.stack([x, x], axis=1) * 32767).astype("<i2").tobytes()

    n = int(six * 32)
    brk = np.zeros(n, np.float32)
    t = np.arange(int(0.18 * rate)) / rate
    kick = np.sin(2 * np.pi * (50 + 120 * np.exp(-t * 30)) * t) * np.exp(-t * 18)
    snare = rng.normal(0, 1, len(t)) * np.exp(-t * 25) * 0.7 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.3
    for b in range(2):
        for s, x in ((0, kick), (2, snare * 0.25), (4, snare), (7, snare * 0.25), (10, kick), (12, snare), (15, snare * 0.25)):
            at = int((b * 16 + s) * six)
            brk[at:at + min(len(x), n - at)] += x[:n - at]
    words = [np.zeros(int(0.12 * rate), np.float32)]
    for i in range(6):
        d = 0.18 + 0.1 * (i % 3)
        tt = np.arange(int(d * rate)) / rate
        f0 = 180 + 30 * (i % 4)
        words += [(sum(np.sin(2 * np.pi * f0 * h * tt) / h for h in range(1, 6)) * np.sin(np.pi * tt / d) ** 0.5 * 0.4).astype(np.float32),
                  np.zeros(int(0.09 * rate), np.float32)]
    was = mixmod.Mixer.WATCH
    mixmod.Mixer.WATCH = watching
    try:
        m = Mixer(bpm=bpm, energy=0.7, open_stream=False, rate=rate, seed=7, compose=False)
    finally:
        mixmod.Mixer.WATCH = was
    logs = []
    m.log = logs.append
    m.groove.scene_set = True
    m.take_sample(pcm(brk * 0.8), rate, 2, "loop", "amen")
    m.take_sample(pcm(np.concatenate(words)), rate, 2, "loop", "talk")
    m.patch([{"part": name, "bring": True} for name in ("amen", "talk")])
    if not with_edge:                               # the mixer's own edge (course.py steps it each bar) hidden from the watch;
        m.edge = None                               # with_edge: the watch judges that real edge, on its autopilot
    callers, real_add, real_work, pieces = set(), Watch.add_bar, Mixer._watch_work, []

    def spy(self, bar, lanes, edge=None):
        callers.add(threading.current_thread().name)
        return real_add(self, bar, lanes, edge)

    def timed_work(self):                       # when each piece of the watch's work was done
        work = real_work(self)
        while True:
            while ab and (self.groove.step // AB) % 2:    # a stretch without the watch's work: it waits
                yield
            t0 = time.perf_counter()
            try:
                next(work)
            except StopIteration:
                pieces.append((t0, time.perf_counter()))
                return
            pieces.append((t0, time.perf_counter()))
            yield
    Watch.add_bar, Mixer._watch_work = spy, timed_work
    # Paced at PACE times the speed it would be heard at: the sound card asks for a block every 23 ms and the block
    # takes well under one, so the rest of the time is the other threads'. Unpaced, every block would be competing
    # with them, which never happens when it plays. One more bar is played at the end, for the watch to finish.
    fills, sides, g, every = [], [], m.groove, 1024 / rate / PACE
    try:
        while g.step < (bars + 1) * 16:
            t0 = time.perf_counter()
            m.fill(1024)
            t1 = time.perf_counter()
            fills.append((t0, t1))
            sides.append((g.step // AB) % 2)
            time.sleep(max(every - (t1 - t0), 0.0))
    finally:
        Watch.add_bar, Mixer._watch_work = real_add, real_work
        m.close()
    return m, fills, sides, pieces, callers, logs


def overlapping(fills, pieces):
    """The blocks that were being made while a piece of the watch's work was being done: [(the block's ms, ms of it
    shared with the watch's work)]."""
    pieces = sorted(pieces)
    starts = [a for a, _ in pieces]
    hit = []
    for a, b in fills:
        k = bisect.bisect_left(starts, b)           # pieces that began before this block ended
        shared = sum(max(0.0, min(b, pe) - max(a, ps)) for ps, pe in pieces[max(0, k - 3):k])
        if shared > 0:
            hit.append(((b - a) * 1000, shared * 1000))
    return hit


ENGINE_CHECKS = ("lag1_at_base", "lag4_above", "few_repeats")     # measures of the chop engine's own output


def main():
    healthy, anchor = healthy_session()
    for name, session, want in (("loop", loop_session(healthy), "looping"), ("noise", noise_session(), "noise"),
                                ("chop engine", healthy, "healthy")):
        r, said = feed(session)
        check(f"{name}: verdict", f"{r['verdict']} ({r['why']})", want, r["verdict"] == want)
        info("  said", "; ".join(f"bar {b}: {line}" for b, line in said) or "(nothing)")
        info("  spine / mix rep1,rep4,distinct / overlap", f"{r['spine']} / {r['mix']} / {r['overlap']}")
        info("  came back / past lip", f"{r['came_back']} / {r['past_lip']}")
        lane_table(r)
        if name == "chop engine":
            for key, ok in r["checks"].items():
                if key in ENGINE_CHECKS:
                    info(f"{name}: check {key}", ok, "(the engine's)")
                elif key == "one_past_lip":
                    check(f"{name}: check {key} (no edge given)", ok, "None", ok is None)
                else:
                    check(f"{name}: check {key}", ok, "True", ok is True)
            check(f"{name}: said once, healthy", f"{len(said)} line(s)", "1", len(said) == 1 and "healthy" in said[0][1])
            # the watch's numbers against chop_check's own, on the same 32 bars of the anchor
            prev, four, _ = cc.repeats(anchor[-32 * 16:])
            m = r["lanes"]["amen"]
            check("chop engine: repeats 1 / 4 back = chop_check's", f"{m['rep1']} / {m['rep4']} vs {prev:.3f} / {four:.3f}", "equal",
                  abs(m["rep1"] - prev) < 1e-3 and abs(m["rep4"] - four) < 1e-3)
        else:
            check(f"{name}: said it, once", f"{len(said)} line(s)", "1", len(said) == 1 and want.split("ing")[0][:4] in said[0][1])
    for seed in cc.SEEDS[1:]:
        r, said = feed(healthy_session(seed)[0])
        check(f"chop engine, seed {seed}: verdict", f"{r['verdict']}; engine checks " + " ".join(
            f"{k}={r['checks'][k]}" for k in ENGINE_CHECKS), "healthy", r["verdict"] == "healthy")

    # the edge: judged from the edge's own state, a bar at a time
    from mindstream.edge import EdgeControl
    ec, w, past = EdgeControl(seed=3), Watch(), set()
    for bar, lanes in enumerate(healthy):
        now = ec.step(bar)
        past.add(now["past"])
        w.add_bar(bar, lanes, ec.stands())
    r = w.report()
    check("edge: the edge's autopilot over 96 bars", f"{r['edge']}; went past {sorted(x for x in past if x)}; one_past_lip {r['checks']['one_past_lip']}",
          "True", r["checks"]["one_past_lip"] is True and any(past - {None}))
    two = {"lips": {"lock": 0.5, "derange": 0.5}, "base": {"lock": 0.5, "derange": 0.5}, "over": {"lock": 0.8, "derange": 0.7}, "past": "lock"}
    w.add_bar(len(healthy), healthy[0], two)
    r = w.report()
    check("edge: two dials past at once", f"{r['edge']}; one_past_lip {r['checks']['one_past_lip']}", "False",
          r["checks"]["one_past_lip"] is False and r["edge"]["now"] == ["derange", "lock"])
    c = w.compact()
    check("compact report", c, "small, the verdicts", set(c) == {"bar", "verdict", "why", "lanes", "failed", "passed", "spine", "lag4",
          "came_back", "past"} and "one_past_lip" in c["failed"] and len(repr(c)) < 600)

    # the time a report takes
    w = Watch()
    for bar, lanes in enumerate(healthy):         # (healthy is the first seed's session)
        w.add_bar(bar, lanes)
    took = []
    for k in range(20):
        w._cache = (None, None)
        t0 = time.perf_counter()
        w.report()
        took.append((time.perf_counter() - t0) * 1000)
    check("time per report (96 bars kept, 6 lanes)", f"{np.median(took):.1f} ms median, {max(took):.1f} worst", "< 30 ms, off the sound's thread", max(took) < 30)

    # ---- the mixer offline ----
    # The worst block of a whole run swings by milliseconds with whatever else the machine is doing (runs with the
    # watch off alone range from 3 to over 20 ms), so the comparison that decides is made inside each run, under the
    # same conditions: with the watch on, its work is let through only in alternate stretches of three bars (three,
    # so that the chop planner's work, a bar before each four-bar group, falls on both sides alike), and the blocks
    # made in the stretches with its work are compared with those made in the stretches without. Whole runs with the
    # watch off and on, taken in turn, are shown as well.
    worst = {True: [], False: []}
    p99 = {True: [], False: []}
    stretch = {0: [], 1: []}                        # the worst block of each stretch: 0 with the watch's work, 1 without
    side_blocks = {0: [], 1: []}
    hits, blocks, pieces_done = [], 0, 0
    for rnd in range(ROUNDS):
        for watching in (False, True):
            m, fills, sides, pieces, callers, logs = mixer_run(72, watching, with_edge=watching and rnd == ROUNDS - 1, ab=watching)
            warm = [(b - a) * 1000 for a, b in fills[40:]]
            worst[watching].append(max(warm))
            p99[watching].append(float(np.percentile(warm, 99)))
            if watching:
                cur, at = [], None
                for ms, sd in zip(warm, sides[40:]):
                    if sd != at and cur:
                        stretch[at].append(max(cur))
                        cur = []
                    at = sd
                    cur.append(ms)
                    side_blocks[sd].append(ms)
                hits += overlapping(fills[40:], pieces)
                blocks += len(fills)
                pieces_done += len(pieces)
            if watching and rnd == ROUNDS - 1:
                fed, first = m.watcher.last, m.watcher.bars[0][0]
                st = m.stands().get("watch")
                check("mixer: the watch is fed every bar", f"bars {first} to {fed}, {len(m.watcher.bars)} kept", "0 to >= 71, all",
                      fed is not None and fed >= 71 and first == 0 and len(m.watcher.bars) == fed + 1)
                check("mixer: add_bar called only off the fill thread", ", ".join(sorted(callers)), "watch",
                      callers == {"watch"})
                check("mixer: compact report in stands()", st, "present",
                      bool(st) and st.get("bar") is not None and st["lanes"].get("amen") is not None)
                full = m.watcher.report()
                info("  mixer report", f"{full['verdict']}: {full['why']}")
                lane_table(full)
                check("mixer: edge judged from mixer.edge.stands()", f"{full['edge']}; one_past_lip {full['checks']['one_past_lip']}",
                      "most <= 1, True", full["edge"] is not None and full["checks"]["one_past_lip"] is True)
                info("  mixer checks", " ".join(f"{k}={v}" for k, v in full["checks"].items()))
                said = [x for x in logs if x.startswith("watch:")]
                check("mixer: said rarely", f"{len(said)} line(s): " + " | ".join(said), "<= 3 in 72 bars", len(said) <= 3)
                check("mixer: no exception in the sound", "none" if not m.failed else "FAILED", "none", not m.failed)
    without, with_ = float(np.median(stretch[1])), float(np.median(stretch[0]))
    check(f"worst block of a stretch, without / with the watch's work (median of {len(stretch[0])})", f"{without:.2f} / {with_:.2f} ms",
          "with <= without + 0.3", with_ <= without + 0.3)
    q_without, q_with = float(np.percentile(side_blocks[1], 99)), float(np.percentile(side_blocks[0], 99))
    check("p99 fill block, without / with the watch's work", f"{q_without:.3f} / {q_with:.3f} ms", "with <= without + 0.3",
          q_with <= q_without + 0.3)
    info("  the worst block of all, without / with", f"{max(stretch[1]):.2f} / {max(stretch[0]):.2f} ms")
    info(f"whole runs: worst fill block, watch off / on (median of {ROUNDS})", f"{np.median(worst[False]):.2f} / {np.median(worst[True]):.2f} ms",
         "(machine noise)")
    info("  worst of each run, off", " ".join(f"{x:.2f}" for x in worst[False]))
    info("  worst of each run, on", " ".join(f"{x:.2f}" for x in worst[True]))
    info("  p99 fill block, off / on (medians)", f"{np.median(p99[False]):.3f} / {np.median(p99[True]):.3f} ms")
    # Blocks made while a piece of the watch's work was being done (from when the piece began to when it ended, so a
    # piece held up by the planner or the sound maker counts too): hardly any.
    worst_hit = max(hits) if hits else (0.0, 0.0)
    most_shared = max(sh for _, sh in hits) if hits else 0.0
    check("blocks made while the watch was working", f"{len(hits)} of {blocks} blocks ({pieces_done} pieces of work)", "<= 1%",
          len(hits) <= 0.01 * blocks)
    info("  the slowest of them / the most time shared", f"{worst_hit[0]:.2f} ms (sharing {worst_hit[1]:.2f}) / {most_shared:.2f} ms")
    pieces = []
    w = Watch()
    for bar, lanes in enumerate(healthy):
        w.add_bar(bar, lanes)
        mark = [time.perf_counter()]

        def pause():
            pieces.append(time.perf_counter() - mark[0])
            mark[0] = time.perf_counter()
        w.report(pause)
        pieces.append(time.perf_counter() - mark[0])
    pieces = np.array(pieces) * 1000
    info("  the watch's work between pauses", f"median {np.median(pieces):.3f}, p99 {np.percentile(pieces, 99):.3f}, worst {pieces.max():.3f} ms")

    width = max(len(r[0]) for r in rows)
    vwidth = min(max(len(str(r[1])) for r in rows), 110)
    for name, value, target, mark in rows:
        print(f"{name:<{width}}  {str(value):<{vwidth}}  {target:<14}  {mark}")
    print()
    print("ALL OK" if not failures else "FAILURES: " + "; ".join(failures))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
