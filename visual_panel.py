"""The visuals panel: the look of the screen, the effects on it, and every picture and film of the session, to put
back on screen.

Started by the launcher with --visuals, or opened and closed from the viewer with Ctrl+V; it stays on top of the
viewer; when the viewer is full screen it stays where it was left, without its border and see-through, as an inset.
The window has one size: nothing that arrives changes it. The line at its foot says what the control under the
pointer does, and what has just happened. The strip across its top moves the window when dragged (an inset has no
title bar to drag). While the panel is an inset, "small" on that strip leaves only NOW, the effects (which can be shut), five dials of the look
(Chaos, Folds, Spin, Zoom, Trails) with hold flat and flash, and OBJECT; "full" brings the rest back as it was. Its
top left corner stays where it is. Back in a window the panel is whole again, and the next time the viewer goes
full screen it takes the form it had there last.

On the left, LOOK: nine dials in three rows: time (Chaos, how wild the motion is; Rest, how long the picture rests
flat; Move, how long it then moves), space (Folds, Spin, Zoom) and layers (Trails, the Swarm of earlier pictures, the
colour Split). A dial is dragged up and down from anywhere on its face (Shift for a quarter of the speed), turned a
step at a time with the wheel, and put back where it started with a double click. The dials follow the session: when
the story's director moves the look, they move; one a hand is on is not moved under it. A dial you set is never put
back: from then on the director's moves are added to where you left it, so the look still drifts with the story but
from your setting; it wears a hot dot from then on. Under the dials are the shape and the tint: one you choose
stays, and the one in force is marked. HOLD FLAT keeps the picture still and whole (lit while it does); FLASH is a
flash. "release", at the bottom behind a divider, gives everything back to the director; it has to be pressed and
held.

In the middle, EFFECTS: a dial for each effect on the picture, from the list in mindstream/effects.py (the viewer
holds the effects themselves). They are sent, held and followed exactly as the look's dials are, and "release"
gives them back with the rest. The switch above them (screen / images, also in the small form) chooses what they show
and set: the effects over the whole screen, or those on each picture by itself ("image:bloom"); the effects that work
on the whole screen only are greyed while they show the pictures'.

On the right, from the top:

NOW shows what is on screen and sounding at this moment, in four places that do not move: the picture showing, the
film on the reel, the sounds that are in, and the swarm of earlier pictures. What does not fit is a count ("+6");
press it for the rest. To take a film, a sound or a swarm picture out of play, drag it out of the box, press the x
that shows at its corner under the pointer, or right click it. (The picture showing stays: there is always one.)

One box for words, with PICTURE and FILM: a picture of those words in the present scene is painted next (Enter does
the same); a film is made from those words alone, as long as the menu beside it says: a bar unless you choose
otherwise, three seconds at most (with no words, a film between the latest two pictures). The box is outlined in
amber until what was asked for arrives.

PLAY LINK takes a video's web address or its embed code, pasted into the box or dragged onto the panel from a
browser: the viewer fetches a few seconds of it (from the time in the "from" box, for as long as the menu says) and
plays them as a film. Use it for videos that are yours to use.

OBJECT puts an object with sides in place of the one surface: a card (two sides), a prism (three) or a cube (six).
Each side has a box: drag a picture or a film from the shelf onto it (or right click it on the shelf) and that side
shows it (a film goes round and round, without its sound). Several on one side fade from each to the next in time
with the beat, a pulse between them, as often as the menu says. A side with nothing on it shows whatever is live. A
click on a small picture in a side's box takes it off; "empty" clears every side; "none" is the one surface again.

SHELF is the palette: a small picture of everything that has been played, in the order it came. A film has a violet
corner, a sound (each sample pulled in and each film's sound) a green one and shows its shape and name; what is in
play is outlined. "all", "pictures", "films" and "sounds" narrow it. Double click one, drag it into NOW or right out
of this window toward the viewer, or right click it, and it is in play again: a picture arrives as a new picture
does, a film starts on the next bar line, a sound comes back as its layer on the next bar. The wheel moves the
shelf; it follows new arrivals only while it is showing its end, and otherwise says how many are new.

Files dragged onto this panel from a folder are taken in as if dropped on the viewer: pictures, video files, moving
pictures and sounds.

What it says goes out on stdout, one JSON object per line, as messages for the viewer:
    {"type": "visual", "seq": -1, "hold": true, "chaos": 1.4}           (an effect is sent the same way: "bloom": 0.6; on each picture "image:bloom": 0.6)
    {"type": "visual", "seq": -1, "hold": true, "shape": "torus"}       (or "tint": "#ff4020")
    {"type": "visual", "seq": -1, "release": true}
    {"type": "visual", "seq": -1, "flat": true}       {"type": "visual", "seq": -1, "flash": 1.0}
    {"type": "visual", "seq": -1, "show": 12}         number 12 off the shelf, into play
    {"type": "visual", "seq": -1, "unshow": 12}       ... and out of play again
    {"type": "visual", "seq": -1, "object": {"kind": "cube", "sides": [[3, 7], [], [12], [], [], []], "every": 1.0}}    (or null)
    {"type": "visual", "seq": -1, "drop": ["C:/.../a.png"]}      files dragged onto this panel from outside, for the viewer to read
    {"type": "visual", "seq": -1, "link": {"url": "https://...", "start": "1:30", "seconds": 4.0}}      a video at an address
    {"steer": "!pic a fox in the snow"}               for the story feed, as if typed: a picture now ("!sample ..." a film now)
What it hears on stdin, from the viewer: {"shelf": 12, "kind": "picture" or "film", "png": "<base64>"} when something new
goes on the shelf, and {"shelf_gone": 3} when an old one is let go.

    visual_panel.py --try        the panel alone, with a few stand-in pictures (nothing is listening)
"""
import json
import re
import time
import queue
import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mindstream import theme  # noqa: E402
from mindstream.outbox import Outbox  # noqa: E402
from mindstream.dial import Dial  # noqa: E402
from mindstream.inset import inset, keep_typing, moved  # noqa: E402
from mindstream.solid import MOST, SIDES, refit  # noqa: E402
from mindstream.theme import DIM, FACE, FILM, GROUND, HOT, LINE, SOUND, TEXT, WAIT  # noqa: E402

try:                                                          # the effects on the picture: only their list is needed here
    from mindstream.effects import EFFECTS, IMAGE  # noqa: E402
except ImportError:
    EFFECTS, IMAGE = (), ()
AIMS = ("screen", "images")                                   # what the effects' dials show and set: the whole screen, or each picture

# setting: (name on the panel, lowest, highest, where it starts, step, its unit), in three rows: time, space, layers
LOOK = (("chaos", "Chaos", 0.0, 2.0, 1.0, 0.05, ""), ("calm", "Rest", 1.0, 10.0, 3.5, 0.5, "s"), ("wild", "Move", 3.0, 30.0, 9.0, 1.0, "s"),
        ("folds", "Folds", 0.0, 9.0, 0.0, 1.0, ""), ("spin", "Spin", 0.0, 3.0, 1.0, 0.05, ""), ("zoom", "Zoom", -1.0, 1.0, 0.7, 0.05, ""),
        ("trails", "Trails", 0.0, 1.0, 0.75, 0.05, ""), ("swarm", "Swarm", 0.0, 1.0, 0.8, 0.05, ""), ("split", "Split", 0.0, 2.0, 1.0, 0.05, ""))
HINTS = {"chaos": "how wild the motion is", "calm": "how long the picture rests flat, in seconds", "wild": "how long it then moves, in seconds",
         "folds": "how many times the picture is folded", "trails": "how long what has moved leaves a trail", "swarm": "how much of the swarm of earlier pictures shows",
         "split": "how far the colours are pulled apart on the beat", "spin": "how fast it turns", "zoom": "in, or out"}
SHAPES = ("any", "sphere", "torus", "ribbon")
LENGTHS = ("1 bar", "2 beats", "4 beats", "1 s", "1.5 s", "2 s", "3 s")      # how long "film now" makes its film
TINTS = (("none", "#ffffff"), ("red", "#ff4020"), ("amber", "#ffb030"), ("green", "#40ff80"), ("blue", "#4080ff"), ("violet", "#b050ff"), ("cold", "#c0e0ff"))
PULSES = {"1/2 beat": 0.5, "1 beat": 1.0, "2 beats": 2.0, "4 beats": 4.0, "8 beats": 8.0}     # from one thing on a side to the next
QUICK = ("chaos", "folds", "spin", "zoom", "trails")       # the dials of the look that the small form of an inset keeps
KINDS = {"all": None, "pictures": "picture", "films": "film", "sounds": "sound"}                 # what the shelf can be narrowed to

# sizes, in pixels: the window is built from blocks of fixed size, so nothing that arrives can change it
LEFT, MIDDLE, RIGHT, HIGH = 260, 252, 484, 634       # the look, the effects, the right-hand column; how high they all are
CELL = (84, 88)                                      # a dial with its name
FX_CELL, FX_ACROSS = (60, 72), 8                     # in the small form the effects sit closer: eight across
ALL_CELL, ALL_ACROSS = (63, 76), 4                   # and in the full form four across, so that thirty-odd fit the column (32 at most: eight rows)
FX_HIGH = 26 + FX_CELL[1] * -(-len(EFFECTS) // FX_ACROSS)
FX_KEYS = frozenset(row[0] for row in EFFECTS)
ACROSS, DOWN, PITCH = 7, 4, 68                       # the shelf: seven across, four rows in view, a small picture every 68
# NOW: for each kind of thing in play, where its place starts, how big its small pictures are, how many fit, and
# whether they can be taken out of play
NOW = (("showing", "picture", 4, 64, 1, False), ("film", "film", 76, 64, 1, True), ("sounds", "sounds", 152, 48, 2, True), ("swarm", "swarm", 296, 48, 3, True))


OUT = []                                           # the outbox for what is said, made the first time something is


def say(message):
    """A line for the launcher. Queued (mindstream/outbox.py): the panel never waits on a busy launcher."""
    if not OUT:
        OUT.append(Outbox(sys.stdout.write, sys.stdout.flush, name="to launcher"))
    OUT[0].put(json.dumps({"type": "visual", "seq": -1, **message}) + "\n")


class Panel:
    def __init__(self, root, tk, send=say):
        self.root, self.tk, self.send = root, tk, send
        self.value, self.due, self.items, self.carried, self.flat, self.touched, self.glass = {}, {}, {}, None, False, {}, (False, None)
        # mine: the settings held by hand (as far as this panel knows: since it opened). making: the kinds of thing
        # asked for with PICTURE or FILM that have not arrived yet.
        self.mine, self.making, self.playing, self.smalls = set(), set(), {}, {}
        # compact: whether the panel is in its small form (only as an inset); wants_compact: which form was last chosen
        # for full screen
        self.compact, self.wants_compact = False, False
        # fx_aim: which target the effects' dials show and set ("screen", or "images": each picture by itself, kept as
        # "image:<effect>"); aim_choices: the two switches for it (full form and small form); limits: each setting's range
        self.fx_aim, self.aim_choices, self.limits = "screen", [], {}
        root.title("Visuals")
        root.configure(padx=12, pady=12, bg=GROUND)
        root.resizable(False, False)
        bar = theme.hint_bar(root)                            # the hint bar, across the foot of the panel
        self.hints = theme.Hints(bar)
        self.blocks = {}                                      # the blocks the window is made of, by name
        for name, wide, high in (("look", LEFT, HIGH), ("effects", MIDDLE, HIGH), ("now", RIGHT, 120), ("words", RIGHT, 62), ("object", RIGHT, 112),
                                 ("shelf", RIGHT, 316), ("quick", RIGHT, CELL[1]), ("fx", RIGHT, FX_HIGH)):
            self.blocks[name] = tk.Frame(root, bg=GROUND, width=wide, height=high)
            self.blocks[name].pack_propagate(False)
            self.blocks[name].grid_propagate(False)
        self.blocks["look"].grid(row=1, column=0, rowspan=4, sticky="nw")
        self.blocks["effects"].grid(row=1, column=1, rowspan=4, sticky="nw", padx=(12, 0))
        for row, name in enumerate(("now", "words", "object", "shelf"), 1):
            self.blocks[name].grid(row=row, column=2, sticky="nw", padx=(12, 0), pady=(0 if row == 1 else 8, 0))
        bar.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        self.blocks["hint"] = bar
        self.slider = {}
        self.build_title("VISUALS")
        self.build_look(self.blocks["look"])
        self.build_quick(self.blocks["quick"])
        self.build_effects(self.blocks["effects"])
        self.build_fx(self.blocks["fx"])
        self.build_now(self.blocks["now"])
        self.build_words(self.blocks["words"])
        self.build_object(self.blocks["object"])
        self.build_shelf(self.blocks["shelf"])
        root.after(120, self.flush)
        root.after(1000, self.stay_up)

    # ------------------------------------------------------------------ the look

    def dial(self, parent, key, label, low, high, start, step, unit, about, centre=False, cell=CELL, fx=False):
        """One setting of the look, or one effect: its name over a dial. It is sent as it is turned, and follows the session.
        An effect's dial (fx) sets the screen's effect or each picture's, as the switch above the effects says."""
        cell = self.tk.Frame(parent, bg=GROUND, width=cell[0], height=cell[1])
        cell.pack_propagate(False)
        theme.label(cell, label).pack()
        self.value[key], self.limits[key] = start, (low, high)
        if fx and key in IMAGE:
            self.value["image:" + key], self.limits["image:" + key] = start, (low, high)
        made = Dial(cell, size=48, low=low, high=high, start=start, step=step, centre=centre, font=theme.LABEL,
                    says=lambda value, unit=unit: f"{value:g}{unit}",
                    command=(lambda value, key=key: self.turn(self.aimed(key), value)) if fx else (lambda value, key=key: self.turn(key, value)))
        made.pack()
        self.hints.on(made, f"{label}: {about}. Drag up and down; Shift for fine; the wheel for single steps; double click for where it started. "
                            "Set by hand it is yours: the story's moves are then added to where you left it.")
        self.slider.setdefault(key, []).append(made)
        return cell

    def build_look(self, look):
        tk, hint = self.tk, self.hints.on
        theme.heading(look, "LOOK").pack(anchor="w")
        dials = tk.Frame(look, bg=GROUND)
        dials.pack(anchor="w")
        for at, (key, label, low, high, start, step, unit) in enumerate(LOOK):
            self.dial(dials, key, label, low, high, start, step, unit, HINTS[key], centre=low < 0).grid(row=at // 3, column=at % 3)
        theme.heading(look, "SHAPE").pack(anchor="w", pady=(8, 0))
        self.shape, self.tint, self.tint_buttons = None, None, {}
        self.shapes = theme.Segments(look, SHAPES, command=self.choose_shape, w=62, h=28)
        self.shapes.pack(anchor="w", pady=(2, 0))
        for shape, button in self.shapes.buttons.items():
            hint(button, "Shape: " + ("whichever the story chooses." if shape == "any" else f"the picture wraps a {shape}, and stays so.") + " The one in force is lit.")
        theme.heading(look, "TINT").pack(anchor="w", pady=(8, 0))
        tints = tk.Frame(look, bg=GROUND)
        tints.pack(anchor="w", pady=(2, 0))
        for name, colour in TINTS:                            # a swatch is its tint: the one button that is not dark
            swatch = theme.button(tints, "", lambda colour=colour: self.choose_tint(colour), w=26, h=26)
            swatch.configure(bg=colour, activebackground=colour, highlightthickness=3, highlightbackground=GROUND)
            swatch.pack(side="left", padx=(0, 4))
            self.tint_buttons[colour] = swatch
            hint(swatch, f"Tint: {name}. It stays until \"release\". The one in force has a light ring.")
        acts = tk.Frame(look, bg=GROUND)
        acts.pack(anchor="w", pady=(16, 0))
        self.flat_buttons = [theme.button(acts, "HOLD FLAT", self.hold_flat, w=112, h=40)]
        hint(self.flat_buttons[0], "Hold flat: the picture kept still and whole, until pressed again. Lit while it holds.").pack(side="left", padx=(0, 8))
        hint(theme.button(acts, "FLASH", lambda: self.send({"flash": 1.0}), w=112, h=40), "Flash: one flash, now.").pack(side="left")
        foot = tk.Frame(look, bg=GROUND)                      # what cannot be undone stands apart, behind a divider
        foot.pack(side="bottom", fill="x")
        tk.Frame(foot, bg=LINE, height=1).pack(fill="x", pady=(0, 8))
        self.release = theme.HoldButton(foot, "release", self.give_back, w=80, h=28)
        hint(self.release, "Release: press and hold. Everything set by hand here (the look, the effects, the shape, the tint) goes back to the story's director.").pack(side="right")
        self.release.dim(True)

    def build_quick(self, block):
        """For the small form of an inset: the dials of the look that are played most, and hold flat and flash. They
        are the same settings as the dials of the full form, and move with them."""
        for at, (key, label, low, high, start, step, unit) in enumerate(row for row in LOOK if row[0] in QUICK):
            self.dial(block, key, label, low, high, start, step, unit, HINTS[key], centre=low < 0).pack(side="left")
        acts = self.tk.Frame(block, bg=GROUND)
        acts.pack(side="right", anchor="n")
        self.flat_buttons.append(self.hints.on(theme.button(acts, "FLAT", self.hold_flat, w=60, h=40), "Hold flat: the picture kept still and whole, until pressed again. Lit while it holds."))
        self.flat_buttons[-1].pack()
        self.hints.on(theme.button(acts, "FLASH", lambda: self.send({"flash": 1.0}), w=60, h=40), "Flash: one flash, now.").pack(pady=(4, 0))

    def arrange(self):
        """The blocks put out for the form the panel is in. Small: what is in play, a few dials of the look with hold
        flat and flash, and the object; the rest of the look, the effects, the boxes for words and links and the shelf
        are put away. Nothing is lost: what is put away keeps its state and comes back with the full form."""
        for name in ("look", "effects", "words", "shelf"):
            self.blocks[name].grid_remove() if self.compact else self.blocks[name].grid()
        if self.compact:
            self.blocks["quick"].grid(row=2, column=2, sticky="nw", pady=(8, 0))
            self.blocks["fx"].grid(row=4, column=2, sticky="nw", pady=(8, 0))
        else:
            self.blocks["quick"].grid_remove()
            self.blocks["fx"].grid_remove()
        for name in ("now", "object"):
            self.blocks[name].grid_configure(padx=(0 if self.compact else 12, 0))

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

    def build_effects(self, block):
        """A dial for each effect on the picture, made from the list the viewer and the story feed read too, under a
        switch for what they set: the whole screen, or each picture by itself."""
        top = self.tk.Frame(block, bg=GROUND)
        top.pack(anchor="w", fill="x")
        theme.heading(top, "EFFECTS").pack(side="left")
        self.aim_switch(top).pack(side="right")
        dials = self.tk.Frame(block, bg=GROUND)
        dials.pack(anchor="w")
        for at, (key, label, low, high, start, step, about) in enumerate(EFFECTS):
            self.dial(dials, key, label, low, high, start, step, "", about, centre=low < 0, cell=ALL_CELL, fx=True).grid(row=at // ALL_ACROSS, column=at % ALL_ACROSS)

    def aim_switch(self, parent):
        """The switch over the effects: whether their dials show and set the screen's effects or each picture's."""
        made = theme.Segments(parent, AIMS, command=self.choose_aim, w=56, h=22, start=self.fx_aim, font=theme.SMALL)
        for aim, button in made.buttons.items():
            self.hints.on(button, "The effects' dials set the whole finished screen." if aim == "screen" else
                          "The effects' dials set each picture by itself, before it is placed (on the surface, the object's sides, the swarm). "
                          "Greyed ones work on the whole screen only.")
        self.aim_choices.append(made)
        return made

    def aimed(self, key):
        """The setting an effect's dial stands for now: the screen's effect, or the pictures' ("image:<effect>")."""
        return "image:" + key if self.fx_aim == "images" and key in FX_KEYS else key

    def dials_of(self, key):
        """The dials showing a setting just now (an effect's dials show the screen's or the pictures', not both)."""
        if key.startswith("image:"):
            return self.slider.get(key[len("image:"):], []) if self.fx_aim == "images" else []
        if self.fx_aim == "images" and key in FX_KEYS:
            return []
        return self.slider.get(key, [])

    def choose_aim(self, aim):
        """The switch turned: the effects' dials go to where that target's settings stand and wear its hot dots, and
        the effects that work on the whole screen only are greyed while the dials show the pictures'."""
        if aim not in AIMS:
            return
        self.fx_aim = aim
        for made in self.aim_choices:
            made.set(aim)
        for key in FX_KEYS:
            for dial in self.slider.get(key, []):
                dial.dim(aim == "images" and key not in IMAGE)
                dial.set(self.value.get(self.aimed(key), 0.0) if key in IMAGE or aim == "screen" else 0.0)
        self.show_mine()
        self.hints.say("the effects' dials now set " + ("each picture by itself" if aim == "images" else "the whole screen"))

    def build_fx(self, block):
        """For the small form of an inset: the effects again, as a block that can be shut. They are the same settings as
        the dials of the full form, and move with them."""
        top = self.tk.Frame(block, bg=GROUND)
        top.pack(anchor="w", fill="x")
        theme.heading(top, "EFFECTS").pack(side="left")
        self.fx_open = True
        self.fx_button = theme.button(top, "hide", self.toggle_fx, w=56, h=22, font=theme.SMALL)
        self.hints.on(self.fx_button, "Shut or open the effects in the small form. Shut, they keep working: they are only put away.").pack(side="right")
        self.aim_switch(top).pack(side="right", padx=(0, 8))
        self.fx_dials = self.tk.Frame(block, bg=GROUND)
        self.fx_dials.pack(anchor="w")
        for at, (key, label, low, high, start, step, about) in enumerate(EFFECTS):
            self.dial(self.fx_dials, key, label, low, high, start, step, "", about, centre=low < 0, cell=FX_CELL, fx=True).grid(row=at // FX_ACROSS, column=at % FX_ACROSS)

    def toggle_fx(self):
        self.fx_open = not self.fx_open
        self.fx_button.configure(text="hide" if self.fx_open else "show")
        self.blocks["fx"].configure(height=FX_HIGH if self.fx_open else 26)
        at = getattr(self.root, "_inset_at", None)
        if at is not None and self.glass[0]:                  # its top left corner stays where it is
            self.root.update_idletasks()
            self.root.geometry(f"+{at[0]}+{at[1]}")

    def give_back(self):
        """Everything set by hand, handed back to the story's director."""
        self.send({"release": True})
        self.mine = set()
        self.show_mine()
        self.hints.say("released: the look is the story's again")

    def show_mine(self):
        """A setting held by hand wears a hot dot; "release" is grey while there is nothing to give back."""
        for key, dials in self.slider.items():
            for dial in dials:
                dial.hand(self.aimed(key) in self.mine)
        self.release.dim(not self.mine)

    def choose_shape(self, shape):
        """A shape chosen by hand: it stays, and its button is lit at once."""
        self.touched["shape"] = time.time()
        self.send({"hold": True, "shape": shape})
        self.mine.add("shape")
        self.show_mine()
        self.show_shape(shape)

    def choose_tint(self, colour):
        self.touched["tint"] = time.time()
        self.send({"hold": True, "tint": colour})
        self.mine.add("tint")
        self.show_mine()
        self.show_tint(colour)

    def show_shape(self, shape):
        """The shape in force is the one lit."""
        if shape in SHAPES:
            self.shape = shape
            self.shapes.set(shape)

    def show_tint(self, colour):
        """The tint in force is the swatch with a light ring. The viewer tells it as it has it, which can be a step off
        the swatch's own colour, so the nearest swatch within a few steps is the one."""
        try:
            now = [int(colour[i:i + 2], 16) for i in (1, 3, 5)]
        except (TypeError, ValueError):
            return
        near = {swatch: max(abs(int(swatch[i:i + 2], 16) - c) for i, c in zip((1, 3, 5), now)) for swatch in self.tint_buttons}
        chosen = min(near, key=near.get) if near and min(near.values()) <= 3 else None
        if chosen != self.tint:
            self.tint = chosen
            for swatch, button in self.tint_buttons.items():
                button.configure(highlightbackground=TEXT if swatch == chosen else GROUND)

    def turn(self, key, value):
        """A dial turned by hand (a dial says so only then). On the pictures' target, an effect that works on the whole
        screen only is not sent: its dial goes back to nothing, and the hint bar says why."""
        if key not in self.value:
            plain = key[len("image:"):]
            for dial in self.slider.get(plain, []):
                dial.set(0.0)
            self.hints.say(f"{plain} works on the whole screen only")
            return
        if abs(self.value[key] - value) < 1e-6:
            return
        self.touched[key] = time.time()
        self.value[key] = value
        self.due[key] = value
        for dial in self.dials_of(key):                       # the same setting shown elsewhere goes with it
            dial.set(value)
        if key not in self.mine:
            self.mine.add(key)
            self.show_mine()

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
        """How the look stands in the session: the dials go there, except one a hand is on or one moved by hand in the
        last few seconds. A setting the state does not mention is left alone."""
        now = time.time()
        if bool(state.get("full")) != self.glass[0]:          # over a full screen viewer the panel is an inset: where it was, no border
            self.glass = (bool(state.get("full")), state.get("screen"))
            inset(self.root, self.glass[0])
            self.set_compact(self.wants_compact and self.glass[0])       # back in a window the panel is whole
        for key, value in (state.get("look") or {}).items():
            if key not in self.limits or isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            dials = self.dials_of(key)                        # (an effect's other target is followed too, out of sight)
            if now - self.touched.get(key, 0.0) > 2.5 and not any(dial.held for dial in dials):
                low, high = self.limits[key]
                value = min(max(float(value), low), high)
                if abs(self.value[key] - value) > 1e-6:
                    self.value[key] = value
                    for dial in dials:
                        dial.set(value)
        if isinstance(state.get("shape"), str) and now - self.touched.get("shape", 0.0) > 2.5:
            self.show_shape(state["shape"])
        if isinstance(state.get("tint"), str) and now - self.touched.get("tint", 0.0) > 2.5:
            self.show_tint(state["tint"])
        if isinstance(state.get("live"), dict):
            self.show_live(state["live"])
        if "object" in state and state["object"] != self.object_said() and now - self.object_at > 2.5:
            theirs = state["object"]                          # the object as the viewer has it (a memory recalled, a new theme)
            if isinstance(theirs, dict) and theirs.get("kind") in SIDES:
                self.object = {"kind": theirs["kind"], "sides": [list(side) for side in theirs.get("sides", [])], "every": theirs.get("every", 1.0)}
                self.every.set(next((label for label, beats in PULSES.items() if beats == self.object["every"]), "1 beat"))
            else:
                self.object["kind"] = None
            self.draw_object()
        if isinstance(state.get("flat"), bool) and state["flat"] != self.flat:
            self.flat = state["flat"]
            for button in self.flat_buttons:
                theme.lit(button, self.flat)

    def hold_flat(self):
        self.flat = not self.flat
        for button in self.flat_buttons:
            theme.lit(button, self.flat)
        self.send({"flat": self.flat})

    def flush(self):
        """What has been moved since last time goes out, a few times a second, marked as held."""
        due, self.due = self.due, {}
        if due:
            self.send({"hold": True, **{key: round(value, 3) for key, value in due.items()}})
        self.root.after(120, self.flush)

    # ------------------------------------------------------------------ in play now

    def build_now(self, block):
        """What is on screen and sounding, drawn on one canvas in four places that do not move."""
        tk = self.tk
        head = theme.heading(block, "NOW")
        head.pack(anchor="w")
        self.hints.on(head, "Now: what is on screen and sounding. Drag anything from the shelf here, or out of this window, to put it in play.")
        self.now = tk.Canvas(block, width=RIGHT - 2, height=92, bg=GROUND, highlightthickness=1, highlightbackground=LINE, bd=0)
        self.now.pack(pady=(4, 0))
        self.now_hits, self.now_down, self.now_over = [], None, None
        self.now.bind("<ButtonPress-1>", self.now_press)
        self.now.bind("<B1-Motion>", lambda event: self.carry(-self.now_down[4]) if self.now_down and self.now_down[5] else None)
        self.now.bind("<ButtonRelease-1>", self.now_let_go)
        self.now.bind("<Button-3>", self.now_menu_at)
        self.now.bind("<Motion>", self.now_point)
        self.now.bind("<Leave>", lambda event: self.now_point(None))
        self.now_menu = theme.Menu(block)
        self.live_frame = self.now                            # where something carried from the shelf is dropped to go into play
        self.draw_now()

    def small(self, number):
        """A thing's picture at three quarters of its size, for the places in NOW that hold several."""
        if number not in self.smalls:
            self.smalls[number] = self.items[number].zoom(3).subsample(4)
        return self.smalls[number]

    def draw_now(self):
        """The four places: the picture showing, the film on the reel, the sounds that are in, the swarm. What does not
        fit in its place is a count, which opens the rest."""
        now = self.now
        now.delete("all")
        self.now_hits = []                                    # (left, top, right, bottom, number or the rest, whether it can be taken out)
        for title, key, left, size, room, removable in NOW:
            numbers = self.playing.get(key)
            numbers = [n for n in (numbers if isinstance(numbers, list) else [numbers]) if n in self.items]
            now.create_text(left, 2, text=title, anchor="nw", font=theme.SMALL, fill=DIM)
            top = 22 + (64 - size) // 2
            for place in range(room):
                x = left + place * (size + 4)
                if place < len(numbers):
                    now.create_image(x, top, image=self.items[numbers[place]] if size == 64 else self.small(numbers[place]), anchor="nw")
                    self.now_hits.append((x, top, x + size, top + size, numbers[place], removable))
                else:
                    now.create_rectangle(x, top, x + size - 1, top + size - 1, outline=FACE)
            if len(numbers) > room:
                x = left + room * (size + 4)
                now.create_rectangle(x, top, x + 30, top + size - 1, fill=FACE, outline=LINE)
                now.create_text(x + 15, top + size // 2, text=f"+{len(numbers) - room}", font=theme.LABEL, fill=TEXT)
                self.now_hits.append((x, top, x + 30, top + size, numbers[room:], False))
        self.now_over = None

    def now_at(self, event):
        """What of NOW is under the pointer, as one of the hits above; or None."""
        return next((hit for hit in self.now_hits if hit[0] <= event.x < hit[2] and hit[1] <= event.y < hit[3]), None)

    def now_point(self, event):
        """The pointer over something that can be taken out shows an x at its corner."""
        hit = self.now_at(event) if event is not None else None
        if hit == self.now_over:
            return
        self.now_over = hit
        self.now.delete("x")
        if hit is None:
            self.hints.point(None)
        elif isinstance(hit[4], list):
            self.hints.point(f"{len(hit[4])} more in play: press for the list, and choose one to take it out of play.")
        elif hit[5]:
            self.now.create_rectangle(hit[2] - 16, hit[1], hit[2], hit[1] + 16, fill=GROUND, outline=LINE, tags="x")
            self.now.create_text(hit[2] - 8, hit[1] + 7, text="x", font=theme.LABEL, fill=TEXT, tags="x")
            self.hints.point("In play. To take it out: press the x, drag it out of this box, or right click.")
        else:
            self.hints.point("The picture showing. It stays: there is always a picture.")

    def now_press(self, event):
        self.now_down = self.now_at(event)
        if self.now_down is not None and isinstance(self.now_down[4], list):      # the count: the rest, as a list
            self.rest_menu(self.now_down[4])
            self.now_down = None
            self.now_menu.tk_popup(event.x_root, event.y_root)

    def rest_menu(self, numbers):
        """The things in play that did not fit in their place, as a list: choosing one takes it out of play."""
        self.now_menu.delete(0, "end")
        for number in numbers:
            self.now_menu.add_command(image=self.small(number), label=" take out of play", compound="left", command=lambda number=number: self.send({"unshow": number}))

    def now_let_go(self, event):
        """Let go in NOW: after a drag out of the box the thing is out of play; a press on its x does the same."""
        down, self.now_down = self.now_down, None
        if down is None or not down[5]:
            return
        if self.carried == -down[4]:
            self.lift(event, down[4])
        elif event.x >= down[2] - 16 and event.y < down[1] + 16 and self.now_at(event) == down:
            self.send({"unshow": down[4]})

    def now_menu_at(self, event):
        hit = self.now_at(event)
        if hit is not None and hit[5]:
            self.rest_menu([hit[4]])
            self.now_menu.tk_popup(event.x_root, event.y_root)

    def show_live(self, live):
        """What is in play right now, as the viewer tells it, drawn from the small pictures the shelf already has."""
        if live == self.playing:
            return
        self.playing = live
        self.draw_now()
        self.draw_shelf()

    def in_play(self):
        """The numbers of everything that is in play."""
        live = self.playing
        return {n for n in [live.get("picture"), live.get("film")] + list(live.get("sounds") or []) + list(live.get("swarm") or []) if n is not None}

    # ------------------------------------------------------------------ words for a picture or a film, and a link

    def build_words(self, block):
        tk, hint = self.tk, self.hints.on
        row = tk.Frame(block, bg=GROUND, width=RIGHT, height=28)
        row.pack_propagate(False)
        row.pack()
        self.length = tk.StringVar(value="1 bar")
        hint(theme.Choice(row, self.length, LENGTHS, w=92), "How long FILM makes its film: a bar unless you choose beats or seconds.").pack(side="right")
        hint(theme.button(row, "FILM", lambda: self.make("sample"), w=60, h=28),
             "Film: a film from those words alone, as long as the menu says; with no words, a film between the latest two pictures.").pack(side="right", padx=4)
        hint(theme.button(row, "PICTURE", lambda: self.make("pic"), w=80, h=28), "Picture: those words painted in the present scene, next.").pack(side="right", padx=(4, 0))
        self.words = theme.Words(row, hint="words for a picture or a film")
        self.words.pack(side="left", fill="both", expand=True)
        self.words.bind("<Return>", lambda event: self.make("pic"))
        hint(self.words, "Words for a picture or a film. Enter makes a picture.")
        row = tk.Frame(block, bg=GROUND, width=RIGHT, height=28)
        row.pack_propagate(False)
        row.pack(pady=(6, 0))
        hint(theme.button(row, "PLAY LINK", self.play_link, w=92, h=28), "Play link: a few seconds of the video at that address, as a film.").pack(side="right")
        self.span = tk.StringVar(value="4 s")
        hint(theme.Choice(row, self.span, ("1 s", "2 s", "4 s", "8 s"), w=60), "How many seconds of the video are played.").pack(side="right", padx=4)
        self.begin = theme.Words(row, width=9, hint="from 0:00")
        self.begin.pack(side="right", fill="y", padx=(4, 0))
        self.begin.bind("<Return>", lambda event: self.play_link())
        self.address = theme.Words(row, hint="a video's address or embed code")
        self.address.pack(side="left", fill="both", expand=True)
        self.address.bind("<Return>", lambda event: self.play_link())
        hint(self.address, "A video's web address or its embed code, pasted here or dragged onto the panel from a browser. Enter plays it. For videos that are yours to use.")
        hint(self.begin, "Where in the video to start: seconds, or 1:30.")

    def make(self, key):
        """A picture or a film asked for now, from the words in the box: said to the story feed as if typed."""
        words = " ".join(self.words.get().split())
        if key == "sample":
            amount, unit = self.length.get().split()
            if words:                                          # a film from the words alone: "!sample 2s a dancer"
                said = f"!sample {amount}{'s' if unit == 's' else ' ' + unit} {words}" if self.length.get() != "1 bar" else f"!sample {words}"
            else:                                              # no words: between the latest two pictures, "!film 2" or "!film 4 beats"
                said = f"!film {amount}" + ("" if unit == "s" else " " + unit + ("s" if not unit.endswith("s") else ""))
        else:
            said = f"!pic {words}".strip()
        self.send({"steer": said})
        self.words.empty()
        self.wait_for("film" if key == "sample" else "picture", words)

    def wait_for(self, kind, words=""):
        """Something has been asked for: the box is outlined in amber until the next thing of that kind arrives."""
        self.making.add(kind)
        self.words.configure(highlightbackground=WAIT)
        self.hints.say(f"a {kind} is being made" + (f': "{words}"' if words else ""), 12.0)
        self.root.after(120000, lambda: self.arrived(kind))   # and if it never arrives, the amber goes after a while

    def arrived(self, kind):
        self.making.discard(kind)
        if not self.making:
            self.words.configure(highlightbackground=LINE)

    def play_link(self, address=None):
        """A video at a web address (a link, or an embed code): the viewer fetches a few seconds of it, from the time in
        the "from" box (seconds, or 1:30), and plays them as a film."""
        address = " ".join(str(address if address is not None else self.address.get()).split())
        if not address:
            return
        self.send({"link": {"url": address, "start": self.begin.get().strip() or "0", "seconds": float(self.span.get().split()[0])}})
        self.address.empty()
        self.hints.say("fetching a few seconds of that video")

    def dropped(self, things):
        """What is dragged onto the panel from outside: files, which the viewer reads, shows and puts on the shelf; or
        a link or an embed code, of which it plays a few seconds."""
        things = [str(thing) for thing in things]
        links = [thing for thing in things if re.match(r"\s*(?:https?://|<iframe|<embed)", thing, re.I)]
        paths = [thing for thing in things if thing not in links][:12]
        for link in links[:3]:
            self.play_link(link)
        if paths:
            self.send({"drop": paths})

    # ------------------------------------------------------------------ the object

    def build_object(self, block):
        """An object with sides in place of the one surface: which object, and a box for each of its sides. A picture or
        a film dragged from the shelf onto a box goes on that side; a click on it there takes it off."""
        tk, hint = self.tk, self.hints.on
        self.object, self.object_at, self.kinds, self.thirds, self.side_boxes = {"kind": None, "sides": [], "every": 1.0}, 0.0, {}, {}, []
        row = tk.Frame(block, bg=GROUND)
        row.pack(anchor="w", fill="x")
        hint(theme.heading(row, "OBJECT"), "Object: sides in place of the one surface. Drag pictures and films from the shelf onto a side; several on one side pulse between them."
             ).pack(side="left", padx=(0, 8))
        self.kind_choice = theme.Segments(row, ("none",) + tuple(SIDES), command=lambda kind: self.choose_object(None if kind == "none" else kind), w=52, start="none")
        self.kind_choice.pack(side="left")
        for kind, button in self.kind_choice.buttons.items():
            hint(button, "None: the one surface again." if kind == "none" else f"A {kind}: {len(SIDES[kind])} sides. What is on the sides is kept, side for side.")
        hint(theme.button(row, "empty", self.empty_object, w=56, h=28), "Empty: every side cleared; each then shows whatever is live.").pack(side="right")
        self.every = tk.StringVar(value="1 beat")
        hint(theme.Choice(row, self.every, PULSES, command=self.pulse_every, w=116, says=lambda value: "every " + value),
             "How often a side with several things goes from one to the next.").pack(side="right", padx=4)
        self.sides_row = tk.Frame(block, bg=GROUND, width=RIGHT, height=76)
        self.sides_row.pack(anchor="w", fill="x", pady=(6, 0))
        self.sides_row.pack_propagate(False)
        self.draw_object()

    def object_said(self):
        """The object as it is told to the viewer (None: no object)."""
        if not self.object["kind"]:
            return None
        return {"kind": self.object["kind"], "sides": [list(side) for side in self.object["sides"]], "every": self.object["every"]}

    def say_object(self):
        self.object_at = time.time()
        self.send({"object": self.object_said()})
        self.draw_object()

    def choose_object(self, kind):
        """Another kind of object (or none: the one surface again). What is on its sides is kept, side for side."""
        if kind:
            self.object["sides"] = refit(self.object["sides"], kind)
        self.object["kind"] = kind
        self.say_object()

    def pulse_every(self, chosen):
        self.object["every"] = PULSES.get(chosen, 1.0)
        if self.object["kind"]:
            self.say_object()

    def empty_object(self):
        self.object["sides"] = [[] for _ in self.object["sides"]]
        self.say_object() if self.object["kind"] else self.draw_object()

    def put_on(self, at, number):
        """A picture or a film from the shelf onto a side. A side with several pulses between them."""
        side = self.object["sides"][at]
        if self.kinds.get(number) not in ("picture", "film") or number in side or len(side) >= MOST:
            if len(side) >= MOST:
                self.hints.say(f"that side is full: {MOST} at most")
            return
        side.append(number)
        self.say_object()

    def take_off(self, at, number):
        if number in self.object["sides"][at]:
            self.object["sides"][at].remove(number)
            self.say_object()

    def draw_object(self):
        """The boxes for the sides, each with small pictures of what is on it."""
        tk = self.tk
        self.kind_choice.set(self.object["kind"] or "none")
        for child in self.sides_row.winfo_children():
            child.destroy()
        self.side_boxes = []
        if not self.object["kind"]:
            theme.note(self.sides_row, "choose an object, then drag pictures and films from the shelf onto its sides;\n"
                       "several on one side pulse between them, and an empty side shows what is live", justify="left").pack(anchor="w")
            return
        for at, name in enumerate(SIDES[self.object["kind"]]):
            box = tk.Frame(self.sides_row, bg=FACE, width=76, height=76, highlightthickness=1, highlightbackground=LINE)
            box.pack(side="left", padx=(0, 4))
            box.pack_propagate(False)
            self.hints.on(theme.note(box, name, bg=FACE), f"The {name} side: drag a picture or a film from the shelf onto it. Empty, it shows whatever is live.").pack(anchor="w")
            held = tk.Frame(box, bg=FACE)
            held.pack(anchor="w")
            for place, number in enumerate(n for n in self.object["sides"][at] if n in self.items):
                if number not in self.thirds:
                    self.thirds[number] = self.items[number].subsample(3)
                thumb = tk.Label(held, image=self.thirds[number], bd=0, bg=FACE, cursor="hand2")
                thumb.grid(row=place // 3, column=place % 3, padx=1, pady=1)
                thumb.bind("<Button-1>", lambda event, at=at, number=number: self.take_off(at, number))      # a click takes it off
                self.hints.on(thumb, f"On the {name} side. Click to take it off.")
            self.side_boxes.append(box)

    # ------------------------------------------------------------------ the shelf

    def build_shelf(self, block):
        """Everything this session, drawn on one canvas: seven across, four rows in view, the rest reached with the wheel."""
        tk, hint = self.tk, self.hints.on
        row = tk.Frame(block, bg=GROUND, width=RIGHT, height=28)
        row.pack_propagate(False)
        row.pack()
        hint(theme.heading(row, "SHELF"), "The shelf: everything played this session, in the order it came. A film has a violet corner, a sound a green one; what is in play is outlined."
             ).pack(side="left", padx=(0, 8))
        self.only = theme.Segments(row, tuple(KINDS), command=lambda kind: self.narrow(), w=68, h=28, start="all")
        self.only.pack(side="left")
        for kind, button in self.only.buttons.items():
            hint(button, "The whole shelf." if kind == "all" else f"Only the {kind}.")
        self.fresh, self.top_row, self.shelf_down = 0, 0, None
        self.new_button = hint(theme.button(row, "", self.to_end, w=76, h=28), "New things have arrived while the shelf was scrolled back: press to go to them.")
        self.shelf = tk.Canvas(block, width=RIGHT - 2, height=DOWN * PITCH + 2, bg=GROUND, highlightthickness=1, highlightbackground=LINE, bd=0)
        self.shelf.pack(pady=(6, 0))
        self.shelf.bind("<ButtonPress-1>", self.shelf_press)
        self.shelf.bind("<B1-Motion>", lambda event: self.carry(self.shelf_down) if self.shelf_down is not None else None)
        self.shelf.bind("<ButtonRelease-1>", self.shelf_let_go)
        self.shelf.bind("<Double-Button-1>", lambda event: self.show(self.shelf_at(event)) if self.shelf_at(event) is not None else None)
        self.shelf.bind("<Button-3>", self.shelf_menu_at)
        self.shelf.bind("<MouseWheel>", lambda event: self.scroll(-1 if event.delta > 0 else 1))      # only with the pointer on the shelf
        self.shelf.bind("<Motion>", self.shelf_point)
        self.shelf.bind("<Leave>", lambda event: self.hints.point(None))
        self.shelf_menu = theme.Menu(block)
        self.draw_shelf()

    def listed(self):
        """The numbers on the shelf that are in view of the filter, in the order they came."""
        kind = KINDS[self.only.get()]
        return [number for number in self.items if kind is None or self.kinds.get(number) == kind]

    def last_row(self):
        """The top row when the shelf is showing its end."""
        return max(-(-len(self.listed()) // ACROSS) - DOWN, 0)

    def draw_shelf(self):
        """The small pictures in view. A film has a violet corner and a sound a green one; what is in play has a hot
        outline. At the right edge a thin bar shows where in the shelf this is."""
        shelf, listed = self.shelf, self.listed()
        shelf.delete("all")
        self.top_row = min(max(self.top_row, 0), self.last_row())
        live = self.in_play()
        for at, number in enumerate(listed[self.top_row * ACROSS:(self.top_row + DOWN) * ACROSS]):
            x, y = 2 + (at % ACROSS) * PITCH, 2 + (at // ACROSS) * PITCH
            shelf.create_image(x, y, image=self.items[number], anchor="nw")
            colour = {"film": FILM, "sound": SOUND}.get(self.kinds.get(number))
            if colour:
                shelf.create_polygon(x, y, x + 16, y, x, y + 16, fill=colour, outline="")
            if number in live:
                shelf.create_rectangle(x + 1, y + 1, x + 62, y + 62, outline=HOT, width=3)
        rows = -(-len(listed) // ACROSS)
        bar_left, high = RIGHT - 9, DOWN * PITCH
        shelf.create_rectangle(bar_left, 2, bar_left + 5, high, fill=FACE, outline="")
        if rows > DOWN:
            shelf.create_rectangle(bar_left, 2 + high * self.top_row / rows, bar_left + 5, high * (self.top_row + DOWN) / rows, fill=DIM, outline="")
        if self.top_row >= self.last_row():
            self.fresh = 0
        if self.fresh:
            self.new_button.configure(text=f"{self.fresh} new" + theme.DOWN)
            self.new_button.pack(side="right")
        else:
            self.new_button.pack_forget()

    def shelf_at(self, event):
        """The number of the thing under the pointer, or None."""
        column, row = int(event.x - 2) // PITCH, int(event.y - 2) // PITCH
        if not (0 <= column < ACROSS and 0 <= row < DOWN) or event.x < 2 or event.y < 2:
            return None
        listed, at = self.listed(), (self.top_row + row) * ACROSS + column
        return listed[at] if at < len(listed) else None

    def shelf_point(self, event):
        number = self.shelf_at(event)
        kind = self.kinds.get(number)
        self.hints.point(None if number is None else
                         f"A {kind}" + (", in play" if number in self.in_play() else "") + ". Double click, drag to NOW or out of this window, or right click, to put it in play"
                         + (". Drag it onto a side of the object to show it there." if kind != "sound" else "."))

    def shelf_press(self, event):
        self.shelf_down = self.shelf_at(event)
        if event.x >= RIGHT - 12:                             # a press on the bar at the edge goes to that part of the shelf
            self.top_row = round(self.last_row() * event.y / (DOWN * PITCH))
            self.draw_shelf()

    def shelf_let_go(self, event):
        down, self.shelf_down = self.shelf_down, None
        if down is not None and self.carried == down:
            self.drop(event, down)

    def shelf_menu_at(self, event):
        number = self.shelf_at(event)
        if number is not None:
            self.fill_shelf_menu(number)
            self.shelf_menu.tk_popup(event.x_root, event.y_root)

    def fill_shelf_menu(self, number):
        """What a right click offers for one thing on the shelf: into play, out of play, or onto a side of the object."""
        menu = self.shelf_menu
        menu.delete(0, "end")
        menu.add_command(label="put in play", command=lambda: self.show(number))
        if number in self.in_play() and number != self.playing.get("picture"):
            menu.add_command(label="take out of play", command=lambda: self.send({"unshow": number}))
        if self.object["kind"] and self.kinds.get(number) in ("picture", "film"):
            for at, name in enumerate(SIDES[self.object["kind"]]):
                menu.add_command(label=f"onto the {name} side of the {self.object['kind']}", command=lambda at=at: self.put_on(at, number))

    def scroll(self, by):
        self.top_row += by
        self.draw_shelf()

    def to_end(self):
        self.top_row = self.last_row()
        self.draw_shelf()

    def narrow(self):
        """The shelf narrowed to one kind of thing, or widened again: shown from its end."""
        self.fresh = 0
        self.to_end()

    def add(self, number, kind, png):
        """Something new on the shelf: a small picture of it at the end. The shelf goes to it if it was showing its end
        already; looking back at older things, it stays where it is and says how many are new."""
        if number in self.items:
            return
        try:
            picture = self.tk.PhotoImage(data=png)
        except Exception:
            return
        at_end = self.top_row >= self.last_row()
        self.items[number] = picture                         # the picture is kept here: tk forgets one nobody else holds
        self.kinds[number] = kind
        if kind in self.making:                               # what was asked for with PICTURE or FILM has arrived
            self.arrived(kind)
        if at_end:
            self.top_row = self.last_row()
        elif KINDS[self.only.get()] in (None, kind):
            self.fresh += 1
        self.draw_shelf()
        self.draw_now()

    def gone(self, number):
        """An old one let go from the shelf."""
        if number in self.items:
            self.items.pop(number)
            self.kinds.pop(number, None)
            self.smalls.pop(number, None)
            self.thirds.pop(number, None)
            self.draw_shelf()
            self.draw_now()
            if any(number in side for side in self.object["sides"]):      # it leaves the object's sides too (the viewer has done the same)
                self.object["sides"] = [[n for n in side if n != number] for side in self.object["sides"]]
                self.draw_object()

    def carry(self, number):
        """Something is being dragged: off the shelf (its number), or out of NOW (its number, negative). While a thing
        from the shelf is carried, NOW, where it can be dropped, is outlined."""
        if self.carried != number:
            self.carried = number
            self.root.configure(cursor="hand2")
            if number > 0:
                self.now.configure(highlightbackground=HOT)

    def drop(self, event, number):
        """Let go after a drag from the shelf: onto a side of the object it goes on that side; onto NOW, or anywhere
        outside this window, it goes into play."""
        if self.carried != number:
            return
        self.carried = None
        self.root.configure(cursor="")
        self.now.configure(highlightbackground=LINE)
        under = self.root.winfo_containing(event.x_root, event.y_root)
        for at, box in enumerate(self.side_boxes):            # onto a side of the object: it goes on that side
            if under is not None and (str(under) == str(box) or str(under).startswith(str(box) + ".")):
                self.put_on(at, number)
                return
        if under is None or str(under).startswith(str(self.live_frame)):
            self.show(number)

    def lift(self, event, number):
        """Let go after dragging something from NOW: anywhere outside that box, it is taken out of play."""
        if self.carried != -number:
            return
        self.carried = None
        self.root.configure(cursor="")
        under = self.root.winfo_containing(event.x_root, event.y_root)
        if under is None or not str(under).startswith(str(self.live_frame)):
            self.send({"unshow": number})

    def show(self, number):
        self.send({"show": number})


def main():
    import tkinter as tk
    try:                                                      # with this, files can be dragged onto the panel from outside
        from tkinterdnd2 import DND_FILES, DND_TEXT, TkinterDnD
        root = TkinterDnD.Tk()
    except Exception:
        DND_FILES, root = None, tk.Tk()
    root.attributes("-topmost", True)                         # it floats over the viewer, full screen or not
    keep_typing(root)
    panel = Panel(root, tk)
    if DND_FILES is not None:
        try:
            root.drop_target_register(DND_FILES, DND_TEXT)
            # files come as a list of paths; a link dragged from a browser, or an embed code, comes as one piece of text
            root.dnd_bind("<<Drop>>", lambda event: panel.dropped([event.data] if re.match(r"\s*(?:https?://|<)", event.data or "", re.I)
                                                                  else root.tk.splitlist(event.data)))
        except Exception:
            pass
    heard = queue.Queue()

    def listen():
        for raw in sys.stdin:
            try:
                message = json.loads(raw)
            except ValueError:
                continue
            if isinstance(message, dict):
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
                    if isinstance(message.get("shelf"), int) and isinstance(message.get("png"), str):
                        panel.add(message["shelf"], str(message.get("kind", "picture")), message["png"])
                    elif isinstance(message.get("shelf_gone"), int):
                        panel.gone(message["shelf_gone"])
                except Exception:
                    pass
            if latest is not None:
                try:
                    panel.follow(latest)
                except Exception as e:
                    panel.hints.say(f"could not follow the session ({type(e).__name__})")
        finally:
            root.after(200, take)

    if "--try" in sys.argv:                                   # a few stand-ins, to see the panel on its own
        import base64
        import io
        from PIL import Image
        for number in range(1, 15):
            out = io.BytesIO()
            Image.new("RGB", (64, 64), (number * 17 % 255, number * 53 % 255, number * 91 % 255)).save(out, "PNG")
            heard.put({"shelf": number, "kind": "film" if number % 5 == 0 else "picture", "png": base64.b64encode(out.getvalue()).decode("ascii")})
    else:
        threading.Thread(target=listen, daemon=True).start()
    root.after(200, take)
    root.mainloop()


if __name__ == "__main__":
    main()
