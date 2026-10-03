"""One look for both panels: nine colours, four sizes of type, and the stock widgets dressed in them.

The panels sit over the picture, in the dark. A stock button is light grey with black letters, which makes "mute"
the brightest thing on screen; so every stock widget is made here, flat and dark with light letters, and nothing
lights up unless it means something:

    hot    live, or yours: the chosen part, the live memory, the row that is playing, a button that is latched
    wait   waiting: a layer not yet in, play pressed and not yet on the bar line, something being fetched or made
    dim    off, or beside the point: headings, units, hints

A face is too close to the ground to be seen on its own, so a face always carries a one pixel line round it.
Nothing is smaller than 9 pt. Nothing here needs anything but tkinter.
"""
import os
import time
import tkinter as tk

# The colours come as a set, a skin. "acid" is the one used unless another is asked for (mindstream --skin ember, or
# the MINDSTREAM_SKIN setting): black, with a lime that is only ever used for what is live or yours.
#          ground      face       line       dim        text       hot        wait       sound      film
SKINS = {
    "acid":  ("#050607", "#12151a", "#343c47", "#93a0ae", "#f2f6fa", "#c8ff2e", "#ffb300", "#35e0c8", "#ff4df0"),
    "ember": ("#080606", "#171212", "#463636", "#a89d98", "#f8f2ee", "#ff4a1c", "#ffc233", "#40c080", "#b58cff"),
    "ice":   ("#04070b", "#0e151e", "#2c3d50", "#8a9db3", "#edf6ff", "#37d5ff", "#ffd166", "#7dffb0", "#c79bff"),
}
SKIN = os.environ.get("MINDSTREAM_SKIN", "acid").strip().lower()
GROUND, FACE, LINE, DIM, TEXT, HOT, WAIT, SOUND, FILM = SKINS.get(SKIN, SKINS["acid"])


def between(one, two, share):
    """A colour `share` of the way from `one` to `two`."""
    a, b = (int(one[i:i + 2], 16) for i in (1, 3, 5)), (int(two[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(x + (y - x) * share):02x}" for x, y in zip(a, b))


WARM = between(GROUND, HOT, 0.3)         # hot at about a third over the ground: a whole row that is live
DROP = between(GROUND, FACE, 0.5)        # the ground of a list that has dropped: darker than a face, so its line shows

# The type: a narrow engineering face (the one on German road signs), which packs more into a control than a text
# face and reads as equipment, not as an office. It comes with Windows 10 and 11; elsewhere the system's own stands in.
SMALL = ("Bahnschrift SemiCondensed", 10)               # headings (in capitals), units, hints, the lesser buttons
LABEL = ("Bahnschrift SemiBold SemiConden", 11)         # button faces, part names, the names of controls
VALUE = ("Bahnschrift SemiBold Condensed", 14)          # the number in a dial
BIG = ("Bahnschrift SemiBold Condensed", 20)            # the tempo, the super knob's number, the number on a memory
WORDS = ("Bahnschrift SemiCondensed", 11)               # what is typed in a box
LIST = ("Bahnschrift SemiBold SemiConden", 12)          # a row of a list that has dropped: bigger than a face, to be hit

DOWN = " ▾"                         # the small triangle at the right of a menu's face


def dress(widget):
    """One stock widget put in the panels' look, by what kind of widget it is. Returns it."""
    kind = widget.winfo_class()
    if kind in ("Button", "Menubutton"):
        widget.configure(bg=FACE, fg=TEXT, activebackground=LINE, activeforeground=TEXT, disabledforeground=DIM, relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=LINE, highlightcolor=LINE, font=LABEL, takefocus=0)
    elif kind == "Entry":
        widget.configure(bg=FACE, fg=TEXT, insertbackground=HOT, relief="flat", bd=0, font=WORDS,
                         highlightthickness=1, highlightbackground=LINE, highlightcolor=TEXT)
    elif kind == "Menu":
        widget.configure(bg=DROP, fg=TEXT, activebackground=HOT, activeforeground=GROUND, relief="flat", bd=0, font=LIST, tearoff=0)
    elif kind == "Label":
        widget.configure(bg=GROUND, fg=TEXT, font=LABEL)
    return widget


def pixel(widget):
    """An empty picture one pixel square. A button that carries it measures its width and height in pixels and not in
    letters, which is the only way a stock button can be given an exact size."""
    root = widget.winfo_toplevel()
    if not hasattr(root, "_pixel"):
        root._pixel = tk.PhotoImage(master=root, width=1, height=1)
    return root._pixel


def sized(widget, w, h):
    """A button or a menu's face made exactly w by h pixels, its one pixel line included."""
    widget.configure(image=pixel(widget), compound="center", width=w - 2, height=h - 2, padx=0, pady=0)
    return widget


def button(parent, text, command=None, w=None, h=28, font=LABEL, fg=TEXT, **more):
    """A button: a dark face, a line round it, light letters. With `w`, exactly that many pixels wide and `h` high."""
    made = dress(tk.Button(parent, text=text, command=command, **more))
    made.configure(font=font, fg=fg)
    return sized(made, w, h) if w else made


def lit(widget, on, colour=HOT):
    """A button lit (latched, chosen, live) or dark again. Lit, its letters are the ground's colour on `colour`."""
    widget.configure(bg=colour if on else FACE, fg=GROUND if on else TEXT, activebackground=colour if on else LINE,
                     activeforeground=GROUND if on else TEXT)


def heading(parent, text, bg=GROUND):
    """The name of a section: small grey capitals. A heading never lights up."""
    return tk.Label(parent, text=text.upper(), fg=DIM, bg=bg, font=SMALL, anchor="w")


def label(parent, text, bg=GROUND, **more):
    """The name of a control."""
    return tk.Label(parent, text=text, fg=TEXT, bg=bg, font=LABEL, anchor="w", **more)


def note(parent, text="", bg=GROUND, **more):
    """Small grey words: a unit, a hint, something said in passing."""
    return tk.Label(parent, text=text, fg=DIM, bg=bg, font=SMALL, anchor="w", **more)


class Menu:
    """A list that drops from a control or pops up under the pointer, drawn by the panel itself.

    The system's own menus cannot be trusted with the panels' colours (on some Windows themes they keep a light
    ground under the panels' light letters, or grey them), and they inherit an inset's see-through. This one is a
    small window of its own: fully opaque, a dark ground, light letters, the row under the pointer lit. It closes
    when a row is chosen, on Escape, on a press anywhere else in the panel, or a moment after the pointer has left it.
    It answers to the few calls the panels made of the system's menu: add_command, add_separator, delete, tk_popup,
    invoke."""

    open_now = None                                           # the one list that is down, if any

    def __init__(self, parent):
        self.parent, self.items, self.top, self.opened, self.left = parent, [], None, 0.0, None

    def add_command(self, label="", command=None, image=None, compound=None, **more):
        self.items.append((str(label), command, image))

    def add_separator(self):
        self.items.append(None)

    def delete(self, first=0, last="end"):
        self.items = []

    def invoke(self, index):
        """Choose a row, as a hand would."""
        item = self.items[index]
        self.close()
        if item is not None and item[1] is not None:
            item[1]()

    def tk_popup(self, x, y, wide=0, chosen=None):
        """The list, with its top left corner at (x, y) on the screen (or above that, if it would run off the foot of
        it). `wide`: at least this many pixels across. `chosen`: the label of the row in force, which is marked."""
        if Menu.open_now is not None:
            Menu.open_now.close()
        if not self.items:
            return
        root = self.parent.winfo_toplevel()
        if not getattr(root, "_menus_watched", False):         # a press anywhere in the panel closes whatever list is down
            root._menus_watched = True
            root.bind_all("<ButtonPress>", Menu.pressed, add="+")
        top = self.top = tk.Toplevel(root)
        top.withdraw()
        top.overrideredirect(True)
        top.configure(bg=LINE, padx=1, pady=1)
        for at, item in enumerate(self.items):
            if item is None:
                tk.Frame(top, bg=LINE, height=1).pack(fill="x")
                continue
            words, _, image = item
            marked = chosen is not None and words == str(chosen)
            row = tk.Label(top, text=words, bg=DROP, fg=HOT if marked else TEXT, font=LIST, anchor="w", padx=12, pady=5)
            if image is not None:
                row.configure(image=image, compound="left")
            row.pack(fill="x")
            row.bind("<Enter>", lambda event, row=row: row.configure(bg=HOT, fg=GROUND))
            row.bind("<Leave>", lambda event, row=row, marked=marked: row.configure(bg=DROP, fg=HOT if marked else TEXT))
            row.bind("<ButtonRelease-1>", lambda event, at=at: self.invoke(at))
        top.bind("<Escape>", lambda event: self.close())
        top.update_idletasks()
        w, h = max(top.winfo_reqwidth(), int(wide)), top.winfo_reqheight()
        if y + h > top.winfo_screenheight() and y - h >= 0:    # no room below: it goes up instead
            y -= h
        top.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
        top.transient(root)                                   # owned by the panel: Windows keeps an owned window above its owner, always
        top.attributes("-topmost", True)
        top.deiconify()
        top.lift()
        Menu.open_now, self.opened, self.left = self, time.time(), None
        top.after(250, self.watch)

    def watch(self):
        """Closes the list once the pointer has been away from it for most of a second."""
        top = self.top
        if top is None:
            return
        try:
            x, y = top.winfo_pointerxy()
            inside = (top.winfo_rootx() - 24 <= x <= top.winfo_rootx() + top.winfo_width() + 24
                      and top.winfo_rooty() - 40 <= y <= top.winfo_rooty() + top.winfo_height() + 24)
            now = time.time()
            self.left = None if inside else (self.left or now)
            if self.left is not None and now - self.left > 0.8:
                self.close()
            else:
                top.lift()                                    # and above it again, whatever has just lifted the panel
                top.after(250, self.watch)
        except tk.TclError:
            self.top = None

    def close(self):
        top, self.top = self.top, None
        if Menu.open_now is self:
            Menu.open_now = None
        if top is not None:
            try:
                top.destroy()
            except tk.TclError:
                pass

    @staticmethod
    def pressed(event):
        """A press somewhere in the panel: the list that is down closes, unless the press is on it (or is the very
        press that opened it)."""
        down = Menu.open_now
        if down is None or down.top is None or time.time() - down.opened < 0.2:
            return
        try:
            if str(event.widget).startswith(str(down.top)):
                return
        except Exception:
            pass
        down.close()


class Choice(tk.Button):
    """A choice from a list: its face says what is chosen, with a small triangle at its right edge, and pressing it
    drops the list (see Menu), with the one in force marked. `var` holds what is chosen; `command(value)` is called
    when a hand chooses, and not when the panel sets `var` itself. `says` turns a value into the words on the face."""

    def __init__(self, parent, var, values, command=None, w=None, h=28, says=None, font=LABEL):
        super().__init__(parent, command=self.drop)
        dress(self)
        self.configure(font=font, anchor="w", padx=6)
        self.var, self.command, self.says = var, command, says or str
        self.list = Menu(self)
        if w:
            sized(self, w, h)
        self.fill(values)
        var.trace_add("write", lambda *_: self.face())
        self.face()

    def face(self):
        try:
            self.configure(text=self.says(self.var.get()) + DOWN)
        except tk.TclError:                                   # the panel is closing
            pass

    def fill(self, values):
        """The list, written afresh."""
        self.values = tuple(values)
        self.list.delete(0, "end")
        for value in self.values:
            self.list.add_command(label=str(value), command=lambda value=value: self.choose(value))

    def drop(self):
        """The list, dropped under the face, as wide as the face at least."""
        if Menu.open_now is self.list:
            self.list.close()
            return
        self.list.tk_popup(self.winfo_rootx(), self.winfo_rooty() + self.winfo_height() + 1, wide=self.winfo_width(), chosen=self.var.get())

    def choose(self, value):
        """A hand has chosen from the list."""
        self.var.set(value)
        if self.command is not None:
            self.command(value)


class Words(tk.Entry):
    """A box for words. With a `hint`, while the box is empty and the keyboard is elsewhere it says in grey what it
    is for; the hint is never taken for something typed."""

    def __init__(self, parent, width=20, hint=""):
        super().__init__(parent, width=width)
        dress(self)
        self.hint, self.hinting = hint, False
        if hint:
            self.bind("<FocusIn>", lambda event: self.clear_hint(), add="+")
            self.bind("<FocusOut>", lambda event: self.show_hint(), add="+")
            self.show_hint()

    def show_hint(self):
        if self.hint and not self.hinting and not tk.Entry.get(self):
            self.hinting = True
            self.configure(fg=DIM)
            tk.Entry.insert(self, 0, self.hint)

    def clear_hint(self):
        if self.hinting:
            self.hinting = False
            tk.Entry.delete(self, 0, "end")
            self.configure(fg=TEXT)

    def get(self):
        return "" if self.hinting else super().get()

    def put(self, text):
        """Words put in the box by the panel, as if typed."""
        self.clear_hint()
        tk.Entry.delete(self, 0, "end")
        tk.Entry.insert(self, 0, text)

    def empty(self):
        """The box cleared, once what was in it has been taken."""
        self.clear_hint()
        tk.Entry.delete(self, 0, "end")
        try:
            elsewhere = self.focus_get() is not self
        except Exception:
            elsewhere = True
        if elsewhere:
            self.show_hint()


class Hints:
    """The one line at the foot of a panel. It says what the control under the pointer is and everything it does, the
    gestures and the keys included, so that nothing has to be remembered; and it is where the panel says what has
    just happened ("memory 3 kept", "timeline full: 12 rows"). Something said stays for a few seconds, or until the
    pointer moves on to another control."""

    def __init__(self, label):
        self.label, self.pointed, self.said, self.until = label, None, "", 0.0

    def on(self, widget, words):
        """`words` (a string, or a function that gives one) is what the bar says while the pointer is on `widget`."""
        widget.bind("<Enter>", lambda event: self.point(words), add="+")
        widget.bind("<Leave>", lambda event: self.point(None), add="+")
        return widget

    def point(self, words):
        self.pointed = words
        if words is not None:
            self.until = 0.0
        self.draw()

    def say(self, words, seconds=6.0):
        """Something that has just happened."""
        self.said, self.until = words, time.time() + seconds
        self.draw()
        try:
            self.label.after(int(seconds * 1000) + 60, self.draw)
        except tk.TclError:
            pass

    def draw(self):
        try:
            if time.time() < self.until:
                self.label.configure(text=self.said, fg=TEXT)
            else:
                words = self.pointed() if callable(self.pointed) else self.pointed
                self.label.configure(text=words or "", fg=DIM)
        except tk.TclError:                                   # the panel is closing
            pass


def hint_bar(parent):
    """The label for a panel's hints: it takes the width it is given and never asks for more."""
    return tk.Label(parent, text="", fg=DIM, bg=GROUND, font=SMALL, anchor="w", width=1, height=1)


class HoldButton(tk.Canvas):
    """A button for what cannot be undone: it has to be pressed and held. Its face fills from the left while it is
    held, and it acts when it is full (after `seconds`); let go before that and nothing happens."""

    def __init__(self, parent, text, command, w=80, h=28, seconds=0.4, font=LABEL):
        super().__init__(parent, width=w - 2, height=h - 2, bg=FACE, highlightthickness=1, highlightbackground=LINE, bd=0, takefocus=0)
        self.command, self.seconds, self.since, self.w, self.h = command, seconds, None, w - 2, h - 2
        self.fill = self.create_rectangle(0, 0, 0, self.h, fill=HOT, outline="")
        self.words = self.create_text(self.w // 2, self.h // 2, text=text, font=font, fill=TEXT)
        self.bind("<ButtonPress-1>", self.press)
        self.bind("<ButtonRelease-1>", self.let_go)

    def press(self, event):
        self.since = time.time()
        self.fills()

    def fills(self):
        if self.since is None:
            return
        share = (time.time() - self.since) / self.seconds
        self.coords(self.fill, 0, 0, min(share, 1.0) * self.w, self.h)
        if share >= 1.0:
            self.since = None
            self.command()
            self.after(250, lambda: self.coords(self.fill, 0, 0, 0, self.h))
        else:
            self.after(30, self.fills)

    def let_go(self, event):
        if self.since is not None:
            self.since = None
            self.coords(self.fill, 0, 0, 0, self.h)

    def dim(self, on):
        """Grey words while there is nothing for it to do."""
        self.itemconfigure(self.words, fill=DIM if on else TEXT)


class Segments(tk.Frame):
    """A choice between two to four things, as a row of buttons with the chosen one lit (a light face, dark letters):
    one press, and what is chosen can be seen. `command(value)` is called when a hand chooses; `set(value)` is the
    panel's way of showing what is in force, and does not call back."""

    def __init__(self, parent, choices, command=None, w=56, h=28, start=None, says=None, font=LABEL, bg=GROUND):
        super().__init__(parent, bg=bg)
        self.command, self.value, self.buttons = command, None, {}
        for choice in choices:
            self.buttons[choice] = button(self, (says or str)(choice), lambda choice=choice: self.press(choice), w=w, h=h, font=font)
            self.buttons[choice].pack(side="left")
        self.set(start)

    def get(self):
        return self.value

    def set(self, value):
        if value != self.value:
            self.value = value
            for choice, made in self.buttons.items():
                lit(made, choice == value, TEXT)

    def press(self, value):
        """A hand has chosen."""
        self.set(value)
        if self.command is not None:
            self.command(value)


class TitleStrip(tk.Frame):
    """The strip across the top of a panel: its name, and a button for its small form. Dragging the strip moves the
    window, which is the only way to move a panel while it is an inset and has no title bar of its own.
    `move(x, y)` puts the window there; `press` is what the button does. `button` is the button itself, so that the
    panel can change what it says."""

    def __init__(self, parent, name, move, press):
        super().__init__(parent, bg=GROUND, height=22)
        self.pack_propagate(False)
        self.move, self.from_ = move, None
        self.button = button(self, "small", press, w=56, h=22, font=SMALL)
        self.button.pack(side="right")
        self.handles = [self, heading(self, name), note(self, "drag to move")]
        self.handles[1].pack(side="left")
        self.handles[2].pack(side="left", padx=(16, 0))
        for handle in self.handles:
            handle.configure(cursor="fleur")
            handle.bind("<ButtonPress-1>", self.grip)
            handle.bind("<B1-Motion>", self.drag)
            handle.bind("<ButtonRelease-1>", lambda event: setattr(self, "from_", None))

    def grip(self, event):
        root = self.winfo_toplevel()
        self.from_ = (event.x_root, event.y_root, root.winfo_x(), root.winfo_y())

    def drag(self, event):
        if self.from_ is not None:
            self.move(self.from_[2] + event.x_root - self.from_[0], self.from_[3] + event.y_root - self.from_[1])
