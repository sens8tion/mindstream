"""Instruments whose sound moves: the voices that carry a hook.

A part that plays few notes is still worth hearing when its sound never stands still (docs/research/07_good_edm.md:
"Energy Flash" is one note under a moving filter; "Acid Tracks" a fixed line whose filter was turned by hand). Every
voice here moves on two clocks:

- fast, inside the note: a filter envelope that opens and closes, an accent that opens it further and shorter, a
  slide from the last note, a pitch envelope, two oscillators beating against each other;
- slow, across the phrase: `cut`, a number from 0 (dark) to 7 (bright) that the player moves over sixteen bars.

So a note repeated is not the same sound, and a line held for a section still goes somewhere.

The voices:
    stab      a piece of the film's own sound, tuned, cut short, through a filter that snaps open and closes
    acid      a sawtooth through a resonant low-pass whose envelope, accents and slides are the line (after the 303)
    reese     two sawtooths a few cents apart, beating, under a filter that breathes with the bar
    hoover    a wide stack of sawtooths whose pitch swoops into the note
    dub       a minor-seventh chord stab, and its echoes, each darker than the last: the delay does the work

The oscillators are made by adding their harmonics, and the filter is applied to each harmonic as it sounds: so a
sweep is exact, nothing aliases, and no sample-by-sample loop is needed. Numpy only; nothing is written.
"""
import numpy as np

LOWEST, HIGHEST = 180.0, 6400.0          # where `cut` 0 and 7 put a voice's filter, before its envelope


def base_cutoff(cut):
    """The filter's resting place for `cut` 0 (dark) to 7 (bright)."""
    return LOWEST * (HIGHEST / LOWEST) ** (min(max(float(cut), 0.0), 7.0) / 7.0)


def lowpass_gain(freq, cutoff, resonance):
    """How much a resonant two-pole low-pass lets through at `freq` when it stands at `cutoff`: 1 well below it, a
    peak of about `resonance` at it, falling twelve decibels an octave above it."""
    r = freq / cutoff
    return 1.0 / np.sqrt((1.0 - r * r) ** 2 + (r / resonance) ** 2)


def envelope(n, rate, attack=0.003, release=0.008, decay=None):
    """The note's loudness: a quick rise, an optional fall (`decay` seconds to a third), and a clean end."""
    t = np.arange(n) / rate
    out = np.minimum(t / max(attack, 1e-4), 1.0)
    if decay:
        out = out * np.exp(-t / decay)
    tail = min(int(rate * release), n // 2)
    if tail > 1:
        out[-tail:] *= np.linspace(1.0, 0.0, tail)
    return out


def additive(rate, pitch, cutoff, resonance, wave="saw", most=96, phase=0.0):
    """An oscillator made of its harmonics, each through the filter as it stands at that moment. `pitch` and `cutoff`
    are curves, one value a sample. wave: "saw" (every harmonic, falling as 1/k) or "square" (odd ones only)."""
    pitch = np.asarray(pitch, dtype=np.float64)
    turning = (2.0 * np.pi * np.cumsum(pitch) / rate + phase).astype(np.float32)
    pitch, cutoff = pitch.astype(np.float32), np.asarray(cutoff, dtype=np.float32)
    out = np.zeros(len(pitch), np.float32)
    top, bottom = float(pitch.max()), float(pitch.min())
    ceiling = 6.0 * float(np.max(cutoff))                         # harmonics far above the filter are not heard: they are not made
    for k in range(1, most + 1):
        if k * top > rate * 0.45 or k * bottom > ceiling:
            break
        if wave == "square" and k % 2 == 0:
            continue
        out += lowpass_gain(k * pitch, cutoff, resonance) * np.sin(k * turning) / k
    return out


def _seconds(rate, length):
    return max(int(rate * max(length, 0.03)), 64)


def acid(rate, freq, length, cut, accent=False, slide_from=None, wave="saw"):
    """A 303-style note: the filter's envelope is the sound. An accent opens it further, shortens it and plays
    louder; a slide glides in from the last note's pitch instead of starting afresh."""
    n = _seconds(rate, length)
    t = np.arange(n) / rate
    pitch = np.full(n, float(freq))
    if slide_from:
        pitch = freq + (float(slide_from) - freq) * np.exp(-t / 0.035)
    decay = 0.06 if accent else 0.12
    # (a third of the other voices' range: a 303's filter rests low and its envelope does the opening)
    cutoff = 0.33 * base_cutoff(cut) * (1.0 + (6.0 if accent else 4.0) * np.exp(-t / decay))
    tone = additive(rate, pitch, np.minimum(cutoff, rate * 0.45), 7.0 if accent else 5.0, wave)
    tone *= envelope(n, rate, attack=0.002, release=0.01) * (1.35 if accent else 1.0)
    return (0.92 * np.tanh(1.6 * tone / 3.0)).astype(np.float32)


def reese(rate, freq, length, cut, beat_seconds=0.35):
    """Two sawtooths about fifteen cents apart, so that they beat; under a filter that breathes once every two beats,
    and a third an octave down for weight."""
    n = _seconds(rate, length)
    t = np.arange(n) / rate
    cutoff = base_cutoff(cut) * 0.6 * (1.0 + 0.7 * (0.5 - 0.5 * np.cos(2.0 * np.pi * t / (2.0 * beat_seconds))))
    tone = (additive(rate, np.full(n, freq * 2 ** (-7.5 / 1200)), cutoff, 1.3) + additive(rate, np.full(n, freq * 2 ** (7.5 / 1200)), cutoff, 1.3, phase=1.1)
            + 0.5 * additive(rate, np.full(n, freq / 2.0), cutoff, 1.0, most=24))
    tone *= envelope(n, rate, attack=0.012, release=0.04)
    return (0.92 * np.tanh(1.2 * tone / 2.5)).astype(np.float32)


def hoover(rate, freq, length, cut):
    """A wide stack of sawtooths (three, spread a fifth of a semitone either side) whose pitch swoops into the
    note from three semitones above, overshooting a little below before it settles."""
    n = _seconds(rate, length)
    t = np.arange(n) / rate
    swoop = 3.0 * np.exp(-t / 0.05) - 0.4 * np.sin(np.minimum(t / 0.18, 1.0) * np.pi) * np.exp(-t / 0.25)
    cutoff = base_cutoff(cut) * (1.2 + 0.8 * np.exp(-t / 0.3))
    tone = sum(additive(rate, freq * 2 ** ((swoop + cents / 100.0) / 12.0), cutoff, 1.1, phase=at * 0.9) for at, cents in enumerate((-20, 0, 20)))
    tone *= envelope(n, rate, attack=0.006, release=0.06)
    return (0.92 * np.tanh(1.4 * tone / 3.0)).astype(np.float32)


def dub(rate, freq, length, cut, echo_seconds, echoes=5, feedback=0.55):
    """A minor-seventh chord stab, short and plucked, and its echoes: each a little later, quieter, and darker than
    the one before, as a tape delay's repeats are."""
    n = _seconds(rate, length)
    t = np.arange(n) / rate

    def stab(cut_now):
        cutoff = base_cutoff(cut_now) * (1.0 + 2.5 * np.exp(-t / 0.05))
        notes = sum(additive(rate, np.full(n, freq * 2 ** (step / 12.0)), cutoff, 1.6, phase=step * 0.37) for step in (0, 3, 7, 10))
        return notes * envelope(n, rate, attack=0.002, release=0.02, decay=0.12)

    gap = max(int(rate * echo_seconds), 1)
    out = np.zeros(n + gap * echoes)
    for i in range(echoes + 1):
        out[i * gap:i * gap + n] += stab(cut - 1.2 * i) * feedback ** i
    return (np.tanh(out / 3.0)).astype(np.float32)


def stab(rate, piece, length, cut, accent=False):
    """A piece of the film's own sound (already tuned) made into a stab: cut to length with a quick fade, and passed
    through a low-pass that snaps open at the start and closes as it sounds; an accent opens it further."""
    x = np.asarray(piece, dtype=np.float64)[:_seconds(rate, length)]
    if len(x) < 256:
        return np.zeros(64, np.float32)
    size, hop = 1024, 256
    pad = np.concatenate([np.zeros(size), x, np.zeros(size)])
    window = np.hanning(size)
    freqs = np.fft.rfftfreq(size, 1.0 / rate)
    out, weight = np.zeros(len(pad)), np.zeros(len(pad))
    for start in range(0, len(pad) - size, hop):
        when = max(start - size, 0) / rate                         # time into the note at this frame
        cutoff = base_cutoff(cut) * (1.0 + (5.0 if accent else 2.5) * np.exp(-when / (0.05 if accent else 0.1)))
        frame = np.fft.irfft(np.fft.rfft(pad[start:start + size] * window) * lowpass_gain(freqs, cutoff, 1.8), size)
        out[start:start + size] += frame * window
        weight[start:start + size] += window ** 2
    out = (out / np.maximum(weight, 1e-6))[size:size + len(x)]
    out *= envelope(len(out), rate, attack=0.002, release=0.015, decay=0.35 if accent else 0.25) * (1.25 if accent else 1.0)
    peak = float(np.abs(out).max()) + 1e-9
    return (out / peak * 0.9).astype(np.float32)


SYNTHS = ("acid", "reese", "hoover", "dub")       # the signature synths: one a scene
VOICES = ("stab",) + SYNTHS
LEADS = ("auto", "film") + SYNTHS                  # what the lead may be told to play: as it comes, the film's sound alone, or one synth alone
