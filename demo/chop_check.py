"""Offline checks of the chop engine (mindstream/chopper.py) against the numbers in docs/research/README.md, build
step 1. Plans only: nothing is played and nothing running is touched.

    python -B demo/chop_check.py            (from the repo root; needs numpy, for making and measuring the sounds)

Three synthetic sounds are made and measured by `chop.measure` as the mixer would: an Amen-like break (kicks, loud
snares, ghosts, a crash and a ride running through, laid out as the Amen's four bars), a voice (syllables of pitched
sound, some with a consonant in front) and a pad (three slow chords). Their slices are classified, given roles, and
planned over 128 bars against held drums from deal.py. Then the plans are measured:

- bar-to-bar similarity (each bar as 16 steps x 3 bands, low = heavy, mid = tone and other, high = sharp and ghost,
  weighted by loudness): lag 1 should sit at the same-section baseline and lag 4 about 0.13 above it, as the
  reference set measured (0.355 / 0.356 / 0.486);
- exact repeats of a bar (same slices on the same steps): near zero, where the old four-bar plan repeated 47 to 55
  bars of every 64;
- the spine: steps 1, 5 and 13 sounding in more than nine bars of ten;
- the rationing per group, the ghosts, the gates, the loudest first downbeat, four different bars;
- layers planned in turn with `taken`: no two sharing more than half their onsets;
- the same arguments giving the same plan, every style and role running, and the time a plan takes.
"""
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from mindstream import chop, chopper, deal          # noqa: E402

RATE, BPM = 44100, 166
SLOT = RATE * 60.0 / BPM / 4
BARS = 128
SEEDS = ("amen", "second", "third", "fourth")
AMEN = ("K1 K3 S5 g8 g10 K11 K12 S13 g16", "K1 K3 S5 g8 g10 K11 K12 S13 g16",
        "K1 K3 S5 g8 g10 K11 S15", "g2 K3 K4 S5 g8 g10 C11 S15")          # 01_amen_chopping.md 1.2
rng = np.random.default_rng(1969)


def hp(x):
    return np.diff(x, prepend=0.0)


def sound(kind, seconds=0.6):
    t = np.arange(int(seconds * RATE)) / RATE
    if kind == "K":
        return 0.9 * np.sin(2 * np.pi * (50 * t + 90 * 0.03 * (1 - np.exp(-t / 0.03)))) * np.exp(-t / 0.12) + 0.3 * hp(rng.normal(size=len(t))) * np.exp(-t / 0.004)
    if kind in "Sg":
        s = 0.5 * hp(rng.normal(size=len(t))) * np.exp(-t / 0.07) + 0.35 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04)
        return s * (0.22 if kind == "g" else 1.0)
    if kind == "C":
        return 0.45 * hp(rng.normal(size=len(t))) * np.exp(-t / 0.5)
    return 0.08 * hp(rng.normal(size=len(t))) * np.exp(-t / 0.03)            # the ride


def make_break():
    out = np.zeros(int(64 * SLOT + RATE * 0.5))
    hits = []
    for b, row in enumerate(AMEN):
        for tok in row.split():
            hits.append(((b * 16 + int(tok[1:]) - 1), tok[0]))
    for step in range(0, 64, 2):                                            # the ride on every eighth
        at = int(step * SLOT)
        out[at:at + int(0.6 * RATE)] += sound("r")[:len(out) - at]
    starts, truth = [], []
    for step, kind in hits:
        at = max(int(step * SLOT + rng.uniform(-0.003, 0.003) * RATE), 0)
        s = sound(kind)
        out[at:at + len(s)] += s[:len(out) - at]
        starts.append(at)
        truth.append(kind)
    return out / np.abs(out).max() * 0.9, starts, truth


def make_voice():
    out = np.zeros(int(128 * SLOT + RATE))
    starts, step = [], 0
    while step < 124:
        at = int(step * SLOT + rng.uniform(-0.01, 0.01) * RATE) if step else 0
        dur = rng.uniform(0.12, 0.3)
        t = np.arange(int(dur * RATE)) / RATE
        f0 = rng.uniform(150, 220) * (1 + 0.03 * t / dur)
        phase = 2 * np.pi * np.cumsum(f0) / RATE
        v = sum((1.0 / h) * (1.6 if 500 < h * f0[0] < 1400 else 1.0) * np.sin(h * phase) for h in range(1, 11))
        env = np.minimum(np.minimum(t / 0.03, 1.0), np.clip((dur - t) / 0.04, 0, 1))
        v = v * env * rng.uniform(0.5, 1.0)
        if rng.random() < 0.4:
            n = int(0.012 * RATE)
            v[:n] += 0.15 * hp(rng.normal(size=n))
        out[at:at + len(v)] += v
        starts.append(at)
        step += int(rng.choice((2, 3, 3, 4, 5)))
    return out / np.abs(out).max() * 0.9, starts


def make_pad():
    seconds, chords = 1.2, ((220.0, 261.6, 329.6), (196.0, 246.9, 293.7), (174.6, 220.0, 261.6))
    t = np.arange(int(seconds * RATE)) / RATE
    env = np.minimum(t / 0.35, 1.0) * np.clip((seconds - t) / 0.2, 0, 1)
    out = np.concatenate([env * sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) for f in c) for c in chords])
    return out / np.abs(out).max() * 0.8, [int(i * seconds * RATE) for i in range(3)]


def drums_for(bar):
    """The drums as the integrator would pass them when they are held bars: deal.held_bar's kick and snare steps
    for each bar of the group, with the group's fill (deal.fill) added to the last bar's snares."""
    out = []
    for b in range(bar, bar + 4):
        held = deal.held_bar({"kick": [0, 10], "snare": [4, 12], "hats": [2, 6, 10, 14]}, "dnb", 0.7, b, "drums")
        out.append({"kick": sorted(held["kick"]), "snare": sorted(set(held["snare"]) | {s for s, _ in deal.fill(b, "drums")})})
    return out


# ---- measuring a run of plans -------------------------------------------------------------------------------

def run(cuts, role, style, seed, density=0.7, taken_of=None, bars=BARS):
    """One layer's events over `bars` bars, a group at a time."""
    events = []
    for bar in range(0, bars, 4):
        taken = taken_of(bar) if taken_of else set()
        events += chopper.plan(cuts, role=role, style=style, drums=drums_for(bar), taken=taken, bar=bar, seed=seed,
                               density=density, slot_len=SLOT)
    return events


def band(kind):
    return 0 if kind == "heavy" else 2 if kind in ("sharp", "ghost") else 1


def vectors(cuts, events):
    top = max(c["level"] for c in cuts)
    out = []
    for b in range(len(events) // 16):
        v = [0.0] * 48
        for s, e in enumerate(events[16 * b:16 * b + 16]):
            if isinstance(e, dict):
                c = cuts[e["slice"]]
                v[s * 3 + band(c["kind"])] += c["level"] / top * e["gain"]
        out.append(v)
    return out


def corr(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    da, db = [x - ma for x in a], [y - mb for y in b]
    den = math.sqrt(sum(x * x for x in da) * sum(y * y for y in db))
    return sum(x * y for x, y in zip(da, db)) / den if den else None


def lags(cuts, events):
    """Mean similarity at lags 1, 2, 4 and the same-section baseline (all pairs inside a section)."""
    v = vectors(cuts, events)
    n, sums = len(v), {}
    for i in range(n):
        for j in range(i + 1, n):
            if i // deal.SECTION != j // deal.SECTION:
                continue
            r = corr(v[i], v[j])
            if r is None:
                continue
            for key in ("base", j - i):
                s = sums.setdefault(key, [0.0, 0])
                s[0] += r
                s[1] += 1
    get = lambda k: sums[k][0] / sums[k][1] if k in sums and sums[k][1] else float("nan")
    return get(1), get(2), get(4), get("base")


def sig(events, b):
    return tuple(e if not isinstance(e, dict) else (e["slice"], e["reverse"], e["semis"]) for e in events[16 * b:16 * b + 16])


def repeats(events):
    n = len(events) // 16
    prev = sum(sig(events, b) == sig(events, b - 1) for b in range(1, n)) / (n - 1)
    four = sum(sig(events, b) == sig(events, b - 4) for b in range(4, n)) / (n - 4)
    earlier = sum(any(sig(events, b) == sig(events, a) for a in range(b // deal.SECTION * deal.SECTION, b)) for b in range(n)) / n
    return prev, four, earlier


def is_sharp(cuts, e):
    return isinstance(e, dict) and cuts[e["slice"]]["kind"] == "sharp"


def spine(cuts, events):
    n = len(events) // 16
    occ = [sum(isinstance(events[16 * b + s], dict) for b in range(n)) / n for s in (0, 4, 12)]
    second = sum(any(is_sharp(cuts, events[16 * b + s]) for s in (12, 14, 10)) or is_sharp(cuts, events[16 * b + 8]) and not is_sharp(cuts, events[16 * b + 4]) for b in range(n)) / n
    heavy3 = 0
    for g in range(n // 4):
        heavy3 += sum(isinstance(events[64 * g + 16 * j], dict) and cuts[events[64 * g + 16 * j]["slice"]]["kind"] == "heavy" for j in range(4)) >= 3
    return occ, second, heavy3 / (n // 4)


def runs_of_same(group):
    """Retrigger figures: three or more starts of the same slice, each within two sixteenths of the last."""
    found, c = [], 0
    starts = [(i, e) for i, e in enumerate(group) if isinstance(e, dict)]
    k = 0
    while k < len(starts):
        m = k
        while m + 1 < len(starts) and starts[m + 1][1]["slice"] == starts[k][1]["slice"] and starts[m + 1][0] - starts[m][0] <= 2:
            m += 1
        if m - k >= 2:
            found.append(starts[k:m + 1])
        k = m + 1
    return found


def plain_bar(cuts, bar):
    hits = [(s, e) for s, e in enumerate(bar) if isinstance(e, dict)]
    return len(hits) >= 3 and all(cuts[e["slice"]]["home"] == s and not e["reverse"] and not e["semis"] for s, e in hits)


def budgets(cuts, events, anchor=True):
    """Per group: (most rolls, most reversals, most empty downbeats, fewest plain bars, rolls not rising, groups
    whose four bars are not all different, groups whose first downbeat is not the loudest)."""
    worst = [0, 0, 0, 4, 0, 0, 0]
    for g in range(len(events) // 64):
        grp = events[64 * g:64 * g + 64]
        rolls = runs_of_same(grp)
        worst[0] = max(worst[0], len(rolls))
        worst[1] = max(worst[1], sum(isinstance(e, dict) and e["reverse"] for e in grp))
        if anchor:
            worst[2] = max(worst[2], sum(not isinstance(grp[16 * j], dict) for j in range(4)))
            worst[3] = min(worst[3], sum(plain_bar(cuts, grp[16 * j:16 * j + 16]) for j in range(4)))
            loud = [cuts[e["slice"]]["level"] * e["gain"] for e in grp if isinstance(e, dict)]
            if isinstance(grp[0], dict) and cuts[grp[0]["slice"]]["level"] * grp[0]["gain"] < max(loud) - 1e-9:
                worst[6] += 1
        for r in rolls:
            if all(e["gate"] == 1 for _, e in r) and all(r[k + 1][0] - r[k][0] == 1 for k in range(len(r) - 1)):
                gains = [e["gain"] for _, e in r]
                worst[4] += any(b <= a for a, b in zip(gains, gains[1:])) and len(set(gains)) > 1
        sigs = {tuple(map(repr, grp[16 * j:16 * j + 16])) for j in range(4)}
        worst[5] += len(sigs) < 4
    return worst


def ghosts_attached(cuts, events):
    bad = total = 0
    for g in range(len(events) // 64):
        grp = events[64 * g:64 * g + 64]
        for c, e in enumerate(grp):
            if isinstance(e, dict) and cuts[e["slice"]]["kind"] == "ghost" and not e["reverse"]:
                total += 1
                nxt = next((m for m in range(c + 1, c + 3) if m >= 64 or grp[m] is not None), None)
                if nxt is None or nxt < 64 and not (isinstance(grp[nxt], dict) and cuts[grp[nxt]["slice"]]["kind"] in ("heavy", "sharp", "ghost")):
                    bad += 1
    return bad, total


def gate_faults(cuts, events):
    """Slices that would still be sounding when this layer's next event comes (the group wrapping round)."""
    bad = 0
    for g in range(len(events) // 64):
        grp = events[64 * g:64 * g + 64]
        marks = [c for c, e in enumerate(grp) if e is not None]
        for k, c in enumerate(marks):
            e = grp[c]
            if not isinstance(e, dict):
                continue
            room = (marks[k + 1] if k + 1 < len(marks) else 64 + marks[0]) - c
            length = e["gate"] if e["gate"] else cuts[e["slice"]]["steps"]
            bad += length > room + 1e-9
    return bad


def true_share(cuts, events):
    """The share of slices that land on the step they came from: (off the spine, all). The spine's cells (1, 5, 13)
    are filled by rule in every style, so the share off them is the cutter's own: how much source order survives."""
    hits = [(c % 16, e) for c, e in enumerate(events) if isinstance(e, dict) and not e["reverse"]]
    off = [(s, e) for s, e in hits if s not in (0, 4, 12)]
    same = lambda some: sum(cuts[e["slice"]]["home"] == s for s, e in some) / max(len(some), 1)
    return same(off), same(hits)


def valid(events, n):
    ok = len(events) == 64
    for e in events:
        if e is None or e == "rest":
            continue
        ok &= isinstance(e, dict) and set(e) == {"slice", "gain", "reverse", "semis", "gate"} and 0 <= e["slice"] < n
        ok &= e["gain"] > 0 and isinstance(e["reverse"], bool) and (e["gate"] is None or isinstance(e["gate"], int) and e["gate"] >= 1)
    return ok


# ---- the checks ---------------------------------------------------------------------------------------------

def main():
    rows, failures = [], []

    def check(name, value, target, ok):
        rows.append((name, value, target, "ok" if ok else "OUT"))
        if not ok:
            failures.append(name)

    brk, starts, truth = make_break()
    amen = chopper.classify(chop.measure(brk, RATE, starts), SLOT)
    voice_mono, vstarts = make_voice()
    voice = chopper.classify(chop.measure(voice_mono, RATE, vstarts), SLOT)
    pad_mono, pstarts = make_pad()
    pad = chopper.classify(chop.measure(pad_mono, RATE, pstarts), SLOT)

    want = {"K": ("heavy",), "S": ("sharp",), "g": ("ghost",), "C": ("sharp", "other")}
    right = sum(c["kind"] in want[k] for c, k in zip(amen, truth))
    check("break slices classed as played", f"{right}/{len(truth)}", "all", right == len(truth) and len(amen) == len(truth))
    vk = [c["kind"] for c in voice]
    check("voice slices classed tone", f"{vk.count('tone')}/{len(vk)}", ">= 80%", vk.count("tone") >= 0.8 * len(vk))
    roles = {"break": chopper.role_of(amen), "break 2": chopper.role_of(amen), "voice": chopper.role_of(voice), "pad": chopper.role_of(pad)}
    check("roles by themselves", " ".join(f"{k}={v}" for k, v in roles.items()), "anchor anchor hook bed",
          list(roles.values()) == ["anchor", "anchor", "hook", "bed"])
    given = chopper.assign_roles(roles)
    check("roles assigned", " ".join(f"{k}={v}" for k, v in given.items()), "one anchor, one carrier",
          list(given.values()) == ["anchor", "carrier", "hook", "bed"])
    homes = sum(c["home"] == (int(round(s / SLOT)) % 16) for c, s in zip(amen, starts))
    check("homes on the source's steps", f"{homes}/{len(amen)}", "all", homes == len(amen))

    # ---- the anchor, every style: similarity, repeats, spine, budgets ----
    targets_true = {"jungle": 0.6, "atmospheric": 0.85, "drumfunk": 0.5, "techstep": 1.0, "breakcore": 0.2, "footwork": 0.6}
    # The spine applies where the preset keeps a backbeat (breakcore's is "free", footwork alternates half time). The
    # similarity and repeat targets come from the reference jungle set, so they apply where the preset has bars that
    # differ inside a group (01 7.6 "bars alike within group": jungle 2 of 4, drumfunk 1-2); atmospheric (3 of 4
    # alike) and techstep (all alike, a fixed skeleton) are meant to repeat, and are shown for information.
    strict = ("jungle", "atmospheric", "drumfunk", "techstep")
    varied = ("jungle", "drumfunk")
    for style in chopper.STYLES:
        stats = []
        for seed in SEEDS:
            ev = run(amen, "anchor", style, seed)
            stats.append((lags(amen, ev), repeats(ev), spine(amen, ev), budgets(amen, ev), ghosts_attached(amen, ev),
                          gate_faults(amen, ev), true_share(amen, ev)))
        mean = lambda f: sum(f(s) for s in stats) / len(stats)
        l1, l2, l4, base = (mean(lambda s, k=k: s[0][k]) for k in range(4))
        prev, four, earlier = (mean(lambda s, k=k: s[1][k]) for k in range(3))
        occ = [mean(lambda s, k=k: s[2][0][k]) for k in range(3)]
        second, heavy3 = mean(lambda s: s[2][1]), mean(lambda s: s[2][2])
        worst = [max(s[3][k] for s in stats) for k in (0, 1, 2)] + [min(s[3][3] for s in stats)] + [sum(s[3][k] for s in stats) for k in (4, 5, 6)]
        ghost_bad, ghost_all = sum(s[4][0] for s in stats), sum(s[4][1] for s in stats)
        gates, share, share_all = sum(s[5] for s in stats), mean(lambda s: s[6][0]), mean(lambda s: s[6][1])
        tag = f"{style}:"
        if style in varied:
            check(f"{tag} lag 1 - baseline", f"{l1 - base:+.3f} (lag1 {l1:.3f}, base {base:.3f})", "within 0.05 of 0", abs(l1 - base) <= 0.05)
            check(f"{tag} lag 4 - baseline", f"{l4 - base:+.3f} (lag2 {l2 - base:+.3f})", "0.13 +/- 0.06", 0.07 <= l4 - base <= 0.19)
            check(f"{tag} exact repeats (prev / 4 back)", f"{prev:.3f} / {four:.3f}", "<= 0.05 / <= 0.10", prev <= 0.05 and four <= 0.10)
        elif style in strict:
            rows.append((f"{tag} lag 1 / lag 4 - baseline", f"{l1 - base:+.3f} / {l4 - base:+.3f}; repeats {prev:.2f}/{four:.2f}", "(preset: bars alike)", "info"))
        if style in strict:
            # 13 is checked as the second backbeat, wherever the preset puts it (13, 15 or 11): the research's own
            # overlay has a good chop's backbeat on 13 "half the time" (README; 01 R10), and the reference's 0.89 on
            # that cell is a full mix, where the kit's snare holds it (deal.py plays the spine at 1.0).
            check(f"{tag} spine 1 / 5 sounding (13: own)", f"{occ[0]:.2f} / {occ[1]:.2f} ({occ[2]:.2f})", "> 0.9 each", min(occ[:2]) > 0.9)
            check(f"{tag} second backbeat 13|15|11 sharp", f"{second:.2f}", "> 0.9", second > 0.9)
            check(f"{tag} heavy on 1 in >= 3 of 4", f"{heavy3:.2f} of groups", "1.00", heavy3 >= 0.999)
        else:
            rows.append((f"{tag} lag 1 / lag 4 - baseline", f"{l1 - base:+.3f} / {l4 - base:+.3f}", "(preset is free)", "info"))
            rows.append((f"{tag} spine 1 / 5 / 13", " / ".join(f"{o:.2f}" for o in occ) + f"; repeats {prev:.2f}/{four:.2f}", "(preset is free)", "info"))
        rows.append((f"{tag} same bar earlier in section", f"{earlier:.3f}", "(old plan: 0.73-0.86)", "info"))
        check(f"{tag} per group roll/rev/empty/plain", f"{worst[0]} / {worst[1]} / {worst[2]} / {worst[3]}", "<=1 <=1 <=1 >=1",
              worst[0] <= 1 and worst[1] <= 1 and worst[2] <= 1 and worst[3] >= 1)
        check(f"{tag} rolls rise, 4 bars differ, 1st loudest", f"{worst[4]} / {worst[5]} / {worst[6]} faults", "0 / 0 / 0", worst[4:] == [0, 0, 0])
        check(f"{tag} ghosts left alone / gate faults", f"{ghost_bad}/{ghost_all} / {gates}", "0 / 0", ghost_bad == 0 and gates == 0)
        check(f"{tag} position-true share off spine (all)", f"{share:.2f} ({share_all:.2f})", f"{targets_true[style]:.2f} +/- 0.15", abs(share - targets_true[style]) <= 0.15)

    # ---- layers together ----
    layers = (("break", amen, "anchor"), ("break 2", amen, "carrier"), ("voice", voice, "hook"), ("stab", voice, "stab"),
              ("colour", amen, "colour"), ("pad", pad, "bed"))
    for use_taken in (True, False):
        planned = {}
        for name, cuts, role in layers:
            def taken_of(bar, done=dict(planned)):
                return set().union(*[chopper.cells(ev[16 * bar:16 * bar + 64]) for ev in done.values()]) if done and use_taken else set()
            planned[name] = run(cuts, role, "jungle", name, taken_of=taken_of)
        worst, pair = 0.0, ""
        names = list(planned)
        for a in range(len(names)):
            for b in range(a + 1, len(names)):
                shares = []
                for g in range(BARS // 4):
                    A, B = (chopper.cells(planned[n][64 * g:64 * g + 64]) for n in (names[a], names[b]))
                    if A and B:
                        shares.append(len(A & B) / min(len(A), len(B)))
                share = sum(shares) / len(shares) if shares else 0.0
                if share >= worst:
                    worst, pair = share, f"{names[a]} + {names[b]}"
        if use_taken:
            check("layers planned with taken: worst overlap", f"{worst:.2f} ({pair})", "<= 0.5", worst <= 0.5)
            hook = planned["voice"]
            hook_bars = sum(any(isinstance(e, dict) for e in hook[16 * b:16 * b + 16]) for b in range(BARS)) / BARS * 8
            onsets = [c % 16 for c, e in enumerate(hook) if isinstance(e, dict)]
            late = sum(s >= 8 or s == 5 for s in onsets) / max(len(onsets), 1)
            check("hook: bars with a hook per 8", f"{hook_bars:.2f}", "about 3 (2-4)", 2 <= hook_bars <= 4)
            check("hook: onsets on steps 9-16 or 6", f"{late:.2f}", ">= 0.9", late >= 0.9)
            for name, cuts, role in layers:
                g, ok = gate_faults(cuts, planned[name]), all(valid(planned[name][64 * k:64 * k + 64], len(cuts)) for k in range(BARS // 4))
                check(f"{role} ({name}): events valid, gate faults", f"{'valid' if ok else 'INVALID'}, {g}", "valid, 0", ok and g == 0)
        else:
            rows.append(("layers planned without taken: worst", f"{worst:.2f} ({pair})", "(for contrast)", "info"))

    # ---- determinism, every style and role, timing ----
    same = True
    for style in chopper.STYLES:
        for role in chopper.ROLES:
            for bar in (0, 28, 60):
                kw = dict(role=role, style=style, drums=drums_for(bar), taken={1, 17}, bar=bar, seed="det", density=0.6, slot_len=SLOT, turn=1)
                a = chopper.plan(amen, **kw)
                b = chopper.plan([dict(c) for c in amen], **{**kw, "drums": [{k: tuple(v) for k, v in d.items()} for d in kw["drums"]], "taken": [17, 1]})
                same &= a == b and valid(a, len(amen))
    check("same arguments, same plan (all styles x roles)", "yes" if same else "NO", "yes", same)
    held = [chopper.plan(amen, role="anchor", style="jungle", drums=drums_for(0), taken=set(), bar=bar, seed="h", density=0.7, slot_len=SLOT, held=True) for bar in (0, 4, 36)]
    turned = chopper.plan(amen, role="anchor", style="jungle", drums=drums_for(0), taken=set(), bar=0, seed="h", density=0.7, slot_len=SLOT, turn=1)
    check("held: same plan group to group; turn changes it", f"{held[0] == held[1] == held[2]} / {turned != held[0]}", "True / True", held[0] == held[1] == held[2] and turned != held[0])

    forty = [dict(c) for c in amen] + [dict(c, pos=c["pos"] + int(64 * SLOT)) for c in amen[:40 - len(amen)]]
    chopper.classify(forty, SLOT)
    times = []
    for style in chopper.STYLES:
        for bar in range(0, 64, 4):
            d = drums_for(bar)
            t0 = time.perf_counter()
            chopper.plan(forty, role="anchor", style=style, drums=d, taken=set(), bar=bar, seed="t", density=0.8, slot_len=SLOT)
            times.append((time.perf_counter() - t0) * 1000)
    times.sort()
    check(f"time per plan, {len(forty)} slices (median / worst)", f"{times[len(times) // 2]:.2f} / {times[-1]:.2f} ms", "< 5 ms", times[-1] < 5)

    width = max(len(r[0]) for r in rows)
    vwidth = max(len(r[1]) for r in rows)
    twidth = max(len(r[2]) for r in rows)
    for name, value, target, mark in rows:
        print(f"{name:<{width}}  {value:<{vwidth}}  {target:<{twidth}}  {mark}")
    print()
    print("ALL OK" if not failures else "FAILURES: " + "; ".join(failures))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
