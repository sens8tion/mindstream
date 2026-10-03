# mindstream

**Its content does not exist unless it is being watched.** Nothing is made ahead, nothing is kept behind, and
when nobody is looking nothing is made at all.

A story that exists only while it is running. A language model on another machine writes it a beat at a
time; each beat becomes a picture, pairs of pictures become short films with sound, and a rhythm section
plays under all of it. You steer it by typing. Nothing is written to disk: text, pictures, film and sound
live in memory and in pipes between processes, and are gone when it stops.

## Warning

Read this before running it, and before showing it to anyone else.

- **It can produce anything.** The story, the pictures, the films and the spoken or sung words are generated
  live and are not filtered, reviewed or limited by this code. What comes out depends entirely on the models
  you choose and on what you type. With unrestricted models it can produce violent, sexual, disturbing or
  otherwise harmful material, including material that was not asked for. You choose the models; you are
  responsible for what they make, for who sees it, and for whether it is lawful where you are.
- **Nothing is kept, so nothing can be checked afterwards.** There is no log and no record. That is the point
  of it, and it also means there is no way to review what a session showed.
- **It flashes.** The viewer pulses, strobes, flashes on every new picture and can fill the screen with fast
  kaleidoscopic motion. It may trigger seizures in people with photosensitive epilepsy, and can cause
  nausea or disorientation in anyone. Do not use it if that could affect you or someone in the room. Lower
  the intensity with the Down key, or hold the picture still with Space.
- **It is meant to be overwhelming.** Sustained use is tiring. The sound includes heavy sub bass: set the
  volume before starting, especially on headphones.
- **It works the machine hard.** It uses all of the GPU's memory and most of the system's, for as long as it
  runs. Watch temperatures on a laptop.

Not for children. Not for an audience that has not agreed to see unfiltered generated material.

## What it can do

[See it](https://photos.app.goo.gl/e3B4M1Tg3YSssVDX7) (the visuals) and [hear it](https://soundcloud.com/sens8tion/doesntexist) (the sound).
The Warning above applies to both.

## Watched, or it is not there

- Closing the viewer ends the session: every stage stops, and the story is cleared from the remote host.
- Minimising the viewer holds everything: no new beat is written, no picture or film is started, the sound
  stops. The step already under way when you looked away is finished and waits, unseen, in memory; nothing
  follows it until the window is back.
- Nothing is written to disk at any point, so there is nothing to find afterwards.

A window that is open but covered by another, or a screen nobody is in front of, still counts as watched: the
code can tell that a window is minimised, not whether eyes are on it.

## The stages

| Stage | File | Runs on |
|---|---|---|
| Launcher: starts everything, schedules pictures and film | `run_stream.py` | any Python |
| Story feed: beats, prompts, direction, steering | `story_feed.py` | any Python; talks to Ollama on the remote host over an SSH tunnel |
| Steer reader: a small model that reads a typed steer when llama is away | `steer_intent.py` | CPU |
| Picture generator | `img_gen.py`, `mindstream/painter.py` | the main GPU |
| Text encoder helper for pictures | `te_amd.py` | the integrated GPU (DirectML) |
| Film generator (video with sound) | `vid_gen.py` | the main GPU, using ComfyUI's code as a library |
| Viewer: moving surface, flow strip, running account | `gl_view.py` (`img_view.py` is the plain fallback) | OpenGL |
| Sound: the rhythm section, with the films' sound and pulled samples chopped over it as named layers | `mindstream/groove.py`, `mindstream/mixer.py`, `mindstream/chop.py` | CPU |
| Sample puller: finds a sound in the local library or a free archive, in memory | `sample_pull.py` | CPU |
| Stand-ins for trying the viewer and launcher with no models | `demo/fake_stage.py` | CPU |

Stages talk in one format: one JSON object per line, binary payloads in base64. The message types are
`image`, `text`, `status`, `visual`, `clip`, `control`, `story`, `prompt`, `read`, `fresh` and `sample`.

## Running it

    mindstream --demo --view-args "--groove"            stand-in content, no models: for looking at the viewer
    mindstream --demo --knobs --visuals --view-args "--groove --bpm 170"      the same with both panels, at jungle tempo:
                                                        choose dnb on the knob panel to hear what jungle does
    mindstream                                          story and pictures
    mindstream --video ask                              films only when you type !film
    mindstream --video-preset test                      with short films between pictures
    mindstream --video-preset test --view-args "--groove"    with the rhythm section and everything below about sound

Nothing about a session is printed on the terminal: what you type, how it was read and what is happening are
shown in the viewer only. `--console` prints them on the terminal as well. Only a failure to start is always printed.

One session at a time: a second one is refused, because the stages need the whole GPU and most of the RAM.

## Steering

At `guide>` type what the story is about. The moment it has a theme, the viewer shows it as words on a test card, which
moves as any picture does, until the first picture is painted. A new theme is a clean cut: its card is on screen at
once and alone, with the old picture, its trails, the swarm and the film gone, and a picture still being painted for
the old theme is never shown. After that, anything typed at `steer>` shapes the story and is read for
what it asks of the music, the motion and the pictures. You can type straight into the viewer window instead
(useful full screen): the line appears above the caption, Enter sends it, Esc clears it. `/bye` stops everything,
clears the remote host and closes the window.

A line is read in three ways, quickest first:

1. **Exact words act at once.** Everything quoted in this README is of that kind. They are matched narrowly, so
   a line of story that merely contains such words is left alone.
2. **Plain words about pace and feel act within a couple of seconds**: "slower, gently", "give me a break then
   bring it back harder", "slow the photos down".
3. **Anything looser is worked out by llama** between its other jobs: "stick a delay on the tune", "another layer
   under the sub", "make the drums sound like a warehouse", "it's a bit much". That takes as long as llama takes.
   While llama is away a small model on this machine has a go instead, and it is cruder.

The panels at the sides of the viewer say what was understood, what will follow from it, and why each stream
changed. A steer about the story repaints the present scene with your words in it while llama writes the next
beat. To let something arrive with the story instead of jumping, say so: "gradually...", "...with the flow", or
start the line with `~`.

### Starting again

"new theme: a night market in the rain", "start afresh with ...", or `!new ...`: the story, its people and its
pictures start over from your words; the music and motion carry on.

Short instructions that open with the verb do one thing again from scratch, at once:

    replace all of the pics          new pictures for where the story is; the old ones leave the screen
    start the theme again            the same theme, a new story (also: restart the story, from the top)
    rebuild the musical intent       the music worked out again from the story as it stands, with new riffs
    reset the look                   motion and colour back to how a session starts
    redo everything                  all four

They can be joined ("replace the pics and rebuild the music"). The exact forms are `!redo pics`, `!redo story`,
`!redo music`, `!redo look`, `!redo all`.

### Exact settings

    !bpm 150            hold a tempo            !bpm auto      let it drift again
    !style twostep key F#m twinkle 0.8 sub 1 swing 0.3
    !break 8            the low end out for 8 bars while the drums run on, then back
    !rescore            new riffs, same style and key
    !bloom 0.8 rays 0.5 an effect on the picture, from 0 to 1 (see Effects)
    !image bloom 0.8    the same effects on each picture by itself (see Effects on each picture); !image off|hold|auto
    !structure 16       the session changes the style, key or riffs at most every 16 bars (8 unless you say)
    !chop drumfunk      how the sample layers are chopped; !role rain hook  a layer's part in it (see The chop engine)
    !cadence 20         a new picture every 20 s
    !film               a short film of the latest two pictures, now (1.5 s unless you say: !film 3, !film 4 beats; 3 s at most)
    !sample ...         a one-bar film made to be chopped (see Films)
    !pull ...           a sample from your library or a free archive (see Samples)
    !styles             the musical styles a clip can be asked for in
    !video ask|interlude|reel|off      ask = films only when you ask for one
    !chaos 1.4 folds 6 shape torus tint #ff4020

### Bringing things in from outside

Drag files from a folder onto the viewer window, or onto the visuals panel.

- A picture is shown as a new picture is.
- A video file (mp4, mov, webm, mkv, avi; its first eight seconds) plays as a film, and its sound becomes a layer
  named after the file, as a generated film's does. An animated GIF or WebP plays as a film without sound.
- A sound file (wav, flac, ogg, mp3, aiff; its first twenty seconds) becomes a layer named after the file, waiting
  to be brought in like any sample.

- A video at a web address: paste its link or its embed code into the "play link" box on the visuals panel (or drag
  the link onto that panel from a browser; a saved `.url` shortcut dropped on the viewer works too). A few seconds
  of it, from the time in the "from" box (`90`, `1:30`), for 1, 2, 4 or 8 seconds, are fetched over the network and
  play as a film whose sound becomes a layer. Sites generally forbid taking their streams outside their own
  player, and showing someone else's video to an audience needs their permission: use this for videos that are
  yours to use.

Each also goes on the palette. They are read into memory; nothing is copied or written.

### The viewer's keys

`Ctrl+F` full screen, `Ctrl+M` overlays, `Ctrl+Space` hold flat, `Ctrl+R` watch the last film again, `Ctrl+A` mute,
`Ctrl+G` rhythm section, `Ctrl+C` the newest film's sound in or out, `Ctrl+K` the knob panel and `Ctrl+V` the visuals
panel (each opens it, or closes it if it is open); `Up`/`Down` change the intensity and `Esc`
(with nothing typed) quits.

### The visuals panel

`mindstream ... --visuals` opens a second window for the screen (it can be used with `--knobs` or without), and
`Ctrl+V` in the viewer opens and closes it at any time. Both panels stay on top of the viewer. When the viewer is full
screen they become insets in it: each stays exactly where you left it, loses its border and title bar, and turns a
little see-through (nine tenths solid). Back in a window they get their borders back in the same place.
(Full screen is a borderless window over the whole monitor, so that they can sit on it.)

Each panel has a strip of its own across the top. Drag it to move the panel: that works in a window and, since an
inset has no title bar, it is how an inset is moved. While a panel is an inset, "small" on that strip shrinks it to
what is played with, at about a third of its area, without moving its top left corner; "full" brings everything
back as it was (what was put away has kept following the session). The small visuals panel is "now", five dials of
the look (Chaos, Folds, Spin, Zoom, Trails) with hold flat and flash, the object, and a dial for every effect
(that block can be shut with "hide", which makes the panel a third shorter). The small knob panel is the
strips (name, knob, mute and mutate), the super knob, the memories and the crossfader. Back in a window a panel is
whole again; the next time the viewer goes full screen it takes the form it had there last, for as long as the
panel stays open.

The panels are black with one bright colour, which is only used for what is live or yours. `--skin` chooses it:
`acid` (lime, the usual), `ember` (orange-red) or `ice` (cyan). Lists drop as windows the panel draws itself: fully
solid even on a see-through inset, light on dark, the row under the pointer lit and the one in force marked.

The window has one size (about 1045 by 720): nothing that arrives changes it. The line at its foot says what the
control under the pointer does, with its gestures, and reports what has just happened. From left to right it has
the look, the effects, and a column with what is in play, the boxes for words and links, the object and the shelf.

- **Now**, at the top right, shows what is on screen and sounding at this moment, in four places that do not move:
  the picture showing, the film on the reel, the sounds that are in, and the swarm of earlier pictures. What does
  not fit in its place is a count ("+6"); press it for the rest. To take a film, a sound or a swarm picture out of
  play, drag it out of the box, press the x that shows at its corner under the pointer, or right click it (the
  picture showing stays: there is always a picture). Anything dragged in from the shelf goes into play.
- **Shelf**, at the bottom right, is the palette: a small picture of everything played, in the order it came:
  pictures; films, with a violet corner; and sounds, with a green corner, showing their shape and name (every sample
  pulled in and every film's sound). What is in play is outlined. "all", "pictures", "films" and "sounds" narrow
  it, and the wheel moves it; it follows new arrivals only while it is showing its end, and otherwise says how many
  are new. Drag one into "now", or right out of the window toward the viewer, and it is in play again (a double
  click, or a right click, does the same). A picture arrives as a new picture does; a film starts on the
  next bar line, and the layer its sound already has is left as it is; a sound comes back as its layer on the next
  bar, made again if it had gone. The palette holds the last 200 pictures, 40 films and 60 sounds, in memory only:
  it is gone when the session ends.
- **Object**, above the shelf, puts an object with sides in place of the one surface: a card (two sides), a prism
  (three) or a cube (six). Each side has a box. Drag a picture or a film from the shelf onto a box (or right click
  it on the shelf) and that side
  shows it; a film goes round and round there, without its sound. Put several on one side and it fades from each to
  the next in time with the beat, a pulse between them, as often as the menu says (half a beat to eight). A
  side with nothing on it shows whatever is live, so a bare cube is the story on six sides. The object never
  stops turning: while the picture rests, and when it is held flat, it turns steadily about its upright so each side
  comes round the right way up (the Spin dial sets how fast); while the picture moves it tumbles as well. A click on
  a small picture in a side's box takes it off, "empty" clears every side, and "none" is the one surface again. The
  object is kept in a memory and comes back with it; a new theme takes it off.
- **Picture and film**, under "now": one box for words. PICTURE (or Enter) paints those words in the
  present scene next (typed: `!pic a fox in the snow`). FILM makes a film from the words alone, as `!sample` does; with
  no words it films between the latest two pictures, as `!film` does. The menu beside it sets how long the film
  is: a bar unless you choose beats or seconds, three seconds at most. Typed: `!sample 2s a fox running`,
  `!sample 4 beats a fox running`, `!film 2`. The box is outlined in amber until what was asked for arrives. Under
  it, PLAY LINK plays a few seconds of a video from its web address or embed code.
- **The look**, on the left: nine dials in three rows: time (Chaos, Rest: how long the picture rests flat, Move: how
  long it moves), space (Folds, Spin, Zoom) and layers (Trails, Swarm, colour Split). Drag a dial up and down from
  anywhere on its face (Shift for a quarter of the speed), turn it a step at a time with the wheel, or double click
  it to put it back where it started. A dial you have set wears a hot dot. Under them are the shape and the tint,
  with the one in force marked, and HOLD FLAT (lit while it holds) and FLASH.
- **Effects**, in the middle: a dial for each of the picture effects, which work and follow the session exactly as
  the look's dials do. The switch above them (screen / images, in the small form too) chooses what the dials show
  and set: the effects over the whole screen, or those on each picture by itself (the effects that only work on the
  whole screen are greyed then).

### Effects

32 effects can be laid on the picture, each one number from nothing to full (exposure, in stops, either side of nothing). They all start at nothing, and an
effect at nothing costs nothing: its work is skipped, and a few seconds later whatever it was remembering is let go
from the graphics card. Typed, each is set by name: `!bloom 0.8`, `!fluid 0.7 relief 0.5`, `!bloom 0` to take it
off. They are kept in a memory with the rest of the look, and they move smoothly to where they are set.

| | |
|---|---|
| `flow` | the trails are carried along like smoke in moving air |
| `particles` | the picture as a cloud of up to four million points that remember where they are: born in its bright places and edges, carried on a curling current, blown off on the beat and pulled home on the bar |
| `fluid` | the picture's colours carried in swirling ink; every kick pushes it |
| `coral` | living pattern grows out of the picture's edges: mazes in the dark, coral in the light |
| `mosh` | the picture stops renewing and is dragged about by what moves; it snaps back on the bar |
| `sort` | the bright parts of the picture melt into sorted streaks, bar by bar |
| `slit` | different parts of the frame show different moments of the last second |
| `echo` | the frame fed back into itself: spiralling, crawling, turning colour as it ages |
| `ripple` | rings of water spread from the middle on every beat |
| `shatter` | seen through a sheet of crystal cells, each bending the picture its own way |
| `glitch` | blocks and lines of the picture slip sideways on the beat |
| `droste` | the picture inside itself, down a spiral, for ever |
| `mobius` | the picture slid through itself: the middle swells, the far side shrinks to the rim |
| `gyroid` | a flight through an endless curved lattice, skinned with the picture |
| `fractal` | a flight down a carved corridor painted with the picture, which snaps whole as you pass where it is thrown from |
| `paint` | oil paint: flat strokes that keep their edges |
| `relief` | the picture raised from its own light and dark, under a lamp that circles |
| `edges` | the outlines of things glow like neon |
| `halftone` | printed in four inks, as dots |
| `ascii` | the picture as characters: dense ones where it is bright, strokes along its edges |
| `rays` | shafts of light stream out from the bright parts |
| `bloom` | bright things glow into what is around them |
| `streak` | bright things smear sideways, as through a cinema lens |
| `strobe` | a flash on the beat (never more than three a second) |
| `invert` | light and dark change over on the beat, in bands, the colours kept |
| `cycle` | the picture in six bands of colour that step round on the beat |
| `bokeh` | the edges of the screen go out of focus, bright points opening into discs |
| `lens` | the picture bulges and its colours part towards the edges |
| `grain` | film grain and faint scan lines |
| `vhs` | off a worn tape: soft, its colour smeared and late, tearing and rolling |
| `exposure` | -2 to 2 stops: how much light is let through; above 0 the brightest burn to white |
| `sharp` | 1 to 2: everything is drawn at up to twice the size and brought down: finer, and four times the work |

**The ones that remember.** Fluid, coral, mosh, sort, slit scan and echo keep something from frame to frame, and each
takes the picture over: turned up, less and less of the true picture is let back in, until it is only a rumour in
the ink, the pattern or the smear. That way home is the point of them. Mosh gives the whole picture back on a bar
line (every bar; every fourth when turned past half); sort takes a new picture and starts melting it again on
every bar; echo lets it back a little on every beat. Two of these at once fight each other: use one at a time.

**Order.** Those turned up run in this order: what takes the picture over (fluid, coral, mosh, sort, slit), then the
echo, then what bends it (ripple, shatter, droste, moebius, the gyroid, the fractal), then what redraws it (paint,
relief, edges, halftone, glyphs), then the optics (bokeh, rays, bloom, streak); then the light is brought down to the
screen (exposure, the tone curve, lens); then the print (halftone, glyphs), the beat (strobe, invert, cycle) and the
faults of the signal (glitch, VHS). Grain and the dither are in the last pass of all.

**Light.** The screen's frame is worked as light: in 16-bit floats, where light adds as it does in a room and may
pass white. Pictures are stored as the screen shows them and turned into light where they are drawn; the trails,
the particles, blending, the simulations and the optics (bloom, rays, streak, bokeh) all work in light, so a glow is
as bright and as coloured as what makes it. Then, once, at the end: `exposure`, a tone curve, back to the screen's
numbers, and a dither of about one step so slow fades do not band. The tone curve is typed only: `!tonemap 0` (where
it rests) leaves a picture exactly as it was and lets only light past white burn towards white, keeping its hue;
`!tonemap 1` is a film's curve, deeper shadows and highlights rolled off, a look rather than a correction. Seven
effects are built on the screen's numbers rather than on light, and run after the curve: halftone (its inks are
1 minus the colour), glyphs (chosen by brightness from 0 to 1), the strobe, invert and colour cycle (a flash over
what is shown, a turn about mid grey, bands of brightness), glitch and VHS (faults of a finished signal). Each
picture's own chain works on the picture as stored, before it is turned into light: a picture has nothing brighter
than white to work with, every effect was tuned on those numbers, and so all eighteen can run on it in one order;
what it makes is kept in floats and goes into the frame's light with the rest. The particles are drawn adding their
light; at full there are 4,194,304, half as many when frames run slow and a quarter when the screen's heavy effects
are being left out too. The director takes the exposure down on dark words and up on glaring ones.

**The strobe** flashes on the beat and never more than three times a second: above 180 to the minute it takes
every second beat. The story's director is not given it.

**Cost.** Several are heavy on the graphics card on purpose. The fluid runs forty-five small passes a frame; the
fractal walks a ray of up to a hundred and ten steps for every point of the screen, with shadows; the gyroid
ninety-six; coral twelve steps a frame; sort sixteen; paint reads up to two hundred points for each one; and
`sharp 2` quadruples all of it. With a film being made on the same card each slows the other. If the card will not
take an effect it is left out and the side panel says which; if one fails while running, the effects are switched
off for the session and the picture carries on. How each is built, and where it comes from, is in
`docs/research/06_visual_effects.md`.

**The director has them all** (except `sharp`, which is the machine's business, and the strobe, which is yours). With every beat of the story it
says where each effect should stand, so they come and go as the story moves: it may name up to three itself, and
when it does not, the beat is read for what it is about (water brings ripple, glass or ice shatter, a tunnel the
gyroid, neon the edges, the past grain, and so on), further turned the wilder the beat. The side panel says which it
chose. An effect you set on the visuals panel keeps the difference you gave it, as everywhere; one you type is the
director's again after three beats. `!fx hold` makes the effects yours alone, and `!fx auto` gives them back.
It changes them a step at a time: at most one effect comes in and one goes on a beat, and a heavy effect coming in
waits until the heavy one going has gone, so a change of scene does not switch several heavy passes on one beat.

### Effects on each picture

The effects can also be laid on each picture by itself, as well as over the whole screen: every picture (and each
frame of a film) is put through its own chain before it is placed, on the surface, on the sides of an object and in
the swarm, and the screen's effects then run over the finished frame as before. This "image" target has its own
numbers: `!image bloom 0.8 edges 0.4` sets them (`!bloom 0.8` is still the screen's), `!image off` turns them all to
nothing and leaves them there, `!image hold` keeps them yours, `!image auto` gives them back to the director. On the
visuals panel, the switch over the effects turns the dials to "images". As messages to the viewer they are
`{"image": {"bloom": 0.8}}`, or `"image:bloom": 0.8` among the other settings; held, released and followed exactly
as the screen's are.

Eighteen of the effects work on a picture: all but the ones that remember (fluid, coral, mosh, sort, slit, echo:
each would need a simulation of its own for every picture on screen, and what they smear is the moving frame, not a
still), and the ones that belong to the screen (flow, particles, bokeh, lens, grain, the strobe, sharpness). The
director has them too, chosen apart from the screen's (never the same effect on both), at most two, gentler (60% at
most), and not the gyroid or the fractal, which replace a picture with a flight through it. While the director has
them, the pictures differ from each other: each keeps its own share of the effects in play (each with a chance of
two in three, always at least one) at its own strength, on its own clock and beat. Set by hand, every picture gets
exactly what you set.

Cost: the picture being looked at is worked every frame (and the one it is turning from, while it turns); the rest
(swarm, sides) a few a frame in turn, each keeping its last result in between, and at most 24 at once. The work
counts toward the slow-frame measure, and when frames run slow the pictures' heavy effects are left out first,
before the screen's.

**Pauses.** Anything that holds up one frame is seen as a hitch, so the viewer keeps such work out of the frame:
every effect's program is drawn once as it starts (drivers finish building a program the first time it draws);
framebuffers are kept in a pool and handed round rather than made and deleted as effects come and go; the screen's
scratch framebuffers are made with the screen, and the particles' memory once, with the first screen; pictures and film frames are written into the storage their texture
already has; at most one finished picture is sent to the card a frame, and previews already overtaken are not sent;
packing pictures for the shelf, shrinking them for the swarm and drawing the overlay are done aside; Python's
garbage collector is kept quiet; and once heavy effects are left out for slow frames they stay out for a while
(longer each time it happens again soon), instead of blinking on and off. The viewer also keeps a record of frames
much slower than usual and what happened in them (a picture sent to the card, an effect turned on, framebuffers
made, the garbage collector...); at most once a minute, if there were any, the side panel says so in one line.


**Who is in charge.** The session moves everything as the story goes, and both panels follow it. What you set by
hand is never put back:

- A dial (the look, the effects; the sub, the twinkle, the swing) lands where you put it. From then on the director's moves
  are added to where you left it: the session can move away from your setting, but it does not snap it back.
- What cannot move by degrees stays as you chose it: the archetype, the key, the shape, the tint, and the patterns
  once you have mutated or edited one (the director then leaves the style and the riffs alone).
- The knobs, volumes and mutes of the parts are yours alone: the story's director never touches them.
- "release", on either panel, hands everything back to the director. It has to be pressed and held for a moment,
  so that it is not hit by mistake.

## The music

With `--groove` the sound begins as a heartbeat: the kick alone, two thumps close together and then a wait, about
once a second, and nothing else. It stays that way until the scene is set, which is when the first picture arrives
(a picture or a film you drop in, or a memory you go back to, sets it too). The whole rhythm section then comes in
on the next bar line, with nothing added to mark it. From there it plays on. Every part is shown on a small roll at the right of
the viewer, under the name you call it by, lit as it sounds: kick, snare, hats, sub, bass, tune, bells, drones,
clip (a film's sound while it is first shown), and one row for each layer: every film's sound and every sample you
have pulled in, under its own name.

The last row of the roll, "audio", is the dropout watcher. It shows how much of the time available the sound takes
to make ("load 12%"), puts a mark on any sixteenth where the sound was not ready in time, and then counts them
("3 dropped"). The first dropout in any ten seconds is also said in the side panel, with why: a block that took
too long to make (and how many sounds were being rebuilt at the time), or the sound card running dry because
something else had the machine.

**How it plays.** The rhythm section follows the jungle research kept in the thelmic project (measurements of a
reference set, checked against what the press and the forums say). `mindstream/deal.py` holds the numbers.

- **A section holds its identity.** Everything is decided once a section of thirty-two bars and then kept. For the
  drums, three bars are dealt at the start of a section (the spine always plays: the kick on the one, the snares
  on two and four; in the break styles the other eighths sound about two times in three and the odd sixteenths
  about one in three) and an order for the four-bar group is chosen (A A B A, A B A C, A A B C or A B A B), which
  every group in the section then follows. Only the quiet ghost snares are dealt afresh each bar. A new section
  brings new bars. (Chance choosing every hit read as random; this is what producers' variation looks like.)
- **A fill** closes a four-bar group about one time in four, and it is two or three hits, not a build.
- **The sub** is a clean low note with a knock at its front, and in the break styles it plays a written riff that
  develops (see [The bass and its hooks](#the-bass-and-its-hooks) and [The edge and development](#the-edge-and-development)).
- **Nothing pumps.** The sub and the bass do not duck under the kick; they keep out of its way by register (the
  kick rests at 58 Hz, the sub has everything below). Everything else gives way by a decibel or so. A part can
  still be made to duck with its own control.
- **The lead** (the part called "tune" on the panel) carries the hook, and its sound is the point of it, not its
  notes (docs/research/07_good_edm.md).
  - **Who plays it.** Once there is film sound, the films' own sound, cut into tuned stabs: the note each piece of
    film sound really sounds is found, and it is moved from there, so the hook is in tune. In turn with it, a section
    each, the scene's one signature synth; before there is any film sound, the synth alone. A scene's synth is one of
    four, chosen when the scene changes: **acid** (a sawtooth through a resonant filter whose envelope, accents and
    slides are the line; it plays a sixteen-step line of its own, held for the section), **reese** (two sawtooths
    fifteen cents apart, beating, under a filter that breathes with the bar, an octave lower), **hoover** (a wide
    stack whose pitch swoops into each note from above) or **dub** (a minor-seventh chord stab whose echoes, each
    darker than the last, do the work).
  - **How it moves.** On two clocks. Inside each note a filter snaps open and closes, accents open it further, the
    acid slides from note to note. Across the phrase the filter's resting place rises and falls over sixteen bars.
    So a repeated note is never the same sound twice, and a held line still goes somewhere.
  - **How the hook is developed.** It is drawn once a section and held. The section's four blocks of eight bars take
    it through stages, as a sample is developed: teased (once, its first notes only, dark and quiet), stated (whole),
    chopped (stated, answered four bars later with its last note brought home, its relatives in other bars, and a
    stutter into the next block), and then answered once more, or, every other section, taken out for eight bars.
    Its relatives are made from it (a fragment, the same notes an eighth later, its contour inverted, a step lower),
    never drawn afresh. "Busier" and "sparser" on the tune change how many bars have the hook; muting the tune
    silences the lead.
  - **Choosing it.** `!lead acid` (or `reese`, `hoover`, `dub`) puts the hook on that synth alone and keeps it there;
    `!lead film` on the film's own sound alone; `!lead auto` back to the two in turn. The same choice is on the knob
    panel, beside the archetype. A memory keeps it.
- **A break is subtraction.** The low end goes and the drums keep running, a little busier. There is no riser and
  no crash; about one in four ends in a four-hit roll, and about one in four leaves a single sixteenth empty.
- **The bells rest** unless you ask for them, and are an octave lower than they were.
- **Jungle** is a style word (`!style jungle`): the measured spine, kick on the one and the "and" of three.

A drum pattern you edit or mutate is from then on played exactly as you wrote it, every bar; a hook or a sub riff
you mutate is held instead of turning over. "As written" gives a part back to the dealing.

**The super knob follows the story.** With each beat the session asks the super knob toward a place that suits it:
nothing for a calm beat, up to half way for the wildest. The knob does not leap there. It creeps, a small step every
fourth bar, and only jumps when the scene changes: when a change of structure lands, or a new theme begins. A knob
you set by hand keeps the difference you gave it, as everywhere else. `!super hold` makes the super knob yours
alone; `!super auto` gives it back to the session.

**Structure.** The style, the key, new riffs and a break are what the music is built on, and the session treats
them differently from everything else it moves. A change of structure it asks for is not made at once: it lands on
the next four-bar line, and once the structure has changed (by the session or by you) the session leaves it alone
for eight bars, or as many as `!structure 16` says (4 to 64, in fours). When it holds one back, the side panel says
so. What you change by hand is made at once. Everything that moves by degrees (the look, sub, twinkle, swing)
still follows the story beat by beat.

### What the parts play

The drums, sub and bass play one of sixteen patterns: six plain styles and the ten rhythmic archetypes from
[thelmic](https://github.com/sens8tion/thelmic)'s rules (`amen`, `rolling`, `stutter`, `two_step`, `gabber` ...),
named in a steer or with `!style amen`. A pattern is yours to play with live:

- "busier kick", "sparser hats", "double the hats", "vary the snare", "snare fill", "kick as written";
- "sub on the off-beats", "snare on the three", or exactly, `!kick 1 5 9 13` (sixteenths of the bar, from 1).

Adding `--thelmic` to the viewer's options hands the writing to thelmic's engine instead, sixteen bars at a time;
those parts cannot be edited step by step.

### How the parts sound

Change how a part SOUNDS, not what it plays, by naming it: "make the bass dirtier", "more room on the tune",
"brighter hats", "mute the bells", "tune up an octave", "longer kick", "reset the bass" (or `!bass dirty`). Words:
louder, quieter, mute, back; dirty, clean; wet, dry; bright, dark; higher, lower; long, short; reset.

Anything beyond those words goes to llama, which answers with settings (level, drive, room, tone, length, punch,
attack, octave, pitch), effects (delay, chorus, crush, tremolo, filter, sweep, reverse) and extra layers for
whichever parts it thinks you meant; the side panel says how it read you.

Once a film has been made, the tune and the drones are played on pieces of the films' own sound; the synthesised
tones are only for before that.

### Knobs

Every part has a knob: the eight parts of the rhythm section, and every layer. A knob pushes its part into damage,
from untouched at nothing to wrecked at full, at the loudness it had before; below 90 Hz the sound is left alone.
`mindstream ... --knobs` (or `Ctrl+K` in the viewer, at any time) opens the knob panel. From the top it has a strip
for each part, then the **super knob** with the memories and the crossfader, then the tempo and the archetype, and at
the bottom a drawer with the chosen part's character or the box for pulling a sound; the timeline is on the right.
The window has one size (about 1120 by 720): nothing that arrives changes it. Beside the eight parts there is a
place for every layer there can be (ten: six samples and four films' sounds), small, five across in two rows, so
none is ever out of sight; a layer that leaves the session gives up its place. A layer's strip has its name, knob
and volume, and two half-width buttons: MUTE (WAIT while the layer is not in yet) and SHUF, which shuffles its
slices; Shift or Ctrl with it, or its right-button list, rechop the layer or make it whole. The line
at the foot of the panel says what the control under the pointer does, with its keys and gestures, and reports
what has just happened.

- **The knobs are dials.** Drag one up and down from anywhere on its face (hold Shift for a quarter of the speed),
  turn it a step at a time with the wheel, or double click it to put it back at nothing. The number in its middle
  is where it stands. The same dial is used for the super knob and for a part's character.

- **Pull a sound**, in the drawer ("pull a sound" opens it): a box for words ("rain on a tin roof", "amen break",
  "a punchy kick"), a menu for where to look (anywhere, splice, bbc, internet archive, nasa, freesound) and an
  optional name. What it is looking for is said in the line at the foot of the panel. It is the same as typing
  `!pull ...`: the sound is fetched into memory and waits as a layer, with its own knob, or takes a drum's place
  if the words name one. A search of an archive sends the words to that service.
- **Tempo and archetype** sit under the super knob. The tempo is a number (60 to 300): drag it up and down, turn
  the wheel over it, or press "-" and "+". It is set and held when you let go ("held" shows beside it); "free" lets
  the session move it again. The archetype menu chooses the pattern the drums, sub and bass play (six plain styles
  and the ten archetypes), and "next" steps through them. Both follow the session when it moves them. **Hold**,
  8 or 16, is how many bars the session leaves the style, key and riffs alone once they have changed (typed:
  `!structure 16`). **Lead** chooses what plays the hook (`!lead`), and **chop** how the sample layers are chopped
  (`!chop`, see The chop engine). "release", at the far right behind a divider, has to be pressed and held.
- The super knob, the large dial, moves every other knob by as much as it moves itself. A knob that reaches full
  or nothing stops there, but shows a tick where you set it and comes back when the super knob does. Beside it,
  "session" lets the super knob follow the story (the panel starts so) and "mine" keeps it where you put it.
- A knob's **character** is which kinds of damage it turns toward (`mindstream/mangle.py` has fourteen: tape, tube,
  clip, fuzz, fold, crease, rectify, half, sputter, crush, decimate, harmonic, ring, shift), whether a filter sweeps
  before it, whether the louder moments are driven harder, and what the result rings in. Every knob starts in the
  middle of its pad: an even mix of the pad's four corners (clip, fold, crush, shift).
- Under each knob, **mute** silences the part and brings it back (its knob stays where it is; the button reads
  MUTED while the part is silent, and WAITS on a layer that is not in yet), and **mutate**
  gives the part a new pattern to play: a drum's loose hits move while its anchors stay, the bass takes new steps
  and a new movement of roots, the tune a new riff, the bells new notes, a layer a new phrase from further into its
  sound. Typed, it is "mutate the bass". The faster you press it, the more hits the new pattern is given: one more
  when presses are under a second apart, two under half a second, three under a quarter (the tune and the bells
  are played more often; a layer is chopped more busily). **"fewer"**, under mutate (or Shift with mutate), gives a
  softer pattern instead: a new pattern with a hit fewer each press, and fewer still the faster it is pressed. A
  drum's anchors always stay. **"as written"** (or Ctrl with mutate) puts the part back as its style writes it.
- **On a layer** (a sample, a film's sound) the three buttons work on its slices and are named for it. "shuffle"
  repositions them: the same slices, in other places in the bar. "rechop" (or Shift with shuffle) cuts the sound up
  another way, stepping through its obvious transients, less obvious ones too, eighths, sixteenths and beats.
  "whole" (or Ctrl) restores it to one whole sound, played from its start on the one, as often as its length
  allows. Typed: "mutate the rain", "rechop the rain", "unchop the
  rain". A mutated layer keeps the arrangement you gave it: it is no longer planned afresh every four bars, and it
  does not thin or thicken as the session's energy moves, until you mutate it again or put it back "as written".
  Any of the three on a layer that is waiting brings it in on the next bar. A memory keeps the mutation.
- The green bar under each knob is the part's **volume**: click where you want it, or drag. It starts at 100, at
  the tick, and goes to 150; a double click puts it back at 100. Typed: `!vol bass 80`.
- **Ducking.** Each part can give way to another every time that other sounds. Left as it comes, the bass, the
  tune, the drones and the layers give way to the kick, the sub does so a little and briefly, and the drums to
  nothing ("auto"). On a part's own controls, "Ducks under" chooses what it gives way to (any part of the rhythm
  section, or nothing) and "Duck" how far. Typed: "duck the bass under the snare", "duck the rain to the hats 90", "no
  ducking on the tune". A layer can give way to a part, but nothing can yet give way to a layer. Volume, ducking
  and mute are heard at once; they make no sound again.
- **Press a part's name** and its strip is outlined, and the drawer at the bottom (open as the panel starts;
  "character" opens it, and shuts it if it is open) is that part's own controls, the same as in the knob device: a
  pad whose four corners each hold a kind of damage (choose them from the menus beside it, or "dice") and whose dot
  is the blend between them; dials for Movement, Follow and Body, with a menu for what it rings in; and a filter
  after it all (off, low, high or band), with Cutoff and Reso. The part's knob is the drive. Unlike the knob
  device, a change here is heard a note or two later, because that part's sounds are made again.
- By typing: `!knob bass 60`, "bass knob 60", `!knobs 30` (all of them), `!super 40`, `!patch bass fold crush`,
  `!patch bass mutate`, `!patch bass another`.

**Memorise.** The "memorise" button on the panel keeps everything as it stands under the next number. One of the
eight slots beside it then wears a small picture of the middle of the screen as it was; press it to go back. The
memory being heard is marked "live", and "changed" once you move anything by hand. Memorising over a memory cannot
be undone, so it takes two gestures: right click the slot and choose "memorise over this" (or Shift and click it),
then press the slot again within a few seconds. Typed: `!memorise 2`, `!recall 2`. What is kept:

- the music: what every part plays, how every part sounds (its knob, its character, its effects, its volume and
  ducking, whether it is muted), the style, key and riffs, the super knob, and every layer with its sound, whether
  it is in, when and where it plays and how it is cut;
- the screen: the pictures showing, the swarm of earlier ones, the film reel, the caption and the look;
- the story: the guide, the last few beats and the people in it. Going back puts the story where it was, and the
  next beat carries on from there. Its beats get new numbers, and a film needs two new pictures before it can be
  made again.

The tempo is kept too: a memory comes back at the tempo it had, at once, and stays there (the story's director
does not move it) until you set a tempo by hand or press "release". There are eight memories, held in memory only, so they go when the session ends.

**The crossfader**, under the memories, stands between two of them: choose a memory for each end (they are marked
A and B on their slots) and slide, or click where you want it. Every
knob, volume and level moves between the two as you go. On screen, the picture is a mix of the two memories' pictures in the same proportion, and the look
and the tint move between theirs. What cannot be mixed (what the parts play, the style and key, the characters of
the knobs, which layers are in; on screen the caption, the swarm, the reel and the shape) is the first memory's on
its half and the second's on the other, changing over in the middle. In sound it is one engine moving between two
states, not two tracks playing at once.

**The timeline** is on the right of the panel. Drag a memory's slot onto it (or right click the slot) to add that
memory to the end. Each
row is a memory, how many bars it is held for (4, 8 or 16: press one), and how it is left for the next (press
it for the list); the "x" at its end takes the row away. Twelve rows at most; nine show, and the wheel brings the
others round.

- **smooth**: its knobs, volumes and levels move toward the next memory's a bar at a time, and what the parts
  play changes over on the bar line;
- **drop**: the low end goes for the last bar while the drums run on, and the next memory lands on the one;
- **breakdown**: the same for the second half of its bars.

"play" starts the first on the next bar line (the button stays amber until that memory arrives), "loop" sends it
round again, "stop" leaves the music where it is. The row playing is lit as a whole and the knobs show that memory. The timeline moves the music and the screen; it leaves the
story alone, so the story is not restarted at every step.

To find a character by ear, use the knob device, which is separate from a session:

    .venv-dml\Scripts\python.exe demo\knobs.py

It loops a sample from your library under a pad that blends four kinds of damage, with drive, movement, follow,
body and a filter. "That's it" marks a setting and "Copy marks" copies it; typing `!patch bass` followed by a
pasted mark in a session gives the bass that character, with its knob where the drive stood.

Where each knob stands is shown beside its part on the roll ("knob 60"). The panel follows knobs moved by typing,
by a memory or by the timeline; a knob your hand is on is not moved under it.

### Feel

[FEEL.md](FEEL.md) is the canon of feel: nine kinds of engagement with heavy music (weight, violence, grit, menace,
lock, release, filth, swagger, derangement), each with an inverse, a ladder of words and what it asks of the
engine. It is the vocabulary for a control pad. It is defined and read (`mindstream/feel.py`), but not yet wired
to the sound or shown on screen.

### Chopping

Every film's sound, and every sample, is played chopped. It is cut at its **obvious transients**: where the level
at least doubles in an instant and what arrives is at least a quarter as loud as the loudest thing in it (a hit,
a word). Washes, swells and ghost notes are not cut at. A sound with no obvious transients is cut on the eighths
instead, and says so when it arrives.

The slices are then played to a four-bar phrase planned against the drums as they stand:

- bar 1 states a run of slices in their own order, starting on the one, the rest in the gaps the kick leaves;
- bar 2 says it again with the hardest-hitting slice on the snare;
- bar 3 is bar 1 again;
- bar 4 turns round: half of bar 1, then a stutter that quickens into the next phrase (left empty when things
  are sparse).

Each new phrase starts further into the sound.

To cut another way, say so, of any layer by name:

    chop the rain on the eighths     or sixteenths, beats, bars
    cut the dust into 8              equal pieces, 2 to 32
    chop the clip finer              less obvious transients too (or the next smaller grid); "coarser" the other way.
                                     "clip" is the newest film's sound; the films after it are cut the same way
    chop the rain on its transients  back to the default

### The chop engine

The four-bar phrase above is being replaced by a chop engine (`mindstream/chopper.py`; the design is in
`docs/research/README.md`). In plain words:

- **Every layer has a role**, worked out from its slices: the **anchor** (it speaks on the main beats), the
  **carrier** (it fills quietly between them), **colour**, a **hook**, a **stab** or a **bed** under everything.
  There is one anchor and one carrier at a time; the other layers take the nearest free role.
- **It cuts in blocks.** A block is one or three eighths of the sound (five, rarely), played once or twice, and each
  new block reads the sound from where the bar has got to, so a hit lands on the step it came from.
- **A spine.** The heaviest slice falls on the one in three bars of four, the sharpest on the snare's places; ghosts
  stay with the hit they lead into, and each slice keeps its own loudness.
- **Lanes are kept apart.** A layer keeps off the cells the kick, the sub and the snare own, and two layers never
  take the same sixteenth.
- **Tricks are rationed.** In each four bars at most one roll, one reversed slice and one emptied downbeat, and at
  least one plain bar.
- **Held per section.** The four bars' shape is kept for a section and dealt afresh inside it, so the group comes
  back while no bar repeats exactly.

It plays in one of six styles (jungle unless you choose):

    jungle         eighth-note blocks, the source's order mostly kept, a stutter at a phrase end one time in five
    atmospheric    light, close to the source, fills only at eight- and sixteen-bar marks
    drumfunk       cut hit by hit and rebuilt like a drummer playing it, fills and kickbacks, reset every 8 or 16 bars
    techstep       a fixed two-step skeleton under it, the break as texture, rolls only to build into a section
    breakcore      tiny cuts, no loop that holds, ratchets and pitch runs, changing all the time
    footwork       skipping kicks, sparse and dense by turns, half-time and full-time bars traded

Choosing:

    !chop drumfunk       the style, for every layer (or jungle, atmospheric, techstep, breakcore, footwork)
    !role rain hook      the rain plays the hook (anchor, carrier, colour, hook, stab or bed), and keeps it
    !role rain auto      the rain's role is the engine's choice again

The same are on the knob panel: "chop" at the end of the tempo row, and "Role" in a layer's own controls (press
the layer's name; on auto it shows the role the engine gave). Both follow the session.

### The bass and its hooks

Built: `mindstream/bassline.py` (a stored riff: two anchors, decorations dealt from its own odds, an eight-bar phrase
of statement, answer a step lower two times in three, the high point, a thinned closed bar, fragments and a
turnaround; three home pitches and one colour note that always resolves; slides on small moves; nothing on the
sixteenth after a snare; lock/answer/free against the kick per scene; the saw bass answering in the sub's rests or
resting) and `mindstream/motif.py` (a hook from the bass's pitch set with one leap of a fourth, fifth or minor sixth,
stated in bar 4, its leap in bar 5, answered in bar 8, replaced by a relative, placed in the low end's gaps). Check:
`python -B demo/bass_check.py`.

### The edge and development

`!edge lock 0.7` (0 locked … 1 restless) and `!edge derange 0.3` (0 composed … 1 deranged) turn two dials that reach
across the engine: how much of the drums' deal and the chop's comes back, how long riffs and skeletons are held, how
busy the carrier is, how short the cuts are, how many rolls, stutters and reversals, how much damage on the layers.
0.5 on both is the engine as it is. `!edge lip lock 0.6` sets where a dial's lip sits, by ear. Past the lip the
program rations the dial: one dial at a time, on one lane (the drums or the chopped layers, never the low end), for a
bar or two at the end of a four-bar group, and more after a long hold. `!edge auto` gives the dials back to the
session (the session's own values when it sends them, otherwise they wander inside the lips and now and then lean
past one). `!roller 16` is how many bars a riff is held before it changes, from 32 (a roller) down to 2 (a
switch-up). The knob panel has both on its EDGE row; right-click a dial to put its lip there. A memory keeps the
dials, whose they are, the lips and the roller.

Development (`mindstream/develop.py`) gives every lane its own clock: one riff change per eight bars, the B riff at
32 (the kick and the hats' carrier change with it), the low end out for a bar or two and then A back changed at 64,
B back changed at 96, a new A at 128; the hook following a four-bar line later and replaced by relatives in between;
and each sample layer with four slow clocks of its own (what of its sound it reads, its role, its odds, its
processing), one layer changing at a time. The side panel says so when the riff turns over or a layer takes another
role ("The bass: the B riff comes in, and the kick changes with it."). `mindstream/course.py` works all of this out
a few bars ahead, aside from the sound. `python -B demo/develop_check.py` checks it.

The hand beats development. A riff or hook you made or mutated, a drum part you wrote, a layer you mutated (held),
placed, gave a role or a density, stays as you left it until you let it go ("as written", "reset", a new score or
style); the clocks run on underneath, and what they say is heard again from then.

### The music measures itself

`mindstream/watch.py`. The mixer hands each finished bar (the band from groove.heard, the layers' slices as they
started) to a Watch on a thread of its own; the sound's thread only appends. Every bar it judges the last 32 per lane
and overall (healthy, looping, or drifting into noise) and says one line when the verdict changes.
`stands()["watch"]` carries the compact report, and the knob panel shows it as HEALTH on its EDGE row: the verdict
in green, amber or red, the layers' lag 4, how many checks fail and a letter for each lane in its colour; the pointer
on it says why. `python -B demo/watch_check.py` checks it.

## Films

`--video` says when films are made: `ask` (only when you ask), `interlude` (between pictures), `reel`, `off`.
`!film`, or "film this", makes one now between the latest two pictures: 1.5 seconds unless you say (`!film 3`,
`!film 4 beats`), 3 seconds at most.

A film is shown once, straight through, with its own sound, starting on the next bar line. Then its sound is a
layer like any sample (see Layers): cut up, named, and waiting until you bring it in. A story film is called
`film` and the number of the picture it arrives at (`film7`); a clip you asked for is called by the first telling
word of what you asked ("a bossa nova dance" is `bossa`). "clip" always means the newest film, and `Ctrl+C` brings
it in or takes it out. While the newest film's layer plays, the picture jumps to each slice as it sounds. Four
films' sounds are kept; a fifth pushes out the oldest, and a new theme lets them all go.

A clip made to be chopped, on demand: "make me a bossa nova dance for the soundtrack to chop, with words too", or
`!sample ...`. It is one bar long at the tempo playing, made from your words alone (the dance, the music, a few
words). Bring it in and it is chopped over the rhythm section; the tune plays on its sound from the moment it
arrives. Say "the words should be ..." or "invent some words" for the same clip with other words; `!styles` lists
the musical options, though any style can be described.

## Samples

"pull a vinyl crackle loop from splice", "grab a kick", "find some rain on a tin roof from the bbc", or
`!pull ...`. Your local Splice library is looked in first, by file name; then the free archives (the BBC sound
effects archive, the Internet Archive, NASA, and Freesound when its key is in the environment). What is found is
fetched into memory, never onto disk.

- A kick, snare or hat takes that drum's place.
- Something tonal (a vocal, a chord, a pad) becomes what the tune is played on.
- Anything else becomes a **layer** of its own.

### Layers

A new layer arrives cut up and named, and **waits**: it does not play until you bring it in.

- **Its name** is the first telling word of what you asked for ("rain on a tin roof" is `rain`), or one you give
  ("pull a vinyl crackle loop from splice as dust"). "sample" means the newest pulled sample; films' sounds are
  named as described under Films.
- **How many**: up to six pulled samples and four films' sounds, each with its own row on the roll. One more
  pushes out the oldest of its kind, and pulling under a name already in use replaces that layer.

You say when each one plays:

    bring in the rain                it enters on the next bar line (also: rain in, play the dust)
    take out the rain                it stops and waits, still loaded (also: dust out)
    rain only in the breaks          which bars: also "dust every fourth bar", "rain every other bar", "rain all the time"
    dust on the off-beats            where in the bar: also "rain on the one", or exactly, !dust 1 4 7 11
    busier rain                      how busy, when it is left to chop itself: also "sparser dust", "vary the rain"
    reset the rain                   back to how it arrived
    drop the rain                    gone

Saying which bars or where in the bar brings a waiting layer in too.

A layer is a part like any other, so everything under "How the parts sound" applies to it by name: "make the rain
darker", "more room on the dust", "mute the dust", and through llama, "stick a delay on the rain".

### What leaves this machine

A search of an archive sends its words to that service, which logs them. What you type for a pull is sent as you
typed it. A search of your own Splice folders sends nothing.

The story may also ask for a sound, one beat in three. It is written by a language model and may ask for
anything, so its request is sorted first:

- if every word is a plain sound word from a fixed list ("heavy rain", "busy market"), it is asked for, and waits
  as a layer like any other;
- if not, nothing is sent. The sound is made here instead as a clip to chop, or, when films are made only on
  request, you are told and can ask for it.

`--feed-args "--no-story-sounds"` stops the story asking at all. The BBC's licence is for personal use only; each
sample's licence is shown as it arrives.

## Setting up

- **Models.** The code names none. Copy `models.example.json` to `models.local.json` (never tracked) and say
  which files and tags this machine uses. No weights belong in this repository.
- **Environments.** The picture generator runs in an existing Forge environment and the film generator in an
  existing ComfyUI environment, both chosen in `models.local.json` (below); `MINDSTREAM_PYTHON`,
  `MINDSTREAM_COMFY_PYTHON` and `MINDSTREAM_GL_PYTHON` override them for one run. The viewer, sound, steer reader
  and encoder helper share `.venv-dml`, whose packages are listed in `requirements-dml.txt`.
- **Remote host.** An SSH host alias (default `llama`, or `--feed-args "--host <alias>"`) running Ollama on its
  loopback address. Two things are cleared there when a session ends, and again when the next one starts in case
  the last was killed: Ollama is restarted, so the story does not stay in its memory, and the system log is
  emptied, so there is no record of when the host was used. For that the host needs:
  - the system log kept in RAM (`Storage=volatile` in journald) and Ollama's own output sent nowhere
    (`StandardOutput=null`, `StandardError=null` in its service override);
  - a root-owned command `/usr/local/sbin/mindstream-clear` taking `all` (restart Ollama, then
    `journalctl --rotate` and `--vacuum-time=1s`) or `log` (the log only), and a sudoers rule letting the login
    user run exactly those two forms without a password. Without it the feed falls back to restarting Ollama.
- **Samples.** The local library is looked for in `~/Documents/Splice/Samples` and `~/Splice`, or wherever
  `MINDSTREAM_SPLICE` points. The archives are reached through thelmic's source adapters, expected in a `thelmic`
  folder beside this one (or at `MINDSTREAM_THELMIC`). Freesound is used only when `FREESOUND_API_KEY` is in the
  environment the session was started in.
- **Launchers.** `launchers/*.cmd` are the commands: put that folder on the PATH. They find the scripts beside
  themselves, and the environments from `models.local.json` (or the variables above).
- **Guides.** The story feed reads its instructions from `prompts/`, and prefers your own guides for picture and
  film prompts when they exist (`picture_guide` and `film_guide`, below).

### Setting up on your own machine

Copy `models.example.json` to `models.local.json` beside it and fill in what applies; leave the rest empty. Any key
can also be given for one run as an environment variable, `MINDSTREAM_<KEY>` in capitals. A missing choice stops
the program that needs it with a message naming the key, not a traceback.

    story_model, steer_model, steer_suffix   the Ollama tag of the story model on the remote host; the small local
                                             model file that reads steers, and any text added to its prompts
    forge_dir, forge_python                  the Forge install whose model folders hold the picture model's files,
                                             and its Python (default: the venv inside forge_dir)
    image_model, image_vae, image_te         the picture model, its autoencoder and its text encoder: bare file
                                             names are looked for in Forge's model folders
    image_config_dir                         the folder of the picture model's config and tokenizer files (no
                                             weights); a relative path is inside forge_dir
    image_pipeline, image_transformer_class  the diffusers classes for the picture model, written "module:Name"
    image_checkpoint_converter               the diffusers function that turns its single-file checkpoint into
                                             diffusers' layout, "module:name"
    image_te_config_class, image_te_model_class   the transformers classes for the text encoder, "module:Name"
    comfy_dir, comfy_python                  the ComfyUI install the film model runs in, and its Python (default:
                                             the venv inside comfy_dir)
    video_model, video_lora, video_te,       the film model's files, by name in ComfyUI's model folders (video_lora
    video_vae, video_audio_vae               may be empty)
    video_nodes_module, video_node_class     the ComfyUI module and node class that turn a prompt and pictures into
                                             the film model's input ("package.module" and "ClassName")
    video_clip_type                          the type ComfyUI's text-encoder loader is given for the film model
    picture_guide, film_guide                your own guides for writing picture and film prompts (defaults
                                             ~/guides/picture.md and ~/guides/film.md; prompts/ is used without them)

## Prompts written by llama, or put together in code

By default llama writes every picture prompt and every film prompt out in full, from the guides. That is most of
what it writes, and it writes slowly. The other way is switched on through the story feed:

    mindstream --feed-args "--prompts structured"
    mindstream --feed-args "--prompts inline"

- `structured`: for each beat llama fills in a short card (`prompts/card.md`: who is there, what they do, the
  place, the light, the mood) and, for a film, four more lines (`prompts/film_card.md`: how the camera travels,
  who is heard, their words, the sounds). `mindstream/prompts.py` writes the prompts round those slots: the
  order of the picture prompt, its framing and medium, the film format, the speaker reference, and the music
  line, which is taken from the score the rhythm section is playing.
- The people of the story are described once, on a `new:` line of the card, and kept in memory as the cast.
  From then on code writes the same look into every picture they are in and the same voice into every film they
  speak in.
- `inline`: the same, with the card asked for in the same reply as the beat, which saves a call. If a reply
  carries no card, it is asked for separately.
- What llama writes goes in word for word. Whatever it leaves out or gets wrong is filled in by code (the viewer
  is told what), and it is never asked twice. The picture and film guides are not sent in these modes.

### While llama is away

llama may not be there yet, may be busy with another session, may stop answering, or may simply be in the middle
of a long reply. Whatever the `--prompts` mode, the same code then makes everything in a plainer way, from what
is on this machine:

- The guide is painted at once as picture 0, from a whole prompt: the guide's words, then a framing and a medium.
- Until llama answers, anything typed about the story *is* the story: it becomes the next beat, in your words,
  with a caption and a picture of its own. When llama arrives it is shown those beats and carries on from the
  next number.
- `!film` (or "film this") makes a film at once between the latest two pictures: what the two beats say, whoever
  of the cast is there, a simple camera move, the sounds of the place, and the music line from the score. Nobody
  speaks in it, unless the last thing typed about the story is short enough to be said in the time, in which case
  a voice off screen says it. This is also what `!film` does while llama is busy writing something else.
- While llama is connected but busy, something typed about the story repaints the present scene with your words
  leading the prompt, and llama takes it into its next beat, as before.

The viewer is told each time something was made without llama. What is not possible without it: new story text
that you did not type, descriptions of people (the cast is only added to by llama), and the director's scoring
of a beat (the music and motion still answer to what you type).

`python -B demo/try_prompts.py --show` runs the feed against canned replies, with no model, and prints an
assembled picture prompt and film prompt. It also plays out llama being absent, busy and failing.

## Other tools

    film-audition       film one fixed scene with different music descriptions and hear each one
    steer_intent.py try "slower, gently"      see how the small model reads a steer
    sample_pull.py try "amen break" --role loop --where splice      find a sample and describe it (plays nothing)
    vid-gen --check     check the film generator's environment without loading a model
    te-export <file>    convert a text encoder for the integrated GPU

## Licence

Copyright (c) 2026 sens8tion. You may use, change and share this for any non-commercial purpose, under the
[PolyForm Noncommercial License 1.0.0](LICENSE). Keep the copyright notice with any copy you pass on. For
commercial use, apply to sens8tion for a licence.

One file is different. `vid_gen.py` loads ComfyUI as a library, and ComfyUI is under the GNU General Public License;
so `vid_gen.py` is under the [GPL, version 3 or later](LICENSES/GPL-3.0.txt), and the small file it uses,
`mindstream/local.py`, may be used under either licence. It runs as a program of its own and speaks to the rest
only in lines of JSON over a pipe.

No models, weights or model choices are part of this repository, and nothing here gives any right to them: each
has its own licence, as do ComfyUI, the picture generator's libraries and the other packages this needs. The
[Warning](#warning) at the top applies whatever the licence.
