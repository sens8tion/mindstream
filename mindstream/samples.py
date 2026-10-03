"""Samples pulled from outside (a local sample library, or the free archives) made ready to play: brought to
the session's sample rate, trimmed, and cut into slices at their obvious transients (or as stated) so they can be re-played on the grid.
Everything is arithmetic on audio in memory; nothing is written to disk.
"""
import numpy as np


def to_rate(x, rate, target=44100):
    """Stereo float32 at the target rate, from mono or multi-channel audio at any rate."""
    x = np.asarray(x, dtype=np.float32)
    x = x[:, None] if x.ndim == 1 else x
    x = x[:, :2] if x.shape[1] >= 2 else np.repeat(x[:, :1], 2, axis=1)
    if rate != target and len(x) > 1:
        n = int(round(len(x) * target / rate))
        where = np.linspace(0, len(x) - 1, n)
        x = np.stack([np.interp(where, np.arange(len(x)), x[:, c]) for c in (0, 1)], axis=1).astype(np.float32)
    return x


def trim(x, rate, seconds, quiet=0.02):
    """From where the sound really starts, at most `seconds` of it, at a level that sits with everything else."""
    level = np.abs(x).max(axis=1)
    peak = float(level.max()) if len(level) else 0.0
    if peak < 1e-4:
        return x[:0]
    loud = np.nonzero(level > peak * quiet)[0]
    start = max(int(loud[0]) - int(rate * 0.003), 0)
    out = x[start:start + int(rate * seconds)].copy()
    edge = min(int(rate * 0.006), len(out) // 2)
    if edge > 1:
        out[-edge:] *= np.linspace(1, 0, edge, dtype=np.float32)[:, None]
    return (out / (float(np.abs(out).max()) + 1e-9) * 0.9).astype(np.float32)


def onsets(mono, rate, sense=1.0):
    """Where things OBVIOUSLY begin in a sound (sample positions): a drum hit, a word, a note. A transient is
    obvious when the level at least doubles, within a few hundredths of a second, over what came just before it,
    and what arrives is at least a quarter as loud as the loudest thing in it. A wash (rain, a room, a held chord) has none. `sense` above 1 asks
    for less obvious ones as well, below 1 for only the plainest."""
    hop = 256
    frames = len(mono) // hop
    if frames < 8:
        return [0]
    level = np.sqrt((np.asarray(mono[:frames * hop], dtype=np.float64).reshape(frames, hop) ** 2).mean(axis=1))
    peak = float(level.max())
    if peak < 1e-5:
        return [0]
    sense = max(float(sense), 0.2)
    ratio, floor, loud = 1.0 + 1.0 / sense, 0.03 * peak, min(0.25 / sense, 0.5) * peak     # a ghost note is not obvious
    jump = np.zeros(frames)
    for i in range(1, frames - 2):
        after = level[i:i + 3].max()
        if after > loud:
            jump[i] = after / (level[max(i - 5, 0):i].mean() + floor)
    gap, last, found = max(int(0.09 * rate / hop), 1), -10 ** 9, [0]
    for i in range(1, frames - 2):
        if jump[i] >= ratio and jump[i] >= jump[i - 1] and jump[i] >= jump[i + 1] and i - last >= gap:
            if i * hop > int(0.03 * rate):
                found.append(max(i * hop - hop, 0))
            last = i
    return sorted(set(found))


GRIDS = {"sixteenths": 0.25, "eighths": 0.5, "beats": 1.0, "bars": 4.0}       # lengths in beats


def cut_points(mono, rate, bpm, how="transients", sense=1.0):
    """Where a sound is cut, and how that is said. `how` is "transients" (the default: at its obvious transients),
    a grid at the tempo ("sixteenths", "eighths", "beats", "bars"), or a number of equal pieces. A sound with no
    obvious transients cannot be cut at them, so it is cut on the eighths, and the answer says so."""
    if isinstance(how, int):
        count = min(max(how, 2), 32)
        return [int(i * len(mono) / count) for i in range(count)], f"cut into {count} equal pieces"
    if how == "whole":
        return [0], "left whole"
    if how == "transients":
        starts = onsets(mono, rate, sense)
        if len(starts) >= 3:
            return starts, f"cut at its {len(starts)} obvious transients"
        how, said = "eighths", "no obvious transients in it, so cut on the eighths"
    else:
        said = f"cut on the {how}"
    step = max(int(rate * 60.0 / bpm * GRIDS.get(how, 0.5)), 1)
    return list(range(0, max(len(mono) - step // 2, 1), step)), said


def slices(x, rate, starts, most=32):
    """A sound cut at `starts` into pieces to be re-played in time, each faded at its edges so it does not click.
    Returns (the pieces, where each began)."""
    starts = list(starts)[:most]
    gaps = [b - a for a, b in zip(starts, starts[1:])]
    longest = max(int(rate * 1.2), max(gaps) if gaps else len(x))      # a sound left whole is one piece, all of it
    out, kept = [], []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(x)
        piece = x[start:min(end, start + longest)].copy()
        if len(piece) < int(rate * 0.03):
            continue
        edge = min(int(rate * 0.004), len(piece) // 2)
        piece[:edge] *= np.linspace(0, 1, edge, dtype=np.float32)[:, None]
        piece[-edge:] *= np.linspace(1, 0, edge, dtype=np.float32)[:, None]
        out.append(piece)
        kept.append(start)
    return out, kept
