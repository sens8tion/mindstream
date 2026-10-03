"""gl-view: the mindstream as a moving, GPU-rendered thing. Nothing is written to disk.

Reads the same stream as img-view (image, text and status frames, one JSON object per line) and
draws it with OpenGL:

  - the current picture is the skin of a faceted surface that spins and pulses, morphing between a
    sphere, a torus and a twisted ribbon; every cycle it opens out flat and nearly still for a few
    seconds, so the picture can actually be seen, then folds back into motion
  - a new picture always arrives flat, with a flash, before it is swept up
  - earlier pictures orbit as a swarm of shards
  - the whole frame feeds back into itself (zoom, rotation, kaleidoscope folds), leaving trails
  - everything kicks on a beat (--bpm); colour splits apart on each kick

How it moves (tempo, violence, shapes, mirrors, trails, colour cast) can be set by "visual" frames in the
stream: the story feed sends one per beat, written by the model from the beat and your steering.

Video clips ("clip" frames) join a reel that plays in order and loops, on the same surface. A clip's first
showing is held flat so it can be watched; after that it is swept into the motion like the pictures.
Only the segment being played is heard. A new still picture takes the surface briefly, then the reel resumes.

The effects (mindstream/effects.py) run over the whole finished frame ("bloom": 0.8 in a visual frame) and, as well,
over each picture by itself before it is placed ("image": {"bloom": 0.8}, or "image:bloom": 0.8): see prepare_images.

A "visual" frame may also carry "memorise": n or "recall": n. Memorise keeps what is on screen under that number
(the last two finished pictures, the swarm, the caption, the reel, how it moves and its colour), next to what the
mixer keeps of the music; recall puts it back. All of it is held in memory as images, never written anywhere.

What it says on stdout, one JSON object per line, when a launcher is listening (--report-watching):
{"steer": "..."} a line typed in the window, {"watched": true/false} whether the window is being looked at, and
{"thumb": n, "png": "<base64>"} a 64x64 picture of the middle of the screen as it was when n was memorised.

Keys: F fullscreen, M overlay (caption and flow strip) on/off, A sound on/off, Up/Down more or less chaos,
      Space hold the picture flat, Esc or Q quit.
"""
import argparse
import base64
import collections
import gc
import io
import json
import math
import queue
import random
import re
import struct
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import winsound

import glfw
import numpy as np
from OpenGL import GL
from PIL import Image, ImageDraw, ImageFont

from mindstream import effects, fx
from mindstream.outbox import Outbox
from mindstream import chopper, instruments
from mindstream import solid as solids
from mindstream.parts import STRUCTURAL

EOF = object()
LANES = (("llama", "llama"), ("encoder", "text enc"), ("image", "image gpu"), ("video", "video gpu"))
COLOURS = {"load": (85, 85, 106), "beat": (59, 110, 165), "prompt": (47, 143, 131), "encode": (192, 138, 43),
           "render": (79, 154, 79), "decode": (154, 205, 50), "error": (176, 48, 48), "stop": (68, 68, 68)}

# ----------------------------------------------------------------------------------------- shaders

SURFACE_VS = """
#version 330 core
layout(location = 0) in vec2 uv;
uniform mat4 mvp; uniform mat4 model;
uniform float t, flat_, mixAB, pulse, chaos, aspect;
uniform int shapeA, shapeB;
out vec2 vUV; out vec3 vPos;
const float PI = 3.14159265;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
vec3 plane(vec2 u) { return vec3((u.x - 0.5) * 2.0 * aspect, (0.5 - u.y) * 2.0, 0.0); }
vec3 shape(int s, vec2 u) {
    if (s == 1) { float th = u.x * 2.0 * PI, ph = u.y * PI;
        return 1.15 * vec3(sin(ph) * cos(th), cos(ph), sin(ph) * sin(th)); }
    if (s == 2) { float th = u.x * 2.0 * PI, ph = u.y * 2.0 * PI; float R = 0.85, r = 0.42;
        return vec3((R + r * cos(ph)) * cos(th), r * sin(ph), (R + r * cos(ph)) * sin(th)); }
    vec3 p = plane(u) * 1.1;                                   // twisted ribbon
    p.z += 0.38 * sin(u.x * 6.0 * PI + t * 1.7) * cos(u.y * 4.0 * PI - t * 1.3);
    float a = (u.x - 0.5) * 3.2 * sin(t * 0.4);
    return vec3(p.x, p.y * cos(a) - p.z * sin(a), p.y * sin(a) + p.z * cos(a));
}
void main() {
    vec3 wild = mix(shape(shapeA, uv), shape(shapeB, uv), mixAB);
    float n = noise(uv * 7.0 + t * 0.9) - 0.5;
    wild += normalize(wild + vec3(0.0, 0.0, 0.001)) * n * (0.25 + 0.55 * pulse) * chaos;
    wild *= 1.0 + 0.10 * pulse * chaos;
    vec3 calm = plane(uv);
    calm.z += 0.03 * sin(uv.x * 9.0 + t * 1.5) * sin(uv.y * 7.0 - t);     // never completely still
    vec3 p = mix(wild, calm, flat_);
    vUV = uv; vPos = (model * vec4(p, 1.0)).xyz;
    gl_Position = mvp * vec4(p, 1.0);
}
"""

# The pictures (and each picture's own effects) are as the screen shows them; the frame they are drawn into is light
# (fx.py, "Light and the screen's numbers"). So the surface works its colour as before, on the screen's numbers (the
# shading, the colours pulled apart, the flash all look as they did), and turns it into light as the last thing it does.
SURFACE_FS = """
#version 330 core
in vec2 vUV; in vec3 vPos;
uniform sampler2D texA, texB;
uniform float blend, pulse, chaos, flat_, alpha, flash, split, shade;
out vec4 colour;
""" + fx.SRGB + """
vec3 pick(vec2 u) { return mix(texture(texA, u).rgb, texture(texB, u).rgb, blend); }
void main() {
    vec3 n = normalize(cross(dFdx(vPos), dFdy(vPos)));                    // one normal per facet
    float light = 0.55 + 0.45 * abs(n.z) + 0.25 * pow(abs(n.x), 3.0);
    float sp = (0.004 + 0.02 * pulse) * chaos * split * (1.0 - 0.8 * flat_);
    vec3 c = vec3(pick(vUV + vec2(sp, 0.0)).r, pick(vUV).g, pick(vUV - vec2(sp, 0.0)).b);
    c *= mix(1.0, light, max(0.6 * (1.0 - flat_), shade));               // shade: a side of an object, lit though flat
    c += flash;
    colour = vec4(toLinear(c), alpha);                                    // as light (past white, if the flash takes it there)
}
"""

QUAD_VS = """
#version 330 core
layout(location = 0) in vec2 pos;
out vec2 vUV;
void main() { vUV = pos * 0.5 + 0.5; gl_Position = vec4(pos, 0.0, 1.0); }
"""

# The trails, in light: the last frame (light, in float) faded by the old rate to the power 2.2, so a trail looks to fade
# as fast as it did, and now fades all the way out instead of stopping at a floor; the far tiled picture turned into
# light as it is added.
FEEDBACK_FS = """
#version 330 core
in vec2 vUV;
uniform sampler2D last, picture;
uniform float t, pulse, chaos, flat_, aspect, folds, trails, zoom, flow;
out vec4 colour;
""" + fx.SRGB + """
const float PI = 3.14159265;
float fhash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float fnoise(vec2 p) {
    vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(fhash(i), fhash(i + vec2(1, 0)), f.x), mix(fhash(i + vec2(0, 1)), fhash(i + vec2(1, 1)), f.x), f.y);
}
float field(vec2 p) { return fnoise(p) + 0.5 * fnoise(p * 2.03 + 7.1); }
void main() {
    vec2 p = (vUV - 0.5) * vec2(aspect, 1.0);
    float r = length(p), a = atan(p.y, p.x);
    float n = folds < 0.0 ? 3.0 + floor(mod(t * 0.07, 5.0)) : floor(folds + 0.5);   // kaleidoscope mirrors (auto: 3 to 7)
    if (n >= 1.5) {
        float seg = 2.0 * PI / n;
        float ka = abs(mod(a + t * 0.05, seg) - seg * 0.5);
        a = mix(a, ka, min(0.55 * chaos, 0.95) * (1.0 - flat_));
    }
    a += (0.012 + 0.03 * pulse) * chaos;                                   // swirl
    r *= 1.0 - zoom * 0.04 - 0.02 * pulse * chaos * sign(zoom + 0.001);    // trails burst outward (zoom > 0) or sink inward
    vec2 q = vec2(cos(a), sin(a)) * r / vec2(aspect, 1.0) + 0.5;
    if (flow > 0.004) {                                                    // flow: the trails are carried round the swirls of a slow field, like smoke
        vec2 f = q * 3.0 + vec2(t * 0.05, -t * 0.04);
        vec2 curl = vec2(field(f + vec2(0.0, 0.01)) - field(f - vec2(0.0, 0.01)), field(f - vec2(0.01, 0.0)) - field(f + vec2(0.01, 0.0))) / 0.02;
        q += curl * flow * 0.004 * (1.0 + pulse);
    }
    vec3 c = texture(last, q).rgb;
    c = c.gbr * 0.03 + c * 0.97;                                           // slow colour drift
    c *= pow(mix(mix(0.80, 0.985, trails), 0.80, flat_), 2.2);            // trails fade, faster when calm
    vec3 ghost = texture(picture, fract(q * (1.0 + 2.0 * chaos))).rgb;     // the picture, tiled, far away
    c += toLinear(ghost * 0.035 * (1.0 - flat_) * chaos);
    colour = vec4(c, 1.0);
}
"""

POST_FS = fx.OUTPUT                     # the last passes: exposure, the tone curve, back to the screen's numbers, grain, dither

OVERLAY_FS = """
#version 330 core
in vec2 vUV;
uniform sampler2D tex;
out vec4 colour;
void main() { colour = texture(tex, vec2(vUV.x, 1.0 - vUV.y)); }
"""


def program(vs, fs):
    def compile_(src, kind):
        s = GL.glCreateShader(kind)
        GL.glShaderSource(s, src)
        GL.glCompileShader(s)
        if not GL.glGetShaderiv(s, GL.GL_COMPILE_STATUS):
            raise RuntimeError(GL.glGetShaderInfoLog(s).decode())
        return s
    p = GL.glCreateProgram()
    for s in (compile_(vs, GL.GL_VERTEX_SHADER), compile_(fs, GL.GL_FRAGMENT_SHADER)):
        GL.glAttachShader(p, s)
    GL.glLinkProgram(p)
    if not GL.glGetProgramiv(p, GL.GL_LINK_STATUS):
        raise RuntimeError(GL.glGetProgramInfoLog(p).decode())
    return p


class Uniforms:
    def __init__(self, prog):
        self.prog, self.loc = prog, {}

    def __call__(self, **values):
        for name, v in values.items():
            loc = self.loc.get(name)
            if loc is None:
                loc = self.loc[name] = GL.glGetUniformLocation(self.prog, name)
            if isinstance(v, np.ndarray):
                GL.glUniformMatrix4fv(loc, 1, GL.GL_TRUE, v.astype(np.float32))
            elif isinstance(v, int):
                GL.glUniform1i(loc, v)
            else:
                GL.glUniform1f(loc, float(v))


def perspective(fovy, aspect, near, far):
    f = 1.0 / math.tan(fovy / 2)
    return np.array([[f / aspect, 0, 0, 0], [0, f, 0, 0],
                     [0, 0, (far + near) / (near - far), 2 * far * near / (near - far)], [0, 0, -1, 0]], dtype=np.float32)


def rotation(ax, ay, az):
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    rx = np.array([[1, 0, 0, 0], [0, cx, -sx, 0], [0, sx, cx, 0], [0, 0, 0, 1]], dtype=np.float32)
    ry = np.array([[cy, 0, sy, 0], [0, 1, 0, 0], [-sy, 0, cy, 0], [0, 0, 0, 1]], dtype=np.float32)
    rz = np.array([[cz, -sz, 0, 0], [sz, cz, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32)
    return rz @ ry @ rx


def translate(x, y, z):
    m = np.eye(4, dtype=np.float32)
    m[:3, 3] = (x, y, z)
    return m


def scale(s):
    m = np.eye(4, dtype=np.float32)
    m[0, 0] = m[1, 1] = m[2, 2] = s
    return m


def make_texture(image=None, alpha=False):
    tex = GL.glGenTextures(1)
    TEX_SIZE.pop(tex, None)                                     # a number handed out again: what it held before is gone
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
    for k, v in ((GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR), (GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR),
                 (GL.GL_TEXTURE_WRAP_S, GL.GL_MIRRORED_REPEAT), (GL.GL_TEXTURE_WRAP_T, GL.GL_MIRRORED_REPEAT)):
        GL.glTexParameteri(GL.GL_TEXTURE_2D, k, v)
    upload(tex, image or Image.new("RGBA" if alpha else "RGB", (2, 2)))
    return tex


# What each picture texture holds: (width, height, format). A new picture (or film frame) of the same size is written
# into the storage the texture already has (glTexSubImage2D); only a new size makes the driver find new memory, which
# is what stalls a frame. Only textures made by make_texture are written through put_pixels.
TEX_SIZE = {}


def put_pixels(tex, w, h, data, alpha=False):
    fmt, inner = (GL.GL_RGBA, GL.GL_RGBA8) if alpha else (GL.GL_RGB, GL.GL_RGB8)
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
    if TEX_SIZE.get(tex) == (w, h, inner):
        GL.glTexSubImage2D(GL.GL_TEXTURE_2D, 0, 0, 0, w, h, fmt, GL.GL_UNSIGNED_BYTE, data)
    else:
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, inner, w, h, 0, fmt, GL.GL_UNSIGNED_BYTE, data)
        TEX_SIZE[tex] = (w, h, inner)


def upload(tex, image):
    mode = "RGBA" if image.mode == "RGBA" else "RGB"
    put_pixels(tex, image.width, image.height, image.convert(mode).tobytes() if image.mode != mode else image.tobytes(), alpha=mode == "RGBA")


def keep_screen(pics, small, aspect, caption, reel, reel_at, want, tint_want, shape_want):
    """What is on screen, as something to go back to. Images only, never texture ids: textures are deleted by a new
    theme, images are not. The pictures, the clips and their frames are shared, not copied: nothing changes them."""
    return {"pics": tuple(pics), "small": list(small), "aspect": aspect, "caption": caption, "reel": list(reel),
            "reel_at": reel_at, "want": dict(want), "tint": np.array(tint_want, dtype=float), "shape": shape_want}


def centre_square(w, h):
    """The square in the middle of a w x h window that a memory's small picture is taken from: x, y, side."""
    side = max(min(w, h) // 2, 1)
    return (w - side) // 2, (h - side) // 2, side


def wrapped(text, font, width, most=7):
    """Words broken into lines no wider than `width` in that font; None if they need more than `most` lines."""
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if font.getlength(trial) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines if len(lines) <= most and all(font.getlength(one) <= width for one in lines) else None


def theme_card(text, size=(1024, 1024)):
    """The theme as words on a test card: bars of one colour, rings, and the words large in the middle. It stands in
    as the picture until the first one is painted, and moves as any picture does."""
    w, h = size
    text = " ".join(str(text).split())[:400] or "..."
    seed = sum(ord(c) for c in text)
    hue = ((200, 70, 50), (50, 120, 200), (70, 170, 90), (190, 150, 40), (150, 70, 190))[seed % 5]
    img = Image.new("RGB", size, tuple(c // 5 for c in hue))
    d = ImageDraw.Draw(img)
    for y in range(0, h, 8):
        d.line([(0, y), (w, y)], fill=tuple(int(c * (0.25 + 0.6 * y / h)) for c in hue), width=6)
    for r in range(40, int(min(w, h) * 0.48), 46):
        d.ellipse([w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r], outline=(255, 235, 200), width=5)
    for k in range(12):
        a = k * math.pi / 6 + (seed % 7) * 0.2
        d.line([(w / 2, h / 2), (w / 2 + math.cos(a) * w, h / 2 + math.sin(a) * w)], fill=(20, 20, 30), width=4)
    font, lines = None, None
    for points in (110, 92, 76, 64, 54, 46, 38, 32, 26):               # the largest size the words fit at
        try:
            font = ImageFont.truetype("segoeuib.ttf", points)
        except OSError:
            try:
                font = ImageFont.truetype("arialbd.ttf", points)
            except OSError:
                font = ImageFont.load_default()
        lines = wrapped(text, font, w * 0.8)
        if lines:
            break
    if not lines:                                                      # too long even small: as much as fits
        lines = (wrapped(text[:160], font, w * 0.8, most=99) or [text[:40]])[:7]
    tall = font.getbbox("Ag")[3] * 1.25
    top = h / 2 - tall * len(lines) / 2
    d.rectangle([w * 0.06, top - tall * 0.15, w * 0.94, top + tall * (len(lines) + 0.15)], fill=(12, 12, 18))
    for i, one in enumerate(lines):
        d.text((w / 2, top + tall * (i + 0.5)), one, fill=(255, 255, 255), font=font, anchor="mm")
    return img


def mixed(one, two, share):
    """Two sets of settings, mixed: each number that both have stands `share` of the way from the first to the second."""
    return {key: value + (two[key] - value) * share if isinstance(two.get(key), (int, float)) else value for key, value in one.items()}


PICTURES = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff")
SOUNDS = (".wav", ".flac", ".ogg", ".mp3", ".aif", ".aiff")
FILMS = (".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v")


def link_in(text):
    """The address in what was pasted or dropped: a plain link, or the one inside an embed code. '' if there is none."""
    text = str(text).strip()
    found = re.search(r"""src\s*=\s*["']([^"']+)["']""", text) or re.search(r"""((?:https?:)?//[^\s"'<>]+)""", text)
    if not found:
        return ""
    url = found.group(1)
    return ("https:" + url if url.startswith("//") else url) if re.match(r"(?:https?:)?//", url) else ""


def seconds_in(text):
    """'90', '1:30', '1m30s' -> seconds, for where in a video to start. 0 if it cannot be read."""
    text = str(text).strip().lower()
    clock = re.fullmatch(r"(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)", text)
    if clock:
        return int(clock.group(1) or 0) * 3600 + int(clock.group(2)) * 60 + float(clock.group(3))
    named = re.fullmatch(r"(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+(?:\.\d+)?)s?)?", text)
    if named and any(named.groups()):
        return int(named.group(1) or 0) * 3600 + int(named.group(2) or 0) * 60 + float(named.group(3) or 0)
    return 0.0


def read_link(url, start=0.0, seconds=8.0):
    """A video at a web address (a video site's page, or its embed address) as a film: a few seconds of it from `start`,
    with its sound. The streams are found and read over the network straight into memory; nothing is written, and
    nothing is kept but those seconds. Use it for videos that are yours to use."""
    import shutil
    import yt_dlp
    # picture and sound often come as two streams; a small picture is plenty, as the reel carries it small anyway
    wanted = {"quiet": True, "no_warnings": True, "cachedir": False, "noplaylist": True, "skip_download": True,
              "format": "bv*[height<=480][vcodec^=avc1]+ba/bv*[height<=480]+ba/b[height<=720]/bv*+ba/b"}
    node = shutil.which("node")
    if node and not shutil.which("deno"):                       # some sites need a script runner to give up their streams
        wanted["js_runtimes"] = {"node": {"path": node}}
    with yt_dlp.YoutubeDL(wanted) as fetcher:
        found = fetcher.extract_info(url, download=False)
    if found.get("entries"):                                    # a list of videos: the first
        found = next(iter(found["entries"]))
    streams = found.get("requested_formats") or [found]
    picture = next((one for one in streams if one.get("vcodec") not in (None, "none")), streams[0])
    sound = next((one for one in streams if one.get("acodec") not in (None, "none")), None)

    def asked(stream):                                          # the address, and what the site expects to be sent with it
        headers = stream.get("http_headers") or {}
        return stream["url"], {"headers": "".join(f"{key}: {value}\r\n" for key, value in headers.items())} if headers else {}
    return read_film(asked(picture), str(found.get("title") or "link"), seconds=min(max(float(seconds), 0.5), 8.0), start=max(float(start), 0.0),
                     sound=asked(sound) if sound is not None and sound is not picture else None)


def read_film(path, name, seconds=8.0, side=640, most_fps=24.0, start=0.0, sound=None):
    """A video file (or a stream at an address) as a film: a few seconds of it, from `start`, at a size and a rate the
    reel can carry, with its sound if it has any (from `sound`, when that is kept apart from the picture). `path`
    and `sound` are each a path or address, or (address, options for opening it). Read into memory; nothing is
    written."""
    import av

    def opened(where):
        return av.open(where[0], options=where[1]) if isinstance(where, tuple) else av.open(where)
    frames, pcm = [], b""
    with opened(path) as box:
        stream = box.streams.video[0]
        rate = float(stream.average_rate or 24.0)
        skip = max(int(round(rate / most_fps)), 1)
        if start > 0:
            box.seek(int(start * 1_000_000))                    # to the picture just before it; what comes before `start` is passed over
        kept = 0
        for frame in box.decode(stream):
            when = frame.time if frame.time is not None else start + kept / rate
            if when < start - 0.5 / rate:
                continue
            at, kept = kept, kept + 1
            if when - start > seconds or at / rate > seconds:
                break
            if at % skip == 0:
                image = frame.to_image().convert("RGB")
                image.thumbnail((side, side))
                frames.append((image.width, image.height, image.tobytes()))
    with opened(sound if sound is not None else path) as box:
        if box.streams.audio:
            even = av.AudioResampler(format="s16", layout="stereo", rate=44100)
            if start > 0:
                box.seek(int(start * 1_000_000))
            for frame in box.decode(box.streams.audio[0]):
                if frame.time is not None and frame.time < start - 0.05:
                    continue
                if frame.time is not None and frame.time - start > seconds:
                    break
                for out in even.resample(frame):
                    pcm += out.to_ndarray().tobytes()
            pcm = pcm[:int(seconds * 44100) * 4]
    layer = "".join(c for c in name.lower() if c.isalnum())[:16] or "dropped"
    return {"frames": frames, "fps": rate / skip, "wav": wav_bytes(pcm, 44100, 2) if pcm else None, "pcm": (pcm, 44100, 2) if pcm else None,
            "follows": False, "seq": 0, "tempo": None, "layer": layer}


def dropped(path):
    """A file dropped on the window, read into memory (nothing is copied or written anywhere):
      ("picture", image)   a still picture
      ("film", clip)       a video file (its first eight seconds, with its sound), or a moving picture (an animated GIF or WebP)
      ("sample", frame)    a sound: a "sample" message, as the sample puller would send
      ("no", why)          something this cannot read"""
    import os
    name = os.path.splitext(os.path.basename(path))[0]
    kind = os.path.splitext(path)[1].lower()
    if kind == ".url":                                              # a link saved as a shortcut: the video it points to
        with open(path, encoding="utf-8", errors="ignore") as shortcut:
            url = link_in(next((line[4:] for line in shortcut if line.upper().startswith("URL=")), ""))
        if not url:
            return "no", f'"{name}" is a shortcut with no address in it'
        clip = read_link(url)
        return ("film", clip) if clip["frames"] else ("no", f'nothing to show at the address in "{name}"')
    if kind in FILMS:
        clip = read_film(path, name)
        return ("film", clip) if clip["frames"] else ("no", f'"{name}" has no picture in it')
    if kind in SOUNDS:
        import soundfile as sf
        data, rate = sf.read(path, dtype="float32", always_2d=True, frames=int(20 * 48000))        # the first twenty seconds at most
        if not len(data):
            return "no", f'"{name}" has no sound in it'
        pcm = (np.clip(data[:, :2], -1, 1) * 32767).astype("<i2").tobytes()
        layer = "".join(c for c in name.lower() if c.isalnum())[:16] or "dropped"
        return "sample", {"type": "sample", "role": "loop", "layer": layer, "name": name, "source": "a file you dropped", "licence": "yours",
                          "seconds": round(len(data) / rate, 2),
                          "audio": {"rate": int(rate), "channels": min(data.shape[1], 2), "data": base64.b64encode(pcm).decode("ascii")}}
    if kind not in PICTURES:
        return "no", f'"{name}{kind}" is not a picture or a sound this can read'
    image = Image.open(path)
    count = getattr(image, "n_frames", 1)
    if count > 1:                                                   # it moves: a film without sound
        frames, pause = [], image.info.get("duration", 80) or 80
        for at in range(0, min(count, 240)):
            image.seek(at)
            frame = image.convert("RGB")
            frame.thumbnail((720, 720))
            frames.append((frame.width, frame.height, frame.tobytes()))
        return "film", {"frames": frames, "fps": min(max(1000.0 / pause, 2.0), 60.0), "wav": None, "pcm": None, "follows": False, "seq": 0,
                        "tempo": None, "layer": ""}
    image = image.convert("RGB")
    image.thumbnail((2048, 2048))
    return "picture", image


def wave_card(peaks, name, film=False, size=64):
    """A sound as a small picture: its shape (how loud it is from start to end) and its name."""
    img = Image.new("RGB", (size, size), (18, 34, 26) if not film else (38, 22, 18))
    d = ImageDraw.Draw(img)
    most = max(max(peaks, default=0.0), 1e-6)
    for i, peak in enumerate(peaks[:size - 4]):
        tall = max(int(peak / most * (size * 0.33)), 1)
        d.line([(2 + i, size * 0.4 - tall), (2 + i, size * 0.4 + tall)], fill=(110, 230, 160) if not film else (255, 150, 110))
    d.text((size / 2, size - 9), str(name)[:9], fill=(255, 255, 255), anchor="mm")
    return img


def small_png(image, size=64):
    """A picture as a small square PNG in base64: the middle of it, for a button on a panel."""
    side = min(image.width, image.height)
    left, top = (image.width - side) // 2, (image.height - side) // 2
    out = io.BytesIO()
    image.crop((left, top, left + side, top + side)).convert("RGB").resize((size, size)).save(out, "PNG")
    return base64.b64encode(out.getvalue()).decode("ascii")


def packed(image):
    """A picture packed small, to be kept in memory in numbers (a JPEG, a tenth of its size or less)."""
    out = io.BytesIO()
    image.convert("RGB").save(out, "JPEG", quality=90)
    return out.getvalue()


def unpacked(data):
    return Image.open(io.BytesIO(data)).convert("RGB")


def swarm_copy(image):
    """Aside: the small copy of a picture that flies in the swarm (made off the frame: shrinking a large picture takes
    a dozen milliseconds). It keeps the picture's number on the shelf."""
    small = image.copy()
    small.thumbnail((512, 512))
    return small


def shelf_picture(item):
    """A picture off the shelf: unpacked, or (packing it is done aside, and may not have finished) the picture itself."""
    image, data = item.get("image"), item.get("jpeg")
    if data:
        return unpacked(data)
    if image is not None:
        return image.copy()
    return unpacked(item["jpeg"])                               # packed between the two looks above


def thumb_png(data, side, size=64):
    """A square read back from the screen (raw RGB, bottom row first, as OpenGL hands it over) -> a small PNG in memory."""
    image = Image.frombytes("RGB", (side, side), data).transpose(Image.FLIP_TOP_BOTTOM)
    out = io.BytesIO()
    image.resize((size, size), Image.LANCZOS).save(out, format="PNG")
    return out.getvalue()


def side_frames(frames, fps, most=96, wide=384):
    """A film (or one picture) for the side of an object: its frames as (width, height, bytes), at most `most` of them
    and no wider than `wide`, with the rate that keeps it the same length. `frames`: packed pictures, or (width,
    height, bytes). Several films may be on an object at once, each held unpacked, so they are kept light."""
    skip = max(-(-len(frames) // most), 1)
    out = []
    for frame in frames[::skip]:
        image = unpacked(frame) if isinstance(frame, (bytes, bytearray)) else Image.frombytes("RGB", (frame[0], frame[1]), frame[2])
        if image.width > wide:
            image = image.resize((wide, max(int(round(image.height * wide / image.width)), 1)))
        image = image.convert("RGB")
        out.append((image.width, image.height, image.tobytes()))
    return out, float(fps) / skip


def wav_bytes(pcm, rate, channels):
    """16-bit PCM wrapped as a WAV file in memory."""
    return (b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, channels, rate,
            rate * channels * 2, channels * 2, 16) + b"data" + struct.pack("<I", len(pcm)) + pcm)


def decode_clip(frame):
    """A clip message -> frames as raw RGB (ready to hand to the GPU) and its sound as an in-memory WAV."""
    frames = []
    for data in frame["frames"]:
        img = Image.open(io.BytesIO(base64.b64decode(data))).convert("RGB")
        frames.append((img.width, img.height, img.tobytes()))
    audio = frame.get("audio") or {}
    wav = wav_bytes(base64.b64decode(audio["data"]), int(audio["rate"]), int(audio["channels"])) if audio.get("data") else None
    pcm = (base64.b64decode(audio["data"]), int(audio["rate"]), int(audio["channels"])) if audio.get("data") else None
    return {"frames": frames, "fps": float(frame.get("fps", 24)), "wav": wav, "pcm": pcm, "follows": bool(frame.get("follows")),
            "seq": frame.get("seq", 0), "tempo": frame.get("tempo"), "layer": str(frame.get("layer") or f"film{frame.get('seq', 0)}")}


def reader(frames, texts, statuses, visuals, clips):
    for raw in sys.stdin.buffer:
        try:
            frame = json.loads(raw)
            kind = frame.get("type")
            if kind == "text":
                texts.put(str(frame.get("text", "")))
            elif kind in ("visual", "read", "fresh", "sample", "theme"):
                visuals.put(frame)
            elif kind == "clip":
                clips.put(decode_clip(frame))
            elif kind == "status":
                statuses.put((frame.get("source", "?"), frame.get("kind", "idle"), frame.get("seq", 0),
                              str(frame.get("text", "")), str(frame.get("detail", ""))))
            elif kind == "image":
                image = Image.open(io.BytesIO(base64.b64decode(frame["data"]))).convert("RGB")
                frames.put((image, bool(frame.get("final", True)), frame.get("step", 1), frame.get("steps", 1)))
        except (ValueError, KeyError, OSError):
            continue
    frames.put(EOF)


class Target:
    """A colour (+ optional depth) framebuffer. `fine`: colours kept as fractions that may pass full brightness, for
    the effects, where plain bytes would band and clip."""

    def __init__(self, w, h, depth, fine=False, edge=False):
        self.w, self.h = w, h
        self.key = (w, h, bool(depth), bool(fine), bool(edge))      # what it can stand in for, kept in a Pool
        self.fbo, self.tex = GL.glGenFramebuffers(1), GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex)
        if fine:
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA16F, w, h, 0, GL.GL_RGBA, GL.GL_FLOAT, None)
        else:
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA8, w, h, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, None)
        wrap = GL.GL_CLAMP_TO_EDGE if edge else GL.GL_MIRRORED_REPEAT        # edge: what runs off the side stays at the side (for the simulations)
        for k, v in ((GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR), (GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR),
                     (GL.GL_TEXTURE_WRAP_S, wrap), (GL.GL_TEXTURE_WRAP_T, wrap)):
            GL.glTexParameteri(GL.GL_TEXTURE_2D, k, v)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, self.tex, 0)
        self.rbo = None
        if depth:
            self.rbo = GL.glGenRenderbuffers(1)
            GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, self.rbo)
            GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_DEPTH_COMPONENT24, w, h)
            GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_RENDERBUFFER, self.rbo)
        GL.glClearColor(0, 0, 0, 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    def clear(self):
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo)
        GL.glClearColor(0, 0, 0, 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    def free(self):
        GL.glDeleteFramebuffers(1, [self.fbo])
        GL.glDeleteTextures([self.tex])
        if self.rbo:
            GL.glDeleteRenderbuffers(1, [self.rbo])


class Ring:
    """The last `count` frames, kept as the layers of one texture and written round and round: `head` is the layer
    written next, so the newest frame is the one before it. (For the slit scan, which shows different moments in
    different places.)"""

    def __init__(self, w, h, count):
        self.w, self.h, self.count, self.head = w, h, count, 0
        self.key = ("ring", w, h, count)
        self.fbo, self.tex = GL.glGenFramebuffers(1), GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D_ARRAY, self.tex)
        # light, in float (three small floats in four bytes: as small as the bytes it used to be, and it does not band)
        GL.glTexImage3D(GL.GL_TEXTURE_2D_ARRAY, 0, GL.GL_R11F_G11F_B10F, w, h, count, 0, GL.GL_RGB, GL.GL_FLOAT, None)
        for k, v in ((GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR), (GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR),
                     (GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE), (GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)):
            GL.glTexParameteri(GL.GL_TEXTURE_2D_ARRAY, k, v)

    def aim(self):
        """What is drawn next goes into the layer at the head."""
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo)
        GL.glFramebufferTextureLayer(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, self.tex, 0, self.head)

    def clear(self):
        """Every layer black, and the head back at the start (it is being used again, from the Pool)."""
        GL.glClearColor(0, 0, 0, 1)
        for layer in range(self.count):
            self.head = layer
            self.aim()
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        self.head = 0

    def free(self):
        GL.glDeleteFramebuffers(1, [self.fbo])
        GL.glDeleteTextures([self.tex])


class State:
    """The particles' state: three float textures of one size (where, moving, home: see fx.py), written together by one
    pass through three colour attachments. Two of these are used by turns."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.key = ("state", w, h)
        self.fbo, self.texs = GL.glGenFramebuffers(1), []
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo)
        # where in 32-bit floats (a place added to for minutes must not lose small steps); moving and home in 16-bit
        attach = (GL.GL_COLOR_ATTACHMENT0, GL.GL_COLOR_ATTACHMENT1, GL.GL_COLOR_ATTACHMENT2)
        for at, inner in enumerate((GL.GL_RGBA32F, GL.GL_RGBA16F, GL.GL_RGBA16F)):
            tex = GL.glGenTextures(1)
            GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, inner, w, h, 0, GL.GL_RGBA, GL.GL_FLOAT, None)
            for k, v in ((GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST), (GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST),
                         (GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE), (GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)):
                GL.glTexParameteri(GL.GL_TEXTURE_2D, k, v)
            GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, attach[at], GL.GL_TEXTURE_2D, tex, 0)
            self.texs.append(tex)
        GL.glDrawBuffers(len(attach), list(attach))            # all three written by one pass (kept with the framebuffer)
        self.clear()
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    def clear(self):
        """Every point unborn (age 0 of a life of 0): the first pass that runs over it gives it a place."""
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo)
        GL.glClearColor(0, 0, 0, 0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    def free(self):
        GL.glDeleteFramebuffers(1, [self.fbo])
        GL.glDeleteTextures(self.texs)


class Pool:
    """Framebuffers kept for use again. Making one asks the driver for memory, and on some frames that stalls the
    picture for tens of milliseconds; the effects come and go with every beat. So what an effect (or a picture's own
    chain) lets go of is kept here, cleared, and handed out again to the next that wants one of the same size and kind.
    What has not been wanted for `stale` seconds is let go, one a frame (trim), so a size no longer drawn does not
    stay on the card for ever. `made` counts how many were really made (the hitch recorder reports it)."""

    def __init__(self, stale=300.0):
        self.spare, self.stale, self.made = {}, stale, 0

    def take(self, w, h, fine=True, edge=False):
        key = (w, h, False, bool(fine), bool(edge))
        if self.spare.get(key):
            target = self.spare[key].pop()[1]
            target.clear()
            return target
        self.made += 1
        return Target(w, h, False, fine=fine, edge=edge)

    def pair(self, w, h, edge=True):
        return [self.take(w, h, True, edge), self.take(w, h, True, edge)]

    def ring(self, w, h, count):
        key = ("ring", w, h, count)
        if self.spare.get(key):
            ring = self.spare[key].pop()[1]
            ring.clear()
            return ring
        self.made += 1
        return Ring(w, h, count)

    def state(self, w, h):
        key = ("state", w, h)
        if self.spare.get(key):
            state = self.spare[key].pop()[1]
            state.clear()
            return state
        self.made += 1
        return State(w, h)

    def give(self, thing, now=None):
        if hasattr(thing, "key"):
            self.spare.setdefault(thing.key, []).append((time.time() if now is None else now, thing))

    def trim(self, now):
        """At most one let go per call: a frame is never spent deleting a heap of them."""
        for key, kept in self.spare.items():
            if kept and now - kept[0][0] > self.stale:
                kept.pop(0)[1].free()
                return True
        return False

    def drop_all(self):
        for kept in self.spare.values():
            for _, thing in kept:
                thing.free()
        self.spare = {}

    def __len__(self):
        return sum(len(kept) for kept in self.spare.values())


class Bench:
    """The scratch framebuffers one chain of effects is worked on: two to draw into by turns, the steps of the bloom,
    the smears of the streak, two at half size for the effects that walk a ray for every point (fractal, gyroid), and
    the relief's height. One for the screen (at the size things are drawn, made with the screen, not when an effect is
    first turned up), and one for each size the pictures are worked at."""

    def __init__(self, pool, rw, rh, w, h):
        self.w, self.h = rw, rh
        self.pair = [pool.take(rw, rh), pool.take(rw, rh)]
        self.mips = [pool.take(max(w >> (i + 1), 2), max(h >> (i + 1), 2)) for i in range(6)]
        self.smears = [pool.take(max(w // 4, 2), max(h // 4, 2)) for _ in range(2)]
        self.halves = [pool.take(max(w // 2, 2), max(h // 2, 2)) for _ in range(2)]
        self.height = pool.take(max(w // 2, 16), max(h // 2, 16), True, True)

    def all(self):
        return self.pair + self.mips + self.smears + self.halves + [self.height]

    def give_back(self, pool):
        for target in self.all():
            pool.give(target)


class Hitches:
    """A cheap record of frames that took too long, and what happened in them. Each frame things that can stall it
    note themselves (a picture sent to the card, a framebuffer made, an effect switched on, the screen read back, the
    garbage collector...); a frame much slower than usual (over `least` seconds and over twice the usual) is kept with
    its notes, the worst few at a time, and every `every` seconds a line about them is ready (report). Nothing is said
    about a quiet stretch, and nothing is printed per frame."""

    def __init__(self, least=0.045, every=60.0, keep=4):
        self.least, self.every, self.keep = least, every, keep
        self.usual, self.notes, self.worst, self.count, self.frames, self.since = 1.0 / 60.0, [], [], 0, 0, time.time()

    def note(self, what, seconds=None):
        self.notes.append(what if seconds is None else f"{what} {seconds * 1000:.0f} ms")

    def frame(self, took, cpu=None):
        """One frame done, `took` seconds from the start of the last (the whole loop, the wait for the screen
        included); `cpu`: how long its own work took. Returns True if it was a hitch."""
        notes, self.notes = self.notes, []
        self.frames += 1
        hitch = took > self.least and took > 2.0 * self.usual
        if hitch:
            self.count += 1
            self.worst = sorted(self.worst + [(took, cpu, notes)], key=lambda one: -one[0])[:self.keep]
        else:
            self.usual += (took - self.usual) * 0.05
        return hitch

    def report(self, now):
        """A line about the slow frames since the last report (None if there were none, or it is not yet time)."""
        if now - self.since < self.every:
            return None
        count, worst, frames, span = self.count, self.worst, self.frames, now - self.since
        self.count, self.worst, self.frames, self.since = 0, [], 0, now
        if not count:
            return None
        parts = []
        for took, cpu, notes in worst:
            said = ", ".join(notes) or "nothing noted on this side: the graphics card itself (a heavy effect), or the system"
            parts.append(f"{took * 1000:.0f} ms" + (f" (its own work {cpu * 1000:.0f} ms)" if cpu is not None else "") + f": {said}")
        return (f"Hitches: {count} of {frames} frames in the last {span:.0f} s took over {max(self.least, 2.0 * self.usual) * 1000:.0f} ms "
                f"(usually {self.usual * 1000:.0f}). The worst: " + "; ".join(parts) + ".")


def glyph_atlas(characters, cell=(24, 40)):
    """The characters side by side, white on black, each in a cell of its own: what the glyph effect draws from."""
    image = Image.new("RGB", (cell[0] * len(characters), cell[1]), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("consolab.ttf", 32)
    except OSError:
        try:
            font = ImageFont.truetype("consola.ttf", 32)
        except OSError:
            font = ImageFont.load_default()
    for at, character in enumerate(characters):
        draw.text((at * cell[0] + cell[0] / 2, cell[1] / 2), character, font=font, fill=(255, 255, 255), anchor="mm")
    return image


class View:
    def __init__(self, args):
        self.args = args
        self.frames, self.texts, self.statuses, self.visuals = queue.Queue(), queue.Queue(), queue.Queue(), queue.Queue()
        # how the picture moves: `want` is where the story (or a typed !setting) says to be, `look` glides towards it
        self.want = {"chaos": args.chaos, "bpm": args.bpm, "calm": args.calm, "wild": args.wild, "folds": -1.0,
                     "trails": 0.75, "swarm": 0.8, "split": 1.0, "spin": 1.0, "zoom": 0.7}
        self.want.update(effects.STARTS)                    # the effects (effects.py): each one number, all at nothing to begin with
        self.want.update({key: 0.0 for key in effects.IMAGE_RANGES})        # ... and on each picture by itself ("image:bloom")
        self.look = dict(self.want)
        self.RANGES = {**View.RANGES, **effects.RANGES, **effects.IMAGE_RANGES}
        self.tint, self.tint_want, self.shape_want, self.beat = np.ones(3), np.ones(3), 0, 0.0
        # video: a reel of clips played in order and looped; only the segment playing is heard
        self.clips, self.reel, self.reel_at, self.segment_start, self.shown_frame = queue.Queue(), [], 0, 0.0, None
        self.premiere_until, self.still_until, self.mute = 0.0, 0.0, args.mute
        # one clock for everything, counted in beats: the pulse, and scene changes on bar lines
        self.cycle_beat0, self.bpm_now, self.bpm_locked = 0.0, args.bpm, False
        self.notes = []          # what was understood and why things are changing: (when, stream, sentence)
        self.snap_until, self.kick_cycle = 0.0, False       # a typed change is taken up fast, and shown in motion
        # --groove: a synthesised rhythm section plays from the start and the video's sound is played over it
        # as a clip; the sound card then becomes the clock for the pulse
        self.mixer = None
        if args.groove:
            try:
                from mindstream.mixer import Mixer
                self.mixer = Mixer(bpm=args.bpm, energy=min(args.chaos / 2.0, 1.0), compose=args.thelmic,
                                   log=self.tell)
                self.mixer.mute = args.mute
            except Exception as e:
                self.tell(f"no rhythm section ({type(e).__name__}: {e}); video sound plays on its own")
        self.lanes = {key: {"segments": [], "text": "", "detail": "", "since": time.time(), "kind": "idle"}
                      for key, _ in LANES}
        self.caption, self.overlay_on, self.overlay_due = "", not args.no_overlay, 0.0
        self.chaos, self.hold_flat, self.ended = args.chaos, False, False   # chaos follows self.look each frame
        self.count, self.rendered = 0, 0

        if not glfw.init():
            sys.exit("[gl-view] cannot start OpenGL")
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.AUTO_ICONIFY, glfw.FALSE)       # full screen stays up when you click another screen
        self.windowed = (args.width, args.height)
        self.win = glfw.create_window(self.windowed[0], self.windowed[1], "mindstream", None, None)
        glfw.make_context_current(self.win)
        self.full, self.screen = False, None
        if args.fullscreen:
            self.set_full(True)
        glfw.swap_interval(1)
        glfw.set_key_callback(self.win, self.on_key)
        glfw.set_char_callback(self.win, self.on_char)
        glfw.set_drop_callback(self.win, self.on_drop)
        self.typing = ""                                    # a steer being typed in this window

        self.surface, self.feedback = program(SURFACE_VS, SURFACE_FS), program(QUAD_VS, FEEDBACK_FS)
        self.post, self.overlay = program(QUAD_VS, POST_FS), program(QUAD_VS, OVERLAY_FS)
        self.u_surface, self.u_feedback = Uniforms(self.surface), Uniforms(self.feedback)
        self.u_post, self.u_overlay = Uniforms(self.post), Uniforms(self.overlay)
        # the effects' own programs (mindstream/fx.py). One that this card will not take is left out, and said; and if
        # anything goes wrong while they run, they are all switched off for the session rather than stop the picture
        self.fx, self.fx_at, self.fx_broken = {}, 0, False
        # pool: framebuffers kept for use again (made once, handed round: see Pool). bench: the scratch framebuffers the
        # chain being run is worked on; screen_bench the screen's (made with the screen), benches the pictures' by size
        self.pool, self.bench, self.screen_bench, self.benches = Pool(), None, None, {}
        self.hitches, self.loop_at = Hitches(), None             # the slow frames, and what happened in them
        # each picture's own effects (the "image" target): what each picture looks like with them, by the texture it
        # comes from (imgfx), and this frame's stand-ins for the textures drawn (shown_as)
        self.imgfx, self.shown_as, self.image_plan = {}, {}, []
        # shedding when frames run slow: 0 nothing shed, 1 the pictures' heavy effects shed, 2 the screen's too. It is
        # held for a while once it has risen (longer each time it flaps), so heavy effects do not blink on and off
        self.shed = {"level": 0, "until": 0.0, "hold": 4.0, "fell": -1e9}
        self.fx_slow, self.fx_shedding, self.fx_was = 0.0, False, []
        # work that must not hold up a frame, done aside: packing pictures for the shelf; drawing the overlay
        self.packer, self.drawer, self.overlay_job, self.outbox_lock = ThreadPoolExecutor(1), ThreadPoolExecutor(1), None, threading.Lock()
        refused = []
        for name, source in fx.ALL.items():
            try:
                made = program(fx.VERTEX.get(name, QUAD_VS), source)
                self.fx[name] = (made, Uniforms(made))
            except Exception as e:
                refused.append(name)
                self.trace(f"effect {name}: {e}")
        if refused:                                         # said by the effects lost (the particles' step is not an effect's name)
            lost = [key for key in effects.KEYS if any(name in refused for name in fx.needs(key))]
            lost += [name.split(":")[-1] for name in refused if not any(name in fx.needs(key) for key in effects.KEYS)]
            self.tell("These effects are not available on this graphics card: " + ", ".join(lost) + ".")
        self.points_vao = GL.glGenVertexArrays(1)           # the particles need nothing sent: each reads its own place
        # the particles' state (two sets, used by turns: made with the screen, kept for the session, as it does not
        # depend on the screen's size), which set is the newest, how many rows of points were moved last frame (0: none,
        # so all are born afresh when they come back) and the beat they last kicked on
        self.particles, self.pt_at, self.pt_rows, self.pt_beat = None, 0, 0, -1
        self.lin = 0.0                                      # whether the passes now running read light (fx.py): only the screen's, up to the curve
        self.lin_at = {}                                    # ... and what each program was last told of it
        # what the effects that remember are holding, by effect: made when one is first turned up, let go a few seconds
        # after it is turned back to nothing. fx_bar: the bar the effects last ran in (some renew themselves on the bar)
        self.fx_state, self.fx_bar = {}, -1
        self.glyph_tex = make_texture(glyph_atlas(fx.fx2.GLYPHS))

        n = args.facets                                            # coarse grid = visible facets
        u, v = np.meshgrid(np.linspace(0, 1, n + 1), np.linspace(0, 1, n + 1))
        grid = np.stack([u.ravel(), v.ravel()], 1).astype(np.float32)
        idx = []
        for j in range(n):
            for i in range(n):
                a = j * (n + 1) + i
                idx += [a, a + 1, a + n + 1, a + 1, a + n + 2, a + n + 1]
        self.grid_count = len(idx)
        self.grid_vao = self.vertex_array(grid, np.array(idx, dtype=np.uint32))
        self.quad_vao = self.vertex_array(np.array([[-1, -1], [1, -1], [-1, 1], [1, 1]], dtype=np.float32),
                                          np.array([0, 1, 2, 2, 1, 3], dtype=np.uint32))
        self.warm_up()

        self.tex_a, self.tex_b = make_texture(), make_texture()    # surface: from picture A towards picture B
        self.blend, self.blend_target = 1.0, 1.0
        self.aspect = 1.0
        self.history = []                                          # textures of earlier finished pictures
        # the same pictures as images, on this side of the GPU, so that "memorise" has something to hold: the last two
        # FINISHED pictures (step previews pass through the textures but not through here) and the small ones of the
        # swarm, kept in step with self.history
        self.pic_a, self.pic_b, self.history_pics = None, None, []
        self.swarm_due = collections.deque()                       # small copies for the swarm, being made aside (swarm_copy)
        self.kept, self.grab_for = {}, []        # memorised screens by number; numbers waiting for their small picture
        # the shelf: every picture and film shown this session, by number, packed small and in memory only, so that any
        # of them can be put back on screen. held_look: settings turned by hand on the visuals panel, which the story's
        # director leaves alone until they are released
        self.shelf, self.shelf_next = {}, 1
        # boss: what was last set by hand (on a panel, or typed), and until when the session leaves it alone. The session
        # moves everything as the story goes; a setting touched by hand is the boss for a moment (eight bars), then the
        # session may move it again. told/told_at: how things stand, as last told to the panels, which follow the session
        # Who has the say. The story's director moves the look and the score as the story goes. A setting turned by hand
        # is not put back by it: from then on the director's moves are added to where the hand left the setting (offset:
        # how far the hand put it from where the director had it; session: where the director last had it), so the
        # session can move away from a knob but never snaps it back. What cannot be moved by degrees (the style, the key,
        # the shape, the tint, the patterns once changed by hand) stays as the hand chose it (hand) until it is released.
        self.offset, self.session, self.hand, self.told, self.told_at = {}, {}, set(), None, 0.0
        self.fading = None                       # the crossfader: (the two memories its pictures are loaded from, whose side it is on)
        # an object with sides in place of the one surface (mindstream/solid.py): which, what is on each side, and for
        # each thing on a side its picture or its film's frames, got ready aside and put on the GPU when first drawn
        self.solid, self.solid_turn, self.side_pics = None, 0.0, {}
        # the session's hand on the super knob: where it has asked the knob to be (None: it has not), the bar the knob
        # last moved on, the change of structure last seen, and whether the scene has just changed (then it jumps)
        self.super_goal, self.super_bar, self.super_change, self.super_jump = None, -1, None, False
        self.overlay_tex = make_texture(alpha=True)
        self.roll_tex, self.roll_due, self.roll_size, self.panel_floor = make_texture(alpha=True), 0.0, (0, 0), 0
        self.size = (0, 0)
        self.targets = None

        self.t0 = time.time()
        self.flat, self.flash = 1.0, 0.0
        self.cycle_start = self.t0                                  # each cycle: calm (flat) then wild
        self.shape_a, self.shape_b = 1, 2
        self.spin = np.zeros(3)
        self.swarm = [(random.uniform(1.7, 2.9), random.uniform(0, 6.28), random.uniform(0.25, 0.9) * random.choice((-1, 1)),
                       random.uniform(-1.0, 1.0), random.uniform(0.22, 0.5), random.uniform(0, 6.28)) for _ in range(args.shards)]
        try:
            self.font = ImageFont.truetype("segoeui.ttf", args.text_size)
            self.mono = ImageFont.truetype("consola.ttf", 13)
            self.tiny = ImageFont.truetype("consola.ttf", 10)
        except OSError:
            self.font = self.mono = self.tiny = ImageFont.load_default()
        self.tex_video = make_texture()
        threading.Thread(target=reader, args=(self.frames, self.texts, self.statuses, self.visuals, self.clips), daemon=True).start()
        self.quiet_collector()

    def quiet_collector(self):
        """Python's garbage collector, kept from stopping a frame: everything made while starting (fonts, programs,
        tables) is put out of its sight for good (gc.freeze), and it is asked to look less often. Each collection that
        does happen is timed and noted for the hitch recorder."""
        gc.collect()
        gc.freeze()
        gc.set_threshold(20000, 20, 20)
        began = {}

        def timed(phase, info):
            if phase == "start":
                began["at"] = time.perf_counter()
            elif "at" in began:
                took = time.perf_counter() - began.pop("at")
                if took > 0.002:
                    self.hitches.note(f"garbage collection (generation {info.get('generation')})", took)
        gc.callbacks.append(timed)

    def warm_up(self):
        """Every effect's program drawn once, small, as the viewer starts. Drivers finish building a program the first
        time it draws, not when it is compiled: left to then, the first beat that turns an effect up stalls the picture
        while it is built. Anything that goes wrong here is let go (the effect is tried again when it is used)."""
        began = time.perf_counter()
        try:                                                    # the picture file formats too: the first JPEG or PNG made in a
            Image.init()                                        # session otherwise imports them all then, holding everything up
            packed(Image.new("RGB", (8, 8)))
            small_png(Image.new("RGB", (8, 8)))
        except Exception:
            pass
        try:
            target = Target(16, 16, False, fine=True)
            GL.glBindVertexArray(self.quad_vao)
            GL.glDisable(GL.GL_DEPTH_TEST)
            GL.glDisable(GL.GL_BLEND)
            for name, (made, _) in self.fx.items():
                GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, target.fbo)
                GL.glViewport(0, 0, 16, 16)
                GL.glUseProgram(made)
                if name in fx.VERTEX:                           # the particles' points: one, drawn as they are
                    GL.glBindVertexArray(self.points_vao)
                    GL.glDrawArrays(GL.GL_POINTS, 0, 1)
                    GL.glBindVertexArray(self.quad_vao)
                else:
                    GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)
            GL.glUseProgram(self.post)                          # and the last pass, both ways
            GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
            GL.glFinish()                                       # once, at start: the building is done now, not later
            target.free()
        except Exception as e:
            self.trace(f"warm up: {e}")
        self.trace(f"effects warmed up in {(time.perf_counter() - began) * 1000:.0f} ms")

    def trace(self, msg):
        if self.args.trace:
            print(f"[gl-view] {msg}", file=sys.stderr, flush=True)

    @staticmethod
    def vertex_array(vertices, indices):
        vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, GL.glGenBuffers(1))
        GL.glBufferData(GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, False, 0, None)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, GL.glGenBuffers(1))
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL.GL_STATIC_DRAW)
        GL.glBindVertexArray(0)
        return vao

    def tell(self, msg):
        """Something the viewer itself has to say (about the sound, mostly): shown in its own side panel, and on
        the terminal only if that has not been hushed."""
        self.notes = (getattr(self, "notes", []) + [(time.time(), "sound", str(msg))])[-8:]
        self.overlay_due = 0.0
        if not self.args.hush:
            print(f"[gl-view] {msg}", file=sys.stderr, flush=True)

    def on_drop(self, win, paths):
        """Files dragged onto the window from outside: a picture is shown as a new picture is, a moving picture plays
        as a film, a sound becomes a layer (waiting, like any sample). Each also goes on the palette. They are read
        aside, so a large one does not hold the picture up; nothing is copied or written."""
        def take():
            for path in list(paths)[:12]:
                try:
                    kind, thing = dropped(path)
                except Exception as e:
                    kind, thing = "no", f"that file could not be read ({type(e).__name__})"
                if kind == "picture":
                    self.frames.put((thing, True, 1, 1))
                elif kind == "film":
                    self.clips.put(thing)
                elif kind == "sample":
                    self.visuals.put(thing)
                else:
                    self.tell(thing[0].upper() + thing[1:] + ".")
        threading.Thread(target=take, daemon=True).start()

    def on_link(self, wanted):
        """A video at a web address (pasted or dropped on the visuals panel, as a link or an embed code): a few seconds
        of it are fetched aside and play as a film, whose sound becomes a layer; it goes on the palette too."""
        url = link_in(wanted.get("url", ""))
        if not url:
            self.tell("There is no web address in that.")
            return
        start = wanted.get("start", 0.0) if isinstance(wanted.get("start"), (int, float)) else seconds_in(wanted.get("start", ""))
        seconds = wanted.get("seconds", 4.0) if isinstance(wanted.get("seconds"), (int, float)) else 4.0
        self.tell(f"Fetching {seconds:g} seconds from {start:g} s of the video at that address...")

        def take():
            try:
                clip = read_link(url, start, seconds)
                if clip["frames"]:
                    self.clips.put(clip)
                else:
                    self.tell("There was no picture to show at that address.")
            except Exception as e:
                self.tell(f"The video at that address could not be fetched ({type(e).__name__}).")
        threading.Thread(target=take, daemon=True).start()

    def on_char(self, win, codepoint):
        """Typing in the viewer writes a steer (when a launcher is listening): Enter sends it to the story."""
        if self.args.report_watching and (self.typing or chr(codepoint) != " ") and len(self.typing) < 400:
            self.typing += chr(codepoint)
            self.overlay_due = 0.0

    def on_key(self, win, key, scancode, action, mods):
        if action not in (glfw.PRESS, glfw.REPEAT):
            return
        if self.args.report_watching and not mods & glfw.MOD_CONTROL:
            # plain keys belong to the steer being typed; the viewer's own commands are Ctrl+key
            if key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER) and self.typing.strip():
                try:
                    sys.stdout.write(json.dumps({"steer": self.typing.strip()}) + "\n")
                    sys.stdout.flush()
                except (OSError, ValueError):
                    pass
                self.typing = ""
            elif key == glfw.KEY_BACKSPACE:
                self.typing = self.typing[:-1]
            elif key == glfw.KEY_ESCAPE:
                if self.typing:
                    self.typing = ""
                else:
                    glfw.set_window_should_close(win, True)
            elif key == glfw.KEY_UP:
                self.want["chaos"] = min(self.want["chaos"] + 0.15, 2.0)
            elif key == glfw.KEY_DOWN:
                self.want["chaos"] = max(self.want["chaos"] - 0.15, 0.0)
            self.overlay_due = 0.0
            return
        if action != glfw.PRESS:
            return
        self.overlay_due = 0.0
        if key in (glfw.KEY_ESCAPE, glfw.KEY_Q):
            glfw.set_window_should_close(win, True)
        elif key == glfw.KEY_M:
            self.overlay_on = not self.overlay_on
        elif key == glfw.KEY_SPACE:
            self.hold_flat = not self.hold_flat
        elif key == glfw.KEY_A:
            self.mute = not self.mute
            if self.mixer:
                self.mixer.mute = self.mute
            if self.mute:
                winsound.PlaySound(None, winsound.SND_PURGE)
        elif key == glfw.KEY_R and self.reel:                   # the last film again, from its start, held flat
            now = time.time()
            if self.mixer:
                self.mixer.replay()
            else:
                self.start_segment(len(self.reel) - 1, now)
                self.premiere_until = now + len(self.reel[-1]["frames"]) / self.reel[-1]["fps"]
            self.still_until = 0.0
        elif key == glfw.KEY_K:                                 # the knob panel, opened or closed
            self.toggle_panel("knobs")
        elif key == glfw.KEY_V:                                 # the visuals panel, opened or closed
            self.toggle_panel("visuals")
        elif key == glfw.KEY_G and self.mixer:                  # the rhythm section on / off
            self.mixer.groove_on = not self.mixer.groove_on
        elif key == glfw.KEY_C and self.mixer:                  # the newest film's sound in, or out again
            said = self.mixer.toggle_film()
            if said:
                self.tell(said[0].upper() + said[1:] + ".")
        elif key == glfw.KEY_UP:
            self.want["chaos"] = min(self.want["chaos"] + 0.15, 2.0)
        elif key == glfw.KEY_DOWN:
            self.want["chaos"] = max(self.want["chaos"] - 0.15, 0.0)
        elif key == glfw.KEY_F:
            self.set_full(not self.full)
            self.told_at = 0.0                                  # the panels dock, or undock, at once

    # ------------------------------------------------------------------ video reel

    def start_segment(self, index, now):
        self.reel_at, self.segment_start, self.shown_frame = index, now, None
        wav = self.reel[index]["wav"]
        if self.mixer:
            if self.reel[index]["pcm"]:
                # shown once on the next bar line; a film taken off the shelf keeps the layer its sound already has
                said = self.mixer.play(*self.reel[index]["pcm"], name=self.reel[index].get("layer"), again=bool(self.reel[index].get("shelved")))
                if said:
                    self.tell(said[0].upper() + said[1:] + " (or Ctrl+C).")
            return
        if wav and not self.mute:      # a new PlaySound cuts off the previous one: one segment is heard at a time
            threading.Thread(target=winsound.PlaySound, args=(wav, winsound.SND_MEMORY | winsound.SND_NODEFAULT), daemon=True).start()

    def play_reel(self, now):
        """Advance the reel and put the current video frame on the GPU. Returns the frame's aspect ratio."""
        clip = self.reel[self.reel_at]
        elapsed = now - self.segment_start
        if self.mixer:                                          # the frame that belongs to the sound being heard
            elapsed = (self.mixer.clip_seconds() or 0.0) if self.mixer.pending is None else 0.0
        elif elapsed >= len(clip["frames"]) / clip["fps"]:
            self.start_segment((self.reel_at + 1) % len(self.reel), now)
            clip, elapsed = self.reel[self.reel_at], 0.0
        index = min(int(elapsed * clip["fps"]), len(clip["frames"]) - 1)
        w, h, data = clip["frames"][index]
        if self.shown_frame != (self.reel_at, index):
            put_pixels(self.tex_video, w, h, data)              # into the texture's own storage while the size holds
            self.shown_frame = (self.reel_at, index)
        return w / h

    # ------------------------------------------------------------------ incoming stream

    def take_input(self, now):
        # Pictures go to the card one finished picture a frame at most (each is a large upload, and two or three
        # arriving together made one long frame); a preview that a later picture already replaces is not sent at all.
        # What is not taken this frame waits, in order, for the next.
        waiting = self.waiting = getattr(self, "waiting", collections.deque())
        while True:
            try:
                waiting.append(self.frames.get_nowait())
            except queue.Empty:
                break
        took_final = False
        while self.swarm_due and self.swarm_due[0].done():     # small copies made aside: into the swarm
            try:
                small = self.swarm_due.popleft().result()
            except Exception:
                continue
            self.history.append(make_texture(small))
            self.history_pics.append(small)
            if len(self.history) > 12:
                GL.glDeleteTextures([self.history.pop(0)])
                self.history_pics.pop(0)
        while waiting:
            item = waiting[0]
            if item is not EOF:
                if not item[1] and any(later is not EOF for later in list(waiting)[1:]):
                    waiting.popleft()                           # a preview already overtaken
                    continue
                if item[1] and took_final:
                    break
            waiting.popleft()
            if item is EOF:
                self.ended = True
                self.trace(f"stream ended after {self.count} finished image(s)")
                for lane in self.lanes.values():
                    if lane["segments"] and lane["segments"][-1][1] is None:
                        lane["segments"][-1][1] = now
                    if lane["kind"] not in ("error", "stop"):
                        lane.update(kind="stop", text="ended", detail="")
                if self.args.exit_on_eof:
                    self.close_at = now + self.args.linger
                continue
            image, final, step, steps = item
            began = time.perf_counter()
            if final:
                took_final = True
                if not image.info.get("shelved"):                  # new to the session: onto the shelf (packed aside, see shelve)
                    self.shelve("picture", {"jpeg": None, "image": image}, image)
                if self.mixer:                                     # the first picture sets the scene: the heartbeat gives way to the music
                    self.mixer.groove.scene_set = True
                self.count += 1
                self.aspect = image.width / image.height
                if not image.info.get("card"):                     # a card of words is not one of the story's pictures: it stays out of the swarm
                    self.swarm_due.append(self.packer.submit(swarm_copy, image))      # joins the swarm when its small copy is made, aside
                self.tex_a, self.tex_b = self.tex_b, self.tex_a     # what was shown becomes "from"
                upload(self.tex_b, image)
                self.pic_a, self.pic_b = self.pic_b, image          # the last two finished pictures, for "memorise"
                self.fading = None                                  # a new picture: the crossfader's two are no longer what is loaded
                GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex_b)
                self.blend, self.blend_target = 0.0, 1.0
                self.cycle_start, self.cycle_beat0, self.flash = now, self.beat, 0.6   # arrive flat, with a flash
                self.forming = False
                self.still_until = now + self.look["calm"]          # a new picture is seen before the reel resumes
                self.trace(f"finished image {self.count}: shown flat, then swept into motion")
                self.hitches.note(f"a new picture sent to the card ({image.width}x{image.height})", time.perf_counter() - began)
            else:                                                   # a step preview: the next picture forming
                if not getattr(self, "forming", False):
                    self.tex_a, self.tex_b = self.tex_b, self.tex_a
                    self.forming = True
                    self.blend = 0.0
                upload(self.tex_b, image)
                self.blend_target = min((step / max(steps, 1)) ** 1.5, 0.8)
                self.hitches.note("a preview sent to the card", time.perf_counter() - began)
        try:
            self.caption = self.texts.get_nowait()
            self.overlay_due = 0.0
        except queue.Empty:
            pass
        try:
            clip = self.clips.get_nowait()
            if clip["frames"]:
                if not clip.get("shelved"):                        # new to the session: onto the shelf
                    self.shelve_film(clip)
                # a segment that follows on from the last one joins the reel; anything else starts a new reel
                self.reel = (self.reel + [clip])[-8:] if clip["follows"] and self.reel and not self.mixer else [clip]
                self.start_segment(len(self.reel) - 1, now)
                self.premiere_until = now + len(clip["frames"]) / clip["fps"]     # first showing: held flat, watchable
                self.still_until = 0.0
                self.cycle_start, self.cycle_beat0, self.flash = now, self.beat, 0.4
                self.trace(f"clip for beat {clip['seq']}: {len(clip['frames'])} frames, reel of {len(self.reel)} segment(s), "
                           + (f"soundtrack tempo {clip['tempo']['bpm']:.1f} bpm, first beat at {clip['tempo']['offset']:.2f}s" if clip["tempo"] else "no tempo measured"))
        except queue.Empty:
            pass
        while True:
            try:
                v = self.visuals.get_nowait()
            except queue.Empty:
                break
            if v.get("type") == "theme":                        # the theme, as words on a card: the picture until one is painted
                self.show_card(str(v.get("text", "")), now)
                continue
            if v.get("type") == "sample":                       # a sample pulled from the library or an archive
                audio = v.get("audio") or {}
                if self.mixer and audio.get("data"):
                    did = self.mixer.take_sample(base64.b64decode(audio["data"]), int(audio.get("rate", 44100)), int(audio.get("channels", 2)),
                                                 str(v.get("role", "texture")), str(v.get("layer") or v.get("name", "")))
                    self.tell(f'Pulled "{v.get("name", "")}" from {v.get("source", "somewhere")} ({v.get("seconds", 0)} s; licence: '
                              f'{v.get("licence", "not stated")}): {did}.')
                continue
            if v.get("type") == "fresh":                        # a new theme: the old pictures leave the swarm, the old film stops
                if self.history:
                    GL.glDeleteTextures(list(self.history))
                    self.history = []
                self.history_pics = []                          # what has been memorised holds its own images, and is not touched
                self.swarm_due.clear()                          # (nor do the old pictures still being made small join it)
                self.flash, self.overlay_due = max(self.flash, 0.5), 0.0
                if v.get("what") == "pictures":                 # only the pictures are being replaced
                    continue
                self.reel, self.caption = [], ""
                if self.mixer:
                    self.mixer.clip = self.mixer.pending = None
                    self.mixer.forget_films()                   # the old films' layers go; pulled samples stay
                    self.mixer.groove.set_kit(None)             # the old story's sound leaves the instruments too
                winsound.PlaySound(None, winsound.SND_PURGE)
                continue
            if v.get("type") == "read":
                notes = self.notes + [(now, str(v.get("stream", "")), str(v.get("text", "")))]
                # the last thing you said stays up while the streams report on what followed from it
                self.notes = sorted([n for n in notes if n[1] == "steer"][-1:] + [n for n in notes if n[1] == "score"][-2:]
                                    + [n for n in notes if n[1] == "picture"][-2:] + [n for n in notes if n[1] == "film"][-2:]
                                    + [n for n in notes if n[1] not in ("steer", "score", "picture", "film")][-2:])
                self.overlay_due = 0.0
                continue
            if isinstance(v.get("link"), dict):                 # a video at a web address: a few seconds of it, as a film
                self.on_link(v["link"])
            if isinstance(v.get("drop"), list):                 # files dropped on the visuals panel: as if dropped here
                self.on_drop(self.win, [str(path) for path in v["drop"]])
            if "object" in v:                                   # an object with sides in place of the one surface (or None: no object)
                self.set_solid(v["object"])
            if isinstance(v.get("unshow"), int):                # something taken out of play
                self.unshow(v["unshow"])
            if isinstance(v.get("show"), int):                  # a picture or film off the shelf, back on screen
                self.show(v["show"])
            if v.get("release") is True:                        # everything turned by hand is given back to the story
                self.offset, self.hand = {}, set()
            if isinstance(v.get("image"), dict):                # the effects on each picture: {"image": {"bloom": 0.8}} is "image:bloom": 0.8
                v = {**v, **{"image:" + str(key): value for key, value in v["image"].items() if "image:" + str(key) in self.want}}
            aimed = [key for key in v if key.startswith("image:") and key in self.want]
            if aimed:       # the pictures differ from each other while the director has the say; set by hand, each gets exactly what was set
                self.image_varied = v.get("seq", 1) > 0 and not any(key in self.offset for key in aimed)
            elif v.get("release") is True:
                self.image_varied = True
            v = self.settle(v)                                  # who has the say over each setting in this message
            if isinstance(v.get("flat"), bool):
                self.hold_flat = v["flat"]
            if isinstance(v.get("flash"), (int, float)):
                self.flash = max(self.flash, min(float(v["flash"]), 1.0))
            for key in self.want:
                if isinstance(v.get(key), (int, float)):
                    self.want[key] = float(v[key])
            if v.get("shape") in ("sphere", "torus", "ribbon", "any"):
                self.shape_want = ("any", "sphere", "torus", "ribbon").index(v["shape"])
            tint = v.get("tint")
            if isinstance(tint, str) and len(tint) == 7:
                self.tint_want = np.array([int(tint[i:i + 2], 16) / 255 for i in (1, 3, 5)])
            if self.args.trace:
                self.trace("visuals: " + ", ".join(f"{k}={self.want[k]:g}" for k in self.want) + f", shape={v.get('shape')}, tint={tint}")
            if isinstance(v.get("memorise"), int):              # the screen and the music as they stand, kept under a number
                self.memorise_screen(v["memorise"])
                if self.mixer:
                    said = self.mixer.memorise(v["memorise"])
                    self.tell(said[0].upper() + said[1:] + ".")
                else:
                    self.tell(f"Memorised as {v['memorise']}.")
            if isinstance(v.get("recall"), int):                # ... and gone back to. A recall that includes the story is
                found = self.recall_screen(v["recall"], now)    # preceded by a "fresh", which cleared the screen: this refills it
                if self.mixer:
                    said = self.mixer.recall(v["recall"])
                    self.tell(said[0].upper() + said[1:] + ".")
                else:
                    self.tell(f"Back to {v['recall']}." if found else f"Nothing has been memorised as {v['recall']}.")
            fade = v.get("crossfade")
            if isinstance(fade, dict) and isinstance(fade.get("at"), (int, float)):     # somewhere between two memories: sound and screen
                if self.mixer:
                    self.mixer.crossfade(fade.get("a"), fade.get("b"), fade["at"])
                self.fade_screen(fade.get("a"), fade.get("b"), float(fade["at"]), now)
            if self.mixer and isinstance(v.get("timeline"), list):          # memories played in order, each left in its own way
                said = self.mixer.play_line(v["timeline"], bool(v.get("loop")))
                self.tell(said[0].upper() + said[1:] + ".")
            if self.mixer and v.get("lead") in instruments.LEADS:          # what the lead plays: as it comes, the film's sound, or one synth
                self.mixer.groove.lead_choice = v["lead"]
                self.tell("The lead: " + {"auto": "the film's sound and the scene's synth in turn, as it comes", "film": "the film's own sound"}.get(v["lead"], f"the {v['lead']}") + ".")
            if self.mixer and v.get("chop_style") in chopper.STYLES:       # how the sample layers are chopped
                self.tell(self.mixer.set_chop_style(v["chop_style"]).capitalize() + ".")
            if self.mixer and isinstance(v.get("role"), dict):              # a layer's role in the chop by hand; None: the engine's again
                self.tell(self.mixer.set_role(v["role"].get("layer"), v["role"].get("role")).capitalize() + ".")
            if self.mixer and isinstance(v.get("edge"), dict):              # the edge's two dials, their lips, or back to the session
                said = self.mixer.edge.take(v["edge"], self.mixer.groove.step // 16, session=v.get("seq", 0) > 0)
                if said:
                    self.tell("The edge: " + said + ".")
            if self.mixer and isinstance(v.get("roller"), (int, float)) and not isinstance(v.get("roller"), bool):     # bars a riff is held
                self.tell(self.mixer.edge.take_roller(v["roller"], self.mixer.groove.step // 16).capitalize() + ".")
            if self.mixer and isinstance(v.get("super"), (int, float)):     # the super knob: every part's knob moves with it
                if v.get("seq", 0) > 0:                         # asked for by the session: gone to slowly, or at once when the scene changes
                    self.super_goal = min(max(float(v["super"]), 0.0), 1.0)
                else:                                           # by hand: now, and it stays until the session next asks
                    self.super_goal = None
                    self.mixer.set_super(v["super"])
                    self.overlay_due = 0.0
            if self.mixer and isinstance(v.get("patch"), list):  # effects, layers and settings worked out from what was typed
                self.mixer.patch(v["patch"])
            if self.mixer and isinstance(v.get("parts"), list):  # how a part of the rhythm section sounds
                self.mixer.set_parts([(str(p[0]), str(p[1])) for p in v["parts"] if isinstance(p, (list, tuple)) and len(p) == 2])
                self.overlay_due = 0.0
            if v.get("seq", 0) == 0:                            # typed by the person watching: it must be seen to land, now
                self.snap_until = now + 1.5
                if not isinstance(v.get("memorise"), int):      # no flash on a memorise: it would whiten the small picture taken of this frame
                    self.flash = max(self.flash, 0.35)
                if not self.hold_flat:                          # if the picture is resting flat, set it moving so the change shows
                    self.kick_cycle = True
            if self.mixer:                                      # the same message scores the music; heard from the next sixteenth
                score = {k: v[k] for k in ("style", "key", "swing", "sub", "twinkle", "rescore", "break", "keep_patterns") if k in v}
                if isinstance(v.get("structure"), (int, float)):    # for how many bars the session leaves the structure alone
                    self.mixer.groove.structure_bars = int(min(max(round(v["structure"] / 4) * 4, 4), 64))
                if v.get("seq", 0) > 0:                         # the session's changes of structure wait for a four-bar line
                    structure = {k: score.pop(k) for k in STRUCTURAL if k in score}
                    if structure:
                        self.mixer.groove.later({**structure, **({"keep_patterns": True} if score.get("keep_patterns") else {})})
                changed = self.mixer.groove.set_score(score)
                if isinstance(v.get("bpm"), (int, float)) and v.get("seq", 0) == 0:
                    self.look["bpm"] = float(v["bpm"])          # a tempo typed by hand does not glide
                if changed:
                    self.overlay_due = 0.0
                    self.trace("music: " + changed)
        while True:
            try:
                source, kind, seq, text, detail = self.statuses.get_nowait()
            except queue.Empty:
                break
            lane = self.lanes.get(source)
            if lane is None:
                continue
            last = lane["segments"][-1] if lane["segments"] else None
            if last is not None and last[1] is None and (last[2], last[3]) == (kind, seq):
                lane["text"], lane["detail"] = text, detail
                continue
            if last is not None and last[1] is None:
                last[1] = now
            if kind != "idle":
                lane["segments"].append([now, None, kind, seq])
            lane.update(text=text, detail=detail, since=now, kind=kind)

    # ------------------------------------------------------------------ memorise and recall: what is on screen

    RANGES = {"chaos": (0.0, 2.0), "calm": (1.0, 10.0), "wild": (3.0, 30.0), "folds": (-1.0, 9.0), "trails": (0.0, 1.0), "swarm": (0.0, 1.0),
              "split": (0.0, 2.0), "spin": (0.0, 3.0), "zoom": (-1.0, 1.0), "sub": (0.0, 1.0), "twinkle": (0.0, 1.0), "swing": (0.0, 0.5),
              "super": (0.0, 1.0)}

    def settle(self, v):
        """Who has the say over each setting in a message; returns the message as it is to be applied.
        The director's message (its number is that of a beat): each number is moved by however far the hand has put that
        setting from where the director had it, and what the hand has chosen outright is left out.
        A message from a panel (-1), of which the story feed knows nothing: its numbers land as they are, and how far
        each now stands from the director's is remembered. Typed (0), the feed has taken it as its own: it lands, and
        that setting is level with the director again."""
        by_hand, direct, out = v.get("seq", 1) <= 0, v.get("seq", 1) < 0, dict(v)
        for key, (low, high) in self.RANGES.items():
            if isinstance(v.get(key), bool) or not isinstance(v.get(key), (int, float)):
                continue
            value = float(v[key])
            if direct:
                if key not in self.session:                     # the director has not said yet: where it stands now is its
                    now_at = self.want.get(key) if key in self.want else getattr(self.mixer.groove, key, getattr(self.mixer, key, None)) if self.mixer else None
                    self.session[key] = float(now_at) if isinstance(now_at, (int, float)) else value
                self.offset[key] = value - self.session[key]
            elif by_hand:
                self.offset.pop(key, None)
                self.session[key] = value
            else:
                self.session[key] = value
                out[key] = min(max(value + self.offset.get(key, 0.0), low), high)
        if isinstance(v.get("bpm"), (int, float)):              # the tempo of a memory gone back to stays, until a tempo is set by hand
            if by_hand:
                self.hand.discard("bpm")
            elif "bpm" in self.hand:
                out.pop("bpm")
        for key in ("style", "key", "shape", "tint"):
            if key in v and by_hand:
                self.hand.add(key)
            elif key in v and key in self.hand:
                out.pop(key)
        if by_hand:                                             # a pattern changed by hand is not written over by the director
            from mindstream.parts import WORDS
            words = [str(pair[1]) for pair in v.get("parts") or [] if isinstance(pair, (list, tuple)) and len(pair) == 2]
            steps = any(isinstance(op, dict) and "steps" in op for op in v.get("patch") or [])
            if steps or v.get("rescore") or "style" in v or any(WORDS.get(word, ("",))[0] == "pattern" for word in words):
                self.hand.add("patterns")
            if direct and any(key in v for key in ("patch", "parts", "super", "timeline", "crossfade", "recall")):
                self.hand.add("patterns")                       # the knob panel is in use: what the drums play is no longer the director's to replace
        elif "patterns" in self.hand:
            out.pop("style", None)
            out.pop("rescore", None)
            out["keep_patterns"] = True                         # and a change of key moves the riffs as they are: it writes no new ones
        return out

    def set_full(self, full):
        """Full screen, or back to a window. Full screen is a borderless window over the whole of the monitor the
        window is on, not the graphics card's exclusive mode: so the panels can sit on top of it, docked."""
        self.full = bool(full)
        if not self.full:
            self.screen = None
            glfw.set_window_attrib(self.win, glfw.DECORATED, glfw.TRUE)
            glfw.set_window_monitor(self.win, None, 80, 80, self.windowed[0], self.windowed[1], 0)
            return
        try:
            self.fill_monitor()
        except Exception as e:                                  # said, not swallowed: the panels dock by what this finds
            self.screen = None
            if hasattr(self, "notes") or hasattr(self, "args"):
                self.tell(f"Full screen could not be set up as a borderless window ({type(e).__name__}: {e}).")

    def fill_monitor(self):
        x, y = glfw.get_window_pos(self.win)
        w, h = glfw.get_window_size(self.win)
        best, most = glfw.get_primary_monitor(), -1
        for monitor in glfw.get_monitors():                     # the monitor most of the window is on
            mx, my = glfw.get_monitor_pos(monitor)
            mode = glfw.get_video_mode(monitor)
            shared = max(0, min(x + w, mx + mode.size.width) - max(x, mx)) * max(0, min(y + h, my + mode.size.height) - max(y, my))
            if shared > most:
                best, most = monitor, shared
        mx, my = glfw.get_monitor_pos(best)
        mode = glfw.get_video_mode(best)
        self.screen = [int(mx), int(my), int(mode.size.width), int(mode.size.height)]
        glfw.set_window_attrib(self.win, glfw.DECORATED, glfw.FALSE)
        # one row taller than the monitor: a window of exactly the monitor's size is taken over by the graphics driver as
        # if it were exclusive full screen, and then nothing else, the panels included, is drawn over it
        glfw.set_window_monitor(self.win, None, mx, my, mode.size.width, mode.size.height + 1, 0)

    def show_card(self, text, now):
        """A theme begins (the first, or a new one): its card is on screen at once and alone. It does not form over the
        picture that was there: both sides of the surface are the card, the trails of what was moving are wiped, and
        nothing waiting to be shown from before is shown. The swarm, the reel and the films' layers have gone with the
        "fresh" that comes before a new theme."""
        card = theme_card(text)
        card.info["shelved"] = card.info["card"] = True
        held = getattr(self, "waiting", collections.deque())
        if any(item is EOF for item in held):
            self.frames.put(EOF)
        held.clear()
        while True:                                             # pictures of the old theme still waiting their turn
            try:
                waiting = self.frames.get_nowait()
            except queue.Empty:
                break
            if waiting is EOF:
                self.frames.put(EOF)
                break
        upload(self.tex_a, card)
        upload(self.tex_b, card)
        self.pic_a = self.pic_b = card
        self.aspect, self.count = card.width / card.height, max(self.count, 1)
        self.blend = self.blend_target = 1.0
        self.forming, self.fading, self.wipe = False, None, True
        self.reel, self.reel_at, self.shown_frame = [], 0, None
        self.set_solid(None)                                    # an object goes too: the card is alone
        self.super_jump = True                                  # a new scene: the super knob goes straight to where the session wants it
        self.caption = text
        self.cycle_start, self.cycle_beat0, self.flash = now, self.beat, 0.6      # it arrives flat, with a flash, and then moves
        self.still_until, self.snap_until, self.overlay_due = now + self.look["calm"], now + 1.5, 0.0

    def to_launcher(self, message):
        """One line for the launcher (which passes it to the panel it is for). Only when there is a launcher listening."""
        if self.args.report_watching:                           # queued: the picture never waits on a busy launcher
            with self.outbox_lock:                              # (the shelf's packing, aside, tells the launcher too)
                if getattr(self, "outbox", None) is None:
                    self.outbox = Outbox(sys.stdout.write, sys.stdout.flush, name="to launcher")
            self.outbox.put(json.dumps(message) + "\n", latest="state" if "state" in message else None)

    def shelve(self, kind, item, image):
        """A picture or a film goes on the shelf, and the visuals panel is sent a small picture of it. The shelf holds
        the last 200 pictures and 40 films; older ones are let go. Packing a picture (a JPEG) and its small picture (a
        PNG) takes a large picture tens of milliseconds: that is done aside (packer), never in a frame; until it is
        done the shelf holds the picture itself (item "image")."""
        number, self.shelf_next = self.shelf_next, self.shelf_next + 1
        self.shelf[number] = {"kind": kind, **item}
        if kind == "picture":
            image.info["shelf"] = number                       # it carries its number, so what is in play can be named
        of_kind = [n for n, kept in self.shelf.items() if kept["kind"] == kind]
        for old in of_kind[:-{"picture": 200, "film": 40}.get(kind, 60)]:
            del self.shelf[old]
            self.to_launcher({"shelf_gone": old})
            if self.solid and any(old in side for side in self.solid["sides"]):
                self.set_solid(self.solid)                      # it leaves the object's sides too
        entry = self.shelf[number]

        def pack():
            try:
                if entry.get("image") is not None:
                    entry["jpeg"] = packed(entry["image"])
                    entry.pop("image", None)
                entry["png"] = small_png(image)                # kept, so a visuals panel opened later can be shown the shelf
                self.to_launcher({"shelf": number, "kind": kind, "png": entry["png"]})
            except Exception:
                pass
        self.packer.submit(pack)
        return number

    def shelve_film(self, clip):
        """A film on the shelf: at first as it is, then (worked out aside, since it takes a moment) with its frames
        packed small."""
        frames = clip["frames"]
        w, h, data = frames[len(frames) // 2]
        clip["shelf"] = self.shelve("film", {"clip": clip, "frames": None}, Image.frombytes("RGB", (w, h), data))
        item = self.shelf[clip["shelf"]]

        def pack():
            try:
                small = [packed(Image.frombytes("RGB", (fw, fh), raw)) for fw, fh, raw in frames]
                item["frames"], item["clip"] = small, {key: value for key, value in clip.items() if key != "frames"}
            except Exception:
                pass
        threading.Thread(target=pack, daemon=True).start()

    def show(self, number):
        """Something off the shelf, back on screen: a picture arrives as a new picture does; a film starts as a new
        film does (its sound comes in on the next bar line, and its layer is left as it is)."""
        item = self.shelf.get(number)
        if item is None:
            return
        if item["kind"] == "sound":
            if self.mixer:
                said = self.mixer.bring_back(item["sound"])
                self.tell(said[0].upper() + said[1:] + ".")
            return
        if item["kind"] == "picture":
            image = shelf_picture(item)
            image.info["shelved"], image.info["shelf"] = True, number
            self.frames.put((image, True, 1, 1))
            return

        def unpack():
            try:
                frames = item["clip"].get("frames")
                if frames is None:
                    frames = [(image.width, image.height, image.tobytes()) for image in (unpacked(data) for data in item["frames"])]
                self.clips.put({**item["clip"], "frames": frames, "follows": False, "shelved": True, "shelf": number})
            except Exception:
                pass
        threading.Thread(target=unpack, daemon=True).start()

    def follow_super(self):
        """The super knob going to where the session has asked it to be. On a scene boundary (the structure of the
        music has just changed, or a new theme has begun) it jumps there. Otherwise it creeps: one small step every
        fourth bar, a sixteenth of its travel at most, so the whole way takes sixty-four bars. (Every move makes every
        sound again, so it moves seldom.)"""
        if not self.mixer or self.super_goal is None:
            return
        g = self.mixer.groove
        boundary = self.super_jump or (self.super_change is not None and g.changed_at != self.super_change)
        self.super_change, self.super_jump = g.changed_at, False
        bar, now_at = g.step // 16, self.mixer.super
        if boundary:
            value = self.super_goal
        elif bar != self.super_bar and bar % 4 == 1:            # (the bar after a four-bar line: not when everything else is changing)
            value = now_at + min(max(self.super_goal - now_at, -1.0 / 16), 1.0 / 16)
        else:
            return
        self.super_bar = bar
        if abs(value - now_at) > 0.004:
            self.mixer.set_super(value)
            self.overlay_due = 0.0

    def set_solid(self, wanted):
        """The object with sides that stands in place of the one surface (None: no object, the surface again), and what
        is on each of its sides, by number on the shelf. What has come onto a side is got ready aside; what has left
        every side is let go."""
        self.solid = solids.clean(wanted, {number: item["kind"] for number, item in self.shelf.items()})
        used = {number for side in self.solid["sides"] for number in side} if self.solid else set()
        for number in [n for n in self.side_pics if n not in used]:
            tex = self.side_pics.pop(number)["tex"]
            if tex is not None:
                GL.glDeleteTextures([tex])
        for number in sorted(used - set(self.side_pics)):
            entry = self.side_pics[number] = {"tex": None, "frames": None, "fps": 12.0, "at": None, "aspect": 1.0}
            threading.Thread(target=self.ready_side, args=(self.shelf[number], entry), daemon=True).start()
        self.told_at = 0.0                                      # the panels hear of it at once

    @staticmethod
    def ready_side(item, entry):
        """Aside: a picture or a film off the shelf, unpacked for the side of an object."""
        try:
            if item["kind"] == "picture":
                frames, fps = side_frames([packed(shelf_picture(item))] if item.get("jpeg") is None else [item["jpeg"]], 1.0, wide=1024)
            else:
                clip = item["clip"]
                raw = clip.get("frames")
                frames, fps = side_frames(raw if raw is not None else item["frames"], clip.get("fps", 12.0))
            entry["fps"], entry["frames"] = fps, frames
        except Exception:
            pass

    def side_texture(self, number, now):
        """What a thing on a side looks like at this moment: (its texture, its shape), or None while it is being got
        ready. A film goes round and round; only a frame that has changed is sent to the GPU."""
        entry = self.side_pics.get(number)
        if not entry or not entry["frames"]:
            return None
        frames = entry["frames"]
        at = int((now - self.t0) * entry["fps"]) % len(frames)
        if entry["tex"] is None:
            entry["tex"] = make_texture()
        if entry["at"] != at:
            w, h, data = frames[at]
            put_pixels(entry["tex"], w, h, data)
            entry["at"], entry["aspect"] = at, w / h
        return entry["tex"], entry["aspect"]

    def draw_solid(self, now, t, eye, body, pulse, split, live):
        """The object: each side a flat picture in its place. A side with nothing on it shows what the session is
        showing (`live`: from, to, how far between, shape); with one thing, that; with several, a fade from each to the
        next in time with the beat. Each picture keeps its own shape, fitted inside the side."""
        kind = self.solid["kind"]
        out = solids.apothem(kind)
        for at, (about_x, about_y) in enumerate(solids.turns(kind)):
            ready = [got for got in (self.side_texture(number, now) for number in self.solid["sides"][at]) if got]
            if ready:
                one, two, blend = solids.showing(len(ready), self.beat, self.solid["every"])
                tex_one, tex_two = self.shown_as.get(ready[one][0], ready[one][0]), self.shown_as.get(ready[two][0], ready[two][0])
                shape = ready[one][1] + (ready[two][1] - ready[one][1]) * blend
            else:
                tex_one, tex_two, blend, shape = live
            m = body @ rotation(about_x, about_y, 0.0) @ translate(0.0, 0.0, out) @ scale(min(1.0, 1.0 / max(shape, 0.01)))
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, tex_one)
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glBindTexture(GL.GL_TEXTURE_2D, tex_two)
            self.u_surface(mvp=eye @ m, model=m, t=t + at, flat_=1.0, mixAB=0.0, pulse=pulse, chaos=self.chaos, aspect=shape,
                           shapeA=1, shapeB=1, texA=0, texB=1, blend=float(blend), alpha=1.0, flash=self.flash, split=split, shade=0.6)
            GL.glDrawElements(GL.GL_TRIANGLES, self.grid_count, GL.GL_UNSIGNED_INT, None)

    def toggle_panel(self, which):
        """The knob panel or the visuals panel, opened or closed (the launcher does it). A panel that has just been
        opened knows nothing: it is told how things stand, and sent the small pictures it shows."""
        self.to_launcher({"panel": which})
        self.told = None                                        # how things stand is told again, to whichever panels are open
        if which == "knobs":
            for n, kept in sorted(self.kept.items()):
                self.to_launcher({"thumb": n, "png": kept.get("png", "")})
        else:
            for number, item in sorted(self.shelf.items()):
                if item.get("png"):
                    self.to_launcher({"shelf": number, "kind": item["kind"], "png": item["png"]})

    def tell_panels(self, now):
        """How things stand, told to the panels twice a second when anything has moved: the session moves the knobs."""
        if now - self.told_at < 0.5 or not self.args.report_watching:
            return
        self.told_at = now
        tint = "#%02x%02x%02x" % tuple(int(min(max(c, 0.0), 1.0) * 255) for c in self.tint_want)
        state = {"look": {key: round(value, 3) for key, value in self.want.items()}, "shape": ("any", "sphere", "torus", "ribbon")[self.shape_want],
                 "tint": tint, "flat": bool(self.hold_flat), "full": self.full, "screen": self.screen, "live": self.in_play(), "object": self.solid,
                 **(self.mixer.stands() if self.mixer else {})}
        if state != self.told:
            self.told = state
            self.to_launcher({"state": state})

    def in_play(self):
        """What is in play right now, by its number on the shelf: the picture showing, the earlier pictures in the swarm,
        the film on the reel, and the sounds that are in."""
        sounds = {item["name"]: number for number, item in self.shelf.items() if item["kind"] == "sound"}
        showing = self.pic_b.info.get("shelf") if self.pic_b is not None else None
        swarm = [small.info.get("shelf") for small in self.history_pics]
        playing = self.mixer.stands()["in"] if self.mixer else []
        return {"picture": showing, "swarm": [n for n in swarm if n and n != showing],
                "film": self.reel[min(self.reel_at, len(self.reel) - 1)].get("shelf") if self.reel else None,
                "sounds": [sounds[name] for name in playing if name in sounds]}

    def unshow(self, number):
        """Something taken out of play: a picture leaves the swarm, a film leaves the reel (the pictures show again), a
        sound's layer is taken out. The picture showing stays: there is always a picture."""
        item = self.shelf.get(number)
        if item is None:
            return
        if item["kind"] == "sound":
            if self.mixer:
                self.mixer.patch([{"part": item["name"], "bring": False}])
        elif item["kind"] == "film":
            if self.reel and self.reel[min(self.reel_at, len(self.reel) - 1)].get("shelf") == number:
                self.reel, self.reel_at, self.shown_frame = [], 0, None
        else:
            for at in reversed([i for i, small in enumerate(self.history_pics) if small.info.get("shelf") == number]):
                GL.glDeleteTextures([self.history.pop(at)])
                self.history_pics.pop(at)
        self.told_at = 0.0                                      # the panels hear of it at once

    def shelve_sounds(self):
        """Every sound that becomes a layer goes on the shelf beside the pictures and films, as a small drawing of its
        shape with its name."""
        while self.mixer:
            new = self.mixer.heard_new()
            if new is None:
                return
            self.shelve("sound", {"sound": new["sound"], "name": new["name"]}, wave_card(new["peaks"], new["name"], new["film"]))

    def follow_line(self, now):
        """The timeline has gone to another memory: the screen goes with the music, and the launcher is told (the knob
        panel shows where it is)."""
        slot = self.mixer.arrived() if self.mixer else None
        if slot is None:
            return
        self.recall_screen(slot, now)
        self.overlay_due = 0.0
        if self.args.report_watching:
            try:
                sys.stdout.write(json.dumps({"arrived": slot}) + "\n")
                sys.stdout.flush()
            except (OSError, ValueError):
                pass

    def memorise_screen(self, n):
        """What is on screen, kept under a number (in memory only), and a small picture of it asked for: that is
        taken from the next frame drawn (send_thumbs)."""
        self.kept[n] = keep_screen((self.pic_a, self.pic_b), self.history_pics, self.aspect, self.caption, self.reel,
                                   self.reel_at, self.want, self.tint_want, self.shape_want)
        self.kept[n]["object"] = json.loads(json.dumps(self.solid))
        if self.args.report_watching and n not in self.grab_for:
            self.grab_for.append(n)

    def recall_screen(self, n, now):
        """Back to what was on screen when that number was memorised. False if nothing was."""
        kept = self.kept.get(n)
        if kept is None:
            return False
        if self.history:                                        # the swarm, made again from the small pictures
            GL.glDeleteTextures(list(self.history))
        self.history_pics = list(kept["small"])
        self.swarm_due.clear()
        self.history = [make_texture(small) for small in self.history_pics]
        a, b = kept["pics"]
        a, b = a or b, b or a                                   # only one picture so far: it is both "from" and "to"
        if b is not None:                                       # (none at all: the surface is left as it is)
            upload(self.tex_a, a)
            upload(self.tex_b, b)
            self.pic_a, self.pic_b = a, b
            self.count = max(self.count, 1)
        self.blend = self.blend_target = 1.0
        self.forming, self.fading = False, None
        self.aspect, self.caption = kept["aspect"], kept["caption"]
        # the reel as it was, from the start of the film it was on, and NOT through start_segment: that would queue the
        # film's sound again, and the mixer puts its own layers back
        self.reel, self.reel_at = list(kept["reel"]), kept["reel_at"]
        self.segment_start, self.shown_frame, self.still_until = now, None, 0.0
        self.want, self.tint_want, self.shape_want = dict(kept["want"]), np.array(kept["tint"], dtype=float), kept["shape"]
        # its tempo is the scene's: taken up at once (no glide), and not moved by the story's director afterwards, which
        # may not know of the recall (the timeline and the crossfader go between memories without telling it)
        self.look["bpm"] = self.want["bpm"]
        self.hand.add("bpm")
        self.overlay_due, self.flash = 0.0, max(self.flash, 0.3)
        self.set_solid(kept.get("object"))                      # the object as it was (less anything since let go from the shelf)
        return True

    def fade_screen(self, a, b, at, now):
        """The screen somewhere between two memories: 0 is all of `a`, 1 all of `b`. The picture is a mix of the two
        memories' pictures in that proportion, and the look and the tint stand that share of the way between theirs.
        What cannot be mixed (the caption, the swarm of earlier pictures, the reel, the shape) is `a`'s on its half
        and `b`'s on the other. While it is being moved the pictures are shown, not the film."""
        one, two = self.kept.get(a), self.kept.get(b)
        if one is None or two is None or a == b:
            return False
        at = min(max(at, 0.0), 1.0)
        side, kept = (a, one) if at < 0.5 else (b, two)
        first, second = one["pics"][1] or one["pics"][0], two["pics"][1] or two["pics"][0]
        was = self.fading
        if first is not None and second is not None:
            if was is None or was[:2] != (a, b):                # the two pictures, loaded once for this pair
                upload(self.tex_a, first)
                upload(self.tex_b, second)
                self.pic_a, self.pic_b = first, second
                self.count, self.forming = max(self.count, 1), False
            self.blend_target = at                              # the mix eases toward where the fader stands
            self.still_until = now + 4.0
        if was is None or was != (a, b, side):                  # over the middle: what cannot be mixed changes sides
            if self.history:
                GL.glDeleteTextures(list(self.history))
            self.history_pics = list(kept["small"])
            self.swarm_due.clear()
            self.history = [make_texture(small) for small in self.history_pics]
            self.aspect, self.caption, self.shape_want = kept["aspect"], kept["caption"], kept["shape"]
            self.reel, self.reel_at = list(kept["reel"]), kept["reel_at"]
            self.segment_start, self.shown_frame = now, None
        self.fading = (a, b, side)
        self.want = mixed(one["want"], two["want"], at)
        self.tint_want = np.array(one["tint"], dtype=float) * (1.0 - at) + np.array(two["tint"], dtype=float) * at
        self.overlay_due = 0.0
        return True

    def send_thumbs(self):
        """The small picture for a memory's button: the middle of the frame just drawn (and not yet swapped to the
        screen), read back, shrunk and told to the launcher as a PNG. Whatever goes wrong here is let go: a missing
        picture on a button must never stop the drawing."""
        slots, self.grab_for = self.grab_for, []
        try:
            w, h = glfw.get_framebuffer_size(self.win)
            if not slots or not self.args.report_watching or w < 2 or h < 2:
                return
            x, y, side = centre_square(w, h)
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
            GL.glPixelStorei(GL.GL_PACK_ALIGNMENT, 1)
            data = GL.glReadPixels(x, y, side, side, GL.GL_RGB, GL.GL_UNSIGNED_BYTE)
            png = base64.b64encode(thumb_png(data.tobytes() if hasattr(data, "tobytes") else bytes(data), side)).decode("ascii")
            for n in slots:
                if n in self.kept:
                    self.kept[n]["png"] = png                   # kept, so a knob panel opened later can be given its buttons
                sys.stdout.write(json.dumps({"thumb": n, "png": png}) + "\n")
            sys.stdout.flush()
        except Exception:
            pass

    # ------------------------------------------------------------------ the roll: each part of the music, playing

    ROLL_STEP, ROLL_ROW, ROLL_LEFT, ROLL_NOTE = 5, 11, 40, 66        # pixels: a sixteenth, a row, the names, the notes on the right. Tiny.

    def draw_roll(self):
        """Two bars of every part, by name, with a line where the music is now: what has sounded to its left, what
        is coming to its right. Small, and redrawn several times a second, so it moves with the music."""
        at, rows = self.mixer.roll()
        step, row_h, left = self.ROLL_STEP, self.ROLL_ROW, self.ROLL_LEFT
        wide, high = left + 32 * step + self.ROLL_NOTE, len(rows) * row_h + 10
        img = Image.new("RGBA", (wide, high), (0, 0, 0, 130))
        d = ImageDraw.Draw(img)
        for n in range(0, 33, 4):                                # beat lines, and heavier bar lines
            d.line([left + n * step, 4, left + n * step, high - 5], fill=(255, 255, 255, 70 if n % 16 == 0 else 26))
        for i, row in enumerate(rows):
            y = 5 + i * row_h
            lit = row["playing"]
            d.text((4, y - 1), row["name"], font=self.tiny, fill=(255, 200, 120, 255) if lit else (125, 115, 105, 255))
            for offset, length, pitch, coming in row["cells"]:
                x0 = left + offset * step
                x1 = min(x0 + max(length * step - 2, 3), left + 32 * step)
                colour = (150, 150, 165, 110) if coming else (255, 214, 150, 255) if pitch is not None else (235, 235, 245, 255)
                if pitch is None:                                # a drum, or the film's sound: a block the height of the row
                    d.rectangle([x0, y + 2, x1, y + row_h - 3], fill=colour)
                else:                                            # a note: higher notes sit higher in the row
                    yy = y + row_h - 4 - (pitch % 12) / 11.0 * (row_h - 6)
                    d.rectangle([x0, yy, x1, yy + 1], fill=colour)
            if row["changed"]:
                d.text((wide - 3, y - 1), row["changed"][:11], font=self.tiny, fill=(140, 220, 160, 255), anchor="ra")
        x = left + at * step
        d.line([x, 2, x, high - 3], fill=(255, 120, 90, 255), width=2)
        upload(self.roll_tex, img)
        self.roll_size = (wide, high)

    # ------------------------------------------------------------------ overlay: caption + flow strip

    def overlay_snapshot(self, now, w, h):
        """On the frame's own thread: what has aged out is dropped, and what the overlay shows is copied, so that the
        drawing itself (a picture the size of the window, tens of milliseconds) can be done aside (overlay_image)."""
        self.notes = [n for n in self.notes if now - n[0] < 240]
        span = self.args.flow_span
        for lane in self.lanes.values():
            lane["segments"] = [s for s in lane["segments"] if (s[1] or now) > now - span]
        tempo = ("HELD FLAT (Ctrl+Space)   " if self.hold_flat else "") + f"{self.bpm_now:.0f} bpm" + (" from the soundtrack" if self.bpm_locked else "")
        if self.mixer:
            tempo += f"  {self.mixer.groove.archetype or self.mixer.groove.style}  {self.mixer.groove.key()}"
        return SimpleNamespace(now=now, w=w, h=h, caption=self.caption, notes=list(self.notes), typing=self.typing, tempo=tempo,
                               lanes={key: {**lane, "segments": [list(s) for s in lane["segments"]]} for key, lane in self.lanes.items()},
                               hint=self.args.report_watching and now - self.t0 < 90)

    def overlay_image(self, s):
        """Aside: the overlay drawn from a snapshot. Returns its pixels (RGBA, as the texture takes them), its size, and
        where the panel of the parts may sit above (panel_floor)."""
        now, w, h = s.now, s.w, s.h
        lane_h, left, span = 20, 84, self.args.flow_span
        strip_h = len(LANES) * lane_h + 8
        lines = []
        if s.caption:
            words, line = s.caption.split(), ""
            for word in words:
                trial = (line + " " + word).strip()
                if self.font.getlength(trial) > w - 80 and line:
                    lines.append(line)
                    line = word
                else:
                    line = trial
            lines.append(line)
        text_h = len(lines) * (self.args.text_size + 8) + (16 if lines else 0)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        top = h - strip_h - text_h
        if lines:
            d.rectangle([0, top, w, h - strip_h], fill=(0, 0, 0, 150))
            for i, line in enumerate(lines):
                d.text((w / 2, top + 8 + i * (self.args.text_size + 8)), line, font=self.font, fill=(230, 230, 230, 255), anchor="ma")
        # the running account, down the two sides, so the middle and the top stay clear: on the left what you said
        # and how the music and motion answered; on the right what is being painted and filmed
        wide = int(min(max(w * 0.17, 210), 330))
        floor = (top if lines else h - strip_h) - 28
        for side, streams in ((0, ("steer", "score", "sound")), (1, ("picture", "film"))):
            rows = []
            for when, stream, text in reversed([n for n in s.notes if n[1] in streams]):     # newest at the top
                age = now - when
                rows.append((stream, age, True))
                row = ""
                for word in text.split() + [None]:
                    trial = (row + " " + word).strip() if word is not None else None
                    if word is None or (self.mono.getlength(trial) > wide - 16 and row):
                        rows.append((row, age, False))
                        row = word or ""
                    else:
                        row = trial
                rows.append(("", age, False))
            rows = rows[:max(0, (floor - 12) // 16)]
            while rows and not rows[-1][0]:
                rows.pop()
            if not rows:
                continue
            x = 8 if side == 0 else w - 8 - wide
            d.rectangle([x, 8, x + wide, 16 + len(rows) * 16], fill=(0, 0, 0, 120))
            for i, (row, age, heading) in enumerate(rows):
                shade = 235 if age < 20 else 175 if age < 90 else 125
                fill = ((255, 200, 120, 255) if age < 20 else (160, 135, 100, 255)) if heading else (shade, shade, shade + 10, 255)
                d.text((x + 8, 12 + i * 16), row, font=self.mono, fill=fill)
        d.rectangle([0, h - strip_h, w, h], fill=(8, 8, 10, 190))
        for row, (key, name) in enumerate(LANES):
            lane, y = s.lanes[key], h - strip_h + 4 + row * lane_h
            d.text((6, y + 3), name, font=self.mono, fill=(112, 112, 122, 255))
            for start, end, kind, seq in lane["segments"]:
                x0 = max(w - (now - start) / span * (w - left), left)
                x1 = max(w - (now - (end or now)) / span * (w - left), x0 + 1)
                d.rectangle([x0, y + 2, x1, y + lane_h - 3], fill=COLOURS.get(kind, (100, 100, 100)) + (230,))
                if seq and x1 - x0 > 16:
                    d.text((x0 + 4, y + 3), str(seq), font=self.mono, fill=(10, 10, 12, 255))
            if lane["text"]:
                words = lane["text"] + (f"  ·  {lane['detail']}" if lane["detail"] else "")
                if lane["kind"] not in ("idle", "stop"):
                    words += f"  ·  {int(now - lane['since'])} s"
                d.text((left + 6, y + 3), words, font=self.mono,
                       fill=(255, 128, 128, 255) if lane["kind"] == "error" else (205, 205, 215, 255))
        panel_floor = top if lines else h - strip_h            # the roll of the parts sits above this (draw_roll)
        if s.typing:                                            # the steer being typed, large, just above the caption
            box = (top if lines else h - strip_h) - 46
            d.rectangle([w * 0.2, box, w * 0.8, box + 36], fill=(0, 0, 0, 200), outline=(255, 200, 120, 255))
            shown = s.typing
            while self.font.getlength("> " + shown + "_") > w * 0.6 - 24 and len(shown) > 1:
                shown = shown[1:]
            d.text((w * 0.2 + 12, box + 5), "> " + shown + "_", font=self.font, fill=(255, 240, 220, 255))
        elif s.hint:
            d.text((8, (top if lines else h - strip_h) - 18), "type here to steer, Enter sends  |  Ctrl+ F full screen, M overlays, "
                   "Space hold flat, R replay film, A mute, G drums, C chops, K knobs, V visuals  |  Esc quits", font=self.mono, fill=(150, 150, 160, 255))
        d.text((w - 8, h - strip_h - 18 if not lines else top - 18), s.tempo, font=self.mono, fill=(150, 150, 160, 255), anchor="ra")
        return img.tobytes(), w, h, panel_floor

    def draw_overlay(self, now, w, h):
        """The overlay drawn now, on this thread (the frame uses overlay_snapshot and overlay_image aside instead)."""
        data, ow, oh, self.panel_floor = self.overlay_image(self.overlay_snapshot(now, w, h))
        put_pixels(self.overlay_tex, ow, oh, data, alpha=True)

    def follow_overlay(self, now, w, h):
        """The overlay kept up to date without holding up a frame: a drawing finished aside is sent to the card (into
        the texture's own storage), and when one is due and none is being drawn, the next is started."""
        job = self.overlay_job
        if job is not None and job.done():
            self.overlay_job = None
            try:
                began = time.perf_counter()
                data, ow, oh, self.panel_floor = job.result()
                put_pixels(self.overlay_tex, ow, oh, data, alpha=True)
                self.hitches.note("overlay sent to the card", time.perf_counter() - began)
            except Exception as e:
                self.trace(f"overlay: {e}")
        if now >= self.overlay_due and self.overlay_job is None:
            self.overlay_job = self.drawer.submit(self.overlay_image, self.overlay_snapshot(now, w, h))
            self.overlay_due = now + 0.5

    # ------------------------------------------------------------------ one frame

    def frame(self):
        now = time.time()
        t = now - self.t0
        dt = min(now - getattr(self, "last", now), 0.1)
        self.last = now
        w, h = glfw.get_framebuffer_size(self.win)
        if w < 2 or h < 2:
            self.report_watching()
            time.sleep(0.05)
            return
        sharp = round(min(max(self.want.get("sharp", 1.0), 1.0), 2.0) * 4) / 4      # drawn at up to twice the size, and brought down
        if (w, h, sharp) != self.size:
            for target in (self.targets or []) + (self.screen_bench.all() if self.screen_bench else []):
                target.free()
            for key in list(self.fx_state):                     # what the effects remembered was the old size
                self.fx_free(key, keep=False)
            for kept in [key for key in self.pool.spare if key[0] != "ring" and key not in {t.key for b in self.benches.values() for t in b.all()}]:
                for _, thing in self.pool.spare.pop(kept):      # spares of the old size (the pictures' own sizes stay)
                    thing.free()
            for kept in [key for key in self.pool.spare if key[0] == "ring"]:
                for _, thing in self.pool.spare.pop(kept):
                    thing.free()
            # (kept as fractions and not bytes: in bytes a long trail cannot fade below a grey floor)
            self.targets = [Target(int(w * sharp), int(h * sharp), True, fine=True), Target(int(w * sharp), int(h * sharp), True, fine=True)]
            # the screen's scratch framebuffers are made now, with the screen, and not the first time an effect is
            # turned up (which used to stall that frame)
            self.screen_bench = Bench(self.pool, self.targets[0].w, self.targets[0].h, w, h)
            if self.particles is None and all(name in self.fx for name in fx.needs("particles")):
                self.particles = [self.pool.state(*fx.PARTICLES), self.pool.state(*fx.PARTICLES)]      # once: the first time there is a screen
                self.hitches.note("the particles' state made")
            self.hitches.note(f"the screen's framebuffers made ({int(w * sharp)}x{int(h * sharp)})")
            self.size, self.overlay_due = (w, h, sharp), 0.0
        rw, rh = self.targets[0].w, self.targets[0].h
        made = self.pool.made
        began = time.perf_counter()
        self.take_input(now)
        if time.perf_counter() - began > 0.004:
            self.hitches.note("what came in taken", time.perf_counter() - began)
        if getattr(self, "wipe", False):                        # a new theme: the trails of the old picture are not carried into it
            for target in self.targets:
                GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, target.fbo)
                GL.glClearColor(0.0, 0.0, 0.0, 1.0)
                GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
            self.wipe = False
        self.follow_line(now)
        self.follow_super()
        self.shelve_sounds()
        self.tell_panels(now)
        self.report_watching()

        look = self.look
        self.glide(look, now, dt)                               # so a new beat changes the motion smoothly
        self.shed_level(now, dt)
        self.pool.trim(now)
        self.tint += (self.tint_want - self.tint) * min(1.0, dt * 0.9)
        self.chaos = look["chaos"]
        video = bool(self.reel) and now >= self.still_until
        picture_aspect = self.play_reel(now) if video else self.aspect
        # The tempo. While a clip with a measured soundtrack tempo is playing, the pulse is locked to what
        # is heard: same tempo, kicks landing on its beats. Otherwise it follows the story's tempo.
        heard = self.reel[self.reel_at].get("tempo") if self.reel and not self.mixer else None
        bpm = heard["bpm"] if heard else look["bpm"]
        self.bpm_now, self.bpm_locked = bpm, bool(heard)
        if self.mixer:                                          # our own rhythm section sets the time
            self.mixer.groove.bpm, self.mixer.groove.energy = bpm, min(look["chaos"] / 2.0, 1.0)
            self.beat = max(self.beat, self.mixer.beat())
        else:
            self.beat += dt * bpm / 60.0                        # total beats so far: scene changes count in these
        position = (now - self.segment_start - heard["offset"]) * bpm / 60.0 if heard else self.beat
        pulse = (1.0 - (position % 1.0)) ** 4                   # a kick on every beat, decaying
        bars = lambda seconds: max(1, round(seconds * bpm / 60.0 / 4.0)) * 4.0     # whole bars of four, in beats
        calm_beats, wild_beats = bars(look["calm"]), bars(look["wild"])
        cycle = self.beat - self.cycle_beat0
        if self.kick_cycle:                                     # a typed change while resting flat: the motion starts now
            self.kick_cycle = False
            if cycle < calm_beats:
                self.cycle_beat0, cycle = self.beat - calm_beats, calm_beats
        if cycle > calm_beats + wild_beats:                     # next cycle, on a bar line: new pair of shapes
            self.cycle_beat0, cycle = math.floor(self.beat), 0.0
            nxt = self.shape_want or random.choice([s for s in (1, 2, 3) if s != self.shape_b])
            self.shape_a, self.shape_b = self.shape_b, nxt
        calm = cycle < calm_beats or self.hold_flat or (self.count == 0 and not video) or (video and (self.mixer.premiere() if self.mixer else now < self.premiere_until))
        self.flat += ((1.0 if calm else 0.0) - self.flat) * min(1.0, dt * (2.2 if calm else 1.4))
        mix_ab = 0.5 - 0.5 * math.cos(math.pi * min(max(cycle - calm_beats, 0.0) / wild_beats, 1.0))
        self.blend += (self.blend_target - self.blend) * min(1.0, dt * 3.0)
        self.flash *= math.exp(-dt * 4.0)
        wild = 1.0 - self.flat
        self.spin += dt * np.array([0.5, 0.9, 0.3]) * (0.15 + 1.6 * wild * self.chaos) * (1.0 + 1.5 * pulse * wild) * look["spin"]
        calm_rot = np.array([0.10 * math.sin(t * 0.7), 0.16 * math.sin(t * 0.5), 0.03 * math.sin(t * 0.9)])
        angles = self.spin * wild + calm_rot                    # opens out facing the viewer when flat

        if not self.fx_broken and not getattr(self, "images_broken", False):
            try:                                                # 0. each picture through its own effects, before anything is drawn
                self.prepare_images(now, t, pulse, bpm, dt, video)
            except Exception as e:                              # a picture's effects must never take the picture with them
                self.images_broken, self.shown_as = True, {}
                self.tell(f"The effects on each picture have been switched off: one of them failed ({type(e).__name__}). The screen's carry on.")
                self.trace(f"picture effects: {e}")
        shown_as = self.shown_as.get
        scene, last = self.targets
        aspect = w / h
        proj = perspective(math.radians(50), aspect, 0.1, 50.0)
        fit = min(1.0, aspect / picture_aspect) * 0.92           # flat picture fills the height or the width
        view = translate(0, 0, -(2.2 + 0.9 * wild))
        model = rotation(*angles) @ scale(fit * (1.0 + 0.04 * pulse * self.chaos))

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, scene.fbo)
        GL.glViewport(0, 0, rw, rh)
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_BLEND)
        GL.glUseProgram(self.feedback)                          # 1. last frame, swirled and folded: the trails
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, last.tex)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex_b)
        self.u_feedback(last=0, picture=1, t=t, pulse=pulse, chaos=self.chaos, flat_=self.flat, aspect=aspect,
                        folds=look["folds"], trails=look["trails"], zoom=look["zoom"], flow=look["flow"])
        GL.glBindVertexArray(self.quad_vao)
        GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glUseProgram(self.surface)
        GL.glBindVertexArray(self.grid_vao)
        if self.history:                                        # 2. earlier pictures: a swarm of shards
            for i, (radius, phase, speed, height, size, tilt) in enumerate(self.swarm[:max(int(len(self.swarm) * look["swarm"]), 0)]):
                ang = phase + t * speed * (0.4 + self.chaos)
                pos = translate(radius * math.cos(ang) * (1.0 + 0.8 * self.flat), height + 0.3 * math.sin(t + phase),
                                radius * math.sin(ang) - 0.5)
                m = pos @ rotation(tilt + t * speed, ang, tilt * 0.5) @ scale(size * (1.0 + 0.5 * pulse))
                GL.glActiveTexture(GL.GL_TEXTURE0)
                GL.glBindTexture(GL.GL_TEXTURE_2D, shown_as(self.history[i % len(self.history)], self.history[i % len(self.history)]))
                self.u_surface(mvp=proj @ view @ m, model=m, t=t + phase, flat_=1.0, mixAB=0.0, pulse=pulse, chaos=self.chaos,
                               aspect=1.0, shapeA=1, shapeB=1, texA=0, texB=0, blend=0.0,
                               alpha=0.85 * (1.0 - 0.75 * self.flat) * min(self.chaos + 0.3, 1.0), flash=0.0, split=look["split"], shade=0.0)
                GL.glDrawElements(GL.GL_TRIANGLES, self.grid_count, GL.GL_UNSIGNED_INT, None)
        if self.solid:                                          # 3. an object with sides, each with its own pictures and films
            kind = self.solid["kind"]
            # it never stops: flat, it turns steadily about its upright, each side coming round the right way up (the
            # spin setting is how fast; a beat gives it a small push); moving, it tumbles as well
            self.solid_turn += dt * 0.7 * look["spin"] * (1.0 + 0.6 * pulse * self.chaos)
            turned = self.spin * wild + calm_rot + np.array([0.0, self.solid_turn, 0.0])
            body = rotation(*turned) @ scale(solids.size(kind) * min(1.0, aspect) * (1.0 + 0.04 * pulse * self.chaos))
            live_a, live_b = (self.tex_video, self.tex_video) if video else (self.tex_a, self.tex_b)
            self.draw_solid(now, t, proj @ view, body, pulse, look["split"], (shown_as(live_a, live_a), shown_as(live_b, live_b), self.blend, picture_aspect))
        else:                                                   # 3. the current picture (or video frame) on the morphing surface
            live_a, live_b = (self.tex_video, self.tex_video) if video else (self.tex_a, self.tex_b)
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, shown_as(live_a, live_a))
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glBindTexture(GL.GL_TEXTURE_2D, shown_as(live_b, live_b))
            self.u_surface(mvp=proj @ view @ model, model=model, t=t, flat_=self.flat, mixAB=mix_ab, pulse=pulse, chaos=self.chaos,
                           aspect=picture_aspect, shapeA=self.shape_a, shapeB=self.shape_b, texA=0, texB=1, blend=self.blend,
                           alpha=1.0, flash=self.flash, split=look["split"], shade=0.0)
            GL.glDrawElements(GL.GL_TRIANGLES, self.grid_count, GL.GL_UNSIGNED_INT, None)

        shown, toned, pointed, had_points = scene.tex, False, False, self.pt_rows > 0
        # the last passes' settings (exposure and the tone curve, the lens, the colours pulled apart, the tint, grain)
        self.out_with = dict(scene=0, pulse=pulse, chaos=self.chaos, flat_=self.flat, split=look["split"], tintR=self.tint[0], tintG=self.tint[1],
                             tintB=self.tint[2], lens=look["lens"], grain=look["grain"], t=t % 1000.0, exposure=look["exposure"],
                             tonemap=look["tonemap"], frame=float(self.rendered % 4096))
        if not self.fx_broken:
            try:
                if look["particles"] > 0.004 and self.particles and all(name in self.fx for name in fx.needs("particles")):
                    live_a, live_b = (self.tex_video, self.tex_video) if video else (self.tex_a, self.tex_b)     # 3b. the picture as a cloud of points
                    self.draw_points(scene, look["particles"], proj @ view @ model, t, pulse, picture_aspect, rw, rh,
                                     (shown_as(live_a, live_a), shown_as(live_b, live_b), self.blend), dt, bpm)
                    pointed = True
                shown, toned = self.run_effects(scene.tex, look, t, pulse, w, h, rw, rh, dt, bpm)     # 3c. the effects, each one or more passes over the whole screen
            except Exception as e:                              # an effect must never take the picture with it
                self.fx_broken, shown, toned = True, scene.tex, False
                self.lin = 0.0
                self.tell(f"The effects have been switched off: one of them failed ({type(e).__name__}). The picture carries on without them.")
                self.trace(f"effects: {e}")
        if pointed != had_points:
            self.hitches.note("particles " + ("on" if pointed else "off"))
        if not pointed:
            self.pt_rows = 0                                    # (when they come back, all are born afresh)
        GL.glBindVertexArray(self.quad_vao)                     # 4. to the screen: the light brought down to it (unless the effects on
        self.output(shown, 0, w, h, tone=not toned, finish=True)     # the finished picture have had it already), grain, dither
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        if self.overlay_on:                                     # 5. caption and flow strip on top
            self.follow_overlay(now, w, h)                      # drawn aside; sent to the card when ready
            GL.glEnable(GL.GL_BLEND)
            GL.glUseProgram(self.overlay)
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.overlay_tex)
            self.u_overlay(tex=0)
            GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)
            if self.mixer:                                      # 6. the roll of the parts, bottom right, above the caption
                if now >= self.roll_due:
                    self.draw_roll()
                    self.roll_due = now + 0.1
                rw, rh = self.roll_size
                if rw and self.panel_floor - 44 - rh > 0:
                    GL.glViewport(w - rw - 8, h - (self.panel_floor - 44), rw, rh)       # the same quad, drawn into a corner
                    GL.glBindTexture(GL.GL_TEXTURE_2D, self.roll_tex)
                    GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)
                    GL.glViewport(0, 0, w, h)
        self.targets = [last, scene]                            # this frame becomes next frame's trails
        self.rendered += 1
        if self.pool.made > made:
            self.hitches.note(f"{self.pool.made - made} framebuffer(s) made")

    # (the exposure is not cut on its way out: it has two sides, and 0 is where it rests, not "off")
    FX_KEYS = frozenset(k for k in effects.KEYS if k != "sharp" and k not in effects.SIGNED) | frozenset(effects.IMAGE_RANGES)
    HEAVY_SETS = (frozenset(effects.HEAVY), frozenset("image:" + k for k in effects.HEAVY if k in effects.IMAGE))

    def glide(self, look, now, dt):
        """Every setting moves toward where it is wanted, so a new beat changes the motion smoothly. An effect on its
        way out goes faster, and is cut once it can no longer be seen (2%), rather than running its passes for
        seconds at a strength no one can see. A heavy effect on its way in waits while another heavy one (on the same
        target) is still on its way out: two heavy effects are never both running for the length of a cross-fade."""
        fast = now < self.snap_until
        want = self.want
        going = [{k for k in heavy if look.get(k, 0.0) > 0.004 and want.get(k, 0.0) <= 0.0} for heavy in self.HEAVY_SETS]
        for key, target in want.items():
            rate = 6.0 if fast else 4.0 if key == "folds" else 0.9
            if key in self.FX_KEYS:
                if target <= 0.0:
                    rate = max(rate, 2.0)
                elif look[key] <= 0.004 and any(key in heavy and gone - {key} for heavy, gone in zip(self.HEAVY_SETS, going)):
                    continue                                    # waits its turn
            look[key] += (target - look[key]) * min(1.0, dt * rate)
            if key in self.FX_KEYS and target <= 0.0 and look[key] < 0.02:
                look[key] = 0.0

    # ------------------------------------------------------------------ the effects (mindstream/effects.py, fx.py)

    @staticmethod
    def particle_drive(amount, chaos, flat, beat, bpm, last_beat):
        """What the music and the look ask of the particles this frame (fx.py, STEP): the spring home, the stir of the
        field, a kick, how long they live. The amount is how far from the picture they may go: a little, and the cloud
        is the picture, shimmering; full, and it is smoke that keeps being born back into it. The chaos (the music's
        energy) stirs harder and kicks harder. Every beat kicks the cloud outward from a point of its own; the one (the
        first beat of the bar) kicks hardest and then pulls home hard for the whole beat, so the picture is seen to
        re-form on it (less of it, the further the effect is turned); on the backbeats the spring lets go for a tenth of
        a second. Resting flat, they hold the picture."""
        amount, energy = min(max(amount, 0.0), 1.0), min(max(chaos, 0.0), 2.0) / 2.0
        whole, phase = int(beat), beat % 1.0
        since = phase * 60.0 / max(bpm, 20.0)                   # seconds since the beat
        spring = 1.0 + 35.0 * (1.0 - amount) ** 2
        if whole % 4 == 0:
            spring += 60.0 * (1.0 - 0.6 * amount)               # (60 a second squared: nine tenths of the way home in half a second)
        elif whole % 2 == 1 and since < 0.1:
            spring = 0.0
        spring = max(spring, 40.0 * flat)
        curl = (0.2 + 1.0 * amount) * (0.5 + 0.5 * energy) * (1.0 - 0.85 * flat)
        kick = 0.0
        if whole != last_beat:
            kick = (0.4 + 1.2 * energy) * (0.5 + amount) * (1.6 if whole % 4 == 0 else 1.0) * (1.0 - flat)
        return {"spring": spring, "curl": curl, "kick": kick, "kx": 0.5 + 0.3 * math.sin(whole * 2.399), "ky": 0.5 + 0.25 * math.cos(whole * 1.731),
                "drag": 0.6, "life": 6.0 - 3.5 * amount}

    def draw_points(self, scene, amount, mvp, t, pulse, shape, rw, rh, live, dt=1.0 / 60.0, bpm=120.0):
        """The particles (fx.py): the cloud moved on a frame (one pass over the rows of points in use, into the other
        set of state), then drawn over the scene, each point adding its light. Up to fx.MOST_POINTS at full; half as
        many when frames are running slow, a quarter when the screen's heavy effects are being left out too."""
        (step, set_step), (made, uniforms) = self.fx["pt:step"], self.fx["points"]
        wide, high = fx.PARTICLES
        count = max(int(min(amount, 1.0) * fx.MOST_POINTS) >> self.shed["level"], wide)
        rows = min(-(-count // wide), high)
        drive = self.particle_drive(amount, self.chaos, self.flat, self.beat, bpm, self.pt_beat)
        self.pt_beat = int(self.beat)
        was, now = self.particles[self.pt_at], self.particles[self.pt_at ^ 1]
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_BLEND)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, now.fbo)
        GL.glViewport(0, 0, wide, rows)                         # only the rows in use are moved
        GL.glUseProgram(step)
        for unit, tex in zip((GL.GL_TEXTURE0, GL.GL_TEXTURE1, GL.GL_TEXTURE2, GL.GL_TEXTURE3, GL.GL_TEXTURE4), was.texs + [live[0], live[1]]):
            GL.glActiveTexture(unit)
            GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
        kx, ky = drive.pop("kx"), drive.pop("ky")               # the kick's point, on the picture's plane
        set_step(where=0, moving=1, home=2, texA=3, texB=4, blend=float(live[2]), dt=min(max(dt, 1.0 / 240.0), 0.05), t=t % 1000.0, aspect=shape,
                 kx=(kx - 0.5) * 2.0 * shape, ky=(0.5 - ky) * 2.0, born=float(self.pt_rows), seed=float(self.rendered % 65536), **drive)
        GL.glBindVertexArray(self.quad_vao)
        GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)
        self.pt_at, self.pt_rows = self.pt_at ^ 1, rows
        drawn = rows * wide
        across = (2.6 - 1.0 * min(amount, 1.0)) * rh / 1080.0                      # points across, on screen: finer as there are more
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, scene.fbo)
        GL.glViewport(0, 0, rw, rh)
        GL.glEnable(GL.GL_PROGRAM_POINT_SIZE)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)                    # light added to light: where they crowd it is brighter, past white if it must be
        GL.glUseProgram(made)
        for unit, tex in zip((GL.GL_TEXTURE0, GL.GL_TEXTURE1, GL.GL_TEXTURE2, GL.GL_TEXTURE3, GL.GL_TEXTURE4), now.texs + [live[0], live[1]]):
            GL.glActiveTexture(unit)
            GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
        uniforms(mvp=mvp, where=0, moving=1, home=2, texA=3, texB=4, blend=float(live[2]), size=across * 2.6,
                 alpha=min(1.0, 0.9 * rw * rh * 0.35 / (drawn * across * across)))       # so that many points together do not burn out
        GL.glBindVertexArray(self.points_vao)
        GL.glDrawArrays(GL.GL_POINTS, 0, drawn)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glDisable(GL.GL_BLEND)
        GL.glBindVertexArray(self.quad_vao)

    def output(self, src, fbo, w, h, tone, finish):
        """One of the last passes (fx.OUTPUT) over `src` into `fbo` (0: the screen): `tone` brings the light down to
        what the screen shows (exposure, the tone curve, the sRGB curve, with the lens, vignette and tint); `finish`
        adds grain and the dither."""
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fbo)
        GL.glViewport(0, 0, w, h)
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_BLEND)
        GL.glUseProgram(self.post)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, src)
        self.u_post(**self.out_with, tone=1.0 if tone else 0.0, finish=1.0 if finish else 0.0)
        GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)

    def fx_quad(self, target, made, tex):
        """Ready to draw over the whole of `target` with the program `made`, reading `tex`."""
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, target.fbo)
        GL.glViewport(0, 0, target.w, target.h)
        GL.glUseProgram(made)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex)

    def fx_next(self):
        """The effects draw into two targets by turns (the pair of the bench in use): each pass reads the one the last
        pass wrote."""
        self.fx_at ^= 1
        return self.bench.pair[self.fx_at]

    def shed_level(self, now, dt):
        """How much is left out because frames are running slow: 0 nothing; 1 the heavy effects on the pictures (and
        fewer pictures worked a frame); 2 the heavy effects on the screen too, all but the first. The measure is the
        time between frames, smoothed, so each picture's own effects count toward it as the screen's do. Once it has
        risen it holds for a while (four seconds; twice as long each time it rises again soon after falling, up to a
        minute) and falls only when frames are quick: a heavy effect is not switched off and on every half second,
        which is itself felt as pauses."""
        self.fx_slow = 0.9 * self.fx_slow + 0.1 * dt
        shed, was = self.shed, self.shed["level"]
        wanted = 2 if self.fx_slow > 0.07 else 1 if self.fx_slow > 0.055 else 0
        if wanted > was:
            if now - shed["fell"] < 30.0:
                shed["hold"] = min(shed["hold"] * 2.0, 60.0)
            elif now - shed["fell"] > 120.0:
                shed["hold"] = 4.0
            shed["level"], shed["until"] = wanted, now + shed["hold"]
        elif was and self.fx_slow < 0.03 and now >= shed["until"]:
            shed["level"], shed["fell"] = 0, now
        level = shed["level"]
        if level != was:
            self.hitches.note(f"shedding went from {was} to {level}")
            if level == 2:
                self.tell("Frames are running slow: the heaviest effects are left out until they are quick again.")
        self.fx_shedding = level >= 2
        return level

    def run_effects(self, src, look, t, pulse, w, h, rw, rh, dt=1.0 / 60.0, bpm=120.0):
        """The passes over the screen, in order, for the effects that are turned up (none: nothing is done and nothing
        is held). Returns the texture holding the picture with its effects, and whether its light has already been
        brought down to the screen's numbers: the effects that work on the finished picture (effects.DISPLAY) run after
        the tone curve, which is then drawn into the bench first (see output)."""
        chain = [key for key in effects.chain(look) if all(name in self.fx for name in fx.needs(key))]
        now = time.time()
        for key in [k for k, mem in self.fx_state.items() if k not in chain and now - mem["used"] > 8.0]:
            self.fx_free(key)                                   # an effect turned to nothing gives back what it held (to the pool)
        if self.fx_shedding:                                    # frames running slow (shed_level): all but the first heavy one are left out
            heavy = [key for key in chain if key in effects.HEAVY]
            chain = [key for key in chain if key not in heavy[1:]]       # the first heavy one stays: the look does not vanish
        on, off = [k for k in chain if k not in self.fx_was], [k for k in self.fx_was if k not in chain]
        if on or off:
            self.hitches.note("screen effects " + " ".join(["on: " + ", ".join(on)] * bool(on) + ["off: " + ", ".join(off)] * bool(off)))
        self.fx_was = chain
        if not chain:
            return src, False
        if self.screen_bench is None:                           # (made with the screen, in frame(); here only if it was not)
            self.screen_bench = Bench(self.pool, rw, rh, w, h)
        bar = int(self.beat // 4)
        c = SimpleNamespace(t=t % 1000.0, dt=min(max(dt, 1.0 / 240.0), 0.05), pulse=pulse, beat=self.beat % 1024.0, whole=self.beat, w=w, h=h, rw=rw, rh=rh,
                            bpm=max(float(bpm), 20.0), bar=bar, newbar=bar != self.fx_bar)
        self.fx_bar = bar
        light, shown = effects.in_light([(key, min(max(float(look[key]), 0.0), 1.0)) for key in chain])
        self.bench = self.screen_bench
        try:
            self.lin = 1.0                                      # up to the tone curve the frame is light
            if light:
                src = self.run_chain(src, light, c, self.screen_bench)
        finally:
            self.lin = 0.0
        if not shown:
            return src, False
        target = self.fx_next()                                 # the curve, into the bench: the rest work on the finished picture
        self.output(src, target.fbo, target.w, target.h, tone=True, finish=False)
        GL.glBindVertexArray(self.quad_vao)
        return self.run_chain(target.tex, shown, c, self.screen_bench), True

    def run_chain(self, src, steps, c, bench):
        """One chain of effects, [(effect, amount)] in order, run over `src` on `bench`: the screen's, or a picture's.
        Returns the texture holding the result (one of the bench's)."""
        self.bench = bench
        amounts = dict(steps)
        own = {"echo": self.fx_echo, "mosh": self.fx_mosh, "fluid": self.fx_fluid, "slit": self.fx_slit, "coral": self.fx_coral, "sort": self.fx_sort,
               "relief": self.fx_relief, "ascii": self.fx_ascii}
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_BLEND)
        GL.glBindVertexArray(self.quad_vao)
        beaten = False
        for key, amount in steps:
            if key in ("strobe", "invert", "cycle"):            # the three on the beat are one pass between them
                if not beaten:
                    src, beaten = self.fx_beat(src, amounts, c), True
            elif key == "bloom":
                src = self.bloom(src, amount, bench.w, bench.h)
            elif key == "streak":
                src = self.streak(src, amount, bench.w, bench.h)
            elif key in own:
                src = own[key](src, amount, c)
            elif key in ("fractal", "gyroid"):              # a ray walked for every point: at half size, or a frame takes seconds
                half = bench.halves[self.fx_at % 2]
                self.fx_at ^= 1
                src = self.fx_pass("pass:" + key, half, (src,), src=0, amount=amount, t=c.t, pulse=c.pulse, beat=c.beat,
                                   resx=float(c.rw) * half.w / bench.w, resy=float(c.rh) * half.h / bench.h)
            else:
                src = self.fx_pass("pass:" + key, self.fx_next(), (src,), src=0, amount=amount, t=c.t, pulse=c.pulse, beat=c.beat, resx=float(c.rw), resy=float(c.rh))
        return src

    def fx_pass(self, name, target, textures, **uniforms):
        """One pass: the program `name` drawn over the whole of `target`, reading `textures` (the first as its first
        texture, and so on; a pair ("array", texture) is a ring of frames). Returns the target's texture."""
        made, setter = self.fx[name]
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, target.fbo)
        GL.glViewport(0, 0, target.w, target.h)
        GL.glUseProgram(made)
        for unit, tex in zip((GL.GL_TEXTURE0, GL.GL_TEXTURE1, GL.GL_TEXTURE2, GL.GL_TEXTURE3), textures):
            GL.glActiveTexture(unit)
            if isinstance(tex, tuple):
                GL.glBindTexture(GL.GL_TEXTURE_2D_ARRAY, tex[1])
            else:
                GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
        self.lin_for(made, setter)
        setter(**uniforms)
        GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)
        return target.tex

    def lin_for(self, made, setter):
        """Whether the program `made` is reading light (fx.py), told it only when that has changed for it (a program
        keeps its uniforms; they start at 0, the screen's numbers)."""
        if self.lin_at.get(made, 0.0) != self.lin:
            setter(lin=self.lin)
            self.lin_at[made] = self.lin

    def fx_mem(self, key, build):
        """What an effect keeps from frame to frame, made the first time it is asked for ("fresh" until the effect
        has run once). What it is made of comes from the pool (taken cleared), so turning an effect on is not a stall."""
        mem = self.fx_state.get(key)
        if mem is None:
            mem = self.fx_state[key] = {**build(), "fresh": True}
        mem["used"] = time.time()
        return mem

    def fx_free(self, key, keep=True):
        """An effect's memory let go: back to the pool (keep), or deleted (the screen has changed size)."""
        for held in self.fx_state.pop(key, {}).values():
            for one in held if isinstance(held, (list, tuple)) else (held,):
                if keep and hasattr(one, "key"):
                    self.pool.give(one)
                elif hasattr(one, "free"):
                    one.free()

    def fx_pair(self, w, h, edge=True):
        return self.pool.pair(w, h, edge=edge)

    def fx_echo(self, src, amount, c):
        """The frame fed back into itself (the video-synth loop): the further it is turned, the less true picture is let in."""
        mem = self.fx_mem("echo", lambda: {"pair": self.fx_pair(c.rw, c.rh, edge=False), "at": 0})
        last, out = mem["pair"][mem["at"]], mem["pair"][mem["at"] ^ 1]
        mem["at"] ^= 1
        return self.fx_pass("echo", out, (src, last.tex), src=0, last=1, amount=amount, t=c.t, dt=c.dt, pulse=c.pulse, resx=float(c.rw), resy=float(c.rh))

    def fx_mosh(self, src, amount, c):
        """The picture held and dragged about by the motion of what should have replaced it. How things moved is read
        from two small soft copies of the frame, this one and the last; the whole picture is let back on a bar line
        (every bar; every fourth when turned past half)."""
        sw, sh = max(c.w // 4, 8), max(c.h // 4, 8)
        mem = self.fx_mem("mosh", lambda: {"small": self.fx_pair(sw, sh), "flow": self.pool.take(sw, sh, True, True), "pair": self.fx_pair(c.rw, c.rh), "at": 0})
        small, before = mem["small"][mem["at"]], mem["small"][mem["at"] ^ 1]
        last, out = mem["pair"][mem["at"]], mem["pair"][mem["at"] ^ 1]
        self.fx_pass("small", small, (src,), src=0, px=1.0 / sw, py=1.0 / sh)
        self.fx_pass("flow", mem["flow"], (small.tex, before.tex), now=0, before=1, px=1.0 / sw, py=1.0 / sh)
        whole = mem["fresh"] or (c.newbar and c.bar % (4 if amount >= 0.5 else 1) == 0)
        self.fx_pass("mosh", out, (src, last.tex, mem["flow"].tex), src=0, last=1, flow=2, amount=amount, t=c.t, keyframe=1.0 if whole else 0.0,
                     resx=float(c.rw), resy=float(c.rh))
        mem["at"], mem["fresh"] = mem["at"] ^ 1, False
        return out.tex

    def fx_fluid(self, src, amount, c):
        """The picture's colours carried in a flow that cannot be squeezed (after Stam's stable fluids). Each frame: the
        flow carries itself along; forces are added (a push from a point on every kick, a slow stirring, the bright
        rising, the small swirls put back); it is made to neither pile up nor thin out (forty rounds); then it carries
        the colour, and a little true picture is let back in: less, the further the effect is turned."""
        gw, gh = max(c.w // 4, 16), max(c.h // 4, 16)
        mem = self.fx_mem("fluid", lambda: {"vel": self.fx_pair(gw, gh), "press": self.fx_pair(gw, gh), "div": self.pool.take(gw, gh, True, True),
                                            "dye": self.fx_pair(c.w, c.h), "v": 0, "p": 0, "d": 0})
        px, py = 1.0 / gw, 1.0 / gh
        a, b = mem["vel"][mem["v"]], mem["vel"][mem["v"] ^ 1]
        self.fx_pass("advect", b, (a.tex, a.tex), field=0, vel=1, dt=c.dt, px=px, py=py, keep=0.985 ** (60.0 * c.dt))
        beat = int(c.beat)                                      # each kick pushes from somewhere new
        self.fx_pass("force", a, (b.tex, src), vel=0, src=1, dt=c.dt, t=c.t, pulse=c.pulse, amount=amount, cx=0.5 + 0.3 * math.sin(beat * 2.399),
                     cy=0.5 + 0.25 * math.cos(beat * 1.731), aspect=gw / gh, px=px, py=py)
        self.fx_pass("diverge", mem["div"], (a.tex,), vel=0, px=px, py=py)
        at = mem["p"]
        for _ in range(40):
            self.fx_pass("jacobi", mem["press"][at ^ 1], (mem["press"][at].tex, mem["div"].tex), press=0, div=1, px=px, py=py)
            at ^= 1
        self.fx_pass("project", b, (a.tex, mem["press"][at].tex), vel=0, press=1, px=px, py=py)
        was, out = mem["dye"][mem["d"]], mem["dye"][mem["d"] ^ 1]
        self.fx_pass("dye", out, (was.tex, b.tex, src), dye=0, vel=1, src=2, dt=c.dt, px=px, py=py, back=1.0 if mem["fresh"] else 0.25 + (0.004 - 0.25) * amount)
        mem["v"], mem["p"], mem["d"], mem["fresh"] = mem["v"] ^ 1, at, mem["d"] ^ 1, False
        return out.tex

    def fx_slit(self, src, amount, c):
        """Different places show different moments: each frame is kept (the last forty-eight, at half size), and each
        place looks back by its own delay. Which way the delay runs changes every four bars: down the frame, out from
        the middle, by the picture's own darkness, by patches."""
        mem = self.fx_mem("slit", lambda: {"ring": self.pool.ring(max(c.w // 2, 16), max(c.h // 2, 16), 48)})
        ring = mem["ring"]
        ring.aim()
        self.fx_pass("copy", ring, (src,), src=0)
        ring.head = (ring.head + 1) % ring.count
        return self.fx_pass("slit", self.fx_next(), (src, ("array", ring.tex)), src=0, ring=1, amount=amount, head=float(ring.head), count=float(ring.count),
                            mode=float((c.bar // 4) % 4), f16=max(15.0 / c.bpm / c.dt, 1.0), resx=float(c.rw), resy=float(c.rh))

    def fx_coral(self, src, amount, c):
        """Two chemicals that make pattern of themselves (Gray and Scott's), twelve steps a frame at half size, fed along
        the picture's edges and shown as a wet raised skin over it."""
        hw, hh = max(c.w // 2, 16), max(c.h // 2, 16)
        mem = self.fx_mem("coral", lambda: {"pair": self.fx_pair(hw, hh), "at": 0})
        at = mem["at"]
        for step in range(12):
            self.fx_pass("grow", mem["pair"][at ^ 1], (mem["pair"][at].tex, src), state=0, src=1, px=1.0 / hw, py=1.0 / hh, seed=0.02 if step == 0 else 0.0,
                         fresh=1.0 if mem["fresh"] and step == 0 else 0.0)
            at ^= 1
        mem["at"], mem["fresh"] = at, False
        return self.fx_pass("coral", self.fx_next(), (src, mem["pair"][at].tex), src=0, state=1, amount=amount, px=1.0 / hw, py=1.0 / hh, t=c.t)

    def fx_sort(self, src, amount, c):
        """The bright runs of the picture sorted by brightness, up and down the frame, sixteen steps of the sort a frame:
        so it is seen to melt over a second or so. A new picture is taken, and the melting starts again, on every bar."""
        mem = self.fx_mem("sort", lambda: {"pair": self.fx_pair(c.rw, c.rh), "at": 0, "turn": 0})
        at = mem["at"]
        if mem["fresh"] or c.newbar:
            self.fx_pass("latch", mem["pair"][at], (src,), src=0, amount=amount, resx=float(c.rw), resy=float(c.rh), seedn=float(c.bar % 97))
        for _ in range(16):
            self.fx_pass("sort", mem["pair"][at ^ 1], (mem["pair"][at].tex,), state=0, parity=mem["turn"] & 1)
            at, mem["turn"] = at ^ 1, mem["turn"] + 1
        mem["at"], mem["fresh"] = at, False
        return self.fx_pass("sorted", self.fx_next(), (src, mem["pair"][at].tex), src=0, state=1, amount=amount)

    def fx_relief(self, src, amount, c):
        """The picture as a raised thing: its height from its own brightness in broad shapes, seen from an eye that
        moves a little, under a lamp that circles and casts shadows. (Worked afresh each frame: its height is the
        bench's, so it runs on the screen and on each picture alike.)"""
        height = self.bench.height
        self.fx_pass("height", height, (src,), src=0, px=1.0 / height.w, py=1.0 / height.h)
        return self.fx_pass("relief", self.fx_next(), (src, height.tex), src=0, height=1, amount=amount, t=c.t, pulse=c.pulse, resx=float(c.rw), resy=float(c.rh))

    def fx_ascii(self, src, amount, c):
        return self.fx_pass("ascii", self.fx_next(), (src, self.glyph_tex), src=0, glyphs=1, amount=amount, resx=float(c.rw), resy=float(c.rh))

    def fx_beat(self, src, amounts, c):
        """Strobe, invert and colour cycling, on the beat (c.whole: the beats so far, a picture's own offset added).
        The strobe never flashes more than three times a second: above 180 to the minute it takes every second beat."""
        every = 1 if c.bpm <= 180.0 else 2
        flash = math.exp(-((c.whole / every) % 1.0) * every * 60.0 / c.bpm / 0.09)
        hit = math.exp(-(c.whole % 1.0) * 60.0 / c.bpm / 0.12)
        return self.fx_pass("beat", self.fx_next(), (src,), src=0, strobe=float(amounts.get("strobe", 0.0)), invert=float(amounts.get("invert", 0.0)),
                            cycle=float(amounts.get("cycle", 0.0)), flash=flash, hit=hit, turn=float(int(c.whole) % 64))

    def lay_over(self, src, glow, gain, tint):
        """The picture with a glow laid over it, the brightest parts rolling off instead of burning out."""
        made, uniforms = self.fx["lay"]
        target = self.fx_next()
        self.fx_quad(target, made, src)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, glow)
        self.lin_for(made, uniforms)
        uniforms(src=0, glow=1, gain=gain, tr=tint[0], tg=tint[1], tb=tint[2])
        GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)
        return target.tex

    def bloom(self, src, amount, rw, rh):
        """Bright things glow into what is around them: the bright parts are taken, halved in size six times over (each
        softer and wider than the last), built back up one on another, and laid over the picture."""
        mips = self.bench.mips
        made, uniforms = self.fx["down"]
        tex, tw, th = src, rw, rh
        for at, mip in enumerate(mips):
            self.fx_quad(mip, made, tex)
            if at == 0:
                self.lin_for(made, uniforms)
            uniforms(src=0, px=1.0 / tw, py=1.0 / th, knee=1.0 if at == 0 else 0.0)
            GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)
            tex, tw, th = mip.tex, mip.w, mip.h
        made, uniforms = self.fx["up"]
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)                    # each is added to the one above it
        for at in range(len(mips) - 2, -1, -1):
            below = mips[at + 1]
            self.fx_quad(mips[at], made, below.tex)
            uniforms(src=0, px=1.0 / below.w, py=1.0 / below.h)
            GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)
        GL.glDisable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        return self.lay_over(src, mips[0].tex, 0.55 * amount, (1.0, 1.0, 1.0))

    def streak(self, src, amount, rw, rh):
        """Bright things smear sideways, as through a cinema lens: the bright parts, made small, are spread along the
        line twice (the second time much further), and laid over the picture with a little blue in them."""
        one, two = self.bench.smears
        made, uniforms = self.fx["down"]
        self.fx_quad(one, made, src)
        self.lin_for(made, uniforms)
        uniforms(src=0, px=1.0 / rw, py=1.0 / rh, knee=1.0)
        GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)
        made, uniforms = self.fx["smear"]
        for target, tex, stretch in ((two, one.tex, 1.5), (one, two.tex, 5.0)):
            self.fx_quad(target, made, tex)
            uniforms(src=0, px=1.0 / one.w, stretch=stretch)
            GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)
        return self.lay_over(src, one.tex, 1.6 * amount, (0.7, 0.85, 1.0))

    # ------------------------------------------------------------------ each picture's own effects (the "image" target)
    #
    # Each picture drawn this frame (the one showing and the one it is turning from, or the film's frame; each picture
    # in the swarm; each thing on a side of an object) can be put through its own chain before it is drawn: turned the
    # screen's way up, run through the image target's effects on a bench of its own size, turned back, and kept in a
    # framebuffer of its own (imgfx, by the texture it came from). The drawing then uses that in place of the plain
    # texture (shown_as). Only the effects that forget are given to pictures (effects.IMAGE says why). Cost: the
    # pictures being looked at (the live ones) are worked every frame; the rest a few a frame in turn, stalest first,
    # each keeping its last result in between; at most MOST_IMAGES are kept; and all of it counts toward the slow-frame
    # measure, which sheds the pictures' heavy effects (and works fewer of them a frame) before the screen's.
    #
    # A picture's chain is worked on the picture as the screen shows it (its stored numbers, before they are turned into
    # light), not in light: a picture has no light past white to work with, every effect was tuned on those numbers,
    # and the half of them that only mean something between 0 and 1 (halftone, glyphs, the beat, glitch, the tape) can
    # then run anywhere in it, in the one order. What it makes is kept in float, so a glow on a picture may pass white;
    # the surface turns it into light as it draws it, and the screen's tone curve brings it down with the rest.

    IMAGE_SIDES = (320, 512, 768, 1024)     # the square sizes pictures are worked at: the smallest that holds the picture, at most its place's
    MOST_IMAGES = 24                        # pictures kept worked at once; more on screen than that are drawn plain
    IMAGE_TURNS = (6, 2)                    # pictures other than the live ones worked a frame: usually, and while shedding

    def image_side(self, tex, most):
        size = TEX_SIZE.get(tex)
        want = min(max(size[0], size[1]) if size else most, most)
        return next((side for side in self.IMAGE_SIDES if side >= want), self.IMAGE_SIDES[-1])

    def bench_for(self, side):
        bench = self.benches.get(side)
        if bench is None:
            bench = self.benches[side] = Bench(self.pool, side, side, side, side)
        return bench

    def let_images_go(self):
        """The image target turned to nothing a while: what the pictures held goes back to the pool."""
        for entry in self.imgfx.values():
            self.pool.give(entry["target"])
        for bench in self.benches.values():
            bench.give_back(self.pool)
        self.imgfx, self.benches = {}, {}

    def image_jobs(self, now, video):
        """What is drawn this frame that is a picture: [(texture, what it is, the most it is worked at, live)]."""
        jobs = []

        def name(image, fallback):
            number = image.info.get("shelf") if image is not None else None
            return ("shelf", number) if number is not None else fallback

        if video:
            clip = self.reel[min(self.reel_at, len(self.reel) - 1)]
            jobs.append((self.tex_video, ("shelf", clip["shelf"]) if clip.get("shelf") is not None else ("film", id(clip)), 1024, True))
        else:
            if self.blend < 0.999:                              # the picture it is turning from shows only while it turns
                jobs.append((self.tex_a, name(self.pic_a, ("tex", self.tex_a)), 1024, True))
            jobs.append((self.tex_b, name(self.pic_b, ("tex", self.tex_b)), 1024, True))
        if self.history:
            count = max(int(len(self.swarm) * self.look["swarm"]), 0)
            for at in sorted({i % len(self.history) for i in range(count)}):
                pic = self.history_pics[at] if at < len(self.history_pics) else None
                jobs.append((self.history[at], name(pic, ("tex", self.history[at])), 320, False))
        if self.solid:
            for side in self.solid["sides"]:
                for number in side:
                    got = self.side_texture(number, now)
                    if got:
                        jobs.append((got[0], ("shelf", number), 512, False))
        seen, out = set(), []
        for job in jobs:
            if job[0] not in seen:
                seen.add(job[0])
                out.append(job)
        return out

    def prepare_images(self, now, t, pulse, bpm, dt, video):
        """Each picture drawn this frame through its own effects, before anything is drawn (the passes take over the
        framebuffer, the program and the textures). Fills shown_as: texture -> what to draw in its place."""
        self.shown_as = {}
        plan = [(key, amount) for key, amount in effects.image_chain(self.look) if all(name in self.fx for name in fx.needs(key))]
        if "flip" not in self.fx:
            plan = []
        level = self.shed["level"]
        if level >= 1:                                          # the pictures' heavy effects are the first to go
            plan = [(key, amount) for key, amount in plan if key not in effects.HEAVY]
        keys = [key for key, _ in plan]
        was = [key for key, _ in self.image_plan]
        if keys != was:
            on, off = [k for k in keys if k not in was], [k for k in was if k not in keys]
            if on or off:
                self.hitches.note("picture effects " + " ".join(["on: " + ", ".join(on)] * bool(on) + ["off: " + ", ".join(off)] * bool(off)))
        self.image_plan = plan
        if not plan:
            if (self.imgfx or self.benches) and now - getattr(self, "image_used", 0.0) > 6.0:
                self.let_images_go()
            return
        self.image_used = now
        began, ran = time.perf_counter(), 0
        jobs = self.image_jobs(now, video)
        turns = self.IMAGE_TURNS[1 if level >= 1 else 0]
        others = sorted([job for job in jobs if not job[3]], key=lambda job: self.imgfx.get(job[0], {}).get("at", -1.0))
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_BLEND)
        GL.glBindVertexArray(self.quad_vao)
        for tex, name, most, live in [job for job in jobs if job[3]] + others:
            seed = effects.picture_seed(name)
            entry = self.imgfx.get(tex)
            if entry is not None and entry["seed"] != seed:     # another picture is behind this texture now: what was worked is not it
                self.pool.give(self.imgfx.pop(tex)["target"])
                entry = None
            if not live and turns <= 0:
                if entry is not None:
                    entry["used"] = now
                    self.shown_as[tex] = entry["target"].tex
                continue
            if entry is None and len(self.imgfx) >= self.MOST_IMAGES:
                spare = [key for key, kept in self.imgfx.items() if kept["used"] < now]
                if not spare:
                    continue                                    # this many on screen at once: the rest are drawn plain
                self.pool.give(self.imgfx.pop(min(spare, key=lambda key: self.imgfx[key]["used"]))["target"])
            side = self.image_side(tex, most)
            if entry is None or entry["target"].w != side:
                if entry is not None:
                    self.pool.give(entry["target"])
                entry = self.imgfx[tex] = {"target": self.pool.take(side, side, True, False), "seed": seed, "at": -1.0, "used": now}
            self.image_pass(tex, entry, effects.for_picture(plan, seed, getattr(self, "image_varied", True)), seed, now, t, pulse, bpm, dt)
            self.shown_as[tex] = entry["target"].tex
            ran += 1
            if not live:
                turns -= 1
        for key in [key for key, kept in self.imgfx.items() if now - kept["used"] > 3.0]:
            self.pool.give(self.imgfx.pop(key)["target"])      # no longer drawn: back to the pool
        self.hitches.note(f"effects on {ran} of {len(jobs)} pictures", time.perf_counter() - began)

    def image_pass(self, tex, entry, steps, seed, now, t, pulse, bpm, dt):
        """One picture through its own chain, into its own framebuffer. Its clock and its beat are its own (offset by
        its seed, whole beats so it stays on the beat), and its effects are worked as if it were a screen of its own
        shape: `rw` and `rh` are its width and height in points of the bench."""
        target = entry["target"]
        side = target.w
        bench = self.bench_for(side)
        size = TEX_SIZE.get(tex)
        aspect = size[0] / size[1] if size and size[1] else 1.0
        rw, rh = (side, side / aspect) if aspect >= 1.0 else (side * aspect, side)
        toff, boff = effects.time_offset(seed)
        c = SimpleNamespace(t=(t + toff) % 1000.0, dt=min(max(dt, 1.0 / 240.0), 0.05), pulse=pulse, beat=(self.beat + boff) % 1024.0, whole=self.beat + boff,
                            w=side, h=side, rw=rw, rh=rh, bpm=max(float(bpm), 20.0), bar=int(self.beat // 4), newbar=False)
        self.bench = bench
        src = self.fx_pass("flip", self.fx_next(), (tex,), src=0)           # the screen's way up
        src = self.run_chain(src, steps, c, bench) if steps else src
        self.fx_pass("flip", target, (src,), src=0)                         # and back, into its own
        entry["at"], entry["used"], entry["seed"] = now, now, seed

    def report_watching(self, force=None):
        """Nothing is made unless someone is looking. Minimising the window is "not looking": the launcher is
        told, and holds the story, the pictures and the films until the window is back. The sound stops too."""
        watched = not glfw.get_window_attrib(self.win, glfw.ICONIFIED) if force is None else force
        if watched != getattr(self, "watched", True):
            self.watched = watched
            if self.mixer:
                self.mixer.mute = self.mute or not watched
            self.to_launcher({"watched": watched})

    def run(self):
        self.close_at = None
        started = time.time()
        while not glfw.window_should_close(self.win):
            began = time.perf_counter()
            if self.loop_at is not None and getattr(self, "watched", True):     # the whole of the last frame, the wait for the screen included
                self.hitches.frame(began - self.loop_at, getattr(self, "frame_cpu", None))
                said = self.hitches.report(time.time())
                if said:
                    self.trace(said)
                    self.tell(said)
            self.loop_at = began
            self.frame()
            self.frame_cpu = time.perf_counter() - began
            if self.grab_for:                                   # something was memorised in this frame: its small picture
                began = time.perf_counter()
                self.send_thumbs()                              # (a read back from the card: it waits for the frame. Only on a memorise.)
                self.hitches.note("the screen read back for a memory's picture", time.perf_counter() - began)
            glfw.swap_buffers(self.win)
            glfw.poll_events()
            if self.close_at and time.time() > self.close_at:
                break
        winsound.PlaySound(None, winsound.SND_PURGE)
        if self.mixer:
            self.mixer.close()
        self.trace(f"{self.rendered} frames in {time.time() - started:.1f}s "
                   f"({self.rendered / max(time.time() - started, 0.001):.0f} per second)")
        glfw.terminate()


def main():
    ap = argparse.ArgumentParser(description="Show a mindstream as moving, GPU-rendered visuals (nothing saved)")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=800)
    ap.add_argument("--fullscreen", action="store_true")
    ap.add_argument("--bpm", type=float, default=120.0, help="tempo of the pulse")
    ap.add_argument("--chaos", type=float, default=1.0, help="0 = gentle, 1 = a lot, 2 = too much (Up/Down change it live)")
    ap.add_argument("--calm", type=float, default=3.5, help="seconds each cycle spends opened out flat, so the picture can be seen")
    ap.add_argument("--wild", type=float, default=9.0, help="seconds each cycle spends in motion")
    ap.add_argument("--facets", type=int, default=40, help="grid size of the surface: lower = bigger facets")
    ap.add_argument("--shards", type=int, default=28, help="how many pieces of earlier pictures orbit")
    ap.add_argument("--text-size", type=int, default=20, help="caption font size")
    ap.add_argument("--no-overlay", action="store_true", help="start without the caption and flow strip (M toggles)")
    ap.add_argument("--mute", action="store_true", help="start with video sound off (A toggles)")
    ap.add_argument("--report-watching", action="store_true", help=argparse.SUPPRESS)   # set by the launcher
    ap.add_argument("--hush", action="store_true", help=argparse.SUPPRESS)              # set by the launcher: nothing on the terminal
    ap.add_argument("--thelmic", action="store_true",
                    help="with --groove: let thelmic's engine write the parts sixteen bars at a time, instead of the archetype "
                         "patterns that can be played with live")
    ap.add_argument("--no-thelmic", action="store_true", help=argparse.SUPPRESS)       # the default now; kept so old commands still run
    ap.add_argument("--groove", action="store_true",
                    help="play a synthesised rhythm section from the start and the video's sound over it as a clip "
                         "(G toggles the rhythm section, C the chopping)")
    ap.add_argument("--flow-span", type=float, default=240.0, help="seconds of history in the flow strip")
    ap.add_argument("--exit-on-eof", action="store_true", help="close when the stream ends (default: keep moving)")
    ap.add_argument("--linger", type=float, default=5.0)
    ap.add_argument("--trace", action="store_true")
    args, _ = ap.parse_known_args()   # options meant for the plain viewer are ignored here
    if sys.stdin.isatty():
        sys.exit("gl-view reads a stream from stdin; use mindstream or img-gen --view")
    View(args).run()


if __name__ == "__main__":
    main()
