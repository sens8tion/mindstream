"""Find the tempo and the position of the beat in a piece of audio. Needs only numpy.

Used so that everything moves to one clock: the tempo asked of the video model's music, the pulse of
the visuals and the timing of scene changes all follow what is actually heard.
"""
import numpy as np


def detect(pcm, rate, channels, hint=120.0, low=60.0, high=180.0):
    """16-bit PCM bytes -> {"bpm": float, "offset": seconds to the first beat, "confidence": float}, or None.

    `hint` is the tempo that was asked for: among equally plausible answers (double time, half time)
    the one nearest the hint wins."""
    x = np.frombuffer(pcm, dtype=np.int16).astype(np.float32)
    if channels > 1:
        x = x[: len(x) // channels * channels].reshape(-1, channels).mean(axis=1)
    hop = max(rate // 100, 1)                                   # 10 ms steps
    n = len(x) // hop
    if n < 150:                                                 # under a second and a half: nothing to measure
        return None
    energy = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-9)
    onset = np.maximum(np.diff(np.log(energy + 1e-3)), 0.0)     # how sharply the sound gets louder
    onset -= onset.mean()
    if not np.any(onset > 0):
        return None
    steps_per_second = rate / hop
    lags = np.arange(int(steps_per_second * 60 / high), int(steps_per_second * 60 / low) + 1)
    lags = lags[lags < len(onset) // 2]
    if len(lags) == 0:
        return None
    strength = np.array([float(np.dot(onset[:-lag], onset[lag:])) / (len(onset) - lag) for lag in lags])
    bpms = 60.0 * steps_per_second / lags
    weight = np.exp(-0.5 * (np.log2(bpms / hint) / 0.35) ** 2)   # prefer tempos near the one asked for
    best = int(np.argmax(strength * weight))
    lag = int(lags[best])
    if 0 < best < len(lags) - 1:                                # refine between whole steps
        a, b, c = strength[best - 1], strength[best], strength[best + 1]
        shift = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0.0
        bpm = 60.0 * steps_per_second / (lag + shift)
    else:
        bpm = float(bpms[best])
    phase = int(np.argmax([onset[o::lag].sum() for o in range(lag)]))
    spread = float(strength.std()) or 1.0
    return {"bpm": float(bpm), "offset": phase / steps_per_second,
            "confidence": float((strength[best] - strength.mean()) / spread)}
