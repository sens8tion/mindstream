"""The two controls the panels are played with, drawn on a canvas: a dial, and its straight sibling a fader.

A stock slider can only be grabbed by its thumb, steps when its trough is clicked, and reports a move the panel made
in the same way as one a hand made. These do neither:

- the whole face is the target. A dial is dragged up and down from anywhere on it (Shift for a quarter of the
  speed), turned a step at a time with the wheel, and put back where it started with a double click. A fader goes
  where it is clicked and follows the drag.
- `set(value)` is the panel's way of moving one, and it never calls back; `command(value)` is called only for a
  move made by hand. And a control a hand is on (`held`) is not moved under that hand: `set` leaves it alone.

A dial also carries its state: the number in a fixed place, a hot dot when it is held by hand against the story, a
grey tick for where it was set when something else has pushed it away, and a dimmed look when its part is muted.
Nothing here needs anything but tkinter.
"""
import math
import tkinter as tk

from mindstream.theme import DIM, GROUND, HOT, LINE, SMALL, SOUND, TEXT, VALUE

SHIFT = 0x0001


class Dial(tk.Canvas):
    """A dial `size` pixels square. `low` to `high` in steps of `step`; `start` is where a double click puts it back.
    `says(value)` gives the words in its middle. `centre`: a setting with two sides (zoom), drawn from the top.
    `sweep` is how many pixels of drag cross its whole range. `caption`: a small grey word under the number."""

    def __init__(self, parent, size=56, low=0.0, high=100.0, start=0.0, step=1.0, command=None, says=None, centre=False, font=VALUE,
                 thick=5, sweep=200, bg=GROUND, caption=""):
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0, takefocus=0)
        self.size, self.low, self.high, self.start, self.step, self.command = size, float(low), float(high), float(start), float(step), command
        self.says, self.centre, self.sweep = says or (lambda value: f"{value:g}"), centre, float(sweep)
        self.value, self.exact, self.held, self.last = self.fit(start), float(start), False, 0
        self.ticked, self.dimmed, self.by_hand = None, False, False
        edge = thick / 2 + 2
        self.box = (edge, edge, size - edge, size - edge)
        self.track = self.create_arc(*self.box, start=-45, extent=270, style="arc", width=thick, outline=LINE)
        self.arc = self.create_arc(*self.box, start=225, extent=-1, style="arc", width=thick, outline=TEXT)
        self.tick_line = self.create_line(0, 0, 0, 0, fill=DIM, width=2, state="hidden")
        self.number = self.create_text(size / 2, size / 2 - (8 if caption else 0), text="", font=font, fill=TEXT)
        if caption:
            self.create_text(size / 2, size / 2 + 16, text=caption, font=SMALL, fill=DIM)
        self.dot = self.create_oval(size - 8, size - 8, size - 2, size - 2, fill=HOT, outline="", state="hidden")
        self.bind("<ButtonPress-1>", self.press)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonRelease-1>", self.let_go)
        self.bind("<Double-Button-1>", self.home)
        self.bind("<MouseWheel>", self.wheel)
        self.draw()

    # ------------------------------------------------------------------ where it stands

    def fit(self, value):
        """A value brought inside the dial's range and onto one of its steps."""
        value = min(max(float(value), self.low), self.high)
        return round(self.low + round((value - self.low) / self.step) * self.step, 6)

    def share(self, value):
        return (value - self.low) / (self.high - self.low) if self.high > self.low else 0.0

    def get(self):
        return self.value

    def set(self, value):
        """Put there by the panel: following the session, a memory, the super knob. It does not call back, and it does
        not move a dial a hand is on."""
        if self.held:
            return
        value = self.fit(value)
        if value != self.value:
            self.value = self.exact = value
            self.draw()

    def draw(self):
        share = self.share(self.value)
        extent = -(share - 0.5) * 270 if self.centre else -share * 270
        if abs(extent) < 1.0:                                 # tk draws nothing sensible for an arc of no length
            self.itemconfigure(self.arc, state="hidden")
        else:
            self.itemconfigure(self.arc, state="normal", start=90 if self.centre else 225, extent=extent,
                               outline=DIM if self.dimmed else TEXT)
        self.itemconfigure(self.number, text=self.says(self.value), fill=DIM if self.dimmed else TEXT)
        self.itemconfigure(self.dot, state="normal" if self.by_hand else "hidden")
        if self.ticked is None:
            self.itemconfigure(self.tick_line, state="hidden")
        else:
            angle = math.radians(225 - 270 * self.share(self.ticked))
            middle, radius = self.size / 2, (self.box[2] - self.box[0]) / 2
            self.coords(self.tick_line, middle + (radius - 5) * math.cos(angle), middle - (radius - 5) * math.sin(angle),
                        middle + (radius + 4) * math.cos(angle), middle - (radius + 4) * math.sin(angle))
            self.itemconfigure(self.tick_line, state="normal")

    # ------------------------------------------------------------------ its marks

    def hand(self, on):
        """The hot dot at its lower right: this setting is held by hand."""
        if bool(on) != self.by_hand:
            self.by_hand = bool(on)
            self.draw()

    def tick(self, value):
        """A grey tick on the track at `value`: where the dial was set, when something else has moved it. None: no tick."""
        value = None if value is None else self.fit(value)
        if value != self.ticked:
            self.ticked = value
            self.draw()

    def dim(self, on):
        """Drawn grey: its part is muted."""
        if bool(on) != self.dimmed:
            self.dimmed = bool(on)
            self.draw()

    # ------------------------------------------------------------------ by hand

    def moved(self, exact):
        """A hand has moved it to `exact`: it goes to the nearest step, and says so if that is a new one."""
        self.exact = min(max(exact, self.low), self.high)
        value = self.fit(self.exact)
        if value != self.value:
            self.value = value
            self.draw()
            if self.command is not None:
                self.command(value)

    def press(self, event):
        self.held, self.last, self.exact, self.travel = True, event.y_root, self.value, 0

    def drag(self, event):
        if not self.held:
            return
        speed = (self.high - self.low) / self.sweep * (0.25 if event.state & SHIFT else 1.0)
        up, self.last = self.last - event.y_root, event.y_root
        self.travel += abs(up)
        self.moved(self.exact + up * speed)

    def let_go(self, event):
        self.held = False

    def wheel(self, event):
        self.moved(self.value + (self.step if event.delta > 0 else -self.step))

    def home(self, event):
        """A double click: back to where it started. Two quick drags one after the other are not a double click: the
        second press only counts as one if the first did not move the dial."""
        if getattr(self, "travel", 0) > 3:
            self.press(event)
            return
        self.held = False
        self.moved(self.start)


class Fader(tk.Canvas):
    """A straight fader, w by h pixels, lying on its side: a track filled to the value, with a cap. A click goes there
    and a drag follows; the wheel moves it a step. `home`: where a double click puts it (None: a double click does
    nothing). `mark`: a value that gets a tick on the track. `cap`: how wide the cap is."""

    def __init__(self, parent, w=60, h=20, low=0.0, high=100.0, start=0.0, step=1.0, command=None, fill=SOUND, home=None, mark=None, cap=4,
                 bg=GROUND):
        super().__init__(parent, width=w, height=h, bg=bg, highlightthickness=0, bd=0, takefocus=0)
        self.w, self.h, self.low, self.high, self.step, self.command, self.home_at = w, h, float(low), float(high), float(step), command, home
        self.cap_wide, self.held, self.dimmed, self.colour = cap, False, False, fill
        self.value = self.fit(start)
        thick = 8 if h < 24 else 6
        top = (h - thick) // 2
        self.span = (cap / 2 + 1, w - cap / 2 - 1)            # where the middle of the cap can be
        self.track = self.create_rectangle(self.span[0], top, self.span[1], top + thick, fill=LINE, outline="")
        self.bar = self.create_rectangle(self.span[0], top, self.span[0], top + thick, fill=fill, outline="")
        if mark is not None:
            x = self.x_of(mark)
            self.create_line(x, 1, x, top, fill=DIM)
            self.create_line(x, top + thick, x, h - 1, fill=DIM)
        self.cap = self.create_rectangle(0, 1, cap, h - 1, fill=TEXT, outline=GROUND if cap > 8 else "")
        self.bind("<ButtonPress-1>", self.press)
        self.bind("<B1-Motion>", self.press)
        self.bind("<ButtonRelease-1>", self.let_go)
        self.bind("<MouseWheel>", self.wheel)
        if home is not None:
            self.bind("<Double-Button-1>", lambda event: self.moved(home))
        self.draw()

    def fit(self, value):
        value = min(max(float(value), self.low), self.high)
        return round(self.low + round((value - self.low) / self.step) * self.step, 6)

    def x_of(self, value):
        return self.span[0] + (self.span[1] - self.span[0]) * (value - self.low) / (self.high - self.low)

    def get(self):
        return self.value

    def set(self, value):
        """Put there by the panel. It does not call back, and it does not move a fader a hand is on."""
        if self.held:
            return
        value = self.fit(value)
        if value != self.value:
            self.value = value
            self.draw()

    def draw(self):
        x = self.x_of(self.value)
        top, bottom = self.coords(self.track)[1], self.coords(self.track)[3]
        self.coords(self.bar, self.span[0], top, x, bottom)
        self.coords(self.cap, x - self.cap_wide / 2, 1, x + self.cap_wide / 2, self.h - 1)
        self.itemconfigure(self.bar, fill=DIM if self.dimmed else self.colour)
        self.itemconfigure(self.cap, fill=DIM if self.dimmed else TEXT)

    def dim(self, on):
        if bool(on) != self.dimmed:
            self.dimmed = bool(on)
            self.draw()

    def moved(self, value):
        value = self.fit(value)
        if value != self.value:
            self.value = value
            self.draw()
            if self.command is not None:
                self.command(value)

    def press(self, event):
        """Pressed, or dragged: it goes to where the pointer is."""
        self.held = True
        self.moved(self.low + (self.high - self.low) * (event.x - self.span[0]) / (self.span[1] - self.span[0]))

    def let_go(self, event):
        self.held = False

    def wheel(self, event):
        self.moved(self.value + (self.step if event.delta > 0 else -self.step))
