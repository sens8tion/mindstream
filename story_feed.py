"""story-feed: a story that writes itself on llama, steered by what you type. Nothing is saved.

You type a guide; the model on llama writes the story one short beat at a time. For each beat
a second pass (same model, different instructions) writes an image prompt, and optionally a
video prompt. Type more lines at any time to steer what comes next.

Instructions come from three editable files: prompts/story.md, prompts/image.md, prompts/video.md.

While llama is away (not connected yet, busy with another session, or not answering) the session carries on in
a plainer way: the guide and whatever is typed about the story become beats with pictures of their own, and a
film can be made between them, all put together here by mindstream/prompts.py. llama takes the story up from
there when it is back.

With --prompts structured, llama does not write the image and video prompts out in full. It fills in a short
card (prompts/card.md, prompts/film_card.md) and mindstream/prompts.py writes the prompts around it, keeping
the story's people the same from one picture and film to the next. --prompts inline asks for the card in the
same reply as the beat.

Output  one JSON object per line on stdout:
        {"type": "story", "seq": 1, "text": "..."}
        {"type": "prompt", "target": "image", "seq": 1, "prompt": "..."}
        {"type": "prompt", "target": "video", "seq": 1, "prompt": "..."}      (with --video)
Status  goes to stderr. The story itself is not echoed to the terminal unless you pass --echo.
"""
import argparse
import copy
import json
import os
import queue
import re
import signal
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import steer_intent  # noqa: E402  (the tag vocabulary; its model is only loaded by its own process)
from mindstream.local import pick  # noqa: E402
from mindstream.ollama import ApiError, Ollama  # noqa: E402
from mindstream import effects
from mindstream.effects import RANGES as EFFECT_RANGES
from mindstream.parts import (PARTS, apply_op, bring_in, change as change_part, chop_in, describe_op, drop_in, fresh, knob_in, parts_in, sanitize, set_names,  # noqa: E402
                              steps_in, summary, when_in)
from mindstream.resets import KINDS, resets_in  # noqa: E402
from mindstream.soundwords import layer_name, pull_in, sort_request  # noqa: E402
from mindstream.styles import STYLES as MUSIC_STYLES, find_style, menu as styles_menu, style_line  # noqa: E402
from mindstream.prompts import AGE_WORDS, CARD, GENDER_WORDS, Notebook, read_slots, split_beat, strip_fence  # noqa: E402
from mindstream.score import clean_score, describe, differs, parse_key, score_from_words  # noqa: E402

PROMPTS = os.path.join(HERE, "prompts")
# Defaults: the story model chosen in models.local.json, and the prompt guides kept in the user's guides folder.
# Both can be changed per run (--model, --image-md) or for good with these environment variables.
DEFAULT_MODEL = os.environ.get("MINDSTREAM_MODEL") or pick("story_model")
# The user's own guides for the picture model and the film model, used in place of prompts/ when they exist
# ("picture_guide" and "film_guide" in models.local.json).
USER_PICTURE_GUIDE = pick("picture_guide", "~/guides/picture.md")
USER_FILM_GUIDE = pick("film_guide", "~/guides/film.md")
DEFAULT_VIDEO_MD = os.environ.get("MINDSTREAM_VIDEO_MD",
                                  USER_FILM_GUIDE if os.path.exists(USER_FILM_GUIDE) else os.path.join(PROMPTS, "video.md"))
DEFAULT_IMAGE_MD = os.environ.get("MINDSTREAM_IMAGE_MD",
                                  USER_PICTURE_GUIDE if os.path.exists(USER_PICTURE_GUIDE) else os.path.join(PROMPTS, "image.md"))


QUIET = False   # set by --quiet: the launcher shows progress in the viewer, so the terminal stays clear for typing


HUSH = False    # set by --hush: nothing at all on the terminal; everything is told in the viewer instead


def say(msg, always=False):
    if (always or not QUIET) and not HUSH:
        print(f"[story-feed] {msg}", file=sys.stderr, flush=True)


def ask(label):
    """A visible prompt for typed input (only when a person is at the keyboard)."""
    if sys.stdin.isatty() and not HUSH:
        print(label, end="", file=sys.stderr, flush=True)


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().strip()


def read_line():
    raw = sys.stdin.buffer.readline()
    if not raw:
        return None
    try:
        return raw.decode("utf-8-sig").strip()
    except UnicodeDecodeError:
        return raw.decode(sys.stdin.encoding or "utf-8", errors="replace").strip()


# What the visual director may set, with the allowed range of each (see prompts/visual.md).
VISUAL_RANGES = {"chaos": (0.0, 2.0), "bpm": (40.0, 300.0), "calm": (1.0, 10.0), "wild": (3.0, 30.0), "folds": (0.0, 9.0),
                 "trails": (0.0, 1.0), "swarm": (0.0, 1.0), "split": (0.0, 2.0), "spin": (0.0, 3.0), "zoom": (-1.0, 1.0)}
VISUAL_RANGES.update(EFFECT_RANGES)          # the effects on the picture: "!bloom 0.8 rays 0.5" (mindstream/effects.py)
VISUAL_SHAPES = ("sphere", "torus", "ribbon", "any")


def clean_visual(raw):
    """Keep only known settings, clamped to their ranges."""
    look = {}
    for key, (low, high) in VISUAL_RANGES.items():
        try:
            look[key] = round(min(max(float(raw[key]), low), high), 3)
        except (KeyError, TypeError, ValueError):
            pass
    if str(raw.get("shape", "")).lower() in VISUAL_SHAPES:
        look["shape"] = str(raw["shape"]).lower()
    tint = str(raw.get("tint", ""))
    if len(tint) == 7 and tint[0] == "#" and all(c in "0123456789abcdefABCDEF" for c in tint[1:]):
        look["tint"] = tint.lower()
    look.update(clean_score(raw))          # the music: style, key, swing, sub, twinkle, rescore, break
    why = " ".join(str(raw.get("why", "")).split())[:200]
    if why:
        look["why"] = why                      # the director's own reason, shown to the viewer
    return look


def parse_visual(reply):
    """The first JSON object in the model's reply, cleaned; {} if there is none."""
    start, end = reply.find("{"), reply.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        raw = json.loads(reply[start:end + 1])
    except ValueError:
        return {}
    return clean_visual(raw) if isinstance(raw, dict) else {}


def parse_visual_words(text):
    """'chaos 1.6 bpm 140 shape torus' typed by hand."""
    words = text.replace("=", " ").split()
    alone = [w for w in words if w.lower() == "rescore"]            # "!rescore" takes no value
    words = [w for w in words if w.lower() != "rescore"]
    return clean_visual({**dict(zip(words[0::2], words[1::2])), **({"rescore": "true"} if alone else {})})


MAX_FILM_SECONDS = 3.0     # films are short: longer ones take minutes to write and to make
RETRY_SECONDS = 20.0       # how often llama is tried again while it cannot be reached or is busy with someone else


def word_budget(seconds):
    """How many spoken or sung words fit in a segment. The film model speaks slowly: a five-second clip got five words out."""
    return max(2, round(seconds))


def check_video_prompt(prompt, bpm, seconds=0.0):
    """What a film prompt is missing. Under-specified voices come out garbled, so this is strict."""
    problems = []
    for label in ("integrated_multimodal_description:", "overall_soundscape:", "non_diegetic_music:"):
        if label not in prompt:
            problems.append(f"the '{label}' field")
    speech = re.findall(r"<d>(.*?)</d>", prompt, re.S)
    if not speech:
        problems.append("any spoken or sung line inside <d>...</d>")
    elif any(not re.match(r"\s*[a-z]{2}\s+\S", s) for s in speech):
        problems.append("a language tag (such as en) at the start of every <d> line")
    said = sum(len(s.split()) - 1 for s in speech)     # the language tag is not a word
    if seconds and said > word_budget(seconds) + 1:
        problems.append(f"brevity: {said} words are spoken or sung but only {word_budget(seconds)} fit in "
                        f"{seconds:g} seconds, so the last line would be cut off. Use at most {word_budget(seconds)} words in total")
    ids = re.findall(r"\(S\d+\)", prompt)
    if speech and not ids:
        problems.append("speaker IDs such as (S1) before each line")
    for sid in dict.fromkeys(ids):                      # each speaker, at their first appearance
        start = prompt.find(sid)
        intro = prompt[start:prompt.find("<d>", start) if "<d>" in prompt[start:] else start + 300][:300]
        if not AGE_WORDS.search(intro) or not GENDER_WORDS.search(intro):
            problems.append(f"the age and gender of {sid} where they first speak")
    music = prompt.split("non_diegetic_music:", 1)[-1] if "non_diegetic_music:" in prompt else ""
    if music and not re.search(rf"\b{round(bpm)}\s*BPM\b", music, re.I):
        problems.append(f"the tempo 'at {round(bpm)} BPM' in non_diegetic_music")
    return problems


class SteerReader:
    """The small model that reads steers (steer_intent.py), in its own process on the CPU. If it is missing,
    still loading or slow, `read` returns None and the plain keyword reading is used instead."""

    def __init__(self):
        self.proc, self.ready, self.lock = None, threading.Event(), threading.Lock()
        python = os.environ.get("MINDSTREAM_GL_PYTHON", os.path.join(HERE, ".venv-dml", "Scripts", "python.exe"))
        if not os.path.exists(python):
            return
        try:
            self.proc = subprocess.Popen([python, "-B", os.path.join(HERE, "steer_intent.py"), "serve"],
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except OSError:
            return
        threading.Thread(target=self._wait, daemon=True).start()

    def _wait(self):
        try:
            if json.loads(self.proc.stdout.readline()).get("ready"):
                self.ready.set()
        except (ValueError, OSError, AttributeError):
            pass

    def read(self, steer, now, timeout=8.0, kind="steer"):
        if self.proc is None or not self.ready.is_set() or self.proc.poll() is not None:
            return None
        with self.lock:
            got = []

            def ask_it():
                try:
                    self.proc.stdin.write((json.dumps({kind: steer, "now": now}) + "\n").encode())
                    self.proc.stdin.flush()
                    got.append(json.loads(self.proc.stdout.readline()))
                except (ValueError, OSError):
                    pass
            worker = threading.Thread(target=ask_it, daemon=True)
            worker.start()
            worker.join(timeout)
            if worker.is_alive():           # too slow: stop asking it, the answers would arrive out of step
                self.ready.clear()
                return None
            return got[0] if got and "tags" in got[0] else None


# llama as director, the quick way: it answers with tags (see steer_intent.TAGS) and one sentence of reason.
TAG_DIRECTOR = (steer_intent.SCENE + """

After the tags, on a second line, write "why:" and one short plain sentence, at most 16 words, saying what in the beat made you choose them.
If a real-world sound belongs in this beat (rain, a train, a crowd, a door), you may add a third line "sound:" with two to four plain words for it.
You also have the effects laid over the picture. On a line "fx:" name up to three that suit this beat, each with an amount from 0 to 1, or write "fx: none". The effects: """ + ", ".join(f"{key} ({about})" for key, _, _, _, _, _, about in effects.EFFECTS if key in effects.DIRECTED) + """. Nothing else.
Example reply:
dark, much-calmer, more-sub, cold-light
why: Something vast stirs under the ice, so everything hushes and the bass swells.
sound: ice cracking wind
fx: shatter 0.6, flow 0.4""")

# Structured prompts: what llama is told when it fills in a shot card on its own, and when the card follows the beat.
CARD_ALONE = ("You are given one beat of a story, the Cast so far, and sometimes a Steer (the viewer's own instruction, which "
              "outweighs the beat). \"Before\" is the card of the beat before: use it to tell who \"she\" or \"they\" are, and "
              "what \"same\" would mean. Reply with this beat's shot card and nothing else.\n\n")
CARD_WITH_BEAT = ("\n\nEvery reply is two things: the beat, then a blank line, then that beat's shot card. The card is read by "
                  "code and is not part of the story; this takes the place of \"and nothing else\" above.\n\n")

ALIGNMENT = ("For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced. "
             "At the final moment of the target video, <Picture 2> (from the last shot) is fully referenced.")


# "make me a bossa nova dance to chop, with words too", "!sample ...": a one-bar clip made to be chopped
SAMPLE_ASKED = re.compile(r"^\s*(?:!\s*(?:sample|chop|loop)\b\s*(?P<bare>.*)|(?P<said>(?:(?:please|now|ok|okay|can you|could you)[ ,]+)*"
                          r"(?:make|give|render|film|shoot|get|do|cook)\s+(?:me\s+|us\s+)?(?:up\s+)?(?:a|an|some|another)\b.*"
                          r"\b(?:to chop|chop(?:ping|ped)?|sample|loop|sound ?track)\b.*))$", re.I)
# "the words should be ...", "words: ...", "invent some words", "!words ...": the same clip again with these words
WORDS_ASKED = re.compile(r"^\s*(?:!\s*words\b|(?:the\s+)?(?:words|lyrics?)\s*(?:should be|are|:|=)|"
                         r"(?P<invent>(?:invent|make up|write|new|different|other)\s+(?:some\s+|new\s+|the\s+)?(?:words|lyrics?)))\s*(?P<words>.*)$", re.I)

# how the sample layers are chopped, and the part each layer plays: the names are mindstream/chopper.py's STYLES and
# ROLES, written out here because the feed does not load the music engine (the viewer checks them again)
CHOP_STYLES = ("jungle", "atmospheric", "drumfunk", "techstep", "breakcore", "footwork")
CHOP_ROLES = ("anchor", "carrier", "colour", "hook", "stab", "bed")


def chop_typed(line):
    """'!chop drumfunk' -> {"chop_style": "drumfunk"}; '!role rain hook' -> {"role": {"layer": "rain", "role": "hook"}},
    and '!role rain auto' -> role None (the engine chooses it again). Anything else -> None: "!chop" with other words
    still asks for a clip to chop (SAMPLE_ASKED)."""
    typed = str(line).strip().lower().split()
    if len(typed) == 2 and typed[0] == "!chop" and typed[1] in CHOP_STYLES:
        return {"chop_style": typed[1]}
    if len(typed) == 3 and typed[2] == "color":
        typed[2] = "colour"
    if len(typed) == 3 and typed[0] == "!role" and re.fullmatch(r"[a-z0-9]{1,16}", typed[1]) and typed[2] in CHOP_ROLES + ("auto",):
        return {"role": {"layer": typed[1], "role": None if typed[2] == "auto" else typed[2]}}
    return None


# the two dials for the edge (mindstream/edge.py DIALS): written out here, as the chop's names are
EDGE_DIALS = {"lock": "lock", "derange": "derange", "derangement": "derange"}


def _share(word):
    """'0.7' or '70' -> 0.7; anything else, or outside 0..100, -> None."""
    try:
        value = float(word.rstrip("%"))
    except ValueError:
        return None
    if value != value or value < 0 or value > 100:
        return None
    return round(value / 100.0 if value > 1 else value, 3)


def edge_typed(line):
    """The edge and the roller, typed:
        '!edge lock 0.7'       -> {"edge": {"lock": 0.7}}       locked 0 .. restless 1 (0..100 is read as a percentage)
        '!edge derange 0.3'    -> {"edge": {"derange": 0.3}}    composed 0 .. deranged 1
        '!edge auto'           -> {"edge": {"auto": True}}      the dials are the session's again
        '!edge lip lock 0.6'   -> {"edge": {"lip": {"lock": 0.6}}}     where that dial's lip sits, by ear
        '!roller 16'           -> {"roller": 16}                bars a riff is held before it changes, 2 .. 32
    Anything else -> None."""
    typed = str(line).strip().lower().split()
    if len(typed) == 2 and typed[0] == "!roller":
        try:
            bars = float(typed[1])
        except ValueError:
            return None
        return {"roller": int(min(max(round(bars), 2), 32))} if bars == bars else None
    if not typed or typed[0] != "!edge":
        return None
    if typed[1:] == ["auto"]:
        return {"edge": {"auto": True}}
    if len(typed) == 3 and typed[1] in EDGE_DIALS and _share(typed[2]) is not None:
        return {"edge": {EDGE_DIALS[typed[1]]: _share(typed[2])}}
    if len(typed) == 4 and typed[1] == "lip" and typed[2] in EDGE_DIALS and _share(typed[3]) is not None:
        return {"edge": {"lip": {EDGE_DIALS[typed[2]]: _share(typed[3])}}}
    return None


def edge_said(typed):
    """What edge_typed's answer is, in a few words, for the person who typed it."""
    if "roller" in typed:
        bars = typed["roller"]
        return f"roller: riffs held {bars} bars" + (" (a roller)" if bars >= 32 else " (a switch-up)" if bars <= 4 else "")
    edge = typed["edge"]
    if edge.get("auto"):
        return "edge: the session moves the dials again"
    if "lip" in edge:
        return "edge: " + ", ".join(f"{dial}'s lip at {at:g}" for dial, at in edge["lip"].items())
    return "edge: " + ", ".join(f"{dial} {at:g}" for dial, at in edge.items()) + " (yours until !edge auto)"


def length_first(text, bpm):
    """'2s a dancer', '4 beats a dancer', '1 bar a dancer' -> (seconds or None, 'a dancer'): a length given before the words."""
    found = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(s|sec|secs|seconds?|beats?|bars?)\b[ ,:]*(.*)$", text, re.I)
    if not found:
        return None, text
    amount, unit = float(found.group(1)), found.group(2).lower()
    seconds = amount * 240.0 / bpm if unit.startswith("bar") else amount * 60.0 / bpm if unit.startswith("beat") else amount
    return seconds, found.group(3)


def mend_video_prompt(prompt, bpm, seconds, pictures=True):
    """Put right, in code, what a film prompt lacks: the three labelled fields, the tempo, a language tag on
    every spoken line, a speaker ID, and lines short enough to be said in the time. Returns (prompt, what was
    mended). Nothing is sent back to the model."""
    mended = []
    if "integrated_multimodal_description:" not in prompt:
        prompt = "integrated_multimodal_description: " + prompt.strip()
        mended.append("description label")
    if "overall_soundscape:" not in prompt:
        prompt = prompt.rstrip() + "\noverall_soundscape: The natural sounds of the place and of what is done in it."
        mended.append("soundscape")
    if "non_diegetic_music:" not in prompt:
        prompt = prompt.rstrip() + f"\nnon_diegetic_music: Music at {round(bpm)} BPM that carries the mood of the scene."
        mended.append("music")
    head, music = prompt.rsplit("non_diegetic_music:", 1)
    if not re.search(rf"\b{round(bpm)}\s*BPM\b", music, re.I):
        music = re.sub(r"\b\d{2,3}\s*BPM\b", f"{round(bpm)} BPM", music, flags=re.I) if re.search(r"\d{2,3}\s*BPM", music, re.I) \
            else f" At {round(bpm)} BPM." + music
        mended.append("tempo")
    prompt = head + "non_diegetic_music:" + music
    budget, used, fixed = word_budget(seconds) + 1, 0, {"tag": False, "cut": False, "id": False}

    def line(match):
        nonlocal used
        words = match.group(1).split()
        if not words:
            return match.group(0)
        if not re.fullmatch(r"[a-z]{2}", words[0]):
            words.insert(0, "en")
            fixed["tag"] = True
        room = max(budget - used, 2)
        if len(words) - 1 > room:
            words = words[:1 + room]
            fixed["cut"] = True
        used += len(words) - 1
        return "<d>" + " ".join(words) + "</d>"
    prompt = re.sub(r"<d>(.*?)</d>", line, prompt, flags=re.S)
    if "<d>" in prompt and not re.search(r"\(S\d+", prompt):
        prompt = re.sub(r"((?:says|sings|shouts|whispers|calls|chants)\s+)?<d>",
                        lambda m: "(S1) " + (m.group(1) or "says ") + "<d>", prompt, count=1)
        fixed["id"] = True
    mended += [name for key, name in (("tag", "language tag"), ("cut", "long line shortened"), ("id", "speaker ID")) if fixed[key]]
    if pictures and not prompt.lstrip().startswith("For the target video"):
        prompt = ALIGNMENT + "\n\n" + prompt.lstrip()
    elif not pictures and prompt.lstrip().startswith("For the target video"):      # no pictures are given to this film
        prompt = prompt.lstrip().split("\n", 1)[-1].lstrip()
    return prompt, mended


# words that make a typed line about the sound rather than the story (it is then not painted as a scene)
SOUNDISH = re.compile(r"\b(kick|snare|hats?|hi-?hats?|sub|bass|tune|riff|hook|melody|organ|synth|bells?|drones?|pads?|drums?|beat|rhythm|music\w*|"
                      r"sound\w*|instruments?|mix|volume|louder|quieter|delay|echo\w*|reverb|layers?|distort\w*|filter\w*|chorus|crush\w*|"
                      r"wobbl\w*|tremolo|tempo|bpm|groove|noise)\b", re.I)


class StopAsked(Exception):
    """Raised inside a reply that is still arriving, to abandon it: the session has been told to stop."""


def emit(obj):
    sys.stdout.buffer.write((json.dumps(obj, ensure_ascii=True) + "\n").encode("ascii"))
    sys.stdout.buffer.flush()


def main():
    ap = argparse.ArgumentParser(description="Ephemeral story feed from Ollama on llama (stdout stream, nothing saved)")
    ap.add_argument("-m", "--model", default=DEFAULT_MODEL)
    ap.add_argument("--host", default="llama", help="SSH host alias")
    ap.add_argument("--story-md", default=os.path.join(PROMPTS, "story.md"), help="instructions for the story writer")
    ap.add_argument("--image-md", default=DEFAULT_IMAGE_MD, help="instructions for the image prompt writer")
    ap.add_argument("--video-md", default=DEFAULT_VIDEO_MD, help="instructions for the video (journey) prompt writer")
    ap.add_argument("--video-seconds", type=float, default=1.5,
                    help="length of each film, told to the writer (never more than 3: a short film is quick to write and to make)")
    ap.add_argument("--bpm", type=float, default=120.0, help="music tempo until the visual director sets one")
    ap.add_argument("--video", action="store_true",
                    help="also write a journey prompt between each beat's picture and the next (for the video stage)")
    ap.add_argument("--no-image", action="store_true", help="do not write image prompts")
    ap.add_argument("--prompts", choices=["written", "structured", "inline"], default="written",
                    help="how picture and film prompts are made. written: llama writes each one out in full. structured: llama "
                         "fills in a short card and code writes the prompt round it, with the same people every time. inline: "
                         "as structured, with the card asked for in the same reply as the beat")
    ap.add_argument("--card-md", default=os.path.join(PROMPTS, "card.md"), help="the shot card llama fills in (structured prompts)")
    ap.add_argument("--film-card-md", default=os.path.join(PROMPTS, "film_card.md"), help="the film card llama fills in (structured prompts)")
    ap.add_argument("--interval", type=float, default=15.0, help="seconds per beat (match it to how fast images are made)")
    ap.add_argument("--beats", type=int, default=0, help="stop after this many beats (0 = until you stop it)")
    ap.add_argument("--memory", type=int, default=8, help="how many recent beats the writer is shown")
    ap.add_argument("--think", choices=["on", "off"], default="off", help="reasoning on thinking models")
    ap.add_argument("--echo", action="store_true", help="also show the story on the terminal as it is written")
    ap.add_argument("--keep-loaded", action="store_true", help="leave the model loaded on llama at exit")
    ap.add_argument("--no-restart", action="store_true", help="do not restart Ollama at exit (leaves the story in its memory)")
    ap.add_argument("--share", action="store_true",
                    help="start even if another session has a model loaded on llama (it may slow or evict theirs)")
    ap.add_argument("--visual-md", default=os.path.join(PROMPTS, "visual.md"), help="instructions for the visual director")
    ap.add_argument("--no-visual", action="store_true", help="do not ask the model to direct the visuals")
    ap.add_argument("--stop-handle", type=int, default=0, help=argparse.SUPPRESS)
    ap.add_argument("--director", choices=["tags", "local", "full"], default="tags",
                    help="how each beat's music and motion are scored. tags: llama picks a few tags and gives its reason "
                         "(about ten seconds). local: the small model on this machine picks them (two or three seconds, "
                         "cruder). full: llama sets every value itself (half a minute)")
    ap.add_argument("--cadence-now", type=float, default=0.0, help=argparse.SUPPRESS)   # the launcher's picture cadence at start
    ap.add_argument("--video-mode", default="off", help=argparse.SUPPRESS)      # the launcher's video mode: off, ask, interlude or reel
    ap.add_argument("--no-story-sounds", action="store_true",
                    help="the story may not ask for sounds (by default it may, one beat in three; see README, Samples)")
    ap.add_argument("--film-seconds", type=float, default=1.5, help="length of a film asked for with a bare !film")
    ap.add_argument("--journeys-on-demand", action="store_true",
                    help="write a film prompt only when asked for one (the launcher asks when it is ready to film)")
    ap.add_argument("--no-steer-model", action="store_true",
                    help="read steers by keywords only; do not load the small model that interprets them")
    ap.add_argument("--quiet", action="store_true", help="no progress messages on the terminal (errors still shown)")
    ap.add_argument("--hush", action="store_true",
                    help="nothing on the terminal at all, not even what was typed or how it was read: the viewer shows it")
    args = ap.parse_args()
    global QUIET, HUSH
    QUIET, HUSH = args.quiet, args.hush
    if not args.model:
        sys.exit('[story-feed] no story model chosen: set "story_model" in models.local.json, or pass --model')

    roles = {"story": read_text(args.story_md)}
    if not args.no_image:
        roles["image"] = read_text(args.image_md)
    if os.path.exists(args.video_md):
        roles["video"] = read_text(args.video_md)
    # The cast, the present scene and each beat's card, in memory only. Structured prompts are written from it, and
    # so are the plain prompts made, whatever the mode, while llama is away or busy.
    book, structured = Notebook(), args.prompts != "written"
    if structured:
        roles["card"], roles["film"] = read_text(args.card_md), read_text(args.film_card_md)
        if args.prompts == "inline":
            roles["story"] += CARD_WITH_BEAT + roles["card"]
    video_on = [bool(args.video)]          # journeys are written only while this is on; "!video ..." flips it
    video_now = threading.Event()          # "!video now": write the journey for the latest pair straight away
    pinned, pin_new = [None], threading.Event()    # "!bpm 178": the tempo set by hand; "!bpm auto" lets it go
    # structure: the style, the key, new riffs, a break. The session changes these seldom: once changed (by it or by
    # hand) they are left alone for this many bars, and the viewer makes each change on a four-bar line
    structure = {"bars": 8, "at": 0.0}
    # the super knob (which moves every part's knob with it) follows the story: the wilder the beat, the further it is
    # asked to go, up to half way. The viewer takes it there slowly, or at once when the scene changes. "!super hold"
    # leaves the knob to the hand alone; "!super auto" gives it back
    super_by = {"on": True, "said": None}
    # the effects on the picture are the director's too: every beat it says where each should stand (it may name them
    # itself; otherwise the beat is read for what it is about). "!fx hold" leaves them to the hand; "!fx auto" gives them back
    fx_by = {"on": True, "last": {}}
    # ... and the effects on each picture by itself (the "image" target: mindstream/effects.py), chosen apart from the
    # screen's. "!image hold" (or "!image off") leaves them to the hand; "!image auto" gives them back. last: what each
    # was given on the last beat, so the director changes them a step at a time (effects.paced)
    image_by = {"on": True, "last": {}}
    recalled_tempo = [None]                        # the tempo of a memory just gone back to: taken up at once, then free to drift as before
    music = {"style": "four", "key": "A minor", "bpm": float(args.bpm),    # the score as it stands, for the director
             "cadence": float(args.cadence_now)}

    progress = {"seq": 0}                  # the beat being written, or last written
    # Shared between the main loop and whoever is typing. While llama is away, something typed about the story is a
    # beat of its own, so the beats and their numbers cannot belong to the main loop alone.
    texts, numbering = [], threading.Lock()                    # every beat so far; one beat is numbered at a time
    ready, calling = threading.Event(), threading.Event()      # llama is connected and answering; it is in the middle of a reply
    painted, by_llama = [], {}             # beats a picture prompt has gone out for (0 is the guide); llama's own prompts among them
    told_beats = []                        # beats the viewer told while llama was away, which llama has not been shown yet
    last_steer = [""]                      # the last thing typed about the story: a film made without llama may speak it
    filmed, last_film = [0], [""]          # the last beat a film prompt went out for, and that prompt
    epoch, base = [0], [0]                 # how many times the story has been started afresh, and the beat it last began at
    kept = {}                              # "memorise 2": the story as it stood then, by number; in memory only, gone with the session
    returning = [False]                    # the beats waiting in told_beats were brought back by a recall, not told while llama was away
    joined = [-1]                          # the last beat a recall brought back: it has no picture of its own, so no film starts from it
    reader = None if args.no_steer_model else SteerReader()

    def tell(stream, text):
        """A plain sentence for the viewer: what was understood, what is about to happen, and why."""
        emit({"type": "read", "stream": stream, "text": text})

    def scored(look):
        """Remember how the sound and the motion were last set, whoever set them."""
        music.update({k: v for k, v in look.items() if k not in ("rescore", "break", "why", "pictures", "image") and not k.startswith("image:")})

    film_seconds = [None]                  # the length asked for with "!film"; None = the usual length

    def text_of(n):
        """The words behind picture n: a beat, or for 0 the guide."""
        return (guide_box[0] or "") if n == 0 else texts[n - 1]

    def paint(n, prompt, llama_wrote=False):
        """Send the picture prompt for beat n, and remember that it went and who wrote it."""
        painted[:] = [b for b in painted if b != n][-7:] + [n]      # noted before it is sent: a film asked for on seeing it must find it here
        emit({"type": "prompt", "target": "image", "seq": n, "prompt": prompt})
        by_llama.pop(n, None)
        if llama_wrote:
            by_llama[n] = prompt
        for old in [b for b in by_llama if b < n - 3]:
            del by_llama[old]

    def picture_for(n, lead=""):
        """The picture prompt for beat n, put together here: from its card if llama filled one in, otherwise in a
        plainer way from the beat's own words, the beat before and the guide. `lead` is something just typed,
        which goes first."""
        return book.picture(n, text_of(n), music, guide=guide_box[0] or "", lead=lead,
                            before=text_of(n - 1) if n >= 2 and n - 1 >= base[0] and n != base[0] else "",
                            written=by_llama.get(n, "") if lead else "")

    def start_afresh(theme):
        """A new theme. The story, the people in it and the pictures begin again from these words; nothing of what
        went before is carried over, and no film is made across the join. The music and the motion carry on."""
        with numbering:
            guide_box[0] = theme
            epoch[0] += 1
            texts.append(theme)                # the theme is a beat of its own: it has a number, a caption and a picture
            n = len(texts)
            base[0], progress["seq"] = n, n
            told_beats[:] = []
            returning[0] = False
            painted[:] = []
            by_llama.clear()
            filmed[0], last_film[0], last_steer[0] = n, "", ""
        book.__init__()                        # the cast and the remembered place and light belong to the old story
        while not steering.empty():
            steering.get()
        for name in list(film_names):          # the old films' sounds are no longer layers; pulled samples stay
            forget_layer(name)
        emit({"type": "control", "fresh": n})  # the launcher and the viewer let go of the old pictures and films
        emit({"type": "control", "theme": theme})     # the new theme as words on a card, until its first picture is painted
        emit({"type": "story", "seq": n, "text": theme})
        if "image" in roles:
            paint(n, picture_for(n))
        said = (f'Starting afresh: "{theme}". The story, its people and its pictures begin again from here'
                + (f", with picture {n} painted from your words now" if "image" in roles else "")
                + (". llama takes it up at its next beat." if ready.is_set() else ". llama takes it up when it is there."))
        tell("steer", said)
        say(said, always=True)

    def send_film(a, b, prompt, seconds, bpm, left=(), plain=""):
        """Send the film prompt from picture a to picture b, mended where it needs it, and tell the viewer."""
        prompt, mended = mend_video_prompt(prompt, bpm, seconds)
        mended += ["left to code: " + ", ".join(left)] if left else []
        last_film[0], filmed[0] = prompt, max(filmed[0], b)
        emit({"type": "prompt", "target": "video", "seq": b, "from": a, "to": b, "prompt": prompt,
              "bpm": round(bpm), "seconds": seconds, "name": f"film{b}"})
        know_layer(f"film{b}", film=True)
        gist = " ".join(prompt.split("integrated_multimodal_description:", 1)[-1].split("[Shot", 1)[0].split())[:150]
        lines = re.findall(r"<d>\s*[a-z]{2}\s+(.*?)</d>", prompt, re.S)
        tell("film", (f"The film from picture {a} to {b} was put together here without llama ({plain}), so it is plainer: a simple "
                      f"camera move, the sounds of the place and the music as it stands. " if plain
                      else f"The film from picture {a} to {b} is written. ") + f"{gist} "
             + (f'Heard in it: "{" ".join(lines[0].split())}". ' if lines else "Nobody speaks in it. " if plain else "")
             + f"Its music is asked for at {bpm:.0f} BPM; it is filmed when both pictures exist. It is shown once, then its sound "
               f'waits as the layer called "film{b}".'
             + (f" (Mended: {', '.join(mended)}.)" if mended else ""))

    def plain_film(why):
        """A film prompt made at once with nothing asked of llama, between the latest two pictures: what the two
        beats say, whoever of the cast is there, a simple camera move, the sounds of the place, and the music from
        the score. Something short the viewer has just typed about the story is spoken; otherwise nobody speaks.
        False if there are not yet two pictures to film between."""
        seqs = sorted(painted) if "image" in roles else list(range(len(texts) + 1))
        if len(seqs) < 2:
            said = ("A film runs from one picture to the next, and there is only one so far. Type something about the story: "
                    "it becomes the next picture, and then a film can be made.")
            tell("film", said)
            say(said, always=True)
            return False
        a, b = seqs[-2], seqs[-1]
        seconds, film_seconds[0] = min(film_seconds[0] or args.video_seconds, MAX_FILM_SECONDS), None
        bpm = float(pinned[0] or music["bpm"])
        line = last_steer[0] if 0 < len(last_steer[0].split()) <= word_budget(seconds) + 1 else ""
        if line:
            last_steer[0] = ""                 # said once
        prompt, _ = book.film(b, "", text_of(a), text_of(b), music, bpm, word_budget(seconds) + 1, start=a, line=line)
        send_film(a, b, ALIGNMENT + "\n\n" + prompt, seconds, bpm, plain=why)
        say(f"a film of {seconds:g} seconds from picture {a} to {b}, put together here without llama ({why})", always=True)
        return True

    def steer_beat(text):
        """While llama is away, something typed about the story is the story: the next beat, in the viewer's own
        words, with a picture of its own. Returns its number."""
        with numbering:
            texts.append(text)
            n = len(texts)
            progress["seq"] = n
            told_beats.append((n, text))
        emit({"type": "story", "seq": n, "text": text})
        book.take_card(n, "", text)
        if "image" in roles:
            paint(n, picture_for(n))
        return n

    def ask_film(words=""):
        """A film of the latest two pictures, now, of the length asked for: seconds, or beats or bars at the tempo."""
        found = re.search(r"(\d+(?:\.\d+)?)\s*(beats?|bars?|s|sec\w*)?", words.lower())
        amount = float(found.group(1)) if found else args.film_seconds
        unit = (found.group(2) or "s") if found else "s"
        seconds = amount * 60.0 / music["bpm"] * (4 if unit.startswith("bar") else 1) if unit.startswith("b") else amount
        seconds = round(min(max(seconds, 0.9), MAX_FILM_SECONDS), 2)
        film_seconds[0] = seconds
        video_on[0] = True
        if not ready.is_set() or calling.is_set():      # llama cannot be asked just now: a plainer film, put together here, at once
            if plain_film("llama is busy writing" if ready.is_set() else "llama is not there yet"):
                emit({"type": "control", "video": "now", "once": True})
            return
        video_now.set()
        emit({"type": "control", "video": "now", "once": True})
        nxt = max(progress["seq"], 2)
        said = (f"A film of {seconds:g} seconds" + (f" ({amount:g} {unit} at {music['bpm']:.0f} BPM)" if unit.startswith("b") else "")
                + f" from picture {nxt - 1} to {nxt} is next: llama writes its prompt, then it takes about {max(1, round(seconds))} "
                  f"minute{'s' if round(seconds) > 1 else ''} to make.")
        tell("film", said)
        say(said, always=True)

    reading = queue.Queue()                 # typed lines waiting for llama to work out what was meant: (text, state then, settled keys)
    sound_state = {part: fresh() for part in PARTS}     # how each part of the music has been told to sound, as far as the feed knows
    layer_names, film_names = [], []                    # the layers so far, by name: parts like any other; which of them are films' sounds
    clips_asked = [0]

    def forget_layer(name):
        for names in (layer_names, film_names):
            if name in names:
                names.remove(name)
        sound_state.pop(name, None)
        set_names(layer_names)

    def know_layer(name, film=False):
        """A pulled sample, or a film's sound, becomes a layer called `name`: from now on that name is read as a part
        ("make the rain darker", "bring in the film4")."""
        if name not in layer_names:
            layer_names.append(name)
            if film:
                film_names.append(name)
            # as in the mixer: four films' sounds and six pulled samples at most, the oldest of each making way
            for gone in film_names[:-4] + [n for n in layer_names if n not in film_names][:-6]:
                forget_layer(gone)
        sound_state[name] = fresh()
        set_names(layer_names)

    def enact_change(change, now):
        """Put a change to the show into effect now; returns it as phrases a person can read."""
        change = dict(change)
        if change.get("pictures"):
            change.update(steer_intent.apply(["pictures-" + change["pictures"]], now))
        change.pop("pictures", None)
        if not change:
            return []
        if "cadence" in change:                                   # how often pictures come is the launcher's to change
            emit({"type": "control", "cadence": change["cadence"]})
        if "bpm" in change:
            pinned[0] = change["bpm"]
            pin_new.set()
        parts = describe(change, now)
        typed_score(change)
        emit({"type": "visual", "seq": 0, **change})
        return parts

    samples = queue.Queue()                 # clips asked for to chop, waiting for llama: (request, words, seconds, bpm)
    last_sample = [""]

    def send_sample(prompt, seconds, bpm, how):
        """A one-bar clip to chop: filmed from words alone (no story pictures are pinned to it), as soon as it can be."""
        prompt, mended = mend_video_prompt(prompt, bpm, seconds, pictures=False)
        n = max(painted) if painted else progress["seq"]
        name = layer_name(last_sample[0])
        if name == "sample":                    # nothing telling in what was asked: clip1, clip2 ...
            clips_asked[0] += 1
            name = f"clip{clips_asked[0]}"
        emit({"type": "prompt", "target": "video", "seq": n, "from": n, "to": n, "prompt": prompt, "bpm": round(bpm),
              "seconds": seconds, "free": True, "name": name})
        know_layer(name, film=True)
        emit({"type": "control", "video": "now", "once": True})
        gist = " ".join(prompt.split("integrated_multimodal_description:", 1)[-1].split("[Shot", 1)[0].split())[:140]
        lines = re.findall(r"<d>\s*[a-z]{2}\s+(.*?)</d>", prompt, re.S)
        music_said = " ".join(prompt.split("non_diegetic_music:", 1)[-1].split())[:110]
        tell("film", f"A clip to chop, {seconds:g} seconds (one bar at {bpm:.0f} BPM), {how}. {gist} "
             + (f'Words: "{" ".join(lines[0].split())}". ' if lines else "No words. ") + f"Music: {music_said}... "
             + f'It is filmed next and takes a minute or two. It is shown once, straight through; then its sound waits, cut at its obvious '
               f'transients, as the layer called "{name}": say "bring in the {name}". The tune plays on its sound.')

    def plain_sample(request, words, seconds, bpm, why):
        """The clip's prompt put together here, with nothing asked of llama."""
        style = find_style(request)
        music_text = (style_line(style, bpm) if style else book_music(bpm)) + " One bar that loops."
        said = re.search(r'"([^"]+)"', words or request)
        line = " ".join((said.group(1) if said else "").split()[:word_budget(seconds) + 1])
        voice = f" (S1), a singer, a woman in her thirties, on screen, low warm voice, sings, <d>en {line}</d>" if line else ""
        scene = re.sub(r"^(?:please\s+)?(?:make|give|render|film|shoot|get|do)\s+(?:me\s+|us\s+)?", "", request.strip(), flags=re.I)
        scene = re.split(r"\b(?:to chop|for the sound ?track|with words|and words)\b", scene, flags=re.I)[0].strip(" ,.") or "a dancer"
        send_sample(f"integrated_multimodal_description: {scene[0].upper() + scene[1:]}, moving on every beat. [Shot 1] The camera holds still as "
                    f"the movement lands on each beat.{voice}\noverall_soundscape: Feet and hands landing on each beat.\n"
                    f"non_diegetic_music: {music_text}", seconds, bpm, f"put together here without llama ({why}), so it is plainer")

    def book_music(bpm):
        from mindstream.prompts import music_line
        return music_line(music, bpm)

    def ask_sample(request, words="", length=None):
        """A clip to chop, asked for in the viewer's own words: the picture, the sound track and some words. One bar
        long unless a length is given (three seconds at most)."""
        bpm = float(pinned[0] or music["bpm"])
        seconds = round(min(max(length or 240.0 / bpm, 0.9), MAX_FILM_SECONDS), 2)
        last_sample[0] = request
        if not ready.is_set() or "sample" not in roles:
            plain_sample(request, words, seconds, bpm, "llama is not there yet")
            return
        samples.put((request, words, seconds, bpm))
        heard = (f'You asked for a clip to chop: "{request}"' + (f', with the words: {words}' if words else "") + f". {'One bar, ' if not length else ''}{seconds:g} seconds "
                 f"at {bpm:.0f} BPM. llama writes its prompt next, between its other jobs; then it takes a minute or two to film.")
        tell("film", heard)
        say(heard, always=True)

    story_sound = [-10]                     # the beat the story last asked for a sound at: it may ask one beat in three
    video_mode = [args.video_mode]

    def story_wants_sound(text):
        """The story has named a sound it wants. It is written by a language model and may ask for anything; an
        archive logs whatever it is sent. So only a request made wholly of plain sound words is asked of an archive.
        Anything else is never sent anywhere: it is made here, as a clip to chop, or left for the viewer to ask for."""
        what, query = sort_request(text)
        if what == "ask":
            name = layer_name(query)
            emit({"type": "control", "pull": {"query": query, "role": "texture", "where": "any", "name": name}})
            know_layer(name)
            tell("sound", f'The story asked for the sound of "{query}": looking for it in your library and the archives. '
                          f'If it is found it waits as the layer called "{name}": say "bring in the {name}".')
        elif what == "make" and video_mode[0] in ("interlude", "reel"):
            ask_sample(f"the sound of {query}, with nobody speaking", "no words")
            tell("sound", f'The story asked for a sound that is not for an archive ("{query[:60]}"), so it is being made here, as a clip to chop.')
        elif what == "make":
            tell("sound", f'The story wanted a sound that is not for an archive ("{query[:60]}"). Nothing was sent. Say "!sample {query[:40]}" '
                          "to have it made here.")

    def take_steer(text):
        """What a steer means for the sound and the motion: applied as soon as it is known, and told back
        with what will follow from it."""
        now = dict(music)
        if re.search(r"\b(film|video|clip) (this|it|that|now)\b|\b(make|shoot|give me) a (short |quick )?(film|video|clip)\b", text.lower()):
            ask_film()
        # "with the flow" (or "gradually", "ease it in", a leading ~): nothing jumps now; the next beat brings it in
        flowing = bool(re.search(r"^\s*~|\bwith the flow\b|\bgradual\w*|\bease (it|into)\b|\bslowly bring\b|\bover time\b|\bnext beat\b", text.lower()))
        if flowing:
            said = f'You said "{text}". Nothing jumps: beat {progress["seq"] + 1} of the story brings it in, and its music and motion with it.'
            tell("steer", said)
            say(said, always=True)
            return
        nxt = progress["seq"] + 1
        after = (f"Beat {nxt} of the story takes it in next, then picture {nxt}"
                 + (f", then the film from {nxt - 1} to {nxt}" if video_on[0] and nxt >= 2 else "") + ".")

        enact = lambda change: enact_change(change, now)      # noqa: E731

        # 1. At once, as fast as a ! command: whatever the plain words plainly ask for.
        words = score_from_words(text, music["bpm"], parse_key(music["key"]) or ("a", "minor"))
        done_now = enact(words)
        tell("steer", f'You said "{text}". ' + ("Now: " + "; ".join(done_now) + ". " if done_now else "Reading it... "))
        # 2. A second or two later, the small model's closer reading adds what the plain words did not cover.
        #    Its changes are worked out from how things stood before step 1, and never undo or repeat that step.
        asked_llama = ready.is_set() and "sound" in roles
        if asked_llama:                 # llama works out the rest, between its other jobs; it is applied when it answers
            reading.put((text, now, set(words)))
        got = reader.read(text, now) if reader and not asked_llama else None
        more, tags = [], []
        if got is not None:
            tags = got.get("tags") or []
            extra = {k: v for k, v in (got.get("changes") or {}).items() if k not in words and not (k == "cadence" and "pictures" in words)}
            if set(extra) == {"rescore"} and words.get("rescore"):
                extra = {}
            more = enact(extra)
        sounds = [tuple(p) for p in (got.get("parts") or [])] if got is not None else []
        if sounds:                                                    # the small model heard something about how a part sounds
            for part, word in sounds:
                change_part(sound_state[part], word)
            emit({"type": "visual", "seq": 0, "parts": sounds})
            more += [f"the {part}: {word}" for part, word in sounds]
            tags = tags + [" ".join(p) for p in sounds]
        looser = [kind for tag, kind in (("replace-pictures", "pictures"), ("restart-story", "story"), ("rebuild-music", "music"))
                  if tag in tags]
        if looser:                                                    # the small model heard a "do it again" the patterns missed
            do_resets(looser)
        story_only = not done_now and not more and not tags and not (asked_llama and SOUNDISH.search(text))
        own = 0
        if story_only:                                                # nothing for the sound or motion: let the picture answer now
            last_steer[0] = text
            if not ready.is_set():                                    # llama is away: this is the next beat, with its own picture
                own = steer_beat(text)
            else:                                                     # the present scene again, with this leading it
                now_at = painted[-1] if painted else None
                emit({"type": "control", "picture_now": text, **({"prompt": picture_for(now_at, lead=text)} if now_at is not None else {})})
        parts = done_now + more
        heard = (f'You said "{text}". ' + ("Now: " + "; ".join(parts) + ". " if parts else
                                           "Now: a new picture of the present scene with this in it. " if story_only else "")
                 + ("llama is working out the rest of what you meant; it answers between its other jobs. " if asked_llama else "")
                 + after)
        if own:
            heard = (f'You said "{text}". llama is away, so that is beat {own} of the story, in your own words'
                     + (f", and picture {own} is being painted from it" if "image" in roles else "")
                     + ". llama carries on from it when it is back.")
        tell("steer", heard)
        how = (f"words at once; closer reading in {got.get('seconds', 0):.1f}s: {', '.join(tags) or 'story only'}" if got is not None
               else "words at once; llama reads the rest" if asked_llama else "read by keywords; the small model is not ready")
        say(f"{heard}  ({how})", always=True)

    held = {}      # music settings the viewer typed: the director may not change them for the next three beats

    # ---- doing things again from scratch, when asked: "replace all of the pics", "start the theme again",
    #      "rebuild the musical intent", "reset the look", "redo everything" (mindstream/resets.py reads the phrases)

    def repaint_all():
        """New pictures for where the story is now: the latest two beats are painted again, and the viewer lets the
        older ones go."""
        emit({"type": "control", "repaint": True})
        again = sorted(painted)[-2:]
        for n in again:
            paint(n, by_llama.get(n) or picture_for(n), llama_wrote=n in by_llama)
        return ("the pictures are replaced: " + (" and ".join(f"picture {n}" for n in again) + " painted again, the earlier ones let go"
                                                   if again else "the earlier ones are let go, and the next is painted new"))

    def rebuild_music():
        """The music worked out again from where the story is, as if hearing it for the first time: what was typed
        about it before no longer holds, the tempo is free to move, and the riffs are new."""
        for k in ("style", "key", "swing", "sub", "twinkle"):
            held.pop(k, None)
        pinned[0] = None
        fresh = {"style": "four", "key": "A minor", "sub": 0.8, "twinkle": 0.0}
        source = texts[-1] if texts else (guide_box[0] or "")
        got = reader.read(source, {**music, **fresh}, timeout=8.0, kind="beat") if reader and source else None
        if got is not None:
            read = steer_intent.apply([t for t in got.get("tags") or [] if t not in steer_intent.COLOURS], {**music, **fresh})
        else:
            read = score_from_words(source, music["bpm"], ("a", "minor"))
        change = {**fresh, **{k: v for k, v in read.items() if k in ("style", "key", "sub", "twinkle", "swing")}, "rescore": True}
        parts = describe(change, dict(music))
        scored(change)
        emit({"type": "visual", "seq": 0, **change})
        return "the music is worked out again from where the story is: " + ("; ".join(parts) if parts else "new riffs")

    def reset_look():
        """The motion back to how a session starts."""
        look = {"chaos": 1.0, "calm": 3.5, "wild": 9.0, "folds": -1.0, "trails": 0.75, "swarm": 0.8, "split": 1.0, "spin": 1.0,
                "zoom": 0.7, "shape": "any", "tint": "#ffffff"}
        for k in look:
            held.pop(k, None)
        scored(look)
        emit({"type": "visual", "seq": 0, **look})
        return "the motion and colour go back to how they began"

    def do_resets(kinds, said=""):
        done = []
        if "story" in kinds:
            if guide_box[0]:
                start_afresh(guide_box[0])     # the same theme, a new story; it tells the viewer itself
            kinds = [k for k in kinds if k not in ("story", "pictures")]      # starting again already replaces the pictures
        for kind in kinds:
            done.append({"pictures": repaint_all, "music": rebuild_music, "visuals": reset_look}[kind]())
        if done:
            heard = (f'You said "{said}". ' if said else "") + "Now: " + "; ".join(done) + "."
            tell("steer", heard)
            say(heard, always=True)

    def typed_score(change):
        scored(change)
        if any(k in change for k in ("style", "key", "rescore", "break")):
            structure["at"] = time.time()          # changed by hand: the session leaves the structure alone for a while
        for k in change:                       # sound and motion alike; the tempo has its own hold
            if k not in ("bpm", "rescore", "break", "why", "cadence", "pictures"):
                held[k] = [change[k], 3]
        if "bpm" in change:
            music["bpm"] = change["bpm"]
    if not args.no_visual and os.path.exists(args.visual_md):
        roles["visual"] = read_text(args.visual_md)
    if os.path.exists(os.path.join(PROMPTS, "sample.md")):
        roles["sample"] = read_text(os.path.join(PROMPTS, "sample.md"))    # how llama writes a one-bar clip to chop
    if os.path.exists(os.path.join(PROMPTS, "sound.md")):
        roles["sound"] = read_text(os.path.join(PROMPTS, "sound.md"))      # how llama reads a loosely worded instruction

    def status(kind, text, seq=0, detail=""):
        """Tell whoever is watching what llama is doing right now (drawn by the viewer)."""
        emit({"type": "status", "source": "llama", "kind": kind, "seq": seq, "text": text, "detail": detail})

    typed = sys.stdin.isatty()
    status("idle", "waiting for your guide")
    if typed:
        say("Type a guide for the story and press Enter. After that, type a line at any time to steer it; "
            "/bye stops. Nothing typed here is saved.", always=True)
    tell("steer", "Type what the story is about and press Enter, here or in the terminal.")
    ask("guide> ")
    # The first line typed is the guide, whichever window it is typed in: the terminal, or the viewer (which
    # sends it down the launcher's pipe). Both are listened to from the start; the story waits for that line.
    guide_box, got_guide = [None], threading.Event()

    unwatched = threading.Event()      # set while nobody is watching: nothing is written until it clears
    steering = queue.Queue()
    heard = queue.Queue()      # tempos measured in the generated soundtracks, sent by the launcher
    stop = threading.Event()

    # ---- "memorise" and "recall": the viewer keeps the music and its pictures under a number; the story is kept here

    def keep_story(slot, said=None):
        """Keep the story as it stands under a number: the guide, its latest beats, the cast and the scene, and what
        the feed knows of the music. `said` is the line as typed; None when the knob panel's button was pressed, in
        which case the launcher has already told the viewer."""
        if not guide_box[0]:
            return                             # no story yet: there is only the music, and the viewer keeps that
        for _ in range(3):                     # the main loop may be changing these as they are copied: then copy again
            try:
                with numbering:
                    beats = [(i, texts[i - 1]) for i in range(max(base[0], 1), len(texts) + 1)][-6:]
                    kept[slot] = copy.deepcopy({"guide": guide_box[0], "beats": beats, "book": book.__dict__, "music": music,
                                                "pinned": pinned[0], "held": held, "sound": sound_state,
                                                "layers": layer_names, "films": film_names})
                break
            except RuntimeError:
                continue
        if said is not None:
            emit({"type": "control", "memorise": slot})    # typed, so the viewer has not heard yet: the launcher tells it
        heard = ((f'You said "{said}". ' if said is not None else "")
                 + f'The story and the music as they stand are memorised as {slot}: say "!recall {slot}" to come back to them.')
        tell("steer", heard)
        say(heard, always=True)

    def recall_story(slot, said=None):
        """Put the story back where it was when this number was memorised. It begins again as start_afresh begins a
        new theme, but from the kept beats: they are told again under new numbers, and llama carries on from the
        last of them. No picture is painted: the viewer has kept its own."""
        was = copy.deepcopy(kept.get(slot))    # a copy, so that recalling it twice gives the same story twice
        if was is None:                        # no story under this number; the viewer may still have music under it
            emit({"type": "control", "recalled": slot})
            if said is not None:
                heard = f'You said "{said}". No story was memorised as {slot}; the music goes back to how it stood then, if it was.'
                tell("steer", heard)
                say(heard, always=True)
            return
        if not was["beats"]:                   # memorised before anything was written: the same guide, as a new story
            start_afresh(was["guide"])
        else:
            with numbering:
                guide_box[0] = was["guide"]
                epoch[0] += 1
                first = len(texts) + 1
                texts.extend(text for _, text in was["beats"])     # told again as new beats: a number is never used twice
                n = len(texts)
                base[0], progress["seq"], joined[0] = first, n, n
                told_beats[:] = [(first + i, text) for i, (_, text) in enumerate(was["beats"])]
                returning[0] = True
                painted[:] = []
                by_llama.clear()
                filmed[0], last_film[0], last_steer[0] = n, "", ""
            # the cast, the place and the light as they were; each beat's card moves to the beat's new number
            moved = {old: first + i for i, (old, _) in enumerate(was["beats"])}
            book.__dict__.clear()
            book.__dict__.update(was["book"])
            book.cards = {moved[k]: {**card, "seq": moved[k]} for k, card in book.cards.items() if k in moved}
            while not steering.empty():
                steering.get()
        for now, then in ((music, was["music"]), (held, was["held"]), (sound_state, was["sound"])):
            now.clear()
            now.update(then)
        # the tempo is part of a memory: the scene comes back at the tempo it had, held by hand if it was then
        pinned[0], recalled_tempo[0] = was.get("pinned"), was["music"].get("bpm")
        pin_new.set()
        layer_names[:], film_names[:] = was["layers"], was["films"]
        set_names(layer_names)
        if not was["beats"]:
            emit({"type": "control", "recalled": slot})    # start_afresh has said the rest
            return
        emit({"type": "control", "fresh": n, "recalled": slot})    # the old pictures and films are let go, then the viewer brings back its own
        emit({"type": "story", "seq": n, "text": was["beats"][-1][1]})
        heard = ((f'You said "{said}". ' if said is not None else "")
                 + f"The story is back where it was when {slot} was memorised, and carries on from there as beat {n + 1}"
                 + ("." if ready.is_set() else " when llama is there."))
        tell("steer", heard)
        say(heard, always=True)

    def listen():
        while not stop.is_set():
            line = read_line()
            if line is None:
                got_guide.set()   # input closed: keep going on what we have (or stop, if there is no guide yet)
                return
            if not got_guide.is_set():
                if line:
                    guide_box[0] = line
                    got_guide.set()
                ask("steer> " if line else "guide> ")
                continue
            if take_line(line):
                return
            ask("steer> ")

    def take_line(line):
        """One line from whoever is steering, typed in the terminal or in the viewer. True means stop."""
        if True:
            if line == "/bye":
                # said at once, because clearing llama takes a few seconds and nothing else would show it was heard
                tell("steer", "Stopping. Whatever llama was writing is dropped, its memory and log are cleared, and the "
                              "window closes.")
                emit({"type": "control", "bye": True})
                stop.set()
                return True
            # "new theme: ...", "start afresh with ...", "!new ...": the story and its pictures begin again
            again = re.match(r"\s*(?:!\s*(?:new|theme|fresh|afresh)\b|(?:start|begin) (?:afresh|again|over)\b|new theme\b|fresh start\b|afresh\b)"
                             r"\s*(?:[:,\-]|with\b|on\b|as\b)?\s*(.*)$", line, re.I)
            if again:
                theme = again.group(1).strip()
                start_afresh(theme or guide_box[0])       # no theme given: the same one again, as a new story
                return False
            if line.strip().lower() in ("!styles", "!options", "what styles are there", "what styles are there?", "musical options"):
                tell("film", "Styles a clip can be asked for in: " + ", ".join(MUSIC_STYLES) + ". Or describe another: llama will work it out.")
                return False
            wanted_now = re.match(r"^!\s*(?:pic|picture|paint)\b\s*(.*)$", line, re.I)
            if wanted_now and "image" in roles:                      # "!pic a fox in the snow": a picture of that, now, in the present scene
                words = wanted_now.group(1).strip()
                with numbering:
                    n = painted[-1] if painted else progress["seq"]
                    prompt = picture_for(n, lead=words)
                emit({"type": "control", "picture_now": words or "again", "prompt": prompt, "beat": n})
                heard = (f'A picture now: "{words}", in the present scene. It is painted next.' if words
                         else "The present scene is painted again, now.")
                tell("picture", heard)
                say(heard, always=True)
                return False
            aimed = re.match(r"^!\s*images?\b\s*(.*)$", line, re.I)
            if aimed:                                                # "!image bloom 0.8", "!image off", "!image hold", "!image auto"
                said = aimed.group(1).strip().lower()
                if said in ("auto", "free", "session", "on"):
                    image_by["on"], image_by["last"] = True, {}
                    heard = "Effects on each picture: the session sets them with the story again."
                elif said in ("hold", "hand", "mine"):
                    image_by["on"] = False
                    heard = "Effects on each picture: yours alone; the session leaves them where they are (!image auto gives them back)."
                elif said in ("off", "none", "0", "clear"):
                    image_by["on"], image_by["last"] = False, {}
                    for k in [k for k in held if k.startswith("image:")]:
                        del held[k]
                    emit({"type": "visual", "seq": 0, "image": {k: 0.0 for k in effects.IMAGE}})
                    heard = "Effects on each picture: off, and left off until !image auto (the screen's are as they were)."
                else:
                    wanted_fx, refused = effects.image_typed(said)
                    if wanted_fx:
                        emit({"type": "visual", "seq": 0, "image": wanted_fx})
                        for k, v in wanted_fx.items():
                            held["image:" + k] = [v, 3]          # the director's again after three beats, as a typed screen effect is
                    heard = ("On each picture: " + ", ".join(f"{k} {v:g}" for k, v in wanted_fx.items()) + "." if wanted_fx else
                             "Settings for each picture look like: !image bloom 0.8 edges 0.4   or   !image off | hold | auto.")
                    if refused:
                        heard += " " + ", ".join(refused) + (" works" if len(refused) == 1 else " work") + " on the whole screen only (type it without \"image\")."
                tell("steer", heard)
                say(heard, always=True)
                return False
            pulled = pull_in(line)                                   # "pull a vinyl crackle loop from splice", "!pull rain on a tin roof"
            if pulled:
                emit({"type": "control", "pull": pulled})
                layered = pulled["role"] in ("loop", "texture")
                if layered:
                    know_layer(pulled["name"])
                heard = (f'You asked for "{pulled["query"]}"' + (f' as the {pulled["role"]}' if pulled["role"] in ("kick", "snare", "hats") else "")
                         + {"splice": " from your Splice library", "any": ": your Splice library first, then the free archives"}.get(
                             pulled["where"], f' from {pulled["where"].replace("_", " ")}') + ". It is fetched into memory"
                         + (f', cut at its obvious transients, and waits as the layer called "{pulled["name"]}". Say "bring in the {pulled["name"]}", or '
                            f'say when it plays ("{pulled["name"]} only in the breaks", "{pulled["name"]} on the off-beats"); "chop the '
                            f'{pulled["name"]} on the eighths" cuts it another way.' if layered else " and used when it arrives."))
                tell("sound", heard)
                say(heard, always=True)
                return False
            chopped = chop_typed(line)       # "!chop drumfunk", "!role rain hook": taken first, or "!chop ..." would ask for a clip
            if chopped:
                emit({"type": "visual", "seq": 0, **chopped})
                role = chopped.get("role") or {}
                say(f"chop: {chopped['chop_style']}" if "chop_style" in chopped else f"role: {role['layer']} {role['role'] or 'auto'}", always=True)
                return False
            edged = edge_typed(line)         # "!edge lock 0.7", "!edge auto", "!roller 16": straight to the viewer
            if edged:
                emit({"type": "visual", "seq": 0, **edged})
                say(edge_said(edged), always=True)
                return False
            wanted = SAMPLE_ASKED.match(line)
            if wanted:                                                # a clip made to be chopped, in the viewer's own words
                length, bare = length_first(wanted.group("bare") or "", float(pinned[0] or music["bpm"]))       # "!sample 2s a dancer ..."
                ask_sample((bare or wanted.group("said") or "").strip() or last_sample[0] or "a dancer moving to the music", length=length)
                return False
            worded = WORDS_ASKED.match(line)
            if worded:                                                # the words for the clip: given, or to be invented
                given = worded.group("words").strip()
                ask_sample(last_sample[0] or "a dancer moving to the music",
                           "invent new ones" if worded.group("invent") and not given else f'"{given.strip(chr(34))}"' if given else "invent new ones")
                return False
            turned = knob_in(line)                                    # "!knob bass 60", "!super 40", "!patch bass fold crush"
            if turned:
                if isinstance(turned, dict) and "super" not in turned:     # "!memorise 2", "!recall 2": they say what they did themselves
                    if "memorise" in turned:
                        keep_story(turned["memorise"], line)
                    else:
                        recall_story(turned["recall"], line)
                    return False
                if isinstance(turned, dict):
                    emit({"type": "visual", "seq": 0, "super": turned["super"]})
                    heard = f'You said "{line}". Now: the super knob is at {turned["super"] * 100:.0f}, and every part\'s knob has moved with it.'
                else:
                    for op in turned:
                        apply_op(sound_state.setdefault(op["part"], fresh()), op)
                    emit({"type": "visual", "seq": 0, "patch": turned})
                    heard = f'You said "{line}". Now: ' + ("every part's knob is at " + f"{turned[0]['set']['filth'] * 100:.0f}" if len(turned) > 3
                                                         else "; ".join(describe_op(op) for op in turned)) + "."
                tell("steer", heard)
                say(heard, always=True)
                return False
            gone = drop_in(line)                                      # "drop the rain": a sample layer taken away
            if gone:
                emit({"type": "visual", "seq": 0, "patch": gone})
                for op in gone:
                    forget_layer(op["part"])
                heard = f'You said "{line}". Now: ' + "; ".join(describe_op(op) for op in gone) + "."
                tell("steer", heard)
                say(heard, always=True)
                return False
            # "rain only in the breaks", "dust every fourth bar": which bars a layer plays in; then "sub on the off-beats",
            # "!kick 1 5 9 13", "rain on the one": where in the bar it plays
            placed = bring_in(line) or chop_in(line) or when_in(line) or steps_in(line)
            if placed:
                emit({"type": "visual", "seq": 0, "patch": placed})
                heard = f'You said "{line}". Now: ' + "; ".join(describe_op(op) for op in placed) + "."
                tell("steer", heard)
                say(heard, always=True)
                return False
            # "make the bass dirtier", "more room on the tune", "mute the bells", "!hats bright": how a part sounds
            sounds = parts_in(line[1:] if line.startswith("!") else line)
            if sounds:
                for part, word in sounds:
                    change_part(sound_state.setdefault(part, fresh()), word)
                emit({"type": "visual", "seq": 0, "parts": sounds})
                heard = f'You said "{line}". Now: ' + "; ".join(f"the {part}: {word}" for part, word in sounds) + "."
                tell("steer", heard)
                say(heard, always=True)
                return False
            asked = resets_in(line)
            words_typed = line[1:].lower().split() if line.startswith("!") else []
            if words_typed and words_typed[0] in ("redo", "reset"):       # "!redo pics", "!redo music story", "!reset all"
                names = {"pics": "pictures", "pictures": "pictures", "story": "story", "theme": "story", "music": "music",
                         "look": "visuals", "visuals": "visuals"}
                asked = list(KINDS) if not words_typed[1:] or "all" in words_typed else [names[w] for w in words_typed[1:] if w in names]
            if asked:
                threading.Thread(target=do_resets, args=(asked, line), daemon=True).start()
                return False
            if line.startswith("!"):          # straight to the visuals, no model involved: "!chaos 1.6 bpm 140"
                look = parse_visual_words(line[1:])
                words = dict(zip(line[1:].replace("=", " ").split()[0::2], line[1:].replace("=", " ").split()[1::2]))
                handled = bool(look)
                if "bpm" in look:                 # a tempo typed by hand becomes the one tempo, and it is held
                    pinned[0] = look["bpm"]
                    pin_new.set()
                elif words.get("bpm", "").lower() in ("auto", "free"):
                    pinned[0] = None
                    say("tempo: free again - the soundtrack and the director move it", always=True)
                    handled = True
                if look:
                    typed_score(look)
                    emit({"type": "visual", "seq": 0, **look})
                    say("visuals: " + ", ".join(f"{k} {v}" for k, v in look.items()), always=True)
                if words.get("lead", "").lower() in ("auto", "film", "acid", "reese", "hoover", "dub"):     # what the lead plays
                    emit({"type": "visual", "seq": 0, "lead": words["lead"].lower()})
                    say(f"lead: {words['lead'].lower()}", always=True)
                    handled = True
                if words.get("fx", "").lower() in ("auto", "free", "session", "hold", "hand", "mine"):
                    fx_by["on"] = words["fx"].lower() in ("auto", "free", "session")
                    say("effects: " + ("the session sets them with the story again" if fx_by["on"] else "yours alone; the session leaves them where they are"), always=True)
                    handled = True
                if words.get("super", "").lower() in ("auto", "free", "session", "hold", "hand", "mine"):
                    super_by["on"], super_by["said"] = words["super"].lower() in ("auto", "free", "session"), None
                    say("super knob: " + ("the session moves it with the story again" if super_by["on"] else "yours alone; the session leaves it where it is"), always=True)
                    handled = True
                try:
                    if "structure" in words:      # for how many bars the session leaves the structure alone once it has changed
                        structure["bars"] = int(min(max(round(float(words["structure"]) / 4) * 4, 4), 64))
                        emit({"type": "visual", "seq": 0, "structure": structure["bars"]})
                        say(f"structure: the session changes the style, the key or the riffs at most every {structure['bars']} bars, on a four-bar line", always=True)
                        handled = True
                except ValueError:
                    pass
                try:
                    if "cadence" in words:        # how often a new picture appears, in seconds (0 = only new prompts)
                        emit({"type": "control", "cadence": max(float(words["cadence"]), 0.0)})
                        say(f"cadence: {float(words['cadence']):g}s", always=True)
                        handled = True
                except ValueError:
                    pass
                first = line[1:].split()
                if first and first[0].lower() in ("film", "clip"):    # "!film", "!film 3", "!film 4 beats", "!film 2 bars"
                    ask_film(" ".join(first[1:]))
                    handled = True
                mode = words.get("video", "").lower()
                if mode in ("off", "interlude", "reel", "ask"):
                    video_mode[0] = mode
                if mode in ("now", "on", "off", "interlude", "reel", "ask"):
                    video_on[0] = mode != "off"
                    if mode == "now":
                        video_now.set()
                    emit({"type": "control", "video": mode})
                    say({"now": "video: the next thing written is a journey, and it is filmed as soon as it is ready",
                         "ask": "video: only when you ask (!film)", "off": "video: off"}.get(mode, f"video: {mode}"), always=True)
                    handled = True
                if not handled:
                    say("settings look like: !chaos 1.4 bpm 140 folds 6   or   !cadence 20   or   !film 2   or   "
                        "!video ask|interlude|reel|off   or   !chop " + "|".join(CHOP_STYLES) + "   or   !role <layer> "
                        + "|".join(CHOP_ROLES) + "|auto   or   !edge lock|derange 0..1   or   !edge auto   or   !roller 2..32",
                        always=True)
            elif line:
                steering.put(line)
                threading.Thread(target=take_steer, args=(line,), daemon=True).start()
        return False

    threading.Thread(target=listen, daemon=True).start()
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, lambda *a: stop.set())
    if args.stop_handle:   # the mindstream launcher holds the other end; end-of-file means "stop and clean up"
        import msvcrt
        stop_fd = msvcrt.open_osfhandle(args.stop_handle, os.O_RDONLY)

        inbox = queue.Queue()                      # what came down the pipe, waiting to be acted on

        def watch_stop():
            # the launcher may also send one-line messages down this pipe, e.g. {"bpm": 121.4}: the tempo it
            # measured in the last video's soundtrack. This thread only reads: acting on a message can take a
            # while (a steer may wait on llama), and a pipe that is not read fills and stops the launcher dead
            buffer = b""
            while True:
                try:
                    chunk = os.read(stop_fd, 4096)
                except OSError:
                    chunk = b""
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    one, buffer = buffer.split(b"\n", 1)
                    try:
                        inbox.put(json.loads(one))
                    except ValueError:
                        pass
            stop.set()
            inbox.put(None)

        def act_on_pipe():
            while True:
                message = inbox.get()
                if message is None:
                    return
                try:
                    if message.get("journey"):          # the launcher is ready to film: write the next film prompt
                        if message.get("plain") and ready.is_set():
                            # the first film of a session: put together here at once, so that something is
                            # filmed in the first minutes instead of after llama has worked through several beats
                            plain_film("the first film, made at once while llama writes the story")
                        elif ready.is_set():
                            video_now.set()
                        else:                           # no llama to write it: a plainer one, put together here
                            plain_film("llama is not there yet")
                    if message.get("steer"):            # typed in the viewer rather than the terminal
                        text = " ".join(str(message["steer"]).split())
                        if not got_guide.is_set():      # the first thing typed there is the guide
                            guide_box[0] = text
                            got_guide.set()
                            say("guide taken from the viewer", always=True)
                            ask("steer> ")
                        else:
                            take_line(text)
                    if "pause" in message:              # the viewer is minimised: nobody is watching
                        (unwatched.set if message["pause"] else unwatched.clear)()
                    if "bpm" in message:
                        heard.put(float(message["bpm"]))
                    if "memorise" in message:           # the knob panel's "memorise": the viewer keeps the music, the story is kept here
                        keep_story(int(message["memorise"]))
                    if "recall" in message:             # one of the panel's numbers: the story goes back, and the viewer is told to follow
                        recall_story(int(message["recall"]))
                except Exception as e:              # one bad message must not stop the rest
                    say(f"a message from the launcher could not be acted on ({type(e).__name__})")

        threading.Thread(target=act_on_pipe, daemon=True).start()
        threading.Thread(target=watch_stop, daemon=True).start()

    while not got_guide.wait(0.25):
        if stop.is_set():
            break
    guide = guide_box[0]
    if not guide:
        try:
            status("stop", "no guide given")
        except OSError:
            pass
        say("no guide given", always=True)
        os._exit(1)
    emit({"type": "control", "theme": guide})     # shown at once, as words on a card, until the first picture is painted
    tell("steer", "The story has its guide. Anything typed from here on steers it.")
    if "image" in roles:
        # llama needs a minute or more before its first picture prompt. The picture generator is on this machine
        # and ready sooner, so the guide itself is painted straight away: something to look at, and to steer.
        book.take_card(0, "", guide)
        paint(0, picture_for(0))               # the guide's own words, with the framing and the medium a picture prompt needs
        emit({"type": "story", "seq": 0, "text": guide})
        tell("picture", "A first picture is being painted straight from your guide, while llama gets ready.")
    status("load", f"connecting to {args.host}")
    # Without llama there is no story writer, but everything on this machine still works: the picture from the
    # guide, the music, the motion, breaks; what is typed about the story becomes a beat with a picture of its own, and
    # a film can be made between two of them. So the session carries on in that plainer way and keeps trying; when
    # llama answers, it takes the story up from there.
    llama, told = None, False
    while llama is None:
        try:
            llama = Ollama(args.host, log=say)
        except ApiError as e:
            status("error", f"cannot reach {args.host}; carrying on without it", detail=f"trying again every {RETRY_SECONDS:g} s")
            if not told:
                told = True
                say(f"{e} - carrying on without llama and trying again every {RETRY_SECONDS:g} s", always=True)
                tell("steer", f"{args.host} cannot be reached yet. Pictures, music, steering and films still work, in a plainer "
                              "way: what you type about the story becomes the story, a beat at a time, until llama answers "
                              "and takes it up.")
            if stop.wait(RETRY_SECONDS):
                os._exit(0)

    def writing(kind, seq, label):
        """Progress callback for one reply: 'loading the model' until the first word, then a running word count."""
        state = {"chars": 0, "sent": 0.0, "started": False}
        status("load" if seq == 1 and kind == "beat" else kind, "loading the model on llama" if seq == 1 and kind == "beat" else label, seq)

        def on_text(piece):
            state["chars"] += len(piece)
            if args.echo and kind == "beat":
                print(piece, end="", file=sys.stderr, flush=True)
            now = time.time()
            if not state["started"] or now - state["sent"] >= 1.0:
                state["started"], state["sent"] = True, now
                status(kind, label, seq, detail=f"about {state['chars'] // 6} words")
        return on_text

    # Someone else's model already loaded means another session is using llama. Starting here would
    # evict their model, and our clean-up restart would cut them off. Refuse unless told to share.
    try:
        with llama.request("/api/ps", timeout=15) as r:
            busy = [m["name"] for m in json.load(r).get("models", [])]
    except ApiError:
        busy = []
    if busy and not args.share:
        # A model can also be left loaded by a session that was closed without its clean-up (a closed terminal).
        # If nobody but us is connected to llama, that is what this is: clear it, as that session would have.
        try:
            r = subprocess.run(["ssh", "-o", "BatchMode=yes", args.host,
                                "ss -Htn state established '( sport = :22 )' | wc -l; "
                                "ss -Htn state established '( sport = :11434 )' | wc -l"],
                               stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)
            logins, calls = (int(x) for x in r.stdout.split()[:2])
        except (OSError, ValueError, subprocess.TimeoutExpired):
            logins, calls = 99, 99
        if logins <= 2 and calls == 0:          # our tunnel and this question; no request in flight
            status("load", "clearing a model left by an ended session")
            say(f"{', '.join(busy)} was left loaded by a session that has ended - restarting Ollama to clear it", always=True)
            llama.clear("all")
            for _ in range(40):
                time.sleep(1)
                try:
                    with llama.request("/api/ps", timeout=5) as r:
                        busy = [m["name"] for m in json.load(r).get("models", [])]
                    break
                except (ApiError, OSError):
                    continue
    told = False
    while busy and not args.share:              # someone else is using llama: carry on without it until they are done
        status("error", "llama is busy with another session; carrying on without it", detail=f"checking again every {RETRY_SECONDS:g} s")
        if not told:
            told = True
            say(f"llama is busy: {', '.join(busy)} is loaded by another session. Carrying on without it and checking every "
                f"{RETRY_SECONDS:g} s. (Use --share to use it anyway; Ollama will then not be restarted at exit.)", always=True)
            tell("steer", "llama is busy with another session. Pictures, music, steering and films still work, in a plainer "
                          "way: what you type about the story becomes the story, a beat at a time, until llama is free "
                          "and takes it up.")
        if stop.wait(RETRY_SECONDS):
            llama.close(keep_loaded=True, restart=False)
            os._exit(0)
        try:
            with llama.request("/api/ps", timeout=15) as r:
                busy = [m["name"] for m in json.load(r).get("models", [])]
        except ApiError:
            pass
    if busy:
        args.no_restart = True
    else:
        llama.clear("log")      # a session that was killed, not closed, leaves its timings in llama's log: drop them now

    reason = ""
    try:
        think = None
        try:
            capabilities = llama.capabilities(args.model)
        except ApiError as e:
            raise ApiError(f"model not found on llama: {args.model}") from None
        if "thinking" in capabilities:
            think = args.think == "on"
        say(f"{args.model} on {args.host}, a beat every {args.interval:g}s" + (f", {args.beats} beats" if args.beats else ""))
        say("instructions: " + ", ".join(f"{k} = {os.path.basename(p)}" for k, p in
                                         (("story", args.story_md), ("visual", args.visual_md), ("image", args.image_md), ("video", args.video_md)) if k in roles))
        if structured:
            say(f"prompts: {args.prompts} - llama fills in {os.path.basename(args.card_md)} and {os.path.basename(args.film_card_md)}; "
                "code writes the picture and film prompts (the image and video guides above are not sent)")
        reason = ""    # why the story ended, if it was not asked to
        previous_beat, bpm_now = "", float(args.bpm)
        ready.set()

        def chat(messages, options, on_text, wait=False):
            """One reply from llama. If llama cannot answer, the session carries on without it, as it does before
            llama first connects: a beat (`wait`) is asked for again every 20 s until it comes; anything else
            comes back empty at once, and that step is done here in its plainer way."""
            while not stop.is_set():
                if not wait and not ready.is_set():
                    return ""
                calling.set()

                def hear(piece):               # a reply under way is cut short the moment the session is told to stop
                    if stop.is_set():
                        raise StopAsked()
                    if on_text:
                        on_text(piece)
                try:
                    reply = llama.chat(args.model, messages, think=think, options=options, on_text=hear)
                    if not ready.is_set():
                        ready.set()
                        tell("steer", "llama is answering again, and takes the story up from where it stands.")
                    return reply
                except StopAsked:
                    return ""
                except ApiError as e:
                    if ready.is_set():
                        ready.clear()
                        say(f"{str(e)[:120]} - carrying on without llama and trying again every {RETRY_SECONDS:g} s", always=True)
                        tell("steer", "llama has stopped answering. Pictures, music, steering and films still work, in a plainer "
                                      "way: what you type about the story becomes the story, a beat at a time, until llama is back.")
                    status("error", "llama is not answering; carrying on without it", detail=f"trying again every {RETRY_SECONDS:g} s")
                    if not wait:
                        return ""
                finally:
                    calling.clear()
                stop.wait(RETRY_SECONDS)
            return ""

        def settle_tempo(wish=None):
            """One tempo for everything: the music asked of the video model, the pulse and the scene
            changes. It only drifts: what was actually heard in the last soundtrack pulls it most, the
            director's wish may nudge it by a few percent. A tempo typed by hand ("!bpm 178") replaces
            it at once and is then held to within 3% until "!bpm auto"."""
            nonlocal bpm_now
            if pin_new.is_set():
                pin_new.clear()
                bpm_now, recalled_tempo[0] = float(pinned[0] or recalled_tempo[0] or bpm_now), None
            while not heard.empty():
                measured = heard.get()
                bpm_now += min(max((measured - bpm_now) * 0.6, -0.06 * bpm_now), 0.06 * bpm_now)
            if wish is not None:
                bpm_now += min(max(wish - bpm_now, -0.04 * bpm_now), 0.04 * bpm_now)
            held = pinned[0]
            if held:
                bpm_now = min(max(bpm_now, held * 0.97), held * 1.03)
            music["bpm"] = bpm_now
            return bpm_now

        def sample_if_asked():
            """A clip asked for to chop is written by llama next, between its other jobs (prompts/sample.md)."""
            while not samples.empty() and not stop.is_set():
                request, words, seconds, bpm = samples.get()
                if not ready.is_set():
                    plain_sample(request, words, seconds, bpm, "llama is not answering")
                    continue
                now_at = texts[-1] if texts else (guide_box[0] or "")
                asked = (f"Request: {request}\n" + (f"The words: {words}\n" if words else "") + f"Tempo: {bpm:.0f} BPM\nLength: {seconds:g} seconds\n"
                         f"Words: at most {word_budget(seconds) + 1}\nStory now: {now_at[:300]}")
                reply = strip_fence(chat([{"role": "system", "content": roles["sample"].replace("{styles}", styles_menu(bpm))},
                                          {"role": "user", "content": asked}], {"num_predict": 240, "temperature": 0.8},
                                         writing("prompt", progress["seq"], "writing a clip to chop")))
                if reply:
                    send_sample(reply, seconds, bpm, "written by llama from what you asked")
                else:
                    plain_sample(request, words, seconds, bpm, "llama returned nothing")

        def interpret_if_asked():
            """Whatever has been typed that plain words did not settle is read by llama, between its other jobs: what
            the viewer most likely meant, as changes to the show and to how its parts sound (prompts/sound.md)."""
            while not reading.empty() and ready.is_set() and not stop.is_set():
                text, then, settled = reading.get()
                state = "; ".join(f"{part} ({summary(s)})" for part, s in sound_state.items() if summary(s)) or "all as they started"
                asked = (f"Music now: {music['style']}, {music['key']}, {music['bpm']:.0f} BPM\nParts now: {state}\n"
                         + (f"Sample layers: {', '.join(layer_names)}\n" if layer_names else "") + f"Instruction: {text}")
                reply = chat([{"role": "system", "content": roles["sound"]}, {"role": "user", "content": asked}],
                             {"num_predict": 260, "temperature": 0.3}, writing("prompt", progress["seq"], "working out what you meant"))
                start, end = reply.find("{"), reply.rfind("}")
                try:
                    read = json.loads(reply[start:end + 1]) if 0 <= start < end else {}
                except ValueError:
                    read = {}
                read = read if isinstance(read, dict) else {}
                tags = [t for t in (str(t).strip().lower() for t in (read.get("tags") or []) if isinstance(t, str)) if t in steer_intent.TAGS][:6]
                done = enact_change({k: v for k, v in steer_intent.apply(tags, then).items() if k not in settled}, then)
                ops = sanitize(read.get("patch"))
                if ops:
                    dropped = []
                    for op in ops:
                        if "drop" in op:
                            dropped.append(op["part"])
                        elif "bring" in op or "chop" in op or "when" in op or "steps" in op:
                            pass                    # when and how it plays, not how it sounds
                        else:
                            apply_op(sound_state.setdefault(op["part"], fresh()), op)
                    emit({"type": "visual", "seq": 0, "patch": ops})
                    for name in dropped:
                        forget_layer(name)
                    done += [describe_op(op) for op in ops]
                again = [kind for tag, kind in (("replace-pictures", "pictures"), ("restart-story", "story"), ("rebuild-music", "music"))
                         if tag in tags]
                if again:
                    do_resets(again)
                why = " ".join(str(read.get("why", "")).split())[:160]
                story = why.lower().strip(" .") == "story"
                if done:
                    heard = f'llama read "{text}" as: ' + (why.rstrip(". ") + ". " if why and not story else "") + "Now: " + "; ".join(done) + "."
                elif again:
                    continue                    # do_resets has said what it did
                elif story or not reply:
                    heard = f'llama took "{text}" as story: the next beat takes it in.'
                else:
                    heard = f'llama could not turn "{text}" into a change to the sound or the look. Say it another way, or name a part.'
                tell("steer", heard)
                say(heard, always=True)

        def film_if_asked():
            """A film that has been asked for is written next, between llama's other jobs, rather than after the whole
            beat has been worked through: for the latest two beats that already have pictures on the way."""
            if not (args.journeys_on_demand and video_now.is_set() and video_on[0] and "video" in roles) or stop.is_set():
                return
            n = max(painted) if painted else 0
            if n >= 1 and (n - 1) in painted and filmed[0] < n:
                video_now.clear()
                write_journey(n, [])

        def write_journey(n, notes):
            """The video prompt for the journey from beat n-1's picture to beat n's."""
            watch()
            if stop.is_set():
                return
            filmed[0] = n
            settle_tempo()
            seconds, film_seconds[0] = min(film_seconds[0] or args.video_seconds, MAX_FILM_SECONDS), None
            # Segments are generated separately, so the writer is shown its previous prompt and must
            # carry the same people, voices and music forward.
            asked = ("".join(f"Steer: {note}\n" for note in notes) + f"From: {text_of(n - 1)}\n\nTo: {text_of(n)}\n\n"
                     f"Music tempo: {bpm_now:.0f} BPM\nSeconds: {seconds:g}\n"
                     f"Words: at most {word_budget(seconds)} spoken or sung, in total\n"
                     f"Prompt length: at most {round(40 + 25 * seconds)} words in all. One shot.\n\n"
                     f"Previous segment: {last_film[0] or 'none - this is the first segment'}")
            messages = [{"role": "system", "content": roles["video"]}, {"role": "user", "content": asked}]
            # One go at it. Whatever the reply lacks is mended here rather than asked for again: at a few
            # words a second, a second attempt costs minutes, and a slightly loose prompt still films.
            prompt, filled = "", []
            if structured:
                # llama fills in four short lines; the format, the speaker's voice and the music are written here.
                card = chat([{"role": "system", "content": roles["film"]},
                             {"role": "user", "content": book.film_request(text_of(n - 1), text_of(n), word_budget(seconds), notes)}],
                            {"num_predict": 140}, writing("prompt", n, f"writing film card {n - 1} to {n}"))
                if stop.is_set() and not card:
                    return
                if card:                       # whatever it left out is filled in here; an empty reply gets the plain film below
                    prompt, filled = book.film(n, card, text_of(n - 1), text_of(n), music, bpm_now, word_budget(seconds) + 1)
                    prompt = ALIGNMENT + "\n\n" + prompt
            for attempt in (1, 2) if not structured else ():
                # a short film needs a short prompt: the reply is capped in step with the film's length
                prompt = strip_fence(chat(messages, {"num_predict": round(150 + 70 * seconds)},
                                          writing("prompt", n, f"writing journey {n - 1} to {n}")))
                if prompt or stop.is_set() or not ready.is_set():
                    break
            if stop.is_set() and not prompt:
                return
            if not prompt:                     # nothing from llama: the film is put together here, in its plainer way
                prompt, _ = book.film(n, "", text_of(n - 1), text_of(n), music, bpm_now, word_budget(seconds) + 1)
                send_film(n - 1, n, ALIGNMENT + "\n\n" + prompt, seconds, bpm_now,
                          plain="llama returned nothing" if ready.is_set() else "llama is not answering")
                return
            send_film(n - 1, n, prompt, seconds, bpm_now, filled)

        def watch():
            """Wait here while nobody is watching: what is not seen is not written."""
            if unwatched.is_set() and not stop.is_set():
                status("idle", "holding: nobody is watching")
                while unwatched.is_set() and not stop.is_set():
                    time.sleep(0.3)

        history = []   # alternating user / assistant messages after the opening guide
        with_card = " Then a blank line and its card." if args.prompts == "inline" else ""
        opening = {"role": "user", "content": f"Guide: {guide}\n\nBegin." + (" Write the first beat." + with_card if with_card else "")}
        seq, story_of = 0, epoch[0]                # story_of: which start of the story this history belongs to

        def stale():
            """True once the viewer has started afresh: whatever llama was writing belongs to the old story."""
            return epoch[0] != story_of

        while not stop.is_set() and (args.beats == 0 or len(texts) < args.beats):
            watch()
            started = time.time()
            if stop.is_set():
                break
            sample_if_asked()
            interpret_if_asked()
            if stale():                        # a new theme: llama begins again from it, shown nothing of the old story
                story_of, guide, history = epoch[0], guide_box[0], []
                opening = {"role": "user", "content": f"Guide: {guide}\n\nBegin." + (" Write the first beat." + with_card if with_card else "")}
            seq = len(texts) + 1               # the number it will have, unless the viewer tells a beat first
            progress["seq"] = seq
            notes = []
            while not steering.empty():
                notes.append(steering.get())
            # Beats the viewer told while llama was away are the story now: llama is shown them as that, not as steers.
            # Beats brought back by a recall are shown to it the same way, and called what they are.
            with numbering:
                late = stale()                 # a fresh start or a recall in the last instant: its beats are left for the turn that begins it
                if not late:
                    own, told_beats[:] = list(told_beats), []
                    back, returning[0] = returning[0], False
            if late:
                continue
            notes = [n for n in notes if n not in [text for _, text in own]]
            sofar = (("The story so far, which you are returning to. Carry on from the last of these beats.\n" if back else
                      "While you were away the viewer told these beats of the story in their own words. They are part of the "
                      "story now; carry on from the last of them.\n") + "".join(f"Beat {i}: {text}\n" for i, text in own) + "\n") if own else ""
            if own and back:
                tell("steer", f"llama takes the story up at beat {seq}, from where it stood when it was memorised.")
            elif own:
                tell("steer", f"llama takes the story up at beat {seq}, from the {'beats' if len(own) > 1 else 'beat'} you told while it was away.")
            if sofar and not history:
                opening["content"] = f"Guide: {guide}\n\n{sofar}Begin." + (" Write the next beat." + with_card if with_card else "")
            if history:
                history.append({"role": "user", "content": (sofar + "".join(f"Steer: {n}\n" for n in notes)
                                                            + (f"Cast: {book.cast.listing()}\n" if with_card else "")
                                                            + "Write the next beat of the story now: one paragraph." + with_card)})
            recent = history[-(2 * args.memory):]
            while recent and recent[0]["role"] != "assistant":
                recent = recent[1:]   # the window must open on a reply, right after the guide
            messages = [{"role": "system", "content": roles["story"]}, opening] + recent
            if args.echo:
                print(f"\n[{seq}] ", end="", file=sys.stderr, flush=True)
            beat, card = "", ""
            for attempt in range(1, 5):
                if stop.is_set():
                    break
                beat = chat(messages, {"num_predict": 420 if with_card else 260},
                            writing("beat", seq, f"writing beat {seq}" + (f" (try {attempt})" if attempt > 1 else "")), wait=True)
                if with_card:                  # the reply is the beat and then its card; a reply that is all card is no beat
                    beat, card = split_beat(beat)
                if beat:
                    break
                # models sometimes answer "Continue." with nothing at all; say it differently and ask again
                ended = getattr(llama, "last", {})
                say(f"beat {seq} came back empty ({ended.get('tokens')} tokens, ended on '{ended.get('reason')}', "
                    f"{ended.get('thinking', 0)} characters of hidden thinking) - asking again ({attempt})", always=True)
                nudge = ("Write the next beat of the story now: one paragraph, 50 to 80 words.",
                         "The story is not over. Something new enters the scene. Write that beat now, one paragraph.",
                         "Begin a new scene that follows from the last one. One paragraph, present tense.")[min(attempt, 3) - 1]
                last = nudge if history else f"{opening['content']}\n\n{nudge}"
                messages = messages[:-1] + [{"role": "user", "content": last}]
            if args.echo:
                print(file=sys.stderr, flush=True)
            if stop.is_set() and not beat:
                break
            if stale():
                continue                       # written for the story that has just been put aside: dropped unseen
            if not beat:
                reason = f"beat {seq} came back empty four times"
                say(reason + " - stopping", always=True)
                break
            turn = {"role": "assistant", "content": beat}
            history.append(turn)
            with numbering:                    # numbered as it lands: the viewer may have told a beat while this one was awaited
                texts.append(beat)
                seq = len(texts)
                progress["seq"] = seq
            emit({"type": "story", "seq": seq, "text": beat})
            film_if_asked()
            sample_if_asked()
            interpret_if_asked()
            watch()
            if "visual" in roles and not stop.is_set():
                # the visual director: how the moving part of the picture should behave for this beat.
                # It sees the beat and any steering just given, and answers with a small JSON object.
                read, steered = None, "".join(f"(Steer: {n}) " for n in notes)
                if args.director == "local" and reader is not None:      # the small model on this machine
                    status("prompt", f"scoring beat {seq}", seq)
                    read = reader.read(steered + beat, dict(music), timeout=20.0, kind="beat")
                    if read is not None:
                        low = beat.lower()                              # it reaches for colours too readily: only ones the beat names
                        tags = [t for t in read.get("tags") or [] if t not in steer_intent.COLOURS or t.split("-")[0] in low]
                        look = {k: v for k, v in steer_intent.apply(tags, dict(music)).items() if k != "break"}
                        look["why"] = "Read as " + (", ".join(tags) or "no change")
                if read is None and args.director != "full":            # llama picks tags: a dozen words, not a page of numbers
                    reply = chat([{"role": "system", "content": TAG_DIRECTOR}, {"role": "user", "content": f"Beat: {steered}{beat}"}],
                                 {"num_predict": 70, "temperature": 0.4}, writing("prompt", seq, f"scoring beat {seq}"))
                    first, _, rest = reply.strip().partition("\n")
                    tags = [t.strip().lower() for t in first.lower().replace("tags:", "").split(",")]
                    tags = [t for t in tags if t in steer_intent.TAGS and "break" not in t][:6]
                    look = steer_intent.apply(tags, dict(music))
                    why = rest.lower().partition("why:")[1] and rest[rest.lower().index("why:") + 4:].strip().splitlines()[0]
                    wanted = re.search(r"^\s*sound:\s*(.+)$", rest, re.I | re.M)
                    if wanted and not args.no_story_sounds and seq - story_sound[0] >= 3:
                        story_sound[0] = seq
                        story_wants_sound(wanted.group(1))
                    look["why"] = why or ("Read as " + ", ".join(tags) if tags else "")
                    asked_fx = re.search(r"^\s*fx:\s*(.+)$", rest, re.I | re.M)
                    if asked_fx:                                  # the director named the effects itself ("none" is an answer too)
                        look["fx"] = effects.named(asked_fx.group(1))
                    read = True
                if read is not None:
                    pass
                else:
                    asked = ("".join(f"Steer: {n}\n" for n in notes)
                             + f"Music now: {music['style']}, {music['key']}, {music['bpm']:.0f} BPM\nBeat: {beat}")
                    reply = chat([{"role": "system", "content": roles["visual"]}, {"role": "user", "content": asked}],
                                 {"num_predict": 260, "temperature": 0.7}, writing("prompt", seq, f"directing the visuals {seq}"))
                    look = parse_visual(reply)
                look["bpm"] = round(settle_tempo(look.get("bpm")), 1)
                picked, fx_said = look.pop("fx", None), ""
                if fx_by["on"]:
                    if picked is None:                          # effects it set as plain settings count as its choice; else the beat is read
                        picked = {k: look[k] for k in effects.DIRECTED if look.get(k, 0.0) > 0.0} or effects.from_beat(steered + beat, float(look.get("chaos", music.get("chaos", 1.0))))
                    # a step at a time: one effect in and one out a beat, so heavy passes are not all switched on one beat
                    picked = fx_by["last"] = effects.paced(fx_by["last"], picked)
                    look.update(effects.directed(picked))
                    fx_said = " Effects: " + (", ".join(f"{k} {v * 100:.0f}" for k, v in picked.items()) if picked else "none") + "."
                else:
                    for k in effects.DIRECTED:
                        look.pop(k, None)
                on_pictures = None                              # the effects on each picture by itself, chosen apart from the screen's
                if image_by["on"]:
                    heat = float(look.get("chaos", music.get("chaos", 1.0)))
                    chosen = image_by["last"] = effects.paced(image_by["last"], effects.image_from_beat(steered + beat, heat, picked or {}))
                    on_pictures = {k[len("image:"):]: v for k, v in effects.image_directed(chosen).items()}
                    fx_said += " On each picture: " + (", ".join(f"{k} {v * 100:.0f}" for k, v in chosen.items()) if chosen else "none") + "."
                for k in [k for k in look if k.startswith("image:")]:
                    look.pop(k)                                 # (only in the "image" part of the message)
                for k, entry in list(held.items()):         # what the viewer typed outranks the director for a while
                    if k.startswith("image:"):
                        if on_pictures is not None:
                            on_pictures[k[len("image:"):]] = entry[0]
                    else:
                        look[k] = entry[0]
                    entry[1] -= 1
                    if entry[1] <= 0:
                        del held[k]
                why = look.pop("why", "")
                # how often the structure changes: not sooner than `structure["bars"]` bars after it last did
                wants = [k for k in ("style", "key", "rescore", "break") if k in look and (k in ("rescore", "break") or differs(music.get(k), look[k], k))]
                stood, holds = (time.time() - structure["at"]) * bpm_now / 240.0, ""
                if wants and stood < structure["bars"]:
                    for k in wants:
                        look.pop(k)
                    holds = (f" It would have changed the {' and the '.join({'rescore': 'riffs'}.get(k, k) for k in wants)}, but the structure changed "
                             f"{stood:.0f} bars ago and is left alone for {structure['bars']}.")
                elif wants:
                    structure["at"] = time.time()
                    holds = " The change of structure lands on the next four-bar line."
                knob = {}
                if super_by["on"]:
                    heat = float(look.get("chaos", music.get("chaos", 1.0)))
                    wish = round(min(max((heat - 0.8) / 1.2, 0.0), 1.0) * 0.5, 2)
                    if super_by["said"] is None or abs(wish - super_by["said"]) >= 0.02:
                        super_by["said"], knob = wish, {"super": wish}
                        holds += f" The super knob is asked toward {wish * 100:.0f}: it goes there slowly, or at once when the scene changes."
                moved = {k: v for k, v in look.items() if k in ("rescore", "break") or differs(music.get(k), v, k)}
                parts = describe(moved, dict(music))[:5]
                tell("score", f"Beat {seq}: " + (why.rstrip(". ") + ". " if why else "")
                     + ("So: " + "; ".join(parts) + "." if parts else "The music and the motion hold.") + holds + fx_said)
                scored(look)
                # (asked again here: "!image off" typed while this beat was being worked out must not be undone by it)
                emit({"type": "visual", "seq": seq, **look, **knob, **({"image": on_pictures} if on_pictures is not None and image_by["on"] else {})})
            film_if_asked()
            sample_if_asked()
            interpret_if_asked()
            watch()
            if stale():
                continue
            if structured and not stop.is_set() and (card or "image" in roles or video_on[0]):
                # Structured: llama fills in a short card and the picture prompt is written from it here. With
                # "inline" the card came with the beat; if it did not, or says nothing of what happens, it is
                # asked for on its own. Whatever is still missing is filled in by code; llama is not asked twice. With
                # no card at all (llama has stopped answering) the picture is made in the plainer way.
                if not read_slots(card, CARD).get("does"):
                    card = chat([{"role": "system", "content": CARD_ALONE + roles["card"]},
                                 {"role": "user", "content": book.card_request(beat, notes)}],
                                {"num_predict": 260}, writing("prompt", seq, f"writing shot card {seq}"))
                if stale():
                    continue
                card = book.take_card(seq, card, beat)
                if with_card:                  # llama is shown its cards in one tidy form, so it keeps writing them
                    turn["content"] = beat + "\n\n" + book.render(card)
                for key in card["new"]:
                    person = book.cast.people[key]
                    tell("picture", f"{person['name']} joins the story" + (f": {person['kind']}" if person["kind"] else "")
                         + ". They look and sound the same from here on.")
                if card["filled"]:
                    say(f"shot card {seq}: left to code: {', '.join(card['filled'])}")
                if "image" in roles:
                    prompt = picture_for(seq)
                    paint(seq, prompt)
                    tell("picture", f"Picture {seq} is being painted for beat {seq}: {prompt[:120].rstrip()}...")
            elif not structured and "image" in roles and not stop.is_set():
                prompt = chat([{"role": "system", "content": roles["image"]}, {"role": "user", "content": beat}],
                              {"num_predict": 420}, writing("prompt", seq, f"writing image prompt {seq}"))
                prompt = " ".join(prompt.split())
                if stale():
                    continue
                if prompt:
                    paint(seq, prompt, llama_wrote=True)
                    tell("picture", f"Picture {seq} is being painted for beat {seq}: {prompt[:120].rstrip()}...")
                elif not stop.is_set():        # nothing from llama: the picture is put together here from the beat's own words
                    book.take_card(seq, "", beat)
                    prompt = picture_for(seq)
                    paint(seq, prompt)
                    tell("picture", f"Picture {seq} is being painted for beat {seq} from the beat's own words, without llama's "
                                    f"prompt: {prompt[:120].rstrip()}...")
            if (video_on[0] and "video" in roles and seq >= 2 and seq > base[0] and seq - 1 != joined[0] and not stop.is_set() and not stale()
                    and (video_now.is_set() or not args.journeys_on_demand)):
                write_journey(seq, notes)      # the video starts on the previous beat's picture and arrives at this one's
                video_now.clear()
            previous_beat = beat
            remaining = args.interval - (time.time() - started)
            if args.beats and seq >= args.beats:
                break
            if remaining > 0:
                status("idle", "pausing before the next beat")
                until = time.time() + remaining
                while time.time() < until and not stop.is_set() and not video_now.is_set() and not stale() and reading.empty() and samples.empty():
                    time.sleep(0.2)                # a film asked for, or a fresh start, does not wait out the pause
            # (straight after a recall there is no picture to start from: the film waits for the beat after)
            if video_now.is_set() and "video" in roles and not stop.is_set() and seq - 1 != joined[0]:      # asked for mid-session
                video_now.clear()
                if seq >= 2 and filmed[0] < seq:
                    write_journey(seq, [])
                elif seq < 2:
                    say("video: it needs two pictures; the first journey will be written after the next beat", always=True)
    except ApiError as e:
        reason = f"llama error: {str(e)[:120]}"
        say(reason, always=True)
    except KeyboardInterrupt:
        pass
    except OSError:
        pass   # whoever was reading the stream went away
    finally:
        stop.set()
        ended = f"story stopped: {reason}" if reason else "story ended"
        for text, action in ((ended + " - clearing llama's memory", lambda: llama.close(keep_loaded=args.keep_loaded, restart=not args.no_restart)),
                             (ended + " - llama cleared", None)):
            try:
                status("error" if reason else "stop", text)
            except OSError:
                pass
            if action:
                action()
        # the keyboard listener thread is still blocked reading the terminal; a normal interpreter
        # shutdown would trip over it ("could not acquire lock ... at interpreter shutdown")
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except OSError:
            pass
        os._exit(0)


if __name__ == "__main__":
    main()
