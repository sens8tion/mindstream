# 05. Basslines, sub and tunes that feel written, driving and developing

Written 2026-10-02. Secondary research: the owner's own measurements first, then the web. The question came from the owner's verdict on the present output: "The tunes / basslines / sub don't really feel progressive or on point for me."

How to read the marks:

- **[R-…]** a file in the owner's reference measurements or earlier research (listed in section 2). Those files carry their own methods and citations; I have not re-run them.
- **[n]** a numbered source in the list at the end. Unmarked means I read the page.
- **[snippet]** the claim rests on a search-result summary, not on the page (the site refused the fetch, or the page came back cut short). Treat as a lead.
- **[computed]** my own arithmetic from numbers given in this file or in `deal.py`.
- **[unsourced]** my belief or inference; nothing I found supports it directly.

Three cautions about the evidence. Pages were read in a reduced text form, so I paraphrase throughout and quote almost nothing; any wording that matters should be checked against the page. Tutorials on this subject are mostly about sound, not notes, and several of the pages that do give note-level rules are small teaching sites of unknown authorship. And the search allowance for the session ran out partway through, so several places the brief named were never reached (listed in section 13). Step numbers are sixteenths of a bar counted from 0, as in `deal.py`: 0 is beat 1, 4 is beat 2 (snare), 6 is "2-and", 8 is beat 3, 10 is "3-and", 12 is beat 4 (snare). Scale degrees are written 1, b2, b3, 4, b5, 5, b6, b7, 7.

---

## 1. One-page summary

The present lines have the right statistics and no intent because the things that make a line sound written are not statistics of single notes. They are **relations**: between one bar and the next, between the line and the drums, between a note and the note it is heading for, and between this phrase and the last one. Every source that says anything concrete says some version of this, and the owner's own measurements show the same relations in the reference set once you look past the per-note averages.

The strongest findings:

1. **A bassline is a rhythm before it is a tune.** Producers and teachers repeatedly advise writing the line on one note first and adding pitch afterwards, and using about three pitches with at most one more for colour [15][17][26][60, snippet]. Jump-up hooks are described as one to three notes [23]; Reynolds praised a mid-90s line of barely more than one note that still lodged in the memory [62]. The reference set agrees: 35% of bass moves are repeats and 28% are steps [R-bass §3]. So identity lives in **where the notes fall and how long they last**, and that pattern has to be held from bar to bar. The present code draws a fresh rhythm for every bar.
2. **It is anchored, then decorated.** The root sits on beat 1 [16][18][83, snippet], and in the reference a second anchor sits on 2-and; short notes are spent in pairs around those anchors and as pushes into a beat [R-bass §13]. Anchors stay; decorations are re-dealt.
3. **It is built as statement and answer.** The plainest recipe found: bar 1 states a solid idea on the root; bar 2 is the same idea altered by removing a note, shifting one, changing the octave or changing the ending [18]. Other sources give the same shape at half-bar, two-bar and four-bar sizes [24][23][4]. The reference shows it: in two-bar riffs the second bar sits about a semitone lower in two cycles out of three [R-align]. At eight bars this is the "sentence" of classical theory: idea, idea again, then fragments driving to a close, in proportions 2 + 2 + 4 [73].
4. **Its last bar is different, and in this music the difference is usually a subtraction.** Tutorials describe a flourish, fill or lift at the end of a phrase [1][5][43]. The reference thins instead: the fourth bar of a four-bar riff has the fewest notes of any, and about four riffs in ten end on one low note and a gap [R-bass §13.3][R-rules]. Either way the phrase end is marked. The present code marks it only by the 40% low-note ending.
5. **It leaves room on purpose.** Gaps are named as being as important as notes [12, snippet][24][18]. Concretely: stop a note at the kick rather than running over it [16]; keep the sixteenth after the snare clear [18] (the reference agrees: after the first snare that slot is among the emptiest in the bar [R-bass §13.2]); thin the bass when the break fills and let it speak when the drums settle [18]. How the bass treats the kick depends on the drums: under a break kick the reference bass doubles the kick, under a programmed two-step it steps a sixteenth aside [R-bass §13.7].
6. **Tension notes have a job.** The dark colour in drum & bass is put down to the flat second and the raised seventh [14], the flat second being the Phrygian note [15][80][9]. A modern roller tutorial builds its whole line from the root bent up to b2 and b3 [2]. What makes such a note sound meant rather than wrong is the walking-bass rule: a note a semitone from a target, placed just before the target, on a weak position [82, snippet]. A random walk on scale steps, as now, never produces this.
7. **Development is by substitution on a schedule, not by rising.** The owner's layer clocks (riff about 8 bars, sub tone about 17, kick about 28, carrier about 32, slow layers changing where the riff changes) [R-align] match what producers say: an 8-bar loop kept interesting [57], something changed every 8 and something bigger at 16 or 32 [R-forums A5], a 64-bar drop split into two 32s with the second half a different or stripped or thicker bass pattern [19], and a second drop that is related but harder [19][22][23]. Named classics carry **two bass identities** and switch between them: a sub line and a second, more tuneful line ("Terrorist" [49, snippet], "Burial" [47], "The Nine" [42]). The level does not climb: Reynolds's phrase for hardstep is "no crescendos or lulls" [63].
8. **A roller and a switch-up are two ends of one dial.** A roller holds its core and does not need a dramatic change every 16 bars [31]; its bass is long single notes [31] and its drums change briefly at the end of each 16 or 32 [32]. The other end switches every couple of bars [39, snippet] and swaps basslines every 4 [60, snippet]. Tim Reaper's own description is that jungle is not obliged to do any particular thing within 32 bars [34]. A generator needs the dial, not one setting.
9. **Hooks are short, few-noted, off the drum hits and off the bass's notes.** Stabs are written to avoid the main drum hits and to leave the root to the bass; long and short hits answer each other [8]. A lead fits in the small gaps between bass notes [4][5]. The reference: hooks in about 3 bars of 8, under two beats long, on four or five pitches (5, b3, 1, 4), clustered in bars 4, 5 and 8 of an eight-bar phrase, over a bar where the low end is less busy [R-hooks]. The reference shows **no** hook-calls-and-sub-answers timing [R-align]; the relation is a shared pitch set and a shared space, not a dialogue.
10. **Research on generated music says the same thing in its own words.** Note-to-note chance models stay in key and go nowhere [85][86][88]; what repairs them is structure imposed from above: a plan of which bars repeat which, fixed target notes at given positions, a tension curve, and inputs that let each bar see the bar one and two back [85][86][87, snippet][88].

What I could not find is in section 13. The largest hole: **no source gave a note-level analysis of any of the named classic basslines**. Everything said about those records below is about structure, layers and order of events.

---

## 2. What the owner's measurements already establish

Files read (in the sibling thelmic repository, beside this one):

| mark | file | what it is |
|---|---|---|
| R-readme | `tracks/2026-09-16_reaper/README.md` | summary of seven measurements of a 21-minute reference jungle set |
| R-bass | `tracks/2026-09-16_reaper/bass.md` | the low end: note lengths, intervals, riff periods and runs, short-note placement, placement against the kick |
| R-hooks | `tracks/2026-09-16_reaper/hooks.md` | melodic events: how often, how long, register, pitch set, call-and-response tests |
| R-align | `tracks/2026-09-16_reaper/alignment.md` | whether layers change together; call and response inside the bassline |
| R-drops | `tracks/2026-09-16_reaper/drops.md` | every drop and breakdown |
| R-structure | `tracks/2026-09-16_reaper/structure.md` | sections, repetition, loudness arc |
| R-arch, R-press, R-forums | `archetypes.md`, `archetypes_press.md`, `archetypes_forums.md` | what the press and forums say, set against the measurements |
| R-rules | `tracks/2026-09-16_jungle_scene_rules.md` | the working rules drawn from the above |
| R-0915 | `tracks/2026-09-15_jungle_research.md` | earlier web research (sections 3 and 4 on bass and harmony) |

`docs/tension-vocabulary.md` and `docs/mode-topology.md` are placeholders with open questions and no content yet, so they contribute nothing here.

The per-note numbers that `deal.py` already uses (a note about once a beat, median 0.6 beats, about 0.9 pitch changes a bar, 35% repeats, 28% steps, 7% fifths, riffs of 4 or 8 bars) are not repeated. What follows are the measured **relations** that the present code does not use. Each is a rule waiting to be written.

**Inside the bar**

- Sub onsets are front-loaded: 57% in the first half of the bar, peaking on beat 1 and 2-and. High accents are back-loaded: 58% in the second half, peaking on 3-and and 4 [R-hooks, call and response §2].
- The commonest onset pairs in a bar are 1 + 4 (18%), 1 + 2 (18%), **1 + 2-and (16%)**, 2-and + 4 (16%) [R-bass §13.5]. Beat 1 and 2-and are the skeleton; bare, that skeleton is rare (0.3% of bars), so it is always decorated.
- Short notes (under half a beat) live on the eighth grid (67% on beats and "ands"), with the "and" as heavy as the beat. Best slots: step 2, 12, 0, 10, 4. The off-eighth slots are used for **pushes into the next beat**, above all step 11 into step 12 [R-bass §13.2].
- Short notes come in company: 82% have another onset within an eighth. The signature figure is short on a beat, short on its "and", held note on the next beat. A short note is followed by a repeat or a step 68% of the time. **Leaps happen off long notes**: 40% of moves out of a long note are three semitones or more [R-bass §13.4].
- The sixteenth after the first snare is close to empty for every length class (step 5: about 2 to 3%; uniform would be 6.25%). The one after the second snare (step 13) is thin for short and long notes (about 3%) but not for medium ones (6.8%) [R-bass §13.2].
- Small moves are slid and big moves are struck: glided transitions have a median of 1 semitone, struck ones 2, and 43% of struck ones are 3 or more [R-bass §3].

**Against the drums**

- Under a break kick, short bass notes land on the kick more than chance (36% found, about 45% corrected, against 23%). Under a programmed two-step, short notes sit a sixteenth after the kick and long notes start on step 2 and on the beat-4 snare, off the kick. With no kick the bass plays in the gaps [R-bass §13.7].
- Busy and deep are alternatives. Sections that change pitch 1.6 times a bar keep 34 to 85% of the low end below 60 Hz; sections that change 0.25 to 0.4 times a bar keep 73 to 96% [R-bass §4].

**Across bars**

- In a four-bar riff the notes thin toward the end: bar 1 holds 29% of the short notes and 30% of the long ones, bar 4 holds 19% and 18%. The top single position is a long note on beat 1 of bar 1 [R-bass §13.3].
- In two-bar riffs the second bar is about a semitone lower than the first in 66% of cycles; back-half notes run a little longer. At one bar and at eight bars the back half is higher instead [R-align].
- The bass is present in 77% of bars, in stretches of a median **3 bars on and 1 bar off** [R-bass §5].
- 615 different one-bar figures in 758 bars: the figure is never the same twice, while the riff still agrees with itself at 2, 4 or 8 bars [R-bass §11, §13.5].

**Across phrases**

- A riff runs a median of 11 bars (7 to 15) before it changes; changes fall on 8-bar lines 1.7 times chance and on 16- and 32-bar lines about twice chance [R-bass §11.2, §12.2].
- What follows the end of a run: a new riff 39%, **the same riff again after a fill or dropout 36%**, a partial rewrite 21%, a transposition 3%. "Same rhythm with new notes" and "same notes with new rhythm" are both about absent (0 and 1 of 67) [R-bass §11.2].
- Layers keep separate clocks (riff 8, sub tone 17, kick 28, carrier 32 bars) and the slow ones change where the riff changes: 77% of kick-pattern changes land on a riff change. Three or four layers turning over together marks a real section [R-align].
- Where the bass sits relative to the highs is a state held for a whole sub-section and changed at its edge, most clearly at riff changes [R-hooks, call and response §6].
- The first bar after a drop is often a gap or one held note; the line proper starts in bar 2 (sub +2.1 dB from bar 1 to bar 2). Bar 8 is where the low end starts leaving again [R-drops §4].

**Hooks**

- 39% of bars, median 1.2 beats, 81% under two beats; a shape returns about three times at 4 to 8 bar spacing and is then replaced; only 39% of shapes ever recur [R-hooks §2 to §4].
- Within a section 77% of hook weight sits on four pitch classes; across the set those are 5, b3, 1 and 4. Hook and bass share a pitch set (agreement 0.50) [R-hooks §6].
- Hook onsets drift late in the eight-bar phrase: busiest in bars 4, 5 and 8 [R-hooks, call and response §2].
- Hooks are not placed by sub level (r about 0). What changes under a hook is low-end activity: 2.1 dB less low-band flux, that is, fewer kick and bass onsets [R-hooks §7].
- Tested and **not** found: a high call at the front answered by the sub at the back, at 1, 2, 4 or 8 bars; a back-of-bar accent answered by the sub on the next downbeat; any pitch relation between a hook and the sub note after it beyond sharing the key. The one vertical relation: a hook over a held sub note lands two octaves and a major third above it 18% of the time against 5% by chance [R-hooks, call and response §5].

**What the measurements cannot say.** They describe what the lines do, not why a given note is there. The relations above are consistent with intent (anchors, answers, endings), and the reading below supplies candidate reasons, but the reference is one DJ's 21 minutes of nine unidentified records.

---

## 3. How jungle and drum & bass basslines are written (brief item 1)

### 3.1 The inheritance: a slow line under fast drums

- The standard account: breaks at 150 BPM and up, a bassline at about half that, 75 to 80; dancers move to the slow line while the breaks become texture [65][61]. Producers lifted or imitated slow, low lines from roots reggae [65]. Christodoulou puts it as dub basslines at about 85 BPM joined to breaks at about 170 [67].
- A teaching page states the practical version: write the bass on the slow grid, as long sliding notes that answer the kick and do not double it; a line written on the fast grid fights the break; a dancer can ride either layer [27].
- In reggae the riddim is the drum pattern plus the bassline, reused across many songs, and the weight is on low-frequency rhythm, not melody [72]. A roots bassline outlines the chord in time, lands on the strong beats with a note or two on the syncopated places around them, and in its dub form repeats notes, especially the fifth below the root; it is meant to be melodic and mesmerising and still minimal [71].
- Forum memory of 90s practice: reggae and rocksteady shapes, mostly roots and fifths, pentatonic, rhythm first, worked out by trial and error [60, snippet][R-forums B7].
- At least one anthem's bassline is literally a replayed reggae riddim ("Original Nuttah") [53, snippet].
- **The owner's measurement qualifies all of this** [R-press B1, B2]: the half-time is real in the *rate* (a note a beat apart, a pitch change a bar) but the notes are short (median 0.6 beats), nothing is held past 1.4 bars, and the intervals are repeats and steps far more than roots and fifths. So the dub inheritance in a 2026 revival set is the slow harmonic rhythm, the root weight and the gaps, not long notes and not fifth-leaping.

### 3.2 The sounds, and what each implies for the notes

| sound | origin and character | what it does to the writing |
|---|---|---|
| Sine or 808 sub | sampled 808 kicks and sampler test tones played from a keyboard [3][29]; "clean sine" is what the reference uses [R-bass §7] | carries weight, not tune; keep it harmonically simple so another layer can carry character [18]; sweet range roughly D#1 to G#1 [20] or E to G [21] |
| 808 with pitch movement | glide between notes; a slide placed just before the turnaround raises tension [3]; slides are called a staple of jungle bass [snippet] | 30 to 90 ms portamento, used sparingly: on octave drops and on tension notes before a snare [18]. Reference: 41% of moves slide, median 96 ms, small intervals [R-bass §1] |
| Reese | two slightly detuned saws, from a 1988 Detroit record; put over the Amen in "Terrorist" (1994); 7 tracks used it in 1994, 54 in 1995; distorted through a guitar pedal for techstep [50]. Sampled and replayed across a keyboard [68] | sustains and moves in timbre, so it wants **long notes and few of them**; the interest is the beating, not the pitch [51] |
| Modulated mid bass ("wobble", neuro) | a filter or pitch wobbled by a slow oscillator; a roller tutorial automates the wobble rate from 0.1 to 0.4 Hz up to 4.5 Hz mid-phrase and settles it at 2 Hz [2] | **the modulation rate is part of the rhythm**; development is done by changing rate and filter, not notes [22]. Reynolds, 1997: single heavy riffs gave way to several intricate, glossy basslines over a plain two-step [64] |
| Reversed bass | a sampled acid line reversed (1994) [29]; "Super Sharp Shooter" drops on a reversed bass [41] | the swell *into* the beat is the hook: the note ends on the anchor instead of starting there [unsourced reading] |
| Stab bass, hoover | hoover: layered low-pass and sweeping band-stop filters [11]; Bad Company built a tune on a distorted hoover riff plus a distinct bassline [44] | short, pitched, mid-register; behaves as a hook that happens to be low (section 7) |
| Sub plus mid as two jobs | sub: sine or low-passed square, mono, cut above 100 to 120 Hz; mid: carries the tone that small speakers hear [28][22][25] | the two can play different rhythms. In "The Nine" the sub looms and a metallic upper layer's occasional turns into melody are the tune's only hook [42] |

### 3.3 Rhythm of the line against kick and snare

What sources say, most concrete first:

1. **Root on beat 1, a second note on the off-beat before the snare.** A one-bar jungle sub pattern is described as landing on the first beat and on the offbeat before the snare, with a slid note before the snare for dialogue with the break [18, and snippet of the same site]. In step terms: 0, and 2 or 10, with a slide into 4 or 12 [my mapping].
2. **Notes around drum events.** Before beat 3, after snare gaps, on eighth-note offbeats; pickups just before main beats [18].
3. **Three ways to "follow the kick"**: on every kick; in the gaps between kicks, which makes the bass more of a lead; or both [10]. A drum & bass example removes the note on beat 4 to leave space, keeping notes on beats 2 and 3 [10, snippet].
4. **Lock beat 1, then avoid the kick elsewhere**: move a bass note that lands on a kick earlier or later; stop a note at the kick instead of holding over it; or move the clashing note up an octave [16]. A forum summary says the same: put bass notes where the kick is not [snippet].
5. **Leave silence after the snare** so it cuts; do not hold a bass note through it [18].
6. **Answer the break**: when the break fills, simplify or drop the sub; a snare roll gets silence; the bass answer is one long note or a slide [18].
7. **Nudge the drums to the bass**: move drum hits so a kick or snare lands on most bass notes [21].
8. **Note length is groove**: an eighth of a bar for bounce and snare room, a quarter of a bar for weight, half a bar or more for pressure; most notes between an eighth and a half of a bar [18]. (That is 2, 4 and 8 sixteenths [computed].)
9. **A rest at the end of the bar** lets other hits speak [24]; a small rhythmic flourish at the end of each bar is the other common choice [1].

Against the measurement: items 1, 2, 5, 6 and 8 agree with [R-bass §13]. Items 3, 4 and 7 contradict each other and the reference resolves it by drum type: **double a break's kicks, sidestep a programmed two-step's** [R-bass §13.7]. Item 5 is the best-supported gap rule of all: tutorial and measurement agree that the sixteenth after the snare stays empty, most clearly after the first snare.

---

## 4. What makes a bassline a hook (brief item 2)

### 4.1 Devices, with sources

- **Rhythm first, then pitch.** Write the rhythm on the root with rests, then move some notes [15]; map the kick pattern onto the root, then add a motif [17]; a simple sound with a strong rhythm beats an elaborate sound [26]; write on one note at full velocity to force the rhythm [60, snippet].
- **Few pitches.** Three notes, one more now and then for colour; do not underestimate one note [60, snippet]. One to three notes with rhythmic movement [23]. A three-note cell 1, b3, b7 as the repeated motif [17]. The 303 riff of a famous French house record uses root, b3, 4, b6 and b7 and leaves out the fifth and the second on purpose [4]. An ostinato of two notes with no third fits over several chords [7].
- **Keep several roots for anchoring; span an octave for shape; vary note values** [15].
- **A memorable interval.** Earworm tunes have a common overall contour and an unusual interval pattern, such as an unexpected leap or more repeated notes than usual, and are faster than average [77, snippet]. Zinc's basslines were never the heaviest; they were the ones people hummed afterwards [40].
- **Repetition with a twist.** The pattern stays the same except for one strategic change, such as one note moved by a sixteenth in the third bar [4]. Repeat the rhythm and change which chord tone is played [24]. Bar 2 offsets the timing and reverses the motif [17].
- **The answering phrase.** Call in the first half of the bar and response in the second [24]; two bass notes or two bass sounds in dialogue [23][snippet]; bar 1 states and bar 2 alters [18]; change every second four-bar pattern [19, snippet].
- **Octave moves.** An octave thrown into the space between kicks adds movement without adding a pitch [4]; common leap shapes are 1-5-8 and 1-b7-8 [6]; trap-style 808 lines slide across octaves and fifths for bursts of energy [14].
- **Tension notes.** The flat second and the raised seventh are named as the notes that give drum & bass its dark colour [14]. The flat second is what makes Phrygian dark [15][80]; in a house record analysed bar by bar, the bass's flat second also avoids a clash with the chord above it [9]. A roller tutorial's line is the root with bends up to b2 and then to b3 [2]. The blues scale (with b5) is recommended for bass drops [17] and disco [14]. A teaching page for jungle sub gives, in F minor, F, C, Eb, G and Ab [18]; by the note names those are 1, 5, b7, 2 and b3 [computed], with the 2 as a passing note.
- **Approach notes.** In walking bass a target note sits on a strong beat and is approached from a semitone above or below, or by a scale step, on the beat before [82, snippet]. This is the only clear statement found of *why* an out-of-scale bass note sounds deliberate.
- **Ghost notes and dead notes.** Very short, quiet notes before and after a held note or a fill give a percussive push [4][6].
- **The turnaround.** A flourish at the end of each bar [1]; two to four rhythmically distinct notes leading into a change [5]; glide switched on to slur into the turnaround [3]; in "The Nine", a lift at the end of every sixteen bars where the bassline rises over stuttering drums [43].
- **Changing length as a theme.** Long notes in bars 1 to 4, short plucked notes in 5 and 6, the longest in 7 and 8 [6].

### 4.2 Well-known lines: what sources say (structure only)

No source gave notes. What was found:

| record | what sources describe | source |
|---|---|---|
| Leviticus, "Burial" (1994) | two bass identities: a dubwise sub and a snaking jazz-funk bassline, the second played off the same rare-groove record the vocal "ooh" came from; one of its makers says the record more or less wrote itself | [47][46][48, snippet] |
| Shy FX and UK Apachi, "Original Nuttah" (1994) | the bassline is a replayed reggae riddim; film-sample intro and horns before the beat; full vocal over it | [53, snippet][52] |
| Renegade (Ray Keith), "Terrorist" (1994) | piano intro, a seething Reese sub, then a *second*, digital-dub bassline; described as hook after hook | [49, snippet][50] |
| Origin Unknown, "Valley of the Shadows" (1993) | a menacing dub-influenced bassline under a voice describing a dark tunnel; a countdown sample before the rolling bass drops; made in four hours | [67][54][snippet] |
| DJ Zinc, "Super Sharp Shooter" (1995) | intro on half-speed drums with a borrowed hip-hop bassline; a vocal cue; the drop brings a different, reversed bass described as cartoonish; half-time intro became his template | [41][40] |
| Alex Reece, "Pulp Fiction" (1995) | starts with the bass; only drums and bass, no strings or pads, no big breakdown; rolling, dark, minimal; two-step beat | [45] |
| Dillinja | bass arriving not as a line but as a single blast of clustered low frequencies; recorded hot through desk and sampler gain | [62][snippet] |
| Roni Size, mid-90s | several basslines at once acting as slow-changing melody and as sustained pressure; "Brown Paper Bag": a played double bass | [62][snippet] |
| Omni Trio, "Renegade Snares" (Foul Play remixes, 1993) | pitched snares and a gradual percussive build before the vocal and 808 bassline drop, leading to the piano breakdown; the chords set the range of the bass | [56, snippet] |
| Goldie, "Inner City Life" / "Timeless" (1995) | strings given time to develop before the drums enter; sub parts wanted both subsonic and fat; three sections joined with care | [55][61] |
| Ed Rush & Optical, "Wormhole" era (1997-98) | plain two-step drums; several intricate basslines in place of one heavy riff; funk claimed and, to Reynolds, lost | [64] |
| Bad Company, "The Nine" (1998) | a sub felt more than heard plus a metallic layer whose rare melodic turns are the only hook; sixteen-bar sections each ending in a lift | [42][43] |
| Kings of the Rollers style (recent) | one eight-bar held root; movement by bends to b2 and b3; a small early "drop" in pitch; more movement added toward the end of the loop; wobble rate automated | [2] |
| Tim Reaper | starts from a sample, melody or sound that sets off a hook; prepares sounds first; says jungle need not do any set thing within 32 bars; a profile singles out the tension in his basslines without saying how it is made | [34][33][35] |
| Sully | develops ideas with the notes he puts down, not with automation; brings in a new bass halfway; pitches drum hits into phrases; says his tunes are simpler than they seem and all DJ-able | [36][37] |
| Coco Bryce | few elements, four or five layers at most, kept interesting by switching every couple of bars | [38][39, snippet] |

The pattern across the table: **the famous ones have a second bass idea**, and the tune is partly the switch between the two. Pendulum-era lines: nothing found.

---

## 5. Progression over a track (brief item 3)

### 5.1 What "progressive" can mean here

No source defined the word for this music [unsourced]. Three readings fit what the owner might mean, and each has a different remedy:

1. **Forward motion inside a phrase**: each bar leads to the next. Remedy: statement and answer, targets, a marked ending (sections 4, 9, 12).
2. **Development across phrases**: the line 32 bars in is a consequence of the line at the start. Remedy: a schedule of changes and mutation of what is already there (this section).
3. **The journey of a set**: DJ Storm describes taking the floor along calmly and then flipping [59]; Fabio puts selection and cohesion above mixing [58]. The owner's set measurement shows what that looks like: one tempo, one key family, level almost flat, the *low band's share* swinging from 2% to 26% [R-structure §6].

### 5.2 How long a line holds, and what changes when

Bar lengths at 166 BPM: 8 bars is 11.6 s, 16 is 23.1 s, 32 is 46.3 s, 64 is 92.5 s [computed].

| span | what sources say changes | what the reference does |
|---|---|---|
| every bar | nothing structural; "nothing is a loop" | decorations re-dealt, anchors kept; 615 figures in 758 bars [R-bass] |
| 2 bars | statement and altered answer [18] | second bar about a semitone lower, 66% [R-align] |
| 4 bars | change every second four-bar pattern [19, snippet]; small turnarounds at 2, 4 and 8 [R-forums A6]; some remixes swap basslines every 4 [60, snippet] | bar 4 thinnest; bass on 3 bars, off 1 [R-bass] |
| 8 bars | drum & bass as an eight-bar loop kept interesting [57]; a turnaround every 8 by filtering, a reverse crash or dropping the melody [21]; vary the bass every 8 to 16 by filter, wobble rate or pattern [22] | riff changes favour the 8-bar line; median run 11 bars [R-bass] |
| 16 bars | sections of 16; a counter-melody in the second 16 [snippet]; a roller's short break or pattern change at the end of each 16 or 32 [32]; a lift at the end of each 16 [43] | sub tone about every 17 bars; a surface change every 16 [R-align][R-structure] |
| 32 bars | a 64-bar drop is two 32s; the second half takes a different bass pattern, a stripped version, a thicker version, or a vocal [19]; "drop, then drop variation" [20] | kick and carrier about every 28 to 32, on a riff change [R-align] |
| 64 bars and on | second drop harder: a different but related bass patch, more layers, more drive [19]; an alternate wobble, a new line or a modified pattern [22]; forums are split on whether second drops are worth differing [R-forums A11] | one surprise per record: new material in the first 16 bars, then 40 to 84% verbatim return [R-structure §5] |

### 5.3 The devices of development

- **The B bassline.** A second line that is clearly different and in the same key. A forum rule for switching between two basslines says exactly that: they must be easy to tell apart and in tune with each other, and a hard cut works better than a fade [60, snippet][R-forums A13].
- **Mutation by generations.** Copy the idea, make one meaningful change, copy *that*, change one more thing; after eight generations the line is far from its ancestor but every step is traceable. The dimensions to change: sound, harmony, melody, rhythm, form [81b].
- **One-off events.** A sound or gesture that never recurs, placed mid-phrase as well as at boundaries, used sparingly [81c].
- **Staggered boundaries.** Let one layer change early and another late; let a fill peak before the bar line or hang over it [81d]. The reference does this: the riff moves alone most of the time and the slow layers join it only sometimes [R-align].
- **Register and octave.** Copy the sub's notes up an octave for a top layer [3]; drop 2 by rhythm or octave variation [18]; octave leaps as fills [4][6].
- **Timbre as development.** Filter opening, wobble-rate change, added distortion [22][2][19]. Sully's stated preference is the opposite: develop with notes, not automation [36]. Both are "development"; a generator should be able to do either and should not do both at once [unsourced].
- **Subtraction as signal.** Intro on reduced or filtered sub fragments, a build that strips notes, a breakdown that thins the sub before it returns [18]; leave out an expected note just before a big hit [18]. The reference signals 82% of its drops by removing the low end for about a bar with the break still running, and uses no risers [R-drops].
- **Key or mode shift.** A forum memory is that early jungle could switch scale between parts of a track [R-forums B12]. The reference leaves its home key only for whole sections (5 of 25) and transposes a riff 2 times in 67 [R-bass §8, §11.2]. No source found on pedal points in this music by name; the held root under a changing mid layer, as in the roller tutorial [2], is one in effect [unsourced].
- **Arc or plateau.** The classical dramatic arc (introduce, build, peak, fall, settle) fits drop-based music, and the same text notes that minimal techno and dub refuse it and make their drama from small changes in a static texture [81e]. Reynolds heard jungle's hard end as a plateau of pressure [63], and the reference set is "full" 86% of the time [R-arch]. So progress here means **turnover at constant pressure**.

### 5.4 Rollers against switch-ups

- A roller: a consistent loop of bass, drums or both; it moves through its sequences without needing dramatic change every 16 bars because the core is right [31]; the beat is not too broken and the bass is built on long single notes [31]; drums continuous with a short break at the end of every 16 or 32, percussion added gradually, few musical elements [32]. A sudden "foghorn" bass is said to break the roll [32].
- A switch-up tune changes its elements every couple of bars [39, snippet] or swaps basslines every four [60, snippet].
- Reynolds in 1995 scorned the formula at the soft end: a long teasing intro, cymbal-heavy breaks, a wordless vocal, dragged out for eight minutes; and praised compression and austerity [62].
- The reference set sits between: riffs run 11 bars, but no bar repeats [R-bass][R-arch]. That is a roller's patience at the phrase level with a switch-up's restlessness at the bar level.

---

## 6. Harmony and mode in dark dance music (brief item 4)

- **How little is needed.** One-note basslines in a minor key with the interest in the rhythm are called typical of neurofunk, while liquid leans on soulful chord progressions [20]. Harmony kept minimal, modal or static, so rhythm and timbre lead [snippet]. "Pulp Fiction" is drums and a bass [45]. A two-note ostinato without a third fits whatever the bass does beneath it [7]. In the reference, 85% of bass time is inside one seven-note collection with the root taking about a third of it [R-bass §8].
- **Menace.** Low frequency itself is heard as darkness and fear in Western music (Tagg, as cited by Christodoulou) [67]. On top of that: the flat second (Phrygian) [14][15][80][9]; the raised seventh in minor, that is, the harmonic-minor leading note [14]; the flat fifth by way of the blues scale [17]; darkcore's toolkit of sinister stabs, horror samples, pitch-shifting and reversing [70b]. Metal riff teaching describes the same notes against a low pedal: Phrygian and Locrian colours, chromatic neighbours of the root, and constant return to a low pedal note [84, snippet].
- **Melancholy and euphoria.** Reynolds on 1994's ambient jungle: harps, strings, soul-diva fragments and shimmering sample riffs over a half-speed, heartbeat bassline that makes the fast rhythm soothing; the mood turned from dark to a fragile, bittersweet optimism [61]. Earlier research here found minor sevenths and ninths named for that style [R-0915 §4]. In the reference, 11 of 17 sections read minor and 4 read major; a hook two octaves and a major third above the held sub note turns up more than chance [R-hooks §6].
- **Parallel harmony.** A sampled chord replayed at other pitches moves every voice by the same interval. That is where the rave stab's sound comes from, and why its "progressions" are really one chord shape moved about [81g]. A minor triad or minor seventh is the usual stab [13, snippet]. A stab riff is therefore a *melody of chord roots*, and can be generated as a one-voice motif [unsourced step].
- **One chord and two chords.** The riff or vamp tradition is harmonically sparse by definition, and an ostinato makes tension by staying put while something else moves [78]. A bass moving between two roots under an unchanged ostinato is given as a way to link two sections [7].
- **Not found.** Nothing usable on whole-tone or deliberately chromatic gestures in this music, nor on which movements read as euphoric beyond the above [unsourced]. From general practice: a chromatic run of three or four semitones into a target is the approach-note rule extended, and a whole-tone step pair (1 to b7 to b6 downward) is already inside natural minor [unsourced].

A practical reading for a generator: choose a **home set of three or four pitches** from natural minor (1, b3, 5 below or above, b7 or 4), plus **one colour note** that defines the mood of the scene: b2 for menace, 7 for a harder pull to the root, b6 for melancholy weight, natural 6 (Dorian) or the major third above for lift. The colour note is rationed (section 12.5). This is my synthesis; the individual notes are sourced as above, the packaging is not.

---

## 7. Hooks and tunes (brief item 5)

- **What they are made of.** Across this whole family of music the hooks are chopped vocal fragments, stabs and small string or pizzicato refrains, not songs [66]. Reynolds in 1995 complained that keyboard motifs rarely amounted to a riff [62]; Fabio said the music has few hooks and little melody [58]. The reference: 79% stabs and riff fragments, 3% sustained or lead lines [R-hooks].
- **Where a hook starts.** Tim Reaper usually begins a tune from a sample, melody or sound that sets off a hook [34]. A hook needs no clever patch; melody, arrangement and processing matter more [28].
- **How stabs are placed.** Syncopated, on off-beat sixteenths, leaving out the places the main drum hits occupy; some hits long and most short, which makes a call and response inside the stab part; the root left to the bass; small melodic phrases in the gaps between chords [8].
- **How a lead relates to the bass.** It sometimes plays with the bass and sometimes fills the small gaps between bass notes [4]. In one analysed passage only 7 of 28 bass notes coincide with the rhythm guitar's accents [5]. Splitting one melody between two instruments so they never sound together (hocket) turns a plain line into interplay [81f]. Melody and bass moving in opposite directions is a standard way to make each clearer [9].
- **Relation in the reference**: same pitch set, different register (hooks from 233 Hz up, bass below 174 Hz), later in the bar and later in the phrase than the bass, over a bar with fewer low onsets [R-hooks]. And **no** measurable hook-then-sub answering [R-align].
- **How a short motif is developed.** The classical sentence: state the idea, repeat it (often at another pitch), then break it into smaller pieces repeated faster, then close [73]. Question and answer: two units, the first ending weakly and the second strongly, the second usually echoing the first's material [74]. Variation by offsetting the timing and reversing the motif [17]. Mutation by one change per generation [81b]. The standard list (sequence, inversion, fragmentation, displacement) is ordinary composition teaching; I found no source applying it to jungle hooks specifically [unsourced for this genre].
- **Contour.** Balance rises and falls; after a run of steps, leap the other way, and after a leap, step back; give the phrase one highest note, on a strong beat [81a]. Listeners expect small intervals to continue and large ones to reverse and shrink [75].
- **Withholding and return.** The reference brings a shape back about three times, 4 to 8 bars apart, then replaces it; the median gap between any two hooks is 1.5 bars and a tenth of gaps exceed 5.7 bars [R-hooks]. Pads and strings, where used, float across both tempo layers as a release between them [27].
- **Vocal hooks.** Short ragga chants phrased on the slow grid, against the bass and not against the drums [27][R-0915 §4].

---

## 8. The low end as arrangement (brief item 6)

- **The bass drop is the event.** Every press source says so and the reference measures it: sub +10 dB, total level +2.6 dB, brightness down [R-arch][R-drops].
- **Absence makes it.** Keep the defined bass out of the first 32 bars so the DJ can mix [R-forums A3]. Cut or filter the sub through a build so its return feels larger without being louder [30, snippet]. The reference: low end pulled a median 19 dB for 1.2 bars before a drop, break still running [R-drops].
- **Short holes inside the groove.** Bass on 3 bars and off 1 is the normal punctuation; the long absences (up to 34 bars) are structural [R-bass §5].
- **The first note after a gap carries the weight.** The first bar of a drop is often one held note or a gap, and the line starts in bar 2 [R-drops §4]. Reynolds's description of Dillinja is the extreme case: the bass enters as one detonation, not a line [62]. A teaching page calls leaving out the expected note before a big hit a technique in its own right [18].
- **No bass at all is a style**: let the kick do the low work, with a token bassline arriving late if at all [1].
- **Level over a track.** The set's loudness moves 5.9 dB per minute while the low band's share moves twelvefold [R-structure §6]. So the sub is the dynamic. For a generator: schedule **presence**, not volume.
- **Weight against busyness.** A section is either busy and mid-weighted or sparse and deep [R-bass §4]. Busy drums leave less room for a big bass [R-forums B10].

---

## 9. Composition theory that transfers (brief item 7)

### 9.1 Phrase forms

- **Sentence** (2 + 2 + 4): basic idea, its repetition in a varied version, then continuation by fragmentation toward a close. Schoenberg's point, as reported: it states an idea and at once begins developing it [73]. This is the form that sounds "progressive" at phrase scale.
- **Period, or question and answer**: two matched units, the first ending open and the second closed [74]. In blues the answer is literally the dominant-to-tonic turn [79].
- For a one-chord bassline "open" and "closed" have to be made without chords. My mapping [unsourced]: **closed** = ends on the root, low, long, followed by silence (this is the measured low note and gap). **Open** = ends off the root (on b7, 5, 4 or the colour note), or ends short on a weak step, or ends with a pickup into the next bar.

### 9.2 Expectation

- Small intervals imply continuation in the same direction; large intervals imply a turn back and a smaller interval; a return to near the starting pitch (a-b-a) is a basic closed shape; closure comes with a change of direction or a large interval followed by a small one [75]. An alternative account says leaps turn back simply because they have reached the edge of the range [snippet].
- Three kinds of tension are distinguished in one model: from surprise, from denial of the expected, and from strong expectancy of what comes next [76]. The third is what a leading tone or a b2 hanging over the bar line produces.
- Music that sticks combines a common shape with one unusual interval feature [77, snippet].

### 9.3 Bass craft in neighbouring musics

- **Walking bass**: targets on strong beats, approached by semitone or step from the beat before [82, snippet]. Plan backwards from targets.
- **Funk**: everything is licensed by hitting beat 1; the groove is what happens between [83, snippet][16].
- **Reggae and dub**: strong beats plus one or two syncopated places; repeated notes on the fifth below; rests counted as part of the line [71][snippet].
- **House and techno**: root-rhythm lines with a flourish at the bar end; lines that hold off before a change to make tension; off-beat lines whose rare downbeat lands harder for it [1][6]. Techno's seemingly simple loops work by leaving the metre partly open so the listener completes it (Butler, as reviewed) [69].
- **Metal**: a low pedal note returned to constantly, with the moving notes above it taken from Phrygian, Locrian or chromatic neighbours [84, snippet]. The structure (pedal, departure, return) is the same anchor-and-decoration idea at a higher tempo.
- **Ostinato as the opposite of development**: it creates drama by not changing while other things do [78]. In a roller the bass is the ostinato and the development is elsewhere.

### 9.4 What generative-music work has found

- A chance model that picks each note from the last few produces short stretches that stay in key and no long-range plan; motifs, repeats and variations do not arise from it [85][86][88].
- Remedies that worked:
  - **Structure taken from a template**: fix which bars resemble which (a self-similarity plan), the metre and the tonal profile, and search for notes that satisfy them while staying locally plausible [85].
  - **Repeated-pattern constraints plus a tension curve**: decide where patterns recur and what tension each moment should have, then optimise pitches to fit both [86].
  - **Constraints on a chance model**: require given notes at given positions (for instance the last note), or a given overall contour, and sample only sequences that comply [87, snippet].
  - **Look-back inputs**: let the generator see what happened one and two bars ago and whether the last event was itself a repeat; this was enough to make it produce bars that mirror or contrast with earlier ones [88].
  - **Contour first**: plan the shape (arc, single peak), then fill [81a].
- The common lesson: **decide the plan at the slow level first (which bars return, where the targets are, where tension peaks), and let chance work only inside it.** `deal.py` already does this for drums (a spine, then odds). It does not yet do it for pitch or for phrase.

---

## 10. What is commonly got wrong (brief item 8)

| fault | source | present in `deal.py`? |
|---|---|---|
| Random-sounding lines: notes with no return and no destination | [85][86][88]; "no change, or random change every bar" [R-0915 §7] | yes, in pitch and in bar rhythm |
| Too many notes; bass that plays constantly instead of grooving | [18][snippet]; busy sub blurs the groove [18] | partly: every bar has about 3.7 onsets [computed], no bar is sparse by design |
| No gaps; notes held through the snare | [18][24][12, snippet] | partly: lengths are capped below the gap, but gaps are not placed anywhere in particular |
| Treating length as secondary to pitch | [18] | yes: length is drawn independently of position and role |
| Bass doubling the kick everywhere, or fighting it | [16][10][snippet] | not addressed: the riff does not know where the kicks are |
| Busy break with busy bass | [R-0915 §7][R-forums B10] | not addressed: bass density does not respond to drum density |
| Hook and bass fighting: hook on the root, on the bass's onsets, in the bass's register | [8][4][5] | partly: register is separated; timing and pitch are unrelated to the bass |
| No development; a drop identical for 64 bars; second drop a copy | [19][22][R-forums A11] | yes: the riff is replaced wholesale every sixteen bars, which is change without development |
| Automation standing in for ideas | [36] | n/a |
| Over-signalling: too many one-off events | [81c] | no |
| Sub made wide, or made the melodic voice | [18][28] | n/a here |

---

## 11. Why the present lines feel aimless: `deal.py` against the findings

What the code does (read from `mindstream/deal.py`; the description of the saw "bass" answering on fixed steps is from the brief, since it is not in this file):

**`sub_riff`**

1. Each of four bars draws its own onsets: start at step 0 (90%) or 2, then gaps drawn from 3, 4, 4, 4, 5, 6 sixteenths. Mean gap 4.33, so about 3.7 onsets a bar [computed].
2. Pitch is a walk on scale steps: stay 72%, step 20% (more often down), fifth-or-home 5%, a third 3%, clamped to steps -3 to 4. Only bar 1 is reset to the root.
3. 45% of riffs become eight bars by repeating the four with bar 4 cut to its first two notes. 40% of riffs replace the last bar with one low root and a gap.
4. A new riff every sixteen bars.

Set against sections 2 to 9:

| finding | what the code does | consequence |
|---|---|---|
| Identity is a rhythm held across bars, decorated differently each time | every bar's rhythm is drawn afresh; nothing in bar 2 refers to bar 1 | no riff, only four unrelated bars that then loop. The loop gives repetition at lag 4 without anything memorable to repeat |
| Anchors on beat 1 and 2-and (or 4); pairs an eighth apart; pushes from the off-eighths into a beat | odd gaps (3, 5) put notes on odd sixteenths by drift. About 31% of onsets end up on odd sixteenths [computed], which matches the reference's share, but they are not pickups into anything | the right number of off-grid notes with none of their function. This is the clearest case of "statistics right, intent missing" |
| Short notes repeat or step; leaps leave long notes; small moves slide | the move does not depend on the note's length or position | leaps land anywhere; the rare fifth has no setup and no consequence |
| Statement and answer; the second bar of two sits lower | no bar is derived from another | nothing answers anything |
| The phrase thins toward its end; 3 bars on, 1 off | constant density in every bar; the only ending is the 40% low note | no sense of a phrase closing, except by that one device |
| Targets and approach: tension notes resolve to an anchor | scale steps only; no colour note; no target; the walk ends each bar wherever it happens to be | lines "do not go anywhere" because there is nowhere they are going |
| Placement depends on the drums (double a break kick, sidestep a two-step) | takes only a seed | "does not answer the drums" |
| After a run: the same riff back after a hole 36%, a partial rewrite 21%, new 39% | always new, and unrelated to the last | change every sixteen bars, but no development: nothing heard earlier is ever heard changed |
| Layer clocks: riff 8, tone 17, drums 28 to 32, slow layers moving on a riff change | one clock (16) for the riff, as far as this file shows | sections do not feel like sections |
| First bar after a gap is one heavy note | not modelled | returns have no weight |

**`hook_shape` and `hooks`**

1. Two to four notes; start on step 0, 2 or 4 of the scale; each next note a random step of -2 to +2; onsets 1 to 3 sixteenths apart; no target for the last note.
2. The main shape is placed in bar `first` and bar `first + 4` at one of six start steps, and is new every eight bars. Other hook bars get "cousins", which are fresh shapes from a different seed, not variations of the main one.

| finding | what the code does | consequence |
|---|---|---|
| One distinctive interval and a common contour make a motif stick | intervals are uniform small steps; contour is unplanned | shapes are interchangeable; none is "the" hook |
| A motif is developed: repeated, answered, fragmented, displaced | the repeat four bars later is exact; cousins are unrelated; replacement every eight bars is total | a statement with no answer and no consequence |
| Hooks sit where the low end is less busy, late in the bar and late in the phrase (bars 4, 5, 8) | start step and bar are drawn without reference to the sub riff | hook and bass coexist by accident |
| Hook and bass share a small pitch set (5, b3, 1, 4); stabs leave the root to the bass | starts on 1, 3 or 5 of the scale and wanders anywhere within about an octave | the hook does not sound like it belongs to this bassline |
| A shape returns about three times and is replaced; some shapes are withheld for 8 bars or more | exactly two appearances per eight bars, new every eight | neither a held hook nor a withheld one |
| The saw "bass" (from the brief): fixed steps an octave up | fixed | the classic records' second bass identity is a *different line* that takes turns with the sub; a fixed echo is neither a layer of the sub nor a line of its own |

One sentence: **every draw is independent of every other draw, and intent is the dependence between them.**

---

## 12. As rules a program could follow

Support levels used below: **measured** (the owner's reference), **sourced** (a numbered source says it), **inferred** (my construction from those; the weakest). Parameters are starting values, to be tuned by ear.

### 12.1 The plan before the notes

Decide these per scene and hold them (a scene is a section [R-rules]):

| choice | values | support |
|---|---|---|
| Home pitch set | root plus two or three of: b7 (2 semitones below), 5 (below preferred), b3, 4 | sourced [60, snippet][17][18]; measured root about 33% of weight [R-bass] |
| Colour note | exactly one of b2, 7, b6 (or 6 for lift) | sourced for b2 and 7 [14][15][2]; the "exactly one" is inferred |
| Density class | deep (0.25 to 0.5 pitch changes a bar, long notes) or busy (1.3 to 1.7, short notes) | measured [R-bass §4] |
| Roller dial | 0 = hold the riff 32 bars and vary only decorations; 1 = answer changes every 2 bars, riff rewritten every 8 | sourced as a spectrum [31][32][39, snippet]; the dial is inferred |
| Drum relation | break kick: shorts may double kicks. Two-step: shorts one sixteenth after a kick, longs start on step 2 or 12 | measured [R-bass §13.7] |
| Riff period | 2 bars (in a 4- or 8-bar phrase), 4 or 8 | measured [R-bass §11] |

### 12.2 A rhythm cell with anchors (one bar, the statement)

1. **Anchor A** on step 0: either a long note (4 to 6 sixteenths) or the pair "short on 0, short on 2" leading to a held note on 4. Always present in the statement bar. Measured; sourced [16][18].
2. **Anchor B**: step 6 (2-and) by default; alternatives step 12 or step 10. Held 3 to 5 sixteenths. Measured [R-bass §13.5].
3. **Decorations**: 0 to 3 short notes (1 to 2 sixteenths), drawn only from these moves: a pair an eighth apart; a pickup one eighth or one sixteenth before an anchor or before step 12 (from step 10 or 11); a kick-double or kick-sidestep by the scene's drum relation. No short note may be left without another onset within an eighth. Measured [R-bass §13.4, §13.9].
4. **Forbidden**: an onset on step 5 (the sixteenth after the first snare), and only rarely one on step 13; a note sounding through step 4 or 12 unless it started there or is the bar's one long note in a deep scene; more than four short notes; runs of sixteenths longer than three. Measured, and [18] for the snare.
5. **Lengths by role**: anchors long, pickups short, and the last note of the bar either cut by the next bar's anchor or released at least two sixteenths before the bar line. Sourced [18][24]; measured that 61% of short notes are cut by the next onset.

Two cells in my own notation (S short, M medium, L long, dots are silence; not taken from any record):

```
da-da-DUM      S.S.|L...|....|..S.     shorts on 0 and 2, held from 4, pickup on 14 into the next bar
one, two-and   L...|..L.|..S.|M...     held from 0, held from 6, push from 10 into a medium note on 12
```

### 12.3 The answer (bar 2 of a two-bar unit)

Derive it from the statement by one or two of these, never by a fresh draw:

| operation | detail | support |
|---|---|---|
| Keep the head, change the tail | steps 0 to 7 as in the statement; steps 8 to 15 re-dealt or emptied | sourced [18][24]; inferred split point |
| Remove | delete the last one or two notes, leaving a gap | sourced [18] |
| Shift | move one decoration by an eighth (or one anchor by a sixteenth, at most once per phrase) | sourced [4][16] |
| Lower | transpose the bar's centre down one scale step (to b7) with probability about 0.65 | measured [R-align] |
| Lengthen | back-half notes 0.05 to 0.1 beats longer | measured, weak [R-align] |
| Octave | one note up an octave, in the gap between kicks | sourced [4][6] |

### 12.4 The phrase: four and eight bars

- **Four bars**: S A S A′, where A′ is the answer closed (ends on the root). Or, as a small sentence: S, S varied, then two bars that use only the head of S (fragment), ending closed. Sourced [73][74]; mapping inferred.
- **Density by bar**: weight the number of decorations 29 : 25 : 27 : 19 across the four bars. Measured [R-bass §13.3].
- **Bar 4 or bar 8 is the turnaround**, chosen by scene and re-chosen each time:
  - closed by subtraction: one low root for 3 sixteenths, then silence (probability 0.4 to 0.5). Measured [R-rules].
  - a hole: no bass at all for the bar (aim for about 3 bars on to 1 off over the scene, so roughly one phrase end in two or three). Measured [R-bass §5].
  - open by pickup: the colour note or the 5 on step 14 or 15, sliding into the next phrase's root. Sourced [3][82, snippet].
  - a lift: the answer up an octave or rising by step over the last half bar, at most once per 16 bars. Sourced [43].
- **Eight bars** as a sentence: bars 1-2 statement and answer; bars 3-4 the same with A′; bars 5-6 fragments (the head of S twice per bar, or S's pitches on a thinned rhythm); bars 7-8 a close: target, then turnaround. Sourced form [73]; applying it to a sub riff is inferred.

### 12.5 Pitch with targets

1. **Skeleton first.** Give each bar a target pitch for its first anchor. Default for four bars: root, b7, root (or the phrase's one high point: b3, 4 or 5), root. One high point per phrase, placed in bar 3 of 4 or bar 5 or 6 of 8. Sourced for single peak and arc [81a]; default path inferred, with bar 2 lower measured.
2. **Fill by role.** Short notes repeat the target or its scale neighbour (aim: 35% repeat, 33% step, as measured). A leap of a fourth, fifth or octave may only *leave a long note*, and the next move comes back toward it by step. Measured [R-bass §13.4]; the return is sourced [75][81a].
3. **Approach.** The last short note before any target may be replaced by a note one semitone above or below the target, or a scale step from it. Sourced [82, snippet].
4. **The colour note's ration.** At most one per bar; never longer than an eighth unless it is the last note of an open phrase; only on a weak step or as a pickup; always followed within a beat by the note a step away that it leans on (b2 to 1, 7 to 1, b6 to 5). More likely in answer bars than statement bars, and most likely in the turnaround. Zero in the first statement of a new riff, so the riff is heard plain before it is coloured. All inferred from [82][14][15][2]; this is the rule most in need of testing by ear.
5. **Slides.** Slide when the interval is 2 semitones or less (probability about 0.6, giving about 40% of all moves, as measured), and always on an approach into a target before a snare. Time 60 to 100 ms. Strike the leaps. Measured [R-bass §1, §3]; sourced [18].
6. **Range.** Keep the line within a fifth below and a fourth above the root, as now; an octave move belongs to the mid layer or to a marked event. Measured octaves at 1.8% [R-bass §3].

### 12.6 The second bass (the present saw "bass")

Make it a line with its own job, switchable per scene:

- **Echo**: off, or doubling the sub's anchors an octave up for small speakers. Sourced [3][28].
- **Answer**: plays only in the sub's rests, concentrated in answer bars and turnaround bars; one to three pitches from the home set; its rhythm is the statement cell's head, displaced to start on step 8. Sourced in kind [23][24][4]; the construction is inferred.
- **Lead**: in a deep scene the sub holds one or two long notes a bar and this layer carries the riff of 12.2 to 12.5. Sourced [42][47][49, snippet]; measured as "busy and deep are alternatives".
- Never busy at the same time as a busy sub. Measured [R-bass §4].

### 12.7 Development over 8, 16, 32 and 64 bars

Keep a riff as a stored object (cell, answer operations, skeleton, colour note) so that it can be changed and brought back.

| clock | action | support |
|---|---|---|
| every bar | re-deal decorations inside the cell's rules; anchors and skeleton untouched | measured [R-bass §13.5]; [R-rules] |
| every 2 bars | statement, answer | sourced, measured |
| every 4 bars | bar 4 thinned; turnaround chosen | measured |
| every 8 bars | apply **one mutation** to the stored riff and keep it (next generation builds on this one). Mutations: delete a decoration; add a pickup; shift a decoration an eighth; swap one skeleton pitch for a neighbour in the home set; change which bar holds the high point; switch the answer's operation; lengthen the anchors and drop a decoration (toward deep) or the reverse; turn the colour note on or raise its ration | sourced [81b][57][22]; the list is inferred |
| at the end of a run (draw run length from 7 to 15 bars, snapped to the 8-bar line most of the time) | choose: same riff back after a one-bar hole (0.36); partial rewrite keeping about half the cell and half the skeleton (0.21); new riff (0.39); transposition (0.03) | measured [R-bass §11.2] |
| about every 16 bars | change the sub's tone; add or remove the second bass; one unique event (a single octave lift, a reversed note into an anchor, a bar of half-time anchors) | measured clock [R-align]; sourced [81c] |
| about every 32 bars, on a riff change | switch to the **B riff**: opposite density class, same home set, a different anchor B, a different colour note or none; change kick pattern and carrier with it | sourced [19][20][60, snippet]; measured co-change [R-align]; "opposite class, same set" inferred |
| at 64 bars, or at the second drop | bring back riff A in a later generation, with one of: second bass added; A's rhythm with B's skeleton; a harder tone. Precede it with 1 to 2 bars of no low end, and make the first bar one held root | sourced [19][22][23]; measured [R-drops] |
| when a "new riff" is drawn | keep one thing from the last riff (anchor B, or the answer operation, or the colour note) with probability about 0.5, so even new riffs are relatives | inferred. Note the measured caution: pure "same rhythm, new notes" is about absent in the reference, so keep a *part*, not a whole dimension |

Do not raise level or density over the section. Progress is turnover. Measured [R-arch]; sourced [63].

### 12.8 The hook, tied to the bass

1. **Pitch set**: four or five pitch classes for the scene, chosen from the scale to include 5, b3, 1 and 4, in the 233 to 392 Hz octave as now. Measured [R-hooks §6].
2. **Motif**: two to four notes with **one distinctive interval** (a fourth, a fifth or a minor sixth, once) and otherwise repeats and steps; one highest note; the leap followed by a step back. Sourced [77, snippet][81a][75].
3. **Last note**: chosen against the bass's target for that bar: not the bass's own pitch class when the bass is sounding its root; prefer b3, 5 or b7 above it; the major third two octaves above a held sub note is a measured option for a bright scene. Sourced [8]; measured [R-hooks]; the preference list is inferred.
4. **Where in the bar**: start on a step where the sub riff is silent, preferring steps 8 to 14; never on step 0, 4 or 12. Its own onsets avoid the bass's onsets in that bar. Sourced [8][4][5]; measured back-half preference.
5. **Which bars**: prefer bars 4, 5 and 8 of the eight, and prefer bars where the sub is thin or absent (the turnaround bar is the obvious one). Measured [R-hooks].
6. **Rhythm kinship** (optional, per scene): the hook's inter-onset pattern copies the first two or three onsets of the sub's statement cell. This gives a rhythmic rhyme between hook and bass without a call-and-response timing, which the reference does not show. Inferred.
7. **Development**: appearance 1 is the statement, ending open (not on 1). Appearance 2, four bars later, is the answer: same head, last note changed to 1 or 5, and transposed down a step if the bass answer went down. Appearance 3 is a fragment (first two notes) or the motif displaced by an eighth. Then replace it, keeping its rhythm or its distinctive interval for the successor with probability about 0.5. "Cousins" are drawn from the same operations (fragment, displace, invert the contour, sequence a step down), never from a fresh seed. Sourced forms [73][74][17]; measured three appearances [R-hooks §3]; the mapping is inferred.
8. **Withholding**: after a hook is retired, leave the lane empty for 4 to 8 bars about one time in four; bring hook A back when riff A returns. Measured gaps [R-hooks §2]; the pairing with the riff is inferred from the finding that placement states change at riff changes.

### 12.9 Parameters in one table

| parameter | start value | range | support |
|---|---|---|---|
| pitches in home set | 3 | 2 to 4 | sourced |
| colour notes per scene | 1 | 0 to 1 | inferred |
| colour note per bar, statement / answer / turnaround | 0 / 0.25 / 0.5 probability | | inferred |
| decorations per bar | 1.5 to 3 mean, none in a third of bars | 0 to 4 | measured |
| decoration weights across 4 bars | 29 : 25 : 27 : 19 | | measured |
| anchor B step | 6 | 6, 10, 12 | measured |
| answer lowered a step | 0.65 | 0.5 to 0.8 | measured |
| turnaround: low note and gap / full hole / pickup / lift | 0.4 / 0.2 / 0.3 / 0.1 | | first measured, rest inferred |
| slide when interval ≤ 2 semitones | 0.6 | 0.4 to 0.8 | measured |
| slide time | 80 ms | 30 to 100 | measured, sourced |
| run length before the riff's fate is drawn | 11 bars | 7 to 15, snapped to 8s | measured |
| fate: return / partial / new / transpose | 0.36 / 0.21 / 0.39 / 0.03 | | measured |
| one mutation every | 8 bars | 4 to 16 (roller dial) | sourced |
| B riff every | 32 bars | 16 to 64 | sourced, measured |
| hook appearances before replacement | 3 | 2 to 4 | measured |
| hook bars preferred | 4, 5, 8 of 8 | | measured |

### 12.10 How to tell whether it worked

Checks the program can run on its own output, using the owner's measures as targets:

- Bar-to-bar agreement of the bass at 2 and 4 bars is 50% or more while agreement at 1 bar is low [R-bass §11].
- In two-bar cycles the back bar is lower than the front in about two thirds [R-align].
- More than half of onsets on steps 0, 2, 4, 6, 10, 12; under 4% on step 5 [R-bass §13.2].
- Every colour note is followed within four sixteenths by its neighbour [rule 12.5.4].
- Hook onsets coincide with bass onsets less often than chance for the same densities [rule 12.8.4].
- After 64 bars, at least one earlier riff has come back changed [rule 12.7].

And one check that is not a statistic: whether the statement bar can be sung back after two hearings. Zinc's lines were valued for exactly that [40], and one forum voice asks the same of a drum edit [R-forums E2].

---

## 13. What I could not find, and how far to trust this

- **No note-level analysis of any named classic line** (Burial, Original Nuttah, Terrorist, Valley of the Shadows, The Angels Fell, Super Sharp Shooter, Pulp Fiction, Brown Paper Bag, Renegade Snares, Inner City Life, Wormhole, The Nine, anything by Pendulum). The sources that exist describe layers and order of events. Section 4.2 is as far as they go.
- **Not reached**: the search allowance ran out, so nothing new came from Resident Advisor, FACT, Sound On Sound's drum & bass features beyond the Goldie piece, Computer Music, *State of Bass*, or academic writing on riffs. DJ Mag, Dogs On Acid, Juno Daily and Open Music Theory refused the fetch; MusicRadar and Guitar World pages came back cut short. Claims from these are marked [snippet].
- **Thin**: Tim Reaper, Sully and Coco Bryce say little in print about how they write bass. Christodoulou's dub article is cultural, not technical. Butler's techno book was reached only through a review.
- **Nothing found**: whole-tone and chromatic gestures in this music; a definition of "progressive" as jungle DJs use it; pedal points named as such; the Wormhole-era basslines in any detail.
- **Weight of the evidence.** Best supported: the owner's measurements (one set), and the points where several independent tutorials agree with them (rhythm first, few pitches, root on 1, gap after the snare, statement and answer, a marked phrase end, change on 8/16/32, a second bass idea). Moderately supported: the tension-note vocabulary (b2, 7), the roller dial, hook placement against the bass. Least supported, and my own: the mapping of open and closed endings onto a one-chord bassline, the ration for the colour note, the mutation list, the kinship rules between successive riffs and between hook and bass. Those are designs to be tried, not findings.

---

## 14. Sources

Tutorials and magazines

1. Attack Magazine, "Low-End Theory: Exploring Eight Common Bassline Styles" (pages 1, 2 and 5 read). https://www.attackmagazine.com/technique/tutorials/low-end-theory-exploring-eight-common-bassline-styles/
2. Attack Magazine, "Use Ableton's Wavetable to Create a Bassline Inspired by Kings of the Rollers". https://www.attackmagazine.com/technique/synth-secrets/creating-a-bassline-inspired-by-kings-of-the-rollers-using-abletons-wavetable-and-instrument-rack/
3. Attack Magazine, "Creating 808-Style Basslines for Jungle, Trap and Footwork". https://www.attackmagazine.com/technique/tutorials/creating-808-style-basslines-for-jungle-trap-and-footwork/
4. Attack Magazine, Passing Notes, "Daft Punk Basslines: The Ultimate Guide". https://www.attackmagazine.com/technique/passing-notes/daft-punk-basslines-the-ultimate-guide/
5. Attack Magazine, Passing Notes, "Daft Punk Basslines: Part 2". https://www.attackmagazine.com/technique/passing-notes/daft-punk-basslines-part-2/
6. Attack Magazine, Passing Notes, "5 Tips To Improve Your Synth Basslines". https://www.attackmagazine.com/technique/passing-notes/5-tips-to-improve-your-synth-basslines/
7. Attack Magazine, Passing Notes, "Ostinatos and Acid Riffs". https://www.attackmagazine.com/technique/passing-notes/ostinatos-and-acid-house-riffs/
8. Attack Magazine, Passing Notes, "Levelling Up Your Chord Stabs". https://www.attackmagazine.com/technique/passing-notes/levelling-up-your-chord-stabs/
9. Attack Magazine, The Breakdown, "Julio Bashmore: 'Au Seve'", page 2. https://www.attackmagazine.com/technique/the-breakdown/julio-bashmore-au-seve/2/
10. MusicRadar, "Beat programming: get your kick and bass working together" (page cut short; part snippet). https://www.musicradar.com/how-to/beat-programming-drums-bass-rhythm-section
11. MusicRadar, "23 classic drum 'n' bass tips". https://www.musicradar.com/tuition/tech/23-classic-drum-n-bass-tips-155890
12. MusicRadar, "Songwriting basics: How to program the perfect bassline in your DAW" (snippet only). https://www.musicradar.com/how-to/how-to-program-a-bassline
13. MusicRadar, "How to create a classic rave chord stab" (snippet only). https://www.musicradar.com/how-to/rave-chord-stab
14. Splice blog, "How to Write a Bassline for Different Genres". https://splice.com/blog/how-to-make-basslines/
15. Hack Music Theory, "4-Step Hack for Dark Bass Lines". https://hackmusictheory.com/blogs/theory/posts/4-step-hack-for-dark-bass-lines
16. Hack Music Theory, "3 Hacks for EDM Bass Lines & Kick Drums". https://hackmusictheory.com/blogs/theory/posts/4687854/3-hacks-for-edm-bass-lines-kick-drums
17. Hack Music Theory, "How to Write Epic EDM Bass Drops in 7 Steps". https://hackmusictheory.com/blogs/theory/posts/4703488/how-to-write-epic-edm-bass-drops-in-7-steps
18. DNB College, lesson "Sequence a subsine for oldskool rave pressure" (teaching site, author not identified). https://www.dnb.college/lessons/sequence-a-subsine-for-oldskool-rave-pressure-in-ableton-live-12-advanced-mixing
19. KAN Samples, "Drum and Bass Track Structure & Arrangement". https://kansamples.com/blogs/learn/dnb-track-arrangement
20. EDMProd, "How To Make Drum & Bass: The Complete Guide". https://www.edmprod.com/how-to-make-drum-and-bass/
21. EDMProd, "How to Make Jungle Music". https://www.edmprod.com/how-to-make-jungle-music/
22. Preset Drive, "How to Make Jump-Up Drum and Bass". https://www.presetdrive.com/how-to-make-jump-up-drum-and-bass/
23. Melodigging, "Jump Up" (genre page). https://www.melodigging.com/genre/jump-up
24. Mixed In Key, "How to write a bassline". https://mixedinkey.com/captain-plugins/wiki/how-to-write-a-bassline/
25. Native Instruments blog, "How to produce a drum and bass track". https://blog.native-instruments.com/drum-and-bass/
26. Transmission Samples, "Bass-lines in drum and bass MIDI arrangements". https://www.transmissionsamples.com/tutorials/drum-and-bass-production/dnb-bass-tutorial
27. Orphiq, "What is jungle music". https://orphiq.com/resources/what-is-jungle-music
28. Magnetic Magazine, "Music production tips for making jungle" (2026). https://magneticmag.com/2026/06/music-production-tips-for-making-jungle/
29. Reason Studios, "Jungle 101: Let's Talk Bass". https://www.reasonstudios.com/news/post/jungle-101-lets-talk-bass
30. Point Blank Music School, "How to Make Your Drops Hit Harder" (snippet only). https://www.pointblankmusicschool.com/blog/how-to-make-your-drops-hit-harder-tips-for-edm-producers/

Producers, DJs and records

31. UKF, "Rollers are not a subgenre, you muppets!" (Futurebound, Jade, Skynet, Nymfo, Iris). https://ukf.com/read/rollers-are-not-a-subgenre-you-muppets/
32. In-Reach, "What is a roller?". https://in-reach.co.uk/what-is-a-roller/
33. UKF, "In Conversation With Tim Reaper". https://ukf.com/words/in-conversation-with-tim-reaper/27803
34. T3mpo, Tim Reaper interview. https://t3mpo.com/tim-reaper-jungle-can-do-almost-anything-it-wants-to-interview/
35. Junglist Network, "Tim Reaper: Rewiring Jungle for a New Generation". https://junglistnetwork.com/tim-reaper-rewiring-jungle/
36. Native Instruments blog, "Jungle revivalist Sully sketches out haunting atmospherics". https://blog.native-instruments.com/sketches-sully/
37. Line Noise, interview with Sully. https://linenoise.substack.com/p/john-denvers-got-some-bangers-an
38. UKF, "The curious journey of Coco Bryce". https://ukf.com/read/the-curious-journey-of-coco-bryce/
39. Juno Daily, Coco Bryce interview, 2024 (snippet only; fetch refused). https://www.juno.co.uk/junodaily/2024/07/08/coco-bryce-interview-its-a-culmination-of-everything-ive-done-over-the-past-25-or-so-years/
40. Line Noise, "Go DJ! DJ Zinc, Bingo Beats and ceaseless innovation". https://linenoise.substack.com/p/go-dj-dj-zinc-bingo-beats-and-ceaseless
41. dnb365, "DJ Zinc: Super Sharp Shooter". https://dnb365.wordpress.com/2020/04/09/dj-zinc-super-sharp-shooter/
42. Line Noise, "The best records ever to wreck a genre, part 1: Bad Company, The Nine". https://linenoise.substack.com/p/the-best-records-ever-to-wreck-a
43. dnb365, "Bad Company: The Nine". https://dnb365.wordpress.com/2013/02/19/bad-company-the-nine/
44. Kmag, "The Essential... Bad Company". https://kmag.co.uk/the-essential-bad-company/
45. Wax Poetics, "Alex Reece: Pulp Fiction" (Fabio, Phil Wells quoted). https://magazine.waxpoetics.com/rediscovery/pulp-fiction/
46. Wax Poetics, "Leviticus: The Burial" (Jumpin Jack Frost, Bryan Gee quoted). https://magazine.waxpoetics.com/rediscovery/the-burial/
47. Test Pressing, "Dubwise Vinyl #013: Leviticus 'Burial'". https://www.testpressing.org/magazine/dubwise-vinyl-013leviticus-burial
48. DJ Mag, "How Leviticus' 'Burial' brought jungle's melting pot of influences together" (snippet only; fetch refused). https://djmag.com/features/how-leviticus-burial-brought-jungles-melting-pot-of-influences-together
49. DJ Mag, "How Renegade's 'Terrorist' created a blueprint for jungle" (snippet only; fetch refused). https://djmag.com/longreads/how-renegades-terrorist-created-blueprint-jungle
50. Mixmag, "How Kevin Saunderson's Reese bassline transformed UK dance music" (2025). https://mixmag.net/feature/kevin-saunderson-reese-bassline-transformed-uk-dance-music-jungle-speed-garage-drum-n-bass
51. Tempo, "Rumblizm: In Praise Of The Reese Bass". https://tempo.substack.com/p/rumblizm-in-praise-of-the-reese-bass
52. Wax Poetics, "UK Apachi: Original Nuttah". https://magazine.waxpoetics.com/rediscovery/original-nuttah/
53. Wikipedia, "Original Nuttah" (snippet only, for the riddim). https://en.wikipedia.org/wiki/Original_Nuttah
54. Wikipedia, "Valley of the Shadows". https://en.wikipedia.org/wiki/Valley_of_the_Shadows
55. Sound On Sound, "Rob Playford: Producing Goldie". https://www.soundonsound.com/people/rob-playford-producing-goldie
56. Two Hungry Ghosts, "The Making Of Renegade Snares (Foul Play VIP Mix)" (snippet only; page not found on fetch). https://twohungryghosts.blog/2017/08/26/the-making-of-renegade-snares-foul-play-vip-mix/
57. Red Bull Music Academy lecture, Marcus Intalex (2003). https://www.redbullmusicacademy.com/lectures/marcus-intalex-the-liquidator/
58. Red Bull Music Academy lecture, Fabio (2006). https://www.redbullmusicacademy.com/lectures/fabio-the-root-to-the-shoot/
59. Red Bull Music Academy lecture, DJ Storm (2018). https://www.redbullmusicacademy.com/lectures/dj-storm-lecture/
60. Dogs On Acid forum threads (snippets only; fetch refused): "Writing 90s jungle basslines" https://www.dogsonacid.com/threads/writing-90s-jungle-basslines.809086/ ; "Struggling to write basslines" https://www.dogsonacid.com/threads/struggling-to-write-basslines-help-needed.767113/ ; "Writing basslines" https://www.dogsonacid.com/threads/writing-basslines.797961/ ; "switching the basslines." https://www.dogsonacid.com/threads/switching-the-basslines.341241/

Criticism and academic writing

61. Simon Reynolds, The Wire, hardcore continuum series no. 2, "Ambient Jungle" (1994). https://www.thewire.co.uk/articles/2017/
62. Simon Reynolds, The Wire, no. 3, "The State Of Drum 'n' Bass" (1995). https://www.thewire.co.uk/articles/2018/
63. Simon Reynolds, The Wire, no. 4, "Hardstep, Jump Up, Techstep" (1996). https://www.thewire.co.uk/articles/2028/
64. Simon Reynolds, The Wire, no. 5, "Neurofunk Drum 'n' Bass Versus Speed Garage" (1997). https://www.thewire.co.uk/articles/2030/
65. Afropop Worldwide, interview with Simon Reynolds on UK dance history. https://www.afropop.org/articles/first-draft-simon-reynolds-interview
66. Simon Reynolds, "The Hardcore Continuum, or, (a) theory and its discontents" (2009). http://energyflashbysimonreynolds.blogspot.com/2009/02/hardcore-continuum-or-theory-and-its.html
67. Chris Christodoulou, "Darkcore: Dub's Dark Legacy in Drum 'n' Bass Culture", Dancecult 7(2), 2015. https://dj.dancecult.net/index.php/dancecult/article/view/695/
68. Robert Ratcliffe, "A Proposed Typology of Sampled Material within Electronic Dance Music", Dancecult 6(1), 2014. https://dj.dancecult.net/index.php/dancecult/article/download/369/459/1590
69. Wayne Marshall, review of Mark J. Butler, *Unlocking the Groove* (2006), Music Theory Spectrum 31 (2009). https://wayneandwax.com/academic/mts-butler-unlocking-groove.pdf
70. Wikipedia: (a) "Drum and bass" https://en.wikipedia.org/wiki/Drum_and_bass ; (b) "Darkcore" https://en.wikipedia.org/wiki/Darkcore ; (c) "Techstep" https://en.wikipedia.org/wiki/Techstep

Theory

71. Wayne Marshall, "Feel It In The One-Drop: A Roots Riddims Tutorial". https://wayneandwax.com/org/lessons/roots-riddim-tutorial.html
72. Wikipedia, "Riddim". https://en.wikipedia.org/wiki/Riddim
73. Wikipedia, "Sentence (music)". https://en.wikipedia.org/wiki/Sentence_(music)
74. Yosef Goldenberg, "Continuous Question-Answer Pairs", Music Theory Online 26.3 (2020). https://www.mtosmt.org/issues/mto.20.26.3/mto.20.26.3.goldenberg.php
75. Wikipedia, "Implication-Realization" (Narmour). https://en.wikipedia.org/wiki/Implication-Realization
76. Wikipedia, "Melodic expectation". https://en.wikipedia.org/wiki/Melodic_expectation
77. Jakubowski, Finkel, Stewart and Müllensiefen, "Dissecting an Earworm: Melodic Features and Song Popularity Predict Involuntary Musical Imagery", Psychology of Aesthetics, Creativity, and the Arts, 2017 (snippet only). https://research.gold.ac.uk/id/eprint/19405/
78. Wikipedia, "Ostinato" (riff, vamp). https://en.wikipedia.org/wiki/Ostinato
79. Wikipedia, "Call and response (music)". https://en.wikipedia.org/wiki/Call_and_response_(music)
80. Wikipedia, "Phrygian mode". https://en.wikipedia.org/wiki/Phrygian_mode
81. Dennis DeSantis, *Making Music: 74 Creative Strategies for Electronic Music Producers* (Ableton), online chapters: (a) "Creating Melodies 1: Contour" https://makingmusic.ableton.com/creating-melodies-1-contour ; (b) "Creating Variation 2: Mutation Over Generations" https://makingmusic.ableton.com/creating-variation-2-mutation-over-generations ; (c) "Unique Events" https://makingmusic.ableton.com/unique-events ; (d) "Fuzzy Boundaries" https://makingmusic.ableton.com/fuzzy-boundaries ; (e) "Dramatic Arc" https://makingmusic.ableton.com/dramatic-arc ; (f) "Linear Rhythm in Melodies" https://makingmusic.ableton.com/linear-rhythm-in-melodies ; (g) "Parallel Harmony" https://makingmusic.ableton.com/parallel-harmony
82. Walking-bass teaching pages on target and approach notes (snippets only). https://www.learnjazzstandards.com/blog/learning-jazz/bass/write-walking-bass-line/ ; https://www.thejazzpianosite.com/jazz-piano-lessons/jazz-chord-voicings/walking-bass-lines/
83. Wikipedia, "On the one" (snippet only). https://en.wikipedia.org/wiki/On_the_one
84. Metal riff teaching pages on pedal tones and Phrygian colour (snippets only). https://www.guitarworld.com/lessons/metal-life-how-use-open-string-pedal-tone-build-heavy-single-note-riffs ; https://www.riffhard.com/how-to-write-heavy-metal-riffs/

Generated music

85. Lattner, Grachten and Widmer, on imposing higher-level structure (self-similarity, metre, tonality) on generated polyphonic music by constraints, 2016 (abstract read). https://arxiv.org/abs/1612.04742
86. Herremans and Chew, on generating structured music with constrained repeated patterns and a tension profile, 2017 (abstract read). https://arxiv.org/abs/1812.04832
87. Pachet and Roy, "Markov constraints: steerable generation of Markov sequences", Constraints 16, 2011 (snippet only: the citation and a one-line account as given in search results; no page fetched, so no URL is given).
88. Google Magenta blog, on generating long-term structure in melodies with look-back inputs, 2016. https://magenta.tensorflow.org/2016/07/15/lookback-rnn-attention-rnn
