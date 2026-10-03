"""The effects on the picture: what there are, what each is called, and how far each can be turned.

Each effect is one number. At nothing (where they all start) an effect costs nothing: its work is skipped, and a
moment later what it remembered is let go. Turned
up, several of them are heavy on the graphics card on purpose (they are worked out for every point of the screen,
many times over), and with a film being made on the same card they will slow each other down.

This file is only the list (no numpy, no OpenGL), so the story feed and the panels can read it: the viewer
(gl_view.py) holds the effects themselves. The order here is the order they are applied in.

    EFFECTS     (key, name, lowest, highest, where it starts, step, what it does)
    RANGES      {key: (lowest, highest)}
    STARTS      {key: where it starts}
"""
import zlib

EFFECTS = (
    # in the scene itself
    ("flow", "Flow", 0.0, 1.0, 0.0, 0.05, "the trails are carried along like smoke in moving air"),
    ("particles", "Particles", 0.0, 1.0, 0.0, 0.05, "the picture as a cloud of up to four million points that remember: born in its bright places, carried on a curling current, blown off on the beat, home on the bar"),
    # what takes the picture over and keeps it as its own: each lets the true picture back in less, the further it is turned
    ("fluid", "Fluid", 0.0, 1.0, 0.0, 0.05, "the picture's colours carried in swirling ink; every kick pushes it"),
    ("coral", "Coral", 0.0, 1.0, 0.0, 0.05, "living pattern grows out of the picture's edges: mazes in the dark, coral in the light"),
    ("mosh", "Mosh", 0.0, 1.0, 0.0, 0.05, "the picture stops renewing and is dragged about by what moves; it snaps back on the bar"),
    ("sort", "Sort", 0.0, 1.0, 0.0, 0.05, "the bright parts of the picture melt into sorted streaks, bar by bar"),
    ("slit", "Slit scan", 0.0, 1.0, 0.0, 0.05, "different parts of the frame show different moments of the last second"),
    ("echo", "Echo", 0.0, 1.0, 0.0, 0.05, "the frame fed back into itself: spiralling, crawling, turning colour as it ages"),
    # bending what is on screen
    ("ripple", "Ripple", 0.0, 1.0, 0.0, 0.05, "rings of water spread from the middle on every beat"),
    ("shatter", "Shatter", 0.0, 1.0, 0.0, 0.05, "seen through a sheet of crystal cells, each bending the picture its own way"),
    ("glitch", "Glitch", 0.0, 1.0, 0.0, 0.05, "blocks and lines of the picture slip sideways on the beat"),
    ("droste", "Droste", 0.0, 1.0, 0.0, 0.05, "the picture inside itself, down a spiral, for ever"),
    ("mobius", "Moebius", 0.0, 1.0, 0.0, 0.05, "the picture slid through itself: the middle swells, the far side shrinks to the rim"),
    ("gyroid", "Gyroid", 0.0, 1.0, 0.0, 0.05, "a flight through an endless curved lattice, skinned with the picture"),
    ("fractal", "Fractal", 0.0, 1.0, 0.0, 0.05, "a flight down a carved corridor painted with the picture, which snaps whole as you pass where it is thrown from"),
    # redrawing it
    ("paint", "Paint", 0.0, 1.0, 0.0, 0.05, "oil paint: flat strokes that keep their edges"),
    ("relief", "Relief", 0.0, 1.0, 0.0, 0.05, "the picture raised from its own light and dark, under a lamp that circles"),
    ("edges", "Edges", 0.0, 1.0, 0.0, 0.05, "the outlines of things glow like neon"),
    ("halftone", "Halftone", 0.0, 1.0, 0.0, 0.05, "printed in four inks, as dots"),
    ("ascii", "Glyphs", 0.0, 1.0, 0.0, 0.05, "the picture as characters: dense ones where it is bright, strokes along its edges"),
    # light
    ("rays", "Rays", 0.0, 1.0, 0.0, 0.05, "shafts of light stream out from the bright parts"),
    ("bloom", "Bloom", 0.0, 1.0, 0.0, 0.05, "bright things glow into what is around them"),
    ("streak", "Streak", 0.0, 1.0, 0.0, 0.05, "bright things smear sideways, as through a cinema lens"),
    # on the beat
    ("strobe", "Strobe", 0.0, 1.0, 0.0, 0.05, "a flash on the beat (never more than three a second)"),
    ("invert", "Invert", 0.0, 1.0, 0.0, 0.05, "light and dark change over on the beat, in bands, the colours kept"),
    ("cycle", "Cycle", 0.0, 1.0, 0.0, 0.05, "the picture in six bands of colour that step round on the beat"),
    # the lens and the film
    ("bokeh", "Bokeh", 0.0, 1.0, 0.0, 0.05, "the edges of the screen go out of focus, bright points opening into discs"),
    ("lens", "Lens", 0.0, 1.0, 0.0, 0.05, "the picture bulges and its colours part towards the edges"),
    ("grain", "Grain", 0.0, 1.0, 0.0, 0.05, "film grain and faint scan lines"),
    ("vhs", "VHS", 0.0, 1.0, 0.0, 0.05, "off a worn tape: soft, its colour smeared and late, tearing and rolling"),
    # how much light is let through (in stops, so 0 leaves the picture as it is; it is not one of the passes)
    ("exposure", "Exposure", -2.0, 2.0, 0.0, 0.1, "how much light is let through, in stops: below 0 darker, above brighter, the brightest burning to white"),
    # how finely everything is drawn
    ("sharp", "Sharpness", 1.0, 2.0, 1.0, 0.25, "everything is drawn at up to twice the size and brought down: finer, and four times the work"),
)
KEYS = tuple(effect[0] for effect in EFFECTS)
# Settings of the light that are not effects (no dial on the panel; typed, "!tonemap 1"): how what is brighter than the
# screen can show is brought down to it. 0 keeps the picture exactly as it is and lets only what is brighter than white
# burn towards white; 1 is a film's curve, whose shoulder rolls the highlights off and keeps their colour, and whose toe
# deepens the shadows (a mid grey stays about where it was, white comes down to 0.88, a tenth to a twenty-fifth: more
# contrast, so it is a look, not the rest position). Between, a mix of the two.
TONE = (("tonemap", 0.0, 1.0, 0.0),)
RANGES = {key: (low, high) for key, _, low, high, _, _, _ in EFFECTS}
RANGES.update({key: (low, high) for key, low, high, _ in TONE})
STARTS = {key: start for key, _, _, _, start, _, _ in EFFECTS}
STARTS.update({key: start for key, _, _, start in TONE})
# Each of these is one or more passes over the whole screen, and this is the order they run in: what takes the picture
# over, then the loop, then what bends it, then what redraws it, then the optics (focus before glow); then the light is
# brought down to what the screen can show (exposure, the tone curve), and after that the ones that work on the
# finished picture (DISPLAY): two that print it, the beat, and the faults of the signal, last. (After
# docs/research/06_visual_effects.md, section 4.1.)
POST = ("fluid", "coral", "mosh", "sort", "slit", "echo", "ripple", "shatter", "droste", "mobius", "gyroid", "fractal", "paint", "relief", "edges",
        "bokeh", "rays", "bloom", "streak", "halftone", "ascii", "strobe", "invert", "cycle", "glitch", "vhs")
# The screen's frame is worked in light (linear, as light adds, in float: values may pass white) up to the tone curve,
# and on the finished picture (0 to 1, as the screen shows it) after it. These run after the curve, because each is
# built on the screen's numbers rather than on light:
#   halftone  inks are worked out as 1 - colour (paper and ink), which only means something between 0 and 1
#   ascii     a character is chosen by how bright a cell looks, in twelve steps from 0 to 1
#   strobe, invert, cycle   the room's flash multiplies what is shown; invert turns 0 to 1 about the middle grey;
#             cycle cuts brightness into six bands from 0 to 1
#   glitch    posterises blocks to four levels of 0 to 1 and adds noise sized to the screen's steps: a fault of the signal
#   vhs       a worn tape shows a finished picture (and the research puts screen emulation after the curve)
# Everything else is worked in light: the remaps only move points, the simulations carry colour (and what they take
# from brightness is read as it looks, see fx.LINEAR), and the optics (glow, rays, focus, streaks) are only right in
# light, where a bright thing is really brighter than white.
DISPLAY = ("halftone", "ascii", "strobe", "invert", "cycle", "glitch", "vhs")


# ---- the story's director and the effects
#
# The director has every effect but one: how finely things are drawn ("sharp") is the machine's business, not the
# story's. With each beat it says where every effect should stand, so effects come and go as the story moves. It may
# name them itself (a line "fx: ripple 0.6, bloom 0.4"); when it does not, the beat is read for what it is about.

# the heaviest on the graphics card: the director never has two of these on at once, and the viewer sheds all but one
# of them when frames run slow
HEAVY = ("fractal", "gyroid", "fluid", "coral", "paint", "relief", "sort", "rays", "bokeh", "mosh", "particles")
DIRECTED = tuple(key for key in KEYS if key not in ("sharp", "strobe"))        # nor does the story flash the room: the strobe is the hand's
MOST_AT_ONCE = 3
READ = {
    "flow": "smoke fog mist haze steam cloud clouds wind breath drift drifting vapour vapor incense",
    "particles": "dust sand snow ash ashes stars sparks spores pollen swarm crowd confetti embers rain petals fireflies",
    "ripple": "water sea ocean river lake pond pool rain wave waves tide flood drown drowning swim swimming puddle ripples",
    "shatter": "glass ice crystal mirror mirrors shatter shatters shattered broken breaks crack cracks fracture splinter diamond frost",
    "glitch": "machine machines screen screens signal static error broken digital data code wire wires circuit robot television radio fault",
    "gyroid": "tunnel cave maze labyrinth corridor underground inside lattice hive bones cathedral catacomb mine sewer vein veins",
    "paint": "dream dreams memory painting painted canvas remember remembered childhood garden meadow sleep asleep",
    "edges": "neon city night electric wire sign signs laser club street streets arcade lightning",
    "halftone": "newspaper print printed poster photograph photo magazine comic page pages ink",
    "rays": "sun sunlight dawn light window god heaven church beam beams angel angels sky clearing halo",
    "bloom": "glow glowing fire flame flames gold golden lantern candle lamp moon bright burning blaze",
    "streak": "car cars headlights train speed speeding highway road motorway chase racing rocket comet",
    "bokeh": "close closer face eyes whisper whispers intimate small tiny near tear tears kiss",
    "lens": "dizzy drunk fall falling vertigo spin spinning warped fever sick eye lens",
    "grain": "old past film years ago ghost ghosts faded abandoned ruin ruins dusty forgotten",
    "fluid": "ink blood oil paint milk wine liquid pour pours poured melt melts melting dissolve dissolves bleeding flows",
    "coral": "coral moss mould mold lichen fungus roots skin cells grow grows growing spreading infection veins rust",
    "mosh": "memory forget forgets forgotten lost confused corrupt corrupted dissolving unreal hallucination trip tripping",
    "sort": "rain falling waterfall curtain drip drips dripping streak streaks collapse collapses pours tears",
    "slit": "time clock hour hours moment yesterday tomorrow slow slowly echo echoes late waiting again",
    "echo": "dream spiral trance hypnotic endless repeat repeats mirror mirrors vortex dizzy swirling",
    "droste": "inside within itself infinite infinity recursion eye well staircase stairs descend descends deeper",
    "mobius": "turn turns twisted twist inside-out bend bends warp warped loop loops",
    "fractal": "city tower towers ruin ruins temple building buildings machine architecture corridor corridors vault crypt",
    "relief": "stone carved statue marble wall walls rock mountain desert bone bones sculpture",
    "ascii": "computer terminal code message letter letters text screen typing type words written",
    "invert": "negative shadow shadows opposite death dead ghost eclipse x-ray lightning",
    "cycle": "rainbow colour colours color colors carnival neon party acid festival fireworks",
    "vhs": "television tape video recording camera footage broadcast rewind home childhood nineties",
    "exposure": "blinding dazzling glare overexposed whiteout bleached blazing searing radiant",
}
# words that turn a setting with two sides (exposure) the other way: the frame darker
READ_DOWN = {"exposure": "dark darkness dim gloom murk murky blackout dusk twilight unlit"}
# how far the director takes each (1 unless said; for exposure, a stop either way)
MOST = {"gyroid": 0.8, "paint": 0.85, "lens": 0.6, "grain": 0.6, "halftone": 0.7, "glitch": 0.7, "shatter": 0.75, "fluid": 0.9, "mosh": 0.9, "sort": 0.8,
        "echo": 0.8, "droste": 0.8, "mobius": 0.7, "fractal": 0.8, "ascii": 0.7, "invert": 0.7, "cycle": 0.7, "vhs": 0.8, "slit": 0.85, "exposure": 1.0}
SIGNED = tuple(key for key in KEYS if RANGES[key][0] < 0.0)       # nothing is in the middle: exposure


def named(text):
    """What a line such as "ripple 0.6, bloom 0.4" or "ripple, bloom strong" asks for: {effect: amount}. "none" or
    nothing recognised gives {}. Amounts may be 0 to 1, or 0 to 100, or a word (light, strong, full); a bare name is 0.6."""
    words = {"light": 0.3, "slight": 0.3, "low": 0.3, "some": 0.5, "medium": 0.5, "strong": 0.8, "high": 0.8, "heavy": 0.8, "full": 1.0}
    out = {}
    for piece in str(text).lower().replace(";", ",").split(","):
        bits = piece.replace("=", " ").replace(":", " ").split()
        key = next((bit for bit in bits if bit in DIRECTED), None)
        if key is None:
            continue
        amount = 0.6
        for bit in bits:
            if bit in words:
                amount = words[bit]
            else:
                try:
                    amount = float(bit.rstrip("%"))
                    if key not in SIGNED:                       # exposure is in stops, either side of 0: never a percentage
                        amount = amount / 100.0 if amount > 1.0 else amount
                except ValueError:
                    pass
        most = MOST.get(key, 1.0)
        out[key] = round(min(max(amount, -most if key in SIGNED else 0.0), most), 2)
    return one_heavy(dict(list(out.items())[:MOST_AT_ONCE + 1]))


def one_heavy(chosen):
    """The effects chosen, with only the first of the heavy ones kept."""
    heavy = [key for key in chosen if key in HEAVY]
    return {key: value for key, value in chosen.items() if key not in heavy[1:]}


def from_beat(text, heat=1.0):
    """The effects a beat of the story calls for, read from what it is about: {effect: amount}, three at most. `heat`
    is how wild the beat is (the chaos setting, 0 to 2): the wilder, the further each is turned. A beat that names
    nothing gets a plain setting for its heat: drifting and grainy when calm, glowing when it is not, breaking up
    when it is wild."""
    seen = [word.strip(".,;:!?\"'()") for word in str(text).lower().split()]
    scores, down = {}, {}
    for key, listed in READ.items():
        count = sum(seen.count(word) for word in listed.split())
        if count:
            scores[key] = count
    for key, listed in READ_DOWN.items():                       # dark words turn the exposure down
        count = sum(seen.count(word) for word in listed.split())
        if count > scores.get(key, 0):
            scores[key], down[key] = count, True
    push = min(max(float(heat), 0.0), 2.0) / 2.0
    if not scores:
        if push < 0.4:
            return {"flow": 0.4, "grain": 0.25}
        return {"bloom": 0.35} if push < 0.7 else {"bloom": 0.5, "glitch": 0.4}
    chosen = sorted(scores, key=lambda key: (-scores[key], KEYS.index(key)))[:MOST_AT_ONCE]
    return one_heavy({key: round(min(0.35 + 0.5 * push + 0.1 * (scores[key] - 1), MOST.get(key, 1.0)) * (-1.0 if key in down else 1.0), 2)
                      for key in chosen})


def directed(chosen):
    """Where every effect the director has should stand, given the ones it chose: the rest at nothing."""
    return {key: float(chosen.get(key, 0.0)) for key in DIRECTED}


def chain(look, least=0.004):
    """The passes over the screen that are needed for this look, in order: those whose effect is turned up at all."""
    return [key for key in POST if look.get(key, 0.0) > least]


def in_light(steps):
    """A chain ([effect] or [(effect, amount)], in order) parted at the tone curve: (those worked in light, those worked
    on the finished picture). POST puts every DISPLAY effect last, so the order within each part is the chain's."""
    name = lambda step: step[0] if isinstance(step, tuple) else step
    return [step for step in steps if name(step) not in DISPLAY], [step for step in steps if name(step) in DISPLAY]


def paced(before, chosen, most_new=1):
    """The effects for this beat when the last beat had `before` and the director now asks for `chosen` (both
    {effect: amount}): at most `most_new` new effects come in and at most one goes, so a change of scene turns the look
    over across a few beats rather than switching several heavy passes on and off on one beat (which is felt as a
    hitch). What stays takes its new amount at once (amounts glide in the viewer). Those leaving later are listed
    before the newcomers, so one_heavy keeps an old heavy effect and makes a new heavy one wait its turn."""
    before = {key: value for key, value in (before or {}).items() if value != 0.0}         # (exposure may be below 0)
    kept = {key: value for key, value in chosen.items() if key in before}
    leaving = [key for key in before if key not in chosen]
    staying_on = {key: before[key] for key in leaving[1:]}
    new = {key: value for key, value in chosen.items() if key not in before}
    return one_heavy({**kept, **staying_on, **dict(list(new.items())[:most_new])})


# ---- each picture by itself (the "image" target)
#
# The same effects can also be run over each picture (and each frame of a film) by itself, before it is put on the
# surface, on a side of an object or in the swarm: the screen's effects ("screen") then run over the whole finished
# frame as before. The image target has its own numbers, written "image:<effect>" (a message may also carry them as
# {"image": {"bloom": 0.8}}), held, released and directed exactly as the screen's are.
#
# Not every effect is given to the pictures:
#   - the ones that remember (fluid, coral, mosh, sort, slit, echo) need a memory carried from frame to frame; one per
#     picture would be a copy of every simulation for every picture on screen (twenty-odd fluids), and what they do
#     (smear the moving frame through time) is about the screen, not a still picture. They stay screen only.
#   - flow and particles are part of the scene, not passes; lens, grain and exposure are in the last passes over the screen;
#     bokeh is about the edges of the screen; the strobe flashes the room; sharp is how finely the screen is drawn.
# Everything else can be laid on a picture. The gyroid and the fractal replace the picture with a flight through it,
# which is not legible on a shard of the swarm: they can be set by hand but the director does not give them to images.
IMAGE = tuple(key for key in POST if key not in ("fluid", "coral", "mosh", "sort", "slit", "echo", "bokeh", "strobe"))
IMAGE_DIRECTED = tuple(key for key in IMAGE if key not in ("gyroid", "fractal"))
IMAGE_RANGES = {"image:" + key: RANGES[key] for key in IMAGE}
IMAGE_MOST = 0.6                    # how far the director turns an effect on the pictures: they must stay legible
IMAGE_AT_ONCE = 2


def image_chain(look, least=0.004):
    """The passes each picture needs for this look, in order: [(effect, amount)] for the image target's effects that
    are turned up at all."""
    return [(key, float(look.get("image:" + key, 0.0))) for key in IMAGE if look.get("image:" + key, 0.0) > least]


def image_from_beat(text, heat=1.0, screen=()):
    """The effects the director lays on each picture for a beat: {effect: amount}, two at most, none of those already
    on the screen (`screen`), gentler than the screen's. Read from what the beat is about, as from_beat is; a beat
    that names nothing gets one quiet effect for its heat (none at all when calm)."""
    seen = [word.strip(".,;:!?\"'()") for word in str(text).lower().split()]
    push = min(max(float(heat), 0.0), 2.0) / 2.0
    scores = {}
    for key in IMAGE_DIRECTED:
        if key in screen or key not in READ:
            continue
        count = sum(seen.count(word) for word in READ[key].split())
        if count:
            scores[key] = count
    if not scores:
        if push < 0.4:
            return {}
        return {"halftone": 0.35} if push < 0.7 else {"shatter": 0.4, "glitch": 0.35}
    chosen = sorted(scores, key=lambda key: (-scores[key], KEYS.index(key)))[:IMAGE_AT_ONCE]
    return one_heavy({key: round(min(0.25 + 0.35 * push + 0.08 * (scores[key] - 1), IMAGE_MOST, MOST.get(key, 1.0)), 2) for key in chosen})


def image_directed(chosen):
    """Where every effect the director has on the pictures should stand: {"image:<effect>": amount}, the rest at nothing."""
    return {"image:" + key: float(chosen.get(key, 0.0)) for key in IMAGE_DIRECTED}


def image_typed(text):
    """What "!image bloom 0.8 edges 0.4" asks for: ({effect: amount}, [names that are not effects for pictures]).
    A bare name is 0.6; amounts may be 0 to 1, 0 to 100, or a word (light, strong, full), as for named()."""
    words = {"light": 0.3, "slight": 0.3, "low": 0.3, "some": 0.5, "medium": 0.5, "strong": 0.8, "high": 0.8, "heavy": 0.8, "full": 1.0,
             "off": 0.0, "none": 0.0}
    out, refused, key = {}, [], None
    for bit in str(text).lower().replace(",", " ").replace("=", " ").split():
        if bit in IMAGE:
            key = bit
            out[key] = 0.6
        elif bit in KEYS:
            refused.append(bit)
            key = None
        elif key is not None:
            if bit in words:
                out[key] = words[bit]
            else:
                try:
                    amount = float(bit.rstrip("%"))
                    out[key] = amount / 100.0 if amount > 1.0 else amount
                except ValueError:
                    continue
            low, high = RANGES[key]
            out[key] = round(min(max(out[key], low), high), 3)
            key = None
    return out, refused


def picture_seed(name):
    """A number of the picture's own (0 to 2**32), from whatever names it (its number on the shelf, or its texture)."""
    return zlib.crc32(str(name).encode("utf-8")) & 0xFFFFFFFF


def _share(seed, key, salt):
    return (zlib.crc32(f"{seed}:{key}:{salt}".encode("utf-8")) & 0xFFFF) / 65535.0


def for_picture(steps, seed, vary=True):
    """One picture's own chain, from the image target's [(effect, amount)]: so that the pictures on screen do not all
    look alike. Varied (the director's look), each picture keeps each effect with a chance of two in three (always at
    least one: the one it is most drawn to) and turns it to between 55% and 100% of the amount; its time and its
    beat are offset too (see time_offset). Not varied (set by hand), every picture has exactly what was set."""
    if not vary or not steps:
        return list(steps)
    draw = {key: _share(seed, key, "keep") for key, _ in steps}
    first = min(draw, key=draw.get)
    return [(key, round(amount * (0.55 + 0.45 * _share(seed, key, "amount")), 3)) for key, amount in steps if key == first or draw[key] < 0.67]


def time_offset(seed):
    """How far a picture's own clock is from the screen's (seconds), and its beat (whole beats, so it stays on the
    beat): ripples, cells, glitches and colour bands then fall differently on each picture."""
    return 97.0 * _share(seed, "t", "time"), float(int(8 * _share(seed, "beat", "beat")))
