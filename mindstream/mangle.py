"""Damage, made here: a chain for wrecking a sound in more than one way, with a pad to move between the ways.

    the sound -> below 90 Hz kept as it is
              -> a ringing filter that sweeps in time (movement)
              -> driven, harder where the sound is louder if asked (follow)
              -> four CURVES at once, each a different kind of damage: the pad blends between them
              -> a BODY for it to ring in (a box, a tin, a pipe, or any short sound from a library)
              -> brought back to the loudness it had
              -> a filter turned by hand, over all of it (Filter, below)

Everything after the curves is linear, so the four corners are made once and the pad is only a mix of them:
moving it costs nothing and is heard at once. Arithmetic on audio in memory; nothing is written anywhere.
"""
import numpy as np

from .parts import BODIES, DAMAGE, PLAIN

SPLIT = 90.0       # Hz: what is below this is left alone
CUTOFFS = 10


def _analytic(x):
    """x with its negative frequencies removed (for shifting every frequency by the same amount)."""
    n = len(x)
    spectrum = np.fft.fft(x)
    keep = np.zeros(n)
    keep[0] = 1.0
    keep[1:(n + 1) // 2] = 2.0
    if n % 2 == 0:
        keep[n // 2] = 1.0
    return np.fft.ifft(spectrum * keep)


def _held(v, rate, to=2500.0):
    step = max(int(rate / to), 1)
    return v[(np.arange(len(v)) // step) * step]


# name: (what it does to a signal already driven to some size, what it is)
CURVES = {
    "tape": (lambda u, rate: np.tanh(u), "rounded off: the gentlest"),
    "tube": (lambda u, rate: np.tanh(u + 0.5) - np.tanh(0.5), "rounded off more on one side than the other"),
    "clip": (lambda u, rate: np.clip(u, -1.0, 1.0), "cut flat at the top and bottom"),
    "fuzz": (lambda u, rate: np.sign(u) * (1.0 - np.exp(-3.0 * np.abs(u))), "squared up almost at once"),
    "fold": (lambda u, rate: np.sin(np.clip(u, -8.0, 8.0) * np.pi / 2), "folded back on itself, smoothly"),
    "crease": (lambda u, rate: (2 / np.pi) * np.arcsin(np.sin(np.clip(u, -8.0, 8.0) * np.pi / 2)), "folded back on itself, with sharp corners"),
    "rectify": (lambda u, rate: np.abs(np.tanh(u)), "the bottom half flipped up: an octave above appears"),
    "half": (lambda u, rate: np.maximum(np.tanh(u), 0.0), "the bottom half cut away"),
    "sputter": (lambda u, rate: np.sign(u) * np.maximum(np.abs(np.tanh(u)) - 0.35, 0.0) / 0.65, "the quiet parts cut out: it spits"),
    "crush": (lambda u, rate: np.round(np.tanh(u) * 4.0) / 4.0, "nine steps of level and nothing between"),
    "decimate": (lambda u, rate: _held(np.tanh(u), rate), "held and stepped in time, as if sampled far too slowly"),
    "harmonic": (lambda u, rate: (lambda v: 16 * v ** 5 - 20 * v ** 3 + 5 * v)(np.tanh(u)), "the fifth harmonic forced out of everything"),
    "ring": (lambda u, rate: np.tanh(u) * np.sin(2 * np.pi * 140.0 * np.arange(len(u)) / rate), "multiplied by a low tone: clanging"),
    "shift": (lambda u, rate: np.real(_analytic(np.tanh(u)) * np.exp(2j * np.pi * 70.0 * np.arange(len(u)) / rate)),
              "every frequency moved up by the same amount: nothing lines up any more"),
}


assert tuple(CURVES) == DAMAGE, "the kinds of damage here and in parts.py have come apart"
_rings = {}


def one(sound, rate, knob, patch=None):
    """One sound (a note, a hit, a slice) with its knob at `knob` (0 to 1), in the character `patch`."""
    if knob <= 0.005 or len(sound) < 64:
        return sound
    patch = patch or PLAIN
    if rate not in _rings:
        _rings[rate] = bodies(rate)
    ring = _rings[rate].get(patch["body"]) if patch["body_mix"] > 0.01 else None
    tail = 0 if ring is None else len(ring)
    size = 1 << int(np.ceil(np.log2(len(sound) + tail + 1)))                 # room for the body to ring on; a length the transform likes
    padded = np.zeros(size, np.float32)
    padded[:len(sound)] = sound
    names = list(patch["mix"])
    made = corners(padded, rate, names, knob, patch["movement"], patch["follow"], ring, patch["body_mix"])
    shares = [patch["mix"][name] for name in names]
    out = sum(share * version for share, version in zip(shares, made)) * evened(shares)
    return out[:len(sound) + tail].astype(np.float32)


def bodies(rate, found=None):
    """Things for a sound to ring in: {name: impulse response}. `found` adds short sounds of your own (name -> mono audio)."""
    rng = np.random.default_rng(7)
    t = lambda seconds: np.arange(int(rate * seconds)) / rate      # noqa: E731
    box = rng.standard_normal(len(t(0.03))) * np.exp(-t(0.03) * 160)
    box = np.convolve(box, np.ones(12) / 12, "same")
    tin = sum(np.sin(2 * np.pi * f * t(0.12) + rng.uniform(0, 6)) * np.exp(-t(0.12) * rng.uniform(25, 70))
              for f in (310, 523, 811, 1190, 1630, 2240, 2975, 3620, 4410, 5230))
    pipe = np.zeros(len(t(0.2)))
    for i in range(22):
        pipe[min(int(i * rate / 110.0), len(pipe) - 1)] += 0.86 ** i
    spring = np.sin(2 * np.pi * (900 * t(0.3) + 2600 * t(0.3) ** 2)) * np.exp(-t(0.3) * 9) * rng.standard_normal(len(t(0.3))) ** 2
    out = {"none": None, "box": box, "tin": tin, "pipe": pipe, "spring": spring}
    assert tuple(out) == BODIES
    for name, sound in (found or {}).items():
        sound = np.asarray(sound, dtype=np.float64)[:int(rate * 0.4)]
        if len(sound) > 64:
            out[name] = sound * np.linspace(1, 0, len(sound)) ** 2
    return {name: (None if ir is None else ir / (np.sqrt((ir ** 2).sum()) + 1e-12)) for name, ir in out.items()}


def cycles_for(seconds):
    """How many times the filter sweeps in one pass of a loop: a power of two, near three a second."""
    return int(2 ** max(round(np.log2(max(seconds * 3.0, 1.0))), 0))


def corners(x, rate, names, drive=0.5, movement=0.0, follow=0.0, body=None, body_mix=0.0):
    """A loop (mono) through the chain, once for each of the four curves named: [four arrays], for `blend`.
    drive, movement, follow and body_mix are 0 to 1; body is an impulse response from `bodies`, or None."""
    n = len(x)
    spectrum = np.fft.rfft(x)
    freqs = np.maximum(np.fft.rfftfreq(n, 1.0 / rate), 1.0)
    keep = 1.0 / (1.0 + (freqs / SPLIT) ** 6)
    lows, highs = np.fft.irfft(spectrum * keep, n), spectrum * (1.0 - keep)
    if movement > 0.01:                               # a two-pole low-pass with a peak at its cutoff, sweeping down and back
        top, bottom, q = 9000.0, 9000.0 * 2.0 ** (-5.5 * movement), 1.0 + 14.0 * movement ** 2
        place = (0.5 - 0.5 * np.cos(2 * np.pi * cycles_for(n / rate) * np.arange(n) / n)) * (CUTOFFS - 1)
        sound = np.zeros(n)
        for i in range(CUTOFFS):
            weight = np.clip(1.0 - np.abs(place - i), 0.0, 1.0)
            if weight.any():
                r = freqs / (top * (bottom / top) ** (i / (CUTOFFS - 1.0)))
                sound += np.fft.irfft(highs / (1.0 - r ** 2 + 1j * r / q), n) * weight
    else:
        sound = np.fft.irfft(highs, n)
    level = float(np.abs(sound).max()) + 1e-9
    gain = 1.0 + 40.0 * drive ** 2
    if follow > 0.01:                                 # driven harder where the sound itself is louder
        width = max(int(rate * 0.02), 1)
        loud = np.convolve(np.abs(sound), np.ones(width) / width, "same")
        gain = gain * (1.0 - follow + follow * 2.0 * loud / (float(loud.max()) + 1e-9))
    driven, mix = sound / level * gain, min(drive * 4.0, 1.0)
    dry_level = np.sqrt((x ** 2).mean() + 1e-12)
    ring = None if body is None or body_mix <= 0.01 else np.fft.rfft(body, n)
    out = []
    for name in names:
        made = CURVES[name][0](driven, rate)
        made = made - made.mean()
        made = ((1.0 - mix) * sound / level + mix * made) * level
        if ring is not None:                          # round the loop, so the tail of the end lands on the start
            rung = np.fft.irfft(np.fft.rfft(made) * ring, n)
            rung *= np.sqrt((made ** 2).mean() + 1e-12) / np.sqrt((rung ** 2).mean() + 1e-12)
            made = (1.0 - body_mix) * made + body_mix * rung
        whole = lows + made
        out.append((whole * dry_level / np.sqrt((whole ** 2).mean() + 1e-12)).astype(np.float32))    # as loud as it was
    return out


def weights(x, y):
    """Where the pad stands (0 to 1 each way) as a share for each corner: bottom-left, bottom-right, top-left, top-right."""
    x, y = min(max(x, 0.0), 1.0), min(max(y, 0.0), 1.0)
    return (1 - x) * (1 - y), x * (1 - y), (1 - x) * y, x * y


def evened(shares):
    """What to multiply a blend by so the middle of the pad is as loud as its corners (four different kinds of damage
    partly cancel when mixed)."""
    return sum(w * w for w in shares) ** -0.15


def blend(made, x, y):
    shares = weights(x, y)
    return sum(w * c for w, c in zip(shares, made)) * evened(shares)


class Filter:
    """A filter turned by hand while the sound plays: low-pass, high-pass or band-pass, with a ringing peak at its
    cutoff as the resonance comes up. It works a block at a time and remembers where it was, so it can be swept."""
    KINDS = ("off", "low", "high", "band")

    def __init__(self, rate):
        self.rate, self.a, self.b = rate, 0.0, 0.0

    def run(self, block, kind, cutoff, resonance):
        """block: mono samples. cutoff in Hz; resonance 0 (none) to 1 (close to ringing on its own)."""
        if kind not in ("low", "high", "band"):
            self.a = self.b = 0.0
            return block
        g = float(np.tan(np.pi * min(max(cutoff, 20.0), self.rate * 0.45) / self.rate))
        k = 2.0 - 1.9 * min(max(resonance, 0.0), 1.0)
        a1 = 1.0 / (1.0 + g * (g + k))
        a2, a, b, out = g * a1, self.a, self.b, []
        a3 = g * a2
        for x in block.tolist():
            v3 = x - b
            v1 = a1 * a + a2 * v3
            v2 = b + a2 * a + a3 * v3
            a, b = 2.0 * v1 - a, 2.0 * v2 - b
            out.append(v2 if kind == "low" else v1 * k if kind == "band" else x - k * v1 - v2)
        self.a, self.b = a, b
        return np.asarray(out, dtype=np.float32)
