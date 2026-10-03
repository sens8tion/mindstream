# What mindstream does now when it chops and places sound

This is the "what we do today" half of a comparison with how producers chop breaks and place samples. It is
read from the code and measured by running the code's own functions silently. It makes no recommendations.

## Summary: the plain facts

- **A layer's rhythm is one fixed template.** For a given density and drum style, slices land on the same
  sixteenths in every bar: 0, 2, 6 at density 0.2; 0, 2, 6, 14 at 0.5 (0, 2, 6, 10 where the kick does not use
  10 as a gap); six fixed sixteenths at 0.8. Five of the seven drum styles tested give the identical template.
  Over 64 bars a layer has **one or two distinct bar rhythms** (the normal bar, and the stutter bar), for every
  sound, style and density measured. Rhythm similarity at 4, 8 and 16 bars is 1.00.
- **The form is fixed: A A' A B, every four bars, for ever.** Bar 3 is a literal copy of bar 1. Bar 2 is bar 1
  with its last two slices swapped. Bar 4 is the first half of bar 1 followed by the phrase's first slice on
  sixteenths 8, 10, 12, 13, 14, 15. That stutter is the only roll there is; at density 0.5 it is 29% of all
  slice onsets.
- **Slices are played almost always in the sound's own order**, a run of three, four or five neighbours per
  phrase, moved along by a fixed stride each phrase. 46 to 55 of every 64 bars are exact repeats of an earlier
  bar. A short sound (five or six slices) repeats completely every 8 to 20 bars. In 8 to 14 of the 31 slice
  counts from 2 to 32, some slices at the end of the sound are never played at all.
- **A mutated layer is a literal four-bar loop** (similarity 1.00 at lag 4; 3 distinct bars in 64), and no
  longer follows the energy.
- **Nothing about a slice changes how it is played.** No per-slice pitch, reversal, length or level. Every slice
  starts on the unswung sixteenth grid and plays for its own length capped at one beat. Loudness and tonality are
  measured for every slice and never read. "Punch" is read once (the loudest attack is put on the snare in
  bar 2) and only when the density is high enough for a snare sixteenth to be among the chosen ones: never at
  0.2 or 0.5.
- **Layers do not hear the drums or each other.** They are planned against the style's written kick and snare,
  not against what was dealt for the bar. Two layers at the same density, brought in together, start slices on
  exactly the same sixteenths (overlap 1.00). A layer's four-bar phrase starts when it is brought in, so its
  stutter bar matches the drums' fill bar only one time in four.
- **Drums:** the kick and snare are near-constant (about 4 distinct kick-and-snare bars in 64); the variety is
  hats and ghost notes dealt bar by bar with no memory beyond "half of this is the four-bar group's".
- **Sub:** four riffs per 64 bars, one per 16-bar block, each looped (four bars x4, or eight bars x2) and then
  replaced by an unrelated one. 70% of its moves are the same note again; a riff uses 3.3 different pitches on
  average within about 5 semitones.
- **Bass:** the same two or three sixteenths every bar, always the same length, always the sub's last pitch an
  octave up.
- **Hooks:** three bars in every eight. One shape is played twice, four bars apart, then thrown away; the third
  is unrelated. 16 different shapes in 64 bars, none developed from another. The hook, the sub and the drums are
  dealt from three separate seeds and no function takes another's output: measured, the hook's interval to the
  sub and its coincidence with drum hits are the same as against a stranger's sub and drums.
- **Nothing develops.** No decision in the dealing depends on how long the music has been playing. Over 128 bars
  every 16-bar window has the same density, register and number of pitches, within noise.
- **The tune's pitch is not tracked.** No pitch is measured anywhere. A piece of film sound is assumed to sound
  a tritone above the key's root and is sped up or slowed down from there. A piece that is exactly on the root
  plays every note of the hook 600 cents out. Different notes of one hook can be played on different pieces.

## Settings used for every measurement

- Code at commit `ed5357a`, unchanged. Sample rate 44100 Hz, 160 bpm (a sixteenth is 4134 samples, a beat 16537).
- `Mixer(open_stream=False, rate=44100, compose=False)`: no sound device, no outside composer.
  `groove.scene_set = True`, then `mixer.fill(512)` until `groove.opening` is False, then measured.
- Key A minor (the default), sub 0.8, bells off (the default), nothing edited by hand, no breaks.
- **Similarity** everywhere is Jaccard on a bar's set of events: (sixteenth, slice) for layers, (sixteenth,
  drum) for drums, (sixteenth, pitch) for sub, bass and tune. Two empty bars count as identical. "Exact repeats"
  is the number of bars (of 64) equal to some earlier bar.
- **Slice plans** were computed with `chop.plan` called exactly as `Mixer._plan` calls it (phrase 0, 1, 2 ...,
  `busy=False`, `turn=0`; for a mutated layer the phrase frozen and `turn=1`), 64 bars = 16 phrases. Checked
  against the real mixer: for three sounds under three style and energy settings, the slices the mixer started
  over 64 bars were identical, event for event, to the plan computed directly.
- **Drums, sub, bass and tune** were measured with a silent re-statement of `Groove._trigger` built on `deal.py`.
  Checked against the real mixer's own record (`groove.played`) for four styles x three energies x two seeds over
  39 bars: identical in all 24 runs.
- Drum styles for the layer measurements: `four`, `dnb`, `twostep`, `broken`, `amen`, `breakbeat_hardcore`, `half`.
- Five synthetic sounds, passed through `Mixer.take_sample` so they are cut as a pulled sample is:

| Sound | What it is | How it was cut | Slices | Slice lengths (sixteenths) |
|---|---|---|---|---|
| six | 2.0 s, six hits (three pitched, three noise) at uneven times | at 6 transients | 6 | 3.1 to 4.2 |
| one | 1.0 s, one decaying low hit | no transients found: on the eighths | 5 | 2.0 |
| sixteen | 2.0 s, sixteen hits 125 ms apart, loud and soft alternating | at 16 transients | 16 | 1.2 to 1.4 |
| tone | 2.0 s steady 220 Hz tone | no transients found: on the eighths | 11 | 2.0 |
| voice | 2.4 s, five pitched syllables (196, 247, 294, 220, 330 Hz) with gaps, 50 ms of silence first | at 6 "transients" | 6 | 0.4, then 3.9 to 6.3 |

In the voice sound the first slice is the 41 ms of silence before the first syllable (level 0.000). `onsets`
always puts a cut at 0, and adds another at the first real onset if that is later than 30 ms. Measured with a
plain four-hit sound: up to 40 ms of leading silence gives no silent slice; 50 ms or more does. Pulled samples
are trimmed before they reach the mixer (`sample_pull.py`), a film's sound is not (`Mixer.play`). Where there is
a silent first slice, it is what plays on the one, and it is what the stutter repeats, in the first phrase.

## 1. Which sixteenths slices land on

**The template (bars 1 to 3 of every phrase).** `*` marks a written kick, `s` a written snare.

| Style (kick / snare) | density 0.2 | density 0.5 | density 0.8 |
|---|---|---|---|
| four (0 4 8 12 / 4 12) | 0* 2 6 | 0* 2 6 10 | 0* 2 4*s 6 10 14 |
| dnb (0 10 / 4 12) | 0* 2 6 | 0* 2 6 14 | 0* 2 4s 6 12s 14 |
| twostep (0 10 / 4 12) | 0* 2 6 | 0* 2 6 14 | 0* 2 4s 6 12s 14 |
| broken (0 3 10 / 4 13) | 0* 2 6 | 0* 2 6 14 | 0* 2 4s 6 13s 14 |
| amen (0 3 8 10 / 4 7 12) | 0* 2 6 | 0* 2 6 14 | 0* 2 4s 6 7s 14 |
| breakbeat_hardcore (0 3 7 10 / 4 8 12) | 0* 2 6 | 0* 2 6 14 | 0* 2 4s 6 8s 14 |
| half (0 / 8) | 0* 2 6 | 0* 2 6 10 | 0* 2 6 8s 10 14 |

At 0.2 the template is the same for all seven styles. At 0.5 there are two templates. The drum style only
decides whether sixteenth 10 or 14 is used and, at 0.8, which snare sixteenth joins in.

**Occupancy over 64 bars**: percent of bars with a slice starting on each sixteenth, averaged over the 5 sounds
and 7 styles (it does not depend on the sound).

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alone, 0.2 | 100 | 0 | 100 | 0 | 0 | 0 | 100 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| alone, 0.5 | 100 | 0 | 100 | 0 | 0 | 0 | 100 | 0 | 25 | 0 | 46 | 0 | 25 | 25 | 79 | 25 |
| alone, 0.8 | 100 | 0 | 100 | 0 | 86 | 0 | 100 | 14 | 46 | 0 | 46 | 0 | 46 | 36 | 100 | 25 |
| mutated, 0.2 | 100 | 0 | 0 | 0 | 0 | 0 | 100 | 0 | 0 | 0 | 21 | 0 | 0 | 0 | 54 | 0 |
| mutated, 0.5 | 100 | 0 | 0 | 0 | 71 | 0 | 100 | 0 | 25 | 0 | 46 | 0 | 25 | 25 | 100 | 25 |
| mutated, 0.8 | 100 | 0 | 0 | 0 | 100 | 0 | 100 | 14 | 79 | 0 | 46 | 0 | 79 | 36 | 100 | 25 |

- There is a slice on the one in 100% of bars, in every case.
- The 25% entries on 8, 10, 12, 13, 14, 15 are the stutter in the fourth bar. Sixteenths 1, 3, 5, 9 and 11 are
  never used. 89 to 100% of onsets are on even sixteenths; the only odd ones are the stutter's 13 and 15 (and a
  snare on 7 or 13 in two styles at 0.8).
- Onsets per bar: 3.00 at 0.2, 5.25 at 0.5, 7.00 at 0.8.

**Against the written kick and snare** (share of all slice onsets, averaged over sounds and styles):

| density | on a written kick | on a written snare |
|---|---|---|
| 0.2 | 0.33 (all of it the one) | 0.00 |
| 0.5 | 0.24 | 0.05 (the stutter crossing 4 or 12) |
| 0.8 | 0.20 | 0.26 |

**Against the drums actually dealt** (real mixer, `dnb`, energy 0.5, layer density following it, 327 onsets over
63 bars): 25.4% coincide with a kick, 4.6% with a snare, 4.3% with a ghost snare, 59.9% with a hat, 0.9% with a
fill hit. The layer avoids the written kick on 10 whether or not that kick was dealt (it is dealt in 71% of
bars) and does not know about ghosts, fills or pickups.

**Swing.** In a swung style the drums' odd sixteenths arrive late (twostep: 0.28 of a sixteenth, 1157 samples,
26 ms at 160 bpm). Layers are started from the unswung grid (`groove.steps`), so a layer's hits on 13 and 15 are
26 ms ahead of the hats on the same sixteenths.

## 2. Which slices are used, and in what order

**Order.** Share of consecutive onsets within a bar, by what the second is relative to the first (averaged over
sounds and styles; it does not depend on the sound):

| density | the next slice of the sound | the same slice again | an earlier slice | a later, non-adjacent slice |
|---|---|---|---|---|
| 0.2 | 0.75 | 0.00 | 0.12 | 0.12 |
| 0.5 | 0.53 | 0.29 | 0.12 | 0.06 |
| 0.8 | 0.54 | 0.22 | 0.19 | 0.05 |
| mutated, 0.5 | 0.36 | 0.31 | 0.24 | 0.09 |

Everything that is not "the next slice" comes from four fixed sources: the swap of the last two slices in bar 2;
the stutter (all of "the same slice again"); the window wrapping round when there are more sixteenths than
slices in it (density 0.8: six sixteenths, five slices, so the leader returns on 14); and the loudest-attack
slice replacing whatever was on the snare in bar 2 (0.8 only).

The first two phrases for the six-hit sound against `dnb`, as sixteenth:slice.

- Density 0.2: `0:0 2:1 6:2` / `0:0 2:2 6:1` / `0:0 2:1 6:2` / `0:0 2:1 6:2`, then
  `0:2 2:3 6:4` / `0:2 2:4 6:3` / `0:2 2:3 6:4` / `0:2 2:3 6:4`.
- Density 0.5: `0:0 2:1 6:2 14:3` / `0:0 2:1 6:3 14:2` / `0:0 2:1 6:2 14:3` /
  `0:0 2:1 6:2 8:0 10:0 12:0 13:0 14:0 15:0`, then the same with every slice number one higher.
- Density 0.8: `0:0 2:1 4:2 6:3 12:4 14:0` / `0:0 2:1 4:2 6:4 12:3 14:0` / as bar 1 /
  `0:0 2:1 4:2 6:3 8:0 10:0 12:0 13:0 14:0 15:0`, then the same one higher.

**How many slices, and how far through the sound** (`dnb`; the other styles give the same figures):

| Sound (slices) | density | distinct slices per 4 bars | per 16 bars | share of slices heard after 4 / 16 / 64 bars | share of the sound's length ever heard in 64 bars |
|---|---|---|---|---|---|
| six (6) | 0.2 | 3 | 5.0 | 0.50 / 0.83 / 0.83 | 0.83 |
| six (6) | 0.5 | 4 | 6.0 | 0.67 / 1.00 / 1.00 | 0.99 |
| six (6) | 0.8 | 5 | 6.0 | 0.83 / 1.00 / 1.00 | 0.99 |
| one (5) | 0.2 | 3 | 5.0 | 0.60 / 1.00 / 1.00 | 1.00 |
| one (5) | 0.5 | 4 | 5.0 | 0.80 / 1.00 / 1.00 | 1.00 |
| one (5) | 0.8 | 5 | 5.0 | 1.00 / 1.00 / 1.00 | 1.00 |
| sixteen (16) | 0.2 | 3 | 9.5 | 0.19 / 0.56 / 0.94 | 0.93 |
| sixteen (16) | 0.5 | 4 | 13.75 | 0.25 / 0.81 / 1.00 | 1.00 |
| sixteen (16) | 0.8 | 5.4 | 13.0 | 0.38 / 0.81 / 0.81 | 0.81 |
| tone (11) | 0.2 | 3 | 9.75 | 0.27 / 0.82 / 1.00 | 1.00 |
| tone (11) | 0.5 | 4 | 9.5 | 0.36 / 0.91 / 1.00 | 1.00 |
| tone (11) | 0.8 | 5.4 | 10.25 | 0.55 / 0.91 / 1.00 | 1.00 |
| voice (6) | 0.2 | 3 | 5.0 | 0.50 / 0.83 / 0.83 | 0.64 |
| voice (6) | 0.5 | 4 | 6.0 | 0.67 / 1.00 / 1.00 | 0.79 |
| voice (6) | 0.8 | 5 | 6.0 | 0.83 / 1.00 / 1.00 | 0.79 |

- A phrase works with a run of 3, 4 or 5 neighbouring slices (density 0.2, 0.5, 0.8), never more.
- The voice never has more than 79% of its length heard because four of its five syllables are longer than a
  beat and a slice is cut off at one beat (see section 4).
- Use is uneven. Sixteen-hit sound at 0.8, times each slice was started in 64 bars:
  `78 24 24 18 83 20 20 15 96 20 20 15 15 0 0 0`. The three that lead a phrase (0, 4, 8) are the stuttered
  ones; the last three slices are never played.

**The walk through the sound** is a fixed stride with a fixed cycle. For a sound of n slices: phrases before
the sequence of phrases repeats, and slices that are never reached.

| n slices | density 0.2 (run of 3) | density 0.5 (run of 4) | density 0.8 (run of 5) |
|---|---|---|---|
| 5 | 3 phrases, 0 missed | 2, 0 | 5, 0 |
| 6 | 2, 1 missed | 3, 0 | 2, 0 |
| 8 | 3, 1 | 5, 0 | 4, 0 |
| 11 | 9, 0 | 8, 0 | 7, 0 |
| 12 | 5, 1 | 3, 2 | 2, 3 |
| 16 | 7, 1 | 13, 0 | 3, 3 |
| 24 | 11, 1 | 7, 2 | 5, 3 |
| 32 | 15, 1 | 29, 0 | 7, 3 |
| n from 2 to 32 with some slice never heard | 14 of 31 | 8 of 31 | 12 of 31 |

So "over time the whole of it is heard" (the comment in `chop.py`) holds for some slice counts and not others,
and a twelve-slice sound at density 0.8 alternates between two phrases for ever.

## 3. Bar-to-bar similarity and exact repeats

**A layer left alone**, 64 bars, averaged over the 5 sounds and 7 styles. The first block is the measure used
throughout, (sixteenth, slice); the second is the rhythm alone (sixteenths only).

| density | lag 1 | lag 2 | lag 4 | lag 8 | lag 16 | exact repeats of 64 | distinct bars |
|---|---|---|---|---|---|---|---|
| 0.2 | 0.36 | 0.32 | 0.00 | 0.40 | 0.40 | 54.8 | 9.2 |
| 0.5 | 0.25 | 0.31 | 0.00 | 0.20 | 0.20 | 46.6 | 17.4 |
| 0.8 | 0.38 | 0.35 | 0.02 | 0.41 | 0.41 | 52.6 | 11.4 |
| rhythm only, 0.2 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 63 | 1 |
| rhythm only, 0.5 | 0.73 | 0.72 | 1.00 | 1.00 | 1.00 | 62 | 2 |
| rhythm only, 0.8 | 0.80 | 0.80 | 1.00 | 1.00 | 1.00 | 62 | 2 |

- Lag 4 is 0.00 because each phrase uses a different run of slices on the same sixteenths. The lag 8 and lag 16
  averages hide two cases: exactly 1.00 for a sound whose walk has a two-phrase cycle, about 0 otherwise.
- Within a phrase, bar 3 equals bar 1 always; at density 0.2 bar 4 equals bar 1 as well.

By sound (`dnb`), the same measure:

| Sound | density | lag 1 | lag 2 | lag 4 | lag 8 | lag 16 | exact repeats | distinct bars |
|---|---|---|---|---|---|---|---|---|
| six | 0.2 | 0.36 | 0.31 | 0.00 | 1.00 | 1.00 | 60 | 4 |
| six | 0.5 | 0.25 | 0.31 | 0.00 | 0.00 | 0.00 | 55 | 9 |
| six | 0.8 | 0.37 | 0.35 | 0.02 | 1.00 | 1.00 | 58 | 6 |
| one | 0.5 | 0.25 | 0.31 | 0.00 | 1.00 | 1.00 | 58 | 6 |
| sixteen | 0.2 | 0.36 | 0.31 | 0.00 | 0.00 | 0.00 | 50 | 14 |
| sixteen | 0.5 | 0.25 | 0.30 | 0.00 | 0.00 | 0.00 | 25 | 39 |
| sixteen | 0.8 | 0.40 | 0.36 | 0.02 | 0.02 | 0.02 | 55 | 9 |
| tone | 0.5 | 0.25 | 0.30 | 0.00 | 0.00 | 0.00 | 40 | 24 |
| voice | 0.2 | 0.36 | 0.31 | 0.00 | 1.00 | 1.00 | 60 | 4 |
| voice | 0.5 | 0.25 | 0.31 | 0.00 | 0.00 | 0.00 | 55 | 9 |

**A mutated layer** (it holds its plan; one mutation, 64 bars, averaged over sounds and styles):

| density | lag 1 | lag 2 | lag 4 | lag 8 | lag 16 | exact repeats of 64 | distinct bars |
|---|---|---|---|---|---|---|---|
| 0.2 | 0.43 | 0.62 | 1.00 | 1.00 | 1.00 | 61 | 3 |
| 0.5 | 0.23 | 0.56 | 1.00 | 1.00 | 1.00 | 61 | 3 |
| 0.8 | 0.46 | 0.68 | 1.00 | 1.00 | 1.00 | 61 | 3 |

Confirmed in the real mixer: after `set_parts([("six", "mutate")])` the layer gave lag 4 = 1.00 and 3 distinct
bars over 32 bars, while an unmutated layer beside it gave lag 4 = 0.00 and 9. When the energy was then raised
from 0.5 to 0.9 the mutated layer stayed at 5.25 onsets a bar and the other went to 6.9.

## 4. What never happens, checked one by one

| What producers do | Does it happen | How it was checked |
|---|---|---|
| Reordering slices | Only by fixed rule: the last two of the run swapped in bar 2; the run rotated when it covers the whole sound or after a mutation; the loudest-attack slice put on one snare. Never chosen for effect. 53 to 75% of consecutive onsets are simply the next slice. | Section 2 |
| Repeating one slice (stutter, roll) | One form only: the phrase's first slice on 8, 10, 12, 13, 14, 15 of every fourth bar when density is 0.3 or more. Always that slice, those six sixteenths, that bar. Nothing faster than a sixteenth, no roll at any other point, none below density 0.3. | `chop.plan` lines 89 to 94; occupancy 25% on those sixteenths |
| A slice at a length other than its own | No. A slice plays for its own length, capped at one beat (`settings["length"]` scales the cap for the whole layer). The length does not depend on the room before the next onset: 18%, 39% and 44% of onsets (density 0.2, 0.5, 0.8) begin while the previous slice is still sounding. 17 to 19% of onsets are slices cut off at the beat. | Measured over all sounds and styles |
| A clean end where a slice is cut off | No. The cut at one beat has no fade. In the voice sound two of the four cut slices end at 16% and 81% of the slice's peak level. | `_layers_step` line 310; measured |
| The "rest" entries of the plan | Not acted on for layers. `plan` writes "rest" after a slice ends; `_layers_step` only acts on slice numbers. Rests only gate a film's sound that has no name, and every film that has sound is given one. | `_layers_step` line 307; `gl_view.py` line 576 |
| Pitch changes per slice | No. Pitch and octave are settings of the whole layer, applied to every slice alike. | `Mixer._shape` |
| Reversal | Only as an effect on the whole layer (every slice reversed). Never per slice. | `parts.FX`, `Groove._finish` |
| Slices starting off the sixteenth grid | No. Every start is a sixteenth of `groove.steps`. Layers are not swung even when the drums are. | Section 1 |
| Call and answer between two layers | No. Each layer is planned alone from the same rule. Two layers at the same density brought in on the same bar: 327 of 327 onsets on the same sixteenths (Jaccard 1.00). Brought in two bars apart: 76% of onsets still coincide. | Real mixer, 64 bars |
| A layer responding to what the drums just did | No. The plan reads the style's written kick and snare once per phrase. It does not read the dealt bar, ghosts, fills, pickups, or whether the low end is out. With the outside composer on it assumes kick 0 4 8 12, snare 4 12 whatever is played. | `Mixer._plan` |
| Fills at phrase ends | The stutter, as above, at the end of the layer's own four bars. Those four bars are counted from when the layer was brought in, not from the drums' four-bar groups: brought in during group bar 0, 1, 2, 3 the stutter fell in group bar 0, 1, 2, 3 respectively. The drums' own fill is always in group bar 3. | Real mixer, four runs |
| Anything conditional on a slice's own character | `punch` is used for one thing (the loudest attack on the last chosen snare sixteenth, bar 2 only), and only at density 0.8 in the styles tested: at 0.2 and 0.5 no chosen sixteenth is a snare. `level` and `tonal` are never read. `len` is read only to place rests (ignored) and to move the picture. | Search of the code; table in section 1 |
| A different number of onsets from bar to bar | No, except the stutter bar. | Occupancy is 0 or 100% outside the stutter |
| Silence as a choice | Only below density 0.3 (the second half of bar 4 is left empty), or by telling a layer which bars to play in. | `chop.plan` line 90 |

`punch` as computed is `head / (level + 1e-6) * level`, which is `head`: the peak of the first 25 ms. It is the
loudness of the attack, not attack against body. For the steady tone every slice has the same punch (0.41) and
the "hardest" slice is whichever comes first in the tie.

## 5. Drums, sub, bass and hooks

**Similarity** (24 seeds x 64 bars, the same measure; energy 0.5). Energy 0.8 gives the same figures within
0.03. At energy 0.2 only the kick and the sub play: the snare needs 0.3, the hats 0.25, the tune 0.35, the
bass 0.45.

| Style | Part | onsets per bar | lag 1 | lag 2 | lag 4 | lag 8 | lag 16 | exact repeats of 64 | distinct bars |
|---|---|---|---|---|---|---|---|---|---|
| dnb | all drums | 12.1 | 0.48 | 0.49 | 0.62 | 0.65 | 0.66 | 9.7 | 54.3 |
| dnb | kick and snare | 3.8 | 0.88 | 0.86 | 0.94 | 0.92 | 0.92 | 59.9 | 4.1 |
| dnb | hats, ghosts, fills | 8.3 | 0.36 | 0.37 | 0.51 | 0.55 | 0.57 | 11.8 | 52.2 |
| dnb | sub | 3.75 | 0.11 | 0.07 | 0.74 | 0.62 | 0.12 | 46.8 | 17.2 |
| dnb | bass | 2.0 | 0.32 | 0.24 | 0.79 | 0.70 | 0.29 | 54.1 | 9.9 |
| dnb | tune | 0.97 | 0.32 | 0.38 | 0.58 | 0.39 | 0.40 | 47.2 | 16.8 |
| dnb | everything | | 0.33 | 0.31 | 0.62 | 0.56 | 0.41 | 0.9 | 63.1 |
| amen | all drums | 18.8 | 0.69 | 0.68 | 0.77 | 0.78 | 0.78 | 7.0 | 57.0 |
| amen | kick and snare | 6.7 | 0.86 | 0.86 | 0.90 | 0.91 | 0.90 | 54.7 | 9.3 |
| amen | sub | 3.75 | 0.11 | 0.07 | 0.74 | 0.62 | 0.12 | 46.8 | 17.2 |
| four | all drums | 9.6 | 0.80 | 0.80 | 0.84 | 0.86 | 0.85 | 40.9 | 23.1 |
| four | sub | 4.0 | 0.38 | 0.31 | 1.00 | 1.00 | 1.00 | 61.4 | 2.6 |
| half | sub and bass | 2.0 each | 0.38 | 0.31 | 1.00 | 1.00 | 1.00 | 61.4 | 2.6 |

- The tune's figures include the 40 bars in 64 with no hook (two empty bars count as identical). Counting only
  pairs where at least one bar has a hook: lag 1 0.00, lag 2 0.01, lag 4 0.25, lag 8 0.01, lag 16 0.01.
- In the styles that are not break styles (`four`, `half` and their kin) the sub and bass are an exact four-bar
  loop: written sixteenths, one root per bar from a four-bar list.
- Hits per sixteenth in `dnb` at energy 0.5, percent of bars (200 seeds x 64 bars):

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kick | 100 | 0 | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 71 | 0 | 0 | 0 | 6 | 0 |
| snare | 0 | 0 | 0 | 0 | 100 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 100 | 0 | 0 | 0 |
| ghost snare | 0 | 19 | 0 | 19 | 0 | 0 | 8 | 19 | 0 | 19 | 3 | 19 | 0 | 0 | 8 | 18 |
| fill hit | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3 | 0 | 2 | 3 | 4 |
| hat | 26 | 23 | 88 | 22 | 26 | 23 | 88 | 23 | 44 | 22 | 89 | 24 | 28 | 24 | 89 | 24 |

**How many riffs and shapes in 64 bars** (`dnb`, 24 seeds): exactly 4 sub riffs (one per 16-bar block; 17.2
distinct sub bars); 15.9 distinct hook shapes, of which 8 are "main" shapes each heard twice, in 24 bars with a
hook.

**The sub's line** (4000 riffs):

| | |
|---|---|
| Riff length | 4 bars 55%, 8 bars 45% (the 8 is the 4 again with its last bar cut to two notes) |
| Ends on one low note and a gap | 40% |
| Notes per bar | 3.75 (1 to 6); note length 2.4 sixteenths; onset to onset 4.0 sixteenths |
| Pitch changes inside a bar | 0.75 on average; 43% of bars have none |
| Move from one note to the next, in scale steps | same note 70.2%; down one 12.1%; up one 8.7%; a third 4.4%; a fourth 1.4%; a fifth 3.2% |
| Scale steps used | root 41.5%, one below 15.5%, one above 11.8%, fifth above 9.1%, two below 7.5%, others under 6% each |
| Different pitches in a riff | 3.33 on average (2: 18%, 3: 39%, 4: 31%, 5 or more: 10%); 1.1% never leave the root |
| Range of a riff | 5.2 semitones on average, 12 at most; the line is held between a fourth below the root and a fifth above |
| Where the riff ends against where it began | same pitch 55%, higher 24%, lower 21% |
| Onset sixteenths | 0: 24%, 4: 11%, every other sixteenth 3 to 7% |

Each note is chosen from the one before it alone. There is no target note, no shape over the riff, and no link
from one 16-bar block's riff to the next.

**The bass** plays on the style's written bass sixteenths in every bar (`dnb`: 2 and 12, 64 bars of 64; `amen`:
2 and 14; `twostep`: 2, 9, 12), always 1.6 sixteenths long, at the pitch of the sub's most recent note an
octave up. It has no line of its own.

**The hook's line** (4000 eight-bar blocks, key A minor):

| | |
|---|---|
| Bars with a hook per eight | 3, always: the main shape in bar b and b+4 (b is 0 to 3), and one unrelated "cousin" elsewhere |
| Notes per hook | 2: 50%, 3: 37%, 4: 13%. 1.2% of notes are written past the end of the bar and never played |
| Span | 4.9 sixteenths on average, 8 at most; note length 1.6 sixteenths |
| Start sixteenth | 2, 6, 8, 10: about 19 to 20% each; 3 and 11: 11% each |
| First note | root 51%, third 25%, fifth 24% |
| Written moves, scale steps | down two 13%, down one 29%, same 16%, up one 29%, up two 13% |
| Written contour | rises 28%, falls 28%, turns 36%, flat 8% |
| Moves as sounded, semitones | within 4 semitones: 77%; a leap of 8 to 10 semitones: 23% |
| Moves whose direction is reversed between writing and sounding | 23.1% in A minor (C minor 12.9%, E minor 14.6%, F sharp minor 14.3%) |

The leaps and reversals come from `hook_note`, which folds every note into one octave starting at A sharp 3. In
A minor that puts the root at the top of the octave (A4, 440 Hz) and the second step at the bottom (B3), so a
written step up from the root sounds as a minor seventh down. Half of all hooks start on the root.

**Do the hook, the sub and the drums relate?** (`dnb`, energy 0.5, 200 seeds x 64 bars, about 12,400 hook notes.)

| | hook with its own sub and drums | hook with another session's sub and drums |
|---|---|---|
| Interval above the sounding sub note is a unison, third, fifth or sixth | 0.594 | 0.595 |
| Hook note starts on a sub onset | 0.201 | 0.200 |
| Hook note starts on a kick | 0.095 | 0.096 |
| Hook note starts on a snare | 0.127 | 0.122 |

| | sub with its own drums | another seed's riff over the same drums |
|---|---|---|
| Sub note starts on a kick | 0.291 | 0.294 |
| Sub note starts on a snare | 0.176 | 0.177 |
| Kicks with a sub note on them | 0.605 | 0.602 |

The figures are the same with a stranger's parts. The only thing the hook, the sub and the bass share is the
key and scale; the only thing they share with the drums is the bar line. The one real link is bass to sub
(pitch only).

**Does anything develop?** (`dnb`, energy 0.5, 48 seeds x 128 bars, by 16-bar window.)

| | bars 1-16 | 17-32 | 33-48 | 49-64 | 65-80 | 81-96 | 97-112 | 113-128 | spread across seeds |
|---|---|---|---|---|---|---|---|---|---|
| drum onsets per bar | 12.30 | 11.70 | 11.76 | 11.85 | 11.27 | 11.75 | 11.69 | 11.68 | 1.66 |
| drum onsets on odd sixteenths per bar | 3.29 | 2.89 | 2.96 | 2.94 | 2.67 | 2.95 | 2.93 | 2.95 | 0.93 |
| distinct drum bars of 16 | 15.7 | 15.7 | 14.8 | 15.5 | 15.3 | 15.5 | 15.7 | 15.9 | 0.70 |
| sub notes per bar | 3.77 | 3.71 | 3.63 | 3.84 | 3.79 | 3.73 | 3.73 | 3.73 | 0.38 |
| sub mean pitch, semitones from the root | 0.29 | -0.02 | 0.52 | -0.02 | 0.19 | -0.07 | -0.05 | 0.65 | 2.32 |
| sub distinct pitches | 3.21 | 3.19 | 3.35 | 3.35 | 3.48 | 3.35 | 3.35 | 3.60 | 0.94 |
| tune notes per bar | 0.99 | 0.97 | 0.97 | 1.01 | 0.96 | 0.97 | 0.97 | 0.97 | 0.14 |
| tune mean pitch, semitones above the low root | 31.6 | 31.1 | 31.3 | 31.3 | 31.5 | 31.2 | 31.0 | 31.4 | 1.31 |
| tune distinct pitches | 5.31 | 5.25 | 5.40 | 5.17 | 5.15 | 5.19 | 5.46 | 5.33 | 0.97 |

Every window is statistically the same as every other; the differences are far inside the spread across seeds.
This follows from the code: the bar number enters only as something to draw a random number from (`deal._draw`),
as "bar modulo 4" for the group, as "bar divided by 16" to pick the sub riff and "by 8" to pick the hooks.
Nothing reads how many bars have gone by. What does change the music over time comes from outside the dealing:
the session's energy (set from the look each frame, `gl_view.py` line 1774), the super knob, a change of style,
key or riffs landing on a four-bar line, a break when asked for, and a new film changing what the tune is
played on.

## 6. How the tune's sound is chosen, and whether the hooks are in tune

**Choosing** (`kit.tone_slices`). A 0.3 s window is slid along a film's sound in 50 ms steps. A window is
dropped if it is quiet (level under 0.02) or noisy (spectral flatness over 0.3). The rest are scored by level x
(1 - flatness) squared x (0.3 + steadiness of level over four quarters), and the best three that do not overlap
are kept, in the order they occur. Each new film adds up to three; the last eight are kept. What was measured:

| Sound | windows passing | pieces taken | what they are (measured fundamental) |
|---|---|---|---|
| sixteen (percussion) | 0 of 34 | 0 | the tune stays on what it had |
| six (pitched and noise hits) | 5 of 34 | 3 | the three pitched hits: A2, A3, E3, each a decaying hit (steadiness 0.04) |
| tone (220 Hz) | 34 of 34 | 3 | three windows of the same tone, A3 |
| voice | 42 of 42 | 3 | one whole syllable each: 194.6 Hz, 295.5 Hz, 329.8 Hz (the 247 and 220 Hz syllables are not taken) |
| glide (200 to 300 Hz over 2 s) | 34 of 34 | 3 | three stretches of a moving pitch: about 238, 258, 278 Hz at their middles |
| talk (eight short gliding syllables with vibrato) | 42 of 42 | 3 | 186.8, 199.3, 205.3 Hz at their middles, each spanning syllable edges |

The choice knows level, noisiness and evenness of level. It does not know pitch, does not check that the pitch
holds still inside the window, and does not prefer one pitch to another.

**Playing a note** (`Groove._make`). A hook note is asked for as "so many semitones above the key's low root".
The piece is chosen as `kit[(number of rescores + semitones // 12) % len(kit)]`, then played faster or slower by
`fold(semitones, 30)` semitones: the distance of the wanted note from the note 30 semitones above the low root,
brought within plus or minus 7 by octaves. The piece's own pitch is never measured. In effect every piece is
assumed to sound at 30 semitones above the low root, which is a tritone above the key's root (D sharp in A).

**Measured, key A minor**, the seven scale notes a hook can use (wanted B3, C4, D4, E4, F4, G4, A4):

| What the tune is played on | the six notes B3 to G4 | the root, A4 | interval errors between neighbouring notes |
|---|---|---|---|
| no film yet (synthesised) | 0 cents out | 0 | none |
| the 220 Hz tone (exactly on the root) | all 600 cents out: sounded F3, F#3, G#3, A#3, B3, C#4 | 600 out: sounded D#4 | none: the scale is intact, a tritone away |
| the voice | all 813 cents flat (387 cents off as a pitch class), on the 194.6 Hz piece | 91 cents flat, on the 295.5 Hz piece | 0 until the last, then 721 cents |
| the glide | all 467 cents flat | 327 cents flat, on another piece | 0 until the last, then 140 cents |
| the talk | all about 885 cents flat (315 off as a pitch class) | 775 flat, on another piece | 0 until the last, then 110 cents |

- The hook is in tune with the sub and bass only when the piece happens to sound a tritone above the root. For
  any other piece it is out by a fixed amount set by the piece's pitch. Within one piece the intervals of the
  scale are kept exactly.
- Which piece plays a note depends on `semitones // 12`, so a hook that crosses that line is played on two
  pieces with unrelated pitches. In A minor the line falls on the root itself (26% of hook notes); in E minor
  64% of notes are on one piece and 36% on the other.
- As films arrive the same note moves. A test note wanted at C#4 sounded F3 after the first film, G3 after the
  second, G3 after the third, G2 after the fourth, as the kit grew from 3 to 8 pieces and the choice of piece
  shifted.
- A percussive film adds nothing to the kit, and the tune carries on with the pieces it had.
- The sub and the bass are synthesised at exact pitch and are always in key.

## Mechanisms: how each decision is made today

**Where a sound is cut** (`samples.onsets`, `samples.cut_points`, `samples.slices`, called from `Mixer._cut`).
The level is taken in 256-sample frames. An onset is a frame where the loudest of the next three frames is at
least twice the average of the five before it (plus a floor), is at least a quarter of the sound's peak, is a
local maximum of that ratio, and is 90 ms or more after the last onset. A cut is always placed at 0. If fewer
than three cuts result, the sound is cut on the eighths at the tempo instead. At most 32 slices are kept; each
runs to the next cut, with a 4 ms fade at both ends; pieces under 30 ms are dropped.

**What is known about each slice** (`chop.measure`). Position, length, level (RMS), punch (the peak of the
first 25 ms), tonal (1 minus spectral flatness over the first 0.3 s, times level).

**The four-bar plan** (`chop.plan`, called by `Mixer._plan` for each layer at the start of each of the layer's
own four-bar phrases).

- How many slices are in play: `2 + round(4 x density)`, a run of neighbours.
- Where the run starts: `phrase x (run - 1)`, modulo the number of places it can start.
- Which sixteenths: the one, plus the first `1 + round(5 x density)` from a fixed list: 2, 6, 10, 14 where the
  written kick does not fall; then the written snare's sixteenths; then 8, 4, 12; then the other even ones; the
  odd ones only above density 0.75. The chosen sixteenths are sorted and filled left to right with the run in
  order.
- Bar 2: the same with the last two of the run swapped, and the slice with the greatest punch written over the
  last chosen sixteenth that is a snare, if there is one.
- Bar 3: a copy of bar 1.
- Bar 4: the chosen sixteenths below 8, then the run's first slice on 8, 10, 12, 13, 14, 15; below density 0.3
  nothing after 8.
- Density is the layer's own if it has been told "busier" or "sparser" (steps of 0.3), otherwise the session's
  energy. The kick and snare are the style's written pattern as edited by hand, not the dealt bar.
- The "busy" switch (odd sixteenths at any density) is tied to a setting that can only be changed while no film's
  layer exists, so in a session with a film it stays off.

**Playing the plan** (`Mixer._layers_step`). On each sixteenth, if the plan has a slice number there, that slice
is started at the grid position, at the layer's level, for its own length cut to one beat x the layer's length
setting (or its full shaped length once the layer has effects). Slices overlap freely; nothing stops an earlier
one. A layer comes in on a bar line "from the top of its phrase": its bar count starts then.

**Mutate, vary, busier, placed, when** (`Mixer.set_parts`, `Mixer.patch`).

- Mutate: `turn` goes up by one, which rotates both the list of sixteenths and the run of slices by one place;
  the layer is then `held`: the phrase number stops advancing, the plan is no longer redone, and the density is
  frozen at what it was.
- Vary: the phrase number is pushed on one extra.
- Placed by hand (`steps`): the slices in the sound's order, one on each named sixteenth, running on through the
  whole sound and round again. This is the only mode that walks every slice.
- When: every bar, the last bar of every N, or only while a break is running.
- Re-chop: the cutting steps through transients, less obvious transients, eighths, sixteenths, beats.

**Drums** (`deal.bar`, `deal.fill`, used by `Groove._trigger`). For each bar and each sixteenth a hit is decided
by a chance: 1.0 for the kick on the one and the snares on 4 and 12 (or anything written by hand), 0.88 for the
style's other written hits (0.7 for the `dnb` kick on 10), about 0.67 x a factor of the energy for other eighth
hats and 0.34 x for odd ones in the break styles, 0.10 to 0.20 x for ghost snares on nine named sixteenths, 0.1
x energy for a kick pickup on 6 or 14. Each decision is, half the time, the four-bar group's draw for that
place in the group, and half the time a draw for that bar alone. A fill (one of five written two- or three-hit
figures) closes the fourth bar of a group one time in four.

**Sub** (`deal.sub_riff`, `Groove._trigger` lines 841 to 855). In the break styles a riff is made from a seed
and the 16-bar block number: four bars, each a walk from sixteenth 0 (or 2) in gaps of 3 to 6 sixteenths, each
note 1.5 to 4 sixteenths long, the scale step moving by the chances in section 5 and held between -3 and +4; 45%
are doubled to eight bars with a shortened last bar; 40% have their last bar replaced by one note and a gap. In
the other styles the sub plays the style's written sixteenths on a root that follows a four-bar list.

**Bass** (`Groove._trigger` line 856). At energy 0.45 or more, on the written bass sixteenths (the style's sub
sixteenths moved on by two, less any kick sixteenths), the sub's current pitch an octave up, 1.6 sixteenths.

**Hooks** (`deal.hooks`, `deal.hook_shape`, `deal.hook_note`, `Groove._trigger` lines 858 to 868). For each
eight-bar block: a first bar from 0 to 3; the main shape there and four bars later; one more bar, not next to
those, with a cousin shape dealt from a different seed. A shape is 2 to 4 notes; the first is the root, third or
fifth; each next note moves by -2, -1, -1, 0, +1, +1 or +2 scale steps, held between -2 and +6; gaps of 1 to 3
sixteenths. The main shape's start is one of 2, 6, 8, 10, 3, 11. Notes are folded into the octave from A
sharp 3. A hook made by hand is kept from block to block; otherwise each block gets new ones.

**Break** (`Groove.start_break`, `deal.break_ending`). When asked for: sub and bass out, kick at 0.35, hats and
ghosts busier by 0.25, for a set number of bars; 27% end with four rising snare hits, 27% leave the last
sixteenth empty.

**The tune's sound** (`kit.tone_slices`, `Groove.set_kit`, `Groove._make`, `kit.fold`, `kit.repitch`). As in
section 6.

## Where repetition is doing the work

Every place where being able to follow the music depends on literal repetition or on a fixed template.

1. **The layer's rhythm.** One set of sixteenths per density and style, the same in every bar. The listener
   learns "0, 2, 6, 14" and it never moves unless a person mutates the layer or changes the density.
2. **The one.** A slice on the first sixteenth of every bar, without exception.
3. **The phrase form.** Bar 3 is bar 1. Bar 2 is bar 1 with one swap. Bar 4 is half of bar 1 plus the stutter.
   The same form in every phrase of every layer.
4. **The stutter.** The same six sixteenths, the same slice (the phrase's first), every fourth bar. It is the
   only fill and the only roll a layer has.
5. **The sound's own order.** A phrase is a run of neighbouring slices read left to right; the next phrase is
   the next run. Recognising the sound depends on hearing it in its original order.
6. **Short walk cycles.** A sound of five or six slices comes all the way round in two to five phrases; a
   twelve-slice sound at density 0.8 alternates between two phrases.
7. **The held layer.** After a mutation a layer is a literal four-bar loop until a person changes it.
8. **Layers in unison.** Several layers at the same density share one template, so they reinforce the same
   sixteenths.
9. **The drum spine.** Kick on the one, snares on 4 and 12 in every bar; about four distinct kick-and-snare
   bars in 64. The hats and ghosts differ from bar to bar, but by independent chance on each sixteenth, with a
   half-strength return every four bars (similarity 0.62 at lag 4 against 0.48 at lag 1).
10. **The written hats.** In `dnb` the hats on 2, 6, 10, 14 sound in 88% of bars.
11. **The five fills.** A fill is one of five fixed figures, only in the fourth bar.
12. **The sub's loop.** A four-bar riff four times, or an eight-bar riff twice, then a wholly new riff at the
    next 16-bar line (similarity 0.74 at lag 4, 0.12 at lag 16). 70% of moves are the same note again.
13. **The bass's two sixteenths.** The same sixteenths, the same length, every bar.
14. **The hook's one return.** A shape is recognisable because it is played again, unchanged, four bars later.
    It is then discarded.
15. **The hook's calendar.** Three bars in every eight, always.
16. **The non-break styles.** Sub and bass are an exact four-bar loop.
17. **Anything written by hand.** A pattern edited or mutated by hand plays exactly as written, every bar.
18. **The tune's instrument.** Every note of the tune is the same one or two 0.3 s pieces of sound, played
    faster or slower.

What follows a rule that is not repetition, for comparison: the walk through the sound (a fixed stride), the
dealing of hats and ghosts (independent chance), the choice of a new sub riff and new hooks (independent
chance). None of these takes account of what was just played.

## What is measured but unused

Data the code already computes, with where it is computed and what reads it now.

| Data | Computed in | Read today by |
|---|---|---|
| Each slice's `level` (loudness) | `chop.measure` | nothing |
| Each slice's `tonal` (how pitched it is) | `chop.measure` | nothing |
| Each slice's `punch` (attack peak) | `chop.measure` | one substitution in bar 2, only when a snare sixteenth is among those chosen |
| Each slice's `len` | `chop.measure` | placing "rest" entries (which layers ignore) and moving the picture; not the choice of sixteenth or the gap after it |
| Each slice's `pos` (where it was in the sound, so the original gaps and rhythm between slices) | `chop.measure` | moving the picture only |
| How strong each onset was (the `jump` ratio) | `samples.onsets` | thrown away once the cut positions are chosen |
| Whether the sound had obvious transients at all (percussive or a wash) | `samples.cut_points` | the message shown, and the fall back to eighths; not how it is played |
| The bar as dealt: every kick, snare, ghost, hat, pickup and fill, with how hard, known at the bar's first sixteenth | `Groove.dealt` | the drums only; layers plan from the written pattern |
| Whether a break is running, when it ends, and how it will end (roll, gap) | `Groove.break_start`, `break_end`, `break_shape` | the drums and low end; a layer only if told "only in the breaks" |
| The sub's current scale step | `Groove.sub_degree` | the bass; not the hooks, not the layers |
| The sub riff for the block and the hooks for the block, known in full in advance | `Groove.sub_cache`, `hook_cache` | each by its own part only |
| The last 900 notes and hits of every part, with pitch | `Groove.played` | the roll on screen |
| When each part last sounded, per sample | `Groove.struck`, `last_hit`, `since` | ducking only |
| When each layer last started a slice | layer `hits`, `Mixer.clip_steps` | the roll on screen |
| A score for every candidate window of a film's sound (level, flatness, steadiness) | `kit.tone_slices` | the choice of three, then discarded; nothing is kept about the pieces chosen |
| The spectrum of every candidate window (from which a pitch could be read) | `kit.tone_slices`, `chop.measure` | flatness only; no pitch is taken from it |
| A 16-step riff for the tune (`riff`) | `Groove.rescore`, `Groove.mutate` | nothing: it is stored in memories and never played |
| A four-bar movement of roots (`movement`) | `Groove.rescore` | the sub and bass in the non-break styles only; overridden by the sub riff in the break styles |
| The style's swing | `groove.STYLES`, `Groove.swing` | the rhythm section's odd sixteenths; not the layers |
| A film's measured tempo and first beat | `tempo.detect` | the picture's pulse when there is no rhythm section; with the rhythm section running it is not used, and slices are not fitted to the tempo |
| The session's energy | `gl_view.py` | on/off thresholds for parts, hat and ghost chances, and layer density; not riff shape, hook count, register or fills |
| The count of bars since the music began, and since the structure last changed | `Groove.step`, `Groove.changed_at` | holding back changes of structure; nothing in the dealing |
| The vocabulary of feel (nine kinds, each with what it asks of the engine) | `feel.py` | defined and read; not wired to the sound |
