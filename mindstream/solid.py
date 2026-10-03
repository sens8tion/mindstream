"""Objects with sides: a card, a prism, a cube, each side carrying its own pictures and films.

The picture on screen is usually one surface. An object is several flat sides instead, turning together. Each side
has a list of things off the shelf (pictures and films, by their numbers there):

- nothing on a side: it shows whatever the session is showing (the live picture or film);
- one thing: it shows that (a film plays round and round);
- several: it fades from each to the next and round again, in time with the beat: a pulse between them.

The object never stops turning. While the picture rests (and when it is held flat) the object turns steadily about
its upright, like something on a turntable, so each side comes round to face you the right way up; while the
picture moves, the object tumbles as well.

Only what can be worked out without a screen is here: which sides there are and where, how big the object is, which
way to turn it to face a side, and what a side with several things shows at a given beat. No numpy, no OpenGL.
"""
import math

SIDES = {"card": ("front", "back"), "prism": ("one", "two", "three"), "cube": ("front", "right", "back", "left", "top", "bottom")}
EVERY = (0.5, 1.0, 2.0, 4.0, 8.0)        # beats from one thing on a side to the next
MOST = 8                                 # things on one side
FILMS = 12                               # different films on one object (each is held unpacked while it is on a side)


def turns(kind):
    """Where each side is: (about x, about y) in radians, the turn that takes a side facing you to its place."""
    if kind == "cube":
        return [(0.0, i * math.pi / 2) for i in range(4)] + [(-math.pi / 2, 0.0), (math.pi / 2, 0.0)]
    count = len(SIDES[kind])
    return [(0.0, i * 2 * math.pi / count) for i in range(count)]


def apothem(kind):
    """How far each side stands from the middle of the object, a side being a square two across."""
    if kind == "cube":
        return 1.0
    count = len(SIDES[kind])
    return 0.01 if count == 2 else 1.0 / math.tan(math.pi / count)      # a card's two sides are back to back


def size(kind, distance=2.2, reach=0.43):
    """How big to draw the object so that, turning about its upright `distance` away, it fills the height of the
    screen without its sides being cut off as their edges swing towards you (`reach`: half the screen's height, one
    unit away). The nearest an upright edge comes is the distance from the middle to that edge."""
    return reach * distance / (1.0 + reach * math.hypot(1.0, apothem(kind)))


def facing(kind, side):
    """The turn of the whole object (about x, about y, about z) that brings a side round to face you."""
    about_x, about_y = turns(kind)[side % len(SIDES[kind])]
    return (-about_x, -about_y, 0.0)


def showing(count, beat, every=1.0):
    """What a side with `count` things shows at `beat`: (this one, the next one, how far faded from this to the next).
    Each has its moment once every `every` beats and fades smoothly into the next: with two, a pulse between them."""
    if count < 2:
        return 0, 0, 0.0
    at = max(float(beat), 0.0) / max(float(every), 0.05)
    whole = math.floor(at)
    return int(whole % count), int((whole + 1) % count), 0.5 - 0.5 * math.cos(math.pi * (at - whole))


def clean(wanted, kinds):
    """What was asked for, made safe: {"kind", "sides": [[numbers] per side], "every"} or None for no object.
    `kinds`: what each number on the shelf is ("picture", "film", "sound"). Only pictures and films that are still on
    the shelf go on a side; a side holds at most MOST, the object at most FILMS different films."""
    if not isinstance(wanted, dict) or wanted.get("kind") not in SIDES:
        return None
    kind, films = wanted["kind"], []
    given = wanted.get("sides") if isinstance(wanted.get("sides"), list) else []
    sides = []
    for at in range(len(SIDES[kind])):
        side = []
        for number in (given[at] if at < len(given) and isinstance(given[at], list) else []):
            if not isinstance(number, int) or isinstance(number, bool) or kinds.get(number) not in ("picture", "film") or number in side:
                continue
            if kinds[number] == "film" and number not in films:
                if len(films) >= FILMS:
                    continue
                films.append(number)
            side.append(number)
        sides.append(side[:MOST])
    every = wanted.get("every")
    every = float(every) if isinstance(every, (int, float)) and not isinstance(every, bool) and float(every) in EVERY else 1.0
    return {"kind": kind, "sides": sides, "every": every}


def refit(sides, kind):
    """The same things on another kind of object: side for side, with what was on sides the new one lacks moved onto
    its last side, so nothing put on the object is lost by changing its kind."""
    count = len(SIDES[kind])
    out = [list(side) for side in sides[:count]] + [[] for _ in range(count - len(sides))]
    for side in sides[count:]:
        out[-1] += [number for number in side if number not in out[-1]]
    out[-1] = out[-1][:MOST]
    return out
