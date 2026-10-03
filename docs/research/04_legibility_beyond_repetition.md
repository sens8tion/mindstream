# 04. What makes fast, chopped dance music legible, other than repetition

Written 2026-10-02. Secondary research: the owner's own corpus and measurements first, then the web.

How to read the marks:

- **[C…] / [R…]** a file in the owner's corpus or reference measurements (listed in section 2). Those files carry their own citations; I have not re-verified them.
- **[n]** a numbered source in the list at the end. Unmarked means I read the page itself.
- **[snippet]** the claim rests on a search-result summary, not on the page. Treat as a lead.
- **[computed]** my own arithmetic from numbers given elsewhere in this file.
- **[unsourced]** my belief or inference; nothing I found supports it directly.

---

## 1. One-page summary

The question was: if a bar never literally repeats, what lets a listener and a dancer still follow it? The answer from both the owner's measurements and the literature is the same, and it is short:

**People do not follow the surface. They follow a small number of things that stay put underneath it, and they measure every surprise against those.** A loop is only the cheapest way of making something stay put. There are at least twelve others, and the reference jungle set uses most of them at once while repeating no bar.

The strongest findings:

1. **Surprise only counts against a trusted frame.** A hit in an odd place is a big event when the metre is firm and is discounted when the metre is not [C0, C3]. So "more surprising" and "less legible" are not the same dial. Illegible material produces *less* felt surprise than legible material with one thing wrong. This is the single most useful fact for a program: spend certainty in a few places so that everything else can be free.
2. **The reference set's certainty lives in about three cells of forty-eight.** Kick on the one (0.91), snare on two (0.94) and four (0.89) [R-rhythm]. Treating each cell as independent, the set-wide bar is otherwise near maximum disorder: about 13.5 of a possible 16 bits per band [computed]. Legibility there is not coming from low-entropy placement. It comes from the spine, from *which* slots are likely, from the four-bar group returning, from one sound source, and from layers changing on separate slow clocks.
3. **Identity is a distribution, not a pattern.** Neighbouring bars in the reference are no more alike than two random bars from the same section (0.355 against 0.356), yet first half against second half of a kick sub-section correlates at 0.85 [R-rhythm]. Listeners learn odds per position quickly and without attention [C3], and for dense sound the ear keeps time-averaged statistics and discards detail [19, snippet]. A program can hold the odds still and re-deal every bar.
4. **Return at four bars, not at one.** The group A-B-C-D comes back (lag 4 = 0.486, lag 8 = 0.465) while lag 1 sits at the random baseline [R-rhythm]. Four bars at 166 BPM is 5.8 s [computed], which is the span the corpus gives for the perceptual present and for the unit attention grows to with familiarity [C0, C3, C4].
5. **A sound source is recognised in tens of milliseconds** [23, snippet], so one break, or one voice, stays itself through any reordering of sixteenth-note slices (90 ms). Palette is a legibility device independent of pattern.
6. **Makers who do this well describe rules and a drummer's phrasing, not dice.** Paradox programmes fills where a funk drummer would put them and varies kick level so nothing is flat [1]. Autechre say their shifting beats follow rule sets they understand, avoid random operators, and chain conditions (one event recurring triggers another) [3]. Collins's breakbeat cutter cuts in odd numbers of eighths that resolve on the downbeat, limits repeats to two, and reports that sixteenth cut-ups need a solid backing beat to be read [C3].
7. **A few placed displacements beat many.** In a controlled study, one syncopation at a phrase end against an otherwise firm frame gave more groove than shifting everything [6].
8. **Dancers need the slow layer.** Low-frequency flux drives head movement and pulse clarity drives whole-body movement [8]; the lowest stream owns the timing reference [C4]; highly syncopated breaks cut both movement and synchrony [17, snippet]. At 166 BPM the body's level is the half-time one, 83 BPM [computed].

What follows from this for mindstream is in sections 4 and 5: a ranked list of twelve mechanisms, each with an implementation on a sixteenth grid, a measure and an edge; then a table of dials.

One observation about the present code, since it bears on the owner's complaint. `mindstream/deal.py` already deals drums by odds with a spine and a four-bar return, as the reference does. `mindstream/chop.py`, by its own docstring, plans chopped sound as bar 1, bar 1 with one change, bar 1 again, then a turnaround. That is the "three alike and one different" scheme which the reference measurement tested and rejected [R-rhythm §3]. If the output reads as legible-because-repetitive, the chopped layer is the likely place.

---

## 2. What the owner's corpus and measurements already establish

Files read (paths relative to the folder that holds this repository and the sibling thelmic repository):

| Mark | File |
|---|---|
| C0 | `thelmic\docs\corpus\00_synthesis.md` |
| C1 | `thelmic\docs\corpus\01_trance_states_dance_music.md` |
| C2 | `thelmic\docs\corpus\02_build_drop_groove_reward.md` |
| C3 | `thelmic\docs\corpus\03_rhythmic_pattern_recognition.md` |
| C4 | `thelmic\docs\corpus\04_tonal_recognisability_legibility.md` |
| C5 | `thelmic\docs\corpus\05_flow_and_neural_monitoring.md` (headings only; little bears on this question) |
| C6 | `thelmic\docs\corpus\06_measurability.md` |
| R-readme | `thelmic\tracks\2026-09-16_reaper\README.md` |
| R-rhythm | `thelmic\tracks\2026-09-16_reaper\rhythm.md` |
| R-structure | `thelmic\tracks\2026-09-16_reaper\structure.md` |
| FEEL | `mindstream\FEEL.md` |

`thelmic\docs\tension-vocabulary.md` and `mode-topology.md` are placeholders with open questions and no content yet. One of those questions ("when does chaos become noise rather than principled corruption?") is the subject of section 5.

### 2.1 The listening model

- Two states: "I have understood this pattern" and "is a new pattern emerging?". Reward is in the passage between them, not in either [C0 §2a]. Dwell in the first state is the investment that makes the next disturbance readable.
- **Precision weighting** [C0 §2b, C3 A5]: effective surprise = how unexpected × how much the frame is trusted. When the frame collapses the listener either hears noise or re-hears the off-beat as the beat (a phase reset), which is a change of pattern and not a big surprise.
- Two layers of expectation, already separated in the corpus as *schematic* (what metre and style predict) and *episodic* (what this piece has taught so far, with a half-life of two to four cycles) [C3 §d, C6]. A deviation that recurs in the same place stops being surprising but stays alive: "expected deviations".
- Boredom has numbers: four to eight unchanged repeats of a four-bar unit is the disengagement zone; a change every bar is the other failure because the model never converges [C0 §1]. The unit of attention grows from about one second to six to eight seconds as material becomes known, so bar-level variation stops being heard after a few minutes [C0, C1, C4 A9].
- Limits at this tempo [C3 A3, §b]: events closer than about 100 ms fuse into texture. At 166 BPM a sixteenth is 90 ms and an eighth 181 ms [R-rhythm], so the eighth is the fastest level that reads as rhythm and the sixteenth reads as roll or grain. The felt beat moves to the half-time level.
- Strong-beat omissions are the largest single prediction error, with or without attention [C3 A2]. The lowest stream is the timing reference [C4 A13].
- Liking follows a saddle over uncertainty and surprise: a surprising event in a certain context, or an expected one in an uncertain context [C2 §a3, C4 A2]. Interest is the rate of learning, not the amount of novelty; noise is unpredictable and boring because nothing can be learned from it [C2 §a7].
- Groove: a few off-grid events per bar against an unambiguous spine (index about 4 on a scale where 18 collapses it); microtiming is not the lever; shape the sound [C0 §3, C2 §a4-5].
- Recognisability is carried mostly by voice, by timbral recurrence within the piece and by low melodic entropy [C4 A6]. Onsets carry timbral identity; 400 ms of a known record is often enough to name it [C4 A14]. Exact repetition of a spoken fragment turns it into song; reordering its syllables abolishes that [C4 A8].
- Chopping is already framed in the corpus as the way to re-inject episodic surprise per phrase while holding metre precision high, with the failure cases named: seven-eighth blocks that reveal the original, sixteenth cuts with no backing beat, restarts on off-beats every bar [C3 §d].

### 2.2 The reference set, measured

A 21-minute jungle set at 166 BPM, full mix, structural numbers only [R-readme]. Caveats the files state themselves: it is a mix of nine records, bar phase is inferred, and sub-10 ms figures are trends.

**Nothing loops.** Even the most pattern-alike consecutive bars differ by 4.6 ms of per-slot timing where a loop would give 0 to 1 ms; cuts are locked to the sixteenth and land mid-slot [R-rhythm §6].

**Bar to bar.** Consecutive bars r = 0.355; two random bars in the same section 0.356; two random bars anywhere 0.234. About 15 of 48 cells change between neighbours; 2% of bars are near-copies of the previous one [R-rhythm §3].

**The four-bar group returns.** Lag 4 = 0.486, lag 8 = 0.465, lag 2 = 0.436; every even lag beats every odd lag to 16 bars. The low band returns hardest at lag 4 (+0.137 over its own baseline), the high band least (+0.116). "Three alike then disturb" is not supported (p = 0.20) [R-rhythm §3].

**Where the certainty is.** Beat slots 0.83 to 0.87 occupied, other even sixteenths 0.67, odd sixteenths 0.34. Kick slot 0 at 0.91; snare slots 4 and 12 at 0.94 and 0.89. Timing is straight (52.4% swing); spread is 7.5 ms on eighth positions and 13.5 ms on odd sixteenths, which is quantised placement of slices that carry their own loose content [R-rhythm §1-2].

**Fills and density are on a four-bar clock, sparingly.** Fill autocorrelation +0.19 at lag 4; 6.5% of bars are fills, about one opportunity in four; a fill is 1.23 times the onsets and 1.3 times the high-band flux of a normal bar [R-rhythm §4].

**A sixteenth carrier runs in about seven bars of ten.** Gaps are 1 to 2 bars in 82% of cases. Every carrier hit is cut short before the next sixteenth [R-rhythm §9].

**Nested clocks.** Kick *distribution* holds for a median of 25 bars and changes at an edge (within 0.85, across 0.36). Carrier pattern and timbre change in blocks of median 32 bars. Only 36% of kick changes coincide with a carrier change [R-rhythm §9-10]. Surface novelty peaks at a median spacing of 16 bars, mode 8; sections are within two bars of a multiple of four in every case; records run 40 to 192 bars [R-structure §4]. The median section is 9% literal recall and 20% new: most of it is the current material, varied [R-structure §5].

**Two populations of kick.** A programmed two-step repeats (75% of bars within one slot of its pattern, one consistent sample, bass nearly still at 0.25 changes a bar, thin carrier). A break kick is re-dealt every bar (45%), changes timbre hit to hit, and comes with a moving bass (about one change a bar). The reference does not blur them [R-rhythm §10].

**Form is subtraction.** 82% of drops are set up by removing low end while the break keeps running; no risers; the drop is +10 dB of sub with slightly *fewer* events. Low-band share swings 2% to 26% while level moves 6 dB. Drums never thin, even in breakdowns [R-readme, R-structure §6].

**Hooks.** In 39% of bars, median length 1.2 beats, in 233 to 392 Hz with a 10 dB valley separating them from the bass; shapes that recur do so about three times at four to eight bar spacing [R-readme].

**Its own excursions into illegibility are measured too.** In two long blends the beat-comb legibility falls 38 to 39% for 8 to 32 bars with both records audible [R-structure §3]. That is the reference deliberately standing past the lip, twice in 21 minutes.

### 2.3 The feel canon

`FEEL.md` already has the two poles this report is about as pads: **lock / restless** (steady, rolling, driving, hypnotic, relentless against loose, shifting, restless, scattered) and **derangement / composed**. At present lock past 0.6 turns layer variation off and its inverse turns it on; derangement past 0.4 chops finer and past 0.6 adds reversal. Section 5 suggests which dials each pad could move instead of an on/off switch.

---

## 3. Findings by line of inquiry

### 3.1 Expectation and prediction

- Huron separates four kinds of expectation that run in parallel: *schematic* (style-wide habits), *veridical* (this piece, known from before), *dynamic* (built by the piece as it goes, through motif, ostinato and sequence) and *conscious* [7]. For a generator that never repeats, the veridical kind is unavailable by design. Legibility must come from the schematic and the dynamic kinds. That is the theoretical form of the owner's complaint: a loop buys veridical expectation cheaply and leaves the other two unused.
- Correct prediction is itself rewarded, and the reward is credited to the sound; predictions met without conscious recognition are rewarded more than those met consciously [7]. This favours regularities the listener absorbs without noticing (odds per slot, a recurring accent shape) over ones they can name (a loop).
- Huron's advice as reported in the review: introduce a distinctive idea early and use it often, not once [7].
- Abdallah and Plumbley's "predictive information rate", how much each new event tells you about what comes next, is highest for processes between fixed and random, and gives an inverted U against entropy rate in Markov chains [18, snippet]. It is a candidate single number for "the lip": neither low surprise nor high surprise, but high *usefulness* of each event for predicting the next.
- The owner's corpus already holds the inverted U of syncopation and groove, the contest over it, the saddle of uncertainty and surprise, and per-event surprise as −log₂ p [C2, C3, C4]. I did not re-search these.
- Sioros and colleagues built rhythm variants by rule. Shifting a phrase's last note early, with the frame otherwise intact, scored groove effect sizes near 0.60; shifting everything by an eighth scored 0.44; merely doubling density scored about 0.21 to 0.23. Their reading is that single syncopations which momentarily strain a firm metre matter more than the total amount [6].

### 3.2 Metre as the thing that makes variation legible

- Butler: in layered electronic dance music the listener often cannot tell which layer is the metrical one, and attention can flip figure and ground. A low, resonant drum entering can reassign the beat. Ambiguity is resolved by a new layer entering, by a timbral change (a filter opening), or by habituation. Under all of it the fast pulse grid persists [2].
- Butler also argues that uneven patterns such as 3+3+2 are not deviations from 4/4 but *rhythms of reference*: maximally even and "maximally individuated", each onset having a unique set of distances to the others, which is what lets a listener know where they are in the cycle from any point [2]. An evenly spaced pattern cannot do that.
- Hypermetre: rising and falling sweeps sit just before and after hypermetric downbeats and are longer and louder at the more important ones, working as instructions to dancers; the discrete rhythmic frame stays stable beneath them [5]. The reference set marks the same boundaries with subtraction and no risers [R-readme], so the marker is a genre choice, while marking the boundary at all appears to be general.
- Lerdahl and Jackendoff's parallelism rules: when two stretches can be heard as parallel they are preferably grouped as parallel, and given parallel metrical structure [13, snippet]. This is the formal licence for "same shape, different content": parallel *construction* is enough for the listener to align two bars, without identical notes.
- How strongly must the spine be marked? I found no study that states a threshold. The reference gives working numbers: 0.89 to 0.94 for the three spine cells set-wide, and individual sections that run a spine cell as low as 0.64 in one band while another band holds it [R-rhythm §1]. [computed from the tables]
- Not obtained: Butler's book chapters on hypermetre, London's book and Danielsen's microrhythm work were not re-read; the corpus's account of them stands [C2, C3].

### 3.3 Identity carried by things other than pattern

- Sound sources are categorised above chance from a few milliseconds (about 4 ms for voice, 8 ms for instruments), 50 ms is sufficient across voices, instruments and environmental sounds, and targets are still picked out at around 30 sounds a second [23, snippet]. A 90 ms slice is comfortably long enough to say what it came from.
- For dense, texture-like sound the ear keeps time-averaged statistics; listeners get *worse* at telling two examples of the same texture apart as the examples get longer [19, snippet]. Read across to breaks [unsourced]: a re-dealt break with fixed odds is, perceptually, the same thing from bar to bar even though no two bars match.
- Listeners learn the transition statistics of a sequence of timbres by exposure alone, and prefer units made of acoustically similar timbres [24, snippet]. Order among slices is learnable, and a limited, related palette is easier to learn.
- Melodic contour (the up-and-down shape) is used to recognise a melody under transposition, separately from exact interval sizes [24, snippet]. A hook can come back at another pitch or built from other slices and still be the hook if its shape holds.
- Danielsen on funk: whether a groove is heard as the same or as different on each pass depends on the listener's resolution; an unsure listener hears "the same thing" through considerable change [25, snippet]. The same surface is repetition to one listener and variation to another, which is the owner's "different edges than others can tolerate" in a musicologist's words.
- The reference's kick classes show timbre doing this job: a programmed kick is one sample (9.4 dB spectral distance hit to hit), a break kick varies (13.6 dB) but stays within one break [R-rhythm §10].

### 3.4 Grammar of variation

- The Amen break is itself a four-bar sentence: two near-identical bars, a third with the snare displaced by an eighth, a fourth with the downbeat left empty and an early crash [26, snippet; C3 §d]. Statement, statement, displacement, release into the next phrase. Note this is the *source*; the reference set does not reproduce that scheme at the bar level [R-rhythm §3].
- Paradox: thinks as a funk drummer and places fills and tom rolls where one would; slices at the original tempo and keeps the original groove; builds ghost-note shuffles from alternating hat and snare slices with small gaps; cuts and gates slice ends; varies kick level because equal levels sound robotic; inserts a single kick and hat at bar 8 or 16 to reset the loop; treats the edited break as one instrument for tone. One break took 230 slices to sound as if found on tape [1].
- Collins's cutter (as recorded in the corpus; I could not read the paper itself): phrase, then blocks, then cuts; cut lengths in odd numbers of eighths (1 or 3, sometimes 5) so that groups such as 3+3+2 fill the bar and land on the downbeat; at most two repeats; a stutter with probability 0.2; eighth-note subdivision judged the best balance; sixteenth cut-ups easier to read over a solid backing beat [C3 A9, §b]. Search summaries add that the later procedure prefers large cuts, more repeats and early source offsets near the start of a phrase and the opposite toward its end [11, snippet], and that Livecut's hierarchy is cuts in blocks in a phrase, the phrase ending in a roll or fill [4].
- Hockman's study of the genre: producers mostly apply downbeat-preserving transformations [C3 A9; 30, snippet].
- Drum fills are understood by players as markers of phrase ends and announcements of change [27, snippet, non-academic]. The reference agrees on placement and disagrees on size: fills are on the four-bar grid but only one in four is taken and each is a slightly busier, brighter bar [R-rhythm §4].
- Not found: interviews in which Fracture or Equinox describe what makes an edit sound played. Searches returned forum threads and profiles only. Tim Reaper's public comments in search summaries concern tools and favourite breaks, not phrasing [28, snippet].

Drawing these together [unsourced synthesis]: an edit sounds *played* when (a) slices keep their role (a kick slice goes where a kick could be), (b) short runs of slices stay in source order, so the drummer's own phrasing survives inside the chop, (c) departures are displacements by an eighth or a beat and not arbitrary placements, (d) accents are uneven in a consistent way, and (e) density rises toward phrase ends.

### 3.5 Nested timescales

The reference's clocks, with durations at 166 BPM [computed from R-rhythm, R-structure]:

| Scale | Time | What changes |
|---|---|---|
| sixteenth | 90 ms | which slice; nearly five audible truncations a bar |
| bar | 1.45 s | about 15 of 48 cells re-dealt |
| 2 bars | 2.9 s | a weaker sub-period (lag 2 = 0.436) |
| 4 bars | 5.8 s | the group returns; a fill opportunity, taken one time in four; bass about 3 bars on, 1 off |
| 8 to 16 bars | 12 to 23 s | surface novelty (median 16, mode 8); hook shapes recur about three times across this span |
| 25 to 32 bars | 36 to 46 s | kick distribution; carrier pattern and timbre |
| 40 to 190 bars | 1 to 4.6 min | the record |

The corpus supplies the reason this nesting works: the unit of attention lengthens with exposure, so change has to exist at each scale for something to be audible as change at every stage of listening [C1 §d, C4 A9]. It also supplies the limits: something new at least every 8 bars to avoid disengagement, never a new *distribution* every bar [C0 §1].

How much novelty per unit time people enjoy: no direct figure found. The nearest are the corpus's (liking peaks near 2 focused exposures and falls by 8 to 32; a seventh verbatim repeat lowers liking) [C0], and the reference's own ratio of about 20% new material per section [R-structure].

### 3.6 Legibility of non-drum sound

- Exact repetition of a spoken fragment makes it be heard as sung; the effect fails if the repeats are transposed differently each time or if syllables are reordered between repeats [21, snippet; C4 A8]. Looping also musicalises non-speech sound, and the effect is strongest for shorter clips (tested 0.7 to 4 s) [21, snippet].
- Speech with every 50 ms reversed stays almost fully intelligible; around 100 to 130 ms intelligibility is about half; by 200 ms it is gone [22, snippet]. Syllable-rate modulation is roughly 3 to 8 per second [22, snippet].
- At 166 BPM an eighth-note slice is 181 ms, 5.5 a second, inside the syllable band; a sixteenth is 90 ms, 11 a second, above it [computed]. So for voice: **eighth-note slices are about one syllable and can read as words or as a phrase; sixteenth slices are sub-syllabic and read as timbre.** Reversing a sixteenth of voice sits right at the lip of intelligibility; reversing an eighth destroys the word [computed from 22].
- I found no study of chopped vocals in dance music as such. The practical rule in the owner's code (cut where things begin, never at blind distances) is consistent with the above, since a cut at an onset keeps the consonant that identifies the syllable [unsourced].
- The reference's hooks: short, low, recurring about three times and then replaced [R-readme].

### 3.7 Dancers

- Free dancing to 30 pieces: pulse clarity correlated with speed of the body's centre (r = 0.67), feet (0.55) and overall movement (0.62); low-frequency flux (50 to 100 Hz) with head speed (0.73); high-frequency flux with hand speed (0.65) [8]. Different parts of the body lock to different metrical levels at once [14, snippet].
- Raising the level of the bass drum raises the amount of movement in a club-like setting [16, snippet]. Dancers moved more, with more acceleration, to electronic dance music than to funk, Latin or jazz, and moved less during a break [15, snippet].
- With highly syncopated drum breaks, people move little and synchronise poorly [17, snippet]; the corpus has the same result [C3 A5].
- Trance-like absorption needs a near-isochronous pulse (6.7 ms jitter worked, 16.5 ms was the control), continuity of the order of ten minutes, and bodily hold through bass [C0 §2c, C1].

Reading for a generator [unsourced synthesis]: the body needs one slow layer it can trust (the half-time backbeat at 83 BPM and the weight on the one), carried by the lowest band; the upper bands can be re-dealt freely because the hands and head will take them as texture and accent. The reference fits: low band defines the four-bar unit, high band is where the re-chopping shows [R-rhythm §3].

### 3.8 Generative and algorithmic systems

- **Markov chains**: stylistically plausible over short spans, no conception of long-term structure, pieces wander [20, snippet]. The standard remedy is to impose repetition structure or hierarchy from outside. This is the algorithmic statement of "novelty with no return".
- **Euclidean rhythms** spread onsets as evenly as possible and reproduce many traditional timelines [12, snippet]. They give maximally even, self-locating patterns of the 3+3+2 family that Butler treats as reference rhythms [2]. On their own they are fixed loops; their use here is as *frames* to deal against, not as patterns [unsourced].
- **TidalCycles**: variation is made by transforming a cycle, not by generating a new one. The cycle is the fixed metric anchor while content changes from cycle to cycle [29, snippet]. The transformations are a vocabulary of legible operations: `every n` (apply a change on a slow clock), `linger` (repeat the first fraction to fill the cycle), `chunk` (apply a change to one quarter at a time, moving on each cycle), `ply` and `stutter` (repeat each event), `degradeBy` (drop events at random), `rot` (rotate values but keep the rhythm), `palindrome`, and the pair `shuffle` (reorder parts, each used once) against `scramble` (pick parts at random with repeats) [9]. The difference between the last two is exactly a legibility dial: `shuffle` keeps the whole palette present every cycle.
- **Autechre**: the beats follow rule sets the makers understand; they avoid random operators because a process that sounds different every run cannot be shaped; control is by hand on faders that set how often a figure occurs; rules listen to each other, so a figure occurring a set number of times triggers a response [3]. Related accounts describe systems that generate within predefined limits [32, snippet].
- **Collins / Livecut**: see 3.4. The design lesson is the three-level hierarchy with constraint at each level and a marked phrase end.

What works across all of these: a fixed cycle or phrase as the frame; a small set of named transformations; determinism or seeding so that a result can come back; constraints that tighten toward the downbeat and loosen toward the phrase end. What fails: unconstrained chance, and local rules with nothing above them.

---

## 4. Sources of legibility a program can use instead of repetition

Ranked by how much legibility each buys for how little literal sameness. For each: what it is; why it works; how to do it with slices on a sixteenth grid; how to measure it; where its edge is. "Slots" are sixteenths 0 to 15.

### 1. A spine: a few cells that are nearly certain

- **What.** Three cells of the bar that sound almost every time with the same kind of sound: weight on slot 0, a hard bright hit on slots 4 and 12.
- **Why.** All surprise is weighed against trust in the metre [C0, C3]. Omission on a strong beat is the largest error there is [C3 A2]. In the reference these three cells run at 0.89 to 0.94 while everything else moves [R-rhythm].
- **How.** Rank slices by role using what `chop.measure` already yields (level, punch, tonal). Reserve the lowest, heaviest slice class for slot 0 and the sharpest for 4 and 12, at a chance of 0.9 or more. This applies to any sound, not only drums: a chopped voice has a heaviest syllable and a sharpest consonant. If a drum layer already carries the spine, the chopped layer should *leave those cells to it* and not double them.
- **Measure.** Occupancy of the three cells over a window; metre precision as autocorrelation peak clarity of the low-band envelope [C6].
- **Edge.** Lower the chance. Near 0.9 it is the reference. One omitted downbeat per four or eight bars is the classic lip (the Amen's fourth bar). The reference tolerates about 0.65 in one band when another band holds the cell. Below that in all bands, or displaced every bar, the listener resets or hears noise. [thresholds below 0.65 unsourced]

### 2. Fixed odds, re-dealt: identity as a distribution

- **What.** Every slot of every lane has a chance of sounding. The chances stay put for a whole sub-section; each bar is a fresh deal.
- **Why.** Position odds are learned fast and pre-attentively [C3]; dense sound is remembered as statistics [19]. The reference has lag-1 similarity at the random baseline and within-section stability of 0.85 [R-rhythm].
- **How.** `deal.bar` does this for drums. Extend the same idea to slices: a table of chance per slot per slice *class*, held for 16 to 32 bars. The shape of the table is the identity: even slots near 0.67 to 0.85, odd slots near 0.34.
- **Measure.** Occupancy table per sub-section; correlation of first half against second half (target near 0.85); cells changed bar to bar (reference: 15 of 48).
- **Edge.** Flatten the table. The contrast between even and odd slots (0.75 against 0.34) is what keeps it from being a wall [R-rhythm rule 10]. As odd-slot chance rises toward even-slot chance the bar approaches maximum disorder and stops reading as a break. Independent re-dealing from the set-wide odds would change about 19 of 48 cells [computed]; the reference changes 15, so even the reference is a little more constrained than pure dealing.

### 3. Return of the group, not of the bar

- **What.** Four bars that all differ, in a fixed order, and the group comes back partly the same.
- **Why.** Four bars is 5.8 s, the span of the perceptual present and the grown unit of attention [C0, C3, C4]. Return after absence is a rewarded event in its own right [C0 §2d]. Reference: lag 4 = 0.486, lag 1 = 0.355.
- **How.** A share of each cell's deal belongs to its place in the group and the rest to the bar alone (`RETURNS` in `deal.py`). Make the share differ by band: more for the low band, less for the high, as measured. Add a weaker share at 8 and 16 bars. For chopped sound, replace "bar 3 is bar 1 again" with four different bars whose *group* is partly kept next time.
- **Measure.** Lag profile of bar-to-bar similarity. Targets: lag 4 about 0.13 above the same-section baseline, lag 1 at the baseline.
- **Edge.** The share. At 1 it is a four-bar loop; around 0.5 it is the reference; at 0 nothing returns and only the distribution holds (legible as texture, not as phrase).

### 4. One source, small palette

- **What.** A layer draws all its slices from one sound for a whole sub-section.
- **Why.** Source identity is available in under 50 ms [23]; timbre sequences are learned by exposure and related timbres group together [24]. The reference's break kicks vary hit to hit but stay inside one break [R-rhythm §10].
- **How.** One source per lane per sub-section; within it, a working window of a few neighbouring slices per phrase, moving on through the sound over time (as `chop.plan` already does). Change the source only on a slow clock (mechanism 7).
- **Measure.** Timbral distance between successive hits in a lane (reference: about 9 dB for a programmed kick, about 14 dB for a break kick); number of distinct sources sounding per bar.
- **Edge.** Number of sources at once, and how far processing moves a slice from its source. One transformation at a time (pitch, or reverse, or crush) keeps the source; stacked ones lose it. Slices under about 50 ms stop carrying phrase and carry only colour. [stacking claim unsourced]

### 5. An accent shape that holds while content changes, and reserved space

- **What.** Loud on the spine, medium on the other eighths, quiet and sparse on the odd sixteenths; hits cut short so every slot has an edge.
- **Why.** Accent, not presence, is what a listener fits a clock to [C3 A1]. Groove is shaped by sound and envelope more than by timing [C0 §3]. Paradox varies kick level deliberately and gates slice ends [1]. The reference keeps odd slots at 0.34 and every carrier hit decays before the next sixteenth [R-rhythm §9].
- **How.** A fixed gain template per slot applied to whatever slice lands there, with a small random spread; a hard gate at the slot boundary. Ghost material goes only on odd slots and only quietly.
- **Measure.** Mean level per slot against the template; share of hits whose tail clears before the next onset [C6]; the amplitude-weighted syncopation measure [C3 §b].
- **Edge.** Flatten the accents or let tails overlap. Equal-level sixteenths are the wall.

### 6. Displacement by rule, not placement by chance

- **What.** Variation made by moving, rotating, repeating and truncating what is already there.
- **Why.** Parallel construction lets a listener align two bars with different content [13]. Uneven groups such as 3+3+2 tell the listener where they are in the bar [2]. A single placed syncopation against a firm frame beats general displacement [6]. Rule-governed irregularity is what the practitioners describe [1, 3].
- **How.** A short list of moves, each applied by seed so that it can recur: shift a slice by 2 or 4 slots (the rotations the reference shows); cut in runs of 1 or 3 eighths that sum to the bar; keep runs of two to four slices in source order; repeat a slice at most twice; drop events; rotate which slice sounds while keeping the rhythm. Constrain more near slot 0, less toward the bar's end. Chain rules: "if the roll has happened twice in this group, answer it".
- **Measure.** Share of slices sitting on a slot of their own metric class; mean source-order run length; syncopation index per bar against the 0 / 4 / 18 scale [C3].
- **Edge.** Run length and move size. Seven-eighth runs reveal the original (too legible) [C3]; run length 1 with free placement is a scramble. Moves by odd sixteenths with no backing beat tip into reset.

### 7. Nested clocks, one per layer

- **What.** Each layer changes on its own slow period; they do not all change together.
- **Why.** Attention's unit grows, so change must exist at several scales [C1, C4]. The reference: surface every 8 to 16 bars, kick odds every 25 or so, carrier every 32, record every 40 to 190; only 36% of kick changes coincide with a carrier change [R-rhythm, R-structure].
- **How.** Give each lane a period drawn from 8, 16, 32 and a phase. At its tick the lane changes one thing: its odds table, its source, its working window, or its processing. Keep ticks on four-bar lines.
- **Measure.** Change points per lane; their spacing; share landing on multiples of four (reference: 100% within two bars); share coinciding across lanes.
- **Edge.** Shorten the periods or line the ticks up. A new table every bar never converges [C0]. Everything changing at once is a cut to a new record, legible once and tiring if frequent.

### 8. The low band owns time; lanes keep their registers

- **What.** One slow, trustworthy layer at the bottom; other lanes each in their own band.
- **Why.** The lowest stream is the timing reference [C4 A13]; low-frequency flux moves the head and bass-drum level moves the crowd [8, 16]. Reference: bass under 174 Hz, hooks 233 to 392 Hz with a valley between; the low band defines the four-bar unit [R-readme, R-rhythm].
- **How.** High-pass chopped material unless it is the low lane; give the sub the highest return share and the slowest clock; keep chopped lanes out of the hook band when a hook sounds.
- **Measure.** Band occupancy per lane; beat-locked share of low-band modulation energy [C4 §d].
- **Edge.** A chopped layer with strong low content that contradicts the sub steals the timing reference [C4]. That is the fastest way from lip to noise for a dancer.

### 9. A recurring gesture

- **What.** A short figure, a beat or so long, that comes back a few times and is then retired.
- **Why.** Dynamic expectation is built by motif [7]; contour survives transposition [24]; exact repetition of a vocal fragment makes it sing [21]. Reference hooks: 39% of bars, 1.2 beats, about three recurrences at four to eight bar spacing [R-readme].
- **How.** Choose a run of two to four slices (for voice, eighth-note slices, cut at onsets, so each is about a syllable). State it; bring it back four bars later *exactly*; allow a third return; then replace it. Between returns, cousins may share its contour or its rhythm but not both.
- **Measure.** Recurrence count and spacing of each shape; share of bars with a gesture.
- **Edge.** Exactness and count. Changing pitch or syllable order between returns removes the hook effect [21]. More than about three to eight returns is the boredom side [C0]. Sixteenth-length vocal slices cannot carry a phrase [computed].

### 10. Call and answer between lanes

- **What.** One lane's events predict another's at a fixed lag.
- **Why.** A relation is learnable in itself and stays legible when both sides vary [C6, relations]. Reference: break kick with moving bass, two-step with still bass; bass three bars on, one off, leaving the drums alone [R-readme, R-rhythm §10].
- **How.** Place slices in the gaps the kick leaves (already in `chop.plan`); make a lane's density the inverse of another's; let a hook be answered a fixed number of slots later by a slice of a second source.
- **Measure.** Conditional onset probability of B after A by lag; stable and high at one lag for four cycles or more counts as learned [C6].
- **Edge.** Jitter the lag, or let both lanes answer each other at once.

### 11. Phrase-end category

- **What.** Something happens at the end of some four-bar groups. What it is varies.
- **Why.** A change on the hypermetric grid is expected as a *kind of event* even when its content is new [C3 §d, C6]. Fill autocorrelation +0.19 at lag 4, one opportunity in four taken [R-rhythm].
- **How.** At bar 4 of a group, with chance about 0.25: a bar 1.2 times as dense and brighter, or a roll, or one empty sixteenth before the one, or the low end out. Larger events at 8, 16, 32.
- **Measure.** Autocorrelation of a fill indicator at lags 4 and 8; fill size as a ratio to a normal bar.
- **Edge.** Rate and size. A fill every four bars becomes pattern; a fill off the four-bar line reads as error.

### 12. Direction: a change the listener can extrapolate

- **What.** A parameter that moves steadily one way over several bars: the working window walking through the source, a filter opening, density rising, the low end draining.
- **Why.** A trajectory never repeats and is fully predictable; it is a pattern in slope [C6]. Butler notes a filter sweep redirecting which layer is heard as metrical [2]; hypermetric sweeps act as instructions [5]. The reference drains the low end over three to seven bars before a seam and ramps builds at 0.16 to 0.53 dB a bar [R-structure].
- **How.** Attach a slow ramp to one parameter per lane per section; end it on a four-bar line.
- **Measure.** Slope and monotonicity per bar; a trajectory that plateaus has "curdled" [C2].
- **Edge.** Reverse the slope mid-way, or run several ramps in opposing directions.

---

## 5. Dials for the edge

Each row is one parameter. Left is a dry sample, fully legible and soon dull. The middle is where the reference sits or where the sources place the optimum. Right is noise, tolerable briefly. Values in the middle column are from the reference unless marked.

| Dial | Fully legible | The lip | Noise |
|---|---|---|---|
| Spine chance (slots 0, 4, 12) | 1.0 | 0.89 to 0.94; one omitted downbeat per 4 or 8 bars | under about 0.6 in every band [unsourced] |
| Even to odd slot contrast | all on evens, none on odds | 0.75 against 0.34 | equal chances |
| Cells changed bar to bar (of 48) | 0 | 15 | 19 is independent dealing from set-wide odds [computed]; 24 is coin-tossing [computed] |
| Group return share | 1 (a loop) | about 0.5, giving lag 4 near 0.49 | 0 |
| Similarity at lag 1 against lag 4 | lag 1 high | lag 1 at baseline, lag 4 +0.13 | both at baseline |
| Cut unit at 166 BPM | bar or half bar | eighth (181 ms); sixteenth (90 ms) over a firm backing | sixteenths with no backing; anything shorter is grain |
| Source-order run length | 7 eighths or more | 2 to 4 slices [unsourced] | 1, freely placed |
| Syncopation per bar (0 / 4 / 18 scale) | 0 | about 4 [C3] | 18 |
| Sources per lane | 1, unprocessed | 1, one transformation at a time [unsourced] | several, stacked processing |
| Timbral distance hit to hit | about 9 dB (one sample) | about 14 dB (one break, re-dealt) | larger [unsourced] |
| Accent contrast | fixed template | template with small spread; ghosts on odd slots only | flat levels, overlapping tails |
| Layer change period | 32 bars or more | 8 to 16 for the surface, 25 to 32 per lane | every bar |
| Lanes changing at the same tick | one | sometimes two (36%) | all, often |
| Phrase-end events | none | one group in four, 1.2 times density | every bar, or off the four-bar line |
| Sixteenth carrier coverage | every bar | 7 bars in 10, gaps of 1 to 2 bars | under about 3 in 10 [unsourced] |
| Gesture returns | same figure throughout | about 3 exact returns at 4 to 8 bar spacing, then a new one | never returns, or returns altered every time |
| Vocal slice length | whole phrase | eighth (about a syllable), cut at onsets | sixteenth and below; reversal of slices over 100 ms |
| Timing spread on eighth positions | under 2 ms | 7.5 ms, with 13.5 ms inside slices | over about 16 ms on the spine [C1] |
| Low-band agreement with the sub | chopped lanes high-passed | some body down to 80 to 180 Hz | chopped low end contradicting the sub |

### How to turn them

1. **One dial at a time past the lip.** Because surprise is weighed by trust in the frame [C0], pushing one dial to its right-hand side is readable only while the others stay left of centre. The saddle says the same: a surprising event wants a certain context [C2]. A working budget [unsourced]: at most one dial past the lip per lane, at most two in the whole mix.
2. **Excursions have a length.** The owner's premise is that noise is tolerable briefly. The reference's own figures: carrier gaps of 1 to 2 bars; a doubled-drum burst of 2 bars; and, at the large scale, two blends of 8 to 32 bars where beat legibility falls by almost 40%, in 21 minutes [R-rhythm §9, R-structure §3]. So: one to two bars past the lip routinely, a long stand past it rarely and with a hard return.
3. **Return to full legibility on a four-bar line, with the spine and the low end.** That is what makes the excursion an event and not a fault: an expected arrival after uncertainty is one of the two rewarded corners [C2].
4. **Dwell before disturbing.** A state held for eight bars earns a larger disturbance than one held for two [C0 §2a]. A dial should sit still long enough for the listener's odds table to settle (about four cycles) [C3] before it moves.
5. **Mapping to the pads** [unsourced suggestion]. *Lock* raises spine chance, return share, change periods and carrier coverage; *restless* lowers them. *Derangement* shortens the cut unit and run length, raises syncopation, allows stacked processing and more simultaneous changes; *composed* reverses those. Neither pad should touch the spine chance of the low lane below the lip, or the dancer loses the floor.

### What to measure in the output, cheaply

All from the plan (what is played when), with no audio:

- occupancy per slot per lane over a sliding 16 or 32 bars, and its even-to-odd contrast;
- bar-to-bar similarity at lags 1 to 16, against a same-section random baseline;
- cells changed per bar;
- spine chance observed;
- syncopation index per bar;
- source-order run length and share of slices on their own metric class;
- change points per lane and how many coincide;
- gesture recurrence counts.

The reference gives a target for each of these [R-rhythm]. A plan whose lag-1 similarity is well above its baseline is repeating; one whose lag-4 similarity is at the baseline has no phrase.

---

## 6. What I could not find

- Any perceptual experiment on chopped breakbeats, or on chopped vocals, as such.
- Interviews with Fracture or Equinox on what makes an edit sound played; Tim Reaper on phrasing.
- A stated threshold for how strongly a metrical spine must be marked. The numbers in section 4 come from the reference measurement, which is one set.
- A figure for novelty per unit time that people enjoy.
- The text of Collins's breakbeat paper (the copy fetched would not render); its parameters here are as the owner's corpus records them.
- Full texts of Witek 2017, Burger 2018 and 2020, Van Dyck 2013, Toiviainen 2010, Abdallah and Plumbley, McDermott 2013, Saberi and Perrott, the speech-to-song papers and the auditory-gist papers: search summaries only, marked [snippet].
- Butler's book, London's book and Danielsen's books were not re-read; the corpus's account is relied on.

---

## 7. Sources

Read as pages:

1. "Paradox: Breakbeat Mastery", Ableton blog. https://www.ableton.com/en/blog/paradox-breakbeat-mastery/
2. Butler, M. J. (2001). Turning the Beat Around: Reinterpretation, Metrical Dissonance, and Asymmetry in Electronic Dance Music. *Music Theory Online* 7.6. https://www.mtosmt.org/issues/mto.01.7.6/mto.01.7.6.butler.html
3. Autechre interview, *Sound on Sound*. https://www.soundonsound.com/people/autechre
4. Livecut README (cut, block, phrase hierarchy only). https://github.com/mdsp/Livecut
5. Smith, J. (2021). The Functions of Continuous Processes in Contemporary Electronic Dance Music. *Music Theory Online* 27.2. https://mtosmt.org/issues/mto.21.27.2/mto.21.27.2.smith.html
6. Sioros, G., Miron, M., Davies, M., Gouyon, F. & Madison, G. (2014). Syncopation creates the sensation of groove in synthesized music examples. *Frontiers in Psychology* 5:1036. https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2014.01036/full
7. Aversa, review of Huron, *Sweet Anticipation* (2006). *Music Theory Online* 15.3-4. https://mtosmt.org/issues/mto.09.15.3/mto.09.15.3.aversa.html
8. Burger, B., Thompson, M., Luck, G., Saarikallio, S. & Toiviainen, P. (2013). Influences of rhythm- and timbre-related musical features on characteristics of music-induced movement. *Frontiers in Psychology* 4:183. https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2013.00183/full
9. TidalCycles reference, "Alteration". https://tidalcycles.org/docs/reference/alteration/

From search summaries only [snippet]:

10. Huron, D. (2006). *Sweet Anticipation*. MIT Press. https://mitpress.mit.edu/9780262582780/sweet-anticipation/
11. Collins, N. BBCut library; "Algorithmic Composition Methods for Breakbeat Science" (2001). https://composerprogrammer.com/research/acmethodsforbbsci.pdf ; BBenCut description: https://github.com/bencodec/BBenCut
12. Toussaint, G. (2005). The Euclidean Algorithm Generates Traditional Musical Rhythms. https://cgm.cs.mcgill.ca/~godfried/publications/banff.pdf
13. Lerdahl, F. & Jackendoff, R. (1983). *A Generative Theory of Tonal Music*; parallelism rules as quoted in Sullivan, *Music Theory Online* 30.4. https://mtosmt.org/issues/mto.24.30.4/mto.24.30.4.sullivan.html
14. Toiviainen, P., Luck, G. & Thompson, M. (2010). Embodied meter: hierarchical eigenmodes in music-induced movement. *Music Perception* 28(1). https://converis.jyu.fi/converis/portal/detail/Publication/20027390
15. Burger, B. & Toiviainen, P. (2020). Embodiment in Electronic Dance Music. *Musicae Scientiae* 24(2). https://journals.sagepub.com/doi/abs/10.1177/1029864918792594
16. Van Dyck, E. et al. (2013). The Impact of the Bass Drum on Human Dance Movement. *Music Perception* 30(4). https://www.researchgate.net/publication/259731535
17. Witek, M. A. G. et al. (2017). Syncopation affects free body-movement in musical groove. *Experimental Brain Research* 235(4). https://pubmed.ncbi.nlm.nih.gov/28028583/
18. Abdallah, S. & Plumbley, M. (2009). Information dynamics: patterns of expectation and surprise in the perception of music. *Connection Science* 21. https://www.tandfonline.com/doi/full/10.1080/09540090902733756
19. McDermott, J. H., Schemitsch, M. & Simoncelli, E. P. (2013). Summary statistics in auditory perception. *Nature Neuroscience* 16(4). https://mcdermottlab.mit.edu/papers/McDermott_Schemitsch_Simoncelli_2013_summary_statistics.pdf
20. Herremans, D., Chuan, C.-H. & Chew, E. A Functional Taxonomy of Music Generation Systems. https://arxiv.org/pdf/1812.04186 ; Fernández & Vico, AI Methods in Algorithmic Composition. https://arxiv.org/pdf/1402.0585
21. Speech-to-song: Deutsch, Henthorn & Lapidis (2011), via the corpus [C4]; Rowland, Kasdan & Poeppel (2019), *Psychonomic Bulletin & Review* 26. https://link.springer.com/article/10.3758/s13423-018-1527-5 ; overview: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5993277/
22. Saberi, K. & Perrott, D. (1999). Cognitive restoration of reversed speech, as summarised in https://pmc.ncbi.nlm.nih.gov/articles/PMC6156149/
23. Suied, C. et al. (2014). Auditory gist: recognition of very short sounds from timbre cues. Isnard, V. et al. (2019). The time course of auditory recognition measured with rapid sequences of short natural sounds. https://pmc.ncbi.nlm.nih.gov/articles/PMC6541711
24. Tillmann, B. & McAdams, S. (2004). Implicit learning of musical timbre sequences. https://pubmed.ncbi.nlm.nih.gov/15355141/ ; Dowling, W. J. & Fujitani, D. (1971) on contour, as summarised in https://link.springer.com/content/pdf/10.3758/BF03203924.pdf
25. Danielsen, A. (2006). *Presence and Pleasure*. https://www.researchgate.net/publication/261833217
26. Amen break structure: https://www.ethanhein.com/wp/2023/building-the-amen-break/ ; https://www.audiolabs-erlangen.de/resources/MIR/2016-IEEE-TASLP-DrumSeparation/AmenBreak
27. Drum fill function (teaching sites, non-academic): https://hackmusictheory.com/blogs/theory/posts/6777255/3-types-of-drum-fills
28. Tim Reaper interviews and AMA: https://ontheriseacademy.com/what-we-learned-from-tim-reapers-ama/ ; https://www.loudandquiet.com/interview/real-strong-bass-tim-reaper-is-londons-most-in-demand-junglist/
29. McLean, A. (2014). Making Programming Languages to Dance to: Live Coding with Tidal. https://slab.org/tmp/p63.pdf
30. Hockman, J. (2014). An ethnographic and technological study of breakbeats in hardcore, jungle and drum & bass. PhD, McGill. https://mcgill.scholaris.ca/items/04241a9f-5b5c-45e7-9fe9-bb277bce4325
31. Burger, B., London, J., Thompson, M. & Toiviainen, P. (2018). Synchronization to metrical levels in music depends on low-frequency spectral components and tempo. *Psychological Research*. https://doi.org/10.1007/s00426-017-0894-2 (findings not retrieved; not relied on)
32. Autechre's generative practice, secondary accounts: https://www.musicradar.com/news/pioneers-autechre ; https://en.wikipedia.org/wiki/Confield

### Arithmetic used [computed]

- At 166 BPM: beat 361 ms; sixteenth 90 ms (11.1 per second); eighth 181 ms (5.5 per second); bar 1.446 s; 4 bars 5.8 s; 8 bars 11.6 s; 16 bars 23.1 s; 32 bars 46.3 s; half-time beat 83 per minute.
- Disorder of a set-wide bar, cells taken as independent: binary entropy of 0.85 is 0.61 bits, of 0.67 is 0.92, of 0.34 is 0.93. Four beat slots, four other even slots, eight odd slots: 4 × 0.61 + 4 × 0.92 + 8 × 0.93 = 13.5 bits of a possible 16 per band. Per-section tables are sharper than the set-wide one, so real sections are lower; the point is the order of magnitude.
- Cells expected to differ between two bars dealt independently from those odds: 2p(1−p) is 0.255, 0.442 and 0.449 for the three slot classes; mean over 16 slots 0.40; times 48 cells, about 19. Measured: 15.
