"""The composer: thelmic's rule-based engine, used as a library. thelmic knows what a rhythm section should
play (ten rhythmic archetypes, how a phrase withholds before a drop and releases after it, what the sub,
bass, hook, call and response and drones do). It writes sixteen bars at a time as note events; groove.py
is only the instrument that sounds them.

thelmic is a separate project. It is looked for beside this one (../thelmic) or where MINDSTREAM_THELMIC
points; without it the groove falls back to its own simple patterns.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THELMIC = os.environ.get("MINDSTREAM_THELMIC", os.path.join(os.path.dirname(ROOT), "thelmic"))

# archetype -> (density, syncopation, stability) biases that thelmic's own selector maps to it
ARCHETYPES = {
    "half_step": (0.30, 0.30, 0.60), "two_step": (0.30, 0.60, 0.60), "four_on_the_floor": (0.55, 0.30, 0.60),
    "rolling": (0.80, 0.30, 0.60), "shuffled_two_step": (0.30, 0.60, 0.30), "stutter": (0.55, 0.60, 0.30),
    "amen": (0.80, 0.30, 0.30), "breakbeat_hardcore": (0.80, 0.60, 0.30), "happy_hardcore": (0.90, 0.30, 0.10),
    "gabber": (0.90, 0.60, 0.10),
}
# this project's plain style words -> the archetype that plays them
STYLE_TO_ARCHETYPE = {"four": "four_on_the_floor", "twostep": "two_step", "broken": "breakbeat_hardcore", "dnb": "amen",
                      "half": "half_step", "none": "half_step"}
BANK_STEPS = 256          # sixteen bars of sixteenths
REFERENCE_BPM = 174.0     # thelmic gives note lengths in seconds at this tempo


class Composer:
    def __init__(self, path=THELMIC, seed=1):
        if not os.path.isdir(os.path.join(path, "thelmic")):
            raise ImportError(f"thelmic not found at {path}")
        if path not in sys.path:
            sys.path.insert(0, path)
        from thelmic.archetypes import select_archetype
        from thelmic.dimensions import Dimensions
        from thelmic.landscape_map import SignatureRhythm, _derive_bass_steps
        from thelmic.note_generation_chain import generate_bank
        self._generate, self._dimensions, self._signature, self._bass_steps = generate_bank, Dimensions, SignatureRhythm, _derive_bass_steps
        self.seed = int(seed)
        # a thelmic that has taken in its own jungle research can be asked for "jungle" by name: the measured spine,
        # bars dealt by chance, a sub riff, short low hooks, drops by subtraction. An older one cannot, and plays the amen.
        import inspect
        self.jungle = "archetype" in inspect.signature(generate_bank).parameters
        for name, biases in ARCHETYPES.items():            # the table above must agree with thelmic's selector
            if select_archetype(*biases).value != name:
                raise ImportError(f"thelmic's archetype selection has changed ({name})")

    def bank(self, index, archetype, energy, root, phase="steady"):
        """Sixteen bars: {half-step index (32nd notes): [(layer, note, velocity, length in sixteenths)]}.
        phase is "steady", "build" (the phrase before a drop: thelmic withholds and compresses) or "drop"."""
        jungle = archetype == "jungle" and self.jungle
        if archetype == "jungle":
            archetype = "amen"                     # the nearest of the ten, for a thelmic that has no jungle (and for the biases, which jungle ignores)
        density, syncopation, stability = ARCHETYPES[archetype]
        energy = min(max(float(energy), 0.0), 1.0)
        signature = self._signature(id=archetype, base_pattern_seed=self.seed, density_bias=density, syncopation_bias=syncopation,
                                    stability_bias=stability, root_note=int(root), bass_steps=self._bass_steps(density, syncopation),
                                    hook_motif_seed=self.seed * 31 + 7)
        sparsity = min(max(0.75 - 0.75 * energy, 0.0), 1.0)
        if phase == "build" and jungle:            # jungle builds by taking the low end away, not by thinning: the steady phrase, about to drop
            dims, extra = self._dimensions(stability, 0.2, sparsity, 0.0, 0.0), {"phrases_until_drop": 0}
        elif phase == "build":
            dims, extra = self._dimensions(stability, 0.9, max(sparsity, 0.5), 0.0, 0.0), {"phrases_until_drop": 0}
        elif phase == "drop":
            dims, extra = self._dimensions(stability, 0.2, sparsity * 0.5, 1.0, 1.0), {"is_drop_phrase": True}
        else:
            dims, extra = self._dimensions(stability, 0.2, sparsity, 0.0, 0.0), {"phrases_until_drop": 8}
        if jungle:
            extra["archetype"] = "jungle"
        made = self._generate(int(index), dims, signature_rhythm=signature, heat=0.3 + 0.6 * energy, **extra)
        out = {}
        for phrase in made.phrases:
            for event in phrase.events:
                if not event.active:
                    continue
                bar, beat, tick = (int(x) for x in event.time.split("."))
                half = (((bar - 1) % 16) * 16 + (beat - 1) * 4) * 2 + round(tick / 3)
                length = event.duration * REFERENCE_BPM / 15.0
                out.setdefault(half, []).append((event.layer, int(event.note), int(event.velocity), length))
        return out
