"""The sound of a session: the synthesised rhythm section (groove.py) playing from the first second, with the
generated video's soundtrack played over it as a clip, the way a vocal is played over a dance track.

A new film's sound waits for the next bar line and plays once straight through with its picture (its premiere).
After that it is a layer under a name of its own, cut up and waiting like any sample: brought in, it is played a
slice at a time to four bars planned against the drums and the other layers (chopper.py), and the picture jumps
with the slices of the newest film. The kick ducks it, and its low end is removed so the sub owns the bass. (A clip given no name is
chopped as soon as its premiere is over, and heard straight through again every sixteen bars.)

Everything is cut at its obvious transients unless told otherwise ("chop the rain on the eighths", "into 8",
"finer"). Samples pulled from outside are layers beside the clip, as many as six, each under its own name. A new
one arrives cut up and named, and waits: it plays from the bar after it is brought in. Each is chopped the same
way as the clip, or placed by hand on chosen sixteenths; each can be told which bars to play in (every bar, one bar in
N, only in the breaks); and each takes the same sound settings and effects as any other part.

The sound card is the clock. `beat()` and `clip_seconds()` say where the sound that is being HEARD now
is, so the picture can pulse on the kick and show the video frame that belongs to the slice playing.

Everything is in memory; nothing is written anywhere.
"""
import collections
import copy
import sys
import threading
import time

import numpy as np

from .groove import Groove
from . import parts as part_words
from .kit import fade, repitch, reverb, tone_slices
from .parts import QUICK, apply_op, fresh, summary
from .groove import _stand_back
from . import chop, chopper
from . import edge as edge_dials
from .course import Course
from .samples import cut_points, slices as cut_slices, to_rate
from .watch import Watch, compact as watch_compact

FADE = 64                # samples of fade at each cut, so chops do not click
REPLAY_BARS = 16         # how often a chopped clip is heard straight through again


class Mixer:
    WATCH = True             # the self-measurement's thread is started (watch.py; see _watcher)
    WATCH_PARTS = ("kick", "snare", "sub", "bass", "tune")
    WATCH_LATE = 0.002       # a block noticed later than this after it was made is let go: the next is waited for

    def __init__(self, bpm=120.0, energy=0.5, log=None, open_stream=True, rate=44100, seed=None, compose=True):
        self.log = log or (lambda msg: None)
        self.stream, self.failed = None, False
        sys.setswitchinterval(0.001)                  # the sound's thread gets its turn within a millisecond of asking
        if open_stream:
            import sounddevice as sd
            rate = int(sd.query_devices(kind="output")["default_samplerate"])
        self.rate = rate
        self.groove = Groove(bpm=bpm, rate=rate, energy=energy, seed=seed)
        self.rng = np.random.default_rng(seed)
        if compose:                                   # thelmic writes the parts, if it is there
            try:
                from .composer import Composer
                self.groove.use_composer(Composer(seed=seed or 1), log=self.log)
                self.log("music: composed by thelmic")
            except Exception as e:
                self.log(f"music: built-in patterns ({e})")
        self.groove_on, self.chop, self.mute = True, True, False
        self.groove_level, self.clip_level, self.clip_on = 0.8, 0.9, True
        self.chop_density, self.chop_div = None, 2           # how busy the chopping is (None = follows the energy); slice length in sixteenths
        self.clip_steps = collections.deque(maxlen=300)      # the sixteenths on which the film's sound was heard
        self.clip_when, self.clip_place = 1, None            # which bars the chopped clip plays in; sixteenths it is placed on by hand
        self.clip_cut, self.clip_sense = "transients", 1.0   # how the film's sound is cut: at its obvious transients unless told otherwise
        self.layers, self.shots = {}, []                     # sample layers by name; slices of them now sounding
        self.film, self.film_sync = None, None               # the newest film's layer; [where in that film the sound heard is, where it stops]
        self.super, self.own = 0.0, {}                       # the super knob, and where each part's knob stands without it
        self.memory = {}                                     # everything about the music as it stood, by slot number: in memory only
        # the timeline: memories in order, each held for a number of bars and left in a chosen way. `line_at` is which
        # one is playing (-1: the first comes in on the next bar line); the work is done aside from the sound's thread
        self.line, self.line_at, self.line_bars, self.line_loop = [], -1, 0, False
        self.line_jobs, self.arrivals = collections.deque(), collections.deque()
        self.fade_side = None                                # the crossfader: which two memories it is between, and whose side it is on
        # every sound that has been a layer this session (a pulled sample, a film's sound), by number, so that one that
        # has gone can be brought back; and the ones nobody has been told about yet
        self.sounds, self.sound_next, self.sound_news = {}, 1, collections.deque()
        self.line_wake = threading.Event()
        threading.Thread(target=self._line_worker, daemon=True).start()
        # the chopping: how it is done (one of chopper.STYLES; a change is heard from the next four-bar line, so the
        # style before it is kept with the group it starts at), and its plans, four bars at a time, made aside by the
        # planner a bar before they play (see _planner): by group, with the count of hand changes they were made after
        self.chop_style = chopper.DEFAULT_STYLE
        self.style_was = (chopper.DEFAULT_STYLE, 0)
        self.plans, self.plan_rev, self.plan_asked, self.plan_busy, self.plan_told = {}, 0, set(), None, False
        self.plan_wake = threading.Event()
        # the course (course.py): the edge's two dials and development's clocks, worked out on the planner's thread at
        # each bar line (`course_due`, set by the sound's thread, is the bar that has begun) and looked up by the rhythm
        # section (groove.develop) and the chopping. `edge` is the dials themselves, as the viewer's messages reach them
        self.course = Course(self.groove.deal_seed, self.groove, log=lambda msg: self.log(msg))
        self.edge, self.groove.develop, self.course_due, self.course_told = self.course.edge, self.course, 0, False
        threading.Thread(target=self._planner, name="chop planner", daemon=True).start()
        # the dropout watcher: how much of each block's time the sound takes to make, and every time it was not ready
        self.load, self.worst, self.drops, self.told = 0.0, 0.0, 0, 0.0
        self.drop_times, self.drop_steps = collections.deque(maxlen=500), collections.deque(maxlen=64)
        # the self-measurement (watch.py): the slices the layers and the clip start, kept by the sound's thread as it
        # plays them (a deque append and nothing more), handed to the watch a bar at a time by a thread of its own
        # (see _watcher); its last report is kept for stands()
        self.chopped = collections.deque(maxlen=2048)        # (sixteenth, layer name, slice index)
        self.blocks = collections.deque(maxlen=1)            # (where the sound had got to, when) as the last block was made
        self.watcher, self.watch_report, self.watch_bar, self.watch_told = Watch(), None, 0, False
        self.watching = self.WATCH                           # close() ends the watch's thread
        if self.WATCH:
            threading.Thread(target=self._watcher, name="watch", daemon=True).start()
        self.clip, self.pending = None, None
        self.clock = (0.0, 0.0, bpm, None, False)     # when a block reaches the speakers: time, beat, tempo, clip seconds, clip moving
        if open_stream:
            try:                                      # the sound outranks whatever else the machine is doing (a film being made, say)
                import ctypes
                ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00000080)      # HIGH_PRIORITY_CLASS
            except Exception:
                pass
            # a fifth of a second in hand: a block that comes late now and then is not heard
            self.stream = sd.OutputStream(samplerate=rate, channels=2, dtype="float32", blocksize=1024,
                                          latency=0.2, callback=self._callback)
            self.stream.start()
            self.log(f"sound: {sd.query_devices(kind='output')['name']} at {rate} Hz, "
                     f"{self.stream.latency * 1000:.0f} ms behind")

    # ------------------------------------------------------------------ asked by the viewer

    def beat(self):
        """Beats since the start (4 to the bar), as heard now."""
        at, beat, bpm, _, _ = self.clock
        if self.stream is None:
            return self.groove.beat()
        return beat + max(-0.5, min(self.stream.time - at, 0.5)) * bpm / 60.0

    def clip_seconds(self):
        """How far into the clip the sound heard now is, in seconds; None until the clip has started."""
        at, _, _, seconds, moving = self.clock
        if seconds is None or self.stream is None:
            return seconds
        return max(0.0, seconds + (max(-0.5, min(self.stream.time - at, 0.5)) if moving else 0.0))

    def premiere(self):
        """True while a new clip is waiting for its bar or playing straight through for the first time."""
        clip = self.clip
        return self.pending is not None or bool(clip and clip["mode"] == "straight" and clip["bars"] < 2 * REPLAY_BARS
                                                and not clip["chopped"])

    def play(self, pcm, rate, channels, name=None, again=False):
        """Queue a film's soundtrack (16-bit PCM): it starts on the next bar line and plays once straight through.
        Given a name, it is then a layer of that name, cut up and waiting to be brought in; returns how that is said."""
        x = np.frombuffer(pcm, "<i2").astype(np.float32).reshape(-1, max(channels, 1)) / 32768.0
        x = x[:, :2] if x.shape[1] >= 2 else np.repeat(x[:, :1], 2, axis=1)
        if rate != self.rate and len(x):
            n = int(round(len(x) * self.rate / rate))
            where = np.linspace(0, len(x) - 1, n)
            x = np.stack([np.interp(where, np.arange(len(x)), x[:, c]) for c in (0, 1)], axis=1)
        mono = x.mean(axis=1) if len(x) else np.zeros(0, np.float32)
        cuts = self._clip_cuts(mono) if len(x) else []
        tones = tone_slices(mono, self.rate) if len(x) else []
        if tones:                                     # the rhythm section's tune is played on this film's sound from now on
            self.groove.set_kit(tones)
            self.log(f"music: the tune is now played on {len(self.groove.kit)} pieces of the films' sound")
        if len(x):                                    # the sub and the kick own everything below about 100 Hz
            spectrum = np.fft.rfft(x, axis=0)
            freqs = np.fft.rfftfreq(len(x), 1.0 / self.rate)
            x = np.fft.irfft(spectrum * np.clip((freqs - 70.0) / 60.0, 0.0, 1.0)[:, None], n=len(x), axis=0)
        x = x.astype(np.float32)
        # src: what is being played instead of the film's sound itself (a slice made backwards or repitched aside), with
        # `film_at` where in the film the picture holds meanwhile; stop: samples until a gated slice is cut off (0: not gated)
        self.pending = {"samples": x, "pos": 0, "mode": "straight", "gate": False, "fresh": False, "bars": 0, "chopped": False,
                        "cuts": cuts, "lead": self._leads(x, cuts), "want": self._want(cuts, True), "role": None, "variants": {},
                        "phrase": 0, "name": None, "src": None, "stop": 0, "gain": 1.0, "film_at": 0}
        name = "".join(c for c in str(name or "").lower() if c.isalnum())[:16]
        if not name or not len(x):
            return ""
        if again and name in self.layers:              # a film shown again: its layer stays as it has been made
            self.film, self.film_sync, self.pending["name"] = name, None, name
            return ""
        films = [n for n, layer in self.layers.items() if layer.get("film")]
        while name not in self.layers and len(films) >= 4:
            del self.layers[films.pop(0)]                         # four films' sounds at most: the oldest makes way
        layer = self._new_layer(self.pending["samples"])
        layer.update(film=True, cut=self.clip_cut, sense=self.clip_sense)
        said = self._cut(layer)
        if not layer["slices"]:
            return ""
        self.layers[name], self.film, self.film_sync, self.pending["name"] = layer, name, None, name
        self._remember(name, layer["audio"], True)
        part_words.set_names(list(self.layers))
        return f'the film\'s sound is the layer called "{name}", {said}. It plays once with its picture, then waits: say "bring in the {name}"'

    def _new_layer(self, x):
        # "in": False while it waits, "armed" once asked for (it enters on the next bar line), then True
        # turn, held: mutated by hand, its slices are put in other places (turn) and that arrangement is held: it is not
        # planned afresh every four bars, and does not thin or thicken as the session's energy moves
        # steps: the sixteenths it plays on (None = planned against the drums); when: every bar (1), the last of every N
        # bars, or "breaks"; settings: the same sound settings and effects as any part
        # role: what it does among the layers (chopper.ROLES: one anchor, one carrier), given each four bars from the role
        # its sound wants by itself (want), unless one was given by hand (role_by_hand); phrase: how many times it has
        # been varied (each a new deal); held_plan: the four bars a held layer keeps playing; lead: the silence each
        # slice starts with, skipped; variants: its slices made backwards or repitched, aside
        return {"audio": x, "cut": "transients", "sense": 1.0, "in": False, "slices": [], "shaped": None, "cuts": [], "bars": -1,
                "phrase": 0, "steps": None, "when": 1, "settings": fresh(), "density": None, "hits": collections.deque(maxlen=200),
                "next": 0, "rev": 0, "film": False, "turn": 0, "held": False, "role": None, "role_by_hand": None, "hand_was": None, "want": None,
                "held_plan": None, "lead": [], "variants": {}}

    def forget_films(self):
        """A new theme: the old story's films leave the layers too. Pulled samples stay."""
        for name in [n for n, layer in self.layers.items() if layer.get("film")]:
            del self.layers[name]
        self.film, self.film_sync = None, None
        part_words.set_names(list(self.layers))
        self._replan()

    def toggle_film(self):
        """The newest film's sound in, or out again. Returns what happened, or '' if there is none."""
        layer = self.layers.get(self.film)
        if layer is None:
            return ""
        layer["in"] = False if layer["in"] else "armed"
        self._replan()
        return f'the {self.film} comes in on the next bar' if layer["in"] else f"the {self.film} is taken out, and waits"

    def take_sample(self, pcm, rate, channels, role, name):
        """A sample pulled from the local library or an archive. A drum hit replaces that drum; something tonal
        becomes what the tune is played on; anything else is cut up and played as a layer of its own, called `name`."""
        x = to_rate(np.frombuffer(pcm, "<i2").astype(np.float32).reshape(-1, max(channels, 1)) / 32768.0, rate, self.rate)
        if not len(x):
            return "nothing in it"
        mono = x.mean(axis=1)
        if role in ("kick", "snare", "hats"):
            self.groove.set_drum(role, mono)
            return f"it is the {role} now"
        if role == "tune":
            tones = tone_slices(mono, self.rate)
            if tones:
                self.groove.set_kit(tones)
                return f"the tune is played on {len(tones)} piece{'s' if len(tones) != 1 else ''} of it"
        name = "".join(c for c in str(name).lower() if c.isalnum())[:16] or "sample"
        pulled = [n for n, layer in self.layers.items() if not layer.get("film")]
        while name not in self.layers and len(pulled) >= 6:
            del self.layers[pulled.pop(0)]                        # six pulled samples at most: the oldest makes way
        layer = self._new_layer(x)
        said = self._cut(layer)
        if not layer["slices"]:
            return "nothing in it to cut"
        self.layers[name] = layer
        self._remember(name, x, False)
        part_words.set_names(list(self.layers))
        return f'a new layer called "{name}", {said}, and waiting: say "bring in the {name}"'

    def _cut(self, layer):
        """Cut a layer's sound into its slices, by the way it is to be cut. Returns how that is said."""
        mono = layer["audio"].mean(axis=1)
        starts, said = cut_points(mono, self.rate, self.groove.bpm, layer["cut"], layer["sense"])
        pieces, kept = cut_slices(layer["audio"], self.rate, starts)
        if pieces:
            cuts = chop.measure(mono, self.rate, kept)[:len(pieces)]
            pieces = pieces[:len(cuts)]
            sounding = [i for i, cut in enumerate(cuts) if cut["level"] > 1e-4] or list(range(len(cuts)))
            cuts, pieces = self._classify([cuts[i] for i in sounding]), [pieces[i] for i in sounding]     # a slice of silence is no slice
            # each slice from where its sound begins: the silence before it is skipped (not for a sound left whole, whose
            # place in the bar is its own)
            lead = [0] * len(pieces) if layer["cut"] == "whole" else [self._quiet_start(piece) for piece in pieces]
            layer.update(cuts=cuts, slices=[piece[n:] for piece, n in zip(pieces, lead)], lead=lead, want=self._want(cuts, layer["film"]),
                         shaped=None, held_plan=None, variants={}, next=0)
            self._replan()
        return said

    def _classify(self, cuts):
        """Each slice named by what it is like (chopper.classify), in place; the cuts as they were if that fails."""
        try:
            chopper.classify(cuts, int(self.groove.step_len))
        except Exception as e:
            self.log(f"the chop engine could not class the slices: {type(e).__name__}: {e}")
        return cuts

    @staticmethod
    def _want(cuts, film):
        """The role a sound would take by itself (chopper.role_of)."""
        try:
            return chopper.role_of(cuts, film=film) if cuts else None
        except Exception:
            return None

    @staticmethod
    def _quiet_start(x):
        """How many samples of near silence (forty decibels under its peak) a piece of sound starts with, less a little so
        that the attack is kept whole; never more than half of it."""
        level = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
        peak = float(level.max()) if len(level) else 0.0
        if peak < 1e-4:
            return 0
        return int(min(max(int(np.argmax(level > 0.01 * peak)) - 32, 0), len(level) // 2))

    def _clip_cuts(self, mono):
        """Where the film's sound is cut, as the clip is cut, each slice classed; a slice of silence is no slice."""
        cuts = chop.measure(mono, self.rate, cut_points(mono, self.rate, self.groove.bpm, self.clip_cut, self.clip_sense)[0])
        return self._classify([cut for cut in cuts if cut["level"] > 1e-4] or cuts)

    def _leads(self, samples, cuts):
        """The silence each slice of a clip starts with, skipped when it is played."""
        return [self._quiet_start(samples[cut["pos"]:cut["pos"] + cut["len"]]) for cut in cuts]

    @staticmethod
    def _recut(how, cut, sense):
        """What "finer" and "coarser" mean from where the cutting stands: (the way to cut, how sensitive)."""
        if how == "next":                              # a re-chop: the next way of cutting, in turn
            ways = [("transients", 1.0), ("transients", 1.6), ("eighths", 1.0), ("sixteenths", 1.0), ("beats", 1.0)]
            at = next((i for i, (c, s) in enumerate(ways) if c == cut and abs(s - sense) < 0.05), -1)
            return ways[(at + 1) % len(ways)]
        if how not in ("finer", "coarser"):
            return how, 1.0
        if cut == "whole":
            return "transients", 1.0
        if cut == "transients":
            return cut, min(max(sense * (1.6 if how == "finer" else 1 / 1.6), 0.25), 6.0)
        if isinstance(cut, int):
            return (min(cut * 2, 32) if how == "finer" else max(cut // 2, 2)), sense
        order = ["bars", "beats", "eighths", "sixteenths"]
        return order[min(max(order.index(cut) + (1 if how == "finer" else -1), 0), 3)], sense

    def _layer(self, part):
        """The layer a part name means, or None: "sample" is the newest pulled sample, "clip" the newest film's sound."""
        if part == "sample":
            part = next((n for n in reversed(self.layers) if not self.layers[n].get("film")), None)
        elif part == "clip":
            part = self.film
        return part if part in self.layers else None

    def _shape(self, name):
        """Run a layer's slices through its sound settings and effects, aside from the audio thread; the plain
        slices play until the shaped ones are ready."""
        layer = self.layers[name]
        layer["rev"] += 1
        rev, settings, g = layer["rev"], {**layer["settings"], "layers": []}, self.groove
        settings["filth"] = edge_dials.filth(settings["filth"], self.course.params(self.course_due + 1))     # the edge's damage on its knob
        if summary(settings) in ("", "muted", "louder", "quieter"):
            layer["shaped"] = None
            return

        def work():
            _stand_back()
            with g.one_at_a_time:
                if layer["rev"] == rev:
                    shape()

        def shape():
            shaped = []
            for piece in layer["slices"]:
                sides = []
                for c in (0, 1):
                    x = piece[:, c]
                    if settings["octave"] or settings["pitch"]:
                        x = repitch(x, 12 * settings["octave"] + settings["pitch"])
                    if settings["length"] < 0.95:
                        x = fade(x[:max(int(len(x) * settings["length"]), 64)], self.rate, 0.004)
                    x = g._finish(np.asarray(x, dtype=np.float32), settings, 220.0)
                    if settings["room"]:
                        x = reverb(x, g.room, settings["room"])
                    sides.append(x)
                both = np.zeros((max(len(side) for side in sides), 2), np.float32)
                for c, side in enumerate(sides):
                    both[:len(side), c] = side
                shaped.append(both)
            if layer["rev"] == rev:
                layer["shaped"] = shaped
        g.jobs.put(work)                                # made by the rhythm section's worker, in turn

    # ------------------------------------------------------------------ the chopping, planned aside

    CLIP = " clip"          # the clip's own name among the layers being planned (no layer's name has a space)
    PLAIN = {"gain": 1.0, "reverse": False, "semis": 0.0, "gate": None}

    def _replan(self, thing=None):
        """Something about the chopping was changed by hand: the plans for this group of four bars and the next are made
        again, aside (the old ones play until the new are ready, a few milliseconds). A held layer or clip given as
        `thing` also lets go of the four bars it was holding, so the change is heard."""
        if thing is not None:
            thing["held_plan"] = None
        self.plan_rev += 1
        step = self.groove.step
        self._ask(step // 64)
        if step % 64 >= 40:
            self._ask(step // 64 + 1)

    def _ask(self, group):
        if group not in self.plan_asked and group != self.plan_busy:
            self.plan_asked.add(group)
            self.plan_wake.set()

    def _keep_planned(self, step):
        """From the sound's thread, on each sixteenth: is this group planned, and in its last bar the next? If not (or
        a change by hand has been made since), the planner is asked. Nothing is planned here."""
        group = step // 64
        for ahead in ((group, group + 1) if step % 64 >= 48 else (group,)):
            made = self.plans.get(ahead)
            if made is None or made["rev"] != self.plan_rev:
                self._ask(ahead)

    def _event(self, key, step):
        """What the plan for this group says the layer `key` does on this sixteenth: None (carry on) if there is none yet."""
        made = self.plans.get(step // 64)
        events = made["plans"].get(key) if made is not None else None
        return events[step % 64] if events else None

    def _style_at(self, group):
        """The chop style a group of four bars is played in: a change is heard from the four-bar line after it was made."""
        was, until = self.style_was
        return was if group < until else self.chop_style

    def _planner(self):
        """The planner: four bars of chopping for every layer that is in, a bar before they are played (and again at
        once when something is changed by hand), on a thread of its own below the sound's. The sound's thread only
        looks the plans up, and plays on as it was (carries on) if one is late."""
        _stand_back()
        while True:
            self.plan_wake.wait()
            self.plan_wake.clear()
            self._advance_course()
            while self.plan_asked:
                try:
                    group = min(list(self.plan_asked))
                    self.plan_busy = group
                    self.plan_asked.discard(group)
                    self._plan_group(group)
                except Exception as e:                  # a plan that trips must not stop the planning
                    if not self.plan_told:
                        self.plan_told = True
                        self.log(f"the chopping could not be planned: {type(e).__name__}: {e}")
                finally:
                    self.plan_busy = None

    def _advance_course(self):
        """On the planner's thread, at each bar line: the edge and development worked out ahead (course.py). When the
        edge's numbers move under groups already planned, those are planned again; when the damage it adds moves, the
        layers are shaped again (on the rhythm section's worker)."""
        try:
            did = self.course.advance(self.course_due, self.layers)
        except Exception as e:                          # the course that trips must not stop the planning
            if not self.course_told:
                self.course_told = True
                self.log(f"the edge and development could not be worked out: {type(e).__name__}: {e}")
            return
        if did["replan"]:
            self._replan()
        if did["filth"] is not None:
            for name in list(self.layers):
                if name in self.layers:
                    self._shape(name)

    def _plan_group(self, group):
        """Plan the group of four bars starting at bar 4 * `group` for every layer that is in or about to be (and the
        clip, while it is chopped): roles given out, then each layer planned in turn, the anchor first and the
        carrier next, each keeping off the sixteenths the layers before it took. Then the slices it will play
        backwards or repitched are made, so that the sound's thread need not."""
        g, rev, bar = self.groove, self.plan_rev, group * 4
        style, slot_len = self._style_at(group), int(g.step_len)
        drums = [g.drums_ahead(bar + i) if g.composer is None else {"kick": [0, 4, 8, 12], "snare": [4, 12]} for i in range(4)]
        chopped, placed = {}, {}
        for name, layer in list(self.layers.items()):
            if layer["in"] and layer["slices"] and layer["settings"]["on"] and layer["settings"]["level"] > 0:
                (chopped if layer["steps"] is None else placed)[name] = layer
            if layer["steps"] is not None or not layer["in"]:
                layer["role"] = None                    # placed by hand, or out: it holds no role among the chopped
        clip = self.clip
        if clip is not None and not clip.get("name") and self.chop and clip["chopped"] and clip["cuts"] and self.clip_place is None:
            chopped[self.CLIP] = clip
        self._roles(chopped, group)
        # the sixteenths already held: by the layers placed by hand, and by held layers, which do not move
        taken = set()
        for name, layer in placed.items():
            taken |= {b * 16 + s for b in range(4) if self._in_bar(layer["when"], (bar + b) * 16) for s in layer["steps"] if 0 <= s < 16}
        for name, thing in chopped.items():
            if thing.get("held") and thing.get("held_plan") is not None:
                taken |= self._cells(thing, thing["held_plan"], bar)
        rank, names = {"anchor": 0, "carrier": 1}, list(chopped)
        plans = {}
        for name in sorted(names, key=lambda name: (rank.get(chopped[name].get("role"), 2), names.index(name))):
            thing = chopped[name]
            if thing.get("held") and thing.get("held_plan") is not None:
                plans[name] = thing["held_plan"]       # held by hand: the same four bars, until it is mutated or changed again
                continue
            density = self.chop_density if thing is clip else thing.get("density")
            density = min(max(g.energy if density is None else density, 0.0), 1.0)
            if self.chop_div == 1:                     # "double": busier chopping, the odd sixteenths too
                density = min(density + 0.25, 1.0)
            events = self._chop_plan(name, thing, style, drums, taken, bar, density, slot_len)
            if thing.get("held"):
                thing["held_plan"] = events
            plans[name] = events
            taken |= self._cells(thing, events, bar)
        for name, events in plans.items():             # the slices this group plays backwards or repitched, made now
            for event in events:
                if isinstance(event, dict) and (event["reverse"] or event["semis"]):
                    self._variant(chopped[name], event["slice"], event["reverse"], event["semis"], make=True)
        kept = {k: v for k, v in self.plans.items() if k >= group - 1}
        kept[group] = {"rev": rev, "plans": plans, "style": style}
        self.plans = kept

    def _chop_plan(self, name, thing, style, drums, taken, bar, density, slot_len):
        """Four bars of events for one layer, from the chop engine; checked, so that nothing it says can trip the sound.
        The course has its say (course.py): the layer's source clock deals it anew, its odds clock moves its density
        (not a density set by hand), and each bar's preset is the style's as development's processing and the edge's
        dials have it there; where they differ inside the group (an excursion on the chopped layers, a bar or two at
        its end) it is planned once for each and the bars put together."""
        phrase = max(int(thing.get("phrase") or 0), 0)
        seed = name.strip() if phrase == 0 else f"{name.strip()}/{phrase}"      # varied by hand: a new deal
        grown = self.course.layer(name, bar) if thing is not self.clip else None
        if grown and grown["source"]:
            seed = f"{seed}~{grown['source']}"                                  # development's new deal: the same sound read another way
        if grown and thing.get("density") is None:
            density = min(max(density + grown["odds"], 0.0), 1.0)
        try:
            events, made = [None] * 64, {}
            for b, (preset, more) in enumerate(self.course.presets(style, bar, grown)):
                key = (repr(sorted(preset.items())), more)
                if key not in made:
                    made[key] = chopper.plan(thing["cuts"], role=thing.get("role") or "colour", style=style, drums=drums, taken=frozenset(taken),
                                             bar=bar, seed=seed, density=min(max(density + more, 0.0), 1.0), slot_len=slot_len,
                                             turn=thing.get("turn", 0), held=bool(thing.get("held")), preset=preset)
                events[16 * b:16 * b + 16] = list(made[key])[16 * b:16 * b + 16]
        except Exception as e:                          # the engine failed: the old four-bar phrase, rather than silence
            if not self.plan_told:
                self.plan_told = True
                self.log(f"the chop engine failed, so the old phrase plays: {type(e).__name__}: {e}")
            events = chop.plan(thing["cuts"], drums[0]["kick"], drums[0]["snare"], density, bar // 4 + phrase, slot_len,
                               busy=self.chop_div == 1, turn=thing.get("turn", 0))
            events = [dict(self.PLAIN, slice=e) if isinstance(e, int) else e for e in events]
        return self._checked(events, len(thing["cuts"]))

    def _checked(self, events, count):
        """A plan as the sound's thread can trust it: 64 entries, each None, "rest" or a whole event for a slice there is."""
        out = [None] * 64
        for i, e in enumerate(list(events or [])[:64]):
            if e == "rest":
                out[i] = "rest"
            elif isinstance(e, dict) and isinstance(e.get("slice"), int) and 0 <= e["slice"] < count:
                gate = e.get("gate")
                out[i] = {"slice": e["slice"], "gain": min(max(float(e.get("gain", 1.0) or 0.0), 0.0), 2.0), "reverse": bool(e.get("reverse")),
                          "semis": float(e.get("semis") or 0.0), "gate": gate if isinstance(gate, (int, float)) and gate > 0 else None}
        return out

    def _cells(self, thing, events, bar):
        """The sixteenths of the group a plan starts slices on, in the bars the layer really plays in."""
        when = self.clip_when if thing is self.clip else thing.get("when", 1)
        return {c for c in chopper.cells(events) if self._in_bar(when, (bar + c // 16) * 16)}

    def _roles(self, things, group):
        """Give every chopped layer its role for this group: one anchor and one carrier (chopper.assign_roles), a
        layer that holds one keeping it; a role given by hand wins, and one that clashes with it moves aside."""
        hand = {name: self._hand_role(thing, group) for name, thing in things.items() if self._hand_role(thing, group) in chopper.ROLES}
        wants = dict(hand)
        for name, thing in things.items():
            if name not in hand:
                held = thing.get("role")
                grown = self.course.layer(name, group * 4) if thing is not self.clip else None
                if grown and grown["role"] and not thing.get("held"):   # its role clock has ticked: the role development gives it
                    wants[name] = grown["role"]
                else:
                    wants[name] = held if held in ("anchor", "carrier") else thing.get("want") or "colour"
        try:
            got = dict(chopper.assign_roles(wants))
        except Exception:
            got = dict(wants)
        got.update(hand)
        for name in things:
            if name not in hand and got.get(name) in ("anchor", "carrier") and got[name] in hand.values():
                got[name] = "colour"
            things[name]["role"] = got.get(name) if got.get(name) in chopper.ROLES else "colour"

    @staticmethod
    def _hand_role(thing, group):
        """The role given by hand that a layer plays a group in: a change is heard from the four-bar line after it."""
        was, until = thing.get("hand_was") or (None, 0)
        return was if group < until else thing.get("role_by_hand")

    def set_role(self, name, role):
        """A layer's role in the chop, given by hand (one of chopper.ROLES), or None to give it back to the engine.
        Heard from the next four-bar line; kept by the memories. Returns what happened, as text."""
        name = self._layer(name)
        if name is None:
            return "there is no such layer"
        role = str(role).strip().lower() if role is not None else None
        if role in ("auto", ""):
            role = None
        if role == "color":
            role = "colour"
        if role is not None and role not in chopper.ROLES:
            return f'there is no role called "{role}": there are ' + ", ".join(chopper.ROLES)
        layer, group = self.layers[name], self.groove.step // 64 + 1
        layer["hand_was"], layer["role_by_hand"] = (self._hand_role(layer, group - 1), group), role
        self._replan()
        return f"the {name} plays the {role} from the next four-bar line" if role else f"the {name}'s role is the engine's choice again"

    def _piece(self, thing, which):
        """A slice as it plays forwards, from where its sound begins, and what it was taken from."""
        if "samples" in thing:                          # the clip: its slices are read from the film's sound itself
            cut = thing["cuts"][which]
            lead = thing["lead"][which] if which < len(thing.get("lead", ())) else 0
            return thing["samples"][cut["pos"] + lead:cut["pos"] + cut["len"]], thing["samples"]
        shaped = thing["shaped"]
        source = shaped if shaped and which < len(shaped) else thing["slices"]
        return source[which], source

    def _variant(self, thing, which, reverse, semis, make=False):
        """A slice played backwards, repitched (as a sampler does it), or both: made aside by the planner (`make`) and
        kept by slice and pitch; the sound's thread only looks it up, and gets None if it is not there yet."""
        piece, source = self._piece(thing, which)
        key = (which, bool(reverse), round(float(semis), 2))
        variants = thing.setdefault("variants", {})
        kept = variants.get(key)
        if kept is not None and kept[0] is source and kept[1] is thing["cuts"]:
            return kept[2]
        if not make:
            return None
        x = piece
        if reverse:                                     # from its end: the quiet the tail dies into is skipped too
            x = x[::-1]
            x = x[self._quiet_start(x):]
        if semis:
            x = np.stack([repitch(np.ascontiguousarray(x[:, c]), semis) for c in range(x.shape[1])], axis=1)
        x = np.ascontiguousarray(x, dtype=np.float32)
        if len(variants) > 256:
            variants.clear()
        variants[key] = (source, thing["cuts"], x)
        return x

    def _layers_step(self, step, at):
        """On each sixteenth: what each sample layer does now, by its plan (or where it was placed by hand)."""
        slot = step % 16
        for name, layer in list(self.layers.items()):
            settings, slices = layer["settings"], layer["slices"]
            if slot == 0:
                if layer["in"] == "armed":                 # asked for: it comes in here, on the bar line
                    layer["in"], layer["bars"], layer["next"] = True, -1, 0
                layer["bars"] += 1
            if layer["in"] is not True or not settings["on"] or settings["level"] <= 0 or not self._in_bar(layer["when"], step):
                continue
            if layer["steps"] is not None:                # placed by hand: its slices in order, one on each of those sixteenths
                event = None
                if slot in layer["steps"] and slices:
                    event, layer["next"] = dict(self.PLAIN, slice=layer["next"] % len(slices)), layer["next"] + 1
            else:                                          # chopped: looked up in the plan made aside (see _planner)
                event = self._event(name, step)
            if event == "rest":                            # it stops here, with a short fade
                self._choke(name, at)
                continue
            if not isinstance(event, dict) or event["slice"] >= len(slices):
                continue
            self._choke(name, at)                          # one slice of a layer at a time, as on a sampler
            piece = self._sounding(layer, event, step)
            if not len(piece):
                continue
            level = (0.8 if layer["film"] else 0.55) * settings["level"] * event["gain"]
            self.shots.append([piece, -at, level, self.groove.gives_way(settings), name, len(piece)])
            layer["hits"].append(step)
            self.chopped.append((step, name, event["slice"]))       # for the watch (nothing else is done with it here)
            if name == self.film:                         # the picture goes to where this slice begins in the film
                which = event["slice"]
                cut, lead = layer["cuts"][which], (layer["lead"][which] if which < len(layer["lead"]) else 0)
                begin = cut["pos"] + lead
                end = min(cut["pos"] + cut["len"], begin + int(len(piece) * 2 ** (event["semis"] / 12.0)))
                # played backwards, the picture holds on the slice's last frame, where the sound it plays begins
                self.film_sync = [end, end - 1] if event["reverse"] else [begin - at, end]

    def _sounding(self, layer, event, step):
        """The sound a layer's event plays: the slice (as its settings shaped it), backwards or repitched as made aside,
        and gated after its sixteenths (the fade at the cut is put on as it is mixed)."""
        which = event["slice"]
        if event["reverse"] or event["semis"]:
            piece = self._variant(layer, which, event["reverse"], event["semis"])
            if piece is None:                              # not made yet: as it is (backwards costs nothing), and asked for
                piece = self._piece(layer, which)[0]
                piece = piece[::-1] if event["reverse"] else piece
                self._ask(step // 64)
        else:
            piece = self._piece(layer, which)[0]
        end = len(piece)
        if not layer["shaped"] and layer["cut"] != "whole":    # unshaped, a slice is never longer than its length allows
            end = min(end, int(self.rate * 60.0 / self.groove.bpm * layer["settings"]["length"]))
        if event["gate"]:
            end = min(end, int(event["gate"] * self.groove.step_len))
        return piece[:max(end, 0)]

    def _choke(self, name, at):
        """The layer `name` stops sounding `at` samples into this block, with a short fade."""
        for shot in self.shots:
            if shot[4] == name:
                shot[5] = min(shot[5], max(shot[1] + at, 0) + FADE)

    def _in_bar(self, when, step):
        """Does a layer told to play `when` (1 = every bar, N = the last bar of every N, "breaks") play in this bar?"""
        if when == "breaks":
            return self.groove.break_end > step
        return when <= 1 or (step // 16) % when == when - 1

    def set_parts(self, pairs):
        """Change parts by word. The film's own sound is "clip"; each sample layer goes by its name ("sample" is the newest)."""
        from .parts import DEFAULTS, WORDS, change
        said = []
        for part, word in [(self._layer(part), word) for part, word in pairs if self._layer(part)]:
            layer = self.layers[part]
            if WORDS.get(word, ("",))[0] == "pattern":     # how it is chopped: busier, sparser, vary, as written
                how = WORDS[word][1][1]
                now = self.groove.energy if layer["density"] is None else layer["density"]
                if how in ("busier", "sparser", "double", "half"):
                    layer["density"] = min(max(now + (0.3 if how in ("busier", "double") else -0.3), 0.0), 1.0)
                elif how == "reset":
                    layer["density"], layer["steps"], layer["when"], layer["turn"], layer["held"] = None, None, 1, 0, False
                    layer["role_by_hand"], layer["hand_was"] = None, None
                elif how == "vary":                     # a new deal: the chop engine plays it another way
                    layer["phrase"] += 1
                elif how == "mutate" and layer["steps"] is not None:      # placed by hand (or whole): it lands an eighth later
                    layer["steps"] = sorted({(at + 2) % 16 for at in layer["steps"]})
                elif how == "mutate":                   # the same slices, put in other places; and they stay there
                    layer["turn"] += 1
                    layer["held"], layer["density"] = True, now
                if how == "mutate" and layer["in"] is False:               # mutating a layer that waits brings it in: it is meant to be heard
                    layer["in"] = "armed"
                self._replan(layer)
            else:
                change(layer["settings"], word)
                if WORDS.get(word, ("",))[0] == "reset":   # as it arrived: its sound, and when and where it plays
                    layer["density"], layer["steps"], layer["when"], layer["turn"], layer["held"] = None, None, 1, 0, False
                    layer["role_by_hand"], layer["hand_was"] = None, None
                    self._replan(layer)
                self._shape(part)
            said.append(f"{part} {word}")
        pairs = [pair for pair in pairs if not self._layer(pair[0])]
        mine = [(part, word) for part, word in pairs if part == "clip"]
        for _, word in mine:
            if WORDS.get(word, ("",))[0] == "pattern":     # how the film's sound is chopped: busier, sparser, double, half, vary, fill, reset
                how = WORDS[word][1][1]
                if how in ("busier", "sparser"):
                    now = self.groove.energy if self.chop_density is None else self.chop_density
                    self.chop_density = min(max(now + (0.3 if how == "busier" else -0.3), 0.0), 1.0)
                elif how in ("double", "half"):
                    self.chop_div = 1 if how == "double" else 2        # use the odd sixteenths too, or not
                elif how == "fill":
                    self.replay()                                     # the whole clip straight through, from the next bar
                elif how == "reset":
                    self.chop_density, self.chop_div, self.clip_when, self.clip_place = None, 2, 1, None
                if self.clip is not None:
                    if how == "vary":
                        self.clip["phrase"] += 1                      # a new deal
                    self._replan(self.clip)                           # planned again, heard at once
                continue
            state = {**DEFAULTS, "level": self.clip_level / 0.9, "on": self.clip_on}
            change(state, word)
            self.clip_level, self.clip_on = 0.9 * state["level"], state["on"]
        said.append(self.groove.set_parts([pair for pair in pairs if pair[0] != "clip"]))
        return ", ".join(x for x in said + [", ".join(f"clip {word}" for _, word in mine)] if x)

    LAYER_KEEPS = ("steps", "when", "density", "cut", "sense", "phrase", "turn", "held", "role", "role_by_hand")
    GROOVE_KEEPS = ("style", "note", "mode", "swing", "sub", "twinkle", "riff", "bells", "bell_order", "movement", "kit",
                    "deal_seed", "sub_seed", "hook_seed", "sub_held", "hook_held", "by_hand", "tune_every", "signature", "lead_choice")
    LAYER_SOUND = ("audio", "slices", "cuts", "film", "lead", "want")      # a layer's sound itself: kept so that a layer gone since can come back
    MIXER_KEEPS = ("super", "clip_level", "clip_on", "clip_when", "clip_place", "clip_cut", "clip_sense", "chop_density", "chop_div",
                   "chop_style")

    def memorise(self, slot):
        """Everything about the music as it stands, kept under a number to come back to: what every part plays, how
        every part sounds (its knob, its character, its effects, whether it is muted), the style, key and riffs, and
        for every layer whether it is in, when and where it plays and how it is cut. Not the story, the pictures or
        the films, and not the tempo. Kept in memory only: it is gone when the session ends."""
        g = self.groove
        self.memory[slot] = copy.deepcopy({
            "groove": {key: getattr(g, key) for key in self.GROOVE_KEEPS}, "pattern": g.pattern, "parts": g.parts,
            "mixer": {key: getattr(self, key) for key in self.MIXER_KEEPS}, "own": self.own, "film": self.film,
            "layers": {name: {"settings": layer["settings"], "in": bool(layer["in"]), **{key: layer[key] for key in self.LAYER_KEEPS + self.LAYER_SOUND}}
                       for name, layer in self.layers.items()},
            "edge": self.course.keep()})                       # the edge: whose the dials are, where they stand, the lips, the roller
        return f"memorised as {slot}: " + (", ".join(f"{part} {stands * 100:.0f}" for part, stands in self.knobs().items() if stands > 0.005)
                                          or "every knob at nothing")

    def recall(self, slot):
        """Back to how the music stood when that number was memorised. A layer that has gone since comes back; one
        that has arrived since is taken out, since it was not part of it. Returns what happened, as text."""
        kept = copy.deepcopy(self.memory.get(slot))
        if kept is None:
            return f"nothing has been memorised as {slot}"
        g = self.groove
        for key, value in kept["groove"].items():
            setattr(g, key, value)
        g.kit_id += 1                                           # the tune's sounds are made again, on the pieces it had
        with g.waiting_lock:                                    # a change of structure the session had waiting is not laid over the memory
            g.waiting.clear()
        g.changed_at = g.step
        g.scene_set = True                                      # going back to a memory sets the scene, if nothing had yet
        g.pattern = kept["pattern"]
        for part, settings in kept["parts"].items():
            if part in g.parts:
                g.parts[part] = settings
                g.rev[part] += 1                                  # its sounds are made again, as they were
        style = kept["mixer"].pop("chop_style", self.chop_style)
        for key, value in kept["mixer"].items():
            setattr(self, key, value)
        self.set_chop_style(style)                              # the chopping as it was, from the next four-bar line
        self.course.restore(kept.get("edge"))                   # the edge's dials as they were (development's clocks run on)
        self.own = kept["own"]
        if self.clip is not None:
            self.clip["held_plan"] = None
        for name, was in kept["layers"].items():                # a layer that has gone since: back, with the sound it had
            if name not in self.layers:
                layer = self._new_layer(was["audio"])
                layer.update({key: was[key] for key in self.LAYER_SOUND})
                self.layers[name] = layer
        self.film, self.film_sync = (kept.get("film") if kept.get("film") in self.layers else self.film), None
        for name, layer in self.layers.items():
            was = kept["layers"].get(name)
            if was is None:
                layer["in"] = False
                continue
            recut = (layer["cut"], layer["sense"]) != (was["cut"], was["sense"])
            layer.update({key: was[key] for key in self.LAYER_KEEPS})
            layer["settings"], layer["held_plan"], layer["next"], layer["hand_was"] = was["settings"], None, 0, None
            layer["in"] = (layer["in"] or "armed") if was["in"] else False
            if recut:
                self._cut(layer)
            self._shape(name)
        part_words.set_names(list(self.layers))
        self._replan()
        return f"back to {slot}"

    HOWS = ("smooth", "drop", "breakdown")

    def play_line(self, entries, loop=False):
        """Play memories in order: [{"slot": 2, "bars": 8, "how": "smooth"}, ...]. Each is held for its bars (4, 8 or 16)
        and left in its way: "smooth" moves its knobs, volumes and levels toward the next a bar at a time and changes
        over on the bar line; "drop" takes the low end away for the last bar while the drums run on, and the next lands on
        the one; "breakdown" does that for the second half. The first comes in on the next bar line. An empty list
        stops it where it is. Returns what will happen, as text."""
        line = []
        for entry in entries if isinstance(entries, list) else []:
            if isinstance(entry, dict) and entry.get("slot") in self.memory:
                line.append({"slot": entry["slot"], "bars": entry.get("bars") if entry.get("bars") in (4, 8, 16) else 8,
                             "how": entry.get("how") if entry.get("how") in self.HOWS else "smooth"})
        self.line, self.line_at, self.line_bars, self.line_loop = line, -1, 0, bool(loop) and len(line) > 1
        if not line:
            return "the timeline is stopped; the music stays as it is"
        return ("the timeline: " + ", then ".join(f"{e['slot']} for {e['bars']} bars" + (f" ({e['how']})" if i + 1 < len(line) or self.line_loop else "")
                                                  for i, e in enumerate(line)) + (", round and round" if self.line_loop else ""))

    def _remember(self, name, audio, film):
        """A sound that has become a layer is kept for the session (the last sixty), and noted for whoever shows them."""
        number, self.sound_next = self.sound_next, self.sound_next + 1
        self.sounds[number] = {"name": name, "audio": audio, "film": film}
        for old in list(self.sounds)[:-60]:
            del self.sounds[old]
        mono = np.abs(audio).max(axis=1) if audio.ndim == 2 else np.abs(audio)
        chunk = max(len(mono) // 60, 1)
        peaks = [float(mono[i:i + chunk].max()) for i in range(0, chunk * 60, chunk) if i < len(mono)]
        self.sound_news.append({"sound": number, "name": name, "film": film, "peaks": peaks})

    def heard_new(self):
        """A sound that has become a layer since this was last asked, once; None when there is no more."""
        return self.sound_news.popleft() if self.sound_news else None

    def bring_back(self, number):
        """A sound of the session back as a layer under the name it had, coming in on the next bar: made again if it
        has gone, brought in if it is there and waiting. Returns what happened, as text."""
        kept = self.sounds.get(number)
        if kept is None:
            return "that sound is no longer kept"
        name = kept["name"]
        layer = self.layers.get(name)
        if layer is None or layer["audio"] is not kept["audio"]:
            layer = self._new_layer(kept["audio"])
            layer["film"] = kept["film"]
            if kept["film"]:
                layer.update(cut=self.clip_cut, sense=self.clip_sense)
            self._cut(layer)
            if not layer["slices"]:
                return f"there is nothing in the {name} to cut"
            self.layers[name] = layer
            part_words.set_names(list(self.layers))
        layer["in"] = layer["in"] or "armed"
        self._replan()
        return f"the {name} comes in on the next bar"

    def crossfade(self, a, b, at):
        """Somewhere between two memories: `at` is 0 for all of `a`, 1 for all of `b`. Every knob, volume and level
        that both have as a number stands that share of the way between them. What cannot be mixed (what the parts
        play, the style and key, the characters, which layers are in) is `a`'s on its half and `b`'s on the other,
        changing over in the middle. It stops the timeline. Returns the memory whose side it has just crossed to,
        or None."""
        if a not in self.memory or b not in self.memory or a == b:
            return None
        at = min(max(float(at), 0.0), 1.0)
        side = a if at < 0.5 else b
        crossed = None
        self.line = []
        if self.fade_side != (a, b, side):
            self.fade_side, crossed = (a, b, side), side
            self.recall(side)
        self._toward(a, b, at)
        return crossed

    def arrived(self):
        """The memory the timeline has just gone to, once, for whoever shows it; None if it has not moved."""
        return self.arrivals.popleft() if self.arrivals else None

    def _line_bar(self):
        """At the last sixteenth of every bar, from the sound's own thread: what the timeline does on the bar line
        that follows. It only decides; the work is handed to the worker."""
        line = self.line
        if not line:
            return
        if self.line_at < 0:
            self.line_jobs.append(("go", 0))
        else:
            self.line_bars += 1
            entry = line[min(self.line_at, len(line) - 1)]
            follows = self.line_at + 1 if self.line_at + 1 < len(line) else 0 if self.line_loop else None
            left = entry["bars"] - self.line_bars
            if follows is None:
                if left <= 0:
                    self.line = []                              # the last one: the timeline is over, and the music stays there
                return
            if left <= 0:
                self.line_jobs.append(("go", follows))
            elif entry["how"] == "smooth":
                self.line_jobs.append(("toward", entry["slot"], line[follows]["slot"], self.line_bars / entry["bars"]))
            elif left == (1 if entry["how"] == "drop" else max(entry["bars"] // 2, 1)):
                g = self.groove                                 # the drums and bass out from the bar line until the next memory lands
                g.break_start, g.break_end = g.step, g.step + left * 16
                return
            else:
                return
        self.line_wake.set()

    def _line_worker(self):
        while True:
            self.line_wake.wait()
            self.line_wake.clear()
            while self.line_jobs:
                job = self.line_jobs.popleft()
                try:
                    if job[0] == "go" and job[1] < len(self.line):
                        self.line_at, self.line_bars = job[1], 0
                        self.recall(self.line[job[1]]["slot"])
                        self.arrivals.append(self.line[job[1]]["slot"])
                    elif job[0] == "toward":
                        self._toward(*job[1:])
                except Exception as e:                          # a timeline that trips must not take the sound with it
                    self.log(f"the timeline stopped: {type(e).__name__}: {e}")
                    self.line = []

    def _toward(self, here, there, share):
        """Part of the way from one memory to another: every knob, volume and level that both have as a number."""
        a, b = self.memory.get(here), self.memory.get(there)
        if a is None or b is None:
            return
        between = lambda x, y: {key: x[key] + (y[key] - x[key]) * share for key in ("filth", "level", "drive", "tone", "length", "duck")    # noqa: E731
                                if isinstance(x.get(key), (int, float)) and isinstance(y.get(key), (int, float)) and abs(y[key] - x[key]) > 1e-6
                                and not isinstance(x[key], bool)}
        ops = [{"part": part, "set": between(was, b["parts"][part])} for part, was in a["parts"].items() if part in b["parts"]]
        ops += [{"part": name, "set": between(was["settings"], b["layers"][name]["settings"])} for name, was in a["layers"].items()
                if name in b["layers"] and name in self.layers]
        self.patch([op for op in ops if op["set"]], lifted=True)
        score = {key: a["groove"][key] + (b["groove"][key] - a["groove"][key]) * share for key in ("sub", "twinkle", "swing")
                 if isinstance(a["groove"].get(key), (int, float)) and isinstance(b["groove"].get(key), (int, float))}
        if score:
            self.groove.set_score(score)

    def knobs(self):
        """Every part that has a knob, and where it stands: the rhythm section's parts and every layer."""
        return {**{part: settings["filth"] for part, settings in self.groove.parts.items()},
                **{name: layer["settings"]["filth"] for name, layer in self.layers.items()}}

    def stands(self):
        """Where every knob, volume and mute stands, and the super knob: for the panels, which follow the session."""
        each = {**self.groove.parts, **{name: layer["settings"] for name, layer in self.layers.items()}}
        return {"knobs": {part: round(s["filth"], 3) for part, s in each.items()}, "levels": {part: round(s["level"], 3) for part, s in each.items()},
                "muted": sorted(part for part, s in each.items() if not s["on"]), "super": round(self.super, 3),
                "in": [name for name, layer in self.layers.items() if layer["in"]], "style": self.groove.style,
                "lead": self.groove.lead_voice(self.groove.step // (16 * 32)), "lead_choice": self.groove.lead_choice,
                "chop_style": self.chop_style, "roles": {name: layer["role"] for name, layer in self.layers.items()},
                "role_by_hand": {name: layer["role_by_hand"] for name, layer in self.layers.items()},
                "watch": watch_compact(self.watch_report), **self.course.stands()}

    def set_chop_style(self, name):
        """How the layers and the clip are chopped: one of chopper.STYLES (jungle, atmospheric, drumfunk ...), heard
        from the next four-bar line, and kept by the memories. Returns what happened, as text."""
        name = str(name or "").strip().lower()
        if name not in chopper.STYLES:
            return f'there is no chop style called "{name}": there are ' + ", ".join(chopper.STYLES)
        if name == self.chop_style:
            return f"the chopping is {name} already"
        group = self.groove.step // 64 + 1             # the four bars playing now stay as they were
        self.style_was, self.chop_style = (self._style_at(group - 1), group), name
        self._replan()
        return f"the chopping goes {name} from the next four-bar line"

    def set_super(self, value):
        """The super knob: it moves every other knob by as much as it moves itself, each from where it was set by hand
        (a knob cannot go below nothing or past full, but it remembers where it was and comes back)."""
        self.super = min(max(float(value), 0.0), 1.0)
        now = self.knobs()
        for part, stands in now.items():
            self.own.setdefault(part, stands)
        self.patch([{"part": part, "set": {"filth": min(max(self.own[part] + self.super, 0.0), 1.0)}} for part in now], lifted=True)
        return self.knobs()

    def patch(self, ops, lifted=False):
        """Open changes to parts: effects, extra layers, settings, the sixteenths a part plays on, and for a sample
        layer or the clip which bars it plays in. The clip's sound itself takes level and on/off only."""
        from .parts import sanitize
        clean = sanitize(ops)
        taken = []
        for op in clean:
            name = self._layer(op["part"])
            if "filth" in op.get("set", {}) and not lifted:     # a knob turned by hand: the super knob adds to it from here
                self.own[name or op["part"]] = op["set"]["filth"] - self.super
            if name:
                layer = self.layers[name]
                if "drop" in op:
                    del self.layers[name]
                    part_words.set_names(list(self.layers))
                elif "bring" in op:
                    layer["in"] = (layer["in"] or "armed") if op["bring"] else False
                elif "chop" in op:
                    was = layer["cut"]
                    layer["cut"], layer["sense"] = self._recut(op["chop"], layer["cut"], layer["sense"])
                    if layer["cut"] == "whole":                 # one sound again: from the one, as often as its length allows
                        long = len(layer["audio"]) / self.rate / (240.0 / self.groove.bpm)
                        layer["steps"], layer["when"] = [0], next(n for n in (1, 2, 4, 8, 16) if n >= long or n == 16)
                    elif was == "whole":                        # cut up again: back to being planned against the drums, every bar
                        layer["steps"], layer["when"] = None, 1
                    if layer["film"]:                       # and the films that follow are cut the same way
                        self.clip_cut, self.clip_sense = layer["cut"], layer["sense"]
                    self._cut(layer)
                    self._shape(name)
                elif "steps" in op:                         # saying where or when it plays brings it in too
                    layer["steps"], layer["next"], layer["in"] = (list(op["steps"]) or None), 0, layer["in"] or "armed"
                elif "when" in op:
                    layer["when"], layer["in"] = op["when"], layer["in"] or "armed"
                else:
                    apply_op(layer["settings"], op)
                    if op.get("clear") == "all":
                        layer["steps"], layer["when"], layer["density"], layer["turn"], layer["held"] = None, 1, None, 0, False
                    if not set(op.get("set", {"*": 0})) <= QUICK:       # its volume and its ducking need nothing made again
                        self._shape(name)
                if set(op) & {"drop", "bring", "steps", "when", "clear"} or set(op.get("set", {})) & {"on", "level"}:
                    self._replan(layer)                     # who plays, and where, has changed: the chopping is planned again
                taken.append({**op, "part": name})
            elif op["part"] == "clip" and "set" in op:
                self.clip_level = 0.9 * op["set"].get("level", self.clip_level / 0.9)
                self.clip_on = op["set"].get("on", self.clip_on)
            elif op["part"] == "clip" and "chop" in op:
                self.clip_cut, self.clip_sense = self._recut(op["chop"], self.clip_cut, self.clip_sense)
                for clip in (self.clip, self.pending):
                    if clip is not None and len(clip["samples"]):
                        mono = clip["samples"].mean(axis=1)
                        cuts = self._clip_cuts(mono)
                        clip.update(cuts=cuts, lead=self._leads(clip["samples"], cuts), want=self._want(cuts, True), variants={})
                        self._replan(clip)
            elif op["part"] == "clip" and "when" in op:
                self.clip_when = op["when"]
                self._replan()
            elif op["part"] == "clip" and "steps" in op:
                self.clip_place = list(op["steps"]) or None
                self._replan()
        return taken + self.groove.patch(clean)

    def describe(self):
        """Every part by name, what it is doing and how it has been changed: for the viewer to show."""
        clip = self.clip
        doing = ("waiting for the bar line" if self.pending is not None else "no film sound yet" if clip is None
                 else "straight through" if clip["mode"] == "straight" else f"chopped four bars at a time, {self.chop_style}" if clip["mode"] == "chop"
                 else "resting")
        changed = self._clip_note()
        return (self.groove.describe_parts() + [{"name": "clip", "doing": doing, "changed": changed,
                                                 "playing": bool(clip and not clip["gate"] and self.clip_on)}]
                + [{"name": name, "doing": ("a film's sound" if layer["film"] else "a pulled sample") + f" in {len(layer['slices'])} slices, " + (
                    "at its transients" if layer["cut"] == "transients" else "whole" if layer["cut"] == "whole" else f"{layer['cut']} equal pieces" if isinstance(layer["cut"], int)
                    else f"on the {layer['cut']}") + (f", the {layer['role']} ({self.chop_style})" if layer.get("role") and layer["steps"] is None else ""),
                    "changed": self._layer_note(layer),
                    "playing": bool(layer["hits"]) and self.groove.step - layer["hits"][-1] <= 16} for name, layer in self.layers.items()])

    def _clip_note(self):
        when = self.clip_when
        return ", ".join(x for x in ("muted" if not self.clip_on else "louder" if self.clip_level > 0.95 else "quieter" if self.clip_level < 0.85 else "",
                                     "placed" if self.clip_place is not None else "",
                                     "breaks only" if when == "breaks" else f"1 bar in {when}" if when != 1 else "") if x)

    @staticmethod
    def _layer_note(layer):
        when = layer["when"]
        role = layer.get("role_by_hand") or layer.get("role")
        return ", ".join(x for x in ("waiting" if layer["in"] is False else "next bar" if layer["in"] == "armed" else "", summary(layer["settings"]), "placed" if layer["steps"] is not None else "",
                                     (role + (" by hand" if layer.get("role_by_hand") else "")) if role and layer["steps"] is None else "",
                                     "breaks only" if when == "breaks" else f"1 bar in {when}" if when != 1 else "") if x)

    def roll(self, window=32):
        """Every part as a roll, for the viewer: (the place now, in sixteenths within the window; the rows)."""
        now = self.beat() * 4.0
        start = int(now // window) * window
        rows = self.groove.roll(now, window)
        changed = self._clip_note()
        cells = [(step - start, 1.0, None, False) for step in self.clip_steps if start <= step < start + window]
        rows.append({"name": "clip", "changed": changed, "cells": cells,
                     "playing": bool(self.clip and not self.clip["gate"] and self.clip_on)})
        for name, layer in self.layers.items():       # each sample layer has a row of its own, under its own name
            rows.append({"name": name[:6], "changed": self._layer_note(layer),
                         "cells": [(step - start, 1.0, None, False) for step in layer["hits"] if start <= step < start + window],
                         "playing": bool(layer["hits"]) and self.groove.step - layer["hits"][-1] <= 16})
        if self.stream is not None or self.drops:     # the dropout watcher: a mark on each sixteenth where the sound was not ready
            rows.append({"name": "audio", "changed": f"{self.drops} dropped" if self.drops else f"load {self.load:.0%}",
                         "cells": [(step - start, 1.0, None, False) for step in self.drop_steps if start <= step < start + window],
                         "playing": bool(self.drop_steps) and self.groove.step - self.drop_steps[-1] <= 32})
        return now - start, rows

    def replay(self):
        """The current clip again from its start, straight through, on the next bar line. False if there is none."""
        clip = self.clip or self.pending
        if clip is None:
            return False
        self.pending = dict(clip, pos=0, mode="straight", gate=False, fresh=False, bars=0, chopped=False, src=None, stop=0, gain=1.0)
        return True

    def close(self):
        self.watching = False                               # the watch's thread ends
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    # ------------------------------------------------------------------ making the sound

    def health(self):
        """How the sound is keeping up: the share of each block's time it takes to make (load), the slowest block
        lately in milliseconds against the time there is for one, and how often the sound was not ready in time."""
        now = time.time()
        return {"load": self.load, "worst_ms": self.worst * 1000.0, "block_ms": 1024000.0 / self.rate, "drops": self.drops,
                "last_minute": sum(1 for t in self.drop_times if now - t < 60.0), "building": len(self.groove.building)}

    def _watch(self, frames, took, underflow):
        """After each block: was it made in time, and did the sound card say it ran dry?"""
        budget = frames / self.rate
        self.load += 0.05 * (took / budget - self.load)
        self.worst = max(took, self.worst * 0.999)             # the slowest lately: it fades over a minute or so
        if not underflow and took <= budget:
            return
        now = time.time()
        self.drops += 1
        self.drop_times.append(now)
        self.drop_steps.append(self.groove.step)
        if now - self.told > 10.0:                              # said once, then counted quietly: it is on the roll
            self.told = now
            recent = sum(1 for t in self.drop_times if now - t < 60.0)
            building = len(self.groove.building)
            self.log("The sound dropped out: " + (f"a block took {took * 1000:.0f} ms to make and there are {budget * 1000:.0f}"
                                                  if took > budget else "the sound card ran dry (something else had the machine)")
                     + (f"; {building} sound{'s were' if building != 1 else ' was'} being rebuilt" if building else "")
                     + f". {recent} in the last minute.")

    # ------------------------------------------------------------------ the self-measurement (watch.py)

    def _watcher(self):
        """The watch's thread, below the sound's. Its work (hand every finished bar to the watch, work out the
        report, keep it for stands(), say when the verdict changes: rarely) is done a small piece at a time, one
        piece (well under a millisecond) within 2 ms of each block of sound being made (a block noticed later is let go),
        so that it runs in the time between blocks (23 ms apart) and not while the sound's thread wants the
        interpreter. The sound's thread only appends to deques."""
        _stand_back()
        work, seen = None, None
        while self.watching:
            time.sleep(0.002)
            made = self.blocks[-1] if self.blocks else None
            if made is None or made == seen:            # no block since the last piece: one may be being made now
                continue
            seen = made
            if time.perf_counter() - made[1] > self.WATCH_LATE:     # woken late: the next block may be near
                continue
            try:
                if work is None:
                    work = self._watch_work()
                if next(work, StopIteration) is StopIteration:
                    work = None
            except Exception as e:                      # a measurement that trips must not stop the measuring
                work = None
                if not self.watch_told:
                    self.watch_told = True
                    self.log(f"the watch could not measure: {type(e).__name__}: {e}")

    def watch_tick(self):
        """All the watch's work for the bars finished since it was last done, at once (offline, and for tests)."""
        for _ in self._watch_work():
            pass

    def _watch_work(self):
        """Every bar finished since the last time, as the watch takes it (watch.Watch.add_bar): the rhythm section's
        onsets from groove.heard (or groove.played, the roll's records) and the slices the layers and the clip
        started, with their slice class; then the report, a piece at a time (a generator). Never run on the sound's
        thread."""
        g = self.groove
        done = g.step // 16                             # the bars before this one are over
        if done < self.watch_bar:                       # the count of sixteenths went back: a fresh watch
            self.watch_bar, self.watcher = 0, Watch()
        start = max(self.watch_bar, done - 16)          # the records kept reach about that far back
        if start >= done:
            return
        heard = getattr(g, "heard", None)
        records = list(heard if heard is not None else g.played)
        lo, hi = start * 16, done * 16
        bars = {b: {} for b in range(start, done)}
        for rec in reversed(records):                   # newest first: stop at the first from before these bars
            step, part, pitch = rec[:3]
            if step < lo:
                break
            if step < hi and part in self.WATCH_PARTS:
                bars[step // 16].setdefault(part, []).append((step % 16, pitch))
        yield
        for step, name, which in reversed(list(self.chopped)):
            if step < lo:
                break
            if step < hi:
                thing = self.clip if name == self.CLIP else self.layers.get(name)
                cuts = thing.get("cuts") if thing else None
                kind = cuts[which].get("kind") if cuts and 0 <= which < len(cuts) else None
                lane = "clip" if name == self.CLIP else name + "~" if name in self.WATCH_PARTS else name
                bars[step // 16].setdefault(lane, []).append((step % 16, which, kind))
        edge = getattr(self, "edge", None)             # the edge (edge.EdgeControl), when the mixer has one
        try:
            edge = edge.stands() if edge is not None else None
        except Exception:
            edge = None
        for b in range(start, done):
            self.watcher.add_bar(b, bars[b], edge if b == done - 1 else None)
        self.watch_bar = done
        yield
        yield from self.watcher.steps()
        self.watch_report = self.watcher.report()       # worked out above: this only hands it over
        line = self.watcher.says()
        if line:
            self.log(line)

    def _callback(self, out, frames, when, status):
        began = time.perf_counter()
        try:
            beat = self.groove.beat()
            seconds = self._heard()[0]
            out[:] = self.fill(frames)
            self.clock = (when.outputBufferDacTime, beat, self.groove.bpm, seconds, seconds is not None and self._heard()[1])
            self._watch(frames, time.perf_counter() - began, bool(status) and bool(getattr(status, "output_underflow", False)))
        except Exception as e:                        # never let an error become a scream of noise
            out[:] = 0
            if not self.failed:
                self.failed = True
                self.log(f"sound stopped: {type(e).__name__}: {e}")

    def _heard(self):
        """Where in the newest film the sound being made is, in seconds, and whether it is moving: its premiere if
        that is playing, else the slice of its layer that is sounding."""
        clip, sync = self.clip, self.film_sync
        if clip is not None and not clip["gate"]:
            if clip.get("src") is not None:           # a slice made aside (backwards, or repitched): the picture holds where it is from
                return clip["film_at"] / self.rate, False
            return clip["pos"] / self.rate, True
        if sync is not None:
            return max(min(sync[0], sync[1]), 0) / self.rate, sync[0] < sync[1]
        return (clip["pos"] / self.rate if clip else None), False

    def fill(self, frames):
        """The next `frames` of stereo sound."""
        g = self.groove
        mix, duck = g.render(frames)
        out = np.repeat(mix[:, None], 2, axis=1) * (self.groove_level if self.groove_on else 0.0)
        begin = 0
        if self.pending is not None:
            for step, at in g.steps:
                if step % 16 == 0:                    # a bar line inside this block: the new clip starts on it
                    self.clip, self.pending, begin = self.pending, None, at
                    self._replan()
                    break
        bar_line = [step // 16 for step, _ in g.steps if step % 16 == 0]
        clip = self.clip
        if self.layers or clip is not None:           # the planner is asked for what is not planned yet (nothing is planned here)
            for step, _ in g.steps:
                self._keep_planned(step)
        if clip is not None and self.pending is None or clip is not None and begin == 0:
            layer = np.zeros((frames, 2), np.float32)
            cursor, cut = begin, begin > 0
            for step, at in [(s, a) for s, a in g.steps if a >= begin] + [(None, frames)]:
                if at > cursor:
                    self._copy(clip, layer, cursor, at, starts_on_cut=cut, ends_on_cut=step is not None)
                cursor, cut = at, step is not None
                if step is not None and not (at == begin and begin > 0):
                    self._decide(clip, step)
            level = self.clip_level if self.clip_on and (clip["mode"] == "straight" or self._in_bar(self.clip_when, g.step)) else 0.0
            if level and not clip["gate"] and (not self.clip_steps or self.clip_steps[-1] != g.step):
                self.clip_steps.append(g.step)
            out += layer * ((duck if self.groove_on else 1.0) * level)[:, None] if self.groove_on else layer * level
        if self.line and any(step % 16 == 15 for step, _ in g.steps):
            self._line_bar()
        if self.layers:
            for step, at in g.steps:
                self._layers_step(step, at)
        if self.film_sync is not None:
            self.film_sync[0] += frames
        if self.shots:                                # slices of the sample layers that are sounding
            alive = []
            for shot in self.shots:
                piece, into, level, way, _, end = shot      # end: where it is cut off (with a fade just before), at most its length
                start, first = max(0, -into), max(0, into)
                end = min(end, len(piece))
                count = min(frames - start, end - first)
                if count > 0:
                    sound = piece[first:first + count]
                    if first + count > end - FADE:          # the cut falls in this block: faded so it does not click
                        sound = sound * np.clip((end - np.arange(first, first + count, dtype=np.float32)) / FADE, 0.0, 1.0)[:, None]
                    gain = g.duck_gain(way, frames)                 # what this layer gives way to, if anything
                    out[start:start + count] += sound * (level if gain is None else gain[start:start + count, None] * level)
                shot[1] = into + frames
                if shot[1] < end:
                    alive.append(shot)
            self.shots = alive
        if self.mute:
            out[:] = 0
        self.blocks.append((g.pos, time.perf_counter()))         # for the watch: a block has been made (see _watcher)
        mixed = np.tanh(out).astype(np.float32)
        if bar_line:                                  # a bar line in this block: the course is worked out ahead on the planner's
            self.course_due = bar_line[-1]            # thread, woken only now that the block is made, so its work falls in the gap
            self.plan_wake.set()                      # before the next block and never competes with this one
        return mixed

    def _copy(self, clip, layer, a, b, starts_on_cut, ends_on_cut):
        if clip["gate"]:
            return
        source = clip["samples"] if clip.get("src") is None else clip["src"]
        stop = clip.get("stop") or 0                  # a gated slice: cut off this many samples from here
        piece = source[clip["pos"]:clip["pos"] + (min(b - a, stop) if stop else b - a)]
        if len(piece):
            piece = piece.copy()
            if clip["mode"] == "chop" and len(piece) > 2 * FADE:
                if starts_on_cut and clip["fresh"]:
                    piece[:FADE] *= np.linspace(0, 1, FADE, dtype=np.float32)[:, None]
                if ends_on_cut or (stop and stop <= b - a):
                    piece[-FADE:] *= np.linspace(1, 0, FADE, dtype=np.float32)[:, None]
                    clip["fresh"] = True
            if clip["mode"] == "chop" and clip.get("gain", 1.0) != 1.0:
                piece *= clip["gain"]
            layer[a:a + len(piece)] += piece
        clip["pos"] += b - a
        if stop:
            clip["stop"] = stop - (b - a)
            if clip["stop"] <= 0:                     # gated: silent until the next slice
                clip["gate"], clip["stop"] = True, 0
        if clip["pos"] >= len(source):                # ran off the end: silent until the next decision
            clip["gate"] = True
            if clip["mode"] == "straight" and clip.get("src") is None:
                clip["mode"], clip["chopped"] = ("chop" if self.chop and not clip.get("name") else "done"), True
                self._replan()                        # chopped from here on: the planner takes it in

    def _decide(self, clip, step):
        """On each sixteenth: what the film's sound does next, by its plan for these four bars (made aside: see _planner)."""
        if clip.get("name"):                          # it has a layer of its own: after its premiere, that is what plays
            return
        slot = step % 16
        if slot == 0:
            clip["bars"] += 1
            if clip["chopped"] and self.chop and clip["bars"] % REPLAY_BARS == 0:
                clip.update(mode="straight", pos=0, gate=False, src=None, stop=0, gain=1.0)      # the whole line again, on the one
                return
        if clip["mode"] != "chop":
            if clip["mode"] == "done" and self.chop and clip["chopped"]:
                clip["mode"] = "chop"
            else:
                return
        if not self.chop:
            clip["mode"], clip["gate"] = "done", True
            return
        action = self._event(self.CLIP, step)
        if self.clip_place is not None:               # placed by hand: its slices in order, one on each of those sixteenths
            action = None
            if slot in self.clip_place and clip["cuts"]:
                action, clip["next"] = dict(self.PLAIN, slice=clip.get("next", 0) % len(clip["cuts"])), clip.get("next", 0) + 1
        if isinstance(action, dict) and action["slice"] < len(clip["cuts"]):  # that slice, from where its sound begins
            which = action["slice"]
            cut = clip["cuts"][which]
            begin = cut["pos"] + (clip["lead"][which] if which < len(clip.get("lead", ())) else 0)
            src = None
            if action["reverse"] or action["semis"]:  # made aside; if it is not there yet, backwards costs nothing
                src = self._variant(clip, which, action["reverse"], action["semis"])
                if src is None:
                    self._ask(step // 64)
                    src = clip["samples"][begin:cut["pos"] + cut["len"]][::-1] if action["reverse"] else None
            film_at = max(cut["pos"] + cut["len"] - 1, begin) if action["reverse"] else begin
            clip.update(src=src, pos=0 if src is not None else begin, film_at=film_at, gate=False, fresh=True, gain=action["gain"],
                        stop=int(action["gate"] * self.groove.step_len) if action["gate"] else 0)
            self.chopped.append((step, self.CLIP, which))           # for the watch
        elif action == "rest":
            clip["gate"] = True
        if clip["pos"] >= len(clip["samples"] if clip.get("src") is None else clip["src"]):
            clip["gate"] = True
