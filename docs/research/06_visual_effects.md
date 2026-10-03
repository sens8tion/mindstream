# 06. The best visual effects in use for live music, and how each is built

Written 2026-10-02. Secondary research from the web, plus a reading of mindstream's own effect code
(`mindstream/fx.py`, the shaders in `gl_view.py`, `mindstream/effects.py`) so that the existing sixteen could be
judged on what they actually do. Nothing was run, timed or looked at on screen.

How to read the marks:

- **[n]** a numbered source in the list at the end. Unmarked next to a number means I read the page itself.
- **[snippet]** the claim rests on a search-result summary, or the page would not load. Treat as a lead.
- **[computed]** my own arithmetic from numbers given elsewhere in this file.
- **[unsourced]** my belief, inference or memory of a paper I could not fetch. Nothing I read supports it directly.
- **[code]** read in mindstream's own source.

Target throughout: OpenGL 3.3 core, GLSL 330, no compute shaders, float render targets, several render targets
at once, ping-pong framebuffers, texture fetch in the vertex shader, instancing, transform feedback. The screen
is 3440 x 1440 at 60 Hz: 4,953,600 points, 16.7 ms a frame [computed]. All costs are estimates in texture reads
per frame and are **[unsourced]** as timings: no benchmark was run.

---

## One-page summary

**What the field uses.** Three families recur in every tool and every account read, and mindstream has only the
third of them properly:

1. **Things that remember** (feedback, fluid, reaction-diffusion, datamosh, slit-scan, pixel sort, stateful
   particles). The picture goes into a buffer that carries on by its own rules, and the source is fed back in at
   a controlled rate. MilkDrop is nothing but this [11]; the analogue video-synth look is this [13]; Notch ships
   Frame Feedback, Motion Datamosh, Slit Scan and Pixel Sort as stock nodes [3]; TouchDesigner tutorials are
   dominated by the feedback loop [7, 10]; the camera-to-fluid-to-particles chain is a packaged tool [14].
2. **Space remapped** (kaleidoscope, polar, Droste, Moebius, tunnel, raymarched fractal scenes). Stock nodes in
   Notch [3] and Resolume [2]; the staple of Shadertoy and of 64k intros [64, 65].
3. **Lens and print** (bloom, streaks, depth of field, grain, halftone, CRT and VHS, grading). Every tool has
   these and every demoscene post chain ends with them [65]. Mindstream has most of this family already.

**The single most useful finding for this project.** Every effect in family 1 has one parameter that is the
*pull back to the source*: the rate at which the true picture is re-injected (dye re-injection in a fluid,
refresh in a datamosh, the home spring on particles, the source mix in feedback). That parameter is exactly
the owner's "nearly lost and then returns". One control mapped to those rates, moved on phrase lines, is the
edge of legibility as a dial. The effects mindstream has now are almost all stateless filters; they can
obscure a picture but they cannot *lose it and find it again*.

**The second.** Mindstream makes its own music, so it knows every kick, snare and phrase line exactly. The
best-synchronised show found (Noisia's Outer Edges) did not analyse audio at all: every beat and sound sent a
cue [16]. Drive the visuals from the plan, not from a spectrum.

**The third.** The pipeline itself is the cheapest thing in the present viewer. Pictures are uploaded as plain
8-bit and never linearised; the scene and the trail buffer are 8-bit; there is no tone map and no dither
[code]. In an 8-bit feedback loop a fade of 0.985 a frame cannot take any value below 33 of 255 lower, so
trails stall at a grey floor instead of fading out [computed, section 6.0]. Fixing this is worth more than any
one new effect, and every effect below assumes it.

### Ranked shortlist: what to build first

| rank | build | why first |
|---|---|---|
| 0 | **Linear HDR pipeline** (sRGB decode, 16-bit float everywhere, one tone map, blue-noise dither) | everything else is judged through it; removes banding, stalled trails and clipped glow; small change |
| 1 | **Motion vectors + datamosh** (E02) | the purest "lost and returns" effect; the surface and cube can output exact motion for free; a film's own motion carries the previous picture |
| 2 | **Feedback synth, done properly** (E01) | the most used live look of all; mindstream has a thin version; float buffers, sharper resampling, luminance displacement and hue rotation turn it into an instrument |
| 3 | **Fluid with the picture as dye** (E03) | the signature look of the stage tools; cheap at simulation size; re-injection rate is a legibility dial; kicks are forces |
| 4 | **Stateful particles** (E04) | the two million points exist but have no memory; give them positions, a home in the picture and a spring, and the picture can blow apart and reassemble |
| 5 | **Slit-scan / time displacement** (E05) | unlike anything in the present set; made for film; delays quantised to sixteenths lock it to the grid |
| 6 | **Beat strobe, invert and palette cycling with a flash limiter** (E10) | trivial cost; expected in the genre; needs the safety limiter written once, for everything |
| 7 | **Reaction-diffusion seeded by the picture** (E06) | grows the picture's edges into living pattern; pairs with relief shading |
| 8 | **Conformal remaps: Droste, Moebius, hyperbolic, better kaleidoscope** (E07) | one pass each; exact maths; the present kaleidoscope is the cheap kind |
| 9 | **Relief from luminance: lighting, parallax, focus** (E08) | makes a flat picture an object; gives depth of field something real to work on |
| 10 | **Pixel sorting** (E09) | the canonical glitch look; no compute shader needed |
| 11 | **Fractal scenes with the picture projected from a home camera** (E12) and **volumetric light** (E13) | the heavy, high-end family; the card has room; projection gives a built-in return to legibility |
| 12 | **Anisotropic Kuwahara, flow-based lines, strand fields** (E15, E14) | replaces the cheap oil paint and Sobel edges with the versions the papers describe |
| 13 | the rest: CRT/VHS (E16), glyphs and dither (E17), terrain (E18), iridescence (E21), transitions (E11), lens flares (E24), motion blur and temporal accumulation (E25) | each is small; build as wanted |

**How well sourced.** The simulation and lens maths rest on primary technical sources that were read (GPU Gems,
Karl Sims, LearnOpenGL, Catlike Coding, Inigo Quilez, the MilkDrop guide). "What is used" rests on tool manuals
and a handful of interviews: good evidence of what exists and recurs, weak evidence of how often. No source
ranks effects by use. Every timing is an estimate. Section 7 lists what could not be found.

---

## 1. What is actually used

### 1.1 The tools, and what their stock effect lists say

A tool's stock node list is the best evidence found of what working artists reach for, because vendors ship
what is asked for.

**Notch** (the standard for concert camera effects and generative stage content since about 2016 [5, snippet 6]).
Its post-effect list [3], grouped here by family, with the ones mindstream lacks in bold:

- remembering: **Frame Feedback**, **Feedback Blur**, **Motion Datamosh**, **Slit Scan**, **Pixel Sort**,
  **Frame Delay / Frame Loop / Frame Difference**, **Water Ripples** (a simulation), Streaks, **Vector Blur**
- remapping: **Droste Warp**, **Moebius Warp**, **Polar Warp**, **Mirror**, **Twirl**, **Curl Noise Warp**,
  **Turbulence Warp**, **Sine Warp**, **Randomise Tiles**, Barrel Distortion, Ripple, **Bump Map Warp**
- stylising: Kuwahara, **Median**, Edge Detect / Outlines, Halftone, **Dot Matrix**, **Cross Hatch**,
  **Dither**, **Bit Crush**, **Pixelate**, **Block Glitch**, **Chroma Glitch**, **VHS Scanlines / VHS Blur**,
  **Voronoi Post Process**, **Colour Reduce**
- colour: **Strobe**, **Invert**, **Tritone**, **Apply Colour LUT**, Colour Grading, **Tone Map**,
  **Local Contrast**, Tint
- lens: Glow, Glow 2, **Physical Glow**, **FFT Blur/Glow**, **Physical Lens Flare**, Film Grading (with
  chromatic aberration), Tilt Shift, Radial and Directional Blur

Its particle system is built from emitters, affectors and renderers; the affectors include a curl-noise fluid,
a field affector and three fluid solvers [snippet 4]. A reviewer calls particles the tool's most approachable
strength and describes "fields" (a voxel grid) as its way to smoke and cloud [5].

**Resolume** ships over a hundred video effects and can bind any parameter to an audio spectrum band [1]. A
working VJ's list of the ones to learn first: Displace (by a map), Kaleido, Wave Warp, RGB Delay (channel
separation in time), Mirror and Flip, Shaper, Edge Detection, and its particle system [2]. Audio-reactive hue
rotation is singled out by another as a first staple [snippet, search result for a VJ tutorial].

**TouchDesigner.** The feedback loop is the idiom: a Feedback operator re-reads a downstream result, and
whatever sits on that wire (transform, blur, level, displace) is applied again every frame [7, snippet 10]. The
Time Machine operator is slit-scan and time displacement in one: a stack of past frames, and a grey map that
says how old each point should be [8]. The Optical Flow operator outputs motion in red and green as 32-bit
floats and is documented as a driver for the GPU particle system [9].

**MilkDrop** (the music visualiser that set the look for two decades). One frame is: evaluate motion equations
on a coarse mesh; draw last frame warped by that mesh, with decay; draw waves and shapes on top; make three
blurred copies; composite to screen [11]. Its motion variables are the whole vocabulary of feedback: zoom
(1.01 is one percent a frame), rotation, translation, stretch, a warp amount, a centre, a decay (0.98 is the
guide's suggestion) and an echo layer [11].

**Synesthesia** (a shader-based VJ tool) is the clearest statement of audio-reactive practice: see 1.4 [12].

**Analogue-style video synths** (Lumen and the hardware it imitates): oscillators, a keyer, a transform, and
feedback, including pointing a camera at the output [snippet 13].

**openFrameworks' ofxFlowTools**: camera, then optical flow, then a 2D fluid, then particles, described by its
author as a kit for psychedelic live visuals [14]. This chain (motion in, fluid, particles out) recurs in
TouchDesigner practice too [9].

**Unreal on stage.** Used for real-time generative content that responds to the players, for example Moment
Factory's work for Phish at Sphere [snippet 22]; audio-driven particle and smoke systems are sold as packs
[snippet 22].

### 1.2 Stage and club practice in drum & bass and nearby

- **Noisia, Outer Edges** (shown at Let It Roll and Rampage, the two largest drum & bass events). Ableton sends
  a MIDI note for every beat and sound; a patch turns notes into messages; TouchDesigner translates them for
  Resolume and the lighting desk. Each track is split into five elements (beats, snares, melody, effects and so
  on), one video layer each, with clips triggered and opacities moved by the notes. The content was made by
  ten motion designers; one piece took thirty minutes and was kept for its boldness [16]. **The lesson: the
  sync is event-exact and per element; the content is bold and simple.**
- **Let It Roll, Rampage.** Fast graphics, flashes on snare rushes and drops; strobe at the drop for about a
  second and then back to colour or darkness [23]. A guide to bass-music visuals advises quick cuts and stutter
  for drum & bass but distinct shapes that still read, motion blur rather than flashing to convey speed, and
  several seconds of darker picture after any white flash [23].
- **Weirdcore for Aphex Twin.** Mixed live: crowd footage through face-mapping, depth-camera point clouds,
  glitch, with the stated aim of overload [17, snippet 18]. This is the nearest precedent for "the edge of
  legibility": recognisable faces, corrupted in real time.
- **Flying Lotus, Layer 3.** Two projection surfaces, a transparent scrim in front and a screen behind, played
  live by two visual artists [snippet 19]. Depth by layering rather than by rendering.
- **Tarik Barri's Versum** (for Thom Yorke and others): a self-written 3D world steered in real time [snippet 20].
- **Eric Prydz, HOLO.** Large pre-rendered 3D animation per track on a gauze, triggered live [snippet 21]. The
  accounts disagree on how much is live.

### 1.3 Shader artists and the demoscene

- Rendering in size-limited intros is mostly raymarching of signed distance fields, commonly with the hg_sdf
  operator library (repetition, mirroring, polar repetition, folds, and shaped unions) [64, 65].
- One documented 64k intro's post chain, in order: shade; depth of field (three passes of rotated blurs); bright
  extraction; Gaussian bloom; lens flares after Chapman; composite; anti-aliasing; colour grade and grain [65].
- The recurring Shadertoy subjects are raymarched fractals (kaleidoscopic IFS, Mandelbulb, Mandelbox, Menger),
  tunnels, metaballs and volumetric clouds [snippet 86]. The site itself blocked fetching.
- Volumetric clouds done well cost on the order of a hundred steps a ray with half a dozen light steps each
  [snippet 55]; a tutorial version gets by on 50 and 6 with blue-noise jitter and accumulation over frames [54].

### 1.4 Audio-reactive practice

**What the tools expose.** Synesthesia's set is the most complete [12] and is a good design for mindstream's own
uniforms:

| kind | what it is | what it is for |
|---|---|---|
| level (all, bass, mid, mid-high, high) | smoothed loudness per band, 0 to 1 | size, brightness, amounts |
| hits (per band) | transient spikes | drum hits |
| **time (per band)** | a clock that runs faster when that band is loud | **motion speed without jitter: position is the integral of level** |
| presence (per band) | slow "is this band in the track at all" | section-level changes |
| on-beat, toggle-on-beat, random-on-beat, beat count | a spike; a flip-flop; a new random number each beat; a counter | flashes, alternation, re-seeding, counting bars |
| tempo waves | sine and triangle at 1, 2, 4, 8 beats | drift locked to tempo |
| intensity, fade-in-out | very slow accumulators | the arc of a tune |

MilkDrop gives bass, mid and treble **relative to their own running average** (about 0.7 to 1.3, with 1.0
meaning normal) and slower-moving copies of each; its guide says to drive zoom from the slow copy [11]. Relative
levels are what make one mapping work across quiet and loud material.

**What goes to what**, from a routing guide [25] and a festival guide [snippet 24]:

- bass or kick: scale, zoom, large geometric pulses, strobe
- snare and clap band (about 150 to 250 Hz for the body): white flashes, rotations
- mid: colour shifts
- highs (3 to 10 kHz): sparkle, line width, thin line art
- overall loudness: master intensity and glow
- detected beat: scene changes and flashes, not continuous amounts
- spectral brightness: palette position
- the common mistake: every parameter on the bass, which gives one motion at several sizes [25]; and raw bands
  on slow parameters, which jitter [25]

**Envelopes.** An attack-and-release follower with different rates up and down is the standard: about 1 ms
half-life up and 20 to 100 ms down for percussion [26].

**What follows for 160 to 175 BPM** [computed unless marked]:

| | 160 | 170 | 175 |
|---|---|---|---|
| beat | 375 ms, 22.5 frames | 353 ms, 21.2 frames | 343 ms, 20.6 frames |
| sixteenth | 94 ms, 5.6 frames | 88 ms, 5.3 frames | 86 ms, 5.1 frames |
| bar | 1.50 s | 1.41 s | 1.37 s |
| four bars | 6.0 s | 5.6 s | 5.5 s |
| beats per second | 2.67 | 2.83 | 2.92 |

- A sixteenth is about five frames. An accent meant to articulate sixteenths must be over in two or three:
  time constant about 25 to 40 ms. Anything slower merges into a level.
- An envelope that should fall to a tenth before the next beat needs a time constant near 150 ms; before the
  next sixteenth, near 38 ms.
- A trail that halves in one beat at 170 needs a per-frame decay of 0.968; in one sixteenth, 0.877; in one
  bar, 0.992. The present trail range (0.80 to 0.985) [code] spans a twentieth of a second to three quarters
  of a second: it cannot hold a trail for a bar.
- **Flash safety.** The accessibility threshold is three general flashes in any second, a flash being a pair of
  opposing luminance changes of a tenth of full range or more, counted when the flashing area exceeds about a
  quarter of a ten-degree field; saturated red has its own equal limit [30]. Broadcast rules are of the same
  form [snippet 31]. Beats at 160 to 175 come 2.7 to 2.9 times a second: **one full-screen flash per beat is
  only just inside the limit, and anything on eighths or sixteenths is far outside it.** So: full-field
  brightness changes belong to the half-time backbeat or rarer; sixteenth-note accents must be local (a small
  area), or not luminance at all (displacement, hue, a line, a block). This matches what the body follows: the
  companion report on legibility puts the dancer's level at the half-time pulse [04].
- Darkness is the other half of a flash: both the festival guide and a VJ's own advice say to follow intensity
  with dark, and that dark is what gives light its force [23, 27].

**For mindstream specifically** [unsourced, but it follows from 16]: the sequencer already knows the kick, the
snare, each lane's events, the step, the bar and the phrase. Pass those as uniforms (an envelope per lane, a
beat phase, a bar phase, a phrase phase, a per-lane counter and a per-beat random) and keep spectrum analysis
only for film sound that the plan does not describe.

---

## 2. The effects, one entry each

Each entry: the look and who uses it; passes and buffers; the mathematics and parameters; what the good version
does that the cheap one does not; pitfalls; cost; music; legibility. "Fits" says how it sits inside the 3.3
limits.

Notation: S is the source picture (after the surface or cube is drawn), x a point in the frame, dt the frame
time, L luminance. "Ping-pong" means two textures swapped each step. Sizes: full = 3440 x 1440 (4.95 M points),
half = 1720 x 720 (1.24 M), quarter = 860 x 360 (0.31 M) [computed].

### E01. Feedback synth (the video-synth loop)

**Look and use.** The frame is fed back into itself through a small transform: trails that spiral, bloom
outward, shear, shift hue as they age and fold into mandalas. The basis of MilkDrop [11], of the analogue
video-synth look [snippet 13], of Notch's Frame Feedback [3] and of most TouchDesigner pieces [7, 10].
Mindstream has a first version (zoom, swirl, kaleidoscope fold, a noise drift, a fade) [code].

**Passes and buffers.** One ping-pong pair of RGBA16F at full size. One pass:
`F_n(x) = g( decay * F_(n-1)( T(x) + d(x) ) ) + mix-in of S`.

**Mathematics and parameters.**
- T: rotate by a about a centre c, scale by z, translate. Per frame at 60 Hz: z from 0.97 to 1.03 (MilkDrop's
  1.01 is a strong zoom [11]); a up to about 1 degree; make both per-second rates and convert with dt so the
  look does not change with frame rate: `z = exp(rate_z * dt)`.
- A mesh of T rather than one T: MilkDrop evaluates zoom, rotation and warp per mesh vertex, so the edges can
  zoom faster than the middle (a perspective tunnel) or rotation can reverse with radius [11]. In a fragment
  shader this is simply T as a function of x.
- d(x): displacement by the frame's own content. The classic choices: along the luminance gradient
  (`d = k * grad L`, k about 1 to 8 points), or by luminance as an angle
  (`d = k * (cos 2 pi L, sin 2 pi L)`). This is what makes the image crawl like oil.
- Colour per pass: rotate hue by 0.5 to 3 degrees (a rotation about the grey axis in linear RGB), or a small
  channel leak; saturate slightly more than 1 to stop the loop greying out.
- decay: 0.90 to 0.995; choose by half-life: `decay = 0.5^(dt / half_life)`.
- Blur and sharpen inside the loop: a little blur plus a little unsharp mask each pass makes the loop grow
  spots and stripes of its own (it becomes a reaction-diffusion system) [unsourced]. MilkDrop keeps three blur
  levels available to the loop for this [11].
- Mirrors and folds applied to T(x) give the kaleidoscope trail.
- Source mix-in: `F = max(F, S * key)` or `mix(F, S, a)` with a keyed on S's luminance; a from 0.02 (source
  nearly lost in its own echo) to 1 (no feedback).

**The good version.**
- 16-bit float, linear light. In 8 bits a decay of d cannot lower any value below 0.5 / (1 - d): 33 of 255 at
  0.985, 25 at 0.98 [computed]. Trails then end in a flat grey floor.
- Resample the previous frame with a sharper filter than bilinear (Catmull-Rom, 9 reads by the bilinear
  trick [44]); bilinear applied sixty times a second is a blur that sets the look whether wanted or not.
- A soft limiter in the loop (`F / (1 + F/k)` per channel or on luminance) so additive paths cannot run away.
- Displacement from a blurred copy (a bloom level), so the motion field is smooth.

**Pitfalls.** Blow-out when gain round the loop exceeds one. The mirrored-repeat wrap now set on the targets
[code] makes off-screen samples fold back in, which is a look in itself; black borders are the alternative.
Anything drawn into the loop (grain, dither, overlay text) is amplified: keep those after it.

**Cost.** One full-size pass of 9 to 20 reads: trivial.

**Music.** Kick: a zoom impulse (z jumps and relaxes over 150 ms). Snare: a rotation step or a hue jump. Bass
level through a time accumulator: rotation speed. Phrase: change the sign of zoom, the fold count, the centre.
Bar-long decay on a build, short decay on the drop.

**Legibility.** The source mix a is the dial. With a small and decay long the picture is a memory of itself.
Returning is instant (raise a), so it can come back exactly on a downbeat.

**Fits.** Entirely. One fragment pass.

### E02. Motion vectors, optical flow and datamosh

**Look and use.** The "P-frame smear": a picture stops refreshing and is instead dragged around by the motion of
what should have replaced it. Faces melt along the direction things move; a cut does not cut, the old image
wears the new one's movement. A stock node in Notch [3]; a well-known Unity effect built on engine motion
vectors [72, 73].

**How the real thing works** [72]. Compressed video sends occasional whole pictures and, between them, motion
vectors per block plus a correction. Remove a whole picture, and the decoder applies the next frames' motion to
the wrong image.

**Passes and buffers.**
1. A motion field V (RG16F, points per frame). Three sources, best first:
   - **Exact vectors from the geometry.** The surface and cube are drawn by mindstream itself. Give the vertex
     shader last frame's matrices and shape as well as this frame's; output both clip positions; write
     `(now.xy / now.w - before.xy / before.w) * 0.5 * size` to a second colour attachment. This is what the
     engines do [72, 44], it costs almost nothing, and it is exact. The same buffer serves motion blur (E25)
     and temporal accumulation.
   - **Optical flow** for motion inside a film (the picture changing within the surface): see below.
   - **Synthetic flow**: a curl-noise field, or the fluid's velocity (E03), when the source is still.
2. The moshed image M: one ping-pong pair, RGBA16F, full size.
3. Optional: a block-quantised copy of V at 1/16 size (a "macroblock" grid).

**Mathematics.**
- Mosh step: `M_n(x) = M_(n-1)( x - gain * Vb(x) )` where Vb is V read at the centre of x's block (block size
  B of 8 to 32 points; 16 is the codec's own [unsourced]); gain 1 for faithful, up to 3 for exaggerated.
- With correction (closer to a real decoder, and prettier): `M_n = warp(M_(n-1)) + q( S_n - warp(S_(n-1)) )`,
  q a quantiser or simply a gain of 0 to 1. At gain 1 and with true vectors M tracks S exactly; lower it and
  the wrong image persists but takes on the new one's changes.
- Refresh ("I-frame"): `M = S` everywhere on a chosen bar line; or per block with a small probability each
  frame (0.1 to 5 percent), which is the slow healing; or where the block's motion is below a threshold (still
  areas refresh, moving areas smear), which is the per-block noise and threshold the Unity write-up
  recommends [72].
- "Bloom" mosh: hold one V for many frames and keep applying it; the image streams in one direction.
- Optical flow in a fragment shader (what the creative-coding flow shaders do [14, 15]): on two consecutive
  frames, blurred and reduced to quarter size, take the time difference It and the spatial gradient (Ix, Iy)
  at an offset of 1 to 3 points; `V = - It * (Ix, Iy) / (Ix^2 + Iy^2 + lambda)`. lambda (regularisation) and
  the offset are the two controls [14, 15]; then threshold small magnitudes and smooth in time [15].
- The better flow: a 5 x 5 window least-squares solve (sum the products Ix Ix, Ix Iy, Iy Iy, Ix It, Iy It over
  the window and solve the 2 x 2 system), done coarse to fine over 3 to 5 pyramid levels, warping the second
  frame by the coarser level's answer before each solve; then a few smoothing iterations of the form
  `u = mean(u) - Ix (Ix mean(u) + Iy mean(v) + It) / (alpha^2 + Ix^2 + Iy^2)` [snippet 84, unsourced as to
  the exact recipe]. Gradient methods only see motion of about a point or two at the scale they work at,
  which is why the pyramid matters.

**The good version.** True vectors where they exist; blocks with per-block randomness in refresh; the
correction term; float buffer; a hold that is musical (refresh on the one, mosh through the bar).

**Pitfalls.** Flow from compressed or noisy film is noisy: blur first, threshold after. Sampling outside the
frame: clamp and let edges streak, or refresh there. Sub-point bilinear drift blurs M over time; snap the
displacement to whole points for the hard codec look, or leave it for the soft one.

**Cost.** Vectors: free. Flow at quarter size over four levels: under 20 M reads. Mosh: one full pass.

**Music.** Refresh on phrase lines; block refresh probability from the high band; gain from bass; hold a single
V through a fill (the stream), release on the one. A snare can force a refresh of a random third of blocks.

**Legibility.** The refresh rate is the dial, and the return is a hard, satisfying snap when the true picture
is restored on a downbeat. During the smear the old picture's colours and the new one's motion are both
legible separately: one thing wrong, the rest firm.

**Fits.** Entirely: a second colour attachment for vectors, ping-pong for M.

### E03. Fluid simulation with the picture as dye

**Look and use.** Ink and smoke: the picture's colours are carried by a swirling incompressible flow, curling
into filaments, and continuously re-formed. The stage tools' signature (Notch's fluid affectors and fields
[snippet 4, 5]; the flow-to-fluid chain [14]).

**Passes and buffers** (after GPU Gems chapter 38 [33]). All ping-pong:
- velocity u: RG16F, quarter to half size
- pressure p: R16F, same size
- divergence and curl: R16F, single
- dye: RGBA16F at full or half size (it may be finer than the velocity; a common arrangement [unsourced])

Per frame, in order [33]: advect u; add forces; (vorticity confinement); compute divergence; solve pressure by
Jacobi iteration; subtract the pressure gradient; advect dye.

**Mathematics** [33].
- Advection (stable for any step): `q'(x) = q( x - dt * u(x) )`, bilinear.
- Divergence: `div = 0.5 * (u_right.x - u_left.x + u_up.y - u_down.y) / h`.
- Pressure, repeated: `p' = (p_left + p_right + p_down + p_up - h^2 * div) / 4`. The chapter recommends 40 to
  80 iterations and no fewer than 20 [33].
- Projection: `u -= 0.5 * grad p / h`.
- Viscosity (optional; usually skipped): the same Jacobi form with alpha = h^2 / (nu dt), divisor 4 + alpha.
- Vorticity confinement: `w = curl u`; `N = normalize(grad |w|)`; force `= eps * h * (N.y * w, -N.x * w)`.
  It puts back the small swirls that advection smears away; eps about 0.1 to 0.5 in grid units [33, range
  unsourced].
- Edges: velocity negated and pressure copied at the border for a closed box [33], or simply clamp and let the
  flow leave.
- Dissipation: multiply velocity by 0.98 to 0.999 and dye by 0.97 to 0.999 per frame (by half-life, as E01).

**Feeding it the picture.**
- Dye re-injection: `dye = mix(dye_advected, S, r)`, r from 0.002 (the picture is a rumour) to 0.2 (it holds
  its shape and only its edges smoke).
- Forces from the picture: push along or across the luminance gradient; or buoyancy (bright rises).
- Forces from the music: a radial impulse from a point on each kick (a Gaussian splat of velocity, radius 5 to
  15 percent of height); a pair of counter-rotating splats on a snare; a slow stirring field always.
- Motion vectors (E02) added as force: the cube's rotation stirs the ink it is drawn in.

**The good version.** Start each solve from last frame's pressure (fewer iterations for the same result
[unsourced]); back-and-forth error-corrected advection for the dye, which keeps filaments sharp (GPU Gems 3,
chapter 30 [35, not fetched]); dye at full size with Catmull-Rom reads; vorticity confinement on; shade the dye
as a surface (take a normal from the dye's luminance and light it, E08) for the "liquid metal" look
TouchDesigner tutorials sell [snippet 10].

**Pitfalls.** Too few pressure iterations makes the flow compress and the dye pile up; forces too large for the
grid make chequerboard noise; dye with no re-injection becomes mud in about ten seconds; bilinear advection of
dye every frame is a blur.

**Cost** [computed]. At quarter size, 40 iterations of 5 reads over 0.31 M cells: 62 M reads. At half size: 248
M. Dye advection at full size: 5 to 45 M reads. Comfortable either way.

**Music.** Kick: impulse. Snare: vortex pair. Bass level: stirring strength (through an accumulator).
Re-injection r is the phrase-level control. On a drop: cut r to near zero and fire a large impulse.

**Legibility.** r, exactly as described. Also the dye dissipation: with dissipation high and r low the screen
empties, and the picture can be *poured back in*.

**Fits.** Entirely; this is the textbook ping-pong case. About 45 small passes a frame.

### E04. Stateful particles: curl noise, attractors, home springs, trails

**Look and use.** A million or more points that hold the picture, are blown off it, swarm, and fall back into
place. Notch's best-known strength [5]; Unreal's particle systems on stage [snippet 22]; point clouds from
depth cameras in Weirdcore's set [snippet 18].

**What mindstream has.** Two million points whose position is a pure function of their number and the time: a
random place in the picture plus a sine swirl [code]. They cannot accumulate motion, be pushed, or come home.

**Passes and buffers.**
- State in textures, 2048 x 1024 = 2,097,152 particles [computed]: position and age (RGBA32F), velocity and a
  random seed (RGBA16F), each a ping-pong pair. One update pass writes both through two colour attachments.
- Draw: no vertex data; `gl_VertexID` gives the texel; the vertex shader reads the state with `texelFetch`
  (this is the standard method [79]). Points, or instanced quads when a point must be larger than the point
  size limit or be stretched.
- Alternative: transform feedback with two vertex buffers. It fits 3.3 and avoids the float textures, but the
  texture method lets other passes read particle state and is simpler to seed from an image.

**Mathematics.**
- Integrate: `v += dt * a; v *= drag; p += dt * v`. drag as a half-life (0.3 to 3 s).
- Curl noise: take a smooth noise potential and use its curl as velocity, so the field has no sources or sinks
  and particles neither bunch nor thin out. In 2D, `v = (d psi/dy, -d psi/dx)`; in 3D the curl of three
  potentials; sum two or three octaves; move the potential slowly in time [80, read from memory: the paper
  itself would not render]. Mindstream's present "flow" does the 2D form on a two-octave value noise by finite
  differences [code].
- Home spring: `a += k * (home - p) - c * v`, home being the particle's place on the picture's surface. k
  from 0 (free) to about 40 per second squared (snaps back in a quarter second); critical damping at
  `c = 2 sqrt(k)`.
- Flow and fluid forces: read E02's vectors or E03's velocity at the particle's screen position and add them.
- Attractors: a point force `G (q - p) / (|q - p|^2 + s^2)`; or a strange attractor's own velocity field
  (Lorenz, Thomas, Aizawa) scaled into view, which draws its wings out of a million points [unsourced].
- Respawn: when age runs out, return to home (or to a random place weighted by picture brightness: draw
  several candidates and keep the brightest, which concentrates points where the picture has light
  [unsourced]).

**The good version.**
- Additive into the 16-bit float scene with a very small energy each, so density becomes brightness and
  bloom does the rest. Energy per point scaled by 1 / (point area) so a defocused point is a dim disc.
- Size from depth, and a circle of confusion from distance to a focus plane: the cheap, correct depth of
  field for points.
- Streaks: draw each as a quad stretched from last position to this one (both are in the state textures), with
  energy divided by its length. This is true motion blur per particle.
- Trails by drawing into the E01 loop rather than by storing history.
- Depth-sorted alpha is not available without a sort; additive needs none. If occlusion is wanted, weighted
  blended transparency (two colour attachments, one resolve) is the order-free route [unsourced].
- Colour from the picture at home, kept for life, or re-read where the particle now is (the picture seen
  through a swarm).

**Pitfalls.** Sine-based hashes vary between drivers; use integer hashes (mindstream's points already do
[code]). Two million additive points at point size 3 is 18 M blended fragments: fine; at size 20 it is 800 M:
not fine [computed]. 32-bit float positions are needed if positions accumulate for minutes.

**Cost.** Update: 2 M texels, about 20 reads each. Draw: vertex-bound, a few ms [unsourced].

**Music.** Kick: an outward impulse from a point (add to v). Snare: zero the spring for 100 ms, or flip the
curl field's sign. Spring constant k on the phrase. High band: point size jitter or sparkle. A fill: release
all; the one: k to maximum.

**Legibility.** k is the dial. The reassembly on a downbeat is one of the strongest "returns" available, because
the eye watches it happen.

**Fits.** Entirely (vertex texture fetch, two attachments, instancing all in 3.3).

### E05. Slit-scan and time displacement

**Look and use.** Different parts of the frame show different moments. With a ramp, a moving figure is smeared
into ribbons; with a picture-driven map, bright parts run ahead of dark; with a stepped map the frame becomes a
stuttering mosaic of the recent past. Notch's Slit Scan [3]; TouchDesigner's Time Machine, which goes back to a
1995 film-effects system [8].

**Passes and buffers.** A ring of N past frames in a 2D array texture (core since 3.0): each frame, render the
current picture into layer `head` with `glFramebufferTextureLayer`, then advance head. Memory [computed]: at
half size in a 4-byte format (RGBA8 or R11G11B10F), 5 MB a layer; 64 layers 317 MB (1.07 s); 96 layers 476 MB
(1.6 s, more than a bar at 170). At full size, 64 layers is 1.27 GB: affordable on 12 GB but not needed.

**Mathematics.** A delay map d(x) in frames. `layer = mod(head - d(x), N)`; read the two nearest layers and mix
by the fraction (array layers are not interpolated by the sampler). Delay maps:
- a ramp across the frame (the classic slit-scan);
- radius from the centre (time ripples outward);
- the picture's own luminance or its blurred luminance (Time Machine's black-to-white offsets [8]);
- noise, or Voronoi cells (each shard a different moment);
- **stepped in sixteenths**: `d = round(d / f16) * f16` with f16 the frames per sixteenth (5.3 at 170); the
  frame then shows only moments that were on the grid, and the stutter is in time with the break.

**The good version.** Interpolate between layers; store linear float (R11G11B10F is enough here: no feedback);
let the delay map itself move; record the frame *before* the feedback and post chain so those are not doubled.

**Pitfalls.** A still picture has no past: the effect needs film, or the moving surface, or other effects
upstream. A 3D texture would interpolate in time for free but blends across the seam between newest and oldest;
the array with two reads avoids it.

**Cost.** One layer write and a two-read pass: trivial. Memory is the cost.

**Music.** Maximum delay from bass level; map switches on the bar; on a fill, freeze head (stop recording) and
scrub d with the snare pattern: a visual break-chop made of the last bar.

**Legibility.** At small delays the picture is intact but elastic. At large stepped delays it is a collage of
its own past; cut d to zero on the one and it is whole.

**Fits.** Entirely.

### E06. Reaction-diffusion seeded by the picture

**Look and use.** Coral, fingerprints, dividing cells: pattern that grows by itself. Karl Sims's tutorial is the
standard reference [32]. Seeded and steered by the picture, the pattern grows along its edges and fills its
regions with texture that follows its brightness.

**Passes and buffers.** One ping-pong pair, RG16F (two chemicals A and B), at half size. Several iterations per
frame (8 to 20) because one step moves the pattern a fraction of a point.

**Mathematics** (Gray-Scott, as Sims gives it [32]):
`A' = A + (DA lap A - A B^2 + f (1 - A)) dt`, `B' = B + (DB lap B + A B^2 - (k + f) B) dt`,
with DA = 1.0, DB = 0.5, f = 0.055, k = 0.062, dt = 1, and a 3 x 3 Laplacian weighted -1 at the centre, 0.2 on
the four neighbours and 0.05 on the diagonals [32]. Start with A = 1, B = 0 and seed B = 1 in patches.
Different (f, k) give spots, stripes, mazes, dividing cells; the interesting region is a thin crescent of the
(k, f) plane [32]. Sims's page names presets for cell division and coral growth near f 0.037, k 0.065 and
f 0.055, k 0.062 [unsourced as to the exact figures: from memory of the page].

Sims lists the same extensions that make it picture-driven [32]:
- **style map**: f and k vary across the grid. Map picture luminance to a path through the (f, k) crescent, so
  dark areas grow mazes and bright areas spots.
- **orientation**: diffuse faster along one direction. Use the picture's edge direction (the structure tensor
  of E15), so stripes run along contours.
- **flow**: move the chemicals (advect the pair by E02's or E03's field before each reaction step).
- **scale**: pattern size follows the square root of the diffusion rates; or run at a smaller grid and enlarge.

Seeding from the picture: add B where the picture has edges, a little each frame (rate 0.01 to 0.1), so the
pattern keeps regrowing from the picture's lines.

**Showing it.** B (or A - B) is a grey field. Use it as: a mask between the picture and a treated copy; a
height for relief lighting and refraction (E08), which gives the wet, embossed look; a palette lookup; the
displacement source for E01.

**The good version.** Float buffers; enough iterations; anisotropic diffusion; shading as a surface; pattern
scale chosen for the viewing distance (features of 15 to 40 points on this screen [unsourced]).

**Pitfalls.** Unstable if diffusion or dt is raised much beyond the given values; in 8 bits it dies; with no
seeding it reaches a steady pattern and stops being interesting; one iteration per frame looks frozen.

**Cost** [computed]. Half size, 16 iterations, 9 reads: 178 M reads. Fine.

**Music.** Kick: stamp a ring of B. Phrase: move (f, k) along the crescent (the pattern changes species). Bass
level: iterations per frame (speed of growth). Snare: clear a random region to A = 1, B = 0 (a hole that heals).

**Legibility.** As a mask or a relief the picture stays readable under it; as a replacement it does not. The
seeding rate and the mask's opacity are the dials. The pattern growing out from the picture's edges reads as
the picture *becoming* something, which holds attention on the picture.

**Fits.** Entirely.

### E07. Conformal remaps: kaleidoscope, Moebius, Droste, hyperbolic tilings

**Look and use.** The picture folded into symmetric or self-containing space. Kaleidoscope is the most-named
VJ effect [2]; Notch ships Droste, Moebius, Polar and Mirror warps [3].

**Passes and buffers.** One pass each, no state. All are functions from the output point to a source
coordinate, treating the frame as the complex plane z (origin at the centre, aspect corrected).

**Mathematics.**
- **Kaleidoscope.** Polar angle folded into a wedge: `a = mod(theta, 2 pi / n); a = abs(a - pi / n)`. Variants:
  fold in a rotating frame; fold twice at two centres; triangle and hexagon reflections (reflect across three
  lines repeatedly) which tile the plane with no centre and so do not look like a mandala.
- **Moebius.** `w = (a z + b) / (c z + d)`. Circles map to circles. The family that keeps the unit disc,
  `w = (z - a) / (1 - conj(a) z)` with |a| < 1, slides the picture through itself as a moves: the middle
  swells and the far side shrinks to the rim [snippet 68].
- **Droste** (a picture containing itself, optionally in a spiral; after the analysis of Escher's Print
  Gallery [snippet 67, 66]). With s the size ratio between a frame and its copy: take `w = log z`
  (so w = (ln r, theta)); multiply by `beta = 1 - i ln(s) / (2 pi)`, which makes one turn round the centre
  also one step of scale, closing the spiral; add a time offset to the real part for an endless zoom; wrap the
  real part modulo ln s; return with `exp`. For a rectangular picture, replace the wrap by a loop: while the
  point is inside the inner frame multiply by s, while outside the outer divide by s (three or four rounds).
- **Hyperbolic tilings** (Escher's Circle Limit). For p-gons meeting q at a corner (needs 1/p + 1/q < 1/2):
  repeatedly reflect the point into the wedge of angle pi / p, and when it lies inside a circle that meets the
  unit circle at right angles (centre at distance D on the axis, radius R, with
  `D^2 = cos^2(pi/q) / (cos^2(pi/q) - sin^2(pi/p))`, `R^2 = D^2 - 1`), invert it in that circle; 20 to 40
  rounds [unsourced: standard construction, formulas from memory and checked only for D^2 - R^2 = 1]. The
  point ends in one triangle; read the picture there. A Moebius slide applied first flies through the tiling.

**The good version.** These maps squeeze the picture enormously in places, so filtering is the whole quality
difference. Give the source texture mipmaps and read it with explicit gradients (`textureGrad`) computed from
the map's continuous form, before any `mod` or `atan` branch; otherwise a seam of wrong detail level runs
along every fold and along the angle's branch cut. Anisotropic filtering on. Or supersample the pass 4 to 8
times with jittered offsets. Soften fold lines slightly (a smooth absolute value) if the creases should not show.

**Pitfalls.** Aliasing sparkle near the centre of a Droste or the rim of a disc; aspect ratio forgotten (the
present lens and vignette use uncorrected coordinates and are therefore elliptical on a 21:9 screen [code]).

**Cost.** One pass, 1 to 8 reads, up to 40 loop rounds for the tiling: small.

**Music.** Fold count and the Moebius parameter on phrase lines; Droste zoom speed from a bass-driven clock;
a kick nudges the zoom phase; alternate two centres on the backbeat.

**Legibility.** These destroy layout and keep texture and colour: the picture's content is all there, many
times, none of it where it was. A Moebius slide with small |a| is gentle; a seven-fold kaleidoscope is total.
Mix by amount of the *coordinates* (blend the remapped coordinate toward the identity), not of the images, so
the picture unfolds rather than cross-fades. Mindstream's present fold already does this [code].

**Fits.** Entirely.

### E08. Relief from luminance: lighting, parallax, focus

**Look and use.** The flat picture becomes an embossed or deep object: lit from a moving light, seen from a
moving eye, in focus at one depth. Notch has normal-map generation and bump-map warp for this [3].

**The honest caveat.** Brightness is not depth. Bright sky comes forward, dark hair recedes. As a *relief*
style this is fine and reads as embossing; as true depth it is wrong. If a real depth map for the picture is
ever available from upstream, everything here takes it unchanged.

**Passes and buffers.** A height pass (R16F, half size): a blend of blurred luminances, for example
0.6 of a wide blur, 0.3 of a narrow one, 0.1 of the raw. The bloom pyramid already holds the blurs. Then one
shading pass.

**Mathematics.**
- Normal: `n = normalize(vec3(-s dh/dx, -s dh/dy, 1))`, s the relief strength (2 to 20 in points).
- Light: a diffuse term plus a tight specular, with the light circling; in HDR the specular feeds bloom.
- Parallax: march the view ray through the height field, 16 to 32 linear steps then 5 halvings; read the
  picture where it lands [unsourced: the standard parallax-occlusion method]. A slow eye movement of a few
  degrees is enough to make it solid.
- Self-shadow: the same march toward the light.
- Refraction: read the picture at `x + n.xy * amount` (glass), separately per wavelength for dispersion (E22).
- Depth of field: circle of confusion from |h - focus|; feed E-bokeh (section 6, item 13).

**The good version.** Heights from the blurred pyramid so the relief is broad shapes, not grain; binary
refinement so layers do not show; lighting in linear HDR.

**Pitfalls.** Raw luminance as height gives sandpaper. Parallax at steep eye angles shows steps.

**Cost.** 30 to 60 reads a point at full size: 150 to 300 M reads [computed]. Moderate.

**Music.** Light position on a tempo-locked orbit; relief strength pulsed by kick; focus plane swept on the
phrase (rack focus from background to subject is a slow, readable return).

**Legibility.** Mostly preserves it, and adds a reason to keep looking. Focus is a legibility control that
viewers already understand.

**Fits.** Entirely.

### E09. Pixel sorting

**Look and use.** Runs of pixels along rows or columns sorted by brightness, so parts of the picture drip into
smooth gradient streaks while the rest stays intact. Kim Asendorf's 2010 sketch is the origin and still the
reference [74]; Notch ships a node [3].

**How the original works** [74, details from memory of the sketch: the repository page did not show them]. For
each column (or row): find a start where a pixel passes a threshold, find the end where it fails again, sort
that run by value, continue. Three modes choose the threshold test: darker than a black level, brighter than a
brightness level, or not brighter than a white level.

**Without compute shaders.** A fragment shader cannot sort a run in one pass, but it can do one step of an
odd-even exchange sort [snippet 75: the article exists but would not load]: each pixel pairs with its left or
right neighbour according to the parity of its coordinate plus the pass number; the pair compares keys; the
lower-positioned takes the smaller. After as many passes as the longest run, every run is sorted.
- Buffers: one ping-pong pair at full size, and a mask.
- The mask (which pixels are inside a run) must be computed from the *unsorted* source and held; if it is
  recomputed from the half-sorted image the runs flicker and creep.
- Both pixels of a pair must reach the same decision: derive it from the same two keys and the same parity.
- Run 8 to 32 exchange passes a frame. A full sort of 500-point runs then takes 16 to 60 frames, a quarter of a
  second to a second: the sort *happens* visibly, which is better than an instant result.
- Sort direction: along x, y, or along a flow field's dominant axis; sort key: luminance, hue, or one channel.
- Unsorting: there is no inverse; cross-fade back, or re-run from the source.

**The cheap version** is a directional smear or a gradient drawn between the ends of each run. It looks like a
blur, not a sort, because a sort keeps every original colour.

**The good version.** Real exchange sorting; threshold from a blurred luminance so runs follow the picture's
masses; run-length limit (break runs every L points with jitter) so streaks have varied lengths; direction
varying by region; done at full size (the streak edges are single-pixel sharp, which is the look).

**Pitfalls.** Parity errors duplicate or lose pixels. A moving source re-seeds the mask every frame and nothing
ever finishes sorting: latch the source on the beat.

**Cost** [computed]. 32 passes of 3 reads at full size: 475 M reads. Moderate.

**Music.** Latch a new source frame and start a sort on the downbeat; threshold from bass (more of the picture
melts as the bass rises); direction flips on the snare; reset on the phrase.

**Legibility.** Excellent for the edge: the unsorted regions are untouched picture, the sorted regions are
pure colour, and the threshold moves the border between them.

**Fits.** With the odd-even method, entirely.

### E10. Strobe, invert, and colour cycling on the beat

**Look and use.** The oldest live effects: Notch lists Strobe, Invert and Tritone as stock colour nodes [3];
hue rotation on the spectrum is a first staple in Resolume [snippet, 1.1]; festival practice is strobe at the
drop and then dark [23].

**Passes and buffers.** One pass near the end of the chain, before the tone map. No state except the limiter's.

**Mathematics and parameters.**
- Beat phase ph in 0..1; an envelope `e = exp(-ph * beat_len / tau)`, tau 30 to 150 ms.
- Flash: `c *= 1 + g e` (in HDR this drives bloom rather than clipping); black strobe: `c *= 1 - e`.
- Invert: `c = mix(c, w - c, e)` with w the white point; better in a perceptual sense: invert luminance and
  keep hue. Partial invert by a mask (blocks, a wipe, luminance bands) is stronger than whole-frame.
- Tritone and palette cycling: map luminance through a three-colour ramp or a cosine palette
  `a + b cos(2 pi (c t + d))` [59] and advance the phase by a step each beat or bar. Stepping, rather than
  sliding, reads as rhythm.
- Posterise then cycle: quantise luminance to 4 to 8 bands and rotate which colour each band takes.
- Channel time-offset (Resolume's RGB Delay [2]): red from now, green from one sixteenth ago, blue from two,
  using E05's ring. On a still picture nothing happens; on motion every edge splits into a rhythm of colours.

**The good version has a limiter, written once for the whole chain** [30, unsourced as a design]. Track the
frame's mean luminance (the smallest level of the bloom pyramid, read back or kept in a 1 x 1 target); count
opposing changes of more than a tenth of range in the last second; when the count would pass three, hold the
frame's exposure for the rest of the window. Treat saturated red the same way. Per-sixteenth accents then have
to be local or chromatic, which is also the better art.

**Pitfalls.** Flashing at eighths or sixteenths at this tempo is 5.3 to 11.7 per second: outside every
guideline [30, computed]. Whole-frame invert in gamma space is not symmetrical; do it in linear light or on
perceptual lightness.

**Cost.** Nothing.

**Music.** This *is* the music mapping: backbeat flash, bar-line palette step, drop strobe for one second then
two bars of dark.

**Legibility.** Invert and palette keep every contour: the picture is fully readable in the wrong colours. A
safe way to disturb without losing.

**Fits.** Entirely.

### E11. Transitions and morphs between two pictures

**Look and use.** How one picture becomes the next. A cut is always available; these are the alternatives.
Mindstream now cross-fades textures on the surface and morphs the surface's shape [code].

**The useful set, all one pass plus whatever buffers they borrow:**
- **Noise dissolve.** `m = smoothstep(t - w, t + w, n(x))` with n a fractal noise or the picture's own
  luminance (bright parts change first); add an emissive rim where m is near one half, which reads as burning.
- **Mutual displacement.** Each picture displaced by the other's luminance, amounts crossing over:
  `A(x + k t gradL_B)`, `B(x - k (1 - t) gradL_A)`, mixed by t. Edges of the incoming picture appear as
  distortions in the outgoing one before any of its colour does.
- **Flow morph.** With a flow V from A to B: `mix( A(x - t V), B(x + (1 - t) V), t )`. With true optical flow
  between related frames (two frames of a film, two similar pictures) shapes travel to their new places. For
  unrelated pictures flow is meaningless; use a smooth invented field and it becomes a liquid wipe.
- **Datamosh cut** (E02): do not refresh at the change.
- **Simulation hand-over**: change the dye source of E03, the home of E04, or the seed of E06 from A to B. The
  simulation carries the old picture's matter into the new picture's shape. This is the best of them and is
  free once those effects exist.
- **Sort hand-over**: sort A (E09), swap the source to B's sorted state, unsort by cross-fade.
- **Slit-scan wipe**: with E05's ring holding the change, a ramped delay map makes the new picture sweep
  across as a moving line of time.

**The good version.** Timed to the phrase (start on the last bar's fill, land on the one); the mask's soft
width in points, not in fractions, so it is the same on any screen.

**Legibility.** A transition is the one place where two pictures are both half-legible on purpose. Keep it
short (a bar) or very long (sixteen): the middle lengths read as indecision [unsourced].

**Fits.** Entirely.

### E12. Raymarched scenes carrying the picture: tunnels, Menger, Mandelbox, kaleidoscopic fractals

**Look and use.** Flying through endless carved architecture or organic lattice whose surfaces are made of the
picture. The Shadertoy and demoscene staple [64, 65, snippet 86]. Mindstream has one such scene (a gyroid
lattice) [code].

**Passes and buffers.** One heavy fragment pass writing colour and distance (two attachments), optionally at
half size with accumulation over frames; then the ordinary post chain, which can use the distance for fog,
focus and light shafts.

**Mathematics.**
- **Sphere tracing.** From the eye, step by the distance the field reports until it is under a threshold that
  grows with distance (`eps * t`, so far surfaces are not over-resolved). 64 to 128 steps. A relaxation factor
  below one is needed when the field is not a true distance; mindstream's gyroid uses 0.85 on a field already
  scaled by 0.55 [code].
- **Normals.** Four field samples on a tetrahedron rather than six on the axes [unsourced: Quilez's method,
  page not fetched]. Epsilon proportional to distance.
- **Soft shadows.** March toward the light keeping `min(k h / t)`; k from 8 (soft) to 128 (hard) [57].
- **Occlusion.** Five samples along the normal comparing distance travelled with distance reported
  [unsourced]; or, for fractals, an orbit trap (below).
- **Operators** (hg_sdf's vocabulary [64]): repetition `p = mod(p + c/2, c) - c/2`; polar repetition; mirror;
  smooth union. A tunnel is the negative of a cylinder round a curving path, with a displacement.
- **Menger sponge** [56]. Start with a box. Three times over, with scale s = 1, 3, 9: fold the point into a
  repeating cell `a = mod(p s, 2) - 1`, form `r = abs(1 - 3 abs(a))`, take the cross distance
  `c = (min(max(r.x, r.y), max(r.y, r.z), max(r.z, r.x)) - 1) / s` and keep `d = max(d, c)`.
- **Mandelbox** [snippet 63]. Iterate: box fold `p = clamp(p, -1, 1) * 2 - p`; sphere fold (if |p|^2 is below
  a minimum radius squared, scale by fixed/min squared; else if below the fixed radius squared, scale by
  fixed squared over |p|^2); then `p = scale * p + p0` and `dr = dr * |scale| + 1`. Distance about
  `|p| / |dr|`. Usual radii 0.5 and 1; scale between -2.5 and -1.5 or 2 and 3; 8 to 15 iterations
  [snippet 63, ranges unsourced].
- **Mandelbulb** [60]. To spherical form, radius to the eighth power and both angles times eight, back, add the
  start point; with a running derivative `dr = 8 r^7 dr + 1`, distance about `0.5 ln(r) r / dr`
  [unsourced: the usual estimate; the pages that derive it would not load].
- **Kaleidoscopic IFS** [snippet 63, 64]. Each round: fold by absolute value or by reflections in a few
  planes, rotate, scale by s about an offset. Distance is the final shape's distance divided by s to the
  number of rounds. Animating the rotation morphs the whole structure continuously, which is why it is the
  live favourite [unsourced].
- **Orbit traps** [60]. During iteration keep the least distance of the point to the origin and to the three
  axis planes; use them as occlusion and as colour.

**Putting the picture on it.** Four ways, in rising order of interest:
1. three-sided projection by the normal (what the gyroid does [code]);
2. the trap values as texture coordinates, so the picture is smeared along the fractal's own structure;
3. the picture as an emissive wall at the end of the tunnel and as the light source;
4. **projection from a home camera** [unsourced as applied here; it is how projection mapping works]: paint
   every surface point with the picture as seen from one fixed "projector" position. From anywhere else the
   picture is shattered across the geometry; when the camera's path passes through the projector's position
   the picture snaps together, whole. Time the pass for a phrase line.

**The good version.** Distance-scaled thresholds; tetrahedron normals; soft shadow from one moving light;
fog by distance with light scattered in it (E13); the ray start jittered by blue noise and the result
accumulated over frames; reflections by a second, shorter march (cheaper and better than screen-space methods
here); depth of field and motion blur from the distance output.

**Pitfalls.** Step counts that vary wildly across the frame; banding from too few steps without jitter;
texture swimming with three-sided projection; a fractal's distance estimate that over-steps when parameters
are animated (keep the relaxation factor).

**Cost** [computed, upper bounds]. Full size, 96 steps: up to 475 M field evaluations a frame. A gyroid
evaluation is a few operations; a 12-round Mandelbox is about a hundred, giving the order of 5 x 10^10
operations a frame at the limit, which is too much at full size. At half size with accumulation and typical
early exit it is a quarter to a tenth of that. Expect the fractals to need half size; the lattice and tunnels
to run at full [unsourced].

**Music.** Camera speed from a bass-driven clock (already so for the gyroid [code]); fold rotation on the
phrase; a kick breathes the scale or wall thickness; snare flips a mirror; light intensity on the backbeat.

**Legibility.** Method 4 above. Otherwise these are the far end of the range: the picture is material, not
image.

**Fits.** Entirely; it is only a fragment shader.

### E13. Volumetric light and fog

**Look and use.** Visible shafts through haze; glowing fog banks; the air itself lit. Notch reworked its
volumetric lighting around this [3]; clubs are full of real haze, and visuals that have it sit naturally in
the room [unsourced].

**Two methods.**

*Screen-space shafts* (GPU Gems 3, chapter 13 [34]; mindstream's "rays" is this [code]). For each point, step
toward the light's screen position and sum the bright pixels passed, each step weaker:
`L = exposure * sum( decay^i * weight * S(x_i) )`, the steps spanning a fraction ("density") of the way to the
light [34]. The chapter's refinements: use an occlusion image (bright sources only, occluders black); work at
reduced size; clamp or fade when the light is far off screen [34].

*Marched fog* (for E12's scenes or a slab of fog in front of the picture). Along the eye ray through a density
field:
- transmittance by Beer's law: `T *= exp(-sigma * ds)` [54];
- light scattered toward the eye at each step: density times light colour times the light's own transmittance
  to that point (a short second march of 4 to 6 steps [54]) times a phase function;
- Henyey-Greenstein phase: `(1 - g^2) / (4 pi (1 + g^2 - 2 g mu)^1.5)`, mu the cosine between view and light,
  g about 0.6 to 0.9 for the bright halo round a light seen through haze [54];
- integrate each step exactly rather than by rectangle: with scattering S and extinction sigma over a step,
  add `T * S * (1 - exp(-sigma ds)) / sigma` [unsourced: Hillaire's energy-conserving form, from memory].
- Steps: 32 to 64 with 4 to 6 light steps when jittered and accumulated [54]; around 128 with 6 without
  [snippet 55].

**The picture as the fog.** Extrude the picture's luminance into a thin density slab, or use it as the light
(a bright wall behind fog made of noise). Then the shafts come *through the picture's dark shapes* and move
when the fog moves: the volumetric version of the present radial rays.

**The good version.** The ray's start offset per pixel by blue noise, the noise advanced each frame by adding
the golden ratio and taking the fraction, so the error is spread evenly in space and time [48]; half size and
an edge-aware enlargement; accumulation over frames; in HDR, with the result feeding bloom.

**Pitfalls.** White-noise jitter looks like grain; blue noise looks like nothing [48]. Shafts drawn over
foreground objects [34]. Banding at low step counts: N steps give only N + 1 shades without jitter [48].

**Cost.** Screen-space: 64 reads at half size, 80 M [computed]. Marched fog at half size, 48 steps each with 5 light steps: about 360 M
density evaluations [computed]. Moderate to heavy.

**Music.** Light intensity on the backbeat; g toward 0.9 on a drop (the glare tightens); fog density on the
phrase; the light's position on a tempo-locked orbit.

**Legibility.** Haze lowers contrast gently and returns it gently: a slow dial, good for long arcs.

**Fits.** Entirely.

### E14. Strand and line fields

**Look and use.** The picture redrawn as thousands of flowing lines: hair, brushwork, wind, iron filings. A
common generative look in TouchDesigner and Notch work (trails from particles; instanced lines) [unsourced as
to prevalence].

**Three constructions.**
1. **Line integral convolution** (image space, one pass). For each point, walk 15 to 30 steps each way along a
   direction field and average either a noise texture (gives silky streaks that follow the field) or the
   picture itself (gives a smear along its own contours) [unsourced: the classic method].
2. **Instanced ribbons** (geometry). N strands of K points each. The vertex shader, for vertex j of strand i,
   starts from the strand's seed and takes j steps through the field, reading the field texture each step:
   K(K+1)/2 reads a strand. For 100,000 strands of 32 points that is 53 M reads [computed]. Offset alternate
   vertices sideways in screen space to make a ribbon of constant width; `gl_VertexID` and `gl_InstanceID`
   supply i and j. No geometry shader needed.
3. **Particle trails**: E04's particles drawn into E01's loop.

**The field.** The picture's *edge tangent*: build the structure tensor (products of the x and y Sobel
derivatives: xx, xy, yy), blur it, and take the eigenvector of its smaller eigenvalue; that direction runs
along edges [51, snippet 53]. Lines following it trace the picture's contours like hair. Alternatives: curl
noise; the fluid's velocity; the optical flow.

**The good version.** Strands seeded where the picture is bright or edged; colour taken at the seed; width and
opacity tapering along the strand; additive in HDR; the seed set stable from frame to frame so strands writhe
rather than flicker; length animated (grow from the seed on a kick).

**Pitfalls.** The tangent has no sign (it is an axis, not an arrow): choose the sign that agrees with the
previous step when walking. Field noise makes hairy tangles: blur the tensor well (sigma 2 to 6 points).

**Cost.** LIC at full size, 40 reads: 200 M [computed]. Ribbons: vertex-bound, 3.2 M strand points, twice that in vertices [computed].

**Music.** Strand length on the kick; a wave of brightness travelling along every strand at one strand per
beat; field blend (contours to curl noise) on the phrase.

**Legibility.** Lines along the picture's own contours are a drawing of it: highly legible with almost none of
its pixels. Blend the field toward noise and the drawing dissolves into weather.

**Fits.** Entirely (instancing, vertex texture fetch).

### E15. Edge-aware stylisation: anisotropic Kuwahara, extended difference of Gaussians, flow-based lines

**Look and use.** Painting and ink. Kuwahara, edge detection and outlines are stock nodes [3]. Mindstream has
the basic four-square Kuwahara and a Sobel edge [code].

**Anisotropic Kuwahara** (Kyprianidis and others [52]; a readable walk-through [51]).
- Pass 1: structure tensor. Sobel derivatives of the colour image; store xx, yy, xy.
- Pass 2: blur the tensor (Gaussian, sigma about 2).
- Pass 3: per point, eigenvalues `l1, l2 = ((E + G) +- sqrt((E - G)^2 + 4 F^2)) / 2`; direction from the minor
  eigenvector; anisotropy `A = (l1 - l2) / (l1 + l2)`. Stretch the filter into an ellipse along the edge:
  axes `r (alpha + A) / alpha` and `r alpha / (alpha + A)`, alpha about 1 [unsourced: from memory of the
  paper]. Divide the ellipse into 8 sectors with smooth, overlapping weights (a polynomial weight replaces the
  Gaussian for speed, with constants near 0.1 and 0.5 [51]); for each sector take the weighted mean and
  variance; output the sum of means weighted by `1 / (1 + (variance scale)^q)`, q about 8 [unsourced: paper].
  Radius 6 to 12 points [51].
- The differences from the basic filter: eight soft sectors instead of four hard squares (no blocky
  artefacts); a soft blend instead of a hard choice (no flicker); an ellipse that follows edges (strokes).

**Extended difference of Gaussians** (Winnemoller [snippet 53]). Two blurs, one k = 1.6 times wider:
`D = (1 + p) G_sigma - p G_(k sigma)`; then a soft threshold: 1 where D is above eps, else
`1 + tanh(phi (D - eps))`. p sets how much of the tone survives next to the lines (p large: pure ink lines;
p small: a toned woodcut); phi the hardness. One parameter set gives pencil, another charcoal, another a
two-tone poster.

**Flow-based lines** [snippet 53]. Take the difference of Gaussians only *across* the edge (a 1D filter along
the gradient), then smooth *along* the edge tangent (a second 1D pass following the field, as in E14). Lines
come out continuous and even, where Sobel gives broken, noisy ones.

**The good version** is exactly the above. In linear light for the blurs, perceptual for the thresholds.

**Pitfalls.** On film, the tensor flickers: blur it in time as well (mix with last frame's, 0.2 new).

**Cost.** Anisotropic Kuwahara: radius 10, about 150 to 300 weighted reads: up to 1.5 x 10^9 reads at full size
[computed]: the heaviest filter here; half size is usually indistinguishable for a painterly look. Lines: four
small passes.

**Music.** Radius and anisotropy on the phrase; line threshold from the bass (ink floods in on the low end);
the XDoG p parameter pulsed on the backbeat flips between tone and line.

**Legibility.** Removes detail, keeps layout and edges: safe, and useful *under* a destructive effect to make
what survives bolder.

**Fits.** Entirely.

### E16. CRT and VHS

**Look and use.** The picture as seen on a tube or off a worn tape. Stock in Notch (VHS Scanlines, VHS Blur)
[3]; the reference CRT shader is Timothy Lottes's public-domain one [snippet 76].

**CRT** (after Lottes [snippet 76]). Treat the source as a low-resolution raster (240 to 480 lines whatever the
screen). Each source pixel is drawn as a Gaussian spot, sharper across than along (his defaults: pixel
hardness -3, scan hardness -8, on an exponent scale); beam spots widen with brightness; a shadow mask or
aperture grille multiplies the result (stripes of red, green, blue, with the dark part at 0.5); a slight
barrel curve; a bloom of the unmasked image added at about 0.15 [snippet 76]. Do it in linear light or the
scanlines darken the picture unevenly.

**VHS** [77, snippet 77]. The physical causes, each a separate term:
- luma bandwidth about 3 MHz, chroma about 0.6 MHz [snippet 77]. Over a 52 microsecond line that is about 310
  and 62 resolvable samples [computed]; on a 3440-point screen, a horizontal blur about 11 points wide for
  brightness and 55 for colour [computed]. So: convert to a luma-chroma space, blur chroma five times wider
  than luma, horizontally only, and shift chroma a little to the right (it arrives late [77]).
- about 240 lines of vertical detail [77].
- tape-speed wobble: each line displaced horizontally by a slow wander plus a little per-line jitter [77].
- head switching: a band of displaced, noisy lines at the bottom of the frame [77].
- tracking errors: horizontal tears that roll [77].
- dropouts: short white horizontal streaks [77].
- noise, stronger and coarser in chroma.

**The good version.** Separate terms with their own time behaviour (generated per frame, so they move like
tape damage [77]); chroma handled in its own space; the low-resolution raster honoured rather than scanlines
painted over a sharp picture, which is the giveaway of the cheap version. Mindstream's grain adds a
one-pixel-pitch sine as "scan lines" [code]: at 1440 lines that is invisible or shimmers.

**Pitfalls.** Mask and scanline patterns beat against the screen's pixels and against halftone or glyph grids:
keep periods to whole numbers of screen points; do not combine with E17 or halftone.

**Cost.** A few passes; trivial.

**Music.** Tracking tear on the snare; a head-switch band that jumps up the frame on a fill; chroma shift from
the bass; a full vertical roll at a phrase line.

**Legibility.** Very safe: the eye has decades of practice reading through tape noise. A tracking error that
wipes the frame is a readable "lost"; lock-in is a readable "found".

**Fits.** Entirely.

### E17. Glyphs, mosaics and dither

**Look and use.** The picture as characters, tiles or one-bit dots. Notch has Dither, Dot Matrix, Bit Crush,
Pixelate, Colour Reduce [3].

**Glyph rendering.**
- Cheap: one average brightness per cell (a mip level read), pick a character by density. It blurs edges
  because a character is treated as a pixel [78].
- Good [78]: describe every character by how full each of six regions of its cell is; sample the picture in
  the same six regions of each cell; choose the character whose six numbers are nearest; sharpen the choice by
  exaggerating differences within the cell and by looking at neighbouring cells. Edges then get slashes, bars
  and corners that follow them. On the GPU: one pass computes the six samples per cell into a small target; the
  nearest-character search is a loop over the alphabet's vectors held in a small texture (95 characters, 6
  numbers each); a final pass draws from a glyph atlas with the picture's colour.
- A cheaper route to the same improvement: where a cell has a strong edge (Sobel), choose among line glyphs by
  the edge's angle; elsewhere choose by density [unsourced].

**Dither** [50].
- Ordered: compare each pixel with a threshold from a tiled matrix. Bayer matrices are built recursively
  (each level is four copies of the last, scaled and offset); the pattern is the look.
- Blue noise: the same comparison against a blue-noise tile; no visible pattern, an even stipple [49, 50].
- Error diffusion (Floyd-Steinberg, Atkinson) passes each pixel's error to the next and cannot be done
  independently per pixel [50]. Blue-noise thresholding is the nearest parallel look.
- Work in linear light or mid-tones come out too bright [50].
- For colour: dither each channel to 2 to 4 levels, or map to a small palette.

**The good version.** Cell size in whole screen points; the dot grid fixed while the picture moves; in HDR, let
lit dots exceed white so they bloom like a real display.

**Pitfalls.** Moire with CRT masks and halftone; shimmer if the threshold tile moves; sub-pixel cells.

**Cost.** Trivial to small.

**Music.** Cell size stepped on the bar (coarser on the drop); the glyph set swapped on the snare; a wave of
bit depth (8 bits down to 1 and back) across a phrase.

**Legibility.** Cell size is a clean, monotone dial from the full picture to a few dozen blocks; the eye
recovers pictures from remarkably few cells [unsourced]. A good primary control.

**Fits.** Entirely.

### E18. Mesh displacement and wireframe terrain

**Look and use.** The picture as a landscape of lines: ridges where it is bright. The scan-line mountain range
and the glowing grid are fixtures of electronic-music artwork [unsourced].

**Construction.** A grid of about 860 x 360 vertices (310,000 [computed]); the vertex shader reads the blurred
luminance (E08's height) and lifts each vertex; a slow orbiting camera.
- Lines without a geometry shader: draw filled triangles and compute the wire in the fragment shader from the
  grid coordinate: `line = 1 - smoothstep(0, w, min(fract(g), 1 - fract(g)) / fwidth(g))`. Constant width,
  anti-aliased, and it can show only the rows (the ridge-line look) or both.
- Hidden lines: draw the filled surface in black (or in the picture's dimmed colour) with depth test, then the
  lines.
- Normals from the height's gradient for lighting; colour from the picture.

**The good version.** Height from a blurred pyramid level; line brightness in HDR feeding bloom; depth of field
from the real depth buffer; a second, finer displacement from the high band.

**Cost.** Small.

**Music.** Height scale on the kick; a ripple travelling out along the rows per beat; the spectrum itself as
the newest row, scrolling back (the classic waterfall) blended with the picture's height.

**Legibility.** From straight above it is the picture; tilt the camera and it becomes terrain. Camera elevation
is the dial, and returning overhead on a phrase line is a clean recovery.

**Fits.** Entirely.

### E19. Domain-warped noise and flow fields as displacement

**Look and use.** Marbling: the picture stirred by a field that is itself stirred. Notch's Turbulence and Curl
Noise warps [3]; Resolume's Displace [2].

**Mathematics.** Fractal noise is a sum of octaves, each twice the frequency and (usually) half the amplitude;
the amplitude ratio G relates to a roughness H by G = 2^(-H), and 0.5 is the usual choice [58]; detune the
frequency ratio slightly from 2 and rotate between octaves to hide the lattice [58]. Domain warping feeds the
noise its own output as an offset: `f(p + fbm(p + fbm(p)))` [62]. Take two such values as a vector q; a second
round gives r; displace the picture's coordinate by r times an amount (0 to 0.15 of the height). Colour can be
tinted by |q| and |r|, which is where the marbled veins come from [unsourced: Quilez's article, page not
fetched].

**The good version.** Gradient noise with an integer hash, not value noise on a sine hash (mindstream's flow
field is the latter [code]); 5 to 6 octaves; the warp evaluated at half size into a displacement texture and
reused by every effect that wants a field (E01, E03, E04, E14).

**Cost.** 18 noise evaluations of 5 octaves at half size: small.

**Music.** Warp amount from bass through a slow envelope; the field's time from a bass-driven clock.

**Legibility.** Small amounts are a living wobble; large amounts are marble. A smooth dial.

**Fits.** Entirely.

### E20. Tunnel and warp

**Look and use.** The oldest demo effect and still a floor-filler: the picture wrapped round the inside of an
endless tube, rushing at the viewer [snippet 86].

**Mathematics.** `u = k / r + speed * t`, `v = theta / pi`, darkened toward the centre by r. Shapes: replace r
by a p-norm `(|x|^p + |y|^p)^(1/p)` (p = 2 round, p large square, p below 1 a star). Bend: move the centre
along a slow path. Read the picture with explicit gradients to avoid the seam at theta = pi and the sparkle
at the centre (E07's point). The 3D version is E12's tunnel.

**Cost.** One pass.

**Music.** Speed from the bass clock; a twist (v += a * u) kicked on the snare; p stepped on the bar.

**Legibility.** Destroys layout completely. Use it as the "gone" state and blend coordinates back to identity
to return.

**Fits.** Entirely.

### E21. Thin-film iridescence

**Look and use.** Soap-bubble and oil-slick colour that shifts with angle and thickness; the "holographic foil"
look. Usually seen on reflective geometry in stage content [unsourced].

**Mathematics** [69]. Light reflecting from the top and bottom of a film of thickness d and index n travels a
path difference `2 n d cos(theta_t)`, theta_t the angle inside the film; wavelengths for which that difference
is a whole number plus a half of the wavelength reinforce (the half from the phase flip at the denser surface)
[69]. In a shader: for 6 to 8 wavelengths across 400 to 700 nm, intensity `0.5 + 0.5 cos(2 pi path / lambda +
pi)`; convert each wavelength to RGB with a fitted spectral function [70] and sum. The rigorous real-time
model pre-integrates this against the eye's response [snippet 71]. Thickness 100 to 800 nm gives the strongest
colours [unsourced].

**Use here.** Thickness from the picture's luminance plus noise; angle from E08's relief normal or E12's
surface normal; apply as the colour of a reflection term. The picture gains a film of colour that slides when
the light or the relief moves.

**Cost.** 8 evaluations a point: small.

**Music.** Thickness offset from a bass clock (colours cycle through the orders); pulse on the backbeat.

**Legibility.** A colour layer only; contours intact.

**Fits.** Entirely.

### E22. Spectral dispersion and glass

**Look and use.** Colours parting at edges as through a prism; refraction through glass shapes. Mindstream's
lens has an eight-sample spectral split [code], which is already the right idea.

**Mathematics.** Sample the image N times with a displacement that varies with wavelength; weight each sample
by that wavelength's colour; normalise so white stays white. The displacement can be radial (a lens), along a
normal (glass, E08), along motion (a chromatic motion blur), or along the luminance gradient. N of 8 shows
discrete ghosts at large spreads; 16 to 24 with a per-pixel jitter of the sample positions (blue noise) is
smooth [unsourced]. Spectral weights from a fitted function [70] rather than three triangles.

**Cost.** N reads: small.

**Music.** Spread on the kick (already so [code]).

**Legibility.** Mild; edges fringe, layout holds.

**Fits.** Entirely.

### E23. Metaballs and liquid surfaces

**Look and use.** Blobs that merge; liquid chrome; a picture seen through moving drops [snippet 86].

**Two routes.**
- Raymarched: spheres joined by a smooth minimum (`smin(a, b, k)`), k the blend radius; shade with reflection
  and refraction of the picture. Tens of balls are affordable in a marched field [unsourced].
- From particles: splat E04's particles as soft Gaussian blobs into a half-size float target; threshold the
  sum; take normals from its gradient; refract and reflect the picture through it. Thousands of blobs, and the
  blobs inherit every force the particles have.

**Cost.** Small to moderate.

**Music.** Blend radius and threshold on the kick (blobs swell and merge), release on the off-beat.

**Legibility.** Refraction through a few large drops keeps the picture; through many small ones it is frosted
glass. Drop size is the dial.

**Fits.** Entirely.

### E24. Lens flares, dirt and halation

**Look and use.** The artefacts of a camera lens pointed at something bright; used sparingly alongside bloom
[43]. A stock Notch node [3].

**Mathematics** (Chapman's screen-space method [43]). On a small, thresholded copy of the frame:
- ghosts: read the image flipped through the centre, at several points along the line through the centre;
  fade by distance from the centre;
- halo: read at a fixed distance toward the centre, weighted into a ring;
- chromatic split: offset red, green and blue reads along that line;
- blur the result well; at full size multiply by a dirt texture and by a starburst that depends on the angle
  round the centre [43].
Lens dirt on bloom alone: `bloom * (1 + dirt * k)` [36]. Halation (film's red-orange glow round highlights) is
a second, wider bloom of the red channel added back at low strength [unsourced].

**Cost.** Small.

**Music.** Strength on the backbeat.

**Legibility.** Neutral; overdone, it reads as cheap [43].

**Fits.** Entirely.

### E25. Motion blur, temporal accumulation and anti-aliasing over time

**Look and use.** Speed conveyed by blur rather than by flicker, which is also the festival guide's advice for
fast music [23]. And the general technique of spending several frames' samples on one frame's quality.

**Motion blur.**
- With E02's vectors: blur each point along its vector. The reconstruction method takes the largest vector in
  each tile and its neighbours, then gathers a dozen or so samples along it, weighting by whether each sample
  is in front and moving [82: the paper's page would not load; unsourced as to counts]. Scatter-as-gather
  variants handle edges best [37].
- By accumulation: draw the moving stage (surface, cube, particles) several times at sub-frame times and
  average. Four to eight sub-frames is exact, simple, and affordable here because the scene is a few draw
  calls [unsourced].

**Accumulation over frames** (for marched scenes, fog, depth of field, anything noisy) [44]:
- jitter the sample (ray start, sub-pixel position, kernel rotation) with a low-discrepancy sequence of 8 to
  16 values [44];
- reproject last frame's result by the motion vectors [44];
- clamp the old colour to the range of the new frame's 3 x 3 neighbourhood, which is what stops ghosts; do
  the clamp in a luma-chroma space [44];
- blend about 10 percent new [44];
- read history with a sharper-than-bilinear filter [44]; blend in a compressed range so bright pixels do not
  flicker [44].

**Supersampling** remains the simple alternative for the 2D chain: see section 6, item 16.

**Cost.** Vectors and one pass of 12 to 16 reads; or N times the stage's draw cost.

**Music.** Shutter length on the phrase (long on a roll, short on a drop, where crispness reads as impact).

**Legibility.** Motion blur *raises* legibility of fast motion: a tumbling cube with blur is a spinning object;
without it, at 60 Hz, it is a flicker.

**Fits.** Entirely.

### E26. Tone mapping, grading and looks

**Look and use.** The last word on colour. Notch lists Tone Map, LUT, Colour Grading, Tritone and Film Grading
[3].

**Mathematics.**
- Tone map once, at the end, from linear HDR to display range. The fitted filmic curve in common use:
  `(x (2.51 x + 0.03)) / (x (2.43 x + 0.59) + 0.14)`, clamped, with input pre-scaled by about 0.6 to match the
  reference it was fitted to [45]. Its known fault: applied per channel it over-saturates and shifts the hue of
  very bright saturated colours (blue toward purple, red toward orange) [45, snippet 46]. For neon content that
  is a look some want and some do not; the alternatives hold hue and let highlights go to white [snippet 46].
  A practical middle: apply the curve to luminance, scale the colour, then desaturate toward white as
  luminance passes 1 [unsourced].
- Exposure before the curve; make exposure the master "intensity" control.
- Grade after: lift, gamma, gain per channel; split toning (one tint in shadows, its complement in
  highlights); a 3D lookup table (32 cubed in a 3D texture; scale the coordinate by (N - 1) / N and add
  0.5 / N so the ends land on texel centres [unsourced]).
- Then encode to sRGB, then dither.

**Music.** Exposure dips before a drop; palette (LUT blend) per section.

**Fits.** Entirely.

### E27. Blocks and tiles

**Look and use.** The frame cut into blocks that slide, repeat, freeze, swap or quantise: Notch's Block Glitch
and Randomise Tiles [3]; the "glitch" mindstream has is a member [code].

**The fuller vocabulary.**
- multi-scale blocks: choose per region between cell sizes (a hashed quadtree: split a cell if a hash says
  so, up to four levels), so damage has large and small pieces like real compression;
- hold: a damaged block keeps its damage for a hashed number of sixteenths rather than changing every tick;
- frozen blocks: read from E05's ring at a past moment;
- block averaging and 8 x 8 "ringing": replace a block by its mean plus a few coarse cosine terms, the look of
  heavy compression [unsourced];
- tile shuffle: swap blocks' source positions by a permutation that is animated one swap per sixteenth;
- line effects: tears, a rolling band, a frame that slips vertically and wraps.

**Legibility.** Tile shuffle is a sliding puzzle: layout destroyed, every piece intact, and the solve can be
animated into place on the one.

**Fits.** Entirely.

### E28. Screen-space reflection

**Look and use.** Mirror floors and wet surfaces reflecting what is on screen.

**Mathematics** [snippet 81]. Needs depth and normals from the geometry pass. March the reflected ray in screen
space (32 to 64 steps), a hit being where the ray passes behind the depth buffer within a thickness tolerance;
refine by a few halvings; fade near screen edges and for rays coming toward the eye.

**Judgement.** For mindstream's present geometry (one surface or one cube) there is little to reflect. A plane
"floor" under the cube, drawn by rendering the scene a second time mirrored, is simpler and exact. For marched
scenes a second march is better. Low priority.

**Fits.** Yes (depth as a texture, two attachments).

---

## 3. Quality practice

### 3.1 Linear light, float buffers, one tone map

The rule the lens papers all assume [36, 37, 38]: light adds linearly, so blur, glow, defocus, feedback and
blending must be done on linear values that may exceed 1, and the conversion to what the screen shows happens
once, last.

1. **Decode on the way in.** Upload pictures and film frames as sRGB textures (`GL_SRGB8` / `GL_SRGB8_ALPHA8`);
   the sampler then returns linear values and filters correctly. Mindstream uploads plain `GL_RGB8` [code], so
   every blur and blend in the chain is done on gamma-encoded numbers: glows are too dim and too grey, edges of
   blurred shapes too dark, and additive particles saturate too fast.
2. **Float all the way.** RGBA16F for anything that feeds back, simulates or accumulates. `R11F_G11F_B10F`
   (4 bytes, no alpha, no negatives) for one-shot colour targets and the bloom pyramid, as the bloom guide
   uses [36]. Memory [computed]: a full-size RGBA16F target is 39.6 MB, at twice the size 158 MB; a dozen
   full-size float targets is under half a gigabyte.
3. **An exposure, then a tone curve** (E26), in place of the present per-channel roll-off above 0.8 that is
   applied once after bloom and again after streaks [code].
4. **Encode** (linear to sRGB) in the last pass, or let an sRGB framebuffer do it.
5. **Dither** as the very last thing.

### 3.2 Dither and noise

- Quantising a smooth float gradient to 8 bits makes bands; adding noise of about one step before quantising
  turns them into grain too fine to see. Use blue noise: a free, public-domain set exists in sizes from 16 to
  1024 squared, with the recommendation to load the 64 x 64 set as an array, pick a layer and an offset at
  random each frame, and shape the noise to a triangular distribution [49].
- For anything stochastic inside an effect (ray start, kernel rotation, sample jitter) use blue noise advanced
  by the golden ratio each frame [48], or interleaved gradient noise,
  `fract(52.9829189 * fract(0.06711056 x + 0.00583715 y))`, moved 5.588238 points a frame over a 64-frame
  cycle, which is designed to resolve cleanly under accumulation [47].
- Replace `fract(sin(dot(...)) * 43758.5453)` hashes, which mindstream uses in every pass [code], with integer
  hashes (the points' vertex shader already has one [code]). The sine hash shows patterns at large
  coordinates and differs between drivers [unsourced].

### 3.3 Sample counts the good versions use

| effect | count | source |
|---|---|---|
| bloom | 13 reads down, 9 up, 5 to 6 levels, no threshold, strength about 0.04 as a blend | [36] |
| depth of field | 22-point disc at half size (tutorial); 49-point three-ring disc at half size with a 9-read prefilter (production) | [39], [snippet 37] |
| screen-space shafts | 64 to 128 along the ray, at reduced size, jittered | [34], counts [unsourced] |
| marched fog or cloud | 50 + 6 with jitter and accumulation; about 128 + 6 without | [54], [snippet 55] |
| sphere tracing | 64 to 128 steps; soft shadow march up to as many | [57], [code] |
| pressure solve | 20 minimum, 40 to 80 recommended | [33] |
| reaction-diffusion | 8 to 20 iterations a frame | [unsourced] |
| accumulation over frames | 8 to 16 jitter positions, 10 percent new each frame | [44] |
| anisotropic Kuwahara | 8 sectors, radius 6 to 12 | [51] |

### 3.4 Holding 60 Hz at 3440 x 1440

No measurement was made; this is method, with one order-of-magnitude guess.

- **Count reads.** One read per point at full size is 4.95 M reads; a hundred is 0.5 x 10^9 a frame, 3 x 10^10
  a second [computed]. Cards of this class have a nominal texel rate of a couple of hundred billion a second,
  and float targets with scattered reads achieve a fraction of that; plan on a total of roughly 0.3 to 1 x
  10^9 reads a frame and measure [unsourced]. On that scale: the present bokeh (72 reads) is 0.36 x 10^9, the
  present oil paint at full strength (324 reads) is 1.6 x 10^9, and the present rays (96) 0.48 x 10^9
  [computed from code]. Any two of those together at full size are probably already the whole budget, and at
  the "sharp" setting of 2 every pass costs four times as much, because the effect chain runs at the enlarged
  size [code].
- **Run the chain at screen size, not at the supersampled size.** Supersample the geometry (surface, cube,
  particles), resolve to screen size, then run effects. This alone quarters the cost of the chain at sharp 2.
- **Half size for anything smooth.** Fog, shafts, defocus, Kuwahara, fluid velocity, reaction-diffusion,
  optical flow. A quarter of the cost, and the engines do exactly this [39, 40].
- **Use the pyramid.** A wide blur is a read of a small mip level, not a wide kernel. Build one mip chain of
  the frame per frame (the bloom downsample already is one) and let relief, displacement, flow and thresholds
  read it.
- **Separable where the kernel allows**: Gaussian blurs as two 1D passes; even a disc can be approximated by
  two complex-valued 1D passes [41].
- **Spread work over time**: jitter and accumulate (E25); advance simulations in several small steps a frame
  only when the music calls for speed.
- **Stop early**: effects whose amount is zero are already skipped [code]; also skip per point (the bokeh does
  when the radius is under 0.6 [code]).
- **Dynamic size.** Engines lower the internal resolution when the last frame ran long, aiming for a 14 to 15
  ms budget at 60 Hz [40]. A timer query round the chain and a size factor on the half-size targets would do
  it.
- **Correct pyramids.** When halving, a pass must read enough source texels to cover the reduction; the
  13-read filter is built for an exact halving [36]. Keep half-pixel centres consistent between the down and
  up passes or the pyramid shifts [42].

---

## 4. Composition

### 4.1 Order of the chain

The order below is the one the lens and film sources imply (scene, then optics, then sensor, then display)
[36, 37, 65], with the remembering and remapping effects placed where they do least harm [unsourced].

1. **Source**: decode the picture or film frame to linear.
2. **Stage**: the surface or cube, particles, strands, terrain, or a marched scene. Output colour, depth and
   motion vectors. Supersampled or accumulated. Resolve to screen size.
3. **Owner of the picture** (at most one, see 4.2): fluid, reaction-diffusion, datamosh, pixel sort, slit-scan.
   These replace the stage's image with their own state.
4. **Feedback loop** (E01): wraps stages 2 and 3; reads its own last output.
5. **Remap** (at most one): kaleidoscope, Droste, Moebius, hyperbolic, tunnel, domain warp, ripple, shatter.
6. **Stylise** (at most one, perhaps two): Kuwahara, lines, halftone, glyphs, dither, relief lighting,
   iridescence.
7. **Optics**: depth of field, then motion blur, then light shafts, then bloom, streaks and flares.
8. **Lens**: distortion and spectral fringing, vignette.
9. **Beat colour**: strobe, invert, palette (E10), with the flash limiter.
10. **Exposure, tone map, grade.**
11. **Display emulation** (CRT or VHS), which models a screen showing the finished picture and so comes after
    the tone map (with its own small glow).
12. **Grain, encode, dither.** Overlay text after everything.

Differences from the present order [code]: defocus now runs after bloom and streaks, and should run before
them; glitch runs before the lattice, the paint and the halftone, so it gets painted and printed (move it to
stage 9 or 11, where a signal fault belongs, unless the painted look is wanted); the roll-off is applied
twice; everything runs at the supersampled size.

### 4.2 What should be exclusive

- **One owner of the picture at a time.** Fluid, reaction-diffusion, datamosh, pixel sort and slit-scan each
  keep the image as their own state. Chaining two means the second erases the first's character. They hand
  over well (E11), which is better than overlapping.
- **One remap at a time.** Two remaps compose into mush, with one exception: a Moebius slide before a
  kaleidoscope or tiling is how those are flown through.
- **One periodic screen at a time.** Halftone, glyphs, ordered dither, CRT mask, scanlines: any two beat
  against each other in moire.
- **Supersampling or accumulation**, not both, for the same stage.
- **Kuwahara before lines**, not after: lines on a painted image are clean; paint over lines destroys them.

**Good pairs.** Fluid then relief lighting (liquid metal). Reaction-diffusion as a mask for invert. Datamosh
then pixel sort on the downbeat (the smear freezes into streaks). Particles into feedback (trails). Strands
over a Kuwahara base (drawing over paint). Slit-scan then kaleidoscope (time folded into symmetry). Anything
destructive then CRT (the damage reads as a broken broadcast, which gives the viewer a frame for it).

### 4.3 Staying legible at the edge

The companion report on legibility in the music [04] reached conclusions that transfer directly, and nothing
found here contradicts them:

- **Surprise only counts against a trusted frame** [04]. In a picture the frame is its coarse layout: where the
  large light and dark masses are, and its palette. A viewer gets that in a glance; detail comes later
  [unsourced: the scene-gist literature, not consulted here].
- So sort the effects by what they destroy, and destroy one thing at a time:

| destroys | keeps | effects |
|---|---|---|
| fine detail | layout, palette | Kuwahara, halftone, glyphs, dither, short pixel-sort runs, bloom, relief |
| layout | detail, palette | kaleidoscope, Droste, tunnel, tile shuffle, long slit-scan, late fluid |
| continuity in time | each frame | datamosh, strobe, stepped slit-scan, block hold |
| colour | contours | invert, palette cycle, tritone, iridescence |
| the image entirely | only its matter | particles with no spring, fluid with no re-injection, fractal scenes |

- **One dial past the lip at a time** [04]: take one class to its limit while the others hold, for a bar or
  two, and return on a four-bar line.
- **Every destructive effect needs its return path built in**: the re-injection, refresh, spring or coordinate
  blend named in each entry. One "hold on the picture" control should drive all of them, so the director can
  ask for 0.2 without knowing which effect is running.
- **Returns should be events**: a datamosh refresh, particles snapping home, a tile puzzle solving, a camera
  reaching the projector position, a focus pull. Time them to the one.
- **Dark is part of it.** Practitioners say the same thing in several ways: stay with a theme, play less
  bright, leave negative space, keep a readable idea from the back of the room [27, 28]. A screen that is
  always full has nowhere to go.
- **A measure, if wanted** [unsourced]: correlate the low-pass luminance of the output (a mip level about 54 x
  22) with that of the source picture. Near 1, the layout survives; near 0, it is gone. The program can keep
  this within a band, as the music side proposes to do with its own statistics [04].

### 4.4 Beat against drift

- The best-synchronised show found triggered on every element's every event [16]; the best-loved visualiser
  runs almost entirely on slow feedback with the bass nudging a zoom [11]. Both work. They are two layers, not
  two schools.
- **Drift** carries most of the motion: clocks driven by band level (the "time" uniforms of 1.4), tempo-locked
  slow waves over 4 to 32 bars, simulations left to run. Slow parameters must be fed from smoothed sources or
  they jitter [25].
- **Hits** are few and sized by their place in the bar. From the music's own spine [04]: the one and the
  backbeats get the large, frame-wide gestures (and only these may be luminance flashes, section 1.4); other
  sixteenths get small, local or chromatic accents that are over in two or three frames.
- **State changes** (which effect owns the picture, fold counts, palettes, camera targets) happen on phrase
  lines, one at a time [04].
- Route different lanes to different things; the commonest fault is everything on the kick [25].
- A rough share that matches the sources' emphasis: most of what moves should be drift, perhaps a fifth hits
  [unsourced].

---

## 5. Table: effect, passes, buffers, cost, driver, legibility

Cost classes at full size on the target card, unmeasured [unsourced]: **trivial** under 0.05 x 10^9 reads a
frame; **small** to 0.15; **moderate** to 0.5; **heavy** above, and should run at half size or accumulate.
"pp" is a ping-pong pair.

| | effect | passes a frame | buffers kept | cost | best driver | hold on the picture |
|---|---|---|---|---|---|---|
| E01 | feedback synth | 1 | 1 pp RGBA16F full | trivial | kick: zoom impulse; bass clock: rotation | source mix |
| E02 | datamosh (+ vectors, flow) | 1 + flow 4 to 8 small | 1 pp RGBA16F full; RG16F vectors | small | phrase: refresh; bass: gain | refresh rate |
| E03 | fluid | about 45 small + 1 | 3 pp + 2 at quarter or half; dye pp full | small to moderate | kick: impulse; snare: vortex pair | dye re-injection |
| E04 | particles | 1 update + draw | 2 pp state 2048 x 1024 | small | kick: impulse; phrase: spring | home spring |
| E05 | slit-scan | 1 write + 1 | array of 64 to 96 half-size layers (0.3 to 0.5 GB) | trivial | bar: delay map; fill: freeze | maximum delay |
| E06 | reaction-diffusion | 8 to 20 + 1 | 1 pp RG16F half | small to moderate | kick: stamp; phrase: species | mask opacity, seeding |
| E07 | conformal remaps | 1 | none | trivial | phrase: fold or parameter | coordinate blend |
| E08 | relief | 1 + 1 | height R16F half | moderate | backbeat: light; phrase: focus | strength |
| E09 | pixel sort | 8 to 32 | 1 pp full + mask | moderate | downbeat: latch; bass: threshold | threshold |
| E10 | strobe, invert, palette | 1 | limiter state | trivial | backbeat, bar, drop | none needed |
| E11 | transitions | 1 | borrows | trivial | phrase | duration |
| E12 | fractal scenes | 1 heavy (+ accumulate) | colour + distance; history | heavy | bass clock: speed; phrase: folds | projector alignment |
| E13 | volumetric light | 1 to 2 at half | history | moderate to heavy | backbeat: light; phrase: density | density |
| E14 | strands | 3 field + draw or 1 | tensor field half | moderate | kick: length; beat: travelling pulse | field blend |
| E15 | anisotropic Kuwahara, lines | 3 to 4 | tensor | heavy at full, moderate at half | phrase: radius; bass: threshold | radius |
| E16 | CRT, VHS | 2 to 3 | none | trivial | snare: tear; phrase: roll | amount |
| E17 | glyphs, dither | 2 to 3 | atlas, shape table | trivial | bar: cell size | cell size |
| E18 | terrain | draw | none | small | kick: height; beat: ripple | camera elevation |
| E19 | domain warp | 1 at half + 1 | field RG16F half | small | bass envelope: amount | amount |
| E20 | tunnel | 1 | none | trivial | bass clock: speed | coordinate blend |
| E21 | iridescence | 1 | none | small | bass clock: thickness | none needed |
| E22 | dispersion, glass | 1 | none | small | kick: spread | none needed |
| E23 | metaballs | 2 to 3 | blob field half | small to moderate | kick: threshold | drop size |
| E24 | flares, dirt | 3 small | dirt texture | small | backbeat | none needed |
| E25 | motion blur, accumulation | 1 to 2, or N stage draws | vectors; history | small to moderate | phrase: shutter | raises it |
| E26 | tone map, grade | 1 | LUT | trivial | section: palette; drop: exposure | none needed |
| E27 | blocks, tiles | 1 | borrows E05 | trivial | sixteenth: swap; one: solve | share of blocks |
| E28 | screen-space reflection | 1 | depth, normals | moderate | none | none needed |

---

## 6. The existing sixteen: what they do now and how the best versions differ

Read from `mindstream/fx.py` and `gl_view.py`. The order they run in is: ripple, shatter, glitch, gyroid, paint,
edges, halftone, rays, bloom, streak, bokeh, then a final pass with lens, colour split, vignette, tint and
grain; flow lives inside the trail pass; particles are drawn over the scene before the chain [code].

### 6.0 The pipeline under them (do this first)

| now [code] | consequence | change |
|---|---|---|
| pictures and film uploaded as `GL_RGB8` | all blending, blurring and glow on gamma-encoded values | upload as sRGB; work linear |
| scene and trail targets are RGBA8; only the effect chain is RGBA16F | a fade of 0.985 cannot lower values under 33 of 255; at 0.98, under 25 [computed]. Trails stall at grey. Highlights clip at 1 before bloom sees them. Additive particles clip. | RGBA16F for scene and trails |
| bright roll-off (tanh above 0.8, per channel) inside the glow composite, applied after bloom and again after streak | two tone curves, hue shifts in highlights, later passes see compressed values | one exposure and tone map at the end (E26) |
| no dither | banding in every soft gradient (vignette, glow, fog) on an 8-bit output | blue-noise dither last [49] |
| the chain runs at the supersampled size | at sharp 2, every effect costs four times as much | resolve first, then run effects |
| aspect not corrected in lens bulge and vignette | on 21:9 both are ellipses 2.4 times wider than tall | use aspect-corrected radius |
| sine-based hashes everywhere | visible structure, driver differences | integer hash or blue-noise texture |
| music arrives as `pulse` (one envelope) and `beat` (a count) | every effect moves on the same thing | per-lane envelopes, bar and phrase phase, per-beat random (1.4) |

### 6.1 The sixteen

**1. Flow.** *Now:* inside the trail pass, the read coordinate is offset by the curl of a two-octave value noise
taken by finite differences, 0.4 percent of the frame a frame, doubled on the beat [code]. It is a fixed
wobble, not a flow: nothing is conserved and nothing responds to the picture. *Best version:* a real velocity
field. Either the fluid of E03 (pressure-projected, forces from kicks and from motion vectors), or, as the
light alternative, proper curl noise from gradient noise at five octaves with slow advection of the noise
domain itself (E19). Advect with a sharper filter than bilinear, in float. *Verdict: cheap; replace by E03.*

**2. Particles.** *Now:* up to two million additive soft points, each placed by a hash of its number, moved by
a sine swirl, coloured from the picture at a uniformly random place; brightness normalised by count [code].
Stateless. *Best version:* E04. State in textures; true curl noise; a home spring; forces from kicks, flow and
fluid; placement weighted toward bright parts of the picture; additive in HDR; size and focus from depth;
streaks from last position. *Verdict: good count, no physics; the largest single upgrade available.*

**3. Ripple.** *Now:* three analytic rings from the last three beats displace the read coordinate, plus a
standing sine wobble and a fake highlight [code]. *Best version:* a simulated height field. Two float buffers
(this height and last): `next = 2 h - previous + c^2 * laplacian(h)`, times a damping of about 0.99
[snippet 83]. Drops on kicks at chosen points; the picture's own edges or the cube's silhouette as obstacles
or sources; refraction by the height's gradient with dispersion (E22); a specular term from the normal in HDR,
which then blooms. Waves reflect, interfere and die away naturally, which analytic rings cannot. Notch ships
exactly this as Water Ripples [3]. *Verdict: cheap; a small upgrade for a large gain.*

**4. Shatter.** *Now:* one 3 x 3 Voronoi search; each cell shifts the read coordinate by a random constant; the
crack line is the difference of the two nearest distances [code]. Quilez's article on this point says that
difference is not a distance: line width swells and pinches with the spacing of the cell points. The exact
border distance needs a second search over the neighbours of the winning cell, projecting onto each bisector
[61]. *Best version:* exact borders [61]; each shard a tilted plane with its own normal, so it refracts by a
gradient across the shard rather than a constant, with dispersion at the edges; shards that actually separate
(their offset grows from an impact point outward on a kick and relaxes); several layers of glass at different
scales; a bevel highlight from the border distance in HDR. *Verdict: cheap at the lines and the refraction.*

**5. Glitch.** *Now:* per-sixteenth random bands that slide, blocks that jump, line tear, colour split,
posterised blocks, noise [code]. Respectable. *Best version:* E27's vocabulary: multi-scale blocks, damage that
is held for several sixteenths, frozen blocks from a frame ring, compression-style block averaging; plus real
datamosh (E02) and pixel sort (E09), which are what "glitch" now means to an audience [3]. Move it late in the
chain. *Verdict: fair; widen rather than replace.*

**6. Gyroid lattice.** *Now:* 96 steps, a relaxation of 0.85 on a field scaled by 0.55, six-sample normals,
three-sided picture mapping, shading from facing angle and step count, distance fog into the picture [code].
*Best version:* E12. A moving light with soft shadow (`min(k h / t)` [57]); tetrahedron normals; fog that
scatters the light (E13); blue-noise jitter of the ray start with accumulation; a reflection march; distance
output so that depth of field and shafts can use it; the picture projected from a home camera; and more
scenes (Menger, Mandelbox, folded fractals, tunnels). The three-sided mapping should use explicit gradients or
its seams sparkle. *Verdict: a sound start with flat lighting.*

**7. Oil paint.** *Now:* the original four-square Kuwahara with a hard choice of the least-variance square,
radius 2 to 8, up to 324 reads [code]. This is the version every source describes as the starting point
because of its blocky artefacts and flicker [51]. *Best version:* E15's anisotropic filter: structure tensor,
eight soft sectors in an ellipse that follows the edges, weighted blend [51, 52]. Then, for paint rather than
smoothing: a canvas or brush height from the filter's own output lit as relief (E08), and a slight
saturation lift. Run at half size. *Verdict: the cheapest of the sixteen relative to the state of the art.*

**8. Neon edges.** *Now:* one 3 x 3 Sobel on luminance at a two-point spacing, coloured by edge direction,
brightened on the beat [code]. Sobel responds to noise and gives broken double lines. *Best version:* E15's
flow-based difference of Gaussians: lines that are continuous, even in width and follow contours
[snippet 53]; thickness from the blur scale, so thick and thin lines are a parameter; in HDR with values well
above 1 so that the bloom makes the neon (the colour should come from the bloom spill, not from painting the
line bright); a slow travelling pulse along the line direction. *Verdict: cheap.*

**9. CMYK halftone.** *Now:* four rotated dot screens at 15, 75, 0 and 45 degrees, dot area proportional to
ink, simple black extraction, multiplied onto paper white, 55 to 120 cells up the height [code]. This is
already most of the proper method. *Best version:* ink read once per dot cell (at the cell centre, from a
blurred level) so dots are round rather than carved by sub-cell detail, with a control to blend toward the
present per-point reading; edge softness from the screen-space derivative of the cell coordinate rather than a
fixed 0.06, so dots stay crisp at every size; dot gain (ink spreading) as a curve on area; elliptical dots
that chain along one axis in mid-tones; per-ink misregistration, a point or two of offset per plate, kicked by
the beat; done in linear light. *Verdict: good; refine.*

**10. Light rays.** *Now:* 96 reads toward a light point that wanders the frame, bright-pass at 0.55, decay
0.975 a step, white-noise jitter, full size [code]. It is the GPU Gems method [34] done straight. *Best
version:* blue-noise or interleaved-gradient jitter advanced each frame [47, 48] (white noise shows as grain);
half size with an edge-aware enlargement; the bright-pass on HDR values so only real highlights throw shafts;
the light placed where the picture is actually bright (the brightest cell of a small mip level) or behind the
cube so the cube's silhouette cuts the shafts; and for the full effect, marched fog (E13). *Verdict: fair;
the jitter and the light's position are the weak points.*

**11. Bloom.** *Now:* the 13-read downsample and 3 x 3 tent upsample from the standard method, six levels, a
soft-knee bright-pass at 0.6 on the first level, levels summed additively, laid over at 0.55, then the
roll-off [code]. The filters are the right ones [36, 37]. What differs from the best practice:
- **Threshold.** The physically based version has none: the whole HDR frame is blurred and blended in at a
  low strength (about 0.04), so only genuinely bright things glow visibly and nothing pops in or out [36]. A
  threshold on 8-bit-range values is why the present glow needs a knee. With an HDR scene, drop it.
- **Fireflies.** On the first downsample only, weight each group of four by `1 / (1 + luminance)` so a single
  very bright point does not flicker as it moves [36, 37].
- **Energy.** Blend rather than add (`mix(scene, bloom, 0.04)`), or weight the levels so their sum is 1; the
  present unweighted sum of six levels brightens the whole frame as amount rises.
- **First step.** The pyramid's first level is half the *window* size but reads the *supersampled* scene, so
  at sharp 2 it is a four-times reduction through a filter built for two [code, 36]: it aliases. Resolve
  first.
- **Per-level tint and weight** (a wider, redder outer glow) and **lens dirt** (`bloom * (1 + dirt * k)`)
  [36] are the finishing touches.
*Verdict: right filters, LDR thinking.*

**12. Anamorphic streaks.** *Now:* a bright-pass quarter-size copy blurred horizontally twice with a 49-read
Gaussian (strides 1.5 and 5), tinted blue, added at 1.6 [code]. A Gaussian gives a soft bar. Real streaks have
a tight bright core and a very long faint tail. *Best version:* a horizontal-only pyramid: halve the width
repeatedly (five to seven times) keeping the height, then build back up adding the levels with weights, exactly
as bloom but in one axis; this gives the long tail for a few reads a level [unsourced]. HDR input without
threshold. Slight vertical thickness variation and a faint second, shorter streak; tint by level (blue far,
white near). *Verdict: fair; wrong profile.*

**13. Bokeh.** *Now:* at full size, 72 reads on a golden-angle disc whose radius grows with distance from the
screen centre (up to about 32 points at 1440), each read weighted by 1 + 6 x luminance^4 so bright points
dominate, with a white-noise rotation [code]. Three limits: 72 reads over a disc of about 3,150 points is one
read per 44 points [computed], so it is noisy; the radius comes from screen position, not from depth; and
the weighting stands in for highlights that the 8-bit scene has already clipped. *Best version* [39, 37,
snippet 37, 40]:
- a **circle of confusion per point** from depth (the depth buffer of the surface and cube; the particle's
  own depth; E08's height; a marched scene's distance), signed for near and far;
- **half size**, after a prefilter that is itself weighted against fireflies (`1 / (1 + max channel)`) [39];
- **scatter-as-gather**: each sample contributes only if *its own* circle of confusion reaches the centre
  point (`saturate((coc_sample - distance + 2) / 2)`), which stops sharp things leaking into blur and blur
  leaking over sharp things [39];
- **near and far gathered separately**, the near layer laid over the sharp image with its own coverage [39,
  40];
- 22 to 49 reads in rings [39, snippet 37], rotated per pixel by blue noise, then a small tent or
  "fill" filter to hide the gaps [39, 40];
- **in linear HDR, before bloom**: highlights then open into bright, hard-edged discs by themselves, which is
  the whole look, and no luminance weighting is needed;
- aperture shape by mapping the disc to a polygon [40]; optionally cat's-eye squashing toward the edges and a
  faint bright rim.
*Verdict: a good gather with the wrong inputs; needs depth, HDR and the sample test.*

**14. Lens distortion with spectral fringing.** *Now:* a cubic bulge and eight reads across the spectrum with
triangular red, green and blue weights; a three-read split when the lens is off; vignette [code]. The
spectral idea is right. *Best version:* aspect-corrected radius (it is elliptical now); 16 to 24 reads with
per-pixel jitter so large spreads do not show eight ghosts; weights from a fitted spectrum [70]; distortion
with a second coefficient (`1 + k1 r^2 + k2 r^4`) for moustache shapes; vignette as the fourth power of the
cosine of the off-axis angle, in linear light; the fringe scaled by the distortion's own derivative so it
appears where a real lens would show it [unsourced]. *Verdict: good; fix the aspect and the count.*

**15. Film grain.** *Now:* one uniform white-noise value per screen point per frame, stronger in the dark, and
a row-alternating darkening called scan lines [code]. At this pixel density single-point white noise is nearly
invisible, and alternate-row darkening at 1440 rows is either invisible or shimmers. *Best version:* noise
with a grain *size* (generate at half or third size with a soft kernel, or use a blue-noise tile scaled up),
so it reads as grain; applied to the image before the tone curve as a multiplicative variation of exposure,
strongest in the mid-tones, weaker in deep shadow and highlight, as film behaves [unsourced]; slightly
different per colour channel; a new field every frame. Remove the scan lines from here (they belong to E16).
And separately, always on: the final dither. *Verdict: cheap.*

**16. Supersampling.** *Now:* the scene is drawn at 1 to 2 times the window in quarter steps and brought down
by the single bilinear read of the last pass [code]. At exactly 2 that read is a fair box filter; at 1.25 to
1.75 it is a point sample of a bilinear surface, which aliases; and the lens pass's displaced reads undo the
alignment even at 2. *Best version:* a separate resolve pass with a proper reduction filter (a small tent or
Mitchell-like kernel sized to the ratio), run before the effect chain; resolve weighted against very bright
samples (the same `1 / (1 + luminance)` idea) so HDR highlights do not alias [unsourced]; or, for the same
cost and better edges, native size with jitter and accumulation (E25) and motion vectors from the stage.
*Verdict: works only at exactly 2, and makes the whole chain pay for it.*

### 6.2 The trail pass itself

Not one of the sixteen but the heart of the look: last frame, folded by a kaleidoscope, swirled, zoomed,
drifted in colour, faded, with a faint tiled copy of the picture added [code]. It is E01 in outline. The
upgrades are in E01: float buffer (the stall above), a sharper resample, displacement by the frame's own
luminance, hue rotation in place of the channel leak, a limiter, rates defined per second so that the look
does not change if the frame rate does, and a fade expressed as a half-life in beats (0.968 a frame for one
beat at 170 [computed]).

---

## 7. What could not be found, and how far to trust this

- **No ranking by use.** Nothing found counts how often each effect appears in real shows. "Recurs" here means:
  is a stock node in the stage tools, appears in tutorials and practitioner lists, and is named in interviews.
- **Drum & bass specifics are thin.** One detailed technical account (Noisia's show [16]) and one general
  guide [23]. No interview was found with the visual teams of Let It Roll or Rampage, or for Chase & Status,
  Sub Focus, Pendulum or Camo & Krooked, describing effects used. Nothing at all was found on jungle-specific
  visual practice.
- **Shadertoy could not be fetched** (the site refused). What is said about it rests on search summaries and on
  articles by its authors.
- **Papers not read in full**: Kyprianidis on anisotropic Kuwahara (abstract only [52]; constants from memory
  and from [51]); Winnemoller on extended difference of Gaussians (search summary); Bridson on curl noise (the
  file would not render); McGuire on motion blur (page empty); Jimenez's slides (summary page [37]; the sample
  counts are from a search summary); Hvidtfeldt's distance-estimation series (certificate error; Mandelbox and
  Mandelbulb estimates are from a search summary and memory); Quilez's domain-warping article (not found at
  its address); the horizon-style cloud papers (summary only). Each is marked where used.
- **Asendorf's sort** is described from memory of the sketch; the repository page showed only pictures [74].
  The fragment-shader exchange sort is from a search summary of an article that would not load [75].
- **The hyperbolic tiling construction** and its circle formula are from memory, checked only for internal
  consistency.
- **Every cost figure is arithmetic on read counts.** No timing was taken. The stated frame budget in reads is
  a guess at the order of magnitude.
- **Perceptual claims about gist and layout** (4.3) are from general knowledge, not from sources consulted for
  this report.
- **Flash limits** are quoted from the web accessibility guideline [30], which was read; the broadcast
  recommendation of the same form was seen only in summary [31]. Neither is a medical assurance.

Trust, in short: the simulation, lens and tone mathematics in E01 to E03, E06, E13, E26 and section 6 items 11
and 13 are from primary sources read directly and can be built from. The fractal estimates, the Kuwahara
constants and the tiling should be checked against the papers before relying on exact numbers. Everything
about what is "best" in live practice is a reasoned reading of limited evidence.

---

## 8. Sources

Read directly unless marked. "snippet" means only a search summary was seen, or the page failed to load.

**Tools and what they ship**

1. Resolume, Effects (support manual). https://resolume.com/support/en/effects
2. Crazy Artist, Top effects for Resolume. https://crazyartist.net/en/top-effects-for-resolume-that-you-have-to-try-out/
3. Notch manual, Post-FX node reference. https://manual.notch.one/2026.1/en/docs/reference/nodes/post-fx/
4. Notch manual, Particles and Affectors (snippet). https://manual.notch.one/2026.1/en/docs/reference/nodes/particles/affectors/
5. CDM, Notch explained and reviewed. https://cdm.link/notch-tool-explained-and-reviewed-for-mere-mortals/
6. Notch, Made with Notch case pages (snippet). https://www.notch.one/madewithnotch/coldplay-music-of-the-spheres-tour-2022/
7. Derivative, Feedback TOP. https://docs.derivative.ca/Feedback_TOP
8. Derivative, Time Machine TOP. https://docs.derivative.ca/Time_Machine_TOP
9. Derivative, Optical Flow TOP. https://derivative.ca/UserGuide/Optical_Flow_TOP
10. The Interactive & Immersive HQ, Understanding feedback loops in TouchDesigner (snippet). https://interactiveimmersive.io/blog/touchdesigner-lessons/understanding-feedback-loops-in-touchdesigner/ ; allTD, Metallic fluid using feedback, blur and displace (snippet). https://alltd.org/metallic-fluid-in-touchdesigner-using-feedback-blur-and-displace-top-super-fast-tutorial-series/
11. Ryan Geiss, MilkDrop preset authoring guide. http://www.geisswerks.com/milkdrop/milkdrop_preset_authoring.html
12. Synesthesia, SSF audio uniforms. https://app.synesthesia.live/docs/ssf/audio_uniforms.html
13. Lumen, analogue-style video synthesiser (snippet). https://lumen-app.com/
14. ofxFlowTools (optical flow, fluid and particles in GLSL). https://github.com/moostrik/ofxFlowTools
15. Haxademic, optical-flow fragment shader (algorithm described, no code taken). https://github.com/cacheflowe/haxademic/blob/master/data/haxademic/shaders/filters/optical-flow.glsl
85. ISF, Interactive Shader Format documentation. https://docs.isf.video/

**Shows, artists, practice**

16. Resolume blog, Make Some Noisia (the Outer Edges show). https://resolume.com/blog/14308
17. It's Nice That, Weirdcore on Aphex Twin's live visuals. https://www.itsnicethat.com/features/weirdcore-aphex-twin-field-day-050617-miscellaneous
18. Vice, Aphex Twin's Kinect-powered visuals (snippet). https://www.vice.com/en/article/aphex-twin-gets-body-dysmorphic-kinect-powered-visuals/
19. CDM, Three layers of live visuals: Flying Lotus, Strangeloop, Timeboy (snippet). https://cdm.link/three-layers-of-live-visuals-flying-lotus-strangeloop-timeboy-in-immersive-scrims/
20. Cycling '74, An interview with Tarik Barri (snippet). https://cycling74.com/articles/an-interview-with-tarik-barri
21. Live Design, Eric Prydz HOLO (snippet). https://www.livedesignonline.com/news/eric-prydz-holo-stuns-holographic-3d-fx-powered-by-avolites-ai ; DJ Mag (snippet). https://djmag.com/content/eric-prydz-shares-visuals-new-holo-live-tour-watch
22. Unreal Engine, Moment Factory's real-time visuals for Phish at Sphere (snippet; page refused). https://www.unrealengine.com/spotlights/moment-factory-redefines-live-concerts-with-real-time-visuals-for-phish-at-sphere
23. Ticket Fairy, VJ grammar for drum & bass vs deep 140. https://www.ticketfairy.com/blog/2025/08/24/vj-grammar-for-drum-bass-vs-deep-140-tailoring-visuals-for-bass-music-festivals/
24. HeavyM, How to sync visuals with music (snippet; page refused; the band-to-visual figures come from the search summary of this and [23]). https://www.heavym.net/how-to-sync-visuals-with-music-audio-reactive-projection-mapping-made-simple/
25. VJ Loop Studio, Audio-reactive visuals: every source, route and modulator. https://vjloopstudio.com/posts/audio-reactive-guide/
26. K. Ferguson, Audio-reactive programming: envelope followers. https://kferg.dev/posts/2020/audio-reactive-programming-envelope-followers/
27. STV in Motion, Three beginner VJ mistakes. https://www.stvinmotion.com/three-beginner-vj-mistakes/
28. MotionLab, VJ loop design for live visuals. https://www.motionlab.art/guides/vj-loop-design
30. W3C, Understanding WCAG 2.3.1: three flashes or below threshold. https://www.w3.org/WAI/WCAG21/Understanding/three-flashes-or-below-threshold.html
31. ITU-R BT.1702 and a gap analysis of photosensitivity guidelines (snippet). https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1702-3-202311-I!!PDF-E.pdf ; https://pmc.ncbi.nlm.nih.gov/articles/PMC11872230/
04. Companion report in this folder: `04_legibility_beyond_repetition.md`, and the overlay in `README.md`.

**Simulation**

32. Karl Sims, Reaction-diffusion tutorial. https://www.karlsims.com/rd.html
33. Mark Harris, Fast fluid dynamics simulation on the GPU, GPU Gems chapter 38. https://developer.nvidia.com/gpugems/gpugems/part-vi-beyond-triangles/chapter-38-fast-fluid-dynamics-simulation-gpu
35. Crane, Llamas, Tariq, Real-time simulation and rendering of 3D fluids, GPU Gems 3 chapter 30 (not fetched; cited from memory). https://developer.nvidia.com/gpugems/gpugems3/part-v-physics-simulation/chapter-30-real-time-simulation-and-rendering-3d-fluids
79. Chris Wellons, A GPU approach to particle physics. https://nullprogram.com/blog/2014/06/29/
80. Bridson, Hourihan, Nordenstam, Curl-noise for procedural fluid flow (file would not render; from memory). https://www.cs.ubc.ca/~rbridson/docs/bridson-siggraph2007-curlnoise.pdf
83. Height-field ripple simulation (snippet). https://www.mysimulator.uk/content/articles/wave-equation-2d.html
84. Horn-Schunck optical flow with a multi-scale strategy, IPOL (snippet). https://www.ipol.im/pub/art/2013/20/article_lr.pdf

**Lens, light, tone**

34. Kenny Mitchell, Volumetric light scattering as a post-process, GPU Gems 3 chapter 13. https://developer.nvidia.com/gpugems/gpugems3/part-ii-light-and-shadows/chapter-13-volumetric-light-scattering-post-process
36. LearnOpenGL, Physically based bloom. https://learnopengl.com/Guest-Articles/2022/Phys.-Based-Bloom
37. Jorge Jimenez, Next generation post processing in Call of Duty: Advanced Warfare (summary page; slides not read). https://www.iryoku.com/next-generation-post-processing-in-call-of-duty-advanced-warfare/
38. Catlike Coding, Bloom. https://catlikecoding.com/unity/tutorials/advanced-rendering/bloom/
39. Catlike Coding, Depth of field. https://catlikecoding.com/unity/tutorials/advanced-rendering/depth-of-field/
40. Adrian Courreges, UE4 optimized post-effects. https://www.adriancourreges.com/blog/2018/12/02/ue4-optimized-post-effects/
41. Bart Wronski, Separable disk-like depth of field. https://bartwronski.com/2017/08/06/separable-bokeh/
42. Bart Wronski, Bilinear down/upsampling and the half-pixel offset. https://bartwronski.com/2021/02/15/bilinear-down-upsampling-pixel-grids-and-that-half-pixel-offset/
43. John Chapman, Screen-space lens flare. https://john-chapman.github.io/2017/11/05/pseudo-lens-flare.html
44. Emilio Lopez, Temporal AA and the quest for the holy trail. https://www.elopezr.com/temporal-aa-and-the-quest-for-the-holy-trail/
45. Krzysztof Narkowicz, ACES filmic tone mapping curve. https://knarkowicz.wordpress.com/2016/01/06/aces-filmic-tone-mapping-curve/
46. Tone mapper comparisons (snippet). https://www.khronos.org/news/press/khronos-pbr-neutral-tone-mapper-released-for-true-to-life-color-rendering-of-3d-products ; https://cgmeerkat.github.io/blog/who-needs-a-tonemapper/
47. Alan Wolfe, Interleaved gradient noise. https://blog.demofox.org/2022/01/01/interleaved-gradient-noise-a-different-kind-of-low-discrepancy-sequence/
48. Alan Wolfe, Ray marching fog with blue noise. https://blog.demofox.org/2020/05/10/ray-marching-fog-with-blue-noise/
49. Christoph Peters, Free blue noise textures. http://momentsingraphics.de/BlueNoise.html
54. Maxime Heckel, Real-time cloudscapes with volumetric raymarching. https://blog.maximeheckel.com/posts/real-time-cloudscapes-with-volumetric-raymarching/
55. Volumetric cloud and fog references (snippet). https://arxiv.org/pdf/1609.05344 ; https://bartwronski.com/wp-content/uploads/2014/08/bwronski_volumetric_fog_siggraph2014.pdf
81. McGuire and Mara, Efficient GPU screen-space ray tracing (snippet). https://jcgt.org/published/0003/04/04/paper.pdf
82. McGuire et al., A reconstruction filter for plausible motion blur (page did not load). https://casual-effects.com/research/McGuire2012Blur/index.html

**Stylisation and print**

50. Surma, Ditherpunk. https://surma.dev/things/ditherpunk/
51. Maxime Heckel, On crafting painterly shaders. https://blog.maximeheckel.com/posts/on-crafting-painterly-shaders/
52. Kyprianidis, Kang, Dollner, Anisotropic Kuwahara filtering on the GPU (abstract page). https://www.kyprianidis.com/p/gpupro/
53. Winnemoller, Kyprianidis, Olsen, XDoG: an extended difference-of-Gaussians compendium (snippet). https://www.sciencedirect.com/science/article/abs/pii/S009784931200043X
76. Timothy Lottes, public-domain CRT shader (snippet). https://gist.github.com/equalent/da8d18b4ddfe59907c58708c5253ba7b
77. Modulate, VHS effect: every tape artifact explained. https://modulate.to/effects/vhs/
78. Alex Harri, ASCII characters are not pixels. https://alexharri.com/blog/ascii-rendering

**Glitch**

72. ompuco, Creating your own datamosh effect. https://ompuco.wordpress.com/2018/03/29/creating-your-own-datamosh-effect/
73. Keijiro Takahashi, KinoDatamosh. https://github.com/keijiro/KinoDatamosh
74. Kim Asendorf, ASDFPixelSort. https://github.com/kimasendorf/ASDFPixelSort
75. ciphrd, Pixel sorting on shader using well-crafted sorting filters (snippet; page redirected and did not load). https://ciphrd.com/2020/04/08/pixel-sorting-on-shader-using-well-crafted-sorting-filters-glsl/

**Shaders, fractals, maps**

56. Inigo Quilez, Menger fractal. http://iquilezles.org/articles/menger/
57. Inigo Quilez, Soft shadows in raymarched SDFs. http://iquilezles.org/articles/rmshadows/
58. Inigo Quilez, fBM. http://iquilezles.org/articles/fbm/
59. Inigo Quilez, Palettes. http://iquilezles.org/articles/palettes/
60. Inigo Quilez, Mandelbulb. http://iquilezles.org/articles/mandelbulb/
61. Inigo Quilez, Voronoi edges. http://iquilezles.org/articles/voronoilines/
62. The Book of Shaders, chapter 13: fractal Brownian motion. https://thebookofshaders.com/13/
63. Mikael Hvidtfeldt Christensen, Distance estimated 3D fractals (snippet; certificate error). http://blog.hvidtfeldts.net/index.php/2011/11/distance-estimated-3d-fractals-vi-the-mandelbox/
64. Mercury, hg_sdf. https://mercury.sexy/hg_sdf/
65. Pekka Vaananen, How a 64k intro is made. https://www.lofibucket.com/articles/64k_intro.html
66. Reinder Nijhoff, Escher and the Droste effect. https://reindernijhoff.net/2014/05/escher-droste-effect-webgl-fragment-shader/
67. de Smit and Lenstra on Escher's Print Gallery, via secondary pages (snippet). https://www.josleys.com/article_show.php?id=82
68. Hyperbolic tilings and Moebius maps (snippet). https://github.com/felixbauckholt/hyperbolic_canvas
69. Alan Zucconi, The mathematics of thin-film interference. https://www.alanzucconi.com/2017/07/25/the-mathematics-of-thin-film-interference/
70. Alan Zucconi, Improving the rainbow. https://www.alanzucconi.com/2017/07/15/improving-the-rainbow/
71. Belcour and Barla, A practical extension to microfacet theory for the modeling of varying iridescence (snippet). https://belcour.github.io/blog/slides/2017-brdf-thin-film/slides.html
86. Shadertoy (site refused fetching; search summaries only). https://www.shadertoy.com/

Numbering is not continuous: a few numbers were dropped while writing.

