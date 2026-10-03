"""The knob panel: a knob for every part of the music, the super knob that moves them all, the memories and the
crossfader between them, and the full controls for whichever part is chosen.

Started by the launcher with --knobs, or opened and closed from the viewer with Ctrl+K; it stays on top of the
viewer; when the viewer is full screen it stays where it was left, without its border and see-through, as an inset.
The window has one size: nothing that arrives (a layer, a memory's picture, a row on the timeline) changes it. The
line at its foot says what the control under the pointer does, and what has just happened. The strip across its top
moves the window when dragged (an inset has no title bar to drag). While the panel is an inset, "small" on that
strip leaves only what is played with: the strips (name, knob, mute and mutate), the super knob, the memories, the
crossfader and the edge; "full" brings the rest back as it was. Its top left corner stays where it is. Back in a window the
panel is whole again, and the next time the viewer goes full screen it takes the form it had there last.

From the top:

THE STRIPS, one for each part: the eight parts of the rhythm section, then every layer (each sample pulled in, each
film's sound), small, five across in two rows: there can be ten, and all ten show. A layer that leaves the session
gives up its place. On a layer's strip the two buttons are MUTE and SHUF (shuffle; Shift or Ctrl with it, or its
right-button list, rechop it or make it whole). In a strip:
- its name: press it to choose the part (its strip is then outlined, and the drawer below is about it);
- its knob, a dial that pushes the part into damage (mindstream/mangle.py): nothing at 0, wrecked at 100. Drag it up
  and down from anywhere on its face (Shift for a quarter of the speed), turn it a step at a time with the wheel, or
  double click it for nothing;
- its volume, the green bar: click where you want it, or drag (100 at the tick where it starts, 150 at the right
  end; a double click puts it back at 100);
- MUTE silences the part and brings it back. It reads MUTED while the part is silent, and WAITS on a layer that is
  not in yet;
- MUTATE gives the part a new pattern to play (a drum's loose hits move, the tune takes a new riff, a layer a new
  phrase), and the faster it is pressed the more hits the pattern is given. "fewer" under it gives a softer
  pattern: fewer hits; "as written", the pattern as its style writes it (Shift and Ctrl with MUTATE do the same). On
  a layer (a sample, a film's sound) the three are about its slices and are named for it: SHUFFLE puts the same
  slices in other places, "rechop" cuts the sound up another way, "whole" makes it one whole sound again.

THE SUPER KNOB, the large dial, moves every other knob by as much as it moves itself; a knob pushed past full or
below nothing shows a tick where it was set and comes back when the super knob does. Beside it, "session" lets the
super knob follow the story, slowly (it is how the panel starts); "mine" keeps it where you put it.

THE MEMORIES. "memorise" keeps everything as it stands under the next number: one of the eight slots beside it then
wears a small picture of the middle of the viewer as it was. Press it to go back. The memory being heard is marked
"live", and "changed" once anything is moved by hand. Memorising over a memory takes two gestures, because it cannot
be undone: right click the slot and choose "memorise over this" (or Shift and click it), then press the slot again
within a few seconds. The right click menu also adds the memory to the timeline, or makes it an end of the
crossfader. Eight at most, in memory only: they are gone when the session ends.

THE CROSSFADER, under the memories, stands between two of them: choose one for each end (they are marked A and B on
their slots) and slide. Every knob, volume and level moves between the two as it goes, and on screen the two
memories' pictures are mixed in the same proportion; what cannot be mixed (what the parts play, the style and key,
which layers are in, the caption and the reel) changes over in the middle.

THE EDGE, under them (mindstream/edge.py): two dials over the whole engine. LOCK runs from locked (0: what was
played comes back, things are held) to restless (100: nothing returns, everything turns over); DERANGE from composed
(0: long cuts in their own order, one kind of damage) to deranged (100: cut small, scrambled, stacked). 50 on both
is the engine as it is. The tick on each dial is its lip, where legibility goes partial: past it the engine
rations the dial (one dial at a time, on one lane, for a bar or two at the end of a four-bar group, more after a
long hold), and the words beside them say what the budget is doing. Right click a dial to put its lip where the
dial stands. "session" lets the story move the dials; "mine" (or any turn by hand) keeps them where you put them.
ROLLER is how many bars a riff is held before it changes: 32 a roller, down to 2, a switch-up. HEALTH, beside it, is
the music measuring itself (mindstream/watch.py): healthy in green, looping in amber, drifting into noise in red; the
layers' lag 4 (how much comes back four bars on, over what a fresh deal would give), how many of the checks fail, and
a letter for each lane in that lane's colour. The pointer on it says why.

TEMPO is a number: drag it up and down (Shift for fine), turn the wheel over it, or press - and +. It is set and held
when you let go ("held" shows beside it; "free" lets the session move it again). ARCHETYPE chooses the pattern the
drums, sub and bass play, from the plain styles and the archetypes; "next" steps through them. "hold", 8 or 16, is
how many bars the session leaves the style, key and riffs alone once they have changed. "lead" chooses what plays the
hook, and "chop" how the sample layers are cut up and played (jungle, atmospheric, drumfunk, techstep, breakcore,
footwork); both follow the session, and stay as chosen.

The knobs follow the session: when something typed, a memory or the timeline moves a knob, a volume or a mute, the
panel shows it; a control a hand is on is not moved under that hand. What you set by hand is not put back by the
story: an archetype you choose, and a pattern you mutate, stay until "release" (at the right of the tempo row, behind
a divider; press and hold it) hands the tempo, the style and the patterns to the story's director again.

THE TIMELINE is on the right. Drag a memory's slot onto it (or right click the slot) to add that memory to the end.
Each row is a memory, how many bars it is held for (4, 8 or 16: press one), and how it is left for the next (press
it for the list): "smooth" (its knobs and volumes move toward the next a bar at a time), "drop" (the drums and bass
away for the last bar, then the next lands on the one) or "breakdown" (the same for the second half of its bars);
the "x" takes the row away. PLAY starts it on the next bar line (it stays amber until the first memory arrives),
"loop" sends it round again, STOP leaves the music where it is. The row that is playing is lit, and the knobs show
that memory. Nine rows show; the wheel brings the others round.

THE DRAWER, at the bottom, is open as the panel starts; "character" and "pull a sound" choose what is in it, and
pressing the one that is open shuts it.
- character: the chosen part's own controls, the same as in the knob device (demo/knobs.py): a pad whose corners
  each hold one kind of damage (chosen from the menus beside it, or "dice") and whose dot is the blend between them;
  Movement, a ringing filter sweeping before the damage; Follow, the louder moments driven harder; Body, how much of
  what the result rings in; and a filter after it all, with Cutoff and Reso. The part's knob is the drive. "Ducks
  under" is the part it gives way to each time that part sounds, and Duck how far. For a layer, "Role" is the part it
  plays in the chop: auto (the engine's choice, shown beside it) or anchor, carrier, colour, hook, stab or bed.
- pull a sound: looks for the words in its box, in your Splice library first and then the free archives (or only
  where the menu says), and brings what it finds in as a layer that waits, under the name in the second box or the
  first telling word. Words such as "kick", "snare", "hat" or "vocal" make it that drum, or what the tune plays on,
  instead.

What it says goes out on stdout, one JSON object per line, as messages for the viewer:
    {"type": "visual", "seq": -1, "patch": [{"part": "bass", "set": {"filth": 0.6}}]}
    {"type": "visual", "seq": -1, "patch": [{"part": "bass", "set": {"on": false}}]}
    {"type": "visual", "seq": -1, "patch": [{"part": "bass", "set": {"level": 0.8}}]}
    {"type": "visual", "seq": -1, "patch": [{"part": "bass", "set": {"duck_by": "snare", "duck": 0.7}}]}
    {"type": "visual", "seq": -1, "patch": [{"part": "bass", "patch": {"mix": {"clip": 0.7, "fold": 0.3}, "movement": 0.2, ...}}]}
    {"type": "visual", "seq": -1, "patch": [{"part": "bass", "add_fx": {"type": "filter", "kind": "low", "freq": 900, "q": 0.5}}]}
    {"type": "visual", "seq": -1, "parts": [["bass", "mutate"]]}
    {"type": "visual", "seq": -1, "super": 0.4}
    {"type": "visual", "seq": -1, "lead": "acid"}      what plays the hook
    {"type": "visual", "seq": -1, "chop_style": "drumfunk"}      how the sample layers are chopped
    {"type": "visual", "seq": -1, "role": {"layer": "rain", "role": "hook"}}      a layer's role in the chop (None: auto)
    {"type": "visual", "seq": -1, "edge": {"lock": 0.7}}      the edge's dials, by hand ("derange" too, or both at once)
    {"type": "visual", "seq": -1, "edge": {"auto": true}}     ... given back to the session
    {"type": "visual", "seq": -1, "edge": {"lip": {"lock": 0.6}}}      where a dial's lip sits
    {"type": "visual", "seq": -1, "roller": 16}       bars a riff is held before it changes (2 .. 32)
    {"steer": "!bpm 140", "direct": {"bpm": 140.0}}     the tempo, or {"steer": "!style amen", ...} the archetype: for the story feed, as if typed
    {"steer": "!structure 16"}                        ... and so are these: how long the structure is left alone (8 or 16 bars),
    {"steer": "!super hold"}                          and whose the super knob is ("!super auto": the session's)
    {"type": "visual", "seq": -1, "memorise": 2}      everything as it stands, kept as number 2
    {"type": "visual", "seq": -1, "recall": 2}        ... and gone back to
    {"type": "visual", "seq": -1, "crossfade": {"a": 1, "b": 2, "at": 0.35}}      somewhere between two memories
    {"type": "visual", "seq": -1, "timeline": [{"slot": 1, "bars": 8, "how": "smooth"}, ...], "loop": false}    (an empty list stops it)
What it hears on stdin: {"arrived": 2}, when the timeline has gone to a memory; {"layer": "rain"}, when a new layer wants a knob of its own; and {"thumb": 2, "png": "..."},
the small picture for a memory's slot (a PNG in base64, from the viewer).

    knob_panel.py --try        the panel alone (nothing is listening)
"""
import copy
import time
import json
import os
import queue
import random
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mindstream import theme  # noqa: E402
from mindstream.outbox import Outbox  # noqa: E402
from mindstream.dial import SHIFT, Dial, Fader  # noqa: E402
from mindstream.inset import inset, keep_typing, moved  # noqa: E402
from mindstream.parts import BODIES, DAMAGE  # noqa: E402
from mindstream.theme import DIM, FACE, GROUND, HOT, LINE, TEXT, WAIT  # noqa: E402
from mindstream.soundwords import pull_in  # noqa: E402

PLACES = ("anywhere", "splice", "bbc", "internet archive", "nasa", "freesound")      # where a sound is looked for

# the patterns the drums, sub and bass can play, if the engine cannot be asked for its own list
STYLES = ("four", "twostep", "broken", "dnb", "half", "none", "amen", "rolling", "stutter", "two_step", "gabber")

PARTS = ("kick", "snare", "hats", "sub", "bass", "tune", "bells", "drones")
LEADS = ("auto", "film", "acid", "reese", "hoover", "dub")    # what the lead may play (mindstream/instruments.py)
CHOPS = ("jungle", "atmospheric", "drumfunk", "techstep", "breakcore", "footwork")      # how layers are chopped (mindstream/chopper.py STYLES)
ROLES = ("anchor", "carrier", "colour", "hook", "stab", "bed")     # the part a layer plays in the chop (mindstream/chopper.py ROLES)
EDGE_DIALS = ("lock", "derange")                   # the two dials for the edge (mindstream/edge.py DIALS)
EDGE_WORDS = {"lock": ("locked", "restless"), "derange": ("composed", "deranged")}
EDGE_LIP = 0.5                                     # where a lip starts: the engine as it is (mindstream/edge.py REFERENCE)
ROLLERS = (2, 4, 8, 16, 32)                        # bars a riff is held (mindstream/develop.py ROLLERS)
# the watch's verdicts (mindstream/watch.py), in colours that mean the same in every skin; "quiet" lanes are dim
VERDICT = {"healthy": "#3ddc84", "looping": "#ffb300", "noise": "#ff4d4d"}
MOST_LAYERS = 10
CORNERS = ("clip", "fold", "crush", "shift")       # bottom-left, bottom-right, top-left, top-right, as in the knob device
FILTERS = ("off", "low", "high", "band")
DUCKS = ("auto", "nothing") + PARTS                # what a part gives way to; "auto" is the kick for most parts
BARS, HOWS = (4, 8, 16), ("smooth", "drop", "breakdown")
MEMORIES, SLOT = 8, 72                             # how many memories there are, and how big each one's slot is drawn

# sizes, in pixels: the window is built from blocks of fixed size, so nothing that arrives can change it
PAD = 160                                          # the pad
PITCH, ACROSS = 64, 5                              # a strip every 64; the layers sit five across, in two rows
LEFT = len(PARTS) * PITCH + 9 + ACROSS * PITCH     # the strips: the parts, a divider, and a place for every layer there can be
EDGE_H = 56                                        # the edge's row
WATCH_W = 150                                      # the health readout in it
LINE_W, ROW, ROWS = 240, 36, 9                     # the timeline: its width, the height of a row, how many rows show
WARM = theme.WARM                                   # hot at about a third over the ground: the row that is playing


def short(name):
    """A name cut to fit a strip, in its middle: the two ends are what tell one layer from another."""
    return name if len(name) <= 7 else name[:4] + ".." + name[-2:]


OUT = []                                           # the outbox for what is said, made the first time something is


def say(message):
    """A line for the launcher. Queued (mindstream/outbox.py): the panel never waits on a busy launcher."""
    if not OUT:
        OUT.append(Outbox(sys.stdout.write, sys.stdout.flush, name="to launcher"))
    OUT[0].put(json.dumps({"type": "visual", "seq": -1, **message}) + "\n")


def plain():
    """A part's own controls as they start: the dot in the middle of the pad (an even mix of its four corners, which
    is what the mixer plays until a part is given a character of its own), nothing else on."""
    return {"corners": list(CORNERS), "x": 0.5, "y": 0.5, "movement": 0.0, "follow": 0.0, "body": "none", "body_mix": 0.0,
            "filter": "off", "cutoff": 1.0, "resonance": 0.2, "duck_by": "auto", "duck": 0.7}


def patch_of(sheet):
    """A part's character, as the mixer takes it, from where its pad and dials stand."""
    x, y = sheet["x"], sheet["y"]
    mix = {}
    for name, share in zip(sheet["corners"], ((1 - x) * (1 - y), x * (1 - y), (1 - x) * y, x * y)):
        if share > 0.004:
            mix[name] = round(mix.get(name, 0.0) + share, 3)
    return {"mix": mix, "movement": round(sheet["movement"], 3), "follow": round(sheet["follow"], 3), "body": sheet["body"],
            "body_mix": round(sheet["body_mix"], 3)}


def duck_of(name, sheet):
    """What the part gives way to, and how far, as the mixer takes it."""
    by = sheet["duck_by"]
    return {"part": name, "set": {"duck_by": "none" if by == "nothing" else by, "duck": round(sheet["duck"], 3)}}


def filter_of(name, sheet):
    """The filter after the damage, as an effect on the part; or the instruction to take it away."""
    if sheet["filter"] == "off":
        return {"part": name, "drop_fx": "filter"}
    return {"part": name, "add_fx": {"type": "filter", "kind": sheet["filter"], "freq": round(40.0 * 300.0 ** sheet["cutoff"]), "q": round(sheet["resonance"], 3)}}


class Panel:
    def __init__(self, root, tk, send=say):
        self.root, self.tk, self.send = root, tk, send
        self.own, self.knob, self.super, self.due, self.muted, self.mutes = {}, {}, 0.0, {}, set(), {}
        # was: where each knob was last set, by hand or by the session. When the super knob has pushed a knob against
        # an end, a tick on its dial shows that place: it is where the knob comes back to.
        self.was, self.strip, self.layers, self.first = {}, {}, [], 0
        self.sheets, self.names, self.chosen, self.changed, self.kept, self.numbers, self.thumbs = {}, {}, None, {}, {}, {}, {}
        self.level, self.fader, self.touched = {}, {}, {}       # touched: when each control was last moved by hand
        self.glass, self.pressed = (False, None), {}                 # pressed: when each part's mutate was last pressed
        # waits: the layers that are not in yet. live: the memory that is being heard, as (its number, whether
        # anything has been moved by hand since it was gone back to), or None
        self.waits, self.live = set(), None
        self.asking, self.menu_slot, self.fewer, self.written, self.changes = None, None, {}, {}, {}
        # held: what of the tempo and the style has been set by hand (as far as this panel knows: since it opened);
        # mine: whether a pattern has been mutated by hand. "release" gives them all back.
        self.held, self.mine = {"tempo": False, "style": False}, False
        root.title("Knobs")
        # compact: whether the panel is in its small form (only as an inset); wants_compact: which form was last chosen
        # for full screen. extras: the lesser controls of each strip, which the small form leaves out.
        self.compact, self.wants_compact, self.extras = False, False, {}
        root.configure(padx=12, pady=12, bg=GROUND)
        root.resizable(False, False)
        self.blocks = {}                                      # the blocks the window is made of, by name
        bar = theme.hint_bar(root)                            # the hint bar, across the foot of the panel
        self.hints = theme.Hints(bar)
        for name, wide, high in (("strips", LEFT, 232), ("perform", LEFT, 108), ("tempo", LEFT, 36), ("line", LINE_W, 392),
                                 ("edge", LEFT, EDGE_H), ("tabs", LEFT + 12 + LINE_W, 28), ("drawer", LEFT + 12 + LINE_W, 200)):
            self.blocks[name] = tk.Frame(root, bg=GROUND, width=wide, height=high)
            self.blocks[name].pack_propagate(False)
            self.blocks[name].grid_propagate(False)
        self.blocks["strips"].grid(row=1, column=0, sticky="nw")
        self.blocks["perform"].grid(row=2, column=0, sticky="nw", pady=(8, 0))
        self.blocks["tempo"].grid(row=3, column=0, sticky="nw", pady=(8, 0))
        self.blocks["line"].grid(row=1, column=1, rowspan=3, sticky="nw", padx=(12, 0))
        self.blocks["edge"].grid(row=4, column=0, sticky="nw", pady=(8, 0))
        self.blocks["tabs"].grid(row=5, column=0, columnspan=2, sticky="nw", pady=(8, 0))
        self.blocks["drawer"].grid(row=6, column=0, columnspan=2, sticky="nw", pady=(8, 0))
        bar.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.blocks["hint"] = bar
        self.build_title("KNOBS")
        self.build_line(self.blocks["line"])
        self.build_strips(self.blocks["strips"])
        self.build_perform(self.blocks["perform"])
        self.build_tempo(self.blocks["tempo"])
        self.build_edge(self.blocks["edge"])
        self.build_drawer(self.blocks["tabs"], self.blocks["drawer"])
        for part in PARTS:
            self.add(part)
        self.fade_at = None
        self.choose("bass")
        self.show_held()
        root.after(120, self.flush)
        root.after(1000, self.stay_up)

    # ------------------------------------------------------------------ a strip for each part

    def build_strips(self, block):
        """The eight parts, which are always there; then a place for every layer there can be (ten: six samples and
        four films' sounds), in two rows of five, so that none is ever out of sight."""
        tk = self.tk
        self.fixed = tk.Frame(block, bg=GROUND)
        self.fixed.pack(side="left", anchor="n")
        tk.Frame(block, bg=LINE, width=1).pack(side="left", padx=4, fill="y")
        self.layer_view = tk.Frame(block, bg=GROUND, width=ACROSS * PITCH, height=232)
        self.layer_view.pack(side="left", anchor="n")
        self.layer_view.pack_propagate(False)
        self.layer_view.grid_propagate(False)
        self.nothing_yet = theme.note(self.layer_view, "layers get\ntheir knobs here:\nevery sample and\nevery film's sound", justify="left")
        self.nothing_yet.grid(row=0, column=0, columnspan=ACROSS, sticky="nw", padx=8, pady=6)
        self.layer_menu, self.menu_layer = theme.Menu(block), None
        for words, how in (("shuffle: the same slices in other places", {}), ("rechop: cut up another way", {"softer": True}), ("whole: one sound again", {"restore": True})):
            self.layer_menu.add_command(label=words, command=lambda how=how: self.mutate(self.menu_layer, **how))
        self.show_layers()

    def add(self, name):
        """A strip for one part: its name (press it for the part's own controls), its knob, its volume, mute and mutate.
        A layer's strip is the same things made small: there can be ten of them, and all ten show."""
        if name in self.knob:
            return
        layer = name not in PARTS
        if layer and len(self.layers) >= MOST_LAYERS:
            self.hints.say(f"no room for a knob for {name}: {MOST_LAYERS} layers at most")
            return
        tk, hint = self.tk, self.hints.on
        # the whole strip has a line round it, which is hot while its part is the chosen one
        strip = tk.Frame(self.layer_view if layer else self.fixed, bg=GROUND, highlightthickness=1, highlightbackground=GROUND)
        self.level[name] = 1.0
        if layer:
            label = theme.button(strip, short(name), lambda name=name: self.choose(name), w=60, h=22, font=theme.SMALL)
            knob = Dial(strip, size=44, font=theme.LABEL, thick=4, command=lambda value, name=name: self.turn(name, value / 100.0))
            fader = Fader(strip, w=60, h=14, low=0, high=150, start=100, home=100, mark=100, command=lambda value, name=name: self.volume(name, value / 100.0))
            pair = tk.Frame(strip, bg=GROUND)
            mute = theme.button(pair, "MUTE", lambda name=name: self.mute(name), w=30, h=24, font=theme.SMALL)
            change = theme.button(pair, "SHUF", lambda name=name: self.mutate(name), w=30, h=24, font=theme.SMALL)
            mute.pack(side="left")
            change.pack(side="left")
            change.bind("<Button-3>", lambda event, name=name: self.layer_choices(event, name))
            for row, widget in enumerate((label, knob, fader, pair)):
                widget.grid(row=row, column=0, pady=(2 if row else 0, 0))
            fewer = written = None
            self.extras[name] = (fader,)
        else:
            label = theme.button(strip, short(name), lambda name=name: self.choose(name), w=60, h=26)
            knob = Dial(strip, size=56, command=lambda value, name=name: self.turn(name, value / 100.0))
            fader = Fader(strip, w=60, h=20, low=0, high=150, start=100, home=100, mark=100, command=lambda value, name=name: self.volume(name, value / 100.0))
            mute = theme.button(strip, "MUTE", lambda name=name: self.mute(name), w=60, h=30)
            change = theme.button(strip, "MUTATE", lambda name=name: self.mutate(name), w=60, h=30)
            fewer = theme.button(strip, "fewer", lambda name=name: self.mutate(name, softer=True), w=60, h=22, font=theme.SMALL, fg=DIM)
            written = theme.button(strip, "as written", lambda name=name: self.mutate(name, restore=True), w=60, h=22, font=theme.SMALL, fg=DIM)
            for row, widget in enumerate((label, knob, fader, mute, change, fewer, written)):
                widget.grid(row=row, column=0, pady=(4 if row else 0, 0))
            self.extras[name] = (fader, fewer, written)
        change.bind("<Shift-Button-1>", lambda event, name=name: (self.mutate(name, softer=True), "break")[1])
        change.bind("<Control-Button-1>", lambda event, name=name: (self.mutate(name, restore=True), "break")[1])
        self.knob[name], self.own[name] = knob, -self.super          # a new part starts at nothing, whatever the super knob says
        self.mutes[name], self.names[name], self.sheets[name], self.strip[name], self.fader[name] = mute, label, plain(), strip, fader
        self.changes[name], self.fewer[name], self.written[name] = change, fewer, written
        if self.compact:
            for widget in self.extras[name]:
                widget.grid_remove()
        hint(knob, f"{name} knob: how far it is pushed into damage. Drag up and down; Shift for fine; the wheel for single steps; double click for nothing.")
        hint(fader, f"{name} volume: 100 at the tick, 150 at the right. Click to go there, or drag; double click for 100.")
        hint(label, f"{name}: press to choose it. The character controls in the drawer are then this part's.")
        hint(mute, lambda name=name: f"{name} waits: it is not in yet. Shuffle it, or put its sound in play on the visuals panel, to bring it in. This button mutes."
             if name in self.waits and name not in self.muted else f"Mute {name}, or bring it back. Its knob stays where it is.")
        if layer:
            hint(change, f"Shuffle {name}: the same slices in other places. Shift, or the right button's list: rechop (cut up another way). Ctrl, or the list: one whole sound again.")
            self.layers.append(name)
            self.show_layers()
        else:
            hint(change, f"Mutate {name}: a new pattern. Press again quickly for more hits. Shift: fewer. Ctrl: as written.")
            hint(fewer, f"Fewer: a new pattern for {name} with a hit fewer, and fewer still the faster it is pressed (the same as Shift with mutate).")
            hint(written, f"As written: {name} put back as its style writes it (the same as Ctrl with mutate).")
            strip.pack(side="left", padx=1)

    def remove(self, name):
        """A layer that is no longer in the session: its strip goes, and the others close up."""
        if name not in self.layers:
            return
        self.layers.remove(name)
        self.strip[name].destroy()
        for held in (self.knob, self.own, self.was, self.mutes, self.names, self.sheets, self.strip, self.fader, self.changes, self.fewer, self.written,
                     self.extras, self.level, self.pressed, self.touched):
            held.pop(name, None)
        self.roles.pop(name, None)
        self.touched.pop("role:" + name, None)
        self.muted.discard(name)
        self.waits.discard(name)
        self.show_layers()
        if self.chosen == name:
            self.chosen = None
            self.choose("bass")

    def layer_choices(self, event, name):
        """The right button on a layer's SHUF: the three things it can do to the layer's slices, as a list."""
        self.menu_layer = name
        self.layer_menu.tk_popup(event.x_root, event.y_root)

    def show_layers(self):
        """Every layer's strip, five across: the first five in the top row, the rest below."""
        if self.layers:
            self.nothing_yet.grid_remove()
        else:
            self.nothing_yet.grid()
        for at, name in enumerate(self.layers):
            self.strip[name].grid(row=at // ACROSS, column=at % ACROSS, padx=1, pady=(0 if at < ACROSS else 4, 0), sticky="n")

    def turn(self, name, value):
        """A knob turned by hand (a dial says so only then): that is where it stands, and the super knob adds to it
        from here."""
        self.touched[name] = time.time()
        self.own[name], self.was[name] = value - self.super, value
        self.knob[name].tick(None)
        self.due[name] = value
        self.by_hand()

    def volume(self, name, value):
        """A part's volume fader moved by hand."""
        if abs(self.level[name] - value) < 0.006:
            return
        self.touched[name] = time.time()
        self.level[name] = value
        self.changed.setdefault(name, set()).add("level")
        self.by_hand()

    def mutate(self, name, now=None, softer=False, restore=False):
        """A new pattern for the part; and the faster the button is pressed, the more hits the pattern is given: one
        more when presses are under a second apart, two under half a second, three under a quarter. With Shift (or
        "fewer") it is a softer pattern instead: a hit fewer each press, and more fewer the faster it is pressed. With
        Ctrl (or "as written") the part is put back as its style writes it.
        On a layer (a sample, a film's sound) the three are about its slices: plain puts the same slices in other
        places, Shift cuts the sound up another way, and Ctrl makes it one whole sound again."""
        now = time.time() if now is None else now
        self.by_hand()
        self.mine = True
        self.show_held()
        if name not in PARTS and (softer or restore):
            self.touched[name] = now
            # ... and a layer that was waiting is brought in: a change made by hand is meant to be heard
            self.send({"patch": [{"part": name, "chop": "whole" if restore else "next"}, {"part": name, "bring": True}]})
            return
        if restore:
            self.touched[name] = now
            self.send({"parts": [[name, "as written"]]})
            return
        gap, self.pressed[name] = now - self.pressed.get(name, 0.0), now
        more = 3 if gap <= 0.25 else 2 if gap <= 0.5 else 1 if gap <= 1.0 else 0
        self.touched[name] = now
        self.send({"parts": [[name, "mutate"]] + ([[name, "sparser"]] * (1 + more) if softer else [[name, "busier"]] * more)})
        if softer or more:
            count = 1 + more if softer else more
            self.hints.say(f"{name}: " + (f"{count} fewer" if softer else f"+{count}") + (" hits" if count > 1 else " hit"), 2.0)

    def mute(self, name):
        """The part silenced, or brought back. Its knob stays where it is."""
        self.muted ^= {name}
        self.touched[name] = time.time()
        self.by_hand()
        self.show_mutes()
        self.send({"patch": [{"part": name, "set": {"on": name not in self.muted}}]})

    def show_mutes(self):
        """Each strip says how its part stands. The chosen part's name is hot and its strip is outlined. A muted part's
        button is the one light slab on its strip and reads MUTED, and its name, dial and volume go grey; a layer that
        is not in yet reads WAITS, in amber."""
        for name, button in self.mutes.items():
            off, waits = name in self.muted, name in self.waits
            theme.lit(button, off, TEXT)
            small = name not in PARTS                          # a layer's button is half the width
            button.configure(text=("OFF" if small else "MUTED") if off else ("WAIT" if small else "WAITS") if waits else "MUTE")
            if waits and not off:
                button.configure(fg=WAIT, activeforeground=WAIT)
            theme.lit(self.names[name], name == self.chosen)
            if off and name != self.chosen:
                self.names[name].configure(fg=DIM, activeforeground=DIM)
            self.strip[name].configure(highlightbackground=HOT if name == self.chosen else GROUND)
            self.knob[name].dim(off)
            self.fader[name].dim(off)

    def by_hand(self):
        """Something was moved by hand: what is heard is no longer the memory that was gone back to."""
        if self.live is not None and not self.live[1]:
            self.live = (self.live[0], True)
            self.show_memories()

    def place(self):
        """Every knob put where its own setting and the super knob say it stands, without that counting as a turn by hand."""
        for name, knob in self.knob.items():
            stands = min(max(self.own[name] + self.super, 0.0), 1.0)
            knob.set(round(stands * 100))
            was = self.was.get(name)                          # pushed against an end: a tick where it was set
            knob.tick(round(was * 100) if was is not None and stands in (0.0, 1.0) and abs(was - stands) > 0.015 else None)

    def turn_super(self, value):
        """The super knob turned by hand: every other knob moves by as much, from where it was set."""
        self.touched["*"] = time.time()
        self.by_hand()
        self.super = float(value) / 100.0
        self.place()
        self.due["*"] = self.super


    # ------------------------------------------------------------------ the title strip, and the small form of an inset

    def build_title(self, name):
        """The strip across the top: drag it to move the panel (an inset has no title bar), and its button for the small form."""
        self.title_strip = theme.TitleStrip(self.root, name, lambda x, y: moved(self.root, x, y), self.toggle_compact)
        self.title_strip.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        for handle in self.title_strip.handles:
            self.hints.on(handle, "Drag here to move the panel. In full screen it stays where you leave it.")
        self.hints.on(self.title_strip.button, lambda: "Back to the full panel." if self.compact else
                      "The small form, for full screen: only what is played with. Everything else comes back, as it was, with the full form."
                      if self.glass[0] else "The small form is for when the viewer is full screen and this panel is an inset in it.")
        self.title_strip.button.configure(fg=DIM)

    def toggle_compact(self):
        """The button on the title strip: the small form, or the full one again. Only an inset has a small form; which
        of the two was chosen is remembered for the next time the viewer goes full screen."""
        if not self.glass[0]:
            self.hints.say("the small form is for full screen: in a window the panel is whole")
            return
        self.wants_compact = not self.compact
        self.set_compact(self.wants_compact)

    def set_compact(self, on):
        """The panel made small, or whole again, without moving: its top left corner stays where it is."""
        if bool(on) == self.compact:
            return
        self.compact = bool(on)
        at = getattr(self.root, "_inset_at", None)
        self.arrange()
        self.title_strip.button.configure(text="full" if self.compact else "small")
        if at is not None and self.glass[0]:
            self.root.update_idletasks()
            self.root.geometry(f"+{at[0]}+{at[1]}")

    def arrange(self):
        """The blocks put out for the form the panel is in. Small: the strips without their volumes and lesser buttons,
        the super knob, the memories, the crossfader and the edge; the tempo row, the timeline and the drawer are put away.
        Nothing is lost: what is put away keeps its state and comes back with the full form."""
        for name in ("tempo", "line", "tabs", "drawer"):
            if self.compact or (name == "drawer" and self.drawer is None):
                self.blocks[name].grid_remove()
            else:
                self.blocks[name].grid()
        for widgets in self.extras.values():
            for widget in widgets:
                widget.grid_remove() if self.compact else widget.grid()
        high = 200 if self.compact else 232                   # (two rows of layers without their volumes are 196 high)
        self.blocks["strips"].configure(height=high)
        self.layer_view.configure(height=high)

    # ------------------------------------------------------------------ the super knob, the memories, the crossfader

    def build_perform(self, block):
        """What is played with, close together and large: the super knob, the eight memories, the crossfader."""
        tk, hint = self.tk, self.hints.on
        self.master = Dial(block, size=104, font=theme.BIG, thick=8, caption="SUPER", command=self.turn_super)
        self.master.pack(side="left", anchor="n", padx=(0, 12))
        hint(self.master, "Super knob: moves every other knob by as much as it moves itself. A knob pushed against an end shows a tick where it was set, "
             "and comes back when this does. Drag up and down; Shift for fine; the wheel for single steps.")
        right = tk.Frame(block, bg=GROUND)
        right.pack(side="left", anchor="n")
        self.slots = tk.Frame(right, bg=GROUND)
        self.slots.pack(anchor="w")
        self.build_slots()
        self.keep = theme.button(self.slots, "memorise", self.memorise, w=76, h=SLOT)
        self.keep.pack(side="left", padx=(2, 0))
        hint(self.keep, "Memorise: everything as it stands, kept under the next number. Eight at most.")
        fade = tk.Frame(right, bg=GROUND)
        fade.pack(anchor="w", pady=(8, 0))
        # whose the super knob is. The session moves it with the story (it creeps, and jumps on a change of scene);
        # "mine" keeps it where the hand put it. Either way the dial follows what the viewer says, when no hand is on it.
        self.super_whose = theme.Segments(fade, ("session", "mine"), command=lambda whose: self.steer({"steer": "!super auto" if whose == "session" else "!super hold"}),
                                          w=52, start="session", font=theme.SMALL)
        self.super_whose.pack(side="left", padx=(2, 10))
        for button in self.super_whose.buttons.values():
            hint(button, "session: the super knob follows the story, slowly; mine: it stays where you put it")
        self.ends = [tk.StringVar(value="-"), tk.StringVar(value="-")]
        for var in self.ends:                                 # the two ends are marked A and B on their memories
            var.trace_add("write", lambda *_: self.show_memories())
        self.end_menu = [theme.Choice(fade, self.ends[0], ("-",), command=lambda value: self.fade_to(), w=76, says=lambda value: "A: " + value), None]
        self.end_menu[0].pack(side="left", padx=(2, 0))
        self.cross = Fader(fade, w=LEFT - 116 - 2 * 76 - 14 - 116, h=28, cap=28, fill=DIM, command=lambda value: self.fade_to())
        self.cross.pack(side="left", padx=6)
        self.end_menu[1] = theme.Choice(fade, self.ends[1], ("-",), command=lambda value: self.fade_to(), w=76, says=lambda value: "B: " + value)
        self.end_menu[1].pack(side="left")
        hint(self.cross, "Crossfader: between memory A and memory B. Every knob, volume and level moves between the two, and the pictures are mixed. "
             "Click to go there, or drag.")
        hint(self.end_menu[0], "The memory at the crossfader's left end (A).")
        hint(self.end_menu[1], "The memory at the crossfader's right end (B).")
        self.show_memories()

    def build_slots(self):
        """The eight memories, there from the start so that nothing moves when one is filled. Each is drawn: its
        picture, its number, whether it is live, and A or B if it is an end of the crossfader."""
        tk = self.tk
        self.slot_at = {}
        for slot in range(1, MEMORIES + 1):
            box = tk.Canvas(self.slots, width=SLOT, height=SLOT, bg=GROUND, highlightthickness=0, bd=0)
            box.pack(side="left", padx=2)
            box.bind("<B1-Motion>", lambda event, slot=slot: self.carry_memory(slot))
            box.bind("<ButtonRelease-1>", lambda event, slot=slot: self.let_go_slot(event, slot))
            box.bind("<Button-3>", lambda event, slot=slot: self.slot_menu_at(event, slot))
            self.hints.on(box, lambda slot=slot: self.slot_hint(slot))
            self.slot_at[slot] = box
        self.slot_menu = theme.Menu(self.slots)
        self.slot_menu.add_command(label="memorise over this", command=lambda: self.over(self.menu_slot))
        self.slot_menu.add_command(label="add to timeline", command=lambda: self.line_add(self.menu_slot))
        self.slot_menu.add_command(label="crossfade from here (A)", command=lambda: self.set_end(0, self.menu_slot))
        self.slot_menu.add_command(label="crossfade to here (B)", command=lambda: self.set_end(1, self.menu_slot))

    def slot_hint(self, slot):
        if slot not in self.numbers:
            return f"Memory {slot}: empty. \"memorise\" keeps everything as it stands under the next number."
        return (f"Memory {slot}: press to go back to it. Drag it to the timeline. Right click (or Shift and click, then click again) to memorise over it, "
                "or to make it an end of the crossfader.")

    def draw_slot(self, slot):
        box = self.slot_at[slot]
        box.delete("all")
        there, live, asking = slot in self.numbers, self.live is not None and self.live[0] == slot, self.asking == slot
        if slot in self.thumbs:
            box.create_image(SLOT // 2, SLOT // 2, image=self.thumbs[slot])
        fresh = live and not self.live[1]
        if asking or fresh:
            box.create_rectangle(1, 1, SLOT - 2, SLOT - 2, outline=WAIT if asking else HOT, width=3)
        else:
            box.create_rectangle(0, 0, SLOT - 1, SLOT - 1, outline=LINE, width=1)

        def words(x, y, text, font, colour):                  # with a dark copy behind, to be read over a light picture
            box.create_text(x + 1, y + 1, text=text, font=font, fill=GROUND)
            box.create_text(x, y, text=text, font=font, fill=colour)
        words(SLOT // 2, SLOT // 2 - 6, str(slot), theme.BIG, TEXT if there else DIM)
        if asking:
            words(SLOT // 2, SLOT - 14, "over?", theme.SMALL, WAIT)
        elif live:
            words(SLOT // 2, SLOT - 14, "live" if fresh else "changed", theme.SMALL, HOT if fresh else DIM)
        for end, letter, x in ((0, "A", 11), (1, "B", SLOT - 11)):
            if there and self.ends[end].get() == str(slot):
                words(x, 11, letter, theme.LABEL, TEXT)

    def show_memories(self):
        """The memory that is live wears a hot edge and the word "live", until something is moved by hand: then it
        says "changed", because what is heard is no longer that memory."""
        for slot in self.slot_at:
            self.draw_slot(slot)

    def let_go_slot(self, event, slot):
        """A memory's slot let go: after a drag, it is dropped (on the timeline, if that is where); else it was a press."""
        if self.carried == slot:
            self.drop_memory(event, slot)
        elif event.state & SHIFT and self.asking != slot:     # Shift: memorise over it, once it is pressed again
            self.over(slot)
        else:
            self.press_slot(slot)

    def press_slot(self, slot):
        """A plain press goes back to the memory. The press that follows "memorise over this" is the one that does it."""
        if self.asking == slot:
            self.memorise(slot)
        elif slot in self.numbers:
            self.asking = None
            self.recall(slot)
        else:
            self.hints.say(f"memory {slot} is empty")

    def over(self, slot):
        """Memorising over a memory cannot be undone, so it takes two gestures: this asks, and the next press on the
        same slot within a few seconds does it. Anything else leaves the memory as it was."""
        if slot not in self.numbers:
            return
        self.asking = slot
        self.show_memories()
        self.hints.say(f"memory {slot}: press it again to memorise over it")
        self.root.after(4000, lambda: self.forget_asking(slot))

    def forget_asking(self, slot):
        if self.asking == slot:
            self.asking = None
            self.show_memories()

    def slot_menu_at(self, event, slot):
        if slot in self.numbers:
            self.menu_slot = slot
            self.slot_menu.tk_popup(event.x_root, event.y_root)

    def set_end(self, end, slot):
        """A memory made one end of the crossfader."""
        if slot in self.numbers:
            self.ends[end].set(str(slot))
            self.fade_to()

    def memorise(self, slot=None):
        """Everything as it stands, kept under the next number (or over `slot`); the panel keeps its own knobs with it."""
        if slot is None:
            slot = max(self.numbers, default=0) + 1
            if slot > MEMORIES:
                self.hints.say(f"all {MEMORIES} memories are in use: right click one, or Shift and click it, to memorise over it")
                return
        self.number(slot)
        self.kept[slot] = (dict(self.own), self.super, set(self.muted), copy.deepcopy(self.sheets), dict(self.level))
        self.send({"memorise": slot})
        self.live, self.asking = (slot, False), None          # what is heard is this memory, until something is moved
        self.show_memories()
        self.hints.say(f"memory {slot} kept")

    def number(self, slot):
        """A memory's slot comes into use: press to go back, drag to the timeline, right click for the rest."""
        if slot in self.numbers or slot not in self.slot_at:
            return
        self.numbers[slot] = self.slot_at[slot]
        for menu in self.end_menu:                            # the crossfader can stand at any memory
            menu.fill(str(number) for number in sorted(self.numbers))
        if len(self.numbers) == 1:
            self.ends[0].set(str(slot))
        elif self.ends[1].get() == "-":
            self.ends[1].set(str(slot))
        self.draw_slot(slot)

    def fade_to(self):
        """The crossfader moved, or one of its ends changed: where it stands goes out with the next flush."""
        if self.ends[0].get().isdigit() and self.ends[1].get().isdigit() and self.ends[0].get() != self.ends[1].get():
            now = (int(self.ends[0].get()), int(self.ends[1].get()), self.cross.get() / 100.0)
            if now != self.fade_at:
                self.fade_at = now
                self.due["fade"] = now
        else:
            self.hints.say("the crossfader needs a different memory at each end")

    def picture(self, slot, png):
        """The small picture of the viewer as it was when a number was memorised, put on that number's slot. A memory
        made while this panel was closed comes into use here."""
        self.number(slot)
        if not png:
            return
        try:
            self.thumbs[slot] = self.tk.PhotoImage(data=png)      # kept here too: tk forgets a picture nobody else holds
            self.draw_slot(slot)
            for entry in self.entries:                        # and on its rows of the timeline
                if entry["slot"] == slot:
                    self.wear(entry)
            self.draw_line()
        except Exception:
            pass

    def recall(self, slot):
        """Back to a number: the mixer puts everything back, and the panel's knobs, mutes and sheets go to where they were."""
        self.send({"recall": slot})
        self.display(slot)
        if slot in self.numbers:
            self.live = (slot, False)
            self.show_memories()

    def display(self, slot):
        """The panel's knobs, mutes and sheets put where they stood when a number was memorised. Nothing is sent."""
        if slot not in self.kept:
            return
        own, lifted, muted, sheets, levels = self.kept[slot]
        self.own = {name: own.get(name, -lifted) for name in self.knob}       # a part that has arrived since stands at nothing
        self.super = lifted
        self.master.set(round(lifted * 100))
        self.was = {name: min(max(self.own[name] + lifted, 0.0), 1.0) for name in self.knob}
        self.place()
        self.muted = {name for name in muted if name in self.knob}
        self.show_mutes()
        self.sheets = {name: copy.deepcopy(sheets.get(name) or plain()) for name in self.knob}
        for name, fader in self.fader.items():
            self.level[name] = levels.get(name, 1.0)
            fader.set(round(self.level[name] * 100))
        self.changed = {}
        self.show()

    # ------------------------------------------------------------------ tempo and archetype

    def build_tempo(self, block):
        tk, hint = self.tk, self.hints.on
        theme.heading(block, "TEMPO").pack(side="left")
        hint(theme.button(block, "-", lambda: self.nudge(-1), w=28, h=28), "Tempo: one slower. It is set and held a moment after the last press.").pack(side="left", padx=(8, 0))
        self.tempo_at, self.tempo_hand, self.tempo_due = 120, False, None
        self.tempo_label = tk.Label(block, text="120", fg=TEXT, bg=GROUND, font=theme.BIG, width=3, cursor="sb_v_double_arrow")
        self.tempo_label.pack(side="left", padx=4)
        self.tempo_label.bind("<ButtonPress-1>", self.tempo_press)
        self.tempo_label.bind("<B1-Motion>", self.tempo_drag)
        self.tempo_label.bind("<ButtonRelease-1>", self.tempo_let_go)
        self.tempo_label.bind("<MouseWheel>", lambda event: self.nudge(1 if event.delta > 0 else -1))
        hint(self.tempo_label, "Tempo, 60 to 300: drag up and down (Shift for fine), or turn the wheel. It is set and held when you let go; \"free\" lets the session move it again.")
        hint(theme.button(block, "+", lambda: self.nudge(1), w=28, h=28), "Tempo: one faster. It is set and held a moment after the last press.").pack(side="left")
        self.tempo_mark = tk.Label(block, text="", fg=HOT, bg=GROUND, font=theme.SMALL, width=6, anchor="w")
        self.tempo_mark.pack(side="left", padx=(6, 0))
        self.free = hint(theme.button(block, "free", lambda: self.say_steer("!bpm auto", {}), w=36, h=28), "Tempo free: the session moves the tempo again.")
        self.free.pack(side="left")
        theme.heading(block, "ARCHETYPE").pack(side="left", padx=(12, 0))
        self.style = tk.StringVar(value="four")
        # a long name is cut in its middle on the menu's face; the list and the hint bar have it whole
        hint(theme.Choice(block, self.style, self.styles(), command=self.archetype, w=100, says=lambda name: name if len(name) <= 11 else name[:6] + ".." + name[-3:]),
             lambda: f"Archetype: {self.style.get()}. The pattern the drums, sub and bass play. One you choose stays until \"release\".").pack(side="left", padx=(8, 0))
        self.style_mark = tk.Label(block, text="", fg=HOT, bg=GROUND, font=theme.SMALL, width=2, anchor="w")
        self.style_mark.pack(side="left", padx=(4, 0))
        hint(self.style_mark, "A hot dot: the archetype was chosen by hand, and stays until \"release\".")
        hint(theme.button(block, "next", self.next_archetype, w=36, h=28), "Next archetype.").pack(side="left")
        # there is nothing in the state message for this yet: the panel shows what was last chosen here
        self.structure = tk.StringVar(value="8")
        hint(theme.Choice(block, self.structure, ("8", "16"), command=lambda bars: self.steer({"steer": f"!structure {bars}"}), w=62,
                          says=lambda bars: "hold: " + bars),
             "Hold: how many bars the session leaves the style, key and riffs alone once they have changed; its changes land on four-bar lines").pack(side="left", padx=(12, 0))
        self.lead = tk.StringVar(value="auto")
        hint(theme.Choice(block, self.lead, LEADS, command=self.choose_lead, w=90, says=lambda name: "lead: " + name),
             lambda: "Lead: what plays the hook. auto: the film's own sound and the scene's synth, a section each; film: the film's sound only; "
                     "acid, reese, hoover or dub: that synth only. It stays as chosen.").pack(side="left", padx=(8, 0))
        self.chop = tk.StringVar(value="jungle")
        # a long name is cut in its middle on the face, as the archetype's is
        hint(theme.Choice(block, self.chop, CHOPS, command=self.choose_chop, w=112, says=lambda name: "chop: " + (name if len(name) <= 9 else name[:4] + ".." + name[-3:])),
             lambda: f"Chop: {self.chop.get()}. How the sample layers are cut up and played: jungle, atmospheric, drumfunk, techstep, "
                     "breakcore or footwork. It stays as chosen.").pack(side="left", padx=(6, 0))
        self.release = theme.HoldButton(block, "release", self.give_back, w=56, h=28)
        hint(self.release, "Release: press and hold. The tempo, the style and every pattern set by hand go back to the story's director.").pack(side="right")
        tk.Frame(block, bg=LINE, width=1, height=28).pack(side="right", padx=(8, 7))       # a divider before what cannot be undone

    def choose_lead(self, name):
        """What the lead plays, chosen by hand."""
        self.touched["lead"] = time.time()
        self.send({"lead": name})

    def choose_chop(self, name):
        """How the sample layers are chopped, chosen by hand."""
        self.touched["chop"] = time.time()
        self.send({"chop_style": name})

    # ------------------------------------------------------------------ the edge, and the roller

    def build_edge(self, block):
        """The two dials for the edge with their lips, whose they are, where the budget stands, and the roller."""
        tk, hint = self.tk, self.hints.on
        theme.heading(block, "EDGE").pack(side="left")
        self.edge_dial, self.edge_lips = {}, {dial: EDGE_LIP for dial in EDGE_DIALS}
        for dial in EDGE_DIALS:
            knob = Dial(block, size=EDGE_H - 4, font=theme.LABEL, thick=4, start=50, caption=dial,
                        command=lambda value, dial=dial: self.turn_edge(dial, value))
            knob.set(50)
            knob.tick(round(EDGE_LIP * 100))
            knob.pack(side="left", padx=(8, 0))
            knob.bind("<Button-3>", lambda event, dial=dial: self.edge_lip_here(dial))
            low, high = EDGE_WORDS[dial]
            hint(knob, lambda dial=dial, low=low, high=high: f"{dial.capitalize()}: {low} (0) to {high} (100); 50 is the engine as it is. "
                 f"The tick is its lip, now {self.edge_lips[dial] * 100:.0f}: past it the engine rations the dial. Right click: the lip here. "
                 "Double click: back to 50.")
            self.edge_dial[dial] = knob
        self.edge_whose = theme.Segments(block, ("session", "mine"), command=self.edge_owner, w=52, start="session", font=theme.SMALL)
        self.edge_whose.pack(side="left", padx=(12, 0))
        for button in self.edge_whose.buttons.values():
            hint(button, "session: the story moves the edge's dials; mine: they stay where you put them (a turn by hand makes them yours)")
        self.edge_said = tk.Label(block, text="within the lips", fg=DIM, bg=GROUND, font=theme.SMALL, width=28, anchor="w")
        self.edge_said.pack(side="left", padx=(10, 0))
        hint(self.edge_said, "Where the edge's budget stands: one dial past its lip at a time, on one lane, for a bar or two, back on a four-bar line.")
        self.roller_choice = theme.Segments(block, ROLLERS, command=self.choose_roller, w=30, start=16, font=theme.SMALL)
        self.roller_choice.pack(side="right")
        for button in self.roller_choice.buttons.values():
            hint(button, "Roller: how many bars a riff is held before it changes. 32: a roller, held and only mutated; 2: a switch-up.")
        theme.heading(block, "ROLLER").pack(side="right", padx=(0, 6))
        # the music's health, as it measures itself (mindstream/watch.py): the verdict in its colour, the layers' lag 4,
        # the checks failing, and a letter for each lane in that lane's colour. The hint says why.
        self.watch = None
        self.watch_box = tk.Canvas(block, width=WATCH_W, height=EDGE_H - 6, bg=GROUND, highlightthickness=0)
        self.watch_box.pack(side="right", padx=(0, 12))
        hint(self.watch_box, self.watch_why)
        self.show_watch()

    def show_watch(self):
        """The health readout drawn from the last report (state["watch"], watch.compact); "watching" until there is one."""
        box, w = self.watch_box, self.watch
        box.delete("all")
        box.create_text(0, 1, text="HEALTH", anchor="nw", fill=DIM, font=theme.SMALL)
        if not w:
            box.create_text(52, 1, text="listening", anchor="nw", fill=DIM, font=theme.SMALL)
            return
        verdict = w.get("verdict") or "?"
        box.create_text(52, 1, text=verdict, anchor="nw", fill=VERDICT.get(verdict, DIM), font=theme.LABEL)
        lag = w.get("lag4")
        failed = w.get("failed") or []
        line = (f"lag4 {lag:+.2f}" if isinstance(lag, (int, float)) else "lag4 -") + "   " + (f"{len(failed)} failing" if failed else "checks ok")
        box.create_text(0, 18, text=line, anchor="nw", fill=VERDICT["noise"] if failed else DIM, font=theme.SMALL)
        x = 0
        for lane, said in sorted((w.get("lanes") or {}).items()):
            letter = (lane.strip()[:1] or "?").upper()
            item = box.create_text(x, 33, text=letter, anchor="nw", fill=VERDICT.get(said, DIM), font=theme.SMALL)
            x = box.bbox(item)[2] + 4
            if x > WATCH_W - 8:
                break

    def watch_why(self):
        """The hint over the readout: why the verdict is what it is, which checks fail, and each lane's verdict."""
        w = self.watch
        if not w:
            return "Health: the music measures itself (mindstream/watch.py) once it has played a few bars."
        lanes = ", ".join(f"{lane} {said}" for lane, said in sorted((w.get("lanes") or {}).items()))
        return (f"Health at bar {w.get('bar')}: {w.get('verdict')}" + (f" ({w['why']})" if w.get("why") else "")
                + (f". Failing: {', '.join(w['failed'])}" if w.get("failed") else f". {w.get('passed', 0)} checks pass")
                + (f". Lanes: {lanes}" if lanes else "") + ". Green healthy, amber looping, red noise.")

    def follow_watch(self, state):
        """The watch's compact report, when the viewer tells one; drawn only when it has changed."""
        w = state.get("watch")
        if isinstance(w, dict) and w != self.watch:
            self.watch = w
            self.show_watch()
            self.hints.draw()                                 # the hint, if the pointer is on the readout, says the new why

    def turn_edge(self, dial, value):
        """An edge dial turned by hand: sent with the next flush, and the dials are the hand's now."""
        self.touched["edge"] = time.time()
        self.due["~edge"] = dict(self.due.get("~edge") or {}, **{dial: round(value / 100.0, 3)})
        self.edge_whose.set("mine")
        for knob in self.edge_dial.values():
            knob.hand(True)

    def edge_lip_here(self, dial):
        """A right click on an edge dial: its lip is put where the dial stands."""
        self.touched["edge"] = time.time()
        at = round(self.edge_dial[dial].get() / 100.0, 3)
        self.edge_lips[dial] = at
        self.edge_dial[dial].tick(round(at * 100))
        self.send({"edge": {"lip": {dial: at}}})
        self.hints.say(f"{dial}'s lip is at {at * 100:.0f} now: past it the engine rations the dial")

    def edge_owner(self, whose):
        """session: the dials go back to the story; mine: they stay where they stand."""
        self.touched["edge"] = time.time()
        mine = whose == "mine"
        self.send({"edge": {dial: round(knob.get() / 100.0, 3) for dial, knob in self.edge_dial.items()} if mine else {"auto": True}})
        for knob in self.edge_dial.values():
            knob.hand(mine)

    def choose_roller(self, bars):
        """How long a riff is held, chosen by hand."""
        self.touched["roller"] = time.time()
        self.send({"roller": int(bars)})

    def follow_edge(self, state, recent):
        """The edge as the session tells it: "edge" {"lock", "derange", "auto", "lips", "past", "lane", "left"} and
        "roller" (bars). Either may be missing (an older mixer): then the panel shows what was last chosen here."""
        edge = state.get("edge")
        if isinstance(edge, dict):
            if not recent("edge"):
                lips = edge.get("lips") if isinstance(edge.get("lips"), dict) else {}
                for dial, knob in self.edge_dial.items():
                    if isinstance(edge.get(dial), (int, float)) and not knob.held:
                        knob.set(round(float(edge[dial]) * 100))
                    if isinstance(lips.get(dial), (int, float)):
                        self.edge_lips[dial] = float(lips[dial])
                        knob.tick(round(self.edge_lips[dial] * 100))
                if isinstance(edge.get("auto"), bool):
                    self.edge_whose.set("session" if edge["auto"] else "mine")
                    for knob in self.edge_dial.values():
                        knob.hand(not edge["auto"])
            past, left = edge.get("past"), edge.get("left") or 0
            if past in EDGE_DIALS:
                self.edge_said.configure(text=f"{past} past the lip on the {edge.get('lane') or 'mix'}, {left} bar{'s' if left != 1 else ''} to go", fg=HOT)
            else:
                self.edge_said.configure(text="within the lips", fg=DIM)
        roller = state.get("roller")
        if isinstance(roller, (int, float)) and not isinstance(roller, bool) and not recent("roller"):
            self.roller_choice.set(min(ROLLERS, key=lambda bars: abs(bars - roller)))

    def show_held(self):
        """What is held by hand says so: a hot dot and "held". "free" and "release" are grey while they have nothing to give back."""
        self.tempo_mark.configure(text="● held" if self.held["tempo"] else "")
        self.style_mark.configure(text="●" if self.held["style"] else "")
        self.free.configure(fg=TEXT if self.held["tempo"] else DIM)
        self.release.dim(not (self.held["tempo"] or self.held["style"] or self.mine))

    def give_back(self):
        """Everything set by hand, handed back to the story's director."""
        self.send({"release": True})
        self.held, self.mine = {"tempo": False, "style": False}, False
        self.show_held()
        self.hints.say("released: the tempo, the style and the patterns are the story's again")

    def set_tempo(self, bpm):
        self.tempo_at = int(min(max(bpm, 60), 300))
        self.tempo_label.configure(text=str(self.tempo_at))

    def nudge(self, by):
        """A step of tempo, from - or + or the wheel. It is sent a moment after the last step: every change of tempo is
        announced, so a run of steps is one change."""
        self.touched["tempo"] = time.time()
        self.set_tempo(self.tempo_at + by)
        if self.tempo_due is not None:
            self.root.after_cancel(self.tempo_due)
        self.tempo_due = self.root.after(400, self.tempo)

    def tempo_press(self, event):
        self.tempo_hand, self.tempo_last, self.tempo_exact, self.tempo_from = True, event.y_root, float(self.tempo_at), self.tempo_at

    def tempo_drag(self, event):
        if not self.tempo_hand:
            return
        up, self.tempo_last = self.tempo_last - event.y_root, event.y_root
        self.tempo_exact = min(max(self.tempo_exact + up * (0.125 if event.state & SHIFT else 0.5), 60.0), 300.0)
        self.touched["tempo"] = time.time()
        self.set_tempo(round(self.tempo_exact))

    def tempo_let_go(self, event):
        """Sent when let go: every change of tempo is announced."""
        moved, self.tempo_hand = self.tempo_hand and self.tempo_at != self.tempo_from, False
        if moved:
            self.tempo()

    def tempo(self):
        """That tempo, held until "free" lets it drift again."""
        if self.tempo_due is not None:
            self.root.after_cancel(self.tempo_due)
            self.tempo_due = None
        self.say_steer(f"!bpm {self.tempo_at}", {"bpm": float(self.tempo_at)})

    @staticmethod
    def styles():
        """Every pattern the rhythm section knows, as the engine lists them (or the usual ones, if it cannot be asked)."""
        try:
            from mindstream.groove import STYLES as known
            return tuple(known)
        except Exception:
            return STYLES

    def say_steer(self, said, direct):
        """Something for the story feed, said as if typed: it holds the tempo and the style, so that the story's director
        does not move them straight back. `direct` is the same thing for the viewer, used when there is no feed."""
        what = "tempo" if "bpm" in said else "style"
        self.touched[what] = time.time()
        self.held[what] = not said.endswith("auto")
        self.show_held()
        self.steer({"steer": said, "direct": direct})

    def steer(self, message):
        """A line for the story feed, as if typed. It is not wrapped as a message for the viewer: the launcher reads it,
        and hands it to the feed."""
        if self.send is say:
            sys.stdout.write(json.dumps(message) + "\n")
            sys.stdout.flush()
        else:
            self.send(message)

    def archetype(self, name):
        self.style.set(name)
        self.say_steer(f"!style {name}", {"style": name})

    def next_archetype(self):
        known = self.styles()
        self.archetype(known[(known.index(self.style.get()) + 1) % len(known)] if self.style.get() in known else known[0])

    # ------------------------------------------------------------------ following the session

    def stay_up(self):
        """Over a full screen viewer, the panel is put back on top every second: clicking the viewer must not bury it."""
        if self.glass[0]:
            try:
                self.root.attributes("-topmost", True)
                self.root.lift()
                if theme.Menu.open_now is not None and theme.Menu.open_now.top is not None:
                    theme.Menu.open_now.top.lift()            # a list that is down stays above the panel it came from
            except Exception:
                pass
        self.root.after(1000, self.stay_up)

    def follow(self, state):
        """How things stand in the session, as the viewer tells it: the knobs, faders and mutes go there, and a layer
        that exists gets a strip. A control a hand is on, or one moved by hand in the last few seconds, is left where
        the hand put it."""
        now = time.time()
        recent = lambda name: now - self.touched.get(name, 0.0) < 2.5      # noqa: E731
        if bool(state.get("full")) != self.glass[0]:          # over a full screen viewer the panel is an inset: where it was, no border
            self.glass = (bool(state.get("full")), state.get("screen"))
            inset(self.root, self.glass[0])
            self.set_compact(self.wants_compact and self.glass[0])       # back in a window the panel is whole
        knobs, levels = state.get("knobs") or {}, state.get("levels") or {}
        tempo = (state.get("look") or {}).get("bpm")
        if isinstance(tempo, (int, float)) and not recent("tempo") and not self.tempo_hand and round(tempo) != self.tempo_at:
            self.set_tempo(round(tempo))                        # the session's tempo, when it moves
        if state.get("lead_choice") in LEADS and not recent("lead") and state["lead_choice"] != self.lead.get():
            self.lead.set(state["lead_choice"])                 # (a memory recalled, or typed: !lead acid)
        if state.get("chop_style") in CHOPS and not recent("chop") and state["chop_style"] != self.chop.get():
            self.chop.set(state["chop_style"])                  # (a memory recalled, or typed: !chop drumfunk)
        if isinstance(state.get("style"), str) and not recent("style") and state["style"] != self.style.get():
            self.style.set(state["style"])
        if knobs:                                             # a layer that has gone from the session gives up its place
            for name in [layer for layer in self.layers if layer not in knobs]:
                self.remove(name)
        for name in knobs:
            if name not in self.knob:
                self.add(name)
        lifting = recent("*") or self.master.held             # the super knob is being turned: what the viewer says of the knobs is behind
        if isinstance(state.get("super"), (int, float)) and not lifting and round(state["super"] * 100) != self.master.get():
            self.super = float(state["super"])
            self.master.set(round(self.super * 100))
        for name, knob in self.knob.items():
            if recent(name) or knob.held or self.fader[name].held:      # the control a hand is on is the boss
                continue
            if isinstance(knobs.get(name), (int, float)) and not lifting:
                told = float(knobs[name])
                # a knob the super knob holds against an end is told as standing at that end: nothing new, and where
                # it was set is kept
                if not (told in (0.0, 1.0) and round(told * 100) == knob.get() and knob.ticked is not None):
                    self.own[name], self.was[name] = told - self.super, told
                    knob.tick(None)
                    knob.set(round(told * 100))
            if isinstance(levels.get(name), (int, float)) and abs(self.level[name] - float(levels[name])) > 0.006:
                self.level[name] = min(float(levels[name]), 1.5)
                self.fader[name].set(round(self.level[name] * 100))
        muted, waits = self.muted, self.waits
        if isinstance(state.get("muted"), list):
            muted = {name for name in self.knob if (name in self.muted if recent(name) else name in state["muted"])}
        if isinstance(state.get("in"), list):                 # the layers that are in: every other layer waits
            waits = {name for name in self.knob if name not in PARTS and name not in state["in"]}
        if (muted, waits) != (self.muted, self.waits):
            self.muted, self.waits = muted, waits
            self.show_mutes()
        self.follow_roles(state, recent)
        self.follow_edge(state, recent)
        self.follow_watch(state)

    def follow_roles(self, state, recent):
        """Each layer's role, as the session tells it: "roles" {layer: the role it has}, "role_by_hand" {layer: the role
        set by hand, or None}. Either may be missing (an older mixer): what is not told is left as it is."""
        roles, by_hand = state.get("roles"), state.get("role_by_hand")
        if not isinstance(roles, dict) and not isinstance(by_hand, dict):
            return
        for name in self.layers:
            kept = self.roles.setdefault(name, {"now": None, "hand": None})
            if isinstance(roles, dict) and roles.get(name) in ROLES:
                kept["now"] = roles[name]
            if isinstance(by_hand, dict) and name in by_hand and (by_hand[name] is None or by_hand[name] in ROLES) and not recent("role:" + name):
                kept["hand"] = by_hand[name]                    # (a memory recalled, or typed: !role rain hook)
        self.show_role()

    # ------------------------------------------------------------------ the drawer: the chosen part's own controls, and pulling a sound

    def build_drawer(self, tabs, drawer):
        """Sound design and typing, under the controls that are played: two drawers in one place."""
        tk, hint = self.tk, self.hints.on
        self.tab = {"character": theme.button(tabs, "character", lambda: self.open_drawer("character"), w=96, h=28),
                    "pull": theme.button(tabs, "pull a sound", lambda: self.open_drawer("pull"), w=112, h=28)}
        self.tab["character"].pack(side="left")
        self.tab["pull"].pack(side="left", padx=(4, 0))
        hint(self.tab["character"], "Character: the chosen part's pad, what its knob turns toward, its filter and its ducking. Press again to shut the drawer.")
        hint(self.tab["pull"], "Pull a sound: look for a sound by words and bring it in as a layer. Press again to shut the drawer.")
        self.inside = {"character": tk.Frame(drawer, bg=GROUND), "pull": tk.Frame(drawer, bg=GROUND)}
        self.build_sheet(self.inside["character"])
        self.build_pull(self.inside["pull"])
        self.drawer = None
        self.open_drawer("character")                         # the pad and the character dials are played: open from the start

    def open_drawer(self, which):
        """One drawer opened; or, if it is the one that is open, the drawer shut (the window is then that much shorter)."""
        which = None if which == self.drawer else which
        for name, frame in self.inside.items():
            frame.pack_forget()
            theme.lit(self.tab[name], name == which, TEXT)
        self.drawer = which
        if which is None:
            self.blocks["drawer"].grid_remove()
        else:
            self.inside[which].pack(anchor="nw", fill="both", expand=True)
            self.blocks["drawer"].grid()

    def build_sheet(self, sheet):
        tk, hint = self.tk, self.hints.on
        self.title = theme.heading(sheet, "")
        self.title.grid(row=0, column=0, columnspan=4, sticky="w")
        self.corner = [tk.StringVar(value=name) for name in CORNERS]
        sides = [tk.Frame(sheet, bg=GROUND, width=96, height=PAD + 2), tk.Frame(sheet, bg=GROUND, width=96, height=PAD + 2)]
        for side, column in zip(sides, (0, 2)):
            side.pack_propagate(False)
            side.grid(row=1, column=column, padx=4)
        for i, (side, where) in enumerate(((0, "bottom"), (1, "bottom"), (0, "top"), (1, "top"))):
            hint(theme.Choice(sides[side], self.corner[i], DAMAGE, command=self.read, w=92),
                 "The kind of damage in this corner of the pad.").pack(side=where, anchor="w" if side else "e")
        hint(theme.button(sides[0], "dice", self.dice, w=56, h=28), "Dice: four kinds of damage at random, one for each corner.").pack(side="top", expand=True, anchor="e")
        self.pad = tk.Canvas(sheet, width=PAD, height=PAD, bg=GROUND, highlightthickness=1, highlightbackground=LINE)
        self.pad.grid(row=1, column=1)
        self.pad.create_line(PAD / 2, PAD / 2 - 8, PAD / 2, PAD / 2 + 8, fill=LINE)       # a faint cross at its middle
        self.pad.create_line(PAD / 2 - 8, PAD / 2, PAD / 2 + 8, PAD / 2, fill=LINE)
        self.corner_names = [self.pad.create_text(x, y, text="", anchor=anchor, font=theme.SMALL, fill=DIM)
                             for x, y, anchor in ((5, PAD - 3, "sw"), (PAD - 3, PAD - 3, "se"), (5, 3, "nw"), (PAD - 3, 3, "ne"))]
        self.dot = self.pad.create_oval(0, 0, 0, 0, fill=HOT, outline="")
        self.pad.bind("<Button-1>", self.drag)
        self.pad.bind("<B1-Motion>", self.drag)
        hint(self.pad, "The pad: each corner holds one kind of damage, and the dot is the blend between them. Press or drag to move the dot.")
        right = tk.Frame(sheet, bg=GROUND)
        right.grid(row=1, column=3, padx=(28, 0), sticky="n")
        dials = tk.Frame(right, bg=GROUND)
        dials.pack(anchor="w")
        self.slider = {}
        for column, (key, label, about) in enumerate((
                ("movement", "Movement", "a ringing filter sweeping before the damage"), ("follow", "Follow", "the louder moments driven harder"),
                ("body_mix", "Body", "how much of what the result rings in"), ("cutoff", "Cutoff", "where the filter after it all cuts"),
                ("resonance", "Reso", "how much that filter rings"), ("duck", "Duck", "how far the part gives way each time the other sounds"))):
            cell = tk.Frame(dials, bg=GROUND, width=76, height=76)
            cell.pack_propagate(False)
            cell.grid(row=0, column=column)
            theme.label(cell, label).pack()
            self.slider[key] = Dial(cell, size=48, command=self.read)
            self.slider[key].pack()
            hint(self.slider[key], f"{label}: {about}. Drag up and down; Shift for fine; the wheel for single steps.")
        row = tk.Frame(right, bg=GROUND)
        row.pack(anchor="w", pady=(16, 0))
        self.body, self.under = tk.StringVar(value="none"), tk.StringVar(value="auto")
        theme.label(row, "Body").pack(side="left")
        hint(theme.Choice(row, self.body, BODIES, command=self.read, w=84), "Body: what the result rings in.").pack(side="left", padx=(6, 20))
        theme.label(row, "Filter").pack(side="left")
        self.filter = theme.Segments(row, FILTERS, command=self.read, w=48, start="off")
        self.filter.pack(side="left", padx=(6, 20))
        for kind, button in self.filter.buttons.items():
            hint(button, "No filter after the damage." if kind == "off" else f"A {kind}-pass filter after the damage, at Cutoff, ringing by Reso.")
        theme.label(row, "Ducks under").pack(side="left")
        hint(theme.Choice(row, self.under, DUCKS, command=self.read, w=84),
             "Ducks under: the part this one gives way to each time that part sounds. Auto is the kick for most parts.").pack(side="left", padx=(6, 0))
        # a layer's role in the chop, on a line of its own under the others: shown only while a layer is the chosen part (see show_role)
        self.role_row = tk.Frame(right, bg=GROUND)
        self.role, self.roles = tk.StringVar(value="auto"), {}        # roles: {layer: {"now": the role it has, "hand": the one set by hand or None}}
        theme.label(self.role_row, "Role").pack(side="left")
        self.role_choice = hint(theme.Choice(self.role_row, self.role, ("auto",) + ROLES, command=self.choose_role, w=112, says=self.role_face),
                                lambda: f"Role: the part {self.chosen} plays in the chop. auto: the engine chooses it from the sound, and keeps one anchor "
                                        "and one carrier at a time; anchor, carrier, colour, hook, stab or bed: that part, kept until auto.")
        self.role_choice.pack(side="left", padx=(6, 0))

    def build_pull(self, frame):
        tk, hint = self.tk, self.hints.on
        theme.heading(frame, "PULL A SOUND").pack(anchor="w")
        row = tk.Frame(frame, bg=GROUND)
        row.pack(anchor="w", pady=(8, 0))
        self.wanted = theme.Words(row, width=44, hint="words for a sound: rain on a tin roof")
        self.wanted.pack(side="left", ipady=4)
        self.wanted.bind("<Return>", lambda event: self.pull())
        self.where = tk.StringVar(value="anywhere")
        hint(theme.Choice(row, self.where, PLACES, w=164, says=lambda value: "from " + value), "Where to look: anywhere is your Splice library first, then the free archives.").pack(side="left", padx=8)
        self.called = theme.Words(row, width=18, hint="its name (optional)")
        self.called.pack(side="left", ipady=4)
        self.called.bind("<Return>", lambda event: self.pull())
        hint(theme.button(row, "PULL", self.pull, w=72, h=28), "Pull: look for the words and bring what is found in as a layer that waits.").pack(side="left", padx=(8, 0))
        hint(self.wanted, "Words for a sound: \"rain on a tin roof\", \"amen break\". kick, snare, hat or vocal make it that drum, or what the tune plays on. Enter pulls.")
        hint(self.called, "The name the layer is given (optional).")
        theme.note(frame, "What is found comes in as a layer that waits, with a knob of its own: shuffle it to bring it in.\n"
                   "A search of an archive sends the words to that service.", justify="left").pack(anchor="w", pady=(10, 0))

    def pull(self):
        """A sound asked for by its box: found in the Splice library or a free archive, fetched into memory, and made a
        layer that waits (or the kick, snare or hats, or what the tune plays on, if that is what the words ask for)."""
        words = " ".join(self.wanted.get().split())
        if not words:
            return
        place, name = self.where.get(), "".join(c for c in self.called.get().lower() if c.isalnum())[:16]
        said = "!pull " + words + ("" if place == "anywhere" else f" from {place}") + (f" as {name}" if name else "")
        want = pull_in(said)
        if want is None:
            self.hints.say("that is not something to look for")
            return
        self.hints.say(f'looking for "{want["query"]}"' + (f', as the {want["role"]}' if want["role"] in ("kick", "snare", "hats", "tune")
                                                             else f', to be the layer "{want["name"]}"'), 12.0)
        self.steer({"steer": said, "pull": want})             # for the story feed; the launcher pulls it itself if there is no feed
        self.wanted.empty()
        self.called.empty()

    def choose(self, name):
        """A part chosen: the pad and the character dials are that part's from here."""
        if name not in self.sheets:
            return
        self.chosen = name
        self.show_mutes()
        self.title.configure(text=f"{name.upper()} CHARACTER: what its knob turns toward (the knob is the drive)")
        self.show()
        self.show_role()

    def role_face(self, value):
        """The role menu's face: on auto, the role the engine has given the layer, when the session has said."""
        now = self.roles.get(self.chosen, {}).get("now")
        return f"auto: {now}" if value == "auto" and now else str(value)

    def show_role(self):
        """The role menu, there for a layer and not for the eight parts, and showing the chosen layer's role. Nothing is sent."""
        if self.chosen in PARTS or self.chosen not in self.knob:
            self.role_row.pack_forget()
            return
        if not self.role_row.winfo_manager():
            self.role_row.pack(anchor="w", pady=(8, 0))
        wanted = self.roles.get(self.chosen, {}).get("hand") or "auto"
        if self.role.get() != wanted:
            self.role.set(wanted)
        else:
            self.role_choice.face()                           # the role the engine gave may have changed under "auto"

    def choose_role(self, value):
        """The chosen layer's role, set by hand; "auto" gives it back to the engine."""
        if self.chosen in PARTS or self.chosen not in self.knob:
            return
        hand = None if value == "auto" else value
        self.roles.setdefault(self.chosen, {"now": None, "hand": None})["hand"] = hand
        self.touched["role:" + self.chosen] = time.time()
        self.send({"role": {"layer": self.chosen, "role": hand}})

    def show(self):
        """The pad, the dials and the menus put where the chosen part's stand. Nothing is sent."""
        sheet = self.sheets[self.chosen]
        for var, item, name in zip(self.corner, self.corner_names, sheet["corners"]):
            var.set(name)
            self.pad.itemconfigure(item, text=name)
        self.body.set(sheet["body"])
        self.filter.set(sheet["filter"])
        self.under.set(sheet["duck_by"])
        for key, slider in self.slider.items():
            slider.set(round(sheet[key] * 100))
        px, py = sheet["x"] * PAD, (1 - sheet["y"]) * PAD
        self.pad.coords(self.dot, px - 8, py - 8, px + 8, py + 8)

    def drag(self, event):
        sheet = self.sheets[self.chosen]
        sheet["x"], sheet["y"] = min(max(event.x / PAD, 0.0), 1.0), 1.0 - min(max(event.y / PAD, 0.0), 1.0)
        self.changed.setdefault(self.chosen, set()).add("patch")
        self.by_hand()
        self.show()

    def dice(self):
        for var, name in zip(self.corner, random.sample(DAMAGE, 4)):
            var.set(name)
        self.read()

    def read(self, *_):
        """Something on the sheet was moved by hand: take it as the chosen part's, and note what kind of change it was."""
        sheet = self.sheets[self.chosen]
        now = {"corners": [var.get() for var in self.corner], "body": self.body.get(), "filter": self.filter.get(), "duck_by": self.under.get(),
               **{key: slider.get() / 100.0 for key, slider in self.slider.items()}}
        kinds = set()
        for key, value in now.items():
            if sheet[key] != value:
                sheet[key] = value
                kinds.add("filter" if key in ("filter", "cutoff", "resonance") else "duck" if key in ("duck_by", "duck") else "patch")
        if kinds:
            self.changed.setdefault(self.chosen, set()).update(kinds)
            self.by_hand()
            for item, name in zip(self.corner_names, sheet["corners"]):
                self.pad.itemconfigure(item, text=name)

    # ------------------------------------------------------------------ the timeline

    def build_line(self, block):
        """The timeline's rows are drawn on one canvas, so that the row that is playing can be lit as a whole."""
        tk, hint = self.tk, self.hints.on
        self.line_head = theme.heading(block, "TIMELINE")
        self.line_head.pack(anchor="w")
        hint(self.line_head, "Timeline: drag a memory here (or right click it) to add it to the end. Each row is held for its bars, then left for the next in its own way.")
        self.line = tk.Canvas(block, width=LINE_W - 2, height=ROWS * ROW, bg=GROUND, highlightthickness=1, highlightbackground=LINE, bd=0)
        self.line.pack(pady=(4, 0))
        self.line.bind("<Button-1>", self.line_click)
        self.line.bind("<Motion>", self.line_hint)
        self.line.bind("<Leave>", lambda event: self.hints.point(None))
        self.line.bind("<MouseWheel>", lambda event: self.line_scroll(-1 if event.delta > 0 else 1))
        self.how_menu = theme.Menu(block)
        for how in HOWS:
            self.how_menu.add_command(label=how, command=lambda how=how: self.line_how(self.how_for, how))
        row = tk.Frame(block, bg=GROUND)                      # play and stop: in line with the tempo, not at a far corner
        row.pack(side="bottom", anchor="w")
        self.play_button = hint(theme.button(row, "PLAY", self.line_play, w=72, h=36), "Play the timeline: the first row starts on the next bar line. Amber until it does.")
        self.play_button.pack(side="left")
        hint(theme.button(row, "STOP", self.line_stop, w=72, h=36), "Stop the timeline: the music stays where it is.").pack(side="left", padx=4)
        self.looping = False
        self.loop_button = hint(theme.button(row, "loop", self.loop, w=60, h=36), "Loop: after the last row, the first again. Lit while it is on.")
        self.loop_button.pack(side="left")
        self.line_frame, self.entries, self.carried, self.lit, self.line_top, self.line_wait, self.how_for = block, [], None, -1, 0, False, None
        self.draw_line()

    def loop(self):
        self.looping = not self.looping
        theme.lit(self.loop_button, self.looping)

    def carry_memory(self, slot):
        """A memory's slot is being dragged: the timeline, where it can be dropped, is outlined."""
        if self.carried != slot and slot in self.numbers:
            self.carried = slot
            self.root.configure(cursor="hand2")
            self.line.configure(highlightbackground=HOT)

    def drop_memory(self, event, slot):
        """... and let go: if that was over the timeline, the memory joins the end of it."""
        if self.carried != slot:
            return
        self.carried = None
        self.root.configure(cursor="")
        self.line.configure(highlightbackground=LINE)
        under = self.root.winfo_containing(event.x_root, event.y_root)
        if under is not None and str(under).startswith(str(self.line_frame)):
            self.line_add(slot)

    def line_add(self, slot, bars=8, how="smooth"):
        """A row at the end of the timeline: the memory, how many bars it is held, and how it is left for the next."""
        if slot not in self.numbers:
            return
        if len(self.entries) >= 12:
            self.hints.say("timeline full: 12 rows")
            return
        entry = {"slot": slot, "bars": int(bars), "how": how}
        self.entries.append(entry)
        self.wear(entry)
        self.line_top = max(self.line_top, len(self.entries) - ROWS)      # the new row is in view
        self.draw_line()

    def wear(self, entry):
        """A row wears its memory's small picture, half size, once there is one."""
        picture = self.thumbs.get(entry["slot"])
        if picture is not None:
            try:
                entry["small"] = picture.subsample(2)
            except Exception:
                pass

    def draw_line(self):
        """Every row in view, drawn: the memory, its bars as three segments with the chosen one light, how it is left,
        and the x that takes it away. The row that is playing is filled warm with a hot bar at its left; after PLAY
        and before the first arrival, the first row is outlined amber."""
        line = self.line
        line.delete("all")
        self.line_top = min(max(self.line_top, 0), max(len(self.entries) - ROWS, 0))
        for at, entry in enumerate(self.entries[self.line_top:self.line_top + ROWS]):
            index, y = self.line_top + at, at * ROW
            if index == self.lit:
                line.create_rectangle(0, y, LINE_W, y + ROW - 2, fill=WARM, outline="")
                line.create_rectangle(0, y, 4, y + ROW - 2, fill=HOT, outline="")
            elif self.line_wait and index == 0:
                line.create_rectangle(1, y + 1, LINE_W - 3, y + ROW - 3, outline=WAIT)
            if entry.get("small") is not None:
                line.create_image(24, y + 17, image=entry["small"])
            else:
                line.create_rectangle(8, y + 1, 40, y + 33, fill=FACE, outline=LINE)
            line.create_text(25, y + 18, text=str(entry["slot"]), font=theme.VALUE, fill=GROUND)
            line.create_text(24, y + 17, text=str(entry["slot"]), font=theme.VALUE, fill=TEXT)
            for place, bars in enumerate(BARS):
                x, chosen = 46 + place * 28, entry["bars"] == bars
                line.create_rectangle(x, y + 3, x + 28, y + 31, fill=TEXT if chosen else FACE, outline=LINE)
                line.create_text(x + 14, y + 17, text=str(bars), font=theme.LABEL, fill=GROUND if chosen else TEXT)
            line.create_rectangle(134, y + 3, 208, y + 31, fill=FACE, outline=LINE)
            line.create_text(138, y + 17, text=entry["how"] + theme.DOWN, anchor="w", font=theme.SMALL, fill=TEXT)
            line.create_text(226, y + 17, text="x", font=theme.LABEL, fill=DIM)
        count = len(self.entries)
        if not count:
            line.create_text(LINE_W // 2, 28, text="drag a memory here", font=theme.SMALL, fill=DIM)
        self.line_head.configure(text="TIMELINE" + (f"   {self.line_top + 1}-{min(self.line_top + ROWS, count)} of {count}: the wheel for the rest" if count > ROWS else ""))

    def line_zone(self, event):
        """What of the timeline is under the pointer: (its row, which part of the row), or (None, None)."""
        index = self.line_top + int(event.y) // ROW
        if not 0 <= index < len(self.entries) or event.y < 0:
            return None, None
        x = event.x
        what = "memory" if x < 44 else BARS[min(int(x - 46) // 28, 2)] if 46 <= x < 130 else "how" if 134 <= x < 210 else "remove" if x >= 216 else None
        return self.entries[index], what

    def line_click(self, event):
        entry, what = self.line_zone(event)
        if entry is None:
            return
        if what in BARS:
            entry["bars"] = what
            self.draw_line()
        elif what == "how":                                   # the list of ways to leave a row, where it was pressed
            self.how_for = entry
            self.how_menu.tk_popup(event.x_root, event.y_root)
        elif what == "remove":
            self.line_remove(entry)

    def line_how(self, entry, how):
        if entry in self.entries:
            entry["how"] = how
            self.draw_line()

    def line_hint(self, event):
        entry, what = self.line_zone(event)
        self.hints.point(None if entry is None else
                         f"Held for {what} bars." if what in BARS else
                         "How this row is left for the next: smooth (a bar at a time), drop (drums and bass away for the last bar) or breakdown (for the second half). Press for the list."
                         if what == "how" else "Take this row off the timeline." if what == "remove" else
                         f"Memory {entry['slot']}, held for {entry['bars']} bars, then left for the next: {entry['how']}.")

    def line_scroll(self, by):
        self.line_top += by
        self.draw_line()

    def line_remove(self, entry):
        self.entries.remove(entry)
        self.lit = -1
        self.draw_line()

    def line_play(self):
        if not self.entries:
            self.hints.say("the timeline is empty: drag a memory onto it")
            return
        self.lit, self.line_wait = -1, True                   # waiting for the bar line, until the first memory arrives
        theme.lit(self.play_button, True, WAIT)
        self.draw_line()
        self.send({"timeline": [{"slot": e["slot"], "bars": int(e["bars"]), "how": e["how"]} for e in self.entries], "loop": bool(self.looping)})

    def line_stop(self):
        self.send({"timeline": []})
        self.line_wait = False
        theme.lit(self.play_button, False)
        self.light(-1)

    def light(self, index):
        """The row that is playing is lit as a whole, and kept in view."""
        self.lit = index
        if index >= 0:
            self.line_top = min(max(self.line_top, index - ROWS + 1), index)
        self.draw_line()

    def arrived(self, slot):
        """The timeline has gone to a memory: its row is lit, and the knobs show that memory."""
        order = list(range(self.lit + 1, len(self.entries))) + list(range(0, self.lit + 1))
        self.line_wait = False
        theme.lit(self.play_button, False)
        self.light(next((i for i in order if self.entries[i]["slot"] == slot), -1))
        self.display(slot)
        self.live = (slot, False)
        self.show_memories()

    # ------------------------------------------------------------------ sending

    def flush(self):
        """What has been moved since last time goes out, a few times a second: each change rebuilds that part's sounds."""
        due, self.due = self.due, {}
        changed, self.changed = self.changed, {}
        lifted, fade, edge = due.pop("*", None), due.pop("fade", None), due.pop("~edge", None)
        if edge:
            self.send({"edge": edge})
        if fade is not None:
            self.send({"crossfade": {"a": fade[0], "b": fade[1], "at": fade[2]}})
        ops = [{"part": name, "set": {"filth": round(value, 3)}} for name, value in due.items()]     # by hand first: set against the super knob as it stood
        for name, kinds in changed.items():
            if "patch" in kinds:
                ops.append({"part": name, "patch": patch_of(self.sheets[name])})
            if "filter" in kinds:
                ops.append(filter_of(name, self.sheets[name]))
            if "duck" in kinds:
                ops.append(duck_of(name, self.sheets[name]))
            if "level" in kinds:
                ops.append({"part": name, "set": {"level": round(self.level[name], 3)}})
        if ops:
            self.send({"patch": ops})
        if lifted is not None:
            self.send({"super": lifted})
        self.root.after(150, self.flush)


def main():
    import tkinter as tk
    root = tk.Tk()
    root.attributes("-topmost", True)                         # it floats over the viewer, full screen or not
    keep_typing(root)
    panel = Panel(root, tk)
    heard = queue.Queue()

    def listen():
        for raw in sys.stdin:
            try:
                message = json.loads(raw)
            except ValueError:
                continue
            if isinstance(message, dict) and (message.get("layer") or "thumb" in message or "arrived" in message or "state" in message):
                heard.put(message)

    def take():
        """What has come from the viewer, acted on. Of how things stand only the newest counts (several may have
        queued while the panel was busy); a message that cannot be acted on is passed over, and this always comes
        round again."""
        try:
            latest = None
            while not heard.empty():
                message = heard.get()
                if isinstance(message.get("state"), dict):
                    latest = message["state"]
                    continue
                try:
                    if message.get("layer"):
                        panel.add("".join(c for c in str(message["layer"]).lower() if c.isalnum())[:16])
                    elif isinstance(message.get("thumb"), int) and isinstance(message.get("png"), str):
                        panel.picture(message["thumb"], message["png"])
                    elif isinstance(message.get("arrived"), int):
                        panel.arrived(message["arrived"])
                except Exception:
                    pass
            if latest is not None:
                try:
                    panel.follow(latest)
                except Exception as e:
                    panel.hints.say(f"could not follow the session ({type(e).__name__})")
        finally:
            root.after(300, take)

    if "--try" not in sys.argv:
        threading.Thread(target=listen, daemon=True).start()
    root.after(300, take)
    root.mainloop()


if __name__ == "__main__":
    main()
