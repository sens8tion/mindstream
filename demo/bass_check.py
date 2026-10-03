"""Offline checks of the written bass (mindstream/bassline.py) and its hook (mindstream/motif.py) against the numbers
in docs/research/README.md, build steps 2 and 3, and 05_bass_sub_tune_progression.md section 12.10. Plans only:
nothing is played, nothing is made into sound, nothing running is touched, and numpy is not needed.

    python -B demo/bass_check.py            (from the repo root)

Riffs are made for many seeds in four modes and three relations to the kick, and planned over 64 bars, both held
(version 0) and developing (one kept mutation every eight bars). Then:

- agreement of the bar with the bar 1, 2 and 4 later (the share of (sixteenth, pitch) onsets the two have in
  common): at 2 and 4 over a half, at 1 low, as the reference riff agrees with itself at 2, 4 or 8 bars;
- in the statement and answer pair, the answer lower about two times in three;
- onsets on the sixteenth after the first snare (step 6 counted from 1) under 4%, and more than half of all onsets on
  the eighths the reference prefers (steps 1, 3, 5, 7, 11, 13 counted from 1);
- every colour note followed within four sixteenths by the note it leans on; slides only on moves of two semitones
  or less; nothing sounding through a snare it did not start on;
- the fourth bar of each four the thinnest; the turnarounds in about the measured shares;
- hook onsets on the bass's (sub and saw) onsets less often than chance would put them for the same densities;
- hooks in bars 4, 5 and 8 of the eight; the motif's distinctive interval in every statement and answer;
- the same numbers making the same riff, bars, motif and plan; and how long a bar takes to make.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from mindstream import bassline, motif          # noqa: E402

MODES = {"minor": (0, 2, 3, 5, 7, 8, 10), "dorian": (0, 2, 3, 5, 7, 9, 10), "phrygian": (0, 1, 3, 5, 7, 8, 10), "major": (0, 2, 4, 5, 7, 9, 11)}
KICKS = {"lock": (0, 10), "answer": (0, 10), "free": (0, 3, 10)}
SEEDS = range(60)
BARS = 64
rows, failed = [], []


def row(name, value, target, ok):
    rows.append((name, value, target, "ok" if ok else "FAIL"))
    if not ok:
        failed.append(name)


def agree(a, b):
    a, b = {(e[0], e[1]) for e in a}, {(e[0], e[1]) for e in b}
    if not a and not b:
        return 1.0
    return 2.0 * len(a & b) / (len(a) + len(b))


def riffs():
    for seed in SEEDS:
        for mode, scale in MODES.items():
            for relation, kicks in KICKS.items():
                yield seed, mode, scale, relation, kicks


def plan(r, developing=False, seed=0, key=None, scale=None, relation=None, kicks=()):
    """64 bars of a riff, held or with one kept mutation every eight bars (each bar knowing the one really before)."""
    out = []
    for n in range(BARS):
        rr = bassline.riff(seed, key, scale, n // 8, relation, kicks) if developing else r
        out.append(bassline.bar(rr, n, before=out[-1] if out and developing else None, kinds=True))
    return out


t0 = time.perf_counter()
lags = {1: [], 2: [], 4: []}
lags_dev = {1: [], 2: [], 4: []}
onsets = step6 = good_eighths = 0
colours = resolved = 0
slides = bad_slides = 0
through = 0
by_pos = [[] for _ in range(4)]
lower_cycles = lower_n = 0
turns = {}
riff_lower = 0
plans = {}
for seed, mode, scale, relation, kicks in riffs():
    r = bassline.riff(seed, "a", scale, 0, relation, kicks)
    riff_lower += r["lower"]
    bars = plan(r)
    plans[(seed, mode, relation)] = (r, bars)
    for k in lags:
        lags[k] += [agree(bars[n], bars[n + k]) for n in range(BARS - k)]
    if seed < 20:
        dev = plan(None, True, seed, "a", scale, relation, kicks)
        for k in lags_dev:
            lags_dev[k] += [agree(dev[n], dev[n + k]) for n in range(BARS - k)]
    for n, events in enumerate(bars):
        by_pos[n % 4].append(len(events))
        if n % 8 == 7:
            kinds = {e[5] for e in events}
            name = "hole" if not events else "low" if kinds == {"turn"} else "lift" if "lift" in kinds else "pickup"
            turns[name] = turns.get(name, 0) + 1
        for i, (step, semis, length, slide, accent, kind) in enumerate(events):
            onsets += 1
            step6 += step == 5
            good_eighths += step in (0, 2, 4, 6, 10, 12)
            if slide is not None:
                slides += 1
                bad_slides += abs(semis - slide) > 2
            for snare in (4, 12):
                if step < snare < step + length and not (kind == "A" and step == 0 and r["density"] == "deep"):
                    through += 1
            if kind == "colour":
                colours += 1
                to = bassline.COLOURS[r["colour"]][1]
                if i + 1 < len(events):
                    nxt = events[i + 1]
                    resolved += nxt[0] - step <= 4 and nxt[1] == to
                elif n + 1 < BARS and bars[n + 1]:
                    nxt = bars[n + 1][0]
                    resolved += nxt[0] + 16 - step <= 4 and nxt[1] == to
                else:
                    resolved += 1                      # the last bar planned: its next bar was not made
    for front, back in ((0, 1), (8, 9), (16, 17), (24, 25)):
        a, b = bars[front], bars[back]
        if a and b:
            lower_n += 1
            lower_cycles += sum(e[1] for e in b) / len(b) < sum(e[1] for e in a) / len(a) - 0.5
planned = time.perf_counter() - t0
count = len(plans)

mean = lambda xs: sum(xs) / max(len(xs), 1)       # noqa: E731
l1, l2, l4 = (mean(lags[k]) for k in (1, 2, 4))
row("bass agreement, lag 1 (held riff)", f"{l1:.2f}", "low: under lag 2 and 4", l1 < min(l2, l4) - 0.05)
row("bass agreement, lag 2", f"{l2:.2f}", "> 0.50", l2 > 0.5)
row("bass agreement, lag 4", f"{l4:.2f}", "> 0.50", l4 > 0.5)
d1, d2, d4 = (mean(lags_dev[k]) for k in (1, 2, 4))
row("  the same, mutating every 8 bars (1 / 2 / 4)", f"{d1:.2f} / {d2:.2f} / {d4:.2f}", "2 and 4 > 0.50, 1 lower", d2 > 0.5 and d4 > 0.5 and d1 < min(d2, d4))
row("answer bar lower than its statement", f"{lower_cycles / max(lower_n, 1):.2f}", "about 0.66 (0.5 to 0.8)", 0.5 <= lower_cycles / max(lower_n, 1) <= 0.8)
row("onsets on step 6 (from 1): after the snare", f"{100 * step6 / onsets:.2f}%", "< 4%", step6 / onsets < 0.04)
row("onsets on steps 1, 3, 5, 7, 11, 13 (from 1)", f"{100 * good_eighths / onsets:.0f}%", "> 50%", good_eighths / onsets > 0.5)
row("colour notes resolved within a beat", f"{resolved} of {colours}", "all, and some", colours > 0 and resolved == colours)
row("slides on moves of 2 semitones or less", f"{slides - bad_slides} of {slides}", "all", bad_slides == 0 and slides > 0)
row("notes sounding through a snare", str(through), "0", through == 0)
thin = [mean(x) for x in by_pos]
row("onsets in bars 1 to 4 of each four", " / ".join(f"{x:.2f}" for x in thin), "bar 4 the thinnest", thin[3] == min(thin))
total = sum(turns.values())
row("turnarounds: low / hole / pickup / lift", " / ".join(f"{turns.get(k, 0) / total:.2f}" for k in ("low", "hole", "pickup", "lift")),
    "about 0.4 / 0.2 / 0.3 / 0.1 (lift every other)", abs(turns.get("low", 0) / total - 0.4) < 0.1 and turns.get("hole", 0) / total < 0.3)
row("riffs whose answer is lowered", f"{riff_lower / count:.2f}", "about 0.67", 0.55 <= riff_lower / count <= 0.8)

# the B riff and the mutations
r0 = plans[(0, "minor", "lock")][0]
b = bassline.relative(r0, 1)
row("B riff: opposite density, same home, other anchor", f"{r0['density']}->{b['density']}, {r0['b_step']}->{b['b_step']}",
    "all three", b["density"] != r0["density"] and b["home"] == r0["home"] and b["b_step"] != r0["b_step"])
kinds_ok = all(bassline.mutate(r0, how, 3) == bassline.mutate(r0, how, 3) and bassline.mutate(r0, how, 3) != r0 for how in ("kept", "rewrite", "new"))
row("mutate: kept, rewrite and new, each deterministic", "yes" if kinds_ok else "no", "yes", kinds_ok)
# every `how` develop.py can give, as develop.py lists them (and the fates it gives them with)
from mindstream import develop          # noqa: E402
dev_hows = sorted({h for name in ("MUTATIONS", "KEEPS", "RETURNS_HOW", "TRANSPOSES", "DRUM_HOW", "DRUM_RETURNS", "HOOK_KEEPS")
                   for h in getattr(develop, name)} | {"half_cell_half_skeleton", "same_notes_new_rhythm", "opposite_density", "kick_and_carrier"})
taken, bad, sane = 0, [], True
for how in dev_hows + [None]:
    for fate in (None,) + tuple(f for f in develop.FATE_NAMES):
        try:
            a, b2 = bassline.mutate(r0, how, 11, fate), bassline.mutate(r0, how, 11, fate)
            ma, mb = motif.mutate(motif.motif(1, MODES["minor"], motif.pitch_set(MODES["minor"], r0["home"])), how, 11, fate), \
                motif.mutate(motif.motif(1, MODES["minor"], motif.pitch_set(MODES["minor"], r0["home"])), how, 11, fate)
        except Exception as error:      # noqa: BLE001
            bad.append(f"{how}/{fate}: {error}")
            continue
        taken += a == b2 and ma == mb
        for n in range(16):
            for step, semis, length, slide, accent in bassline.bar(a, n):
                sane = sane and step != 5 and -12 <= semis <= 14 and 0 <= accent <= 1 and length >= 1
        sane = sane and motif._good([p for _, p, _ in ma["notes"]], ma["leap"])
row("mutate takes every develop how (riff and hook)", f"{len(dev_hows) + 1} hows x {len(develop.FATE_NAMES) + 1} fates, {len(bad)} refused",
    "all, deterministic, rules kept", not bad and taken == (len(dev_hows) + 1) * (len(develop.FATE_NAMES) + 1) and sane)
if bad:
    print("refused:", bad[:5])
moved = bassline.mutate(r0, "up_fourth", 1)
row("transposed riff: every note moved", f"{moved.get('transpose')} semis", "+5",
    moved.get("transpose") == 5 and [e[1] - 5 for e in bassline.bar(moved, 0)] == [e[1] for e in bassline.bar(r0, 0)])
versions = [bassline.riff(5, "a", MODES["minor"], v) for v in (0, 1, {"side": "B"}, {"riff": 1}, {"partial": 1, "gen": 2})]
row("versions give different riffs", str(len({repr(v["decor"]) + repr(v["b_step"]) + repr(v["history"]) for v in versions})), "5", len({repr(v) for v in versions}) == 5)

# the hook
hook_bars, in_slots, coincide, expected, leaps_ok, leaps_n = 0, 0, 0, 0.0, 0, 0
for (seed, mode, relation), (r, bars) in plans.items():
    scale = MODES[mode]
    saws = [bassline.answer(r, n, bars[n]) for n in range(BARS)]
    pitches = motif.pitch_set(scale, bassline.home(r))
    for group in range(BARS // 8):
        m = motif.motif(seed, scale, pitches, {"motif": group // 4, "gen": (group % 4) // 2})
        st, an = motif.statement(m), motif.answer(m)
        for shape in (st, an, motif.fragment(m, 0)):
            leaps_n += 1
            leaps_ok += any(abs(b[1] - a[1]) == m["leap"] for a, b in zip(shape, shape[1:]))
        low = {pos: [(e[0], e[2]) for e in bars[group * 8 + pos]] + [(e[0], e[2]) for e in saws[group * 8 + pos]] for pos in range(8)}
        for pos, notes in motif.block(m, group * 8, low).items():
            hook_bars += 1
            in_slots += pos in (3, 4, 7)
            starts = {s for s, _ in low[pos]}
            coincide += sum(s in starts for s, _, _ in notes)
            expected += len(notes) * len(starts) / 16.0
row("hook bars in bars 4, 5 and 8 of eight", f"{in_slots} of {hook_bars}", "mostly (> 80%)", in_slots / hook_bars > 0.8)
row("hook onsets on bass onsets / chance", f"{coincide} / {expected:.0f}", "fewer than chance", coincide < expected)
row("distinctive interval in statement, answer, fragment", f"{leaps_ok} of {leaps_n}", "all", leaps_ok == leaps_n)
pset = {m: motif.pitch_set(s, ()) for m, s in MODES.items()}
row("hook pitch set (minor)", " ".join(str(p) for p in pset["minor"]), "1 b3 4 5 b7: 0 3 5 7 10", pset["minor"] == (0, 3, 5, 7, 10))
opened = all(motif.statement(motif.motif(s, MODES["minor"], pset["minor"]))[-1][1] % 12 != 0 for s in range(200))
closed = all(motif.answer(motif.motif(s, MODES["minor"], pset["minor"]))[-1][1] % 12 in (0, 7) for s in range(200))
row("statements end open, answers end on 1 or 5", f"{opened} / {closed}", "True / True", opened and closed)
m0 = motif.motif(7, MODES["dorian"], pset["dorian"])
rel = motif.relative(m0, 1)
row("relative keeps the leap and is another shape", f"{m0['leap']} -> {rel['leap']}", "same leap, other notes", rel["leap"] == m0["leap"] and rel["notes"] != m0["notes"])
mm = all(motif.mutate(m0, how, 2) == motif.mutate(m0, how, 2) for how in ("kept", "rewrite", "new"))
row("motif mutate: kept, rewrite and new, deterministic", "yes" if mm else "no", "yes", mm)

# the same numbers, the same music
again = bassline.riff(0, "a", MODES["minor"], 0, "lock", KICKS["lock"])
same = again == r0 and [bassline.bar(again, n, kinds=True) for n in range(BARS)] == plans[(0, "minor", "lock")][1]
same = same and motif.motif(3, MODES["minor"], pset["minor"], 2) == motif.motif(3, MODES["minor"], pset["minor"], 2)
same = same and motif.block(m0, 8, {3: [(8, 2)]}) == motif.block(m0, 8, {3: [(8, 2)]})
row("deterministic", "yes" if same else "no", "yes", same)
t1 = time.perf_counter()
for n in range(200):
    bassline.bar(bassline.riff(n, "a", MODES["minor"], {"side": "B", "gen": 3}, "lock", (0, 10)), n)
per = (time.perf_counter() - t1) / 200 * 1000
row("a riff (B, 3 generations) and a bar, made", f"{per:.2f} ms", "< 2 ms", per < 2.0)

width = max(len(r[0]) for r in rows)
print(f"{count} riffs x {BARS} bars planned in {planned:.1f} s\n")
print(f"{'check':{width}}  {'measured':28}  {'wanted':34}  ")
for name, value, target, mark in rows:
    print(f"{name:{width}}  {value:28}  {target:34}  {mark}")
print()
print("ALL OK" if not failed else f"{len(failed)} FAILED: " + "; ".join(failed))
sys.exit(1 if failed else 0)
