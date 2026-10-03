# Design review: the knob panel and the visuals panel

A review of `knob_panel.py` and `visual_panel.py` for looks and for live use, with a redesign that stays
inside tkinter. Nothing in the panels was changed. The review was done from the code and from measurements of
the panels built in a withdrawn (never shown) window; nothing was rendered, so a few points are marked
"not seen" and listed at the end.

## 1. Verdict

The panels look like a Windows settings dialog laid over the show, and the thing that does most of the damage is
the mix of stock widgets: forty to seventy light grey system buttons and menus (`#f0f0f0`, black text) sit on a
near-black panel, so the brightest things on screen are labels such as "mute" and "next", while the things that
matter (where each knob stands, what is muted, which memory is live) are drawn dark on dark or not drawn at all.
For playing, the stock `Scale` is the wrong control: the only part of it that can be grabbed is a 30 px thumb (8 x 16 px
on the volume faders), a click anywhere else in the trough moves it by one step instead of going there, and its
thumb is painted in the panel's own background colour. The layout also puts sound design in the middle and the
performance controls (super knob, memories, crossfader) at the very bottom of a 900 px tall window.

The one change that would help most: replace the stock `Scale` with one Canvas-drawn control (a dial, and its
straight sibling a fader) used everywhere on both panels, and restyle every remaining stock button and menu to one
dark, flat look. That single step fixes the look, the target sizes, the state display and the consistency between
the two panels, and it removes the `grabbed` workaround in the code.

## 2. Measurements

Measured with the window withdrawn, on this machine: 96 dpi, Tk scaling 1.333 px per pt, screen 3440 x 1440,
Tk 8.6, default font Segoe UI 9 pt. Sizes are the widgets' requested sizes in pixels, width x height.

### Knob panel

| State | Window |
|---|---|
| As it opens (8 parts, no memories, empty timeline) | 992 x 857 |
| 8 memories with pictures, 6 timeline rows | 1014 x 903 |
| The same with 4 layers | 1109 x 903 |
| The same with 10 layers (the most allowed) | 1499 x 903 |

At 1014 x 903 it covers 29% of the width and 63% of the height of this screen; on a 1920 x 1080 screen that would
be 53% and 84%, and with 10 layers 78% of the width. The window grows by 65 px for every layer that arrives, and
by 46 px in height when the first memory gets its picture.

| Control | Size | Type |
|---|---|---|
| One strip | 59 x 274, at a 65 px pitch | |
| Knob (vertical `Scale`) | 44 x 202; trough 18 wide, thumb 18 x 30 | value 9 pt |
| Volume fader | 12 x 202; trough 8 wide, thumb 8 x 16 | no value |
| Part name button | 59 x 23 | 8 pt bold |
| "mute", "mutate" | 45 x 21 each, 2 px apart | 7 pt (12 px line) |
| Part sheet, whole | 588 x 283 | |
| Pad | 192 x 192, dot 16 | |
| Corner, body, filter, ducking menus | 60 to 104 x 31 | 9 pt |
| "dice" | 30 x 23 | 8 pt |
| Sheet sliders (six) | 302 x 19, thumb 30 x 15 | label 9 pt, no value |
| Tempo slider | 322 x 38 (240 tempos over about 290 px of travel) | |
| "free", "next", "give back" | 29 x 23, 31 x 23, 57 x 23 | 8 pt |
| Pull row | 593 x 31; boxes 208 and 58 wide, "pull" 52 x 26 | 9 pt |
| Super knob | 622 x 38, thumb 30 x 15 | |
| "memorise" | 67 x 26 | 9 pt bold |
| Memory button | 31 x 26 before its picture, 72 x 72 with it | 9 pt bold, then 14 pt bold |
| Crossfader | 382 x 19, thumb 30 x 15; end menus 51 x 31 | |
| Timeline column | 264 to 285 wide, as tall as the window | |
| Timeline row | 265 x 38; tag 38 x 38; menus 51 and 86 x 31 | |
| Timeline "x" (remove) | 12 x 21 | 7 pt |
| "play", "stop", "loop" | 52 x 26, 52 x 26, 52 x 25 | 9 pt |

### Visuals panel

| State | Window |
|---|---|
| As it opens, empty | 856 x 631 |
| 30 things on the shelf; 1 picture, 1 film, 2 sounds and 8 swarm pictures in play | 927 x 643 |
| 14 sounds and 14 swarm pictures in play (the most the box shows) | 1539 x 643 |

The "in play now" box sets the window's width: it is 524 wide in the middle case and 1136 in the last.

| Control | Size | Type |
|---|---|---|
| LOOK column | 339 x 467 | |
| Look slider row | label 97 wide + slider 242 x 38, at a 38 px pitch; thumb 30 x 15 | 9 pt |
| Shape buttons | 52 x 26 | 9 pt |
| Tint swatches | 24 x 26 ("none" 38 x 26) | |
| "hold flat", "flash", "release" | 73 x 26, 59 x 26, 66 x 26, 6 px apart | 9 pt |
| Shelf column | 544 x 619 | |
| Word boxes | 280 x 25 and 208 x 25 | 9 pt |
| "picture now", "film now" | 87 x 26; length menu 71 x 31 | 9 pt |
| "In play now" box | 524 x 119 (middle case) | title 9 pt bold, group names 7 pt |
| In-play thumbnails | 64 x 64 (showing, film), 32 x 32 (sounds, swarm) | |
| Shelf thumbnails | 68 x 68 with edge, 72 px pitch, 6 across; 5.3 rows visible (380 px) | |
| Scrollbar | 17 wide, system colours | |

### Type and colour in use

Five sizes for button text (7, 8, 9, 9 bold, 14 bold), two for headings (10 bold, 9 bold), 9 for labels.
7 pt Segoe UI has a 12 px line; its lower-case letters are about 5 px tall.

Computed contrast (WCAG ratio), not observed:

| Pair | Ratio |
|---|---|
| Label text `#ddd` on panel `#15151a` | 13.4 : 1 |
| The same at 80% over a white picture | 7.6 : 1 |
| Hint text `#888` on panel | 5.1 : 1 |
| The same at 80% over a white picture | 3.7 : 1 |
| Slider trough `#2a2a33` on panel `#15151a` | 1.3 : 1 |
| Stock button face `#f0f0f0` against the panel | about 100 times its luminance |

At 80% opacity, 20% of the picture comes through everything, text and controls included. That is up to 51 levels
(of 255) of moving detail. The trough differs from the panel by 21 levels, 17 after the opacity, so the picture's
detail seen through the panel can be three times stronger than the edge of a trough.

## 3. Findings

Each finding says what it is, why it hurts when playing live, and the fix. H / M / L is high, medium, low.

### Usability

**U1 (H). The stock slider has a small grab target and does not go where you click.**
Tk's own binding (`scale.tcl`, `ScaleButtonDown`) moves a `Scale` by one step when the trough is clicked; only the
thumb drags. So each knob's target is 18 x 30 px, each volume fader's 8 x 16, the crossfader's and the super
knob's 30 x 15. In the dark, under time pressure, a miss does not fail visibly: it nudges the value by 1 and starts
auto-repeating. Fix: a Canvas control whose whole face is the target (section 4), with drag from anywhere, the
wheel, Shift for fine movement and a double click to go back to its starting value.

**U2 (H). Where a knob stands is the hardest thing on the panel to see.** (partly not seen)
A `Scale` paints its thumb in its `bg`, which is set to the panel colour, on a trough at 1.3 : 1 against the panel.
Only the bevel separates them. The value is a 9 pt number that travels with the thumb. On hover the thumb turns
system grey (`activebackground` is left at its default), so the look changes under the pointer. Reading eight to
eighteen knob positions at a glance, which is the point of a mixer, is not possible. Fix: a filled arc (or bar)
in a light colour on a visible track, with the number in a fixed place.

**U3 (H). State that decides what happens next is not shown.**
- Which memory is live: nothing marks it. `recall` and `arrived` change the knobs but no memory button changes.
- The row that is playing on the timeline: `light` recolours only the row's frame. Its children (tag, two grey
  menus, a label with its own background, the "x") cover almost all of the 265 x 38 row, so what is lit is a few
  pixels of padding. (not seen, but the code leaves little room for doubt)
- Held by hand or following the session: no control on either panel shows it. The tempo gives no sign of being
  held; "free", "give back" and "release" give no sign of whether there is anything to free.
- The shape and the tint in force: the viewer already sends `shape` and `tint` in its state message twice a second;
  the visuals panel ignores them, so the buttons never show which is chosen.
- A layer that waits against one that is in: the mixer already sends `in`; the knob panel ignores it. A pulled
  sound gets a strip that looks like every other.
- Waiting for the bar line: pressing "play" on the timeline, "picture now", "film now" or "pull" gives no sign
  that anything was heard. The pull line says "looking for ..." and never changes, found or not.
- What is in play is not marked on the shelf, so the same thing can be put in twice by mistake.

Fix: one rule for both panels, set out in section 4: hot means live or yours, amber means waiting, dimmed means
off, and the three are never used for anything else.

**U4 (H). One press away from frequent controls are presses that cannot be undone.**
- "mute" and "mutate" are 45 x 21 px, 2 px apart, in 7 pt. Mute is reversible; mutate replaces the pattern, and
  Ctrl+mutate goes back to the style's pattern, not to the one just lost.
- "give back" (57 x 23) is 12 px from "next". It hands every hand-set style and pattern back to the director.
- "release" is 6 px from "flash", which is a button meant to be hit in time with the music.
- A plain click on a memory recalls it over whatever stands now, unsaved; Shift+click on the same button
  overwrites the memory. Two opposite actions on one target, told apart by a key, with no undo for either.
- The timeline's "x" is 12 x 21 px, 6 px from the transition menu.

Fix: at least 12 px between a destructive control and a frequent one, a different look for the destructive ones,
and press-and-hold (about 0.4 s, the button fills as it is held) for "give back", "release" and memorising over.

**U5 (H). Meanings hidden behind Shift, Ctrl, timing and gestures, with nothing on screen to say so.**
Shift+mutate, Ctrl+mutate, faster presses giving more hits, Shift+memory, double click on the shelf, drag out of
the window to put in play, drag out of the box to take out, tempo set only on letting go, the thin green slider
being volume with 150 at the top. A first-time user finds none of these; the owner has to remember them in the
dark. Limits are silent too: a ninth memory changes the "memorise" label for good, a thirteenth timeline row and an
eleventh layer are dropped without a word, and the crossfader does nothing while both ends are the same. Fix: the
modifier actions become small visible buttons under "mutate"; every control states its meaning in a one-line hint
bar at the bottom of the panel when the pointer is on it; the modifiers stay as accelerators.

**U6 (H). The windows change size while they are being played.**
The knob panel widens by 65 px per layer, and the timeline, packed on the right, moves with it; the memory row
grows from 26 to 72 px when a picture arrives and pushes the crossfader down; the visuals panel went from 856 to
1539 px wide with the in-play box full. Targets move away from where the hand learned them, and as an inset the
panel can grow off the screen. In full screen the panels have no title bar and cannot be moved at all. Fix: fixed
window sizes; a fixed number of strip slots with the rest reached by scrolling; eight memory slots drawn from the
start; a fixed in-play box that counts what does not fit ("+6"); a strip at the top of each panel to drag it by.

**U7 (M). The layout follows the order things were built in, not the order they are used in.**
From the top: strips, then 283 px of one part's sound design, then tempo and archetype, the pull line, the super
knob, the memories, and last the crossfader, about 780 px below the knobs. The crossfader, the most DJ gesture on
the panel, is the thinnest slider on it (382 x 19). Fix: strips, then one performance block directly under them
(super knob, memories, crossfader), then tempo and archetype; the part's own controls and the pull line go in a
drawer that opens under those.

**U8 (M). "mutate" means different things on a drum and on a layer.**
On a part: new pattern, Shift fewer hits, Ctrl as written. On a layer: move the slices, Shift cut it up another way,
Ctrl one whole sound. Same label, same place. Fix: label the layer's buttons for what they do: "shuffle", "rechop",
"whole"; the part's: "mutate", "fewer", "as written".

**U9 (M). The shelf moves under the pointer.**
Every new picture calls `yview_moveto(1.0)`, so while looking back for an older picture the grid jumps to the end,
possibly between the two clicks of a double click or during a drag. The wheel is bound for the whole window, so it
scrolls the shelf from anywhere. Only 32 of up to 300 things are visible and there is no way to narrow them. A
release outside the window means "put in play" if the drag began on the shelf and "take out of play" if it began in
the in-play box. Fix: follow the end only when already at the end, with a "3 new" marker otherwise; filter buttons
(all, pictures, films, sounds); a right click menu and a small "x" on in-play items as well as the drags; the drop
zone outlined while something is carried.

**U10 (M). The tempo cannot be set to a number.**
240 tempos over about 290 px is 1.2 px per bpm, grabbed by a 30 px thumb, sent on release. Fix: a number box that is
dragged or wheeled, with -1 / +1 buttons beside it and a mark when the tempo is held.

**U11 (M). Menus where two to four choices would fit as buttons.**
Bars (4, 8, 16), transition (smooth, drop, breakdown), filter (off, low, high, band) each cost two clicks and hide
the choice in a grey 31 px box. Fix: segmented buttons with the chosen one lit. Keep menus for the long lists:
damage (14), archetype (16), ducks under (10), body (5), place (6), film length (7).

**U12 (M). Layer names are cut to seven letters.**
`name[:7]`: "rainroof" and "rainroad" both read "rainroo". Fix: a wider strip pitch does not help enough; show the
full name in the hint bar and in the drawer title, and cut in the middle ("rain..ad") on the strip.

**U13 (L). Wording.**
- "give back" on one panel and "release" on the other mean the same. Pick one ("release" is shorter; say what:
  "release to story").
- The shelf has three names: "EVERYTHING THIS SESSION", "the palette" (in the in-play title) and `shelf`.
- The in-play title carries a permanent instruction; the part sheet's title is an explanation ("bass: what its knob
  turns toward (the knob is the drive)"). Instructions belong in the hint bar.
- "rings in a" / "none", "Ducks under" / "as it comes", "free": each needs a second read. Suggested: "Body: none",
  "Ducks under: auto", "Tempo: held / free".
- "Flat for (s)" and "Moving for (s)": the unit belongs with the value ("3.5 s").
- Capitals are mixed: section names in capitals, slider labels with a capital, buttons in lower case.

**U14 (L). Small things.**
The two word boxes have no label until the button at their far end is read. The README says the panel does not
follow knobs moved by typing, the panel's own notes say it does. The in-play box destroys and rebuilds its
thumbnails on every change (possible flicker, not seen).

### Aesthetics

**A1 (H). It reads as a settings dialog.**
Stock `Button`, `OptionMenu` and `Checkbutton` keep the system face: light grey, black text, raised bevel. There
are 24 on the strips alone, 43 on the knob panel as it opens and about 70 once it has memories and timeline rows. On a `#15151a` panel they are the brightest things by
two orders of magnitude, so the eye goes to "mute mute mute mute" and not to the knobs. In a dark room at 80%
opacity they become a grid of pale slabs over the picture. Fix: every stock button and menu restyled flat and dark
with light text (classic `tk.Button` and `Menubutton` honour `bg`, `fg`, `activebackground`, `relief`, `bd` on
Windows); only state lights a button up.

**A2 (H). Hot orange means six things.**
Section headings, the chosen part, a muted part, the pad's dot, film edges on the shelf, "hold flat" when on, and a
darker version for the playing row. A chosen and muted part shows two orange buttons one above the other. Once a
colour is used for headings it can no longer signal anything. Fix: headings go grey; hot is kept for "live or
yours" only; muted, waiting and the kinds of thing on the shelf get their own marks.

**A3 (H). No hierarchy.**
Everything is one of two weights: grey button or thin slider. The super knob, described as the knob that moves them
all, is a 38 px slider like the others, seventh row down. Nothing is big. Fix: three sizes of control by importance
(section 4): large for the super knob, memories, crossfader, flash; medium for part knobs, mute, mutate; small for
set-and-forget.

**A4 (M). Type is too small and too varied.**
7 pt for "mute", "mutate", the timeline "x" and the in-play group names; 8 pt for part names, "dice", "free",
"next", "give back". Six sizes in all, some in two weights. At 80% over a moving picture 7 pt is not readable at arm's length.
Fix: nothing under 9 pt; four sizes.

**A5 (M). Alignment and rhythm are accidental.**
Rows are packed left with their natural widths: 684, 593, 622, 685 and 583 px on the knob panel, so no right edge
lines up. Vertical gaps are 2, 3, 6, 8, 10 and 12 px with no pattern. Label columns are 10 characters wide on one
panel and 13 on the other. The 31 px menus sit in 21 px label rows, so the sheet's rows are uneven (21, 21, 31, 31,
21, 21, 31, 21). Fix: a 4 px unit, gaps of 4 / 8 / 16, one column grid per panel, every row filling the width.

**A6 (M). The two panels do not match.**
Look sliders show values and are 38 px tall; the part sheet's show none and are 19 px. Headings are 10 pt on one
side and 9 pt on the other, orange in one place and white in another. The knob panel's knobs are vertical, the
look's are horizontal. Fix: the same dial, the same button, the same heading on both.

**A7 (M). As an inset it is one opaque-ish slab.**
The whole window is given one opacity, so text and controls fade with the background, and the low-contrast parts
(troughs, hint text, 2 px edges) are lost in the picture first. Fix: a darker ground (`#0c0c10`), lines and tracks
at least 64 levels from it, text near white, and no information carried by a difference smaller than that.
Tk cannot make the background more see-through than the controls; what it can do on Windows is make one colour
fully see-through (`-transparentcolor`), which would let a panel be several separate blocks with the picture
showing between them. That is the nearest tkinter gets to "part of the show"; it is in the build order as an
optional last step.

**A8 (L). Thumbnails.**
A film is told from a picture by a 2 px edge in the same orange as everything else; a picture has no edge. The
system scrollbar is the one widget that cannot be recoloured on Windows. Fix: a corner mark per kind in its own
colour, and a thin drawn position bar instead of the scrollbar.

### What tkinter allows

- Stock `Scale`: thumb-only dragging, trough click steps, thumb and surround share one colour, the value text
  moves with the thumb, a `command` that fires for moves made by the program as well as by hand (the reason for
  the `grabbed` bookkeeping). It can be made less bad (flat thumb, lighter colour, no value) but not good.
- Stock `Button`, `Menubutton`, `Entry`, `Checkbutton`: fully recolourable and flat on Windows. `Scrollbar`: not.
- No rotary control, no rounded corners, no per-widget opacity, no letter spacing.
- `Canvas`: arcs, lines, rectangles, text, images, with mouse events that carry the Shift and Ctrl state even when
  the window has no keyboard focus (which a borderless inset does not). Not anti-aliased: thin arcs look
  stepped. Thick arcs (5 px and more) hide it; if that is not good enough, the hundred or so positions of a dial
  can be drawn once with Pillow at four times the size, shrunk, and shown as images.

What a Canvas control buys: the whole face as target; go-to-click or drag from anywhere; fine movement, wheel,
double click to reset; a fixed place for the value; state drawn in the control (held, following, muted, clamped by
the super knob, with a ghost mark for where the knob was set); one `set(value)` that does not call back, so the
`grabbed` logic goes; and one place for a MIDI controller to connect later. What it costs: about 150 lines for a
dial and a fader, keyboard handling written by hand if wanted, and the stepped edges above.

## 4. Proposed redesign

### Rules

1. One window size per panel. Nothing arriving changes it.
2. Performance controls are large and near each other; sound design and typing are in a drawer.
3. A control is dark until it means something. Hot = live or yours. Amber = waiting. Dim = off.
4. Every action has a visible control. Shift and Ctrl remain as shortcuts for the same actions.
5. The two panels use the same parts.

### Palette

| Name | Hex | Used for |
|---|---|---|
| ground | `#0c0c10` | window background (already the pad's colour) |
| face | `#1c1c24` | button and box faces, always with a 1 px `line` outline |
| line | `#50505e` | outlines, tracks, the unlit part of a dial, dividers |
| dim | `#9a9aa6` | headings, units, hint bar, labels of things that are off |
| text | `#f0f0f0` | labels, values, the lit part of a dial or fader |
| hot | `#ff5a3c` | live or yours: chosen part, live memory, playing row, held-by-hand mark, latched buttons |
| wait | `#ffc233` | waiting: a layer not yet in, play pressed and not yet on the bar, a pull or picture under way |
| sound | `#40c080` | volume bars; sounds on the shelf |
| film | `#b58cff` | films on the shelf |

`line` is 68 levels from `ground`, so it survives the opacity. `face` is not far enough from `ground` to be seen
on its own, which is why faces carry an outline. Muted is not a colour: the strip's dial and name drop to `line`
and `dim`, and its button reads "MUTED" in `ground` on `text` (the one light slab on a strip, and only while muted).

### Type

Segoe UI throughout. Nothing under 9 pt.

| Size | Used for |
|---|---|
| 9 pt regular, `dim` | section headings (in capitals), units, hint bar, secondary buttons ("fewer", "as written") |
| 10 pt bold, `text` | button faces, part names, control labels, menu faces |
| 12 pt bold, `text` | the value in a dial; memory numbers on the timeline |
| 16 pt bold, `text` | tempo, the super knob's value, the number on a memory |

### Minimum sizes (px at 96 dpi; multiply by Tk's scaling over 1.333 elsewhere)

| Thing | Minimum |
|---|---|
| Any press target | 44 x 28 |
| Frequent press target (mute, mutate, memory, play, stop, hold flat, flash) | 56 x 30 |
| Secondary press target | 56 x 22 |
| Dial | 56 x 56 on a strip, 48 x 48 in a grid, 104 x 104 for the super knob |
| Fader | hit area 20 px across its travel whatever is drawn; crossfader cap 28 x 28 |
| Gap between targets | 4 px; 12 px and a divider before anything destructive |
| Thumbnails | 64 px on the shelf, 48 px in "now" (32 px is too small to pick out) |

### The parts

**Dial** (Canvas). A 270 degree track in `line`, 5 px thick, the value as an arc in `text` over it, the number in
the middle at 12 pt bold. Drag up and down anywhere on it (200 px for the whole range), Shift for a quarter of the
speed, the wheel for single steps, double click for its starting value. A two-sided setting (zoom) draws its arc
from the top centre. Marks: a 6 px `hot` dot at the lower right when held by hand; a short `dim` tick on the track
for where the session has it, or for where a knob was set when the super knob has pushed it against an end; whole
dial in `line` and `dim` when its part is muted.

**Fader** (Canvas). A track in `line`, filled to the value, with a cap. Click goes there, drag moves it. Used for
volume (60 x 20, `sound` fill, a tick at 100) and the crossfader (440 x 28, `text` cap, the two ends labelled).

**Button** (stock `tk.Button`, restyled). `face` with `line` outline, 10 pt bold `text`, flat. Three behaviours
on the same look: press; latch (`hot` face while on); hold (fills left to right over 0.4 s, acts when full).

**Segmented choice** (a row of stock buttons). The chosen one has `text` face and `ground` letters.

**Menu** (stock `Menubutton` from `OptionMenu`, restyled the same as a button, with a "v" at its right edge).

**Hint bar** (a `Label`, 9 pt `dim`, the full width at the bottom of each panel). Shows the control under the
pointer and everything it does, for example "mutate hats: new pattern. Press again quickly for more hits.
Shift: fewer. Ctrl: as written." It doubles as the status line ("looking for rain on a tin roof ...", "memory 3
kept", "timeline full: 12 rows").

**Title strip** (a `Frame`, 20 px, at the top of each panel). The panel's name in 9 pt `dim`; dragging it moves
the window, which is the only way to move an inset; a "fold" button shrinks the panel to its first block (the
strips, or the "now" row) and back.

### Knob panel: about 1052 x 500 with the drawer shut, 1052 x 700 with it open

Now: 1014 x 903, growing to 1499 wide. The sketch is to scale: one character is 10 px across, one line 20 px down.
The height is the blocks in the table below plus 12 px of padding top and bottom and 8 px between blocks.

```
+----------------------------------------------------------------------------+--------------------------+
| KNOBS ...................... drag to move ......................... [fold] | TIMELINE                 |
|  kick   snare   hats    sub   [BASS]   tune   bells  drones | rain  vox   >|                          |
|  .--.   .--.   .--.   .--.    .--.    .--.   .--.   .--.    | .--.  .--.   | [1] 4 [8] 16 [smooth v] x|
| ( 0  ) ( 12 ) ( 40 ) ( 0  )  ( 63*)  ( 0  ) ( 25 ) ( 0  )   |( 0  )( 30 )  |                          |
|  '--'   '--'   '--'   '--'    '--'    '--'   '--'   '--'    | '--'  '--'   | [2] 4 [8] 16 [drop   v] x|
| =====- =====- ====-- ======  =====-  ===--- =====- =====-   |=====-=====-  |                          |
| [MUTE] [MUTE] [MUTE] [MUTE]  [MUTE]  [MUTED][MUTE] [MUTE]   |[MUTE][WAITS] |#[1] 4  8 [16][smooth v] x|
| [MUTA] [MUTA] [MUTA] [MUTA]  [MUTA]  [MUTA] [MUTA] [MUTA]   |[SHUF][SHUF]  |                          |
| fewer  fewer  fewer  fewer   fewer   fewer  fewer  fewer    |rechop rechop | [3] 4 [8] 16 [breakd v] x|
| as wr. as wr. as wr. as wr.  as wr.  as wr. as wr. as wr.   |whole  whole  |                          |
|----------------------------------------------------------------------------|                          |
|   .-----.    [MEMORISE]                                                    |                          |
|  /       \   +------++------++------++------++------++------++------++----+|                          |
| |   40    |  |##1###||  2   ||  3   ||  4   ||  .   ||  .   ||  .   || .  ||                          |
| |  SUPER  |  |#live#||   A  ||   B  ||      ||      ||      ||      ||    ||                          |
|  \       /   +------++------++------++------++------++------++------++----+|                          |
|   '-----'    [A: 2 v] |==============[]==========================| [B: 3 v]|                          |
|----------------------------------------------------------------------------|--------------------------|
| TEMPO [-] 140 [+] *held [free]   ARCHETYPE [amen     v] [next]  | [release]| [PLAY ] [STOP ] [loop]   |
| [character v] [pull a sound v]                                             |                          |
| hint: mutate hats: new pattern. Again quickly: more hits. Shift fewer. Ctrl as written.               |
+-------------------------------------------------------------------------------------------------------+
```

| Block | Size | Notes |
|---|---|---|
| Title strip | full width x 20 | |
| Strips | 768 x 232: twelve slots at a 64 px pitch | 8 parts fixed, then 4 layer slots; more layers scroll sideways with the wheel or ">" |
| One strip | name 60 x 26, dial 56 x 56, volume 60 x 20, MUTE 60 x 30, MUTATE 60 x 30, two secondary 60 x 22 | 274 tall now, 232 proposed, with every target larger |
| Performance block | 768 x 112 | super dial 104 x 104; memorise 96 x 30; eight slots 72 x 72 drawn from the start; crossfader 440 x 28 between two menus 76 x 28 |
| Tempo row | 768 x 36 | number 16 pt, dragged or wheeled; -1 / +1 buttons 28 x 28; "release" at the far right behind a divider, press and hold |
| Drawer buttons and hint bar | 768 x 28, full width x 20 | |
| Timeline | 240 wide, full height | rows 240 x 36: picture 32, bars as three segments 28 x 28, transition menu 76 x 28, "x" 24 x 28 after a 12 px gap; nine rows visible, the rest scroll and the playing row is kept in view |
| Transport | PLAY 72 x 36, STOP 72 x 36, loop 60 x 36 (latch) | in line with the tempo row, not at the far corner |

How state shows on it:

- Chosen part: its name in `ground` on `hot`, and a 1 px `hot` outline round the whole strip.
- Muted: "MUTED" light slab, the strip's dial and name dimmed. A chosen and muted strip is now two different marks.
- A layer that waits: its MUTE reads "WAITS" in `wait`; the mixer's `in` list already says which.
- Live memory: a 3 px `hot` border and the word "live" on its slot after a recall or an arrival. When any knob is
  then moved by hand the border goes to `line` and the word to "changed": what is heard is no longer that memory.
- Crossfader ends: "A" and "B" drawn on the two memories' slots as well as in the menus.
- Empty memory slots: a `line` outline and a `dim` number, so the eight are always there and nothing moves.
- Timeline: the playing row is filled `hot` at 35% with a solid `hot` bar at its left; after PLAY and before the
  first arrival, PLAY and the first row are `wait`.
- Tempo and archetype: a `hot` dot and "held" when set by hand; "free" and "release" are dimmed when there is
  nothing to give back.
- Super knob: each part dial shows a `dim` tick where it was set when the super knob has pushed it to an end.

How modifiers become visible: under MUTATE sit "fewer" and "as written" (on a layer: SHUFFLE, "rechop", "whole").
A right click on a memory slot opens a menu: "memorise over this" (asks for a second click), "add to timeline",
"crossfade from here (A)", "crossfade to here (B)". Dragging to the timeline still works; the timeline column is
outlined `hot` while a memory is carried. Pressing mutate quickly shows "+2 hits" in the hint bar.

Behind the drawer ("character" and "pull a sound", each opening the same 200 px area under the tempo row):

```
| BASS character                                                                        |
| [crush   v]  +------------+ [shift v]   Movement  Follow    Body     Cutoff   Reso     Duck   |
|              |            |              .--.     .--.     .--.      .--.     .--.     .--.  |
|              |     o      |             ( 20 )   ( 0  )   ( 35 )    ( 80 )   ( 20 )   ( 70 ) |
|              |            |              '--'     '--'     '--'      '--'     '--'     '--'  |
| [clip    v]  +------------+ [fold  v]   Body [spring v]   Filter [off][LOW][high][band]      |
|              [dice]                     Ducks under [auto v]                                 |
```

Pad 160 x 160 with a faint cross at its centre and the four damage names drawn at its corners; six 48 px dials
in place of six 302 x 19 sliders; the filter kind as four segments. The pull row is the same row as now, restyled,
with its result reported in the hint bar ("rain: found on freesound, waits as a layer" / "nothing found").

Cut or moved: the part sheet's explanatory title (to the hint bar); the six sheet sliders (to dials); the two word
"from" and "as" labels (to grey text inside the empty boxes); the timeline's "bars, then" label; the timeline's
standing hint (to the hint bar); "give back" (renamed "release", moved, held to act).

### Visuals panel: about 768 x 556, fixed

Now: 856 x 631, growing to 1539 wide. Same scale as above.

```
+----------------------------------------------------------------------------+
| VISUALS ..................... drag to move ......................... [fold] |
| LOOK                     | NOW                                              |
|  Chaos    Rest     Move  | showing  film    sounds          swarm           |
|  .--.     .--.     .--. | +-----+ +-----+ +----++----+    +----++----++---+|
| (1.0 )*  (3.5s)   ( 9s )| |     | |     | |    ||    | +2 |    ||    || +6||
|  '--'     '--'     '--' | +-----+ +-----+ +----++----+    +----++----++---+|
|  Folds    Spin     Zoom  |--------------------------------------------------|
|  .--.     .--.     .--. | [words for a picture or a film       ] [PICTURE] |
| ( 0  )   (1.0 )   (0.7 )|                             [FILM] [1 bar     v] |
|  '--'     '--'     '--' |--------------------------------------------------|
|  Trails   Swarm    Split | SHELF  [ALL][pictures][films][sounds]    3 new v |
|  .--.     .--.     .--. | +-----++-----++-----++-----++-----++-----+      ||
| (.75 )   (.80 )   (1.0 )| |     ||     ||  F  ||     ||  S  ||#####|      ||
|  '--'     '--'     '--' | +-----++-----++-----++-----++-----++-----+      ||
| Shape [ANY][sph][tor][rib]| +-----++-----++-----++-----++-----++-----+     ||
| Tint  [ ][#][#][#][#][#][#]| |     ||     ||     ||  F  ||     ||     |     ||
|                          | +-----++-----++-----++-----++-----++-----+      ||
| [HOLD FLAT]  [ FLASH ]   | +-----++-----++-----++-----++-----++-----+      ||
|                          | |     ||     ||     ||     ||     ||     |      ||
|               | [release]| +-----++-----++-----++-----++-----++-----+      ||
| hint: double click or drag to NOW to put in play. Right click for more.     |
+----------------------------------------------------------------------------+
```

| Block | Size | Notes |
|---|---|---|
| LOOK | 260 x 440 | nine dials 48 x 48 in a 3 x 3 grid of 84 x 88 cells, grouped by row: time (chaos, rest, move), space (folds, spin, zoom), layers (trails, swarm, split) |
| Shape | four segments 56 x 28 | the one in force lit, from the `shape` the viewer already sends |
| Tint | seven swatches 30 x 30 | the one in force ringed in `text`, from the `tint` already sent |
| HOLD FLAT, FLASH | 112 x 40 each | hold flat is a latch; flash is the largest plain button on the panel |
| release | 80 x 28, bottom right of the column, behind a divider | press and hold |
| NOW | 464 x 96, fixed | four fixed columns; 64 px for showing and film, 48 px for sounds and swarm; what does not fit is a count ("+6") that opens a list |
| Words | one box 300 x 28, PICTURE 80 x 28, FILM 60 x 28, length menu 96 x 28 | one box serves both; Enter makes a picture |
| Shelf | 6 x 4 thumbnails of 64 px at a 70 px pitch, 420 x 280, with a 6 px drawn position bar | four filter segments above; "3 new" appears when new things arrive while scrolled back |

How state shows on it:

- A look dial held by hand has the `hot` dot; a `dim` tick shows where the story has it. Double click hands that
  one setting back. (The panel knows what it has held since it opened; to be exact after a reopen the viewer has
  to send its `held_look`: see the build order.)
- In play: on the shelf, anything in play has a 3 px `hot` outline. In NOW, the pointer over a removable thing
  shows an "x" at its corner; dragging it out still works.
- Kinds: a film has a `film` coloured corner tab, a sound a `sound` coloured one; a picture has none.
- Under way: after PICTURE or FILM the box's outline goes `wait` and the hint bar says what is being made, until
  the next thing of that kind arrives on the shelf.
- A carried thumbnail outlines NOW in `hot`.

Cut or moved: the second word box; the instruction in the in-play title (to the hint bar); the system scrollbar;
the value text travelling beside each slider; the units in the labels.

### Drawn on a Canvas, or left as stock widgets

| Canvas | Stock, restyled |
|---|---|
| Dial (strips, super, part character, look) | Buttons, latches, hold buttons (`tk.Button`) |
| Fader (volume, crossfader) | Menus (`OptionMenu`'s `Menubutton`) |
| Pad (already a Canvas; add the corner names and centre cross) | Word boxes (`Entry`, already dark) |
| Memory slots (picture, number, border, A/B marks) | Segmented choices (rows of `tk.Button`) |
| Timeline rows (so a row can be lit as a whole) | Hint bar, headings (`Label`) |
| Shelf and NOW (one Canvas each, images placed on it) | Tempo number (`Label` with drag and wheel bindings) |

## 5. Build order

Each step leaves both panels working and can be stopped after.

| # | Step | Size |
|---|---|---|
| 1 | **One theme, no layout change.** A small module with the palette, the four fonts and a function that restyles every stock button, menu and checkbox; headings to `dim`; nothing under 9 pt; the stock `Scale`s given a flat light thumb and a visible trough as a stopgap. The grey slabs go. | small |
| 2 | **State that is already known.** Chosen and muted told apart; the live memory marked; the playing timeline row lit as a whole; the shape and tint in force lit (already in the state message); waiting layers marked (already in `in`); the shelf follows the end only when at the end. | small |
| 3 | **Hint bar and visible modifiers.** The hint bar on both panels; "fewer" and "as written" (or "rechop" and "whole") under mutate; the layer's button renamed; right click menu on memories; "release" and "give back" renamed alike, moved apart and held to act; eight memory slots from the start; messages for the silent limits. | small |
| 4 | **The Dial and the Fader.** One module with the two Canvas controls. Put them on the strips (knob and volume), then the super knob and the crossfader. The `grabbed` and `hold` logic goes. The strip drops from 274 to 232 px. | medium |
| 5 | **Knob panel layout.** Performance block under the strips; tempo number; fixed twelve strip slots with sideways scrolling; part controls and the pull row into the drawer, with dials; timeline rows on a Canvas with segments for the bars; transport moved up. Fixed window size. | medium |
| 6 | **Visuals panel layout.** Dial grid; fixed NOW box with counts; one word box; shelf on one Canvas with filters, in-play outlines and kind tabs; drawn position bar. Fixed window size. | medium |
| 7 | **Title strip.** Drag to move while an inset; fold. Touches `mindstream/inset.py` only to keep the remembered position in step. | small |
| 8 | **State only the viewer knows.** Add to the state message: which look settings are held, whether tempo and style are held, the live memory, the bar within the playing timeline row, and the result of a pull. The panels then show them exactly, and a count-down on the playing row becomes possible. Touches `gl_view.py` and the mixer. | medium |
| 9 | **Optional finish.** Dial positions drawn smooth with Pillow and shown as images; panels as separate blocks with the picture between them (`-transparentcolor`); opacity as a setting. | medium |

Steps 1 to 3 change no control and should remove most of what reads as "settings dialog". Step 4 is the one named
in the verdict.

## 6. Open questions for the owner

1. **Knobs or faders for the parts?** A dial takes the whole face as its target and matches the name, but with a
   mouse it is dragged up and down, not turned, and a row of dials is harder to read at a glance than a row of
   bars. The proposal is dials for the parts and the look, and a straight fader only for the crossfader and volume.
   Is that the feel wanted, or should the parts stay as faders, redrawn?
2. **Is the pad played live, or set beforehand?** If the pad and the character dials are played during a set, the
   drawer should open by default and the window is about 700 px tall; if they are set up before, it stays shut at
   about 500.
3. **How see-through?** 80% lets 20% of the picture through the text as well. 88 to 90% would make the panels
   steadier to read and less part of the picture. Which matters more at an event?
4. **Should memorising over a memory take one deliberate gesture or two?** The proposal is press and hold, or a
   right click and a confirming click. One-press overwrite with Shift is faster and has no undo.
5. **Which MIDI controller, if any?** Knobs without end stops (encoders) or with them, and how many, decide whether
   the dials need a "picked up" state and whether twelve strip slots is the right number.

## Not assessed

These need the panels on screen, which this review did not do:

- How the stock `Scale` thumb, bevels and hover colour really look on the dark ground, and how readable the
  panels are at 80% over a real, moving picture. The contrast figures above are computed.
- Whether restyled menus keep their colours in their drop-down lists on this Windows theme.
- Flicker when the in-play box is rebuilt, and how smooth dragging feels given that changes are sent every 150 ms
  and the session's state arrives twice a second.
- Where the keyboard goes after typing in a word box while the panel is an inset, and whether the viewer's keys
  still work without clicking the viewer again.
- Thumbnail legibility at 64 and 32 px, and whether a sound's drawn shape and name can be read.
- Any scaling other than 96 dpi, and placement on a second screen.
