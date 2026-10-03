# 07. What makes dance music good rather than competent: the instrument, the sample, and how much chance

Written 2026-10-03. Secondary research. The question comes from the owner's verdict after listening: the pattern is
mostly fine, but the composer "wants to introduce too much random", and the tune "reads as very generic, often one
note per bar, without any real interest in the instrument itself", to the point where the owner would rather take the
tune out and leave the samples.

This file builds on, and does not repeat, `README.md` (the overlay), `00` (what the program does, measured), `03`
(where samples sit), `04` (legibility) and `05` (bass, sub and hooks that progress). Where those already settle a
point, this file points to them by section.

How to read the marks:

- **[n]** a numbered source at the end. Unmarked means I read the page itself (in an extracted text form, so wording
  is paraphrased and any exact figure that matters should be checked against the page).
- **[L00], [L03], [L04], [L05], [LR]** the project's own research files `00`, `03`, `04`, `05` and `README.md`.
- **[snippet]** the claim rests on a search-result summary because the page was blocked or came back empty.
- **[weak]** a generic how-to site or forum, not a named producer, magazine, manufacturer or scholar.
- **[computed]** my arithmetic. Tempo figures use 166 BPM unless stated: a sixteenth is 90 ms, a beat 361 ms, a bar
  1.446 s, 16 bars 23.1 s.
- **[unsourced]** my belief or inference.

One caution about method. Some page summaries returned by the fetching tool were visibly invented (one summary of a
research paper described findings the two-page paper does not contain; I read the PDF and discarded it). Every
synthesis number below comes from a page whose text I could see or from a search summary marked [snippet].

---

## Summary

The owner's two complaints have one cause and one remedy each.

**The tune is generic because its sound never moves, not because it has few notes.** Good dance music is full of
hooks that play one or two pitches: a one-note pulsing sequence carries the first act of a 1990 techno classic, with
the interest in a resonant filter moving under it [14]; a two-note figure carries a Jeff Mills track for 80 bars while
two bell timbres are swapped in and out under it by hand [15]; the 303 line that founded acid house was a fixed
sequence whose cutoff and resonance were turned while it ran, in a jam an hour long [12, snippet]; a Daft Punk 303 line
is described as never still, its cutoff and resonance always moving so that attention does not wander [13]. In
mindstream the tune is two saws a hair apart (17 cents [computed]) with harmonics that decay at fixed rates, rendered
once per pitch and cached, so the same note is the identical sound every time it plays, and its 108 to 330 ms length is
shorter than one cycle of its own detune beating [computed, from `groove.py`]. Nothing about it can change over a bar,
four bars or sixteen. That is the measurable form of "no interest in the instrument".

**The pattern is too random because chance is choosing identity.** Every source that treats variation in this music
puts identity (the riff, the sound, the hook sample, where it sits) on a slow, fixed clock and lets variation act
only on decoration, on which bars sound, and on parameter position along a planned path [27][28][15][LR][L05]. The
tools producers use for variation are mostly periodic or fenced, not dice: Elektron's A:B trig conditions fire a note
on a fixed cycle of pattern repeats [38, snippet]; Grids interpolates between drum patterns learned from real records
and adds chance only as perturbation of density [37]; Ableton's own guide to chance suggests anchor points where parts
come back together [39]. mindstream's hook draws a new shape every eight bars from uniform small steps, with unrelated
"cousins" in between [L00 §5], which is chance choosing identity.

The strongest findings:

1. **Movement over notes.** Snoman's manual says that when a part is the same note in a repeating pattern, sound design
   matters more than the notes [34, snippet]. Garcia names timbre and filter change, and adding and removing layers, as
   the variables of a repeating track whose grid stays fixed [27]. Smith shows continuous processes (sweeps, slides,
   swells) telling listeners where they are in the phrase, aligned to 4-, 8- and 16-bar spans [29]. Every classic sound
   examined here (acid, hoover, Reese, wobble, neuro, dub chord, rave stab) is defined by what moves in it.
2. **The movement is tied to the beat and the phrase.** Neuro patches sweep wavetable position once per bar and a
   shelf at sixteenths [6]; hoover patches sync an LFO to a half note [4]; wobble rates are quarter, eighth and
   sixteenth notes, and the rate itself is automated through a phrase [25, snippet]; a techno pad's filter rises from
   about 50 Hz across each four bars [18]; the 303's accents build higher with each consecutive accented step because a
   capacitor has not discharged [10]. Movement has two clocks: a fast one locked to the grid, and a slow one (4 to 32
   bars) that carries the phrase.
3. **Samples carry the hook in most of this music, and the owner's instinct matches the reference.** In the owner's
   measured jungle set 79% of melodic events are stabs or short fragments and 3% are sustained lines [L03 §3][L05 §7].
   Classic records turn one sample into the hook by treatment: a sampled FM harpsichord chord replayed across the
   keyboard [5], a reversed Orbital string sample carrying the middle of "Energy Flash" [14], the Reese itself sampled
   and replayed in "Terrorist" [1]. Sample-led is lazy when the sample is looped untouched and always present;
   it is good when it is tuned, cut to its strongest part, given a role, withheld and developed [L03 §5, §7][41][43,
   snippet].
4. **Controlled repetition is the genre's strength and ambiguity its craft.** Garcia argues that pleasure here is in the
   process of an "ever-changing same", the listener asking when it will change and how it will stay the same [27].
   Butler argues that much of the nuance relies on ambiguity that makes the listener build the metre actively, and
   notes techno's absence of cadences [28]. Neither describes randomness; both describe a fixed frame with planned
   departures.
5. **Generic has a recognisable shape.** Every element on all the time, static presets, no focal point, no contrast
   between sections, a drop identical to the last [47, weak][L05 §10]. The research on builds and drops ties intensity
   to removing and returning the bass and kick, large frequency changes and contrasting breakdowns [30][31].

**What mindstream should do**, in one paragraph (section 7 has the detail): stop playing the plucked-saw tune by
default; make the tuned film sample the default hook, with the 03 stage plan (tease, state, chop, answer, out,
return); add one **signature instrument** per scene, chosen from the catalogue in section 6, that plays very few notes
but has two to four parameters on a phrase clock; render the tune lane continuously (or sample its parameters from a
phrase curve at each note-on) so that the sound can change across 4 and 16 bars; and confine chance to bar masks,
decorations and the choice among a few composed variants on a fixed periodic schedule, seeded per section.

What could not be found: note-level or patch-level documentation of the original hoover, Belgian and jungle stabs
(the Alpha Juno factory patch parameters, the T99 stab recipe, which its makers called a secret); any producer
interview giving automation curves in bars for a jungle tune; and any study measuring how much timbral movement a
listener needs before a repeated part stops sounding static. Section 8 lists the rest.

---

## 1. The instrument, not the notes

### 1.1 What the sources say about few notes and moving sound

- **Snoman.** Where the music is less melodic and consists of one note repeating in a pattern, the sound design is
  what matters; he tests melodic parts on a plain piano timbre to judge the notes on their own [34, snippet]. The
  implication is a split: either the notes carry the part (and a plain timbre will show it), or the timbre does.
  mindstream's tune is in the second class (about one note a bar [L00 §5]) while built like the first.
- **Garcia.** In a looped track the constant is the rhythmic grid and the foundational loops; what changes is timbre,
  filtering, layers in and out, and metric clarity. In his reading of a Plastikman track, EQ and filter shifts together
  with removing a layer forecast the next accumulation, so timbre does structural work [27, §4.3].
- **Smith.** Continuous processes (pitch slides, sweeps, swells) have three jobs: ornament (short, repeated, as an
  effect on a note), orientation (rising sweeps and slides across a build tell the listener a downbeat is coming) and
  disorientation (in a breakdown, tremolo and accelerating layers blur the reference). His examples run 2, 3, 4, 7 to
  8, 16 and 32 bars, and processes sit just before and after hypermetric downbeats, longer and louder for bigger
  boundaries [29, ¶3.3-3.37].
- **Named records.**
  - "Energy Flash" (1990): the signature element enters at bar 25, a one-note pulsing sequence above the sub whose
    filter resonance moves mechanically; the middle section is carried by a reversed string sample [14].
  - "The Bells" (Jeff Mills): a two-note back-and-forth in A minor runs for the whole first half; a lower bell with long
    decay and a higher short one are brought in and out almost at random by hand; from bar 65 the bassline takes
    over; the article puts the energy down to muting and unmuting loops, not to changes in the sequence [15].
  - "Da Funk": the 303 enters with the cutoff low, the clap returns as it opens, and later the cutoff is still moving
    so that attention never wanders [13].
  - "Acid Tracks": a preprogrammed sequence whose pitch and filter settings were turned while it played; the release is
    a 12-minute edit of an hour-long jam [12, snippet].
  - Robert Hood describes minimal as stripped-down rhythm tracks with "maximal soul", and the trance of staying in one
    repetitive pocket [44, snippet].
- **The hoover's fame is the sound.** It came from a factory preset (Alpha Juno "WhatThe"), reportedly made as a joke
  by a Roland sound designer, and was played across 1991 on "Mentasm", "Dominator", "Charly" and "Anasthasia" [2][3].
  The same patch, played with different notes, made a run of different records; what they share is the instrument.
- **Same for the organ bass.** The Korg M1 "Organ 2" preset is the bassline of "Show Me Love" (1990) and of a long run
  of later house records; the author of one write-up says the factory preset, unedited, is that exact sound [19]. The
  producer reportedly stepped to the next preset by chance and kept it [20, snippet].

### 1.2 What "movement" means, concretely

Collected from the recipes in section 6 and the sources above. Each is a parameter that changes during a note, across
a bar, or across a phrase.

| movement | what changes | typical clock | sources |
|---|---|---|---|
| filter envelope | cutoff jumps then decays each note; depth and decay set the "pluck" or "squelch" | per note, 30 ms to 2 s | [7][8][10] |
| accent | louder and a bigger, smoother filter sweep on chosen steps; consecutive accents climb | per step, pattern-defined | [9, snippet][10] |
| glide / slide | pitch slides into the next note instead of re-striking | per note pair, 60 ms on a stock 303 | [9, snippet][6] |
| detune beating | two or more oscillators a few cents apart beat; each harmonic beats at a multiple of the base rate | free-running, set by detune and pitch | [1] |
| PWM | pulse width (or the flat segment of a "PWM saw") swept by an LFO | 3 Hz in one Reese recipe; half-note sync in one hoover | [1][4][2] |
| chorus | short delay modulated by a slow LFO | 0.5 to 0.9 Hz on a Juno-60; 9.75 Hz in the combined mode | [22] |
| wavetable or phase-mod position | the waveform itself morphs | one cycle per bar in a neuro recipe | [6][1] |
| pitch envelope | a short pitch swoop at note start | per note | [3][4] |
| filter or EQ LFO | cutoff, band-reject notch or shelf swept | 1/16 for a shelf, 1 bar for a notch, 1/4 to 1/16 for wobble | [6][25, snippet] |
| distortion amount | more drive brightens and thickens | per section, or ridden | [6][8] |
| delay feedback | repeats grow into a wash or die away | ridden by hand; per phrase | [16][17, snippet] |
| automation over a phrase | cutoff, LFO rate, resonance, send levels | 4 bars (pad filter), 8 to 16 (build), whole track (acid) | [18][29][13] |

The two clocks are the important structure [inference, from the table]: a fast clock locked to the grid (per note,
per sixteenth, per bar) that makes the sound alive, and a slow clock (4, 8, 16, 32 bars) that makes it go somewhere.
A part with only the first sounds like a preset looping; a part with only the second sounds like a static note being
faded.

### 1.3 Register, layering and splitting

- Split low and mid. A sub (sine or filtered square, mono) carries weight; a mid layer carries the character that small
  speakers hear [L05 §3.2]. The Reese tutorial's second recipe is the same idea inside one patch: a pulse wave swept at
  3.2 Hz through a low-pass at about 800 Hz with full key tracking [1, page 2].
- Stack octaves for size. The hoover is described as three oscillators an octave apart with PWM and heavy chorus [2];
  the Landlord stab voices an E minor chord as E2, E3, E4, G4, B4, root doubled across three octaves [5]; techno pad
  advice adds octaves above and below without changing the harmony [18].
- Layer two sounds and alternate them. "The Bells" uses a long low bell and a short high bell on the same two notes,
  switching between them [15]; the T99 stab is reported to be a layer of sounds on an Akai S950 [24, snippet, forum].
- Keep the hook register narrow. The reference jungle set's hooks sit at 233 to 392 Hz [L03 §6]; the instruments below
  should place their main energy there when they play the hook role, and below 174 Hz only when they are the bass.

### 1.4 What this says about mindstream's tune [from the code; arithmetic marked]

From `groove.py` `_make` (kind "pluck", no film yet) and `_tone`, and `deal.py` `hook_shape`, `hooks`, `hook_note`:

- Two additive saws (9 harmonics) at 0.995 and 1.005 of the pitch: 17 cents apart [computed]. The beat rate is 1% of
  the pitch: 2.3 Hz at 233 Hz, 4.4 Hz at 440 Hz [computed], a period of 230 to 430 ms.
- Note length is `max(length, 1) * 1.2` sixteenths, so 1.2 to 3.6 sixteenths, 108 to 325 ms at 166 BPM [computed]. Most
  notes end before one beat cycle completes, so the detune is heard as a fixed tone colour, not as movement.
- Harmonic k decays with a time constant of 0.35/k s: the fundamental barely falls during the note, the ninth falls by
  about 1/e every 39 ms [computed]. That is a darkening pluck, identical on every note.
- No filter, no velocity, no accent, no glide, no envelope depth that varies.
- Each note is rendered once and cached under (kind, pitch, length, revision, kit, rescores), so the same pitch at the
  same length is the bit-identical sound for as long as the settings hold. Settings change only by hand or by a film
  arriving. Effects in `_finish` (including `sweep` and `filter`) are applied inside the note, so even a sweep is the
  same sweep each time.
- When a film is loaded, the tune is a 0.16 s or longer cut of film sound, repitched (out of tune, see [L00 §6]) and
  faded; it too is identical for every repeat of a pitch.
- A stateful filter that can be swept while sound plays already exists (`mangle.Filter`), but only the demo uses it.

So the complaint is exact. The tune is a short, static, identical sound; at about one note per bar it has nothing of
its own to offer. More notes would not fix it. A sound that moves, or a sample that is itself interesting, would.

---

## 2. Samples as the music

### 2.1 How much of good dance music lets samples carry the hook

- In the owner's measured jungle reference, hooks are 79% stabs and short fragments, 3% sustained tones or lead lines;
  a hook sounds in 39% of bars [L03 §3]. Reynolds in 1995 heard keyboard motifs that rarely amounted to a riff; Fabio
  said the music has few hooks and little melody [L05 §7].
- Classic jungle and hardcore hooks named in the earlier reports are samples: the Reese sampled from a Detroit record
  and replayed in "Terrorist" [1][L05 §3.2]; film dialogue and horns in "Original Nuttah"; a rare-groove vocal and
  bassline in "Burial" [L05 §4.2]; rave stabs that are one sampled chord played up and down the keyboard [21,
  snippet][L03 §1].
- The Landlord stab, a template for the rave stab, is a sampled FM harpsichord from a drum machine's expansion,
  itself from a DX7; the modern recipe still ends with "resample the chord into a sampler and play it as a descending
  riff" [5]. Hardware stab practice was to bounce the finished sound and resequence it in a sampler [21, snippet].
- In techno and house the balance is wider: synth hooks dominate acid and minimal; sample loops dominate filter house
  [L03 table]. A whole track from one sample is a recognised exercise and a style (Erdbeerschnitzel's "one track, one
  sample", drums, bass, chords and hook from one source) [42].

So the owner's remark ("that's a lot of edm anyway") is right for jungle and rave: the hook role is mostly sampled,
and the synthesised parts that do carry tracks (303, hoover, Reese, organ) are instruments with a strong, moving sound,
not neutral tones playing a tune.

### 2.2 What makes a sample-led track good rather than lazy

From the sources, set against [L03 §7], which already lists what makes placement sound intended.

1. **Treatment over source.** Tim Reaper: what matters is how a sample is treated and what is done with it [L03 §7].
   A production duo described in a recent studio profile put it as flipping, not looping: finding the best parts,
   chopping and arranging them [43, snippet]. Schloss's distinction between looping (a long phrase repeated mostly
   intact) and chopping (dividing and reconfiguring) is that chopping shows the producer's hand [L03 §4].
2. **The strongest part, cut tight.** Choose the syllable, the hit, the swell; start on its own transient; end at a
   syllable boundary or gate it hard [L03 R4]. One sampled chord is enough for a riff [5][21].
3. **In tune and in register.** Match tempo and key first, then slice; pitch shifts beyond about three semitones
   degrade a voice unless damage is the point; formants decide whether pitched voices sound chipmunk or demonic [41]
   [L03 §4]. Pitch before slicing if timing matters [41].
4. **A role and a schedule.** Tease, state, chop, answer, out, return [L03 R7]. Absent most of the time [L03 §3].
5. **One element doing one job.** RP Boo: when the sample is the rhythm, nothing else is needed behind it [L03 §7].
6. **Made into an instrument.** Mapped across keys and played as a new figure (the stab riff [5][21]), stretched or
   reversed into a gesture (the reversed string of "Energy Flash" [14]), smeared into a bed [L03 §4].

Lazy, by the same sources: an untouched loop running every bar; a sample left at its own key against the bass; long
samples in the hook register; samples that cover the snare; every sample present from bar 1 [L03 §8].

### 2.3 How a sample becomes the hook: a procedure

Assembled from [5][41][21][L03 R4-R10]; ordering mine.

1. **Pick** by measured properties: a clear onset, a stable pitch (for a tonal hook) or a strong formant (for voice),
   and length under two beats for the hook role [L03 R4].
2. **Track pitch** and repitch from what it is, within three semitones where the source is a voice [LR step 0][41].
3. **Cut** to one gesture; gate the end with a short fade at its slot.
4. **Shape** with an envelope and a filter of its own (the Landlord recipe re-envelopes the resampled chord with a
   low-pass to manage its tail [5]); high-pass at about 200 Hz in the hook role [L03 R9].
5. **Play it as an instrument**: a small pitch set (four or five notes shared with the bass [L05 §2]); one-shot stab
   riffs on off-beat sixteenths [L03 R3]; or a single repeated gesture with its filter or start point moving across
   the phrase.
6. **Develop** by treatment, not by replacement: filter opening across the tease [L03 R8], reverse lead-in, echo throw,
   stutter at phrase end, pitch as an effect at a section change.

### 2.4 When a synthesised tune adds something, and when it is clutter

- **It adds** when it is a signature sound with movement (acid, hoover, Reese, organ, dub chord), when it has a
  clearly separate role from the sample hook (the second bass identity of the classics [L05 §4.2]; the 303 entering for
  the second movement of a track [13]), and when it takes turns with the sample rather than playing over it (two vocal
  ideas that never overlap sound arranged [L03 §8]).
- **It is clutter** when it doubles the hook register while a sample is sounding; when it is a neutral tone playing a
  few notes (Snoman's split: a part with few notes must earn its place by sound [34, snippet]); and when it is always
  on. This is [inference] from the sources above, but every source points the same way.

---

## 3. Randomness and intent

### 3.1 What writers say about repetition

- **Garcia** [27]. Repetition yields process pleasure, coextensive with the activity, rather than the pleasure of an
  ending. Thick textures give several points of attention and listeners build their own path through them. The core
  question for a listener is when the music will change next and how it will remain the same (¶6.2). Defences that
  call every repetition "variation" are rejected: the repetition is real and is the point.
- **Butler** (as reviewed by Marshall) [28]. The loop is the basic unit; many nuances rely on ambiguity, so the listener
  builds the metre actively; techno lacks cadences; he describes multi-measure patterns at length (pp. 184-201) and DJ
  sequencing techniques as the clearest account of their kind. The reviewer's opening recalls Stockhausen's 1995
  advice that techno producers vary every rhythm with a direction; Butler's book is a reply that the music's interest is
  elsewhere.
- **The owner's corpus and reference** [L04 §1, §2.1]: surprise only counts against a trusted frame; four to eight
  unchanged repeats of a four-bar unit is the boredom zone and a change every bar is the other failure; three cells
  near-certain and everything else dealt by odds; the group returns at four bars.
- **Snoman** [34, snippet]: repetition is what makes a melody stick; dance music repeats more openly than pop; motifs
  use question and answer.

### 3.2 What reads as too random

Collected from [L04][L05 §9.4][LR] and the sources here.

- **Identity drawn by chance.** A riff, a hook shape, a sound or a placement that is new each time it could have been
  the same. Note-to-note chance models stay in key and go nowhere [L05 §9.4].
- **Variation with no period.** Changes that do not land on 4-, 8- and 16-bar lines [L04 §2.2][29].
- **Everything varying at once.** The reference changes one layer at a time; slow layers change where the riff changes
  [L05 §2][LR].
- **Variation in the frame.** Moving the kick on the one or the snare is a large error; the frame is what lets other
  surprises count [L04 §1].
- **No return.** A shape that never comes back cannot be heard as varied; a varied return needs a memory [L05 §5.3].

### 3.3 How generative and performance tools handle it

| tool or system | how chance is fenced | source |
|---|---|---|
| Elektron trig conditions | A:B fires a step on the A-th of every B pattern repeats (1:4 = first of every four); FILL fires only in fill mode; conditions can depend on whether a previous step fired. Periodic variation, no dice | [38, snippet] |
| Ableton Live 11 chance | per-note chance and velocity ranges; the vendor's guide suggests velocity ranges on hats, chance for sparse high melodies, and anchor points where parts come back together | [39] |
| Mutable Instruments Grids | drum patterns from real loops organised into a 2-D map; coordinates morph between learned patterns; per-channel density thresholds remove or add notes in an order set by the pattern's own backbone; "chaos" randomly perturbs the density, adding rolls and ghosts | [37] |
| Euclidean rhythms | k onsets spread as evenly as possible over n steps; E(3,8) is the tresillo, E(5,8) the cinquillo; rotation and density are the only variables | [40, snippet] |
| GEDMAS | first-order Markov chains and probabilities trained on 100 hand-transcribed EDM tracks generate form, chords, melodies and rhythms | [35] |
| GESMI | a breakbeat generator trained on hand-transcribed breaks tracks (1994-2010); transcriptions include timbre descriptions and the use of effects and their change over time; its author notes that generative EDM is a frequent beginner project because of the style's repetition and explicit forms | [36] |
| Autechre (from [L04]) | rule sets they understand, no random operators, one event recurring triggers another | [L04 §1] |

Two things stand out [inference]. The tools that sound musical use chance on **density and decoration inside a
learned or written structure** (Grids, velocity ranges, fills), or replace chance with **periodic conditions** (A:B).
And the research systems found it worth transcribing **timbre and effect changes over time** as part of the style
[36], which supports section 1: a generator of pitches and onsets alone is missing part of what makes the music.

### 3.4 What to fix, what to vary, on what clock

This merges [L04 §5], [L05 §12] and [LR] with the findings above. Starting values; tune by ear.

| clock | fixed for the span | varied inside the span | chance allowed |
|---|---|---|---|
| every sixteenth | the grid; the spine cells (1, 5, 13) | velocity within a small range; ghost notes | yes, low, on decorations only |
| every bar | the section's step template for each lane; the instrument patch; the hook sample | which decorations fire; the fast modulation runs (LFO, envelope) | yes, on bar masks within a budget |
| every 2 bars | the statement | the answer is derived (ending changed, one note moved) | choice among 2 to 4 written answers |
| every 4 bars | the motif; the patch's slow-curve shape | phrase-end event (fill, stutter, throw, drop-out): its kind varies | kind chosen from a short list; whether it happens on a fixed A:B cycle |
| every 8 bars | the hook sample, its role and template | one macro target moves (filter opens further, delay feedback up, a layer swaps) | which macro, from the instrument's own list |
| every 16 bars | the section | a new modulation destination, a second layer in or out, a turnaround | the fate of the riff (back after a hole, partly rewritten, new) by the measured odds [L05 §2] |
| about 32 bars | the scene's instrument set | B motif or B bass; kick style and carrier change with it | which composed B |
| about 64 bars | the scene | A back, changed | none |

Rules that make this concrete [inference unless marked]:

- **No fresh draw for anything that is identity.** Identity is drawn once per section from a seed and held.
- **Chance chooses among composed alternatives** (two to four written answers, endings, fills) on a fixed cycle where
  possible (an A:B schedule [38, snippet]) rather than per bar.
- **One dial past the lip at a time** [LR], and one layer turning over at a time except at real section edges
  [L05 §2].
- **The fast clock is locked, the slow clock is planned.** LFOs and sweeps sync to the bar or its divisions; phrase
  curves are drawn per section with a direction (open, close, rise, fall) and land on the line.

---

## 4. What separates good from generic, more broadly

### 4.1 Groove

- Swing as defined by Roger Linn: the percentage of each eighth taken by its first sixteenth; 50% is straight, 66% is a
  triplet feel; he delays the even sixteenths only; the useful range is about 50 to 70% [33]. The jungle reference is
  straight (52.4%) with looseness inside the slices [L04 §2.2].
- Medium syncopation gives the most desire to move and the most pleasure (an inverted U) [32]. One syncopation placed
  at a phrase end against a firm frame beats shifting everything [L04 §1].
- Dilla's offsets are small, deliberate and the same every repeat [L03 §1]: deviation that repeats reads as feel.

### 4.2 Space, contrast, tension and release

- Removing and returning the bass and kick, large frequency changes, uplifters, drum rolls and contrasting breakdowns
  are the techniques found in build-ups and drops [30]. A student study of drum & bass listeners found valence, arousal
  and "power" higher at the drop and tension higher in the build, and tension falling at the drop in every subgenre
  [31]. In the jungle reference, 82% of drops are prepared by taking the low end away for about a bar while the break
  runs, with no risers [L03 §2].
- Mala: a producer can add to a track by removing things [L03 §7]. Energy in "The Bells" comes from muting and
  unmuting loops, not from new notes [15].
- Contrast between sections: "The Bells" is melody-led for its first half and bassline-led for its second [15];
  "Energy Flash" has three acts, a one-note sequence, a reversed-string middle, a two-note figure with a doubling choir
  [14]. A second bass identity or a B section at about 32 bars [L05 §5].

### 4.3 The one memorable idea, and character

- A track can be one sound (hoover, organ, 303), one sample, or one figure (two notes). What it cannot be is several
  equal, neutral ideas [inference from 1.1 and 2.1].
- The classic sounds were partly accidents of the machine or of play: a preset made as a joke [3]; a used 303 bought
  cheap and twisted while it ran [12, snippet]; the next organ preset chosen by chance [20, snippet]; a Reese made on a
  Casio phase-distortion synth [1]; timestretch pushed past its limit into a metallic artefact [L03 §4][46, snippet].
  Character came from a strong sound pushed too far, then repeated.

### 4.4 Failure modes of generated and beginner dance music

From the weak sources [47] and from the earlier reports' tables [L03 §8][L05 §10], restated as checks:

1. Every element on all the time; no section without the hook.
2. Static presets: parts that sound the same in bar 1 and bar 64.
3. No focal point: several parts of equal weight in the same register.
4. Variation every bar and no return (the generated failure), or exact loops for 64 bars (the beginner failure).
5. Notes chosen independently of the bass and the drums.
6. Drops identical to each other; no B material.
7. Over-processing: stacked effects that remove identity [L04 §1].
8. Tunes out of tune with the bass (a sampled tune left at its own key) [L00 §6].

mindstream as measured fails 1 partly, 2 fully for the tune, 4 in the hook lane (new shape every eight bars, cousins
unrelated), 5 and 8 [L00].

---

## 5. Named sounds: what makes each work

Short notes; the build recipes are in section 6.

- **Acid (TB-303).** One oscillator (saw or square), a resonant four-pole diode-ladder low-pass often described as
  18 dB/octave [11, snippet], two envelopes: a fixed volume envelope and a main envelope on the filter. On accented
  steps the main envelope runs at its short fixed time (about 200 ms on a stock unit [9, snippet]) and drives the cutoff
  through an "accent sweep" circuit, a capacitor charged through a diode; with consecutive accents the capacitor has not
  discharged, so each sweep goes higher [10]. Slides are 60 ms on a stock unit [9, snippet], and a slid note does not
  restart the envelope. The notes are a sequence; the music is the cutoff, resonance, envelope depth and decay being
  turned by hand while it runs [12, snippet][13]. Movement matters more than notes because the accent and slide pattern
  makes the filter contour itself a rhythm, and the hand on the cutoff gives that rhythm a phrase-length shape.
- **Hoover / mentasm.** A "PWM saw" (flat segments of variable width inserted into a saw), three oscillators an octave
  apart, a fast LFO on the pulse width and a thick chorus, plus a pitch envelope [2][3]. One modern recipe: PWM saw and
  pulse, a sub oscillator, transposed down an octave, a second envelope into pitch, an LFO synced to a half note,
  optional chorus, and sidechain pumping from the kick [4]. Works because it is a wall of beating partials that swirls
  on its own and swoops at every note start: a held chord is already an event.
- **Reese.** Two detuned oscillators (sines a quarter-semitone either side in one recipe, saws 0.07 semitone either
  side in another), mono, sustained [1]. The original was made on a Casio CZ phase-distortion synth for a 1988 Kevin
  Saunderson record and was sampled into "Terrorist" in 1994 [1]. Variants: a single pulse wave with PWM from a 3.2 Hz
  LFO through an 800 Hz low-pass tracking the keyboard [1, p. 2]; and a modern one built on phase modulation with an
  LFO on the phase amount for a growl [1, p. 3]. Works because the beating is a slow, self-generated rhythm; long notes
  and few of them [L05 §3.2].
- **Rave stab.** One chord, voiced wide (root in three octaves), sampled, then played as a riff across the keyboard so
  that every note is the whole chord transposed; the sampler's slowdown at lower pitches is part of the sound;
  bitcrushing, compression, saturation [5][21, snippet]. Works because it is a single bright, harmonically loaded
  gesture with a hard attack that can be placed like a drum.
- **Rave piano.** An M1-style piano layered into minor chords, sometimes with one or two further patches, bus-processed
  with heavy parallel saturation and bitcrushing [21, snippet]. Riffs in eighths and sixteenths over two octaves
  [L03 §1].
- **M1 organ bass.** A factory preset, bright enough to cut through heavy bass and effects [19]; a recreation recipe
  uses a triangle plus a narrow pulse an octave and a fifth or more above [20, snippet]. Works as a percussive
  mid-bass: a short, nasal, clicky note on a syncopated riff.
- **Juno pads.** Saw and PWM pulse, a 24 dB resonant low-pass, slow envelopes, and the chorus, which on the Juno-60
  runs a triangle LFO at 0.513 Hz (mode I) or 0.863 Hz (mode II) on two bucket-brigade delays swept between about 1.7 and
  5.4 ms, the right channel inverted [22][23, snippet]. Works because the chorus and PWM keep a held chord moving while
  the harmony stands still. Not tempo-locked: at 166 BPM chorus I takes 1.35 bars per cycle [computed].
- **Dub techno chord.** A short minor chord through a dark filter and a high-feedback, filtered delay (dotted eighth,
  or eighth, feedback ridden by ear, repeats darker each time), so the delay writes the rhythm [16][17, snippet]. One
  recipe: noise plus saw and square, a high-pass near 80 Hz with an LFO on it, short decay and low sustain, two delay
  taps (dotted eighth with 20% feedback, and 264 ms with 85%), a wide cut at 600 Hz, a low-pass at 4.5 kHz, a little
  plate and a phaser [16]. Works because the chord is one gesture, and the feedback and filter positions are the
  arrangement.
- **Techno pad.** Static harmony; octaves added for size; a low-pass rising from about 50 Hz to high across each four
  bars; extensions (sevenths, ninths); a substitute chord on bars 3 and 7 of eight [18].
- **Wobble.** A low-pass on a saw or saw-and-square, cutoff driven by a tempo-synced LFO: quarter for slow, eighth for
  the classic, sixteenth for talking basses, quarter triplet for a rolling feel; the LFO rate is automated through a
  phrase (quarter, eighth, sixteenth) to build [25, snippet]. Works because the modulation rate is a rhythm and its
  change is the development [L05 §3.2].
- **Neuro bass.** Two wavetables (one down two octaves), noise, a band-reject filter; an LFO synced to one bar moves both
  wavetable positions in opposite directions and the notch; a sixteenth-note sine LFO moves a high shelf; tube
  distortion at 90% drive, a frequency shifter, mono legato with long glide and a 24-semitone bend range; resonance and
  frequency-shifter mix automated through the performance [6]. Producers in this style resample through several
  generations [26, snippet, weak]. Works because every bar of the sound has a shape of its own, and the slow automation
  changes what that shape is.
- **Minimal motifs.** One or two notes (a one-note sequence, a two-note bell figure) with resonance moved mechanically,
  or two timbres swapped by hand [14][15]. Works because the listener's attention moves into the sound once the notes
  are known.
- **Jungle pads and stabs.** Strings, pads and stabs were mostly sampled and timestretched on Akai samplers, the
  stretch pushed into a metallic, stuttering artefact [46, snippet][L03 §4]; pads float across the fast drums and slow
  bass as release [L05 §7]. No patch-level documentation of a named jungle pad was found.

---

## 6. Catalogue: instruments worth building

Each entry is a recipe for a synthesised (or sampled-then-played) instrument. Rates are given against the bar so that
they follow the tempo; at 166 BPM one cycle per bar is 0.69 Hz, per beat 2.77 Hz, per eighth 5.53 Hz, per sixteenth
11.1 Hz [computed]. "Bar / 4 bars / 16 bars" describes what moves on each clock. Numbers from a source carry its mark;
everything else in a recipe is a starting point [unsourced] meant to be tuned by ear.

### 6.1 Acid line (303 type)

- **Oscillator.** One saw (or square). No detune.
- **Filter.** Resonant 4-pole low-pass; resonance high (0.7 to 0.9 of self-oscillation); keyboard tracking about half.
- **Envelopes.** Amp: instant attack, long fixed decay, gate cut at the step's length. Filter: instant attack,
  exponential decay set by a "decay" control (100 ms to 1 s); on accented steps decay fixed at about 200 ms [9,
  snippet], level up 3 to 6 dB, and envelope routed through a smoothing stage (one-pole, time constant about 100 ms) whose
  state carries over to the next accent so consecutive accents climb [10].
- **Glide.** Slide flag per step: 60 ms exponential glide [9, snippet], no envelope retrigger, gate held over.
- **Effects.** Drive before or after the filter (the Diva recipe uses 63% overdrive [7]; the SynthMaster recipe puts
  drive inside the filter [8]); eighth or dotted-eighth delay at 20 to 35% feedback, low mix, highs only [7].
- **Bar.** A 16-step pattern: 3 to 5 pitches, 2 to 4 accents, 2 to 4 slides, 1 to 3 rests. Accents and slides make the
  contour.
- **4 bars.** Cutoff and envelope depth ride a curve (for example closed in bar 1, opening through 2 and 3, a peak in
  bar 4 that resolves on the next bar line). Decay lengthens toward the phrase end.
- **16 bars.** A resonance step at 8 and 16; the pattern stays; at most one note or one accent is moved per eight bars.
- **Plays.** A riff, continuous while on. In jungle it belongs to an acid-jungle or rave scene, low-mid register,
  replacing the hook lane rather than sitting over it.
- **Why first.** The most movement per note of anything here, and the sources on it are precise [9][10].

### 6.2 Hoover

- **Oscillators.** Three "PWM saws" (a saw with a variable flat segment), at the note, an octave down and an octave up
  [2]; or saw plus pulse with PWM and a sub oscillator, transposed down an octave [4]. Each slightly detuned (3 to 8
  cents).
- **PWM.** LFO at 4 to 6 Hz, depth large; or synced to a half note for a slower churn [4].
- **Pitch envelope.** Short (50 to 200 ms) swoop into each note; depth 2 to 12 semitones; one recipe sets envelope-to-
  pitch depth to 24 on its scale [4]. Glide 50 to 150 ms between held notes.
- **Filter.** Mostly open; a gentle low-pass to tame the top.
- **Effects.** Heavy chorus (rate 0.5 to 1 Hz, deep) [2]; sidechain duck from the kick [4]; optional distortion.
- **Bar.** One held note or chord per bar or two, re-struck so the pitch swoop is heard; or a stab riff of 2 to 3 notes.
- **4 bars.** Glide down to the next note at the end of bar 4; PWM rate up slightly through the phrase.
- **16 bars.** Chorus depth and octave layer: start with one oscillator, add the lower octave at 8, the upper at 16.
- **Plays.** Held notes and swells, occasionally a stab riff. Rave and hardcore scenes, darkside jungle.

### 6.3 Reese (mid bass that breathes)

- **Oscillators.** Two saws detuned either side (0.07 semitone each in one recipe [1]); or two sines at ±0.27 semitone
  [1]. Option [unsourced]: detune in hertz, not cents, so the beat rate is a tempo value: with the two fundamentals 0.69 Hz
  apart at 166 BPM the fundamental beats once a bar, the second harmonic twice, the fourth once a beat, the sixteenth
  once a sixteenth [computed].
- **Filter.** Low-pass at about 800 Hz with full key tracking [1, p. 2]; cutoff riding a slow curve. High-pass the layer
  at about 100 Hz if a separate sub plays [L05 §3.2].
- **Envelopes.** Sustain full, release about 24 ms [1]. Mono.
- **Modulation.** Optional PWM at about 3.2 Hz [1, p. 2] (one cycle per eighth at 166 BPM would be 5.5 Hz [computed]);
  modern variant: phase modulation from a second oscillator an octave up, LFO on the amount [1, p. 3].
- **Effects.** Distortion before the filter (techstep put the Reese through a guitar pedal [L05 §3.2]); light chorus.
- **Bar.** One or two long notes.
- **4 bars.** Cutoff up through bars 1 to 3, back down at 4; a glide on the last note.
- **16 bars.** Distortion and phase-mod amount stepped up at 8 and 16; detune widened for a section.
- **Plays.** Long held notes, the second bass identity that takes turns with the sub [L05 §4.2].

### 6.4 Sampled chord stab (rave and jungle)

- **Source.** One chord: either synthesised (two saws or an FM-ish tone, voiced root, octave, double octave, minor third,
  fifth: E2-E3-E4-G4-B4 in [5]) and rendered to a sample, or a tonal film piece, tuned.
- **Treatment.** Bitcrush, compress, saturate [5]; render once.
- **Playback.** As a sampler: transposed by playback rate so lower notes are slower and longer [L03 §4][21, snippet];
  amp envelope full, then a low-pass envelope (attack instant, decay 150 to 400 ms) to manage the tail [5].
- **Bar.** Two to five stabs on off-beat sixteenths, avoiding the snare steps; most short, one longer [L03 §1].
- **4 bars.** A descending riff over a 3-to-5 pitch set; bar 4 varied, bar 8 more [L03 R2].
- **16 bars.** Filter envelope depth opening through the section; a reversed copy as the lead-in to bar 17.
- **Plays.** A riff in its sections, then gone.

### 6.5 Film-sound stab instrument (mindstream's own)

The program's real asset is its film material; this entry treats a piece of film sound as an oscillator.

- **Source.** A tonal film piece with a tracked, stable pitch [LR step 0].
- **Voice.** Play from a chosen start point within the piece; loop a short stable region (50 to 200 ms) for held
  notes; add a second copy detuned 5 to 10 cents for width.
- **Filter.** Low-pass with a fast envelope (as 6.4) and a resonance high enough to colour.
- **Modulation.** Start point (the "position" in the piece) moves on a slow curve across 4 or 16 bars: a "window
  walking through a sound", which [04] already ranks as a direction device [LR]. Filter LFO synced to the bar.
- **Effects.** Short slap or eighth-triplet echo; reverb printed and gated [L03 R9].
- **Bar.** One gesture or a two-note figure, back half of the bar.
- **4 bars.** The window moves; the gesture is the same, so the change is heard.
- **16 bars.** A new region of the same film; or the same region reversed as a lead-in.
- **Plays.** The hook, in the 03 stage plan.

### 6.6 Dub chord (delay as instrument)

- **Oscillators.** Saw and square, with some noise [16]; minor chord, notes nudged slightly off for looseness [16].
- **Filter.** High-pass near 80 Hz with an LFO on it [16], or band-pass around 450 Hz [17, snippet]; low-pass at about
  4.5 kHz and a wide cut at 600 Hz in the EQ [16].
- **Envelope.** Short attack, short decay, low sustain [16].
- **Delay.** Two taps: a dotted eighth at about 20% feedback and a longer tap at high feedback (85% in [16]); repeats
  filtered so each is darker [17, snippet]. At 166 BPM a dotted eighth is 271 ms [computed].
- **Bar.** One stab, usually off the beat.
- **4 bars.** Feedback up through bars 3 and 4 so repeats pile up into the turnaround, then back.
- **16 bars.** The filter centre walks; reverb send rises; the chord itself never changes.
- **Plays.** One stab a bar; for half-time, dub-techno and dub-influenced jungle scenes, and as a breakdown device.

### 6.7 Juno-style pad / jungle string bed

- **Oscillators.** Saw plus PWM pulse (PWM LFO 0.3 to 1 Hz), sub square an octave down at low level.
- **Filter.** 24 dB low-pass, mild resonance, slow filter envelope.
- **Envelopes.** Attack 0.3 to 1.5 s, full sustain, release 1 to 3 s.
- **Chorus.** Triangle LFO at 0.513 Hz or 0.863 Hz, delay swept between 1.66 and 5.35 ms, two lines in antiphase [22].
- **Effects.** Long reverb, high-pass at about 200 Hz [L03 R9].
- **Bar.** Nothing new; it holds.
- **4 bars.** Low-pass rising from low to high across the four bars [18].
- **16 bars.** Chord substitution on bars 3 and 7 of eight [18]; octave layer added at 8.
- **Plays.** A bed in intros and breakdowns, fading before the drop [L03 table]. Not an event; not counted as a hook.

### 6.8 Organ stab / organ bass (M1 type)

- **Oscillators.** Triangle plus a narrow pulse well above it (one recreation: pulse 31 semitones up at 60% level
  against the triangle at 40% [20, snippet]); a short click at the attack.
- **Envelope.** Instant attack, short decay to a moderate sustain, short release.
- **Filter.** Mostly open; a band emphasis around 1 to 2 kHz for the nasal colour [unsourced].
- **Bar.** A syncopated riff of 4 to 6 short notes.
- **4 bars.** Riff varies at bar 4; velocity (brightness) accents fixed per pattern.
- **16 bars.** Doubled an octave up from 8.
- **Plays.** A riff; for house, garage and speed-garage scenes.

### 6.9 Wobble mid-bass

- **Oscillators.** Saw plus square, one octave, slight detune.
- **Filter.** Low-pass, resonance medium; cutoff driven by an LFO synced to the grid: quarter, eighth, sixteenth or
  quarter triplet [25, snippet]; at 166 BPM an eighth is 5.5 Hz, a quarter triplet 4.2 Hz [computed].
- **Envelope.** Sustain full; LFO phase reset at note-on so every note starts the same.
- **Effects.** Distortion after the filter; a separate sub underneath.
- **Bar.** One or two notes; the LFO rate is the rhythm.
- **4 bars.** Rate pattern per bar (for example quarter, eighth, quarter, sixteenth).
- **16 bars.** Rate pattern changes; distortion up at 8; the classic build steps quarter, eighth, sixteenth [25,
  snippet].
- **Plays.** Half-time and dubstep scenes; in jungle, sparingly.

### 6.10 Neuro bass (moving every bar)

- **Oscillators.** Two wavetables, one two octaves down; noise at about a third [6]. A simpler substitute: two saws
  through a waveshaper whose shape parameter stands in for wavetable position [unsourced].
- **Filter.** Band-reject (notch) with modest resonance [6].
- **Modulation.** LFO A, one cycle per bar: both wavetable positions (opposite directions) and the notch cutoff. LFO B,
  sine at a sixteenth (or triplet): a high shelf [6].
- **Effects.** Tube distortion, 60% wet, 90% drive; a stereo widener; a frequency shifter [6].
- **Glide.** Mono legato, long glide; pitch bend range ±24 semitones [6].
- **Bar.** The bar is the gesture; one or two notes with the LFOs carrying the shape.
- **4 bars.** Frequency-shifter mix and resonance ride a curve [6].
- **16 bars.** A resampled "generation": render 16 bars, use the render as a new oscillator for the next 16 [26,
  snippet].
- **Plays.** Techstep and neuro scenes; a moving bass that is also the hook.

### 6.11 One-note pulse with a moving resonance

- **Oscillator.** A pulse or saw, one pitch.
- **Filter.** Resonant low-pass; cutoff modulated by a stepped or sine LFO at one cycle per one or two bars, so the
  resonance peak walks mechanically [14].
- **Envelope.** Short notes on sixteenths or eighths, slight accent on one step.
- **Bar / 4 bars / 16 bars.** The pitch never changes; the LFO depth grows across the phrase; at 16 the filter type or
  the step pattern changes.
- **Plays.** A pulse above the sub; the Energy Flash device [14]. Useful in jungle as a tension layer under a breakdown.

### 6.12 Two-timbre bell motif

- **Voices.** Two bells on the same two notes: one low with a long decay, one high and short [15]. mindstream's `_bell`
  is close to the second.
- **Movement.** The two are faded in and out against each other on a slow clock; a filter on the low one.
- **Bar.** The two-note figure on fixed steps.
- **4 / 16 bars.** Which bell sounds, and how loud, is the variation; the notes never change [15].
- **Plays.** Techno and atmospheric scenes; the figure can hand over to the bass at about bar 65, as in [15].

### 6.13 Formant voice pad (film voice made into an instrument)

- **Source.** A voice piece from a film, tuned.
- **Treatment.** A formant (vowel) filter, two or three band-passes at vowel positions, moved between two vowels on a
  slow curve; long reverb; resample into a pad [L03 §4].
- **Bar.** Holds.
- **4 bars.** Vowel moves from one to the other and back.
- **16 bars.** The source syllable changes; the vowel path stays.
- **Plays.** A bed that reads as human, in breakdowns [L03 §4]. Recipe [unsourced] beyond the cited voice-to-pad idea.

---

## 7. What mindstream should do

Ordered by priority. Each item says how well it is supported.

### 7.1 Drop the plucked-saw tune as the default (supported)

- Turn the "pluck" tune off by default in jungle and breaks scenes. Keep the lane, but fill it with the tuned film-sound
  hook (6.5) following the 03 stage plan, and leave bars empty by the 03 budget (hooks in about 3 bars of 8).
  *Support:* the reference's 79% stabs and 3% lines [L03]; the owner's own preference; Snoman's split [34, snippet];
  every named synthesised hook found here is a moving signature sound, not a neutral tone.
- Keep a synthesised hook only as a **signature instrument** (section 6), one per scene, entering as a section event
  (on an 8- or 16-bar line, after the hook sample has been stated), and taking turns with the sample: never both in the
  same bar of the hook register. *Support:* turn-taking [L03 §8]; second identity [L05 §4.2]; the rest is inference.
- Before any of this, tune the film material (step 0 of [LR]). Without it a sample hook will be as wrong as the pluck.

### 7.2 Let the instrument move: phrase-clock modulation (well supported in principle; implementation is inference)

The present renderer makes each note once and caches it, which rules out movement across a phrase. Two ways to fix it:

1. **Parameters sampled at note-on.** Each tune-lane parameter (cutoff, resonance, envelope depth, decay, drive, PWM
   depth, window position in the film piece, delay feedback) gets a curve over the phrase: a value per sixteenth from a
   shape (rise, fall, rise-and-resolve, hold, step at 8) drawn per section. At note-on the curve's value is read and
   quantised (say to 16 steps) and becomes part of the cache key. Cheap, fits the current threading, and gives
   movement across bars; within a note the movement is still fixed.
2. **A continuous voice per part.** Render the tune lane through a stateful chain (oscillators, the existing
   `mangle.Filter`, drive, delay) block by block, with LFOs locked to the step clock and the phrase curve feeding the
   controls. This is what every recipe in section 6 assumes. `mangle.Filter` is a per-sample Python loop; it would need
   vectorising or a compiled path to run per part in real time [unsourced engineering note].

Either way: LFOs and envelopes use bar-relative rates; one slow curve per part per section; the curve lands on the
phrase line; and at most one part's curve is "past the lip" at a time [LR].

*Check (on the plan, without sound):* for the tune lane, the spectral centroid (or simply the cutoff value) over 16
bars should span a planned range and return near its start at 16 or 32; no two consecutive hook notes should be
bit-identical; the modulation phase should be identical at every bar line within a section.

### 7.3 Make samples take the hook role (well supported)

Implement [L03] R0 to R10 for the film material: roles, a budget, bar masks, step weights, lengths by class, a template
held per section, recurrence at 4 and 8 bars, the tease-to-return stages, transformations, register. Add from this
report: the hook sample is chosen once per section and kept; its **development is by treatment** (filter, window
position, reverse, throw, stutter) on the slow clock; replacement happens only at section edges.

### 7.4 Limit randomness (supported; numbers are inference)

**Fix per section** (seeded, drawn once): the instrument and its patch; the hook sample and its slice set; the motif
(rhythm cell plus a pitch skeleton of 2 to 4 notes from the bass's pitch set [L05]); each lane's step template; the
shape of each slow modulation curve; the list of 2 to 4 composed answers and endings.

**Vary inside the section:** which bars sound (mask, within the 03 budget); decorations (ghosts, pickups) at low odds;
the position along the modulation curves (deterministic, by bar number); which composed answer is used, on a fixed A:B
schedule (for example answer A in bars 4 and 12, B in bar 8, a fill in bar 16), not a per-bar draw.

**Change on the clocks in 3.4:** answer at 2 and 4 bars; turnaround and one macro move at 8; a new modulation
destination or a second layer at 16; B material at about 32; A back, changed, at 64. One layer turning over at a time.

For the current code specifically: `hook_shape` should be drawn once per section, not per eight bars; the "cousins"
should be derived from the main shape (ending changed, one note moved, a fragment), not drawn from a new seed [L05
§11][L00 §5].

### 7.5 Which instruments to build first (inference, ranked by fit and cost)

1. **The film-sound stab instrument (6.5)** with the sampled-chord riff mode (6.4). It uses the program's own
   material, answers the owner's preference, and needs only pitch tracking, an envelope, a filter and a moving window.
2. **Acid line (6.1).** Precise sources, maximum movement for few notes, needs only one oscillator, a resonant filter,
   two envelopes, accent memory and glide. Good test of the phrase-clock machinery.
3. **Reese (6.3).** The jungle-native moving bass; gives the "second bass identity" [L05] a sound of its own.
4. **Hoover (6.2).** For rave and darkside scenes; mostly oscillators, PWM, chorus and a pitch envelope.
5. **Dub chord (6.6).** Cheap if a feedback delay with filtered repeats exists; good for breakdowns.
6. Later: Juno pad bed (6.7), one-note resonant pulse (6.11), two-timbre bells (6.12), wobble (6.9), neuro (6.10),
   organ (6.8), formant voice pad (6.13).

### 7.6 What is well supported and what is inference

- **Well supported:** that classic hooks in this music are few-noted and carried by sound or sample (1.1, 2.1); the
  synthesis facts for the 303, Reese, rave stab, neuro bass, dub chord, Juno chorus and techno pad (sections 5 and 6
  where marked with a number); Garcia's and Butler's accounts of repetition; the drop and build techniques; the swing
  definition; the present code's behaviour (read from the source).
- **Supported in principle, numbers mine:** the two-clock model of movement; the fix/vary/clock table; the A:B
  schedules; the build order.
- **Inference only:** detune set in hertz to the tempo; the film-sound instrument and formant pad recipes; the
  quantised-curve cache key; every starting value in section 6 not carrying a source number.

---

## 8. What could not be found

- The Alpha Juno "WhatThe" patch parameters, the original mentasm settings, and the direction and depth of its pitch
  envelope; forum threads that might hold them were blocked or empty [2][3][4].
- How the T99 and other Belgian stabs were made beyond "layered sounds on an S950" [24, snippet, forum].
- Patch-level descriptions of named jungle pads and stabs (Goldie, LTJ Bukem, 4hero); the samplers article was blocked
  [46, snippet].
- Automation curves in bars for any named jungle tune.
- Any listening study measuring how much timbral movement keeps a repeated part from sounding static.
- The full text of Snoman's manual (cited from a search summary [34]); the full GEDMAS paper (abstract only [35]).
- Sound On Sound's Synth Secrets on the 303 and on chorus (not reached), and the Sound On Sound studio profile of FNZ
  (summary only [43]).

How well this is sourced: the synthesis recipes rest on Attack Magazine walkthroughs, Robin Whittle's 303
documentation and a published Juno-60 analysis, read directly; the account of repetition rests on two music-theory
works (Garcia read directly; Butler through a published review); generative-tool behaviour on manufacturer and
vendor documentation; several items (303 stock timings, filter poles, wobble rates, M1 recipes, Hood and Mills
interviews) are search summaries and are marked. The recommendations are my synthesis of these with the earlier
reports.

---

## Sources

Project files (under `docs/research/`)

- [L00] `00_what_mindstream_does_now.md`
- [L03] `03_sample_placement.md`
- [L04] `04_legibility_beyond_repetition.md`
- [L05] `05_bass_sub_tune_progression.md`
- [LR] `README.md`
- Code read: `mindstream/groove.py` (`_tone`, `_make`, `_note`, `_finish`, `_trigger`), `mindstream/deal.py`
  (`hook_shape`, `hooks`, `hook_note`), `mindstream/mangle.py` (`Filter`).

Sound design and named sounds

1. Attack Magazine, Reese Bass Redux (pages 1-3) - https://www.attackmagazine.com/technique/tutorials/reese-bass-redux/
2. Wikipedia, Hoover sound - https://en.wikipedia.org/wiki/Hoover_sound
3. Wikipedia, Roland Alpha Juno - https://en.wikipedia.org/wiki/Roland_Alpha_Juno
4. Attack Magazine, Liquid Hoover Bass - https://www.attackmagazine.com/technique/synth-secrets/liquid-hoover-bass/
5. Attack Magazine, Make Rave Stabs Like The Landlord Stab - https://www.attackmagazine.com/technique/synth-secrets/make-rave-stabs-like-the-landlord-stab/
6. Attack Magazine, Twisted Neuro Bass - https://www.attackmagazine.com/technique/synth-secrets/twisted-neuro-bass/
7. Attack Magazine, Acid Synths in U-he Diva - http://www.attackmagazine.com/technique/synth-secrets/acid-synth-uhe-diva/
8. Attack Magazine, Tearing Acid Techno Bassline With SynthMaster 2 - https://www.attackmagazine.com/technique/tutorials/tearing-acid-techno-bassline-with-synthmaster2/
9. Robin Whittle, Devil Fish manual (stock 303 slide and accent timings) [snippet] - https://www.firstpr.com.au/rwi/dfish/Devil-Fish-Manual.pdf
10. Robin Whittle, What makes the TB-303 unique - https://www.firstpr.com.au/rwi/dfish/303-unique.html
11. Sequence15, How many poles does the TB-303 filter have? (reporting Tim Stinchcombe's analysis) [snippet] - http://sequence15.blogspot.com/2009/02/how-many-poles-does-tb-303-filter-have.html
12. Wikipedia, Acid Tracks; Insomniac, From the Crate: Phuture Acid Tracks [snippet] - https://en.wikipedia.org/wiki/Acid_Tracks ; https://www.insomniac.com/music/from-the-crate-phuture-acid-tracks/
13. Attack Magazine, Deconstructed: Daft Punk, Da Funk - https://www.attackmagazine.com/technique/deconstructed/daft-punk-da-funk/
14. Attack Magazine, Deconstructed: Joey Beltram, Energy Flash - https://www.attackmagazine.com/technique/deconstructed/joey-beltram-energy-flash/
15. Attack Magazine, Deconstructed: Jeff Mills, The Bells - https://www.attackmagazine.com/technique/deconstructed/jeff-mills-the-bells/
16. Attack Magazine, Dub Techno Synth Chords - https://www.attackmagazine.com/technique/synth-secrets/dub-techno-synth-chords/
17. Dub techno chord tutorials: Attack Magazine Basic Channel-Style Dub Techno; Polarity; House of Loop [snippet] - https://www.attackmagazine.com/technique/beat-dissected/basic-channel-style-dub-techno/ ; https://polarity.me/bitwig-classic-sounddesign/012-dub-chord/ ; https://houseofloop.com/how-to-create-the-iconic-dub-techno-chord-sound/
18. Attack Magazine, The Theory Of Techno Pads (Part 1) - https://www.attackmagazine.com/technique/tutorials/the-theory-of-techno-pads-part-1/
19. Gijs Verheijke, The legendary Korg M1 "Organ 2" preset - https://gijs.substack.com/p/the-legendary-korg-m1-organ-2-preset
20. Wikipedia, Show Me Love (Robin S. song); Syntorial preset recipe [snippet] - https://en.wikipedia.org/wiki/Show_Me_Love_(Robin_S._song) ; https://www.syntorial.com/preset-recipe/robin-s-show-me-love-bass/
21. MusicRadar, How to create a layered rave stab using Korg's M1; 9 tips and production tricks for rave revivalists [snippet] - https://www.musicradar.com/tuition/tech/how-to-create-a-layered-rave-stab-using-korgs-m1-636595 ; https://www.musicradar.com/tuition/tech/9-tips-and-production-tricks-for-rave-revivalists-636301
22. pendragon-andyh, Juno60 chorus analysis (README) - https://github.com/pendragon-andyh/Juno60/blob/master/Chorus/README.md
23. Synthmania, Juno-106; Equipboard Juno-106 guide [snippet] - https://www.synthmania.com/juno-106.htm ; https://equipboard.com/posts/roland-juno-106-guide
24. Dogs On Acid forum thread on T99 "Anasthasia" [snippet, forum] - https://www.dogsonacid.com/threads/anyone-know-the-synth-they-use-in-1990s-techno-song-anasthasia-by-t-99.793482/
25. MusicRadar, How to build an LFO wobble bass; Monosounds, Wobble Bass in Serum 2 [snippet, weak] - https://www.musicradar.com/how-to/lfo-wobble-bass ; https://monosounds.studio/wobble-bass-serum-2/
26. Wikipedia, Neurofunk; Bass Gorilla, What is Neurofunk [snippet, weak] - https://en.wikipedia.org/wiki/Neurofunk ; https://bassgorilla.com/what-is-neurofunk/

Repetition, form, groove

27. Luis-Manuel Garcia, On and On: Repetition as Process and Pleasure in Electronic Dance Music, Music Theory Online 11.4 (2005) - https://www.mtosmt.org/issues/mto.05.11.4/mto.05.11.4.garcia.html
28. Wayne Marshall, review of Mark J. Butler, Unlocking the Groove (2006), Music Theory Spectrum 31 (2009) - https://wayneandwax.com/academic/mts-butler-unlocking-groove.pdf
29. Jeremy W. Smith, The Functions of Continuous Processes in Contemporary Electronic Dance Music, Music Theory Online 27.2 (2021) - https://mtosmt.org/issues/mto.21.27.2/mto.21.27.2.smith.html
30. Ragnhild Torvanger Solberg, "Waiting for the Bass to Drop", Dancecult 6.1 (2014), abstract - https://dj.dancecult.net/index.php/dancecult/article/view/451
31. Katarzyna Glancey, Felt Emotions Evoked at Key Structural Moments in Drum and Bass Music, DURMS 3 (2020) - https://musicscience.net/wp-content/uploads/2020/10/glancey.pdf
32. Witek et al., Syncopation, Body-Movement and Pleasure in Groove Music, PLOS ONE (2014) [snippet] - https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0094446
33. Attack Magazine, Roger Linn On Swing, Groove & The Magic Of The MPC's Timing [snippet] - https://www.attackmagazine.com/features/interview/roger-linn-swing-groove-magic-mpc-timing/
34. Rick Snoman, Dance Music Manual (Routledge), passages on melody, timbre and repetition [snippet] - https://books.google.com/books/about/Dance_Music_Manual.html?id=jvODDwAAQBAJ

Generative and performance tools

35. Anderson, Eigenfeldt and Pasquier, The Generative Electronic Dance Music Algorithmic System (GEDMAS), AIIDE 2013, abstract - https://ojs.aaai.org/index.php/AIIDE/article/view/12649
36. Arne Eigenfeldt, Generating Electronica: A Virtual Producer and Virtual DJ (2013) - http://www.sfu.ca/~eigenfel/Eigenfeldt-CC%202013.pdf
37. Mutable Instruments, Grids manual - https://pichenettes.github.io/mutable-instruments-documentation/modules/grids/manual/
38. Elektron trig conditions: CDM, New Elektron Octatrack OS; Octatrack MKII manual p. 76 [snippet] - https://cdm.link/new-elektron-octatrack-os-trig-conditions-awesome/ ; https://www.manualslib.com/manual/1309767/Elektron-Octatrack-Mkii.html?page=76
39. Ableton, Take a Chance: Producing with Probability in Live 11 - https://www.ableton.com/en/blog/take-chance-producing-probability-live-11/
40. Godfried Toussaint, The Euclidean Algorithm Generates Traditional Musical Rhythms (2005) [snippet] - https://cgm.cs.mcgill.ca/~godfried/publications/banff.pdf

Sampling

41. Attack Magazine, Vocal Chopping & Pitching (pages 1-2) - https://www.attackmagazine.com/technique/tutorials/vocal-chopping-and-pitching/
42. Native Instruments blog, 5 handy sampling tricks and techniques (Erdbeerschnitzel, "one track, one sample") - https://blog.native-instruments.com/top-5-sampling-tricks-and-techniques/
43. Sound On Sound, Inside Track: FNZ, page 2 [snippet] - https://www.soundonsound.com/techniques/inside-track-fnz?page=2

Producers and scenes

44. Robert Hood: Red Bull Music Academy interview; DJ Mag on Minimal Nation [snippet] - https://daily.redbullmusicacademy.com/2014/03/robert-hood-interview/ ; https://djmag.com/features/how-robert-hoods-minimal-nation-became-defining-work-minimal-techno
45. Jeff Mills: MusicRadar interview; DJ Mag on Waveform Transmission Vol. 1 [snippet; consulted, little used] - https://www.musicradar.com/news/jeff-mills-interview ; https://djmag.com/features/how-jeff-mills-waveform-vol-1-started-new-era-techno
46. Reverb, The Samplers and Breakbeats Behind '90s Jungle/Drum & Bass [snippet; page blocked] - https://reverb.com/news/the-samplers-behind-90s-jungle-and-drum-and-bass
47. Generic advice on amateur-sounding tracks: Whipped Cream Sounds, Top 10 Signs Your Electronic Music is Amateur; Supreme Tracks, 7 Amateur Music Production Mistakes [snippet, weak] - https://www.whippedcreamsounds.com/top-10-signs-your-electronic-music-is-amateur/ ; https://www.supremetracks.com/7-amateur-music-production-mistakes/
