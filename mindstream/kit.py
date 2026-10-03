"""Instruments cut from the films' own sound. The tune of the rhythm section (its riff, hook, call and
response) and its drones are played, by first choice, on short stretches of the generated soundtracks:
sustained, tonal moments found in each clip, repitched to the notes and given some room. The synthesised
tones in groove.py are the second resort, for before any film has been made.

Everything here is arithmetic on audio already in memory; nothing is read from or written to disk.
"""
import numpy as np


def make_ir(rate, seconds=0.9, seed=7):
    """The sound of a room: a burst of noise dying away. Sounds are run through it once, when they are made."""
    n = int(rate * seconds)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / rate
    ir = rng.standard_normal(n) * np.exp(-t / (seconds / 5.0))
    ir[:int(rate * 0.012)] *= np.linspace(0, 1, int(rate * 0.012))      # a moment before the room answers
    smooth = np.convolve(ir, np.ones(4) / 4.0, mode="same")             # rooms are duller than noise
    return (smooth / np.sqrt((smooth ** 2).sum())).astype(np.float32)


def reverb(sound, ir, amount):
    """The sound with its echo in the room added after it (the result is longer by the room's tail)."""
    if amount <= 0 or len(sound) < 8:
        return sound
    n = len(sound) + len(ir) - 1
    size = 1 << (n - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(sound, size) * np.fft.rfft(ir, size), size)[:n]
    out = wet * amount
    out[:len(sound)] += sound
    return out.astype(np.float32)


def fade(sound, rate, seconds=0.008):
    edge = min(len(sound) // 2, max(int(rate * seconds), 1))
    out = np.array(sound, dtype=np.float32)
    out[:edge] *= np.linspace(0, 1, edge, dtype=np.float32)
    out[-edge:] *= np.linspace(1, 0, edge, dtype=np.float32)
    return out


def _flat(piece, window):
    """Near 0 for a clear pitch, near 1 for noise."""
    mag = np.abs(np.fft.rfft(piece * window))[4:len(piece) // 4] + 1e-9
    return float(np.exp(np.log(mag).mean()) / mag.mean())


def colour(sound, rate, tone=0.0, drive=0.0):
    """A sound made brighter or darker (tone, -1 to 1) and dirtier (drive, 0 to 1), keeping its loudness."""
    out, peak = sound, float(np.abs(sound).max()) + 1e-9
    if abs(tone) > 0.02 and len(out) > 16:
        freqs = np.fft.rfftfreq(len(out), 1.0 / rate)
        tilt = np.clip((np.maximum(freqs, 30.0) / 900.0) ** (tone * 0.7), 0.12, 6.0)
        out = np.fft.irfft(np.fft.rfft(out) * tilt, len(out))
        out = out * (peak / (float(np.abs(out).max()) + 1e-9))
    if drive > 0.02:
        push = 1.0 + 9.0 * drive
        out = np.tanh(out / peak * push) / np.tanh(push) * peak
    return out.astype(np.float32)


def tone_slices(mono, rate, count=3, seconds=0.3):
    """Up to `count` stretches of a soundtrack that are loud, sustained and tonal (a held vowel, a note, a hum)
    rather than noise or silence: the raw material for a played instrument. Each is `seconds` long."""
    size, hop = int(rate * seconds), int(rate * 0.05)
    if len(mono) < size + hop or float(np.abs(mono).max()) < 1e-3:
        return []
    scored = []
    window = np.hanning(size)
    for start in range(0, len(mono) - size, hop):
        piece = mono[start:start + size]
        level = float(np.sqrt((piece ** 2).mean()))
        if level < 0.02:
            continue
        if _flat(piece, window) > 0.3:                 # hiss, breath, a crash: nothing to play a tune on
            continue
        mag = np.abs(np.fft.rfft(piece * window))[4:size // 4] + 1e-9                  # up to a quarter of the sample rate
        flatness = float(np.exp(np.log(mag).mean()) / mag.mean())                      # near 0 = a clear pitch, near 1 = noise
        halves = [float(np.sqrt((h ** 2).mean())) for h in np.array_split(piece, 4)]
        steady = min(halves) / (max(halves) + 1e-9)                                    # 1 = held, 0 = a blip
        scored.append((level * (1.0 - flatness) ** 2 * (0.3 + steady), start))
    chosen = []
    for _, start in sorted(scored, reverse=True):
        if all(abs(start - other) >= size for other in chosen):
            chosen.append(start)
        if len(chosen) == count:
            break
    out = []
    for start in sorted(chosen):
        piece = mono[start:start + size].astype(np.float32)
        out.append(fade(piece / (float(np.abs(piece).max()) + 1e-9) * 0.9, rate))
    return out


def pitch_of(sound, rate, low=55.0, high=1000.0):
    """The note a piece of sound is sounding, as a MIDI number with its fraction (69 is A 440), or None when it has no
    clear pitch. Found the way a tuner finds it (de Cheveigne and Kawahara's YIN): how unlike the sound is to itself
    a little later, for each delay, normalised; the first delay where it is nearly itself again is the period."""
    x = np.asarray(sound, dtype=np.float64)
    x = x[:min(len(x), int(rate * 0.12))]
    most, least = int(rate / low), max(int(rate / high), 2)
    if len(x) < 2 * most + 2:
        return None
    w = len(x) - most
    diff = np.array([np.sum((x[:w] - x[lag:lag + w]) ** 2) for lag in range(most + 1)])
    diff[0] = 0.0
    norm = diff[1:] * np.arange(1, most + 1) / np.maximum(np.cumsum(diff[1:]), 1e-12)
    norm = np.concatenate([[1.0], norm])
    under = np.where(norm[least:] < 0.15)[0]
    if len(under):
        lag = least + int(under[0])
        while lag + 1 <= most and norm[lag + 1] < norm[lag]:     # down to the bottom of that dip
            lag += 1
    else:
        lag = least + int(np.argmin(norm[least:]))
        if norm[lag] > 0.35:                                     # nothing like a period: noise, or a chord
            return None
    if 1 <= lag < most:                                          # between the samples, by the curve through the three
        a, b, c = norm[lag - 1], norm[lag], norm[lag + 1]
        bend = a - 2 * b + c
        lag = lag + (0.5 * (a - c) / bend if abs(bend) > 1e-12 else 0.0)
    return 69.0 + 12.0 * float(np.log2(rate / lag / 440.0))


def repitch(sound, semitones):
    """The same sound higher or lower, the way a sampler does it: played faster or slower."""
    ratio = 2.0 ** (semitones / 12.0)
    n = max(int(len(sound) / ratio), 8)
    return np.interp(np.linspace(0, len(sound) - 1, n), np.arange(len(sound)), sound).astype(np.float32)


def smear(sound, rate, seconds, rng):
    """A short sound drawn out into a held pad: many overlapping grains taken from all over it."""
    n, grain = int(rate * seconds), int(rate * 0.09)
    if len(sound) <= grain:
        return np.zeros(n, np.float32)
    out = np.zeros(n + grain, np.float32)
    shape = np.hanning(grain).astype(np.float32)
    for at in range(0, n, grain // 4):
        start = int(rng.integers(0, len(sound) - grain))
        out[at:at + grain] += sound[start:start + grain] * shape
    out = out[:n]
    return fade(out / (float(np.abs(out).max()) + 1e-9) * 0.8, rate, 0.4)


def fold(semitones, centre, span=7):
    """A note brought to within `span` semitones of `centre` by octaves: the pitch class is kept, and the sample
    is never played absurdly fast or slow."""
    offset = semitones - centre
    while offset > span:
        offset -= 12
    while offset < -span:
        offset += 12
    return offset


# ---- effects and extra layers: applied once, when a sound is made (see groove.Groove._finish)

def fx_delay(sound, rate, seconds, feedback, mix):
    """Echoes of the sound after it, each quieter than the last."""
    step = max(int(rate * seconds), 1)
    count = 1 if feedback < 0.05 else int(min(8, np.log(0.03) / np.log(feedback) + 1))
    out = np.zeros(len(sound) + step * count, np.float32)
    out[:len(sound)] += sound
    for i in range(1, count + 1):
        out[i * step:i * step + len(sound)] += sound * (mix * feedback ** (i - 1))
    return out


def fx_chorus(sound, depth, mix):
    """The sound doubled by copies a little sharp and a little flat: thicker and wider."""
    cents = 6.0 + 22.0 * depth
    out = sound * (1.0 - 0.4 * mix)
    for sign in (1.0, -1.0):
        copy = repitch(sound, sign * cents / 100.0)
        n = min(len(copy), len(out))
        out[:n] += copy[:n] * (0.5 * mix)
    return out.astype(np.float32)


def fx_crush(sound, bits, rate_fraction):
    """Fewer levels and fewer samples: broken, digital, lo-fi."""
    hold = max(int(round(1.0 / max(rate_fraction, 0.02))), 1)
    held = np.repeat(sound[::hold], hold)[:len(sound)]
    levels = 2.0 ** (bits - 1)
    peak = float(np.abs(sound).max()) + 1e-9
    return (np.round(held / peak * levels) / levels * peak).astype(np.float32)


def fx_tremolo(sound, rate, seconds, depth):
    """The level pulsing up and down in time."""
    t = np.arange(len(sound)) / rate
    return (sound * (1.0 - depth * 0.5 * (1.0 - np.cos(2 * np.pi * t / max(seconds, 0.01))))).astype(np.float32)


def fx_filter(sound, rate, kind, freq, q=0.0):
    """Only the lows, only the highs, or only a band around a frequency. `q` (0 to 1) adds a ringing peak at that
    frequency: the squelch of an acid line, the nasal edge of a wah."""
    if len(sound) < 16:
        return sound
    f = np.maximum(np.fft.rfftfreq(len(sound), 1.0 / rate), 1.0) / freq
    gain = {"low": 1.0 / np.sqrt(1.0 + f ** 4), "high": f ** 2 / np.sqrt(1.0 + f ** 4),
            "band": np.exp(-2.0 * np.log2(f) ** 2)}[kind]
    if q > 0.01:
        gain = gain * (1.0 + 5.0 * q * np.exp(-10.0 * np.log2(f) ** 2))
    out = np.fft.irfft(np.fft.rfft(sound) * gain, len(sound))
    return (out * min(1.0, (float(np.abs(sound).max()) + 1e-9) / (float(np.abs(out).max()) + 1e-9) * 1.2)).astype(np.float32)


def fx_sweep(sound, rate, start, end, seconds):
    """A low-pass filter that moves from one frequency to another over the start of the sound and stays there:
    opening up, or closing down like a plucked string."""
    if len(sound) < 64:
        return sound
    stages = [start * (end / start) ** (i / 4.0) for i in range(5)]
    versions = [fx_filter(sound, rate, "low", f, 0.25) for f in stages]
    place = np.minimum(np.arange(len(sound)) / max(rate * seconds, 1.0), 1.0) * 4.0        # 0 = the start frequency, 4 = the end
    out = np.zeros(len(sound), np.float32)
    for i, version in enumerate(versions):
        out += version * np.clip(1.0 - np.abs(place - i), 0.0, 1.0)
    return out


def front(sound, rate, attack=0.0, punch=0.0):
    """How a sound begins: `attack` seconds of swelling in, or `punch` making its first few milliseconds hit harder."""
    out = np.array(sound, dtype=np.float32)
    if attack > 0.002:
        n = min(int(rate * attack), len(out) // 2)
        if n > 1:
            out[:n] *= np.linspace(0, 1, n, dtype=np.float32) ** 1.5
    if punch > 0.02:
        n = min(int(rate * 0.03), len(out))
        peak = float(np.abs(out).max()) + 1e-9
        out[:n] *= (1.0 + 2.5 * punch * np.exp(-np.arange(n) / (rate * 0.006))).astype(np.float32)
        out = (np.tanh(out / peak * 1.2) / np.tanh(1.2) * peak).astype(np.float32)
    return out


def layer_wave(rate, wave, freq, seconds, decay, rng):
    """One more sound to lay under or over a part: a plain wave or noise at a pitch, dying away."""
    t = np.arange(max(int(rate * seconds), 16)) / rate
    if wave == "noise":
        out = rng.standard_normal(len(t))
    elif wave == "sine":
        out = np.sin(2 * np.pi * freq * t)
    else:
        out = np.zeros(len(t))
        for k in range(1, 14, 2 if wave == "square" else 1):
            if freq * k < rate * 0.45:
                out += np.sin(2 * np.pi * freq * k * t) / k
        out *= 0.7
    return fade(out * np.exp(-t / max(decay, 0.01)), rate, 0.004)
