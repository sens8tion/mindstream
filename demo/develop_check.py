"""Offline checks of development (mindstream/develop.py) and the edge (mindstream/edge.py) against docs/research/README.md,
build steps 4 and 5. Plans only: nothing is played, nothing running is touched, no numpy.

    python -B demo/develop_check.py            (from the repo root)

Development, over many seeds and 128 bars or more:
- one kept change of the riff on every eight-bar line, and none off it, with a roller of 8 or more [05 12.7];
- the run-end fates drawn near the measured shares: back after a hole 0.36, partial rewrite 0.21, new 0.39,
  transposition 0.03, the rest 0.01 [05 12.7, R-bass 11.2];
- at most one lane changing on a bar, the section turnovers (riff and drums together) apart; the rare others counted;
- the B riff at 32 with the drums turning over on the same bar, and A back, changed, at 64 after a bar or two with no
  low end: "after 64 bars something heard earlier has come back changed" [05 12.10];
- every change on a four-bar line (the riff's holes apart, which sit at the end of a group);
- the same arguments always the same answer; a roller changed live, or a layer added later, never rewrites the past.

The edge, over random sweeps of both dials and of the lips:
- never two dials past their lips; past only on the third and fourth bar of a four-bar group, at most two bars, back
  on the four-bar line; only after DWELL bars held, two bars only after EARNED; one lane, never the low end;
- at REFERENCE the engine is untouched (every multiplier 1, every offset 0, a chop preset unchanged);
- the control (what the mixer would keep) takes the messages the viewer passes on.
"""
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from mindstream import chopper, develop, edge  # noqa: E402

LANES = ("sub", "drums", "hook", "chop", "rain", "film3", "voice")
SEEDS = range(200)
BARS = 256
ROWS = []


def row(what, got, want, ok):
    ROWS.append((what, got, want, bool(ok)))


def timeline(seed=7, bars=72):
    """One seed's first bars, a line per bar where something happens: what each lane does."""
    short = {"start": ".", "mutate": "mut", "hole": "hole", "back": "back", "rewrite": "REWR", "new": "NEW", "transpose": "trans",
             "rhythm": "rhy", "B": "B", "A_changed": "A'"}
    print(f"seed {seed}, roller {develop.DEFAULT_ROLLER}: what each lane does, on the bars where any does something")
    print("  bar  " + "".join(f"{name:<12}" for name in LANES))
    for b in range(1, bars):
        st = develop.state(seed, b, LANES)
        if any(i["fate"] != "hold" for i in st.values()):
            cells = []
            for name in LANES:
                i = st[name]
                if i["fate"] == "hold":
                    cells.append("")
                else:
                    word = short.get(i["fate"], i["fate"]) + (f" {i['aspect'][:4]}" if i["aspect"] else f" v{i['version']}.{i['generation']}")
                    cells.append(word)
            print(f"  {b:>3}  " + "".join(f"{c:<12}" for c in cells))
    print()


def development():
    # one kept change per eight bars, and none off the eight-bar lines (rollers 8 to 32)
    windows, good = 0, 0
    for roller in (8, 16, 32):
        for seed in SEEDS:
            d = develop.Development(seed, LANES, roller)
            for start in range(0, BARS, 8):
                changes = [b for b in range(start + 1, start + 9) if d.state(b)["sub"]["fate"] in develop.MATERIAL]
                windows += 1
                good += changes == [start + 8]
    row("riff: kept changes per eight bars (rollers 8, 16, 32)", f"{good}/{windows} windows exactly one, on the line", "all", good == windows)

    # the fates drawn at the end of a run
    drawn = Counter()
    for seed in range(600):
        for b, lane, info in develop.events(seed, 1, BARS, ("sub",), 8):
            if info["drawn"]:
                drawn[info["drawn"]] += 1
    total = sum(drawn.values())
    for fate, share in develop.FATES:
        got = drawn[fate] / total
        row(f"riff fate '{fate}' share ({total} runs)", f"{got:.3f}", f"{share:.2f}", abs(got - share) <= max(0.03, share * 0.25))

    # one lane changing at a time
    for rollers, label, most in (((8, 16, 32), "rollers 8-32", 0.01), ((2, 4), "rollers 2-4 (switch-up)", 0.06)):
        bars_changing, section, other = 0, 0, 0
        for roller in rollers:
            for seed in range(60):
                d = develop.Development(seed, LANES, roller)
                for b in range(1, BARS):
                    moving = [name for name, i in d.state(b).items() if i["changing"]]
                    bars_changing += bool(moving)
                    if len(moving) > 1:
                        if set(moving) <= {"sub", "drums"} and all(d.state(b)[n]["section"] for n in moving):
                            section += 1
                        else:
                            other += 1
        row(f"bars with two lanes changing, {label}: section turnovers / others",
            f"{section} / {other} of {bars_changing}", f"others <= {most:.0%}", other <= most * bars_changing)

    # B at 32 with the drums, A back changed at 64 after the low end has gone
    b_ok = a_ok = hole_ok = hook_ok = back_ok = 0
    count = 0
    for roller in develop.ROLLERS:
        for seed in range(80):
            count += 1
            d = develop.Development(seed, LANES, roller)
            s32, s64, s0 = d.state(32), d.state(64), d.state(0)
            b_ok += s32["sub"]["fate"] == "B" and s32["drums"]["fate"] == "B" and s32["sub"]["family"] == "B"
            a_ok += (s64["sub"]["fate"] == "A_changed" and s64["sub"]["version"] == s0["sub"]["version"]
                     and s64["sub"]["generation"] > 0 and s64["drums"]["fate"] == "A_changed")
            hole_ok += d.state(63)["sub"]["fate"] == "hole" and d.state(61)["sub"]["fate"] != "hole" or roller == 2
            hook = [b for b in range(64, 96) if d.state(b)["hook"]["fate"] == "A_changed"]
            hook_ok += len(hook) == 1 and d.state(hook[0])["hook"]["version"] == s0["hook"]["version"]
            heard = {}                                            # "after 64 bars something heard earlier has come back changed"
            for b in range(0, 64):
                for name, i in d.state(b).items():
                    if i["kind"] in ("riff", "drums", "motif"):
                        heard[(name, i["version"])] = max(heard.get((name, i["version"]), -1), i["generation"])
            back_ok += any((name, i["version"]) in heard and i["generation"] > heard[(name, i["version"])]
                           and i["fate"] in ("A_changed", "B") for b in range(64, 100) for name, i in d.state(b).items())
    row("the B riff at bar 32, the drums turning over with it", f"{b_ok}/{count}", "all", b_ok == count)
    row("riff A back, a later generation, at bar 64 (drums too)", f"{a_ok}/{count}", "all", a_ok == count)
    row("the low end out on bar 63 (and maybe 62) before it", f"{hole_ok}/{count}", "all", hole_ok == count)
    row("hook A back once, after riff A, in the section from 64", f"{hook_ok}/{count}", "all", hook_ok == count)
    row("after 64 bars something heard earlier has come back changed", f"{back_ok}/{count}", "all", back_ok == count)

    # every change on a four-bar line, the riff's holes apart
    off = 0
    for roller in develop.ROLLERS:
        for seed in range(40):
            for b, lane, info in develop.events(seed, 1, BARS, LANES, roller):
                if info["changing"] and b % 4 and not (lane == "sub" and (info["fate"] == "hole" or roller == 2)):
                    off += 1
    row("changes off a four-bar line (riff holes, and switch-up riffs, apart)", off, 0, off == 0)

    # the slice layers: each of the four clocks turns, and the layers share the free lines
    ticks, layers = Counter(), Counter()
    for seed in range(60):
        for b, lane, info in develop.events(seed, 1, 1024, LANES, 16):
            if info["aspect"]:
                ticks[info["aspect"]] += 1
                layers[lane] += 1
    row("slice clocks over 1024 bars, per layer (source/role/odds/processing)",
        "/".join(f"{ticks[a] / 180:.1f}" for a, _ in develop.ASPECTS), "each > 0", all(ticks[a] > 0 for a, _ in develop.ASPECTS))
    rates = [layers[n] / 60 / 8 for n in ("rain", "film3", "voice")]
    row("changes per layer per 128 bars (rain/film3/voice): a fair share of the free lines", "/".join(f"{r:.2f}" for r in rates),
        "> 1, even", min(rates) > 1 and max(rates) <= 1.5 * min(rates))

    # the same arguments, the same answer; nothing rewritten by asking further, by a roller changed live, by a layer added
    same = all(develop.Development(s, LANES).state(b) == develop.state(s, b, LANES) for s in range(10) for b in (0, 31, 64, 200, 1000))
    far, near = develop.Development(3, LANES), develop.Development(3, LANES)
    far.state(3000)
    same = same and all(far.state(b) == near.state(b) for b in range(0, 1500, 7))
    row("the same arguments always give the same answer, however far it was asked", same, True, same)
    live = develop.Development(5, LANES, ((0, 16), (100, 4)))
    still = develop.Development(5, LANES, 16)
    kept = all(live.state(b) == still.state(b) for b in range(0, 100))
    moved = any(live.state(b) != still.state(b) for b in range(100, 300))
    row("a roller changed at bar 100 leaves bars 0-99 alone, and changes what follows", kept and moved, True, kept and moved)
    later = develop.Development(5, LANES + (("pad", "slices", 200),))
    kept = all(later.state(b)[n] == still.state(b)[n] for b in range(0, 200) for n in LANES)
    kept = kept and all(later.state(b)[n] == still.state(b)[n] for b in range(0, 600) for n in ("sub", "drums", "hook"))
    row("a layer added at bar 200 leaves the others' first 200 bars alone (riff, drums, hook: all)", kept, True, kept)


def budget():
    rng = random.Random(1969)
    bars_past, trips, violations, two_bar, lanes, sizes = 0, 0, Counter(), 0, Counter(), []
    for seed in range(120):
        lips = {d: rng.choice((0.5, 0.5, rng.uniform(0.2, 0.9))) for d in edge.DIALS}
        e = edge.Edge(seed, lips)
        want, held_from, last_past, run = {d: rng.random() for d in edge.DIALS}, 0, None, 0
        for b in range(2000):
            if rng.random() < 0.08:                               # jumps and walks, across the lips and back
                want[rng.choice(edge.DIALS)] = rng.random()
            for d in edge.DIALS:
                want[d] = min(max(want[d] + rng.uniform(-0.06, 0.06), 0.0), 1.0)
            if rng.random() < 0.01:
                e.set_lip(rng.choice(edge.DIALS), rng.uniform(0.2, 0.9))
            r = e.step(b, want)
            over = r["over"] or r["base"]
            beyond = [d for d in edge.DIALS if over[d] > r["lips"][d] + 1e-9]
            if any(r["base"][d] > r["lips"][d] + 1e-9 for d in edge.DIALS):
                violations["base past a lip"] += 1
            if len(beyond) > 1:
                violations["two dials past"] += 1
            if beyond != ([r["past"]] if r["past"] else []):
                violations["past misreported"] += 1
            if r["past"]:
                bars_past += 1
                run += 1
                if b % 4 not in (2, 3):
                    violations["past on bar 1 or 2 of a group"] += 1
                if r["lane"] not in edge.LANES:
                    violations["a lane it may not go to"] += 1
                if run == 1:
                    trips += 1
                    lanes[r["lane"]] += 1
                    sizes.append(r["size"])
                    if r["calm"] < e.dwell:
                        violations["too soon after the last"] += 1
                    if r["left"] == 2:
                        two_bar += 1
                        if r["calm"] < e.earned:
                            violations["two bars, not earned"] += 1
                    if r["size"] > min(1.0, r["calm"] / e.earned) + 1e-9:
                        violations["more than earned"] += 1
                if run > 2:
                    violations["past more than two bars"] += 1
            else:
                run = 0
            if r["excursion"] is not None and r["past"] is None:
                violations["an excursion with nothing past"] += 1
    row("edge: bars past a lip / excursions / of two bars", f"{bars_past} / {trips} / {two_bar}", "> 0 each", bars_past and trips and two_bar)
    row("edge: lanes taken (never the low end)", dict(lanes), "drums, chops", set(lanes) <= set(edge.LANES) and len(lanes) == 2)
    row("edge: budget broken, over 120 sweeps of 2000 bars", dict(violations) or 0, 0, not violations)

    p = edge.params()
    ident = all(v == (1.0 if how == "mul" else 0.0) for dial, group, name, how, *_ in edge._TABLE for v in [p[group][name]])
    same_presets = all(edge.chop_preset(chopper.PRESETS[s], p) == chopper.PRESETS[s] for s in chopper.STYLES)
    row("edge: at the reference nothing is changed (params, deal numbers, every chop preset)", ident and same_presets, True,
        ident and same_presets and edge.deal_numbers(p)["RETURNS"] == 0.5)
    lo, hi = edge.params(0, 0), edge.params(1, 1)
    order = lo["drums"]["returns"] > 1 > hi["drums"]["returns"] and lo["chop"]["true"] > 1 > hi["chop"]["true"] and edge.roller(16, lo) == 32 and edge.roller(16, hi) == 4
    row("edge: locked holds and returns more, restless less; composed keeps order, deranged scrambles", order, True, order)

    # the same dials, the same budget
    a, b = edge.Edge(4), edge.Edge(4)
    seq = [{"lock": random.Random(i).random(), "derange": random.Random(-i).random()} for i in range(300)]
    same = [a.step(i, s) for i, s in enumerate(seq)] == [b.step(i, s) for i, s in enumerate(seq)]
    row("edge: the same dials give the same budget", same, True, same)

    # the control, as the mixer would keep it
    c = edge.EdgeControl(9)
    first = c.step(0)
    said = c.take({"lock": 0.7}, 1)
    took = (not c.auto and c.wanted["lock"] == 0.7 and "lock 0.70" in said
            and c.take({"derange": 0.9}, 2, session=True) == "" and c.wanted["derange"] != 0.9
            and "lip" in c.take({"lip": {"lock": 0.6}}) and c.budget.lips["lock"] == 0.6
            and "the session's" in c.take({"auto": True}) and c.auto and c.take({"derange": 0.2}, 3, session=True) == "derange 0.20"
            and c.current()["derange"] == 0.2 and "8 bars" in c.take_roller(8) and c.take_roller(99) and c.roller == 32)
    c2 = edge.EdgeControl(11)
    trips2 = sum(bool(c2.step(b)["past"]) for b in range(512))
    stands = c2.stands()
    took = took and first["past"] is None and trips2 > 0 and set(stands) >= {"lock", "derange", "auto", "lips", "past", "lane", "left"}
    c3 = edge.EdgeControl(1)
    c3.take({"lock": 0.0}, 0)
    for bar in range(5):
        c3.step(bar)
    took = took and c3.schedule()[-1] == (1, 32) and develop.state(1, 10, roller=c3.schedule())["sub"]["fate"] == "hold"
    row("edge control: hand, session, auto, lips, roller; autopilot moves past the lips in 512 bars", f"{trips2} bars past", "> 0", took)


if __name__ == "__main__":
    timeline()
    development()
    budget()
    wide = max(len(r[0]) for r in ROWS)
    print(f"{'check':<{wide}}  {'got':<34} {'want':<14} ok")
    for what, got, want, ok in ROWS:
        print(f"{what:<{wide}}  {str(got):<34} {str(want):<14} {'ok' if ok else 'FAIL'}")
    failed = [r for r in ROWS if not r[3]]
    print("\nALL OK" if not failed else f"\n{len(failed)} FAILED")
    sys.exit(1 if failed else 0)
