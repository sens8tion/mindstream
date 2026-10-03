"""Pulls a sample to play with: from the local Splice library by file name, or from free archives (the BBC
sound effects archive, Freesound, the Internet Archive, NASA) through thelmic's source adapters. What it finds is
fetched into memory, decoded there and handed on; nothing is written to disk.

    sample_pull.py serve                 one JSON request per line in: {"query": "rain on a tin roof", "role": "texture", "where": "any"}
                                         one JSON line out: a "sample" frame with the audio, or a "read" note saying why not
    sample_pull.py try "amen break" --role loop --where splice        find one and describe it (plays nothing)

role: kick, snare, hats (one hit), tune (something tonal to play the riff on), loop, texture.
where: any, splice, bbc, freesound, internet_archive, nasa.

A search of an outside archive sends the query to that service. Freesound needs FREESOUND_API_KEY in the
environment (run under opsec); the others need nothing. Licences differ and are reported with each sample:
the BBC's is for personal use only.
"""
import argparse
import base64
import io
import json
import os
import random
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
THELMIC = os.environ.get("MINDSTREAM_THELMIC", os.path.join(os.path.dirname(HERE), "thelmic"))
SPLICE = [p for p in (os.environ.get("MINDSTREAM_SPLICE"), os.path.expanduser(r"~\Documents\Splice\Samples"), os.path.expanduser(r"~\Splice"))
          if p and os.path.isdir(p)]
AGENT = {"User-Agent": "Mozilla/5.0 (compatible; mindstream/1.0)"}
MOST_BYTES = 20 * 1024 * 1024
RATE = 44100
LENGTH = {"kick": 0.6, "snare": 0.6, "hats": 0.4, "tune": 4.0, "loop": 12.0, "texture": 12.0}      # seconds kept of what is found

_library = None


def library():
    """Every audio file in the local Splice folders (found once, then remembered): (path, lower-case path)."""
    global _library
    if _library is None:
        _library = []
        for root in SPLICE:
            for folder, _, names in os.walk(root):
                for name in names:
                    if name.lower().endswith((".wav", ".aif", ".aiff", ".flac", ".mp3", ".ogg")):
                        path = os.path.join(folder, name)
                        _library.append((path, path[len(root):].lower().replace("\\\\", " ").replace("_", " ").replace("-", " ")))
    return _library


def from_splice(query, role):
    words = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 1]
    hint = {"kick": "kick", "snare": "snare", "hats": "hat", "loop": "loop"}.get(role)
    scored = []
    for path, low in library():
        hits = sum(1 for w in words if w in low)
        if hits and (hits == len(words) or len(words) > 2 and hits >= len(words) - 1):
            scored.append((hits + (0.5 if hint and hint in low else 0) - (0.5 if role in ("kick", "snare", "hats") and "loop" in low else 0), path))
    if not scored:
        return None
    best = max(s for s, _ in scored)
    path = random.choice([p for s, p in scored if s >= best - 0.01])
    return {"name": os.path.splitext(os.path.basename(path))[0], "source": "your Splice library", "licence": "Splice (yours)", "path": path}


def get(url, most=MOST_BYTES, headers=None):
    with urllib.request.urlopen(urllib.request.Request(url, headers={**AGENT, **(headers or {})}), timeout=30) as r:
        data = r.read(most + 1)
    if len(data) > most:
        raise ValueError("too big")
    return data


def from_archives(query, role, where):
    """The first usable hit from the free archives, as {"name", "source", "licence", "bytes"}."""
    if THELMIC not in sys.path:
        sys.path.insert(0, THELMIC)
    import warnings
    warnings.simplefilter("ignore")
    from thelmic.sources import bbc, freesound, internet_archive, nasa
    short = role in ("kick", "snare", "hats")
    order = [("bbc", bbc), ("freesound", freesound), ("internet_archive", internet_archive), ("nasa", nasa)]
    if short or role in ("tune", "loop"):
        order = [order[1], order[2], order[0], order[3]]               # musical material: the sound-effects archive last
    for name, adapter in order:
        if where not in ("any", "free", name) or not adapter.available():
            continue
        try:
            hits = adapter.search(query, limit=8)
        except Exception:
            continue
        hits = [h for h in hits if not h.duration or h.duration <= (15 if short else 240)]
        hits.sort(key=lambda h: (h.duration or 30) if short else abs((h.duration or 30) - 12))
        for hit in hits[:4]:
            try:
                url = hit.download_url or (hit.extra or {}).get("preview_url")
                if name == "freesound":
                    url = (hit.extra or {}).get("preview_url") or url          # the preview needs no login
                if name == "internet_archive":
                    meta = json.loads(get(f"https://archive.org/metadata/{hit.id}", 2 * 1024 * 1024))
                    pick = internet_archive._pick_audio_file({"files": [f for f in meta.get("files", [])
                                                                        if int(f.get("size") or 0) <= MOST_BYTES]})
                    url = f"https://{meta.get('d1') or meta.get('server')}{meta.get('dir')}/{urllib.request.quote(pick[0])}" if pick else None
                if name == "nasa":
                    listed = json.loads(get(f"https://images-api.nasa.gov/asset/{urllib.request.quote(hit.id)}", 1024 * 1024))
                    links = [i.get("href", "") for i in listed.get("collection", {}).get("items", [])]
                    url = next((u for u in links if u.lower().endswith((".mp3", ".wav", ".m4a"))), None)
                    url = url.replace("http://", "https://").replace(" ", "%20") if url else None
                if not url:
                    continue
                return {"name": str(hit.title)[:80], "source": {"bbc": "the BBC sound effects archive", "freesound": "Freesound",
                                                                 "internet_archive": "the Internet Archive", "nasa": "NASA"}[name],
                        "licence": str(hit.license or "not stated")[:80], "bytes": get(url)}
            except Exception:
                continue
    return None


def pull(query, role="texture", where="any", layer=""):
    """Find, fetch and decode one sample. Returns a "sample" frame, or a "read" frame saying why there is none."""
    import numpy as np
    import soundfile as sf
    from mindstream.samples import to_rate, trim
    role = role if role in LENGTH else "texture"
    found = from_splice(query, role) if where in ("any", "splice") else None
    if found is None and where != "splice":
        found = from_archives(query, role, where)
    if found is None:
        places = "your Splice library" if where == "splice" else "your Splice library or the free archives"
        return {"type": "read", "stream": "sound", "text": f'Nothing found for "{query}" in {places}. Try other words.'}
    try:
        data, rate = sf.read(found.get("path") or io.BytesIO(found["bytes"]), dtype="float32", always_2d=True,
                             frames=int(60 * 48000))
    except Exception as e:
        return {"type": "read", "stream": "sound", "text": f'Found "{found["name"]}" for "{query}" but could not read it ({type(e).__name__}).'}
    audio = trim(to_rate(data, rate, RATE), RATE, LENGTH[role])
    if len(audio) < RATE // 50:
        return {"type": "read", "stream": "sound", "text": f'Found "{found["name"]}" for "{query}" but it is silent.'}
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()
    return {"type": "sample", "query": query, "role": role, "name": found["name"], "layer": layer, "source": found["source"], "licence": found["licence"],
            "seconds": round(len(audio) / RATE, 2), "audio": {"rate": RATE, "channels": 2, "data": base64.b64encode(pcm).decode("ascii")}}


def main():
    ap = argparse.ArgumentParser(description="Pull a sample from the local Splice library or the free archives (nothing saved)")
    ap.add_argument("mode", choices=["serve", "try"])
    ap.add_argument("query", nargs="*")
    ap.add_argument("--role", default="texture")
    ap.add_argument("--where", default="any")
    args = ap.parse_args()
    if args.mode == "try":
        got = pull(" ".join(args.query), args.role, args.where)
        got.pop("audio", None)
        print(json.dumps(got, indent=1))
        return
    for raw in sys.stdin:
        try:
            ask = json.loads(raw)
            got = pull(str(ask.get("query", ""))[:80], str(ask.get("role", "texture")), str(ask.get("where", "any")), str(ask.get("name", ""))[:16])
        except Exception as e:
            got = {"type": "read", "stream": "sound", "text": f"The sample pull failed ({type(e).__name__})."}
        sys.stdout.write(json.dumps(got) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
