"""A panel as an inset over a full screen viewer: where it was, without its border, see-through, and on top.

A panel is a window of its own. While the viewer is in a window, so is the panel, with its title bar. When the
viewer goes full screen the panel stays exactly where it was left, loses its border and title bar, and turns a
little see-through (nine tenths solid), so that it reads as part of the picture and can still be read. Back in a
window, it gets its border back in the same place. An inset has no title bar to be dragged by, so a panel has a
strip of its own for that: `moved` is what its drag calls. Nothing here needs anything but tkinter.
"""

ALPHA = 0.9                              # how solid an inset is: the tenth that shows through is enough to belong to the picture


def inset(root, on, tries=6):
    """Make `root` an inset (on) or an ordinary window again (off). What is inside it does not move on screen."""
    on = bool(on)
    try:
        if bool(root.overrideredirect()) != on:
            root.update_idletasks()
            if on:                                            # where its border was, to put it back; and where its inside is, to keep
                root._framed_at = (root.winfo_x(), root.winfo_y())
                x, y = root.winfo_rootx(), root.winfo_rooty()
            else:
                x, y = getattr(root, "_framed_at", (root.winfo_x(), root.winfo_y()))
            root.withdraw()                                   # the border only changes on a window that is shown afresh
            root.overrideredirect(on)
            root.deiconify()
            root._inset_at = (x, y)
            root.geometry(f"+{x}+{y}")
        root.attributes("-alpha", ALPHA if on else 1.0)
        root.attributes("-topmost", True)
        root.lift()
        at = getattr(root, "_inset_at", None)
        if at is not None and tries > 0:                      # looked at again shortly: a window just shown afresh can drop a move
            root.after(200, lambda: _settle(root, on, tries - 1))
    except Exception:
        pass


def _settle(root, on, tries):
    try:
        x, y = root._inset_at
        if bool(root.overrideredirect()) != on:
            return
        if abs(root.winfo_x() - x) > 6 or abs(root.winfo_y() - y) > 6:
            root.geometry(f"+{x}+{y}")
            if tries > 0:
                root.after(200, lambda: _settle(root, on, tries - 1))
    except Exception:
        pass


def moved(root, x, y):
    """The panel dragged, by its own strip, to (x, y). As an inset, where it is remembered to be goes with it: so
    that it is not put back where it was a moment later, and so that its border comes back beside where it now is."""
    try:
        if root.overrideredirect():
            was = getattr(root, "_inset_at", (root.winfo_x(), root.winfo_y()))
            framed = getattr(root, "_framed_at", None)
            if framed is not None:
                root._framed_at = (framed[0] + x - was[0], framed[1] + y - was[1])
            root._inset_at = (x, y)
        root.geometry(f"+{x}+{y}")
    except Exception:
        pass


def keep_typing(root):
    """A window without a border is not given the keyboard by a click, so a box in it could not be typed in: any box
    clicked takes the keyboard itself."""
    def take(event):
        try:
            if root.overrideredirect() and event.widget.winfo_class() in ("Entry", "TEntry", "Text"):
                root.focus_force()
                event.widget.focus_force()
        except Exception:
            pass
    root.bind_all("<Button-1>", take, add="+")
