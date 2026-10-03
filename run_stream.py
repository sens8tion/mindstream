"""mindstream: the whole chain in one command. Nothing is saved.

    you type a guide -> story-feed (llama, over SSH) -> image prompts -> img-gen (this GPU) -> viewer
                                                     -> journey prompts -> vid-gen (this GPU, in interludes)

Each story beat appears as a caption when its picture is finished. The stages are connected with
direct pipes owned by this launcher, so the stream flows continuously (a PowerShell pipe between
programs would hold everything back until the end).

Cadence   New prompts from llama arrive slowly; --cadence S fills the gaps by re-rendering the current
          prompt from a different angle every S seconds. Type "!cadence 20" to change it while running.
Video     --video off        pictures only
          --video interlude  every few beats the image model steps aside and one journey between two
                             recent pictures is filmed (about a minute per second of video)
          --video reel       every consecutive pair of pictures is filmed, in order: one continuous video
                             whose segments start and end on the story's pictures
          --video-preset test|indulge sets sensible lengths and sizes for either
Demo      --demo runs the whole thing with stand-in stages (test cards and beeps): no llama, no models.
"""
import argparse
import collections
import ctypes
import json
import msvcrt
import os
import random
import re
import shlex
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
from mindstream.local import comfy_python, forge_python  # noqa: E402

# the picture model runs in a Forge environment: chosen in models.local.json, or with MINDSTREAM_PYTHON
GPU_PYTHON = forge_python()
# the moving visuals need glfw + PyOpenGL: installed in the project's own environment (the one the
# AMD text-encoder helper also uses)
GL_PYTHON = os.environ.get("MINDSTREAM_GL_PYTHON", os.path.join(HERE, ".venv-dml", "Scripts", "python.exe"))
# the video model only loads through ComfyUI's code, so vid-gen runs in ComfyUI's environment
COMFY_PYTHON = comfy_python()      # models.local.json, or MINDSTREAM_COMFY_PYTHON
VARIATIONS = os.path.join(HERE, "prompts", "variations.txt")
PRESETS = {"test": {"video_seconds": 1.5, "video_megapixels": 0.25, "video_every": 2},
           "indulge": {"video_seconds": 3.0, "video_megapixels": 0.41, "video_every": 1}}
MAX_FILM_SECONDS = 3.0


CONSOLE = False     # set by --console: also say on the terminal what the viewer already shows


def say(msg, always=False):
    """A message for the terminal. By default only what cannot be shown in the viewer is printed (it will not
    start, or it has gone); what was typed and how it was read stay in the viewer, and nowhere else."""
    if CONSOLE or always:
        print(f"[mindstream] {msg}", file=sys.stderr, flush=True)


def split_args(text):
    """Split an option string the Windows way: backslashes in paths survive, quotes group words."""
    return [a[1:-1] if len(a) > 1 and a[0] == a[-1] and a[0] in "\"'" else a for a in shlex.split(text, posix=False)]


from mindstream.outbox import Outbox  # noqa: E402


def line(obj):
    return (json.dumps(obj) + "\n").encode("ascii", "replace")


class Session:
    def __init__(self, args):
        self.args = args
        self.lock = threading.Lock()              # guards writes to the viewer
        # every child's input is written by an outbox of its own (mindstream/outbox.py), so that no thread here ever
        # waits on a child that is busy: one slow part used to stop the others dead
        self.boxes, self.feed_box = {}, None
        self.beats = {}                           # beat number -> story text
        self.pictures = {}                        # beat number -> base64 of its first finished picture
        self.journeys = collections.deque()       # journey prompts waiting to be filmed
        self.pending = collections.deque()        # image prompts waiting for the image generator to be up
        self.order = []                           # for the current img-gen: (beat, is_first_picture_of_beat) per prompt sent
        self.sent = self.done = 0                 # prompts sent to / pictures finished by the current img-gen
        self.cadence = args.cadence
        self.last_prompt = None                   # (prompt text, beat)
        self.last_send = 0.0
        self.last_filmed = 0                      # the "to" beat of the last journey filmed
        self.swapping = self.feed_done = self.closing = self.film_next = self.bye = False
        self.gen = self.vid = None
        self.modifiers = self.load_modifiers()

        quiet = [] if args.verbose else ["--quiet"]
        hush = [] if args.console or args.verbose else ["--hush"]
        fake = [GL_PYTHON, "-B", os.path.join(HERE, "demo", "fake_stage.py")]
        view_python, view_script = GPU_PYTHON or sys.executable, "img_view.py"
        if args.visual == "flux":
            if os.path.exists(GL_PYTHON) and subprocess.run([GL_PYTHON, "-c", "import glfw, OpenGL, numpy, PIL"],
                                                            capture_output=True).returncode == 0:
                view_python, view_script = GL_PYTHON, "gl_view.py"
            else:
                say("the OpenGL libraries (glfw, PyOpenGL) were not found; using the plain viewer", always=True)
        self.watched = True                               # false while the viewer is minimised: nothing is made then
        watching = ["--report-watching", *hush] if view_script == "gl_view.py" else []
        self.viewer = subprocess.Popen([view_python, "-B", os.path.join(HERE, view_script), *watching, *split_args(args.view_args)],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE if watching else None)
        if watching:
            threading.Thread(target=self.pump_viewer, daemon=True).start()
        self.gen_cmd = (fake + ["gen"]) if args.demo else [
            GPU_PYTHON, "-B", "-W", "ignore", os.path.join(HERE, "img_gen.py"),
            *([] if args.no_previews else ["--previews"]), *quiet, *split_args(args.gen_args)]
        self.vid_cmd = (fake + ["vid"]) if args.demo else [
            COMFY_PYTHON, "-B", "-W", "ignore", os.path.join(HERE, "vid_gen.py"), "--megapixels", str(args.video_megapixels),
            *quiet, *split_args(args.vid_args)]
        video = [*(["--video"] if args.video != "off" else []), "--video-seconds", str(args.video_seconds)]
        self.asked_at = 0.0                               # when the story feed was last asked for a film prompt
        self.puller = None                                # the sample puller's process, once something has been asked of it
        # The two panels, each a window of its own, opened at the start (--knobs, --visuals) or from the viewer
        # (Ctrl+K, Ctrl+V) and closed the same way: the knob panel, with a knob for every part of the music; and the
        # visuals panel, with the session's pictures and films and the look.
        self.panel, self.visuals = None, None
        self.story_from = 0                               # the beat the present story began at: older pictures belong to a theme put aside
        # A pipe we never write to: when we close it (or die), the feed sees end-of-file and shuts down
        # cleanly, unloading the model and restarting Ollama so the story leaves llama's memory.
        stop_r, self.stop_w = os.pipe()
        os.set_inheritable(stop_r, True)
        feed_cmd = (fake + ["feed"]) if args.demo else [sys.executable, "-B", os.path.join(HERE, "story_feed.py"),
                                                        "--stop-handle", str(msvcrt.get_osfhandle(stop_r)),
                                                        "--journeys-on-demand", "--cadence-now", str(args.cadence), "--video-mode", args.video, *quiet, *hush]
        self.feed = subprocess.Popen([*feed_cmd, "--beats", str(args.beats), "--interval", str(args.interval), *video,
                                      *split_args(args.feed_args)],
                                     stdout=subprocess.PIPE,   # stdin stays the console: you type the guide into it
                                     close_fds=False)
        os.close(stop_r)
        for which in ("knobs", "visuals"):                # only now: some of what the knob panel says is for the feed
            if getattr(args, which):
                self.toggle_panel(which)
        self.start_gen()
        for target in (self.pump_feed, self.schedule):
            threading.Thread(target=target, daemon=True).start()

    @staticmethod
    def load_modifiers():
        try:
            with open(VARIATIONS, encoding="utf-8") as f:
                found = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        except OSError:
            found = []
        return found or ["Seen from much further away.", "An extreme close-up of one detail of it.", "Seen from directly above."]

    # ------------------------------------------------------------------ plumbing

    def box(self, proc):
        """The outbox for a child process's input, made the first time it is wanted."""
        made = self.boxes.get(id(proc))
        if made is None or made[0] is not proc:
            # the viewer is sent the pictures and films themselves: none of those may be let go, however far behind it is
            most = 100000 if proc is self.viewer else 400
            made = self.boxes[id(proc)] = (proc, Outbox(proc.stdin.write, proc.stdin.flush, proc.stdin.close, most=most, name="to child"))
        return made[1]

    def to_proc(self, proc, data, latest=None):
        """A line for a child process, queued: False if the child has gone. `latest`: see Outbox.put."""
        if proc is None or proc.poll() is not None:
            return False
        return self.box(proc).put(data, latest)

    def to_feed(self, message):
        """A message down the pipe to the story feed, queued in the same way."""
        if self.stop_w is None:
            return False
        if self.feed_box is None:
            stop_w = self.stop_w
            self.feed_box = Outbox(lambda data: os.write(stop_w, data), name="to feed")
        return self.feed_box.put(line(message))

    def to_viewer(self, data):
        return self.to_proc(self.viewer, data)

    def status(self, source, kind, text, detail=""):
        self.to_viewer(line({"type": "status", "source": source, "kind": kind, "seq": 0, "text": text, "detail": detail}))

    def toggle_panel(self, which):
        """Open a panel, or close it if it is open. The viewer, which asks for this, then tells the panel how things
        stand and sends it its small pictures again."""
        name = "panel" if which == "knobs" else "visuals"
        running = getattr(self, name)
        if running is not None and running.poll() is None:
            running.terminate()
            setattr(self, name, None)
            return
        try:
            proc = subprocess.Popen([GL_PYTHON, "-B", os.path.join(HERE, "knob_panel.py" if which == "knobs" else "visual_panel.py")],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except OSError:
            say(f"the {which} panel could not be started", always=True)
            return
        setattr(self, name, proc)
        take = self.from_panel if which == "knobs" else self.from_visuals
        threading.Thread(target=lambda: [take(raw) for raw in proc.stdout], daemon=True).start()

    def from_visuals(self, raw):
        """A line from the visuals panel: for the viewer, unless it is something to say to the story feed (a picture
        or a film asked for by its buttons), which is handed on as if it had been typed."""
        try:
            said = json.loads(raw).get("steer")
        except (ValueError, AttributeError):
            said = None
        if not said:
            self.to_viewer(raw)
        elif self.stop_w is not None and not self.args.demo:
            try:
                self.to_feed(({"steer": str(said)[:400]}))
            except OSError:
                pass

    def from_panel(self, raw):
        """A line from the knob panel. All of it is for the viewer, which holds the music, except that "memorise"
        and "recall" are also about the story, which the feed holds: memorise goes to both; recall goes to the feed,
        which puts the story back and then has the viewer told, so that the viewer lets the present pictures go
        before it brings the kept ones back."""
        try:
            message = json.loads(raw)
            said = message.get("steer")
        except (ValueError, AttributeError):
            message, said = None, None
        if said:                                           # the tempo and the archetype are the story feed's to hold: said as if typed
            if self.stop_w is not None and not self.args.demo and self.feed.poll() is None:
                try:
                    self.to_feed(({"steer": str(said)[:200]}))
                    return
                except OSError:
                    pass
            if isinstance(message.get("pull"), dict):      # a sound asked for, and no feed to ask through: pulled from here
                self.pull(message["pull"])
            if isinstance(message.get("direct"), dict):    # no feed to hold it (the stand-in session): straight to the viewer
                self.to_viewer(line({"type": "visual", "seq": 0, **message["direct"]}))
            return
        try:
            slot = int(message["memorise"] if "memorise" in message else message["recall"])
        except (ValueError, KeyError, TypeError):
            self.to_viewer(raw)                            # knobs, mutes, patches: nothing to do with the story
            return
        told = False
        if not self.args.demo and self.stop_w is not None and self.feed.poll() is None:
            try:
                self.to_feed(({"memorise" if "memorise" in message else "recall": slot}))
                told = True
            except OSError:
                pass
        if "memorise" in message or not told:              # with no feed to answer a recall, the music at least goes back
            self.to_viewer(raw)

    def stop_feed(self):
        """Ask the feed to finish: it unloads the model and restarts Ollama before it exits."""
        if self.stop_w is not None:
            try:
                os.close(self.stop_w)
            except OSError:
                pass
            self.stop_w = None

    # ------------------------------------------------------------------ the image generator

    def start_gen(self):
        self.order, self.sent, self.done = [], 0, 0
        self.gen = subprocess.Popen(self.gen_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        threading.Thread(target=self.pump_gen, args=(self.gen,), daemon=True).start()
        while self.pending:                               # prompts that arrived while it was away
            self.send_prompt(*self.pending.popleft())

    def stop_gen(self):
        gen, self.gen = self.gen, None
        if gen is None:
            return
        try:
            gen.stdin.close()                             # it finishes the picture in hand and exits
        except OSError:
            pass
        try:
            gen.wait(timeout=180)
        except subprocess.TimeoutExpired:
            gen.terminate()

    def pump_viewer(self):
        """The viewer reports whether it is being watched. Unwatched, nothing new is made: the story feed is told
        to wait, picture prompts are held, no film is started. It all resumes when the window is back."""
        for raw in self.viewer.stdout:
            try:
                message = json.loads(raw)
                if message.get("panel") in ("knobs", "visuals"):    # Ctrl+K or Ctrl+V in the viewer: that panel, opened or closed
                    self.toggle_panel(message["panel"])
                    continue
                if "state" in message:                              # how things stand: both panels follow the session (only the newest matters)
                    for proc in (self.panel, self.visuals):
                        self.to_proc(proc, raw, latest="state")
                    continue
                if "shelf" in message or "shelf_gone" in message:   # for the visuals panel: something new on the shelf, or let go from it
                    self.to_proc(self.visuals, raw)
                    continue
                if "thumb" in message or "arrived" in message:      # for the knob panel: a memory's small picture; where the timeline has got to
                    self.to_proc(self.panel, raw)
                    continue
                if message.get("steer") and self.stop_w is not None:    # typed in the viewer: hand it to the story feed
                    self.to_feed(({"steer": str(message["steer"])}))
                watched = bool(message["watched"])
            except (ValueError, KeyError, TypeError, OSError):
                continue
            if watched == self.watched:
                continue
            self.watched = watched
            say("watched again: carrying on" if watched else "nobody is watching (window minimised): holding the story, pictures and film")
            if self.stop_w is not None:
                try:
                    self.to_feed(({"pause": not watched}))
                except OSError:
                    pass
            if watched and self.gen is not None:
                while self.pending:
                    self.send_prompt(*self.pending.popleft())

    def send_prompt(self, prompt, beat, first=True):
        if self.gen is None or not self.watched:          # away for a video interlude, or unwatched: keep only the newest few
            self.pending.append((prompt, beat, first))
            while len(self.pending) > 2:
                self.pending.popleft()
            return
        try:
            self.gen.stdin.write((json.dumps({"prompt": prompt}) + "\n").encode("utf-8"))
            self.gen.stdin.flush()
        except (OSError, ValueError):
            return
        self.order.append((beat, first))
        self.sent += 1
        self.last_send = time.time()
        if first:
            self.last_prompt = (prompt, beat)

    def pump_gen(self, gen):
        for raw in gen.stdout:
            if raw.startswith(b'{"type": "image"'):             # a picture, or one forming: of the story as it is now?
                found = re.search(rb'"seq": (\d+)', raw[:200])
                n = int(found.group(1)) if found else 0
                beat = self.order[n - 1][0] if 0 < n <= len(self.order) else None
                if beat is not None and beat < self.story_from:     # painted for a theme that has been put aside: never shown
                    if b'"final": true' in raw[:120]:
                        self.done = max(self.done, n)
                    continue
            if not self.to_viewer(raw):
                break
            if raw.startswith(b'{"type": "image"') and b'"final": true' in raw[:120]:
                try:
                    frame = json.loads(raw)
                except ValueError:
                    continue
                n = frame.get("seq", 0)
                beat, first = self.order[n - 1] if 0 < n <= len(self.order) else (None, False)
                self.done = max(self.done, n)
                if first and beat is not None:
                    self.pictures[beat] = frame["data"]
                    for old in [b for b in self.pictures if b < beat - 6]:   # keep only recent pictures in memory
                        del self.pictures[old]
                if beat in self.beats:
                    self.to_viewer(line({"type": "text", "text": self.beats[beat]}))
        code = gen.wait()
        if code != 0 and not self.swapping and not self.closing and gen is self.gen:
            # without an image generator there is no point having llama write: stop it, leave the window
            # open so the reason stays readable in the flow strip
            say("the image generator stopped; ending the story feed", always=True)
            self.gen = None
            self.stop_feed()

    # ------------------------------------------------------------------ the story feed

    def pump_feed(self):
        for raw in self.feed.stdout:
            try:
                item = json.loads(raw)
            except ValueError:
                continue
            kind = item.get("type")
            if kind in ("status", "visual", "read"):
                self.to_viewer(raw)        # what llama is doing (flow strip), and how the visuals should move
            elif kind == "story":
                self.beats[item["seq"]] = item["text"]
                for old in [b for b in self.beats if b < item["seq"] - 6]:
                    del self.beats[old]
            elif kind == "prompt" and item.get("target") == "image":
                self.send_prompt(item["prompt"], item["seq"])
            elif kind == "prompt" and item.get("target") == "video":
                self.journeys.append(item)
                self.asked_at = 0.0
            elif kind == "control":
                if item.get("fresh"):                       # a new theme: nothing of the old story is filmed or repainted
                    self.journeys.clear()
                    self.pending.clear()
                    self.pictures.clear()
                    self.last_prompt, self.last_filmed, self.asked_at = None, int(item["fresh"]), 0.0
                    self.story_from = int(item["fresh"])     # pictures still being painted for earlier beats are not shown
                    self.to_viewer(line({"type": "fresh"}))
                # "memorise" and "recall" typed, or a recall the feed has answered: the viewer keeps or brings back the
                # music and its pictures. A recall comes after the "fresh" above, never before it.
                if "recalled" in item:
                    self.to_viewer(line({"type": "visual", "seq": -1, "recall": int(item["recalled"])}))
                if "memorise" in item:
                    self.to_viewer(line({"type": "visual", "seq": -1, "memorise": int(item["memorise"])}))
                if item.get("theme"):                       # the theme, to be shown as words until there is a picture
                    self.to_viewer(line({"type": "theme", "text": str(item["theme"])[:400]}))
                if item.get("bye"):                         # /bye: stop making things now; the window closes when llama is cleared
                    self.bye = self.closing = True
                    say("stopping: clearing llama, then closing the viewer")
                    self.stop_gen()
                    if self.vid is not None and self.vid.poll() is None:
                        self.vid.terminate()
                if isinstance(item.get("pull"), dict):      # a sample asked for: found, fetched into memory and passed to the viewer
                    self.pull(item["pull"])
                if item.get("repaint"):                     # the pictures are being replaced: the viewer lets the old ones go
                    self.to_viewer(line({"type": "fresh", "what": "pictures"}))
                if item.get("video") in ("off", "interlude", "reel", "ask"):
                    self.args.video = item["video"]
                elif item.get("video") in ("now", "on"):
                    # a single film asked for while video is off does not switch regular filming on
                    self.args.video = self.args.video if self.args.video != "off" else ("ask" if item.get("once") else "interlude")
                    self.asked_at = 0.0
                    self.film_next = item["video"] == "now"      # do not wait for the usual number of beats
                if item.get("picture_now") and item.get("prompt") and "beat" in item:
                    self.send_prompt(item["prompt"], int(item["beat"]), first=False)      # asked for outright ("!pic ..."): painted next, or after the film being made
                elif item.get("picture_now") and self.last_prompt and not self.swapping:
                    # a steer about the story: the present scene is painted again with the steer leading the prompt,
                    # so something answers within seconds instead of waiting for llama's next beat
                    # (the feed sends the whole prompt, put together from what it knows of the scene; without one, the
                    # steer is simply put in front of the last prompt)
                    prompt, beat = self.last_prompt
                    self.send_prompt(item.get("prompt") or f"{str(item['picture_now'])[:300].rstrip('. ')}. {prompt}", beat, first=False)
                if "cadence" in item:
                    self.cadence = max(float(item["cadence"]), 0.0)
                    say(f"a new picture every {self.cadence:g}s" if self.cadence else "pictures only when the story supplies a new prompt")
        self.feed_done = True
        if self.bye and self.viewer.poll() is None:         # asked to stop, and llama has been cleared: the window closes
            self.viewer.terminate()

    # ------------------------------------------------------------------ cadence and video interludes

    def idle(self):
        return self.gen is not None and self.sent == self.done

    def ask_for_journey(self):
        """Film prompts are slow to write, so one is asked for only when it will be used: nothing is waiting
        to be filmed, the film generator is free, and the mode's wait since the last film is over."""
        if (self.args.video == "off" or self.args.demo or self.journeys or self.swapping or self.stop_w is None
                or len(self.pictures) < 2 or time.time() - self.asked_at < 300):
            return
        newest = max(self.pictures)
        if self.args.video == "ask" and not self.film_next:
            return                                          # films only when asked for (!film)
        if self.last_filmed == 0 and not self.film_next:
            # The first film: as soon as there are two pictures (the guide's and the first beat's), and put
            # together in code rather than written by llama, so it is being made within the first minutes.
            self.asked_at = time.time()
            try:
                self.to_feed(({"journey": True, "plain": True}))
            except OSError:
                pass
            return
        if self.film_next or newest - self.last_filmed >= (1 if self.args.video == "reel" else self.args.video_every):
            self.asked_at = time.time()
            try:
                self.to_feed(({"journey": True}))
            except OSError:
                pass

    def knob_for(self, name):
        """Tell the knob panel there is a new layer, so it gets a knob of its own."""
        if name:
            self.to_proc(self.panel, line({"layer": str(name)}))

    def pull(self, wanted):
        """Hand a request to the sample puller (sample_pull.py, started the first time it is needed)."""
        if str(wanted.get("role", "")) in ("loop", "texture"):
            self.knob_for(wanted.get("name"))
        if self.puller is None or self.puller.poll() is not None:
            try:
                self.puller = subprocess.Popen([GL_PYTHON, "-B", "-W", "ignore", os.path.join(HERE, "sample_pull.py"), "serve"],
                                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            except OSError:
                return
            threading.Thread(target=lambda out=self.puller.stdout: [self.to_viewer(raw) for raw in out], daemon=True).start()
        try:
            self.puller.stdin.write(line({k: str(wanted.get(k, ""))[:80] for k in ("query", "role", "where", "name")}))
            self.puller.stdin.flush()
        except (OSError, ValueError):
            pass

    def due_journey(self):
        """The journey to film now, if any: both of its pictures must exist."""
        ready = [j for j in self.journeys if j.get("free") or (j["from"] in self.pictures and j["to"] in self.pictures)]
        if self.args.video == "off" or not ready:
            return None
        free = [j for j in ready if j.get("free")]
        if free:
            return free[0]                                 # a clip asked for to chop: it needs no pictures, and does not wait
        if self.args.video == "reel":
            return ready[0]                                # every pair, in order
        newest = ready[-1]                                 # interlude: the latest pair, once enough beats have passed
        if self.last_filmed == 0 and self.args.video != "ask":
            return newest                                  # the first film is made as soon as it can be
        if self.args.video == "ask":
            return newest if self.film_next else None      # only when asked
        return newest if self.film_next or newest["to"] - self.last_filmed >= self.args.video_every else None

    def schedule(self):
        while not self.closing:
            time.sleep(0.4)
            if self.viewer.poll() is not None:
                return
            if not self.watched:
                continue
            self.ask_for_journey()
            journey = self.due_journey()
            if journey is not None and self.idle():
                self.interlude(journey)
            elif (self.cadence > 0 and self.idle() and self.done > 0 and self.last_prompt
                  and time.time() - self.last_send >= self.cadence):
                prompt, beat = self.last_prompt             # same scene, different angle
                self.send_prompt(f"{prompt} {random.choice(self.modifiers)}", beat, first=False)
            elif self.feed_done and self.gen is not None and self.idle() and self.due_journey() is None:
                self.closing = True                         # the story is over and everything owed has been made
                self.stop_gen()
                if self.viewer is not None:
                    self.box(self.viewer).close()           # (after what is queued for it); the viewer keeps going until it is closed
                return

    def interlude(self, journey):
        """The image model steps aside, one journey is filmed, the image model comes back."""
        free = bool(journey.get("free"))                   # a clip to chop: made from words alone, outside the story's films
        self.journeys = collections.deque(j for j in self.journeys if (j is not journey if free else j.get("free") or j["to"] > journey["to"]))
        self.swapping, self.film_next = True, False
        self.status("video", "load", "interlude: making room to film a clip to chop" if free
                    else f"interlude: making room to film journey {journey['from']} to {journey['to']}")
        self.stop_gen()
        self.status("image", "stop", "stepped aside for the video model")
        self.to_viewer(line({"type": "read", "stream": "film", "text":
                             ("Filming the clip to chop now, " if free else f"Filming picture {journey['from']} to {journey['to']} now, ")
                             + f"{journey.get('seconds', self.args.video_seconds):g} "
                             "seconds of it. The picture model has stepped aside to make room, so no new pictures until it is done "
                             "(roughly a minute per second of film)."}))
        self.status("encoder", "stop", "stepped aside for the video model")
        request = {"prompt": journey["prompt"], "seconds": journey.get("seconds", self.args.video_seconds), "bpm": journey.get("bpm", 120)}
        if not free and not self.args.video_free:          # a story film starts on one picture and arrives at the next
            request.update(first=self.pictures[journey["from"]], last=self.pictures[journey["to"]])
        try:
            self.vid = subprocess.Popen(self.vid_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self.vid.stdin.write(line(request))
            self.vid.stdin.close()                          # one journey per interlude; it exits when done
            for raw in self.vid.stdout:
                if raw.startswith(b'{"type": "clip"'):
                    try:
                        clip = json.loads(raw)
                        clip.update(seq=journey["to"], bpm=journey.get("bpm", 120), follows=not free and self.last_filmed == journey["from"],
                                    layer=str(journey.get("name", "")))
                        self.knob_for(journey.get("name"))
                        self.hear(clip)
                        raw = line(clip)
                    except ValueError:
                        pass
                self.to_viewer(raw)
            if self.vid.wait() != 0:
                self.status("video", "error", "the video model stopped", detail=f"exit code {self.vid.returncode}")
            else:
                if not free:
                    self.last_filmed = journey["to"]
                self.status("video", "stop", "the clip to chop is filmed; back to pictures" if free
                            else f"journey {journey['from']} to {journey['to']} filmed; back to pictures")
        except OSError as e:
            self.status("video", "error", "could not start the video model", detail=str(e)[:100])
        self.vid = None
        if not self.closing:
            self.start_gen()
        self.swapping = False

    def hear(self, clip):
        """Measure the tempo of a clip's soundtrack. The viewer locks its pulse to it, and the feed is told,
        so the next segment's music (and everything else) follows what was actually heard."""
        try:
            import base64
            sys.path.insert(0, HERE)
            from mindstream import tempo
            audio = clip.get("audio") or {}
            found = tempo.detect(base64.b64decode(audio["data"]), int(audio["rate"]), int(audio["channels"]), hint=float(clip["bpm"]))
        except Exception:      # no numpy, no audio, odd data: the visuals simply keep the asked-for tempo
            found = None
        if found and found["confidence"] >= 2.5 and abs(found["bpm"] / float(clip["bpm"]) - 1) <= 0.2:
            clip["tempo"] = {"bpm": round(found["bpm"], 2), "offset": round(found["offset"], 3)}
            if self.stop_w is not None:
                try:
                    self.to_feed(({"bpm": found["bpm"]}))
                except OSError:
                    pass

    def close(self):
        self.closing = True
        for proc in (self.gen, self.vid, self.puller, self.panel, self.visuals):
            if proc is not None and proc.poll() is None:
                proc.terminate()
        if self.feed.poll() is None and self.args.demo:
            self.feed.terminate()
        elif self.feed.poll() is None:
            # ask, don't kill: the feed must unload the model and restart Ollama so the story leaves llama's memory
            say("closing: waiting for the story feed to clear llama (can take up to a minute)", always=True)
            try:
                self.stop_feed()
                self.feed.wait(timeout=90)
            except (subprocess.TimeoutExpired, OSError):
                say("the story feed did not stop cleanly; ending it. Ollama on llama was NOT restarted.", always=True)
                self.feed.terminate()
        if self.viewer.poll() is None:
            self.viewer.terminate()


def main():
    ap = argparse.ArgumentParser(description="Story on llama -> images (and video interludes) on this GPU -> viewer, all in memory")
    ap.add_argument("--beats", type=int, default=0, help="stop after this many beats (0 = until you type /bye)")
    ap.add_argument("--interval", type=float, default=15.0, help="seconds per beat")
    ap.add_argument("--cadence", type=float, default=0.0,
                    help="seconds between new pictures: gaps between the story's prompts are filled with the same scene "
                         "from other angles (0 = off; about 14 is as fast as the GPU goes)")
    ap.add_argument("--video", choices=["off", "ask", "interlude", "reel"], default="off",
                    help="off: pictures only; interlude: film one journey every few beats; reel: film every consecutive pair")
    ap.add_argument("--video-preset", choices=sorted(PRESETS), help="test: 1.5 s small clips every 2 beats; indulge: 3 s clips for every pair")
    ap.add_argument("--video-every", type=int, default=3, help="interlude mode: beats between journeys")
    ap.add_argument("--video-seconds", type=float, default=1.5, help="length of each film (3 at most)")
    ap.add_argument("--video-megapixels", type=float, default=0.41, help="video frame area (0.41 is about 640x640)")
    ap.add_argument("--video-free", action="store_true", help="do not pin the journey to the story's pictures (text-to-video)")
    ap.add_argument("--visual", choices=["flux", "plain"], default="flux",
                    help="flux: the picture on a spinning, pulsing surface with trails (OpenGL); "
                         "plain: a still picture that crossfades")
    ap.add_argument("--no-previews", action="store_true", help="show only finished images")
    ap.add_argument("--demo", action="store_true", help="stand-in stages (test cards, beeps): no llama, no models loaded")
    ap.add_argument("--console", action="store_true",
                    help="also print on the terminal what was typed, how it was read and what is happening "
                         "(by default all of that is shown in the viewer only)")
    ap.add_argument("--verbose", action="store_true",
                    help="print every stage's progress messages in the terminal (they are always shown in the viewer)")
    ap.add_argument("--feed-args", default="", help='extra options for story-feed, e.g. "--interval 30"')
    ap.add_argument("--gen-args", default="", help='extra options for img-gen, e.g. "--shift 6 --width 768 --height 1344"')
    ap.add_argument("--vid-args", default="", help='extra options for vid-gen, e.g. "--steps 20 --lora \'\'"')
    ap.add_argument("--view-args", default="", help='extra options for the viewer, e.g. "--fullscreen"')
    ap.add_argument("--visuals", action="store_true",
                    help="open the visuals panel: every picture and film of the session, to drag back onto the screen, and the look")
    ap.add_argument("--knobs", action="store_true", help="open the knob panel: a knob for every part of the music, and the super knob")
    ap.add_argument("--skin", choices=("acid", "ember", "ice"), default=None,
                    help="the panels' colours: acid (black and lime, the usual), ember (black and orange-red) or ice (black and cyan)")
    # "--gen-args --verbose": glue the value on with "=", or argparse mistakes it for another option
    argv, raw = [], sys.argv[1:]
    while raw:
        a = raw.pop(0)
        argv.append(f"{a}={raw.pop(0)}" if a in ("--feed-args", "--gen-args", "--vid-args", "--view-args") and raw else a)
    args = ap.parse_args(argv)
    if args.skin:                                       # the panels are started from here, and take their colours from this
        os.environ["MINDSTREAM_SKIN"] = args.skin
    global CONSOLE
    CONSOLE = args.console or args.verbose
    if args.video_preset:
        for key, value in PRESETS[args.video_preset].items():
            setattr(args, key, value)
        if args.video == "off":
            args.video = "reel" if args.video_preset == "indulge" else "interlude"
    args.video_seconds = min(max(args.video_seconds, 0.9), MAX_FILM_SECONDS)
    if not args.demo:                                   # the two environments the generators run in (models.local.json)
        if not GPU_PYTHON:
            sys.exit('[mindstream] no Forge Python chosen for the picture generator: set "forge_python" (or "forge_dir") '
                     'in models.local.json (see models.example.json), or MINDSTREAM_PYTHON')
        if not COMFY_PYTHON and args.video != "off":
            sys.exit('[mindstream] no ComfyUI Python chosen for the film generator: set "comfy_python" (or "comfy_dir") '
                     'in models.local.json (see models.example.json), or start with --video off')

    # One session at a time on this machine: a second one would fight the first for the GPU, RAM and llama.
    # (The demo loads nothing, so it gets its own lock and can run beside a real session.)
    global _session_lock
    _session_lock = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\mindstream-demo" if args.demo else "Local\\mindstream-session")
    if ctypes.windll.kernel32.GetLastError() == 183:   # ERROR_ALREADY_EXISTS
        sys.exit("[mindstream] a mindstream session is already running on this machine; close it first")

    session = Session(args)
    try:
        session.viewer.wait()                 # closing the window ends the session
    except KeyboardInterrupt:
        pass
    finally:
        session.close()


if __name__ == "__main__":
    main()
