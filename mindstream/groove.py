"""A rhythm section made from nothing: kick, snare, hats, sub, a plucked synth and twinkling bells, synthesised
with numpy and rendered block by block at one tempo. Nothing is loaded and nothing is stored: every sound is
arithmetic, done again each time.

It is the floor under the session. It plays from the first second, before any picture or video exists,
and the generated video's soundtrack is played over it as a clip (see `duck`, which lets the kick push
the clip and the synths down, the way a dance record breathes).

What it plays is a SCORE: a drum style, a key, how much sub, how much twinkle, how much swing, and the riffs
themselves. `set_score` changes any of it and is heard from the next sixteenth note; `rescore` writes new
riffs and a new chord movement in the same key.

    g = Groove(bpm=160)
    block, duck = g.render(1024)      # float32 mono in -1..1, and the gain to apply to anything laid over it
    g.bpm = 150                       # from the next sixteenth; the beat never jumps
    g.energy = 0.8                    # 0 = kick and sub only ... 1 = everything
    g.set_score({"style": "twostep", "key": "F# dorian", "twinkle": 0.8, "rescore": True})
"""
import numpy as np

import collections
import math
import queue
import threading

from .kit import (colour, fade, fold, front, pitch_of, fx_chorus, fx_crush, fx_delay, fx_filter, fx_sweep, fx_tremolo, layer_wave, make_ir, repitch,
                  reverb, smear)
from . import bassline, deal, instruments, mangle, motif
from .parts import LAYERS, PARTS, QUICK, apply_op, change, fresh, sanitize, summary
from .score import NOTES, key_name, parse_key, style_name

RATE = 48000
MODES = {"minor": (0, 2, 3, 5, 7, 8, 10), "major": (0, 2, 4, 5, 7, 9, 11),
         "dorian": (0, 2, 3, 5, 7, 9, 10), "phrygian": (0, 1, 3, 5, 7, 8, 10)}
# Drum styles, on a bar of sixteen steps: where the kick, the snare (or clap) and the hats fall, where the sub
# plays (step, length in steps), and the swing the style has when none is asked for.
def _stand_back(lowest=False):
    """Called by a thread that makes sounds aside: it runs below everything else, so that when the machine is busy it
    is the making of a sound that waits, never the playing of one. (Windows only; elsewhere nothing is done.)"""
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadPriority(ctypes.windll.kernel32.GetCurrentThread(), -2 if lowest else -1)       # below normal: never so low it starves
    except Exception:
        pass


def _style(kick, snare, hat, open_hat=(), sub=(0,), swing=0.0, clap=False):
    """One drum style: the sixteenths (0 to 15) each drum falls on. Sub notes last until the next one."""
    steps = sorted(sub)
    lengths = [min(((steps[(i + 1) % len(steps)] - st - 1) % 16 + 1) * 0.95, 7.5) for i, st in enumerate(steps)] if steps else []
    return {"kick": tuple(kick), "snare": tuple(snare), "hat": tuple(hat), "open": tuple(open_hat), "sub": tuple(zip(steps, lengths)),
            "swing": swing, "clap": clap}


EIGHTHS, SIXTEENTHS = tuple(range(0, 16, 2)), tuple(range(16))
STYLES = {
    # the plain styles
    "four":    _style((0, 4, 8, 12), (4, 12), (2, 6, 10), (14,), sub=(2, 6, 10, 14), clap=True),
    "twostep": _style((0, 10), (4, 12), (2, 6, 8, 14), sub=(0, 7, 10), swing=0.28),
    "broken":  _style((0, 3, 10), (4, 13), (2, 6, 8, 10, 14), sub=(0, 3, 10), swing=0.12),
    "dnb":     _style((0, 10), (4, 12), (2, 6, 10, 14), sub=(0, 10)),      # the measured spine of jungle; the sixteenths between are dealt (deal.py)
    "half":    _style((0,), (8,), (2, 6, 10, 14), sub=(0, 11)),
    "none":    _style((), (), (), sub=(0,)),
    # the ten rhythmic archetypes of thelmic's rules (kick and snare are the anchors; closed and open hats are separate)
    "half_step":          _style((0, 8), (4, 12), EIGHTHS, sub=(0,)),
    "two_step":           _style((0, 6, 12), (4, 12), (0, 2, 4, 6, 8, 10, 12), (14,), sub=(2, 10)),
    "shuffled_two_step":  _style((0, 5, 8), (4, 12), (0, 5, 8, 10, 13), (3,), sub=(2, 11), swing=0.3),
    "stutter":            _style((0, 3, 8, 11), (4, 12), SIXTEENTHS, sub=(0, 3)),
    "rolling":            _style((0, 4, 10, 13), (4, 12), (0, 4, 6, 8, 12, 14), (2, 10), sub=(0, 12)),
    "breakbeat_hardcore": _style((0, 3, 7, 10), (4, 8, 12), (0, 2, 3, 5, 6, 8, 9, 11, 12, 13, 14), (4,), sub=(0, 12)),
    "amen":               _style((0, 3, 8, 10), (4, 7, 12), (0, 2, 3, 6, 8, 9, 10, 13, 14), (5, 12), sub=(0, 12)),
    "four_on_the_floor":  _style((0, 4, 8, 12), (4, 12), (0, 2, 4, 8, 10, 12), (6, 14), sub=(0, 4, 8, 12), clap=True),
    "happy_hardcore":     _style((0, 4, 8, 12), (4, 12), (0, 2, 6, 8, 10, 14), (4, 12), sub=(0, 4, 8, 12), clap=True),
    "gabber":             _style(SIXTEENTHS, (4, 12), EIGHTHS, (7, 15), sub=SIXTEENTHS, clap=True),
}
# where a part gains hits when asked to be busier, in this order, and the hits it never loses
ADD_ORDER = {"kick": (10, 6, 14, 3, 7, 11, 13, 5, 9, 15, 1, 2, 4, 8, 12), "snare": (12, 4, 7, 15, 10, 2, 13, 9, 5),
             "hats": (2, 6, 10, 14, 0, 4, 8, 12, 3, 7, 11, 15, 1, 5, 9, 13), "sub": (0, 8, 10, 2, 6, 12, 14, 4), "bass": (2, 10, 6, 14, 7, 3, 11, 15)}
ANCHORS = {"kick": (0,), "snare": (4, 12), "hats": (), "sub": (0,), "bass": ()}
# How the bass moves, one scale degree per bar (negative = below the root).
# What the music is built on. A change to one of these by the session is a change of structure: it waits for a
# four-bar line, and the structure is then left alone for a while (Groove.later).
STRUCTURAL = ("style", "key", "rescore", "break")
MOVEMENTS = ((0, 0, -2, -1), (0, 0, 0, 0), (0, -2, 0, -3), (0, 3, -2, -1), (0, 0, -3, -3), (0, -1, -2, -1))


def _kick(rate, length=1.0, punch=0.0):
    t = np.arange(int(rate * 0.45 * max(length, 0.5))) / rate
    freq = 58 + 120 * (1.0 + 1.2 * punch) * np.exp(-t / 0.028)         # punch: a bigger drop in pitch, so a harder knock. It comes to rest
    # at 58 Hz, not lower: the kick's body is kept above the sub, which has everything below to itself
    body = np.sin(2 * np.pi * np.cumsum(freq) / rate) * np.exp(-t / (0.11 * length))
    # the knock on the front: it rises over a millisecond and is gone in a few (a bare step here is heard as a click,
    # not as a knock), and there is only much of it when punch is asked for
    click = (1.0 - np.exp(-t / 0.0007)) * np.exp(-t / 0.004) * 0.3 * (0.5 + 2.5 * punch)
    out = np.tanh(1.6 * (body + click))
    tail = min(int(rate * 0.06), len(out) // 3)                        # it dies away to nothing: a kick cut off short ticks at its end
    out[-tail:] *= np.cos(np.linspace(0.0, np.pi / 2, tail)) ** 2
    return out.astype(np.float32)


def _noise(rate, seconds, decay, rng, bright=True):
    n = int(rate * seconds)
    x = rng.standard_normal(n + 1)
    x = np.diff(x) if bright else (x[1:] + x[:-1]) * 0.5       # a crude high-pass or low-pass
    return (x * np.exp(-np.arange(n) / rate / decay)).astype(np.float32)


def _clap(rate, rng):
    out = np.zeros(int(rate * 0.25), np.float32)
    for delay, level in ((0.0, 0.6), (0.011, 0.7), (0.023, 1.0)):       # three hands, not quite together
        burst = _noise(rate, 0.2, 0.045, rng) * level
        start = int(rate * delay)
        out[start:start + len(burst)] += burst[:len(out) - start]
    return out * 0.5


def _snare(rate, rng):
    t = np.arange(int(rate * 0.2)) / rate
    body = np.sin(2 * np.pi * (185 + 60 * np.exp(-t / 0.01)) * t) * np.exp(-t / 0.05) * 0.7
    return (body + _noise(rate, 0.2, 0.06, rng) * 0.45).astype(np.float32)


def _sub(rate, freq, seconds, slide_from=None):
    """The sub: a clean sine. Each note starts two and a half octaves high and falls to its pitch in a few hundredths
    of a second, which is the knock at the front of it; then it is only the low note, a touch warmed so that it can
    be found on small speakers. A note that slides (slide_from, the pitch it comes from) is not struck again: it
    glides from that pitch to its own, most of the way in eighty milliseconds."""
    n = max(int(rate * seconds), 256)
    t = np.arange(n) / rate
    if slide_from:
        glide = freq + (float(slide_from) - freq) * np.exp(-t / 0.027)
    else:
        glide = freq * 2.0 ** (2.5 * np.exp(-t / 0.012))
    out = np.sin(2 * np.pi * np.cumsum(glide) / rate)
    out = np.tanh(1.25 * out) / np.tanh(1.25) * np.exp(-t / max(seconds * 2.5, 0.25))
    edge, tail = min(n // 4, int(rate * 0.003)), min(n // 3, int(rate * 0.015))
    out[:edge] *= np.linspace(0, 1, edge)
    out[-tail:] *= np.linspace(1, 0, tail)
    return out.astype(np.float32)


def _tone(rate, freq, seconds, harmonics, decay):
    t = np.arange(max(int(rate * seconds), 16)) / rate
    out = np.zeros(len(t))
    for k in range(1, harmonics + 1):
        if freq * k < rate * 0.45:
            out += np.sin(2 * np.pi * freq * k * t) / k * np.exp(-t * k / decay)
    edge = min(len(t) // 2, int(rate * 0.004))
    out[:edge] *= np.linspace(0, 1, edge)
    out[-edge:] *= np.linspace(1, 0, edge)
    return out.astype(np.float32)


def _bell(rate, freq):
    """A small struck bell: the note, and two partials that are not quite in tune with it."""
    t = np.arange(int(rate * 0.7)) / rate
    out = (np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.22) + 0.45 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t / 0.09)
           + 0.25 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t / 0.04))
    out[:int(rate * 0.001)] *= np.linspace(0, 1, int(rate * 0.001))
    return out.astype(np.float32)


class Groove:
    def __init__(self, bpm=120.0, rate=RATE, energy=0.5, seed=None):
        self.rate, self.bpm, self.energy = rate, float(bpm), float(energy)
        self.rng = np.random.default_rng(seed)
        self.pos = 0                      # samples rendered so far
        self.step = 0                     # sixteenths triggered so far
        self.next_step = 0.0              # sample position of the next sixteenth
        self.step_len = 15.0 * rate / self.bpm     # samples in the sixteenth now playing
        self.last_kick = -10 * rate
        self.kick_at, self.steps = [], []
        self.voices = []                  # [samples, how far in, level, is it ducked by the kick]
        self.kick, self.hat, self.clap = _kick(rate), _noise(rate, 0.06, 0.012, self.rng), _clap(rate, self.rng)
        self.open_hat, self.snare = _noise(rate, 0.25, 0.07, self.rng), _snare(rate, self.rng)
        self.notes = {}                   # tones already worked out, by (kind, pitch, length)
        # the score
        self.style, self.note, self.mode = "four", "a", "minor"
        self.swing, self.sub, self.twinkle = None, 0.8, 0.0            # swing None = whatever the style has; the bells rest unless asked for
        # how bars are dealt (deal.py): the numbers the drums, the sub's riff and the hooks are dealt from; whether the
        # riff and the hook were made by hand (then they stay, instead of turning over on their own clocks); the parts
        # whose pattern was written by hand (they play exactly as written); and the bar last dealt
        self.deal_seed, self.sub_seed, self.hook_seed = (int(x) for x in self.rng.integers(0, 2 ** 31, size=3))
        self.sub_held, self.hook_held, self.by_hand = False, False, set()
        self.dealt, self.break_shape = (-1, None, []), None
        self.scores = 0
        self.break_start, self.break_end = 0, 0                        # a breakdown runs between these sixteenths
        # The tune and the drones are played, by first choice, on pieces of the films' own sound (kit.py); the
        # synthesised tones are for before there is any. Kick, snare, hats and sub are always synthesised.
        self.kit, self.kit_id, self.room = [], 0, make_ir(rate)
        # Each part has a name, and its own sound that can be changed without touching what it plays (parts.py):
        # level, dirt, room, brightness, octave, length, on or off. `hits` is when each last sounded.
        self.parts = {name: fresh() for name in PARTS if name not in LAYERS}
        # the lead (the part called "tune"): its hook is carried by the film's own sound, cut into tuned stabs, when there
        # is film sound; and in turn with it by the scene's one signature synth (instruments.py), chosen once a scene
        self.signature, self.lead_cache = int(self.rng.integers(0, len(instruments.SYNTHS))), {}
        self.lead_choice = "auto"                      # or "film", or one of the synths: chosen by hand (!lead acid), and kept
        self.rev = {name: 0 for name in self.parts}
        self.hits = {name: -10 ** 6 for name in self.parts}
        self.drums, self.building = {}, set()
        self.last = {}                    # each sound as it was last made, to play while a changed one is being built
        # ducking: where each part last sounded and is about to (in samples since the start), and for the block being
        # made, how long ago that was at every sample
        self.struck, self.last_hit, self.since = {}, {}, {}
        self.one_at_a_time = threading.Lock()         # sounds are rebuilt one after another: many at once starve the sound's own thread
        # and they are built by one worker, from a queue (a thread for every note, as before, could mean dozens at once)
        self.jobs = queue.Queue()
        self.urgent = collections.deque()               # the sub's notes: made before anything else waiting (a missed sub is a hole in the bar)
        threading.Thread(target=self._work, name="sound maker", daemon=True).start()
        self.played = collections.deque(maxlen=900)      # (sixteenth, part, pitch or None): for the roll the viewer draws
        # What was really played, for whatever measures the music as it goes: (sixteenth, part, MIDI note or None),
        # one for every onset of the sub, the bass and the tune (with the note as it sounds, the part's octave and
        # pitch knobs included), and of the kick and the snare (None; ghost snares, fills and rolls are "snare" too).
        # Only what sounded: a part switched off or turned right down is not here.
        self.heard = collections.deque(maxlen=4096)
        # Which version of the riff and the hook each bar plays (bassline.riff, motif.motif). Development (one kept
        # mutation every eight bars, a riff's fate at the end of its run, the B riff, A back changed) is another
        # thing's to decide: set `develop` to an object with versions(bar) -> (riff version, motif version),
        # hole(bar, lane) -> is the riff ("riff") or the hook ("hook") out for that bar, and drums(bar) -> (material,
        # numbers) for deal.held_bar; all quick (asked from the sound's thread: looked up, never worked out) and the
        # same every time they are asked about the same bar (course.py is the mixer's). Left None, `_versions` keeps a
        # plain schedule and the drums are dealt by the section count.
        self.develop = None
        self.riff_cache, self.bar_cache, self.motif_cache, self.hook_cache, self.sub_semis = {}, {}, {}, {}, 0
        # an outside composer (composer.py: thelmic) writes sixteen bars at a time; without one, the patterns below play
        self.composer, self.archetype, self.bank, self.bank_origin, self.bank_index, self.bank_energy = None, None, None, 0, 0, 0.0
        # what the drums, sub and bass play: taken from the style, then yours to change live (edit_pattern, patch)
        self.pattern, self.fill_bar = {}, -1
        self.tune_every = None            # how often the tune plays, in sixteenths: None = as the energy has it, else 1, 2 or 4
        # structure: changes the session has asked for that wait for a four-bar line; the sixteenth the structure last
        # changed on; and for how many bars it is then left alone by the session
        self.waiting, self.waiting_lock, self.changed_at, self.structure_bars = {}, threading.Lock(), -10 ** 6, 8
        # the opening: until the scene is set there is only the kick, as a heartbeat (two thumps close together, then a
        # wait). `scene_set` is said by whoever knows (the viewer, on the first picture); the music then comes in on
        # the next bar line
        self.opening, self.scene_set = True, False
        self.load_pattern()
        self.rescore()

    # ------------------------------------------------------------------ the score

    def _draw_score(self):
        """The numbers the next new score will be made from. Drawn a score ahead, so that what a change waiting for
        the four-bar line will play can be made before the line comes (see _after)."""
        return {"riff": [int(x) for x in self.rng.choice([0, 2, 4, 7, 9, 11, 14], size=16)],        # the pluck, in scale steps
                "bells": [int(x) for x in self.rng.choice([0, 2, 4, 6, 7, 9, 11], size=16)],        # the twinkle
                "bell_order": [float(x) for x in self.rng.random(16)],      # which steps ring first as twinkle rises
                "movement": MOVEMENTS[int(self.rng.integers(0, len(MOVEMENTS)))],
                "sub_seed": int(self.rng.integers(0, 2 ** 31)), "hook_seed": int(self.rng.integers(0, 2 ** 31)),
                "signature": int(self.rng.integers(0, len(instruments.SYNTHS)))}       # a new scene: a new signature synth

    def rescore(self):
        """New riffs and a new movement for the bass, in the same key and style."""
        coming = getattr(self, "coming", None) or self._draw_score()
        self.coming = self._draw_score()
        for name, value in coming.items():
            setattr(self, name, value)
        self.sub_held, self.hook_held = False, False
        self.scores += 1

    def _after(self, changes):
        """What `set_score(changes)` would make of the things a bar's notes are made from, without making it so:
        {attribute: value}. So that the first bar after a change waiting for the four-bar line is made ahead like any
        other (a note made as it is played was a dropout)."""
        out, fresh, keep = {}, bool(changes.get("rescore")), bool(changes.get("keep_patterns"))
        style = style_name(changes.get("style", ""))
        if style in STYLES and style != self.style:
            out.update(style=style, pattern=self._style_pattern(style), by_hand=set())
            fresh = True
        key = parse_key(changes["key"]) if changes.get("key") else None
        if key and key != (self.note, self.mode):
            out["note"], out["mode"] = key
            fresh = not keep
        try:
            out["energy"] = min(max(float(changes["energy"]), 0.0), 1.0)
        except (KeyError, TypeError, ValueError):
            pass
        if fresh:
            out.update({name: self.coming[name] for name in ("movement", "sub_seed", "hook_seed", "signature")},
                       sub_held=False, hook_held=False, scores=self.scores + 1)
        return out

    def _prepare_as(self, changes, number):
        """_prepare, as things will stand once `changes` (from _after) are made. Done in the sound's own thread, and
        put back before anything else of it runs."""
        kept = {name: getattr(self, name) for name in changes}
        try:
            for name, value in changes.items():
                setattr(self, name, value)
            self._prepare(number)
        finally:
            for name, value in kept.items():
                setattr(self, name, value)

    def use_composer(self, composer, log=None):
        self.composer, self.log = composer, log
        self._compose("steady", self.step - self.step % 16)

    def _compose(self, phase, origin):
        """Ask the composer for sixteen bars from `origin` (a sixteenth-note count), as things stand now."""
        if self.composer is None:
            return
        from .composer import ARCHETYPES, STYLE_TO_ARCHETYPE
        name = self.style if self.style in ARCHETYPES else STYLE_TO_ARCHETYPE.get(self.style, "four_on_the_floor")
        if self.style == "dnb":                       # jungle, where thelmic has it (else the composer falls back to the amen)
            name = "jungle"
        try:
            bank = self.composer.bank(self.bank_index, name, self.energy, 28 + (NOTES[self.note] - 4) % 12, phase)
        except Exception as e:                        # the composer must never stop the sound
            self.composer, self.bank = None, None
            if getattr(self, "log", None):
                self.log(f"composer stopped ({type(e).__name__}: {e}); playing the built-in patterns")
            return
        self.bank, self.bank_origin, self.bank_energy = bank, origin, self.energy

    def _low(self):
        """The root the low notes are counted from, as a MIDI note: between E1 (41 Hz) and D#2 (78 Hz)."""
        return 28 + (NOTES[self.note] - 4) % 12

    def _snap(self, midi):
        """A pitch moved to the nearest note of the key and mode now in force."""
        low = 28 + (NOTES[self.note] - 4) % 12
        octave, within = divmod(midi - low, 12)
        nearest = min(MODES[self.mode], key=lambda degree: (abs(degree - within), degree))
        return octave * 12 + nearest               # semitones above the low root

    def _play(self, event, at):
        layer, note, velocity, length = event
        level = velocity / 127.0
        if layer == "kick":
            if self.style != "none" and self._add("kick", self._drum("kick"), at, 0.95 * level):
                self.kick_at.append(max(at, 0))
        elif layer == "snare":
            if self.style != "none":
                self._add("snare", self._drum("clap" if self.style == "four" else "snare"), at, 0.5 * level)
        elif layer in ("hat", "open_hat") or layer.startswith("ghost"):
            if self.style != "none":
                quiet = 0.4 if layer.startswith("ghost") else 1.0
                if note == 38:
                    self._add("snare", self._drum("snare"), at, 0.3 * level * quiet)
                else:
                    self._add("hats", self._drum("open_hat" if note == 46 else "hat"), at, 0.3 * level * quiet)
        elif layer == "sub":
            if self.sub > 0.02:
                self._add("sub", self._note("sub", self._snap(note + 12), min(max(length, 3.7), 8.0)), at, 1.05 * self.sub * level, True,
                          pitch=note, midi=self._low() + self._snap(note + 12))     # held nearly to the next beat: a sub that is there, not a blip
        elif layer == "bass":
            self._add("bass", self._note("bass", self._snap(note), min(length, 6.0)), at, 0.3 * level, True, pitch=note,
                      midi=self._low() + self._snap(note))
        elif layer.startswith("drone"):
            self._add("drones", self._note("drone", self._snap(note), min(length, 64.0)), at, 0.07 * level, True, pitch=note)
        else:                                         # hook, call, response: the tune
            self._add("tune", self._note("pluck", self._snap(note + 12), max(length, 1.5)), at, (0.3 if self.kit else 0.2) * level, True,
                      pitch=note, midi=self._low() + self._snap(note + 12))

    def _bells(self, step, at):
        """The bells, sparingly: only in every other bar, and only a few of its steps even when asked for a lot."""
        s = step % 16
        if self.twinkle > 0.02 and (step // 16) % 2 == 0 and self.bell_order[s] < self.twinkle * 0.3:
            bell = self._note("bell", 36 + self._pitch(self.bells[s]))    # an octave lower than they were: high bells read as sweet
            self._add("bells", bell, at, 0.09 + 0.04 * self.twinkle, pitch=self._pitch(self.bells[s]))
            if self.twinkle >= 0.6:                                    # a short echo (an eighth triplet), only when there are plenty
                self._add("bells", bell, at + int(self.step_len * 4 / 3), 0.04)

    def _trigger_composed(self, step, at):
        if step - self.bank_origin >= 256:            # the sixteen bars are up: the composer writes the next
            self.bank_index += 1
            self._compose("steady", step)
        left = self.break_end - step
        if left == 0 and self.break_end > self.break_start:        # the drop
            self.voices.append([_noise(self.rate, 1.4, 0.4, self.rng), -at, 0.35, False])
            self.break_start = self.break_end
            self.bank_index += 1
            self._compose("drop", step)
        elif left > 0 and left == min(32, self.break_end - self.break_start):
            n = int(left * self.step_len)
            self.voices.append([(self.rng.standard_normal(n) * (np.arange(n) / n) ** 2).astype(np.float32), -at, 0.16, False])
        elif step % 16 == 0 and left <= 0 and abs(self.energy - self.bank_energy) > 0.12:
            self._compose("steady", self.bank_origin)                # fuller or sparser, from the next bar line
        if self.bank is None:
            return
        position = (step - self.bank_origin) % 256
        swing = 0.0 if self.swing is None else self.swing
        late = int(swing * self.step_len) if step % 2 == 1 else 0
        for half in (0, 1):
            for event in self.bank.get(position * 2 + half, ()):
                if left > 32 and event[0] in ("kick", "snare", "bass", "sub"):
                    continue          # a break: drums and bass out, until the composer's own build in the last two bars
                self._play(event, at + late + half * int(self.step_len / 2))
        self._bells(step, at)

    def later(self, changes):
        """Changes of structure asked for by the session (style, key, new riffs, a break): not made now. They are made
        together on the next four-bar line, and no sooner than `structure_bars` after the structure last changed, by
        anyone. Asked for again before then, the latest of each stands. A change made by hand (set_score) is made at
        once and takes the place of one waiting."""
        with self.waiting_lock:
            self.waiting.update(changes)

    def _structure_due(self):
        """On a sixteenth, from the sound's own thread: is this the four-bar line the waiting changes land on?"""
        if not self.opening and self.step % 64 == 0 and self.step - self.changed_at >= self.structure_bars * 16:
            with self.waiting_lock:
                due, self.waiting = self.waiting, {}
            self.set_score(due)

    def set_score(self, changes):
        """Apply any of: style, key, swing, sub, twinkle, energy, bpm, rescore. Unknown or bad values are ignored.
        Heard from the next sixteenth. Returns what actually changed, as text."""
        said = []
        if self.waiting:                              # the same thing asked for by the session, and waiting: this replaces it
            with self.waiting_lock:
                for key in changes:
                    self.waiting.pop(key, None)
        style = style_name(changes.get("style", ""))
        fresh, keep = bool(changes.get("rescore")), bool(changes.get("keep_patterns"))
        if style in STYLES and style != self.style:
            self.style, fresh = style, True
            self.load_pattern()                       # a new style starts from its own pattern, as written
            said.append(f"style {style}")
        key = parse_key(changes["key"]) if changes.get("key") else None
        if key and key != (self.note, self.mode):
            self.note, self.mode = key                # (the notes made are kept by root as well: those of the new key may be ready)
            fresh = not keep                          # riffs made by hand move to the new key as they are (they are in scale steps)
            said.append(f"key {self.key()}")
        for name, low, high in (("sub", 0.0, 1.0), ("twinkle", 0.0, 1.0), ("swing", 0.0, 0.5), ("energy", 0.0, 1.0), ("bpm", 40.0, 300.0)):
            try:
                value = min(max(float(changes[name]), low), high)
            except (KeyError, TypeError, ValueError):
                continue
            if getattr(self, name) is None or abs(value - getattr(self, name)) > 1e-6:
                setattr(self, name, value)
                said.append(f"{name} {value:g}")
        if fresh:
            self.rescore()
            said.append("new riffs")
            if self.composer is not None:
                self.composer.seed += 1 if changes.get("rescore") else 0
                self._compose("steady", self.bank_origin)
        try:
            if float(changes.get("break", 0)) >= 1:
                said.append(f"break for {self.start_break(int(min(float(changes['break']), 32)))} bars")
        except (TypeError, ValueError):
            pass
        if any(what.startswith(("style", "key", "new riffs", "break")) for what in said):
            self.changed_at = self.step               # the structure has just changed: the session leaves it alone for a while
        return ", ".join(said)

    def start_break(self, bars=4):
        """A break, from now: the low end is taken away (the sub and the bass go, the kick falls back) while the drums
        keep running, busier if anything. Nothing rises and nothing crashes: the low end comes back on a bar line."""
        self.break_start = self.step
        self.break_end = (self.step // 16 + 1 + max(1, bars)) * 16     # the rest of this bar, then `bars` more
        if self.composer is not None:                 # the composer's own last bars before a drop, ending on that bar line
            self._compose("build", self.break_end - 256)
        return max(1, bars)

    def key(self):
        return key_name((self.note, self.mode))

    # ------------------------------------------------------------------ where we are

    def beat(self):
        """Beats since the start, as a fraction (4 per bar): the clock the visuals follow."""
        behind = (self.next_step - self.pos) / self.step_len                       # sixteenths until the next one
        return (self.step - behind) / 4.0

    def next_bar(self):
        """Sample position where the next bar starts: the moment to launch a clip so it lands on the one."""
        steps = (-self.step) % 16
        return int(self.next_step + steps * 15.0 * self.rate / self.bpm)

    # ------------------------------------------------------------------ what plays

    def _pitch(self, degree):
        """Semitones above the root for a scale degree; degrees run on past the octave, and below it."""
        scale = MODES[self.mode]
        return scale[degree % 7] + 12 * (degree // 7)

    def set_kit(self, tones):
        """Pieces of a new film's sound to play the tune on (a list of short mono sounds), added to those from the
        last few films. None forgets them all, and the synthesised tones return."""
        self.kit = [] if tones is None else (self.kit + list(tones))[-8:]
        # the note each piece is actually sounding, so that a tune played on it is in tune (None: no clear pitch)
        self.kit_pitch = [pitch_of(piece, self.rate) for piece in self.kit]
        self.kit_id += 1
        self.notes.clear()

    def set_drum(self, part, sound):
        """A drum hit pulled from a sample library takes the place of the synthesised one (None puts it back)."""
        made = {"kick": {"kick": _kick(self.rate)}, "snare": {"snare": _snare(self.rate, self.rng), "clap": _clap(self.rate, self.rng)},
                "hats": {"hat": _noise(self.rate, 0.06, 0.012, self.rng), "open_hat": _noise(self.rate, 0.25, 0.07, self.rng)}}[part]
        for name in made:
            if sound is None:
                setattr(self, name, made[name])
            else:
                setattr(self, name, np.asarray(sound[:int(self.rate * 0.09)] if name == "hat" and len(sound) > self.rate * 0.12 else sound, np.float32))
        self.pulled = {**getattr(self, "pulled", {}), part: sound is not None}
        self.rev[part] += 1
        self.drums.clear()

    @staticmethod
    def _style_pattern(name):
        style = STYLES[name]
        return {"kick": list(style["kick"]), "snare": list(style["snare"]), "hats": list(style["hat"]), "open": list(style["open"]),
                "sub": [st for st, _ in style["sub"]],
                "bass": sorted({(st + 2) % 16 for st, _ in style["sub"]} - set(style["kick"]))[:4]}

    def load_pattern(self):
        """The pattern as the style has it: which sixteenths the kick, snare, closed and open hats, sub and bass fall on."""
        self.by_hand = set()
        self.pattern = self._style_pattern(self.style)

    def edit_pattern(self, part, how):
        """Change what a part plays, live: "busier", "sparser", "double", "half", "vary", "fill", "reset". The anchors
        (the kick on the one, the snare's backbeat) stay. Returns what it did, as text."""
        if how == "mutate":
            return self.mutate(part)
        if part == "tune" and how in ("busier", "sparser", "double", "half", "reset"):     # the tune has no steps of its own: it is played more or less often
            now = self.tune_every or 3
            self.tune_every = None if how == "reset" else max(now // 2, 1) if how in ("busier", "double") else min(now * 2, 4)
            return "tune: hooks in " + {None: "three", 1: "six", 2: "four", 4: "two"}[self.tune_every] + " bars of every eight"
        if part == "bells" and how in ("busier", "sparser", "double", "half"):             # the bells ring more or less often
            self.twinkle = min(max(self.twinkle + (0.2 if how in ("busier", "double") else -0.2), 0.0), 1.0)
            return f"bells: ringing {'more' if how in ('busier', 'double') else 'less'} often"
        if part not in ADD_ORDER:
            return ""
        steps, style = self.pattern[part], STYLES[self.style]
        keep = [x for x in ANCHORS[part] if x in steps]
        if how == "reset":
            self.by_hand.discard(part)                 # as the style writes it: dealt again, like the rest
        elif how != "fill":
            self.by_hand.add(part)                     # written by hand: from now on it plays exactly as written
        if how == "busier":
            new = next((x for x in ADD_ORDER[part] if x not in steps and not (part == "hats" and x in self.pattern["open"])), None)
            if new is not None:
                steps.append(new)
        elif how == "sparser":
            loose = [x for x in steps if x not in keep]
            if loose:
                order = [x for x in ADD_ORDER[part] if x in loose] or loose
                steps.remove(order[-1])
        elif how == "double":
            steps[:] = sorted(set(steps) | {(x + (1 if part == "hats" else 2)) % 16 for x in steps})
        elif how == "half":
            steps[:] = sorted(set(steps[::2]) | set(keep))
        elif how == "vary":
            loose = [x for x in steps if x not in keep]
            if loose:
                old = loose[int(self.rng.integers(0, len(loose)))]
                free = [x for x in ((old + d) % 16 for d in (1, -1, 2, -2, 3)) if x not in steps]
                if free:
                    steps[steps.index(old)] = free[0]
        elif how == "fill":
            self.fill_bar = self.step // 16 + (1 if self.step % 16 else 0)        # the next whole bar ends in a roll
            return f"{part}: a fill at the end of the next bar"
        elif how == "reset":
            fresh = {"kick": style["kick"], "snare": style["snare"], "hats": style["hat"], "sub": [st for st, _ in style["sub"]]}
            steps[:] = list(fresh.get(part, steps))
            if part == "hats":
                self.pattern["open"] = list(style["open"])
            if part == "bass":
                steps[:] = sorted({(st + 2) % 16 for st, _ in style["sub"]} - set(style["kick"]))[:4]
        steps.sort()
        return f"{part} {how}: now on sixteenths " + (", ".join(str(x + 1) for x in steps) or "nothing")

    def mutate(self, part):
        """A new pattern for one part, from the one it has: a drum's loose hits move (its anchors stay), the bass
        and the drones take a new movement of roots, the tune a new riff, the bells new notes in a new order."""
        if self.composer is not None:
            return f"{part}: its part is written by thelmic, sixteen bars at a time, and cannot be changed by hand"
        if part == "tune":                             # the hook playing now, replaced by its relative (never a stranger), held
            self.riff = [int(x) for x in self.rng.choice([0, 2, 4, 7, 9, 11, 14], size=16)]
            version = dict(self._versions(self.step // 16)[1])
            self.hook_held = tuple(sorted({**version, "gen": int(version.get("gen", 0)) + 1}.items()))
            return "tune: the hook's relative, and it stays until you change it"
        if part == "bells":
            self.bells = [int(x) for x in self.rng.choice([0, 2, 4, 6, 7, 9, 11], size=16)]
            self.bell_order = [float(x) for x in self.rng.random(16)]
            return "bells: new notes, in a new order"
        if part == "drones":
            return "drones: they rest unless thelmic is writing the parts, so there is nothing of theirs to change"
        if part in ("bass", "sub"):                    # the notes of the low end are the roots it moves through
            others = [m for m in MOVEMENTS if m != self.movement] or MOVEMENTS
            self.movement = others[int(self.rng.integers(0, len(others)))]
            if self._written():                        # the riff playing now, changed in one thing (a kept mutation), and held
                version = self._versions(self.step // 16)[0]
                version = {"gen": version} if not isinstance(version, dict) else dict(version)
                self.sub_held = tuple(sorted({**version, "gen": int(version.get("gen", 0)) + 1}.items()))
                if part == "sub":
                    return "sub: the riff changed in one thing, and it stays until you change it (the bass follows it)"
            else:
                self.sub_seed, self.sub_held = int(self.rng.integers(0, 2 ** 31)), True     # a new riff for the sub, which stays
        if part not in ADD_ORDER:
            return ""
        steps = self.pattern[part]
        loose = [x for x in steps if x not in ANCHORS[part]]
        if not loose:                                  # nothing free to move: one more hit, then it has something
            self.edit_pattern(part, "busier")
        for _ in range(max(2, len(loose) // 2)):
            self.edit_pattern(part, "vary")
        steps.sort()
        return (f"{part}: a new pattern, on sixteenths " + (", ".join(str(x + 1) for x in steps) or "nothing")
                + (", and a new movement of roots (the sub, the bass and the tune all follow it)" if part in ("bass", "sub") else ""))

    def set_parts(self, pairs):
        """Change parts by word: how one sounds ("bass", "dirtier"), or what it plays ("hats", "busier"). Returns
        what was done, as text."""
        from .parts import WORDS
        said = []
        for part, word in pairs:
            if part in self.parts and WORDS.get(word, ("",))[0] == "pattern":
                said.append(self.edit_pattern(part, WORDS[word][1][1]) or f"{part}: its pattern is not one that can be edited")
            elif part in self.parts:
                change(self.parts[part], word)
                self.rev[part] += 1
                said.append(f"{part} {word}")
        return ", ".join(said)

    def patch(self, ops):
        """Open changes to how parts sound: effects, extra layers, any setting (see parts.sanitize for the forms).
        Returns the operations that were taken."""
        taken = [op for op in sanitize(ops) if op["part"] in self.parts]
        for op in taken:
            if "steps" in op:                         # exactly which sixteenths the part plays on
                self.pattern[op["part"]] = list(op["steps"])
                self.by_hand.add(op["part"])
                if "open" in op:
                    self.pattern["open"] = list(op["open"])
                continue
            apply_op(self.parts[op["part"]], op)
            if not set(op.get("set", {"*": 0})) <= QUICK:           # its volume and its ducking are heard at once: nothing is made again
                self.rev[op["part"]] += 1
        return taken

    def _seconds(self, value):
        """A note length such as "3/16", at the tempo now, or a plain number of seconds."""
        if isinstance(value, str) and "/" in value:
            a, b = value.split("/")
            return float(a) / float(b) * 240.0 / self.bpm
        return float(value)

    def _finish(self, sound, settings, freq):
        """What has been added to a part: extra layers under or over its sound, then its colour, then its
        effects in the order they were asked for."""
        rng = np.random.default_rng(abs(hash(round(freq, 2))) % (2 ** 32))
        for layer in settings["layers"]:
            extra = layer_wave(self.rate, layer["wave"], freq * 2.0 ** (layer["octave"] + layer["detune"] / 1200.0),
                               max(len(sound) / self.rate, 0.08), layer["decay"], rng) * layer["level"]
            mixed = np.zeros(max(len(sound), len(extra)), np.float32)
            mixed[:len(sound)] += sound
            mixed[:len(extra)] += extra.astype(np.float32)
            sound = mixed
        sound = front(sound, self.rate, settings["attack"], 0.0 if 50.0 < freq < 60.0 else settings["punch"])    # the kick's punch is in its making
        sound = colour(sound, self.rate, settings["tone"], settings["drive"])
        for fx in settings["fx"]:
            kind = fx["type"]
            if kind == "delay":
                sound = fx_delay(sound, self.rate, self._seconds(fx["time"]), fx["feedback"], fx["mix"])
            elif kind == "chorus":
                sound = fx_chorus(sound, fx["depth"], fx["mix"])
            elif kind == "crush":
                sound = fx_crush(sound, fx["bits"], fx["rate"])
            elif kind == "tremolo":
                sound = fx_tremolo(sound, self.rate, self._seconds(fx["time"]), fx["depth"])
            elif kind == "filter":
                sound = fx_filter(sound, self.rate, fx["kind"], fx["freq"], fx.get("q", 0.0))
            elif kind == "sweep":
                sound = fx_sweep(sound, self.rate, fx["from"], fx["to"], self._seconds(fx["time"]))
            elif kind == "reverse":
                sound = np.ascontiguousarray(sound[::-1])
        if settings.get("filth", 0.0) > 0.005:        # the part's knob: how far it is pushed into damage, in its own character
            sound = mangle.one(sound, self.rate, settings["filth"], settings.get("patch"))
        return sound[:int(self.rate * 10)]

    def describe_parts(self):
        """Each part by name: what it is, how it has been changed, and whether it sounded in the last bar."""
        kind = {"four": "four on the floor", "twostep": "2-step", "broken": "broken beat", "dnb": "drum and bass",
                "half": "half-time", "none": "no drums"}.get(self.style, self.style).replace("_", " ")
        composed = self.composer is not None
        doing = {
            "kick": kind, "snare": "backbeat" if self.style != "none" else "resting", "hats": "ticking" if self.style != "none" else "resting",
            "sub": f"deep {self.note.capitalize()}" + ("" if self.sub > 0.02 else " (turned off)"),
            "bass": ("twin saws, with the kick" if composed else "twin saws, on the steps written for them" if not self._written() or "bass" in self.by_hand
                     else "twin saws, answering in the sub's rests" if self._riff(self.step // 16).get("bass") == "answer" else "resting: the sub alone in this riff"),
            "tune": (f"the hook: the films' own sound as stabs ({len(self.kit)} piece{'s' if len(self.kit) != 1 else ''}), in turn with the {instruments.SYNTHS[self.signature % len(instruments.SYNTHS)]}"
                     if self.kit else f"the hook on the {instruments.SYNTHS[self.signature % len(instruments.SYNTHS)]} (no film sound yet)"),
            "bells": "a few, every other bar" if self.twinkle > 0.02 else "resting",
            "drones": ("the films' sound, smeared" if self.kit else "detuned tones") if composed else "resting (thelmic plays them)",
        }
        return [{"name": name, "doing": doing[name], "changed": summary(self.parts[name]),
                 "playing": self.step - self.hits[name] <= 16 and self.parts[name]["on"]} for name in self.parts]

    def roll(self, now, window=32):
        """The parts as a roll: for the two bars around `now` (in sixteenths), where each part has sounded, and
        where it is about to. Each row is {"name", "playing", "changed", "cells": [(offset, length, pitch, coming)]}.
        What is coming is exact when a composer has written the bars, and otherwise the last two bars again."""
        start = int(now // window) * window
        cells = {name: [] for name in self.parts}
        for step, part, pitch in list(self.played):
            if start <= step < start + window and step <= now + 2:
                cells[part].append((step - start, 1.0, pitch, False))
        ahead = int(now) + 2
        if self.composer is not None and self.bank is not None:
            where = {"kick": "kick", "snare": "snare", "hat": "hats", "open_hat": "hats", "sub": "sub", "bass": "bass"}
            for step in range(max(ahead, start), start + window):
                position = (step - self.bank_origin) % 256
                for half in (0, 1):
                    for layer, note, _, length in self.bank.get(position * 2 + half, ()):
                        part = "drones" if layer.startswith("drone") else "hats" if layer.startswith("ghost") else where.get(layer, "tune")
                        if self.parts[part]["on"] and not (self.style == "none" and part in ("kick", "snare", "hats")):
                            cells[part].append((step - start + half / 2.0, min(max(length, 1.0), 8.0),
                                                None if part in ("kick", "snare", "hats") else note, True))
        elif self.opening:                                              # only the heartbeat is coming
            every, second = self.heart()
            for step in range(max(ahead, start), start + window):
                if step % every in (0, second) and self.parts["kick"]["on"]:
                    cells["kick"].append((step - start, 1.0, None, True))
        else:
            for step in range(max(ahead, start), start + window):       # the drums: exactly what the pattern has coming
                at = step % 16
                for part, steps in (("kick", self.pattern["kick"]), ("snare", self.pattern["snare"]), ("hats", self.pattern["hats"] + self.pattern["open"])):
                    if at in steps and self.parts[part]["on"]:
                        cells[part].append((step - start, 1.0, None, True))
            for number in range(max(ahead, start) // 16, (start + window - 1) // 16 + 1):     # the sub and the bass: what they will play
                for part, notes in self.low_ahead(number).items():
                    for at, pitch, length in notes:
                        step = number * 16 + at
                        if max(ahead, start) <= step < start + window and self.parts[part]["on"]:
                            cells[part].append((step - start, 1.0, pitch, True))
            for step, part, pitch in list(self.played):                 # the tune and the bells: the last two bars again
                if part in ("tune", "bells", "drones") and start - window <= step < start and step + window >= ahead and self.parts[part]["on"]:
                    cells[part].append((step + window - start, 1.0, pitch, True))
        return [{"name": name, "changed": summary(self.parts[name]), "cells": cells[name],
                 "playing": self.step - self.hits[name] <= 16 and self.parts[name]["on"]} for name in self.parts]

    HEARD = ("kick", "snare", "sub", "bass", "tune")

    def _add(self, part, sound, at, gain, ducked=False, pitch=None, midi=None):
        """Sound a part now (or `at` samples into the block), at its own level; nothing if it is switched off. midi:
        the note asked for, as a MIDI note, for `heard`."""
        settings = self.parts[part]
        if settings["on"] and settings["level"] > 0:
            self.hits[part] = self.step
            self.played.append((self.step, part, pitch))
            if part in self.HEARD:
                self.heard.append((self.step, part,
                                   None if midi is None else round(midi + 12 * settings["octave"] + settings["pitch"], 2)))
            self.struck.setdefault(part, []).append(self.pos + max(int(at), 0))
            self.voices.append([sound, -at, gain * settings["level"], self.gives_way(settings, part, ducked)])
            return True
        return False

    def gives_way(self, settings, part=None, ducked=True):
        """What a part's sound gives way to as it plays: (the part it ducks under, how far, how quickly it comes back),
        or None for nothing. Left as it comes, the sub ducks under the kick a little and briefly, and the bass, the
        tune, the drones and whatever is laid over the music duck under it more."""
        by = settings.get("duck_by")
        if by is None:          # left as it comes: the low end does not duck at all (it and the kick keep to their own registers),
            return None if part in ("sub", "bass") else ("kick", 0.15, 0.08) if ducked else None      # and the rest barely
        return None if by == "none" or by == part or by not in self.parts else (by, settings["duck"], 0.11)

    def _since(self, source, frames):
        """For every sample of the block being made: how many samples ago `source` last sounded."""
        if source not in self.since:
            since = np.arange(frames, dtype=np.float32) + (self.pos - self.last_hit.get(source, -10 * self.rate))
            later = []
            for hit in sorted(self.struck.get(source, ())):
                at = hit - self.pos
                if at < frames:
                    since[max(at, 0):] = np.arange(frames - max(at, 0), dtype=np.float32)
                    self.last_hit[source] = hit
                else:
                    later.append(hit)                  # it sounds after this block: kept for the next
            self.struck[source] = later
            self.since[source] = since
        return self.since[source]

    def duck_gain(self, way, frames):
        """The gain, per sample of the block just made, for a sound that gives way as `way` says (see gives_way)."""
        if way is None or frames != len(next(iter(self.since.values()), ())):
            return None
        since = self._since(way[0], frames)
        eased = np.minimum(since / (0.004 * self.rate), 1.0)        # four milliseconds into the dip: a step down in a held note is a click
        return 1.0 - way[1] * eased * np.exp(-since / (way[2] * self.rate))

    def _drum(self, name):
        """A drum sound as its part has been told to sound."""
        part = {"kick": "kick", "snare": "snare", "clap": "snare", "hat": "hats", "open_hat": "hats"}[name]
        key = (name, self.rev[part])
        sound = self.drums.get(key)
        if sound is None and (self.parts[part]["fx"] or self.parts[part]["layers"] or self.parts[part]["room"] or self.parts[part]["attack"]
                              or self.parts[part]["filth"]):
            if key not in self.building:               # slow to make: built aside; the drum as it last was plays until it is ready
                self.building.add(key)
                self.jobs.put(lambda: self._build_drum(key, name, part))
            return self.last.get(name, getattr(self, name))
        if sound is None:
            sound = self._shape_drum(key, name, part)
        return sound

    def _work(self):
        """The worker that makes sounds aside, one after another. Nothing it is given can stop it."""
        _stand_back()
        while True:
            job = self.jobs.get()
            while self.urgent:
                try:
                    self.urgent.popleft()()
                except Exception:
                    pass
            try:
                job()
            except Exception:
                pass

    def _build_drum(self, key, name, part):
        _stand_back()
        try:
            with self.one_at_a_time:
                if key[1] == self.rev[part]:           # still wanted: the knob may have moved on while this waited
                    self._shape_drum(key, name, part)
        finally:
            self.building.discard(key)

    def _shape_drum(self, key, name, part):
        sound = None
        if sound is None:
            settings = dict(self.parts[part])
            if len(self.drums) > 40:
                self.drums.clear()
            base = (_kick(self.rate, settings["length"], settings["punch"]) if name == "kick" and not getattr(self, "pulled", {}).get("kick")
                    else getattr(self, name))
            if name != "kick" and settings["length"] < 0.95:
                base = fade(base[:max(int(len(base) * settings["length"]), 64)], self.rate, 0.004)
            if settings["octave"] or settings["pitch"]:
                base = repitch(base, 12 * settings["octave"] + settings["pitch"])
            sound = self._finish(np.asarray(base, dtype=np.float32), settings, {"kick": 55.0, "snare": 190.0, "hats": 7000.0}[part])
            room = settings["room"] if settings["room"] is not None else (0.25 * (settings["length"] - 1.0) if name != "kick" else 0.0)
            if room > 0.02:
                sound = reverb(sound, self.room, room)
            self.drums[key] = self.last[name] = sound
        return sound

    def _note(self, kind, semitones, steps=0.0, ahead=False, shade=None):
        """A note as its part is set to sound. No note is made here, in the thread that makes the sound (a note takes
        up to half the time there is for a whole block, and a bar that needs three new ones was a dropout): a note not
        yet made is made aside, and until it is ready the same note as it last was is played, or failing that a bare
        version of it without its room. `ahead`: only see that it is being made (see _prepare); returns nothing."""
        part = "tune" if kind in instruments.VOICES else {"sub": "sub", "bass": "bass", "pluck": "tune", "bell": "bells", "drone": "drones"}[kind]
        settings = self.parts[part]
        # lengths go in twentieths of a second, so that a tempo that is gliding does not make every note a new one
        length = max(round(steps * 15.0 / self.bpm * settings["length"] * 20) / 20, 0.05)
        semitones += 12 * settings["octave"] + round(settings["pitch"], 1)
        # (shade: how a voice is coloured for this note, its filter and accent and slide: the same pitch in another shade
        # is another sound, which is what keeps a repeated note from being the same every time)
        root = 28 + (NOTES[self.note] - 4) % 12
        key = (kind, semitones, length, root, self.rev[part], self.kit_id if kind in ("pluck", "drone", "stab") else 0, self.scores if kind == "pluck" else 0, shade)
        sound = self.notes.get(key)
        if sound is None:
            if key not in self.building:
                self.building.add(key)
                made_with = dict(settings)
                build = lambda: self._build(key, kind, semitones, length, made_with, shade)     # noqa: E731
                if kind == "sub":
                    self.urgent.append(build)
                    self.jobs.put(lambda: None)        # (to wake the worker)
                else:
                    self.jobs.put(build)
            if ahead:
                return None
            if key[:4] not in self.last and kind == "sub":             # a sub note nobody saw coming: bare, this once (it is quick to make,
                self.last[key[:4]] = self._make(kind, semitones, length, {**settings, "fx": [], "layers": [], "filth": 0.0}, quick=True, shade=shade,
                                                root=root)              # and missed)
            return self.last.get(key[:4], np.zeros(8, np.float32))    # any other note not ready is left out this once: better than a dropout
        return sound

    # Under a break the drums want the bass doubling the kick; under a programmed two-step, stepping a sixteenth
    # aside (05_bass_sub_tune_progression.md, 12.1). The scene's seed settles it for the styles in between.
    LOCKING = ("dnb", "amen", "breakbeat_hardcore", "stutter", "rolling", "broken")
    SIDESTEPPING = ("twostep", "two_step", "shuffled_two_step")

    def _versions(self, number):
        """Which version of the riff and of the hook bar `number` plays: (riff version, motif version), as
        bassline.riff and motif.motif take them. Development decides, when there is one (`develop`). Until then: a
        riff made by hand stays as it was made; otherwise each section of thirty-two bars has its riff, with one kept
        mutation every eight bars, the second section of every two plays the first's B riff, and every two sections
        a new riff (a relative of the last). The hook is the section's own, stated for sixteen bars and then
        replaced by its relative.

        The hand beats development: a riff or a hook held by hand (made, or mutated, by hand) stays as it was made
        until it is let go (a new score, a new style), whatever development says meanwhile."""
        section, within = number // deal.SECTION, number % deal.SECTION
        if self.develop is not None:
            riff, hook = self.develop.versions(number)
        else:
            riff = {"riff": section // 2, "side": "AB"[section % 2], "gen": within // 8}
            hook = {"motif": section, "gen": within // 16}
        # held by hand: True (a riff of its own seed, as it was made) or the version that was playing, changed (mutate)
        if isinstance(self.sub_held, tuple):
            riff = dict(self.sub_held)
        elif self.sub_held:
            riff = {"gen": 0}
        if isinstance(self.hook_held, tuple):
            hook = dict(self.hook_held)
        elif self.hook_held:
            hook = {"gen": within // 16}
        return riff, hook

    def _hole(self, number, lane="riff"):
        """Is the riff (or the hook: lane "hook") out for bar `number`, by development (the turnaround hole, the low end
        out before A comes back, a hook withheld)? Never while it is held by hand."""
        held = self.sub_held if lane == "riff" else self.hook_held
        return number >= 0 and self.develop is not None and not held and bool(self.develop.hole(number, lane))

    def _deal(self, number, busier=0.0):
        """Bar `number` of the drums: deal.held_bar with what development says these drums are (the B drums at 32,
        A back changed at 64) and the edge's numbers for that bar, when there is a development; as before when not.
        Parts written by hand play as written either way."""
        material, numbers = self.develop.drums(number) if self.develop is not None else (None, None)
        return deal.held_bar(self.pattern, self.style, self.energy, number, self.deal_seed, set(self.by_hand), busier=busier,
                             material=material, numbers=numbers)

    def _relation(self):
        if self.style in self.SIDESTEPPING:
            return "answer"
        if self.style in self.LOCKING:
            return "lock" if deal._draw(self.sub_seed, "relation", self.scores) < 0.7 else "free"
        return "free"

    def _riff_key(self, number):
        return (self.sub_seed, self.mode, self._relation(), tuple(self.pattern.get("kick", ())), repr(self._versions(number)[0]))

    def _riff(self, number):
        """The stored riff bar `number` plays (bassline.py), as its version has it."""
        key = self._riff_key(number)
        made = self.riff_cache.get(key)
        if made is None:
            if len(self.riff_cache) > 16:
                self.riff_cache.clear()
            made = self.riff_cache[key] = bassline.riff(self.sub_seed, self.note, MODES[self.mode], self._versions(number)[0], key[2], key[3])
        return made

    def _sub_bar(self, number):
        """What the written sub plays in bar `number`: [(sixteenth, semitones, length, slid from, how hard)]. Where
        the riff has changed since the bar before, that bar is the one it slides from (it is what was played)."""
        if number < 0 or self._hole(number):          # development's hole: the low end out for the bar
            return []
        entry = self._hole(number - 1)                 # the first bar back after a hole: one held root
        key = (self._riff_key(number), number, entry)
        made = self.bar_cache.get(key)
        if made is None:
            changed = number > 0 and self._riff_key(number - 1) != key[0]
            made = bassline.bar(self._riff(number), number, before=self._sub_bar(number - 1) if changed and not entry else None, entry=entry)
            if len(self.bar_cache) > 64:
                self.bar_cache.clear()
            self.bar_cache[key] = made
        return made

    def _bass_bar(self, number):
        """What the saw bass plays in bar `number`, its own job: answering in the sub's rests, or nothing (and nothing
        in development's holes: the whole low end is out)."""
        if self._hole(number):
            return []
        return bassline.answer(self._riff(number), number, self._sub_bar(number))

    def _written(self):
        """Is the low end playing the written riff (a break style, the sub not written by hand)?"""
        return self.style in deal.BREAKS and "sub" not in self.by_hand

    def low_ahead(self, number):
        """What the sub and the bass will play in bar `number`, asked ahead and changing nothing:
        {"sub": [(sixteenth, semitones above the root, length in sixteenths)], "bass": [...]}. (The bass sounds an
        octave above what is given.) For whatever should keep out of the low end's way: the hook here, and anything
        else that places itself against the bass."""
        if self._written():
            sub = [(s, p, n) for s, p, n, _, _ in self._sub_bar(number)]
            if "bass" in self.by_hand:
                bass = [(s, sub[-1][1] if sub else 0, 1.6) for s in self.pattern.get("bass", ())]
            else:
                bass = [(s, p, n) for s, p, n, _, _ in self._bass_bar(number)]
            return {"sub": sub, "bass": bass}
        root = self._pitch(self.movement[number % 4])
        steps = sorted(self.pattern.get("sub", ()))
        sub = [(s, root, min(((steps[(i + 1) % len(steps)] - s - 1) % 16 + 1) * 0.95, 7.5)) for i, s in enumerate(steps)]
        return {"sub": sub, "bass": [(s, root, 1.6) for s in self.pattern.get("bass", ())]}

    def _motif(self, number):
        """The hook bar `number` is in (motif.py): made from the pitches the bass is built on."""
        version = self._versions(number)[1]
        riff = self._riff(number)
        key = (self.hook_seed, self.mode, riff["home"], repr(version))
        made = self.motif_cache.get(key)
        if made is None:
            if len(self.motif_cache) > 16:
                self.motif_cache.clear()
            scale = MODES[self.mode]
            made = self.motif_cache[key] = motif.motif(self.hook_seed, scale, motif.pitch_set(scale, bassline.home(riff)), version)
        return made

    def _hooks(self, number):
        """The hooks of the eight bars that bar `number` is in: {bar in the eight: [(sixteenth, semitones, length)]},
        placed in the gaps the sub and the bass leave, and moved as a whole into the octave where hooks live."""
        block = number // 8
        m = self._motif(number)
        key = (block, self.hook_seed, repr(self._versions(number)[1]), self._riff_key(number), self.tune_every, self.style, self.note,
               tuple(sorted(self.by_hand)), tuple(self.pattern.get("bass", ())), tuple(self.pattern.get("sub", ())))
        made = self.hook_cache.get(key)
        if made is None:
            def low(pos):
                ahead = self.low_ahead(block * 8 + pos)
                return [(s, n) for s, _, n in ahead["sub"] + ahead["bass"]]
            plan = motif.block(m, number, low, {None: deal.HOOK_BARS, 1: 6, 2: 4, 4: 2}[self.tune_every])
            home = 28 + (NOTES[self.note] - 4) % 12
            moved = self._riff(number).get("transpose", 0)        # a transposed riff takes its hook with it
            lowest = min(p for _, p, _ in m["notes"]) + moved
            shift = deal.HOOK_LOW + (home + lowest - deal.HOOK_LOW) % 12 - home - lowest + moved
            made = {pos: [(s, p + shift, n) for s, p, n in notes] for pos, notes in plan.items()}
            if len(self.hook_cache) > 8:
                self.hook_cache.clear()
            self.hook_cache[key] = made
        return made

    STAGES = ("tease", "state", "chop", "last")

    def lead_voice(self, section):
        """Who carries the hook in this section. With film sound: the film's own sound, cut into tuned stabs, and the
        scene's signature synth in turn with it, a section each. Before there is any film sound: the synth."""
        synth = instruments.SYNTHS[self.signature % len(instruments.SYNTHS)]
        if self.lead_choice in instruments.SYNTHS:     # chosen by hand: that synth, and only that synth
            return self.lead_choice
        if self.lead_choice == "film":                 # the film's own sound only (the synth until there is some)
            return "stab" if self.kit else synth
        return ("stab" if section % 2 == 0 else synth) if self.kit else synth

    def _lead(self, number):
        """What the lead plays in bar `number`: [(sixteenth, voice, semitones, length in sixteenths, shade, how loud)].

        A section of thirty-two bars is four blocks of eight, and the hook goes through them as a sample is developed
        (docs/research/03_sample_placement.md, R7): teased (its first notes only, dark and quiet), stated (whole, at
        full strength), chopped (stated, answered, its relatives, and a stutter into the next block), and then either
        answered once more or taken out altogether, every other section. Its colour moves on the slow clock: the filter
        opens and closes over sixteen bars. The acid voice plays a line of its own, held for the section, under the
        same stages, on the pitches the hook and the bass share; the others play the hook (motif.py): stated in bar 4
        of each eight, its leap again in bar 5, answered in bar 8, placed in the low end's gaps."""
        withheld = self._hole(number, "hook")             # development has the hook out for a while
        key = (number, self.hook_seed, self.hook_held, self.tune_every, bool(self.kit), self.signature, self.note, self.mode, self.lead_choice,
               self._riff_key(number), self.style, tuple(sorted(self.by_hand)), tuple(self.pattern.get("bass", ())), tuple(self.pattern.get("sub", ())),
               repr(self._versions(number)[1]), withheld)
        if key in self.lead_cache:
            return self.lead_cache[key]
        section, block = number // deal.SECTION, (number // 8) % 4
        stage = self.STAGES[block]
        if stage == "last":
            stage = "answer" if section % 2 == 0 else "out"
        if withheld:
            stage = "out"
        events = []
        if stage != "out":
            voice = self.lead_voice(section)
            swell = 0.5 - 0.5 * math.cos(2.0 * math.pi * (number % 16) / 16.0)
            cut = int(min(7, {"tease": 1, "state": 3, "chop": 4, "answer": 3}[stage] + round(3 * swell)))
            loud = {"tease": 0.5, "state": 1.0, "chop": 0.9, "answer": 0.85}[stage] * {"stab": 0.3, "acid": 0.13, "reese": 0.2, "hoover": 0.15, "dub": 0.16}[voice]
            if voice == "acid":
                scale = MODES[self.mode]
                shared = [scale.index(pc) for pc in self._motif(number)["pitches"] if pc in scale and pc]
                line = deal.acid_line((self.hook_seed,) if self.hook_held else (self.hook_seed, section),
                                      (0, 0, 0) + tuple(sorted(shared)) + (-1 if scale[6] in self._motif(number)["pitches"] else 0, 7))
                last = None
                struck = {s for s, _, _ in self.low_ahead(number)["sub"]}      # the line keeps off the sub's onsets, as the hook does
                for step, degree, accent, slide, held in line:
                    if stage == "tease" and step >= 8:
                        break
                    if step in struck:
                        last = None
                        continue
                    semis = self._pitch(degree) + 24
                    events.append((step, "acid", semis, 2 if held else 1, (cut, int(accent), last if slide else None), loud))
                    last = semis
            else:
                hooks = self._hooks(number)
                hook = hooks.get(number % 8)
                if stage == "tease" and hooks and number % 8 != min(hooks):
                    hook = None                        # teased: once in the block, and only its first notes
                if hook:
                    shape = hook
                    if stage == "tease":
                        shape = shape[:2]
                    if voice == "dub":                 # a chord: on the hook's first note only
                        shape = shape[:1]
                    for at, (step, semis, length) in enumerate(shape):
                        steps = max(length, 1.0) * (2.5 if voice == "reese" else 1.2)
                        events.append((step, voice, semis - (12 if voice == "reese" else 0), steps, (cut, int(at == 0), None), loud))
                if stage == "chop" and number % 8 == 7 and voice == "stab" and hook is None:
                    first = next(iter(self._hooks(number).values()), None)
                    if first:                          # a stutter of the hook's first note into the next block
                        semis = first[0][1]
                        events += [(slot, "stab", semis, 1.0, (cut + 1, int(slot == 15), None), loud * (0.5 + 0.15 * (slot - 12))) for slot in (12, 13, 14, 15)]
            events = [event for event in events if 0 <= event[0] < 16]
        if len(self.lead_cache) > 64:
            self.lead_cache.clear()
        self.lead_cache[key] = events
        return events

    def drums_ahead(self, number):
        """Where the kick and the snare will fall in bar `number`, asked ahead of time and changing nothing: the same
        deal `_trigger` makes when it gets there (as things stand now), for whatever plays against the drums.
        {"kick": [sixteenths], "snare": [sixteenths]}. The snare is not there when the energy is too low for it."""
        hits = self._deal(number)
        return {"kick": sorted(hits["kick"]), "snare": sorted(hits["snare"]) if self.energy >= 0.3 else []}

    def _plan_ahead(self, number):
        """On the worker: what bar `number` will play, worked out (the riff, the sub's and the bass's bars, the hooks,
        the lead) so that the sound's own thread finds it made. Only the plans: their notes are _prepare's. Anything
        changed since is simply worked out again where it is wanted."""
        try:
            if self._written():
                self._bass_bar(number)
            self._lead(number)
        except Exception:
            pass

    def _prepare(self, number):
        """Half a bar early: the notes that bar `number` will need are made aside now, so that none of them has to be
        made as it is played."""
        written = self._written()
        if written and self.sub > 0.02:
            for _, semis, length, slide, _ in self._sub_bar(number):
                self._note("sub", semis, length, ahead=True, shade=slide)
        if self.energy >= 0.45 and written and "bass" not in self.by_hand:     # the bass's own line
            for _, semis, length, _, _ in self._bass_bar(number):
                self._note("bass", semis + 12, length, ahead=True)
        elif self.energy >= 0.45 and self.pattern.get("bass"):                  # the bass on its steps, wherever the sub may be by then
            for semis in {self.sub_semis, self._pitch(self.movement[number % 4])} | {p for _, p, _, _, _ in (self._sub_bar(number) if written else ())}:
                self._note("bass", semis + 12, 1.6, ahead=True)
        if (self.energy >= 0.35 or self.tune_every) and self.parts["tune"]["on"]:     # (nothing made for a muted lead)
            for _, voice, semis, steps, shade, _ in self._lead(number):
                self._note(voice, semis, steps, ahead=True, shade=shade)

    def _build(self, key, kind, semitones, length, settings, shade=None):
        _stand_back()
        try:
            part = "tune" if kind in instruments.VOICES else {"sub": "sub", "bass": "bass", "pluck": "tune", "bell": "bells", "drone": "drones"}[kind]
            with self.one_at_a_time:
                if key[4] != self.rev[part]:           # no longer wanted: the knob moved on while this waited
                    return
                made = self._make(kind, semitones, length, settings, shade=shade, root=key[3])
                if len(self.notes) > 300:              # the oldest go, a few at a time: emptying it all at once made every note new again
                    for old in list(self.notes)[:100]:
                        self.notes.pop(old, None)
                self.notes[key] = self.last[key[:4]] = made
            if len(self.last) > 400:
                for old in list(self.last)[:150]:
                    self.last.pop(old, None)
        finally:
            self.building.discard(key)

    def _make(self, kind, semitones, length, settings, quick=False, shade=None, root=None):
        low = 28 + (NOTES[self.note] - 4) % 12 if root is None else root    # the root between E1 (41 Hz) and D#2 (78 Hz), as it was asked for
        freq = 440.0 * 2 ** ((low + semitones - 69) / 12)
        piece, shift = None, None
        if self.kit:
            # the piece of film sound that needs moving least to sound this note, by what it is really sounding; one with
            # no clear pitch is played as before, as if it sounded a tritone above the root
            heard = getattr(self, "kit_pitch", [None] * len(self.kit))
            # (the note itself where that is within an octave of the piece; failing that its pitch class, within half an octave)
            moves = [(((low + semitones - p) if abs(low + semitones - p) <= 12 else fold(low + semitones - p, 0, span=6)) if p is not None else None, at)
                     for at, p in enumerate(heard)]
            pitched = [(abs(m), (at - self.scores) % len(self.kit), m, at) for m, at in moves if m is not None]
            if pitched:
                _, _, shift, at = min(pitched)
                piece = self.kit[at]
            else:
                piece = self.kit[(self.scores + int(semitones // 12)) % len(self.kit)]
        rng = np.random.default_rng(abs(hash((kind, semitones))) % (2 ** 32))
        own = lambda amount: settings["room"] if settings["room"] is not None else amount       # noqa: E731
        if kind in instruments.VOICES:                 # the lead's voices: shade is (cut 0 to 7, accent, the note slid from)
            cut, accent, slid = shade or (4, 0, None)
            beat = 60.0 / self.bpm
            if kind == "stab":
                tuned = repitch(piece, shift if shift is not None else fold(semitones, 30)) if piece is not None else None
                sound, room = (instruments.stab(self.rate, tuned, length, cut, bool(accent)) if tuned is not None else np.zeros(64, np.float32)), own(0.2)
            elif kind == "acid":
                slide = 440.0 * 2 ** ((low + slid - 69) / 12) if slid is not None else None
                sound, room = instruments.acid(self.rate, freq, length, cut, bool(accent), slide), own(0.0)
            elif kind == "reese":
                sound, room = instruments.reese(self.rate, freq, length, cut, beat), own(0.1)
            elif kind == "hoover":
                sound, room = instruments.hoover(self.rate, freq, length, cut), own(0.25)
            else:
                sound, room = instruments.dub(self.rate, freq, length, cut, echo_seconds=0.75 * beat), own(0.15)
        elif kind == "sub":                            # (shade: the pitch it slides in from, or None)
            slid = 440.0 * 2 ** ((low + shade + 12 * settings["octave"] + round(settings["pitch"], 1) - 69) / 12) if shade is not None else None
            sound, room = _sub(self.rate, freq, length, slid), own(0.0)
        elif kind == "bell":
            sound, room = _bell(self.rate, freq), own(0.25)
        elif kind == "bass":                           # two saws a hair apart, closing down as the note dies: it moves, where a plain tone sits flat
            sound = np.tanh(2.0 * (_tone(self.rate, freq * 0.996, length, 9, 0.22) + _tone(self.rate, freq * 1.004, length, 9, 0.22))) * 0.6
            room = own(0.0)
        elif kind == "drone" and piece is not None:
            sound, room = smear(repitch(piece, shift if shift is not None else fold(semitones, 30)), self.rate, min(max(length, 2.0), 6.0), rng), own(0.6)
        elif kind == "drone":
            seconds = min(length, 8.0)
            sound, room = sum(_tone(self.rate, freq * detune, seconds, 3, 6.0) for detune in (0.994, 1.0, 1.007)) / 3.0, own(0.5)
        elif piece is not None:                        # the tune, played on a piece of the film's own sound
            chop = repitch(piece, shift if shift is not None else fold(semitones, 30))
            sound, room = fade(chop[:max(int(self.rate * max(length * 1.6, 0.16)), 64)], self.rate, 0.01), own(0.35)
        else:                                          # no film yet: a plucked pair of saws in a room
            sound, room = (_tone(self.rate, freq * 0.995, length, 9, 0.35) + _tone(self.rate, freq * 1.005, length, 9, 0.35)) * 0.5, own(0.3)
        if quick:                                       # bare: without its colour, its effects or its room (those are what take the time)
            return np.asarray(sound, dtype=np.float32)
        sound = self._finish(np.asarray(sound, dtype=np.float32), settings, freq)
        return reverb(sound, self.room, room) if room > 0.02 else sound

    def heart(self):
        """The heartbeat at this tempo: (sixteenths from one beat of the heart to the next, how many after the first
        thump the second falls). About a second apart, the second thump about a quarter of a second after the first."""
        sixteenth = 15.0 / self.bpm
        return (8 if sixteenth * 8 >= 0.55 else 16), int(min(max(round(0.27 / sixteenth), 2), 4))

    def _trigger(self, step, at):
        if self.opening:                                               # nothing but the heartbeat until the scene is set
            if self.scene_set and step % 16 == 0:                      # ... and then everything, on the one: nothing added to mark it
                self.opening = False
                self.changed_at = step
                self._prepare(step // 16)                              # (what the first bar plays is made now: it was never prepared)
            else:
                if self.scene_set and step % 16 == 6:
                    self._prepare(step // 16 + 1)                      # the bar the music comes in on, made ahead like any other
                every, second = self.heart()
                where = step % every
                if where in (0, second) and self._add("kick", self._drum("kick"), at, 0.95 if where == 0 else 0.6):
                    self.kick_at.append(min(max(at, 0), 10 ** 9))
                return
        if self.composer is not None:
            return self._trigger_composed(step, at)
        e, s, number = self.energy, step % 16, step // 16
        bar = number % 4
        style, plays = STYLES[self.style], self.pattern
        swing = style["swing"] if self.swing is None else self.swing
        if s % 2 == 1:
            at += int(swing * self.step_len)                           # swung: the odd sixteenths arrive late
        root = self._pitch(self.movement[bar])
        # A break is the low end taken away while the drums keep running (busier, if anything): no riser, no crash on
        # the way back. About one in four ends in a short roll, and about one in four leaves its last sixteenth empty.
        left = self.break_end - step                                   # sixteenths until a break ends
        resting = left > 0
        if resting and self.break_shape is None:
            self.break_shape = deal.break_ending(self.deal_seed, self.break_start)
        elif not resting and self.break_end > self.break_start:
            self.break_start, self.break_shape = self.break_end, None
        roll, gap = self.break_shape if resting else (False, False)
        if self.dealt[0] != number:                                    # each bar is dealt afresh: nothing is a loop
            self.dealt = (number, self._deal(number, busier=0.25 if resting else 0.0),
                          [] if "snare" in self.by_hand else deal.fill(number, self.deal_seed, self.develop.drums(number)[1] if self.develop is not None else None))
        _, hits, closing = self.dealt
        drums = not (resting and gap and left == 1)
        if drums and number == self.fill_bar and s >= 8:               # a fill asked for by hand: the bar ends in a snare roll
            self._add("snare", self._drum("snare"), at, 0.2 + 0.3 * (s - 8) / 7)
            if s == 15:
                self.fill_bar = -1
            drums = False
        if drums:
            hard = hits["kick"].get(s)
            if hard and self._add("kick", self._drum("kick"), at, 0.95 * hard * (0.35 if resting else 1.0)):
                self.kick_at.append(min(max(at, 0), 10 ** 9))
            if e >= 0.3:
                if s in hits["snare"]:
                    self._add("snare", self._drum("clap" if style["clap"] else "snare"), at, 0.45)
                elif s in hits["ghost"]:
                    self._add("snare", self._drum("snare"), at, 0.45 * hits["ghost"][s])
                for slot, how_hard in closing:                         # the fill that closes a four-bar group, now and then
                    if slot == s and s not in hits["snare"]:
                        self._add("snare", self._drum("snare"), at, 0.45 * how_hard)
                if roll and left <= 4:
                    self._add("snare", self._drum("snare"), at, 0.2 + 0.07 * (4 - left))
            if e >= 0.25:
                if s in hits["open"]:
                    self._add("hats", self._drum("open_hat"), at, 0.28)
                elif s in hits["hats"]:
                    self._add("hats", self._drum("hat"), at, 0.26 * hits["hats"][s])
        low = not resting
        if s == 6:                                                     # the next bar's notes, made aside now
            line = (number + 1) * 16
            if self.waiting and line % 64 == 0 and line - self.changed_at >= self.structure_bars * 16:
                with self.waiting_lock:                                # a change waits for that line: made as it will be then
                    coming = self._after(dict(self.waiting))
                self._prepare_as(coming, number + 1)
            else:
                self._prepare(number + 1)
            self.jobs.put(lambda later=number + 2: self._plan_ahead(later))
        home = 28 + (NOTES[self.note] - 4) % 12                        # the root, as a MIDI note
        if self._written():                                            # the sub plays its written riff (bassline.py)
            for slot, semis, length, slide, accent in self._sub_bar(number):
                if slot == s:
                    self.sub_semis = semis
                    if low and self.sub > 0.02:
                        self._add("sub", self._note("sub", semis, length, shade=slide), at, 0.9 * self.sub * (0.85 + 0.15 * accent), True,
                                  pitch=semis, midi=home + semis)
            root = self.sub_semis
            if low and e >= 0.45 and "bass" not in self.by_hand:       # the bass's own job: answering in the sub's rests (or resting)
                for slot, semis, length, _, accent in self._bass_bar(number):
                    if slot == s:
                        self._add("bass", self._note("bass", semis + 12, length), at, 0.3 * accent / 0.7, True, pitch=semis, midi=home + semis + 12)
        elif low and self.sub > 0.02 and s in plays["sub"]:
            ordered = sorted(plays["sub"])
            nxt = ordered[(ordered.index(s) + 1) % len(ordered)]
            self._add("sub", self._note("sub", root, min(((nxt - s - 1) % 16 + 1) * 0.95, 7.5)), at, 0.9 * self.sub, True, pitch=root, midi=home + root)
        if low and e >= 0.45 and s in plays["bass"] and (not self._written() or "bass" in self.by_hand):    # its steps, written or typed: exactly
            self._add("bass", self._note("bass", root + 12, 1.6), at, 0.3, True, pitch=root, midi=home + root + 12)
        if (e >= 0.35 or self.tune_every) and self.parts["tune"]["on"]:     # the lead: the hook, in the voice of the section (see _lead)
            for slot, voice, semis, steps, shade, loud in self._lead(number):
                if slot == s:
                    self._add("tune", self._note(voice, semis, steps, shade=shade), at, loud, True, pitch=semis, midi=home + semis)
        self._bells(step, at)

    def render(self, frames):
        """The next `frames` samples: (mix, duck). `duck` is the gain, per sample, for anything played over the
        groove: it dips on every kick and recovers before the next sixteenth."""
        self.kick_at, self.steps = [], []                               # steps: (sixteenth number, where in this block)
        while self.next_step < self.pos + frames:
            self.steps.append((self.step, int(self.next_step) - self.pos))
            if self.waiting:
                self._structure_due()
            self._trigger(self.step, int(self.next_step) - self.pos)
            self.step += 1
            self.step_len = 15.0 * self.rate / self.bpm                 # one sixteenth at the tempo as it is now
            self.next_step += self.step_len
        self.since = {}
        for source in set(self.struck) | set(self.parts):               # every part's hits are taken into account, asked about or not
            self._since(source, frames)
        duck = self.duck_gain(("kick", 0.15, 0.08), frames)
        # Sounds that give way in the same manner are added up together, then turned down together. (The sub gives
        # way to the kick only briefly and only partly: ducked like the rest, it vanished whenever its notes fell
        # on the kick.)
        buses, alive = {}, []
        for voice in self.voices:
            sound, into, level, way = voice
            start = max(0, -into)                                       # where in this block it begins
            begin = max(0, into)                                        # where in the sound we are
            count = min(frames - start, len(sound) - begin)
            if count > 0:
                way = way or None
                if way not in buses:
                    buses[way] = np.zeros(frames, np.float32)
                buses[way][start:start + count] += sound[begin:begin + count] * level
            voice[1] = into + frames
            if voice[1] < len(sound):
                alive.append(voice)
        self.voices = alive
        mix = np.zeros(frames, np.float32)
        for way, bus in buses.items():
            mix += bus if way is None else bus * self.duck_gain(way, frames)
        self.pos += frames
        return np.tanh(mix).astype(np.float32), duck.astype(np.float32)
