"""Try the story feed's prompt making with no model, no network and no GPU. A stand-in for llama answers
from a script of canned replies (good ones, and malformed, partial and empty ones), the real story feed is
run against it with a piped guide, and what it emits is checked. Nothing is written to disk.

    python -B demo/try_prompts.py             run every check
    python -B demo/try_prompts.py --show      also print one assembled picture prompt and one film prompt,
                                              and how many words llama had to write in each mode
    python -B demo/try_prompts.py --against <folder>      also check that, with written prompts, this feed emits
                                              the same story, prompts and score as the feed in another checkout

The canned text is a harmless made-up story about a trawler.
"""
import io
import json
import os
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

BEATS = [
    "Dawn comes up grey over the harbour and Maggie is already on deck, hauling the wet net over the rail with both fists while "
    "the dog watches the gulls. The trawler rocks. Rust flakes off the winch like old paint, and the first cold light slides "
    "along the water toward her boots.",
    "She gets the net aboard and it is full of nowt but weed and one bent pram wheel. The dog sniffs it and sneezes. Maggie "
    "laughs, a short bark of a laugh, and kicks the wheel across the planks toward the wheelhouse door.",
    "By noon they are tied up at the fish market, where Tam is stacking empty crates under the tin roof. He looks at the pram "
    "wheel, then at his mam, and says nothing at all. Rain drums on the roof and runs off the gutters in ropes.",
]
DIRECTOR = "slower, sad, cold-light\nwhy: A grey dawn and hard work, so the music holds back."
WRITTEN_PICTURE = (
    "A broad woman in her sixties with a weather-cut face and cropped white hair, wearing a yellow oilskin slick with spray, "
    "hauls a heavy wet fishing net over the rail of a rusted trawler, both fists clenched white on the rope, her eyes fixed on "
    "the dark water below. Beside her a grey three-legged lurcher with a wet wiry coat and one torn ear watches gulls on the "
    "wheelhouse roof. The deck is slick, the winch flaking rust, coils of orange rope in the foreground and the harbour wall "
    "faint in the mist behind. Medium shot at eye level, the woman just left of centre, the dog lower right, background soft. "
    "Low cold dawn sun comes from the left through sea mist, pale and diffuse, picking out the wet oilskin. A realistic 35mm "
    "photograph with fine grain and natural colour. Salt grey and rust, a tired, stubborn mood.")
WRITTEN_FILM = (
    "integrated_multimodal_description: On the deck of a rusted trawler at dawn a woman drags a net aboard as a dog watches. "
    "[Shot 1] The camera is carried along the rail as the net comes over and the grey water tips up to fill the frame. (S1), a "
    "woman in her sixties, on screen, low gravelly voice, slow, Hull accent, shouts <d>en Haul, you beast!</d>\n"
    "overall_soundscape: A winch chain grinding, wet rope slapping the deck, gulls.\n"
    "non_diegetic_music: A slow heavy piece at 120 BPM, low drums and a deep bass, sorrowful, the same piece continuing.")
CARDS = [
    "who: Maggie; the dog\n"
    "does: Maggie hauls a wet net over the rail, both fists white on the rope, eyes on the water.\n"
    "where: on the deck of a rusted trawler at dawn, drizzle falling, gulls on the wheelhouse roof\n"
    "light: low cold sun from the left, through sea mist\n"
    "mood: salt grey, rust, tired\n"
    "new: Maggie | a woman in her sixties, a trawler skipper | broad, weather-cut face, cropped white hair, yellow oilskin | "
    "low gravelly voice, slow, Hull accent\n"
    "new: the dog | a grey three-legged lurcher | wet wiry coat, one torn ear |",
    "who: Maggie; the dog\n"
    "does: Maggie kicks a bent pram wheel across the planks, laughing, while the dog sneezes at a heap of weed.\n"
    "where: same\n"
    "light: same\n"
    "mood: grey, daft, bright for a moment",
    "who: Tam; Maggie\n"
    "does: Tam stops with a crate in his arms and stares at the pram wheel Maggie holds out.\n"
    "where: under the tin roof of a fish market at noon, rain running off the gutters in ropes, stacks of empty crates\n"
    "light: flat grey daylight from the open side, wet floor shining\n"
    "mood: wet slate, fish-box blue, wary\n"
    "new: Tam | a lad of nineteen, a market porter | lanky, red ears, shaved head, blue overalls | flat quick voice, Hull accent",
]
FILM_CARDS = [
    "moves: The camera is carried along the rail as Maggie drags the net aboard and the grey water tips up to fill the frame.\n"
    "voice: Maggie\n"
    "shouts: Nowt but weed!\n"
    "sound: A winch chain grinding, wet rope slapping the deck, gulls.",
    "moves: The camera follows the pram wheel as it rolls off the deck, across the quay and under the tin roof to Tam's boots.\n"
    "voice: Maggie\n"
    "says: Look what I caught\n"
    "sound: Rain drumming on tin, crates knocking together, a wheel rattling over stone.",
]
# What a model can get wrong. Each of these must still give a prompt, with nothing asked again.
BAD_CARDS = [
    "",                                                                                    # nothing at all
    "Sure! Here is the card:\n- **Who:** Maggie, the dog and Tam\n- **Action:** Maggie holds up the wheel.",     # chatty, bold, other labels
    "who: Maggie does: Maggie counts coins on a crate. where: same light: one bare bulb overhead mood: brown, tight",   # all on one line
    '{"who": "Old Bert", "does": "Old Bert lights his pipe by the door.", "where": "in the doorway of the ice house", '
    '"new": ["Old Bert, a man in his seventies, an ice house keeper, stooped, flat cap, voice like gravel, slow"]}',       # JSON, and a person run together
]
BAD_FILM_CARDS = [
    "",                                                                                    # nothing: code makes the whole film
    "voice: Tam\nsays: <d>en I never said a word about that wheel to anybody at all</d>",   # tags, too long, no camera, no sound
    "moves: The camera rises.\nsings: Heave away\nhow: sings, a slow rolling tune\nsound: Rain.",    # a line with no speaker
    "moves: The camera turns.\nvoice: the harbourmaster, off screen\nsays: Tide's turning",          # someone never described
]
SCRIPTS = {
    "written": {"story": BEATS, "director": [DIRECTOR], "image": [WRITTEN_PICTURE], "video": [WRITTEN_FILM]},
    "structured": {"story": BEATS, "director": [DIRECTOR], "card": CARDS, "film": FILM_CARDS},
    "malformed": {"story": BEATS + BEATS[:2], "director": ["nonsense"], "card": BAD_CARDS, "film": BAD_FILM_CARDS},
    "inline": {"story": [b + "\n\n" + c for b, c in zip(BEATS, CARDS)], "director": [DIRECTOR], "film": FILM_CARDS},
    # the card missing, then the card with no beat (which counts as an empty reply), then the card first
    "inline-loose": {"story": [BEATS[0], CARDS[1], BEATS[1] + "\n" + CARDS[1], CARDS[2] + "\n\n" + BEATS[2]],
                     "director": [DIRECTOR], "card": CARDS[:1], "film": FILM_CARDS},
}
KINDS = (("# Story writer", "story"), ("You score a live show", "director"), ("You are given one beat of a story, the Cast", "card"),
         ("# Film card", "film"), ("# Image prompt writer", "image"), ("# Journey writer", "video"))


def emitted(kind, **match):
    """A test of what the feed has emitted so far: has a frame of this type, with these values, gone out?"""
    return lambda frames: any(f.get("type") == kind and all(f.get(k) == v for k, v in match.items()) for f in frames)


# llama away, busy or failing. "absent": the stand-in cannot be connected to until this has been emitted. "hold":
# the nth call of a kind does not return until this has been emitted (llama in the middle of a long reply).
# "fail": calls of a kind, from the nth on, raise an error until this has been emitted (None: that call only).
TROUBLE = {
    "mid-call": {"hold": {("story", 1): emitted("prompt", target="video")}},
    "absent": {"absent": emitted("prompt", target="video")},
    "down": {"fail": {"story": (1, emitted("story", text="the ice cracks"))}},
    "card-fails": {"fail": {"card": (0, None)}},
    # beat 2 waits until beat 1 has been memorised, and beat 3 until the story has been recalled
    "kept": {"hold": {("story", 1): lambda frames: any("memorised as 2" in f.get("text", "") for f in frames),
                      ("story", 2): emitted("control", recalled=2)}},
}
for _name, _base in (("mid-call", "written"), ("absent", "written"), ("down", "structured"), ("card-fails", "structured"), ("kept", "written")):
    SCRIPTS[_name] = SCRIPTS[_base]


def stand_in(script, trouble, frames, error):
    """A class to put in place of story_feed.Ollama: no tunnel, no network, replies from the script in order."""
    calls, turn, tries, refused = [], {}, {}, [0]

    class Reply(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    class Fake:
        last = {}

        def __init__(self, host="llama", log=None):
            if "absent" in trouble and not trouble["absent"](frames):
                refused[0] += 1
                raise error("stand-in: no route to llama")

        def request(self, path, body=None, method=None, timeout=600):
            return Reply(b'{"models": []}')

        def capabilities(self, model):
            return set()

        def chat(self, model, messages, think=None, options=None, on_text=None):
            system = messages[0]["content"]
            kind = next((name for mark, name in KINDS if system.startswith(mark) or mark in system[:400]), "unknown")
            attempt = tries.get(kind, 0)
            tries[kind] = attempt + 1
            first, until = trouble.get("fail", {}).get(kind, (None, None))
            if first is not None and (attempt == first if until is None else attempt >= first and not until(frames)):
                raise error("stand-in: llama stopped answering")
            held = trouble.get("hold", {}).get((kind, turn.get(kind, 0)))
            waited = time.time()
            while held and not held(frames) and time.time() - waited < 20:
                time.sleep(0.05)
            replies = script.get(kind, [""])
            reply = replies[min(turn.get(kind, 0), len(replies) - 1)]
            turn[kind] = turn.get(kind, 0) + 1
            calls.append({"kind": kind, "reply": reply, "asked": messages[-1]["content"], "system": len(system.split()),
                          "first": messages[1]["content"], "refused": refused[0],
                          "seen": [m["content"] for m in messages[1:-1] if m["role"] == "assistant"]})
            if on_text and reply:
                on_text(reply)
            return reply.strip()

        def clear(self, what="all"):       # the real one empties the remote host's memory and log
            return True

        def close(self, keep_loaded=False, restart=True):
            sys.stderr.write("CALLS " + json.dumps(calls) + "\n")
            sys.stderr.flush()
    return Fake


def child(root, name, extra):
    """The real story feed, with the stand-in in place of llama. It ends the process itself when the beats are done."""
    sys.path.insert(0, root)
    import story_feed
    frames, emit = [], story_feed.emit

    def watched_emit(obj):                 # the stand-in's troubles end when the feed has emitted a certain thing
        emit(obj)
        frames.append(obj)
    story_feed.emit = watched_emit
    story_feed.RETRY_SECONDS = 0.2         # the feed tries llama again every 20 s; a check cannot wait that long
    story_feed.Ollama = stand_in(SCRIPTS[name], TROUBLE.get(name, {}), frames, story_feed.ApiError)
    prompts = os.path.join(root, "prompts")
    sys.argv = ["story_feed.py", "--model", "stand-in", "--no-steer-model", "--no-restart", "--interval", "0", "--video",
                "--video-seconds", "3", "--image-md", os.path.join(prompts, "image.md"), "--video-md", os.path.join(prompts, "video.md"),
                *extra]
    story_feed.main()


def run(name, *extra, root=ROOT, typed=()):
    """Run the feed on a script; returns (what it emitted, the calls llama was asked to answer). The guide is typed
    first. `typed` is what is typed after it, in order: (something to wait for in what the feed emits, the line)."""
    feed = subprocess.Popen([sys.executable, "-B", os.path.abspath(__file__), "--child", root, name, *extra],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    errors, typed = [], list(typed)
    reading = threading.Thread(target=lambda: errors.append(feed.stderr.read()), daemon=True)
    reading.start()
    killer = threading.Timer(120, feed.kill)
    killer.start()
    feed.stdin.write(b"a trawler, a dog, a wet morning\n")
    feed.stdin.flush()
    out = []
    if not typed:
        feed.stdin.close()
    for raw in feed.stdout:
        if raw.strip():
            out.append(json.loads(raw))
        while typed and typed[0][0] in raw.decode("ascii", "replace"):
            feed.stdin.write(typed.pop(0)[1].encode() + b"\n")
            feed.stdin.flush()
            if not typed:
                feed.stdin.close()
            raw = b""
    feed.wait()
    killer.cancel()
    reading.join(5)
    said = (errors[0] if errors else b"").decode("utf-8", "replace")
    calls = [json.loads(line[6:]) for line in said.splitlines() if line.startswith("CALLS ")]
    if not calls or typed:
        sys.exit(f"the feed did not finish on '{name}'" + (f" (never saw {typed[0][0]!r})" if typed else "") + f":\n{said[-2000:]}")
    return out, calls[0]


FAILED = []


def check(what, ok, detail=""):
    print(("  ok    " if ok else "  FAIL  ") + what + (f"   [{detail}]" if detail and not ok else ""))
    if not ok:
        FAILED.append(what)


def prompts_of(out, target):
    return [o["prompt"] for o in out if o.get("type") == "prompt" and o.get("target") == target and o.get("seq", 0) >= 1]


def story_of(out):
    return [o["text"] for o in out if o.get("type") == "story" and o.get("seq", 0) >= 1]


def written(calls, kinds):
    return {k: [len(c["reply"].split()) for c in calls if c["kind"] == k] for k in kinds}


def units():
    from mindstream.prompts import CARD, FILM, Cast, Notebook, music_line, read_slots, split_beat, split_names
    print("reading what llama returns")
    plain = read_slots(CARDS[0], CARD)
    check("a well-formed card gives every slot", all(plain.get(k) for k in ("who", "does", "where", "light", "mood")) and len(plain["new"]) == 2)
    check("bullets, bold and other spellings are read", read_slots(BAD_CARDS[1], CARD).get("does") == "Maggie holds up the wheel.")
    one = read_slots(BAD_CARDS[2], CARD)
    check("a card run together on one line is read", one.get("who") == "Maggie" and one.get("light") == "one bare bulb overhead", str(one))
    check("a JSON reply is read", read_slots(BAD_CARDS[3], CARD).get("who") == "Old Bert")
    check("an empty reply gives no slots", read_slots("", CARD) == {} and read_slots("I cannot help with that.", CARD) == {})
    check("a fenced reply is read", read_slots("```\nwho: Tam\ndoes: Tam waits.\n```", CARD).get("does") == "Tam waits.")
    check("a continued line joins the slot above", read_slots("does: Tam waits\nby the door.\nwhere: same", CARD)["does"] == "Tam waits by the door.")
    check("'sings:' gives the words and the manner", read_slots("sings: Heave away", FILM) == {"says": "Heave away", "verb": "sings"})
    check("names split on ; , and", split_names("Maggie; the dog and Tam (her son)") == ["Maggie", "the dog", "Tam"]
          and split_names("nobody") == [])
    beat, card = split_beat(BEATS[0] + "\n\n" + CARDS[0])
    check("a beat with its card splits in two", beat == BEATS[0] and card == CARDS[0])
    check("a beat alone has no card", split_beat(BEATS[0]) == (BEATS[0], ""))
    check("a card alone has no beat", split_beat(CARDS[0])[0] == "")
    check("a card before its beat still splits", split_beat(CARDS[1] + "\n\n" + BEATS[1]) == (BEATS[1], CARDS[1]))
    run_on = split_beat(BEATS[1] + " " + CARDS[1].replace("\n", " "))
    check("a card run on from the beat with no line breaks still splits", run_on[0] == BEATS[1] and read_slots(run_on[1], CARD).get("light") == "same")
    check("a 'Card:' heading is not part of the beat", split_beat(BEATS[0] + "\n\nCard:\n" + CARDS[0])[0] == BEATS[0])

    print("the cast")
    cast = Cast()
    maggie = cast.learn("Maggie | a woman in her sixties, a trawler skipper | broad face, yellow oilskin | low gravelly voice, slow", BEATS[0], 1)
    check("four parts are kept as written", (maggie["kind"], maggie["look"], maggie["voice"]) ==
          ("a woman in her sixties, a trawler skipper", "broad face, yellow oilskin", "low gravelly voice, slow"))
    cast.learn("Maggie | a girl of ten | red coat | high voice", BEATS[0], 2)
    check("someone described keeps their first description", maggie["kind"].startswith("a woman") and maggie["look"] == "broad face, yellow oilskin")
    check("names are found loosely", cast.find("maggie") is maggie and cast.find("Maggie Rudd") is maggie and cast.find("Tam") is None)
    bert = cast.learn("Old Bert, a man in his seventies, an ice house keeper, stooped, flat cap, voice like gravel, slow")
    check("a person run together with commas is sorted out", bert["name"] == "Old Bert" and bert["kind"] == "a man in his seventies"
          and "flat cap" in bert["look"] and bert["voice"] == "voice like gravel, slow", str(bert))
    ann = cast.learn("Ann: a woman of thirty; voice: soft and quick, Leeds accent; tall, black coat")
    check("labelled parts out of order are sorted out", ann["kind"] == "a woman of thirty" and ann["look"] == "tall, black coat"
          and ann["voice"] == "soft and quick voice, Leeds accent", str(ann))
    stub = cast.meet("the harbourmaster", "He leans on the rail and his pipe glows.", 3)
    check("someone never described still gets an age, a gender and a voice",
          cast.identity(stub) == "a person, adult, male" and cast.voice(stub) in __import__("mindstream.prompts").prompts.SPARE_VOICES)
    cast.learn("the harbourmaster | a man of fifty, a harbourmaster | grey beard, peaked cap | booming voice", "", 4)
    check("and is filled in when llama describes them later", stub["kind"] == "a man of fifty, a harbourmaster" and stub["voice"] == "booming voice")

    print("the music line")
    from mindstream.score import ARCHETYPE_NAMES, STYLE_NAMES
    for style in STYLE_NAMES + ARCHETYPE_NAMES:
        line = music_line({"style": style, "key": "F# phrygian", "sub": 1.0, "twinkle": 0.8, "chaos": 1.6}, 137.4)
        if "at 137 BPM" not in line or "F# phrygian, dark and menacing" not in line or "sub bass" not in line:
            check(f"music line for {style}", False, line)
    check("every style and archetype has a music line with the tempo, key, bass and bells", True)
    spare = music_line({"style": "none", "key": "C major", "sub": 0.0, "twinkle": 0.0, "chaos": 0.3}, 90)
    check("a bare score gives a bare line", "bell" not in spare and "sub" not in spare and "Stripped back" in spare, spare)
    check("the same score gives the same words", music_line({"style": "dnb", "key": "A minor"}, 172) == music_line({"style": "dnb", "key": "A minor"}, 172.2))

    print("with nothing from llama at all")
    book = Notebook()
    book.take_card(1, "", BEATS[0])
    picture = book.picture(1, BEATS[0], {"key": "A minor"})
    score = {"style": "four", "key": "A minor", "bpm": 120}
    film, filled = book.film(2, "", BEATS[0], BEATS[1], score, 120, 4)
    spoken, _ = book.film(2, "", BEATS[0], BEATS[1], score, 120, 4, line="mind the wheel")
    asked = book.card_request(BEATS[1], ["make it night"])
    check("a steer is passed on with the request for a card", asked.startswith("Cast: nobody yet\n") and "Steer: make it night\nBeat: She gets" in asked, asked)
    check("the picture prompt is the beat's own words, framed and lit by code", picture.startswith(BEATS[0][:60]) and "35mm" in picture, picture)
    check("the film has the beat's own words, a camera move, sound and music, and nobody speaks",
          film.startswith("integrated_multimodal_description: " + BEATS[1][:40]) and "[Shot 1] The camera" in film and "at 120 BPM" in film
          and "<d>" not in film and set(filled) >= {"nobody speaks", "camera", "sound"}, film)
    check("a short line the viewer typed is spoken by a voice off screen", "says in an off-screen voiceover <d>en mind the wheel</d>" in spoken, spoken)
    guide = "a trawler, a dog, a wet morning"
    book = Notebook()
    book.take_card(0, "", guide)
    first = book.picture(0, guide, {"key": "A minor"}, guide=guide)
    check("the guide alone makes a whole picture prompt", first == "A trawler, a dog, a wet morning. Wide shot from a low angle, the horizon in the "
          "upper third, everything sharp from foreground to distance. A realistic 35mm photograph, natural colour, fine film grain.", first)
    check("a guide that names its own medium is not also called a photograph",
          "photograph" not in Notebook().picture(0, "a fox on the ice, as a woodcut", {}, guide="a fox on the ice, as a woodcut")
          and "photograph" not in Notebook().picture(0, "an oil painting of a fox", {}) and "photograph" in Notebook().picture(0, BEATS[0], {}))
    book.take_card(1, "", "a fox crosses the ice")
    book.take_card(2, "", "it stops and listens")
    second = book.picture(2, "it stops and listens", {}, guide=guide, before="a fox crosses the ice")
    check("a typed beat leads its picture, then the beat before, then the guide",
          second.startswith("It stops and listens. A fox crosses the ice. A trawler, a dog, a wet morning. Wide shot"), second)
    check("something just typed leads a prompt llama wrote, which is otherwise left alone",
          book.picture(2, "x", {}, lead="the gulls scatter", written=WRITTEN_PICTURE) == "The gulls scatter. " + WRITTEN_PICTURE)


def feeds(show, against=""):
    import story_feed
    from mindstream.prompts import CARD, read_slots

    def sound(out):
        """What the feed's own strict check finds wrong with each film prompt (a line may run one word over, as mending allows)."""
        return [story_feed.check_video_prompt(o["prompt"], o["bpm"]) for o in out if o.get("type") == "prompt" and o.get("target") == "video"]

    print("written (the default): nothing changes")
    out, calls = run("written", "--beats", "3")
    if against:
        before, _ = run("written", "--beats", "3", root=os.path.abspath(against))
        keep = lambda items: [o for o in items if o.get("type") in ("story", "prompt", "visual") and o.get("seq", 0) >= 1]      # noqa: E731
        check(f"the same story, prompts and score as the feed in {against}", keep(out) == keep(before) and len(keep(out)) == 11)
    check("three pictures and two films, written by llama", len(prompts_of(out, "image")) == 3 and len(prompts_of(out, "video")) == 2
          and prompts_of(out, "image")[0] == WRITTEN_PICTURE)
    base = written(calls, ("story", "director", "image", "video"))

    print("structured: llama fills in cards")
    out, calls = run("structured", "--beats", "3", "--prompts", "structured")
    pictures, films = prompts_of(out, "image"), prompts_of(out, "video")
    look = "Maggie, a woman in her sixties, a trawler skipper: broad, weather-cut face, cropped white hair, yellow oilskin"
    check("three pictures and two films", len(pictures) == 3 and len(films) == 2)
    check("Maggie is described in the same words in every picture", all(look in p for p in pictures), pictures[2])
    check("llama's words go in verbatim", all(read_slots(c, CARD)["does"] in p for c, p in zip(CARDS, pictures)))
    check("'same' keeps the place and the light", "on the deck of a rusted trawler" in pictures[1].lower() and "Lit by low cold sun" in pictures[1])
    check("two people each get a place in the frame", "On the left is Tam, a lad of nineteen" in pictures[2] and "On the right is Maggie" in pictures[2])
    check("pictures run 60 to 200 words", all(60 <= len(p.split()) <= 200 for p in pictures), str([len(p.split()) for p in pictures]))
    voice = "(S1), a woman in her sixties, a trawler skipper, on screen, low gravelly voice, slow, Hull accent, "
    check("Maggie's speaker reference is the same in both films", all(voice in f for f in films), films[1])
    check("the films pass the feed's own strict check", sound(out) == [[], []], str(sound(out)))
    check("nothing needed mending", not any("Mended" in o.get("text", "") for o in out if o.get("stream") == "film"))
    check("'shouts:' is how the line is delivered", "shouts <d>en Nowt but weed!</d>" in films[0])
    check("the second film's music is the same piece continuing", "same piece continuing" in films[1] and "same piece" not in films[0])
    check("the card request shows the cast and the card before", "Cast: Maggie (a woman in her sixties, a trawler skipper)" in
          [c for c in calls if c["kind"] == "card"][1]["asked"] and "Before: who: Maggie; the dog" in [c for c in calls if c["kind"] == "card"][1]["asked"])
    check("newcomers are announced to the viewer", sum("joins the story" in o.get("text", "") for o in out) == 3)
    check("no image or video guide is sent", not any(c["kind"] in ("image", "video", "unknown") for c in calls))
    slots = written(calls, ("story", "director", "card", "film"))
    example = (pictures[0], films[0])

    print("malformed: llama gets everything wrong")
    out, calls = run("malformed", "--beats", "5", "--prompts", "structured")
    pictures, films = prompts_of(out, "image"), prompts_of(out, "video")
    check("five pictures and four films all the same", len(pictures) == 5 and len(films) == 4)
    check("no call is made twice", [c["kind"] for c in calls].count("card") == 5 and [c["kind"] for c in calls].count("film") == 4)
    check("an empty card falls back to the beat's own words", pictures[0].startswith(BEATS[0][:50]))
    check("every film has the three fields, a tagged line and the tempo",
          all(not [p for p in found if "age and gender" not in p and "spoken or sung" not in p] for found in sound(out)), str(sound(out)))
    check("an empty film card gives the plain film, in which nobody speaks, and the viewer is told so", "<d>" not in films[0]
          and "[Shot 1] The camera" in films[0] and any("put together here without llama (llama returned nothing)" in o.get("text", "") for o in out), films[0])
    check("tags are taken off a line and a long line is cut to what fits", "<d>en I never said a</d>" in films[1], films[1])
    check("a line with no speaker goes to someone in the picture", ", sings, a slow rolling tune, <d>en Heave away</d>" in films[2], films[2])
    check("an unseen, undescribed voice is an off-screen voiceover",
          "a person, adult, off screen" in films[3] and "says in an off-screen voiceover <d>en Tide's turning</d>" in films[3], films[3])
    check("the viewer is told what was left to code", any("left to code: camera, sound, line shortened" in o.get("text", "") or
                                                             "left to code: line shortened" in o.get("text", "") for o in out),
          str([o["text"] for o in out if o.get("stream") == "film"]))

    print("inline: the card comes with the beat")
    out, calls = run("inline", "--beats", "3", "--prompts", "inline")
    check("the story is emitted without its card", story_of(out) == BEATS)
    check("no separate card call is made", not any(c["kind"] == "card" for c in calls))
    check("the pictures are the same as with a separate card", prompts_of(out, "image")[0] == example[0])
    check("llama is shown its earlier cards and the cast", "who: Maggie; the dog" in [c for c in calls if c["kind"] == "story"][1]["seen"][0]
          and "Cast: Maggie" in [c for c in calls if c["kind"] == "story"][1]["asked"])
    inline = written(calls, ("story", "director", "film"))

    out, calls = run("inline-loose", "--beats", "3", "--prompts", "inline")
    kinds = [c["kind"] for c in calls]
    check("a beat with no card gets one from a separate call", kinds.count("card") == 1 and len(prompts_of(out, "image")) == 3)
    check("a card with no beat is asked again, as an empty beat is", kinds.count("story") == 4)
    check("a card before its beat is still read", story_of(out) == BEATS)

    if show:
        rate = 1.6      # tokens per word: a beat of 50 to 80 words measured about 115 tokens
        print("\nwhat llama writes, in words (and seconds at 4.2 tokens a second, 1.6 tokens a word)")
        for label, counts in (("written", base), ("structured", slots), ("inline", inline)):
            print(f"  {label}:")
            for kind, words in counts.items():
                if words:
                    mean = sum(words) / len(words)
                    print(f"    {kind:9s} {' '.join(str(w) for w in words):16s} mean {mean:5.1f} words, about {mean * rate:4.0f} tokens, {mean * rate / 4.2:4.0f} s")
        print("\n--- picture prompt, assembled ---\n" + example[0])
        print(f"({len(example[0].split())} words)")
        print("\n--- film prompt, assembled ---\n" + example[1])
        print(f"({len(example[1].split())} words)")


def away():
    """llama busy, absent, and failing: everything is still made, in a plainer way."""
    def said(out, words):
        return any(words in o.get("text", "") for o in out if o.get("type") == "read")

    def at(out, kind, **match):
        return next((i for i, o in enumerate(out) if o.get("type") == kind and all(o.get(k) == v for k, v in match.items())), -1)

    guide_picture = ("A trawler, a dog, a wet morning. Wide shot from a low angle, the horizon in the upper third, everything sharp from "
                     "foreground to distance. A realistic 35mm photograph, natural colour, fine film grain.")

    print("llama in the middle of a long reply (written prompts)")
    out, calls = run("mid-call", "--beats", "3", typed=[("writing beat 2", "the gulls scatter"), ("picture_now", "!film")])
    check("the guide is painted at once from an assembled prompt", out[at(out, "prompt", target="image", seq=0)]["prompt"] == guide_picture)
    repaint = next(o for o in out if o.get("picture_now"))
    check("a story steer repaints the present scene: the steer, then llama's own prompt for it", repaint["prompt"] == "The gulls scatter. " + WRITTEN_PICTURE)
    films = [o for o in out if o.get("type") == "prompt" and o.get("target") == "video"]
    check("!film is answered at once, before the beat llama is writing", 0 < at(out, "prompt", target="video", seq=1) < at(out, "story", seq=2)
          and (films[0]["from"], films[0]["to"]) == (0, 1))
    check("that film is put together here: the beat's words, a camera move, the sounds, the music",
          "integrated_multimodal_description: " + BEATS[0][:50] in films[0]["prompt"] and "[Shot 1] The camera" in films[0]["prompt"]
          and "overall_soundscape: The natural sounds" in films[0]["prompt"] and f"at {films[0]['bpm']} BPM" in films[0]["prompt"], films[0]["prompt"])
    check("the steer just typed is short enough to be spoken in it", "says in an off-screen voiceover <d>en the gulls scatter</d>" in films[0]["prompt"])
    check("the viewer is told it is plainer, and why", said(out, "put together here without llama (llama is busy writing), so it is plainer"))
    check("llama still writes the films that follow", [(f["from"], f["to"]) for f in films] == [(0, 1), (1, 2), (2, 3)]
          and WRITTEN_FILM.split("[Shot 1]")[1][:60] in films[1]["prompt"])
    check("the story and its pictures are as llama wrote them", story_of(out) == BEATS and prompts_of(out, "image") == [WRITTEN_PICTURE] * 3)

    for mode in ("written", "structured"):
        print(f"llama not there yet ({mode} prompts)")
        out, calls = run("absent", "--beats", "4", "--prompts", mode,
                         typed=[("carrying on without it", "!film"), ("there is only one so far", "a fox crosses the ice"),
                                ('"type": "story", "seq": 1', "it stops and listens"), ('"target": "image", "seq": 2', "!film 2")])
        check("the stand-in refused to connect, and the feed kept trying", calls[0]["refused"] >= 1 and said(out, "cannot be reached yet"))
        check("!film with one picture says what is needed", said(out, "there is only one so far"))
        check("two things typed about the story become beats 1 and 2", story_of(out)[:2] == ["a fox crosses the ice", "it stops and listens"]
              and said(out, "that is beat 1 of the story, in your own words") and said(out, "that is beat 2 of the story"))
        pictures = {o["seq"]: o["prompt"] for o in out if o.get("type") == "prompt" and o.get("target") == "image"}
        check("each has a picture of its own, from an assembled prompt", pictures[1].startswith("A fox crosses the ice. A trawler, a dog, a wet morning. ")
              and pictures[2].startswith("It stops and listens. A fox crosses the ice. A trawler, a dog, a wet morning. ") and "35mm" in pictures[2], pictures[2])
        films = [o for o in out if o.get("type") == "prompt" and o.get("target") == "video"]
        check("a film is made between them before llama is there", (films[0]["from"], films[0]["to"], films[0]["seconds"]) == (1, 2, 2.0)
              and at(out, "prompt", target="video", seq=2) < at(out, "story", seq=3)
              and "integrated_multimodal_description: It stops and listens. [Shot 1] The camera" in films[0]["prompt"]
              and "non_diegetic_music: House music at 120 BPM" in films[0]["prompt"], films[0]["prompt"])
        check("the launcher is asked to film it only once it exists", at(out, "prompt", target="video", seq=2) < at(out, "control", video="now"))
        check("the viewer is told it was made without llama", said(out, "put together here without llama (llama is not there yet)"))
        check("llama then carries on from beat 3", story_of(out)[2:] == BEATS[:2] and 3 in pictures and 4 in pictures)
        first = [c for c in calls if c["kind"] == "story"][0]
        check("and is shown the viewer's beats as the story so far, not as steers", "Beat 1: a fox crosses the ice" in first["first"]
              and "Beat 2: it stops and listens" in first["first"] and "Steer:" not in first["first"] + first["asked"], first["first"])

    print("llama stops answering in the middle of the story (structured prompts)")
    out, calls = run("down", "--beats", "4", "--prompts", "structured", typed=[("llama has stopped answering", "the ice cracks")])
    check("the viewer is told, and told again when it is back", said(out, "llama has stopped answering") and said(out, "llama is answering again"))
    check("what is typed meanwhile is the next beat", story_of(out) == [BEATS[0], "the ice cracks", BEATS[1], BEATS[2]], str(story_of(out)))
    pictures = {o["seq"]: o["prompt"] for o in out if o.get("type") == "prompt" and o.get("target") == "image"}
    check("with a picture that keeps the place and light llama last gave", pictures[2].startswith("The ice cracks. On the deck of a rusted trawler")
          and "Lit by low cold sun" in pictures[2], pictures[2])
    later = [c for c in calls if c["kind"] == "story"][2]
    check("llama is shown that beat when it is next asked", "Beat 2: the ice cracks" in later["asked"], later["asked"])

    out, calls = run("card-fails", "--beats", "3", "--prompts", "structured")
    pictures = prompts_of(out, "image")
    check("a card llama fails to give is not waited for: the picture is made from the beat's own words", pictures[0].startswith(BEATS[0][:60])
          and len(pictures) == 3 and "Maggie hauls a wet net" in pictures[1], pictures[0])


def kept():
    """Memorise and recall, typed: the story is kept under a number and brought back, in memory only."""
    print("memorise, then recall: the story goes back to where it was")
    out, calls = run("kept", "--beats", "4", typed=[('"type": "story", "seq": 1', "!recall 5"), ('"recalled": 5', "!memorise 2"),
                                                     ('"type": "story", "seq": 2', "!recall 2")])
    controls = [o for o in out if o.get("type") == "control"]
    check("a number nothing was memorised under is passed on, and the story is left alone",
          any(c.get("recalled") == 5 and "fresh" not in c for c in controls))
    check("memorising is said in a sentence, and the launcher is told so that the viewer keeps the music",
          any(c.get("memorise") == 2 for c in controls) and any("memorised as 2" in o.get("text", "") for o in out if o.get("type") == "read"))
    back = next((i for i, o in enumerate(out) if o.get("type") == "control" and o.get("recalled") == 2), -1)
    after = [o for o in out[back + 1:] if o.get("type") == "story"][:1]
    check("the recall starts afresh at a new number, then gives the beat it stands at",
          back >= 0 and out[back].get("fresh") == 3 and after == [{"type": "story", "seq": 3, "text": BEATS[0]}], str(out[back:back + 3]))
    check("the kept beat is told again under a new number and the story carries on from it",
          story_of(out) == [BEATS[0], BEATS[1], BEATS[0], BEATS[2]], str(story_of(out)))
    check("no picture is painted for the beat brought back, and no film starts from it",
          not any(o.get("type") == "prompt" and (o.get("seq") == 3 or o.get("from") == 3) for o in out) and len(prompts_of(out, "image")) >= 2)
    last = [c for c in calls if c["kind"] == "story"][-1]
    check("llama is shown it as the story so far, and nothing of what came after it was memorised",
          "The story so far, which you are returning to" in last["first"] and "Beat 3: " + BEATS[0][:40] in last["first"]
          and BEATS[1][:40] not in last["first"] + last["asked"] and not last["seen"], last["first"])
    check("the viewer is told where the story is", any("back where it was when 2 was memorised" in o.get("text", "") for o in out)
          and any("from where it stood when it was memorised" in o.get("text", "") for o in out))


def chopping():
    """!chop and !role, typed: how the sample layers are chopped, and a layer's role in it, straight to the viewer."""
    import story_feed
    from story_feed import SAMPLE_ASKED, chop_typed
    print("the chop style and a layer's role, typed")
    check("every chop style is read", all(chop_typed(f"!chop {s}") == {"chop_style": s} for s in story_feed.CHOP_STYLES)
          and chop_typed("!CHOP Drumfunk ") == {"chop_style": "drumfunk"})
    check("every role is read, and auto gives the role back to the engine",
          all(chop_typed(f"!role rain {r}") == {"role": {"layer": "rain", "role": r}} for r in story_feed.CHOP_ROLES)
          and chop_typed("!role Film3 auto") == {"role": {"layer": "film3", "role": None}} and chop_typed("!role rain color")["role"]["role"] == "colour")
    check("anything else is not: '!chop' with other words still asks for a clip to chop",
          chop_typed("!chop a dancer on a roof") is None and SAMPLE_ASKED.match("!chop a dancer on a roof") is not None
          and chop_typed("!chop") is None and chop_typed("!chop gabber") is None and chop_typed("!role rain") is None
          and chop_typed("!role rain lead") is None and chop_typed("!role the rain hook") is None and chop_typed("chop jungle") is None)
    out, calls = run("written", "--beats", "4", typed=[('"type": "story", "seq": 1', "!chop drumfunk"), ('"chop_style": "drumfunk"', "!role rain hook"),
                                                        ('"role": "hook"', "!role rain auto"), ('"role": null', "!chop atmospheric")])
    visuals = [o for o in out if o.get("type") == "visual" and ("chop_style" in o or "role" in o)]
    check("each goes to the viewer as a visual message, in order", visuals == [
        {"type": "visual", "seq": 0, "chop_style": "drumfunk"}, {"type": "visual", "seq": 0, "role": {"layer": "rain", "role": "hook"}},
        {"type": "visual", "seq": 0, "role": {"layer": "rain", "role": None}}, {"type": "visual", "seq": 0, "chop_style": "atmospheric"}], str(visuals))
    check("and nothing else is made of them: no clip to chop is asked for, no steer",
          not [o for o in out if ("drumfunk" in json.dumps(o) or "atmospheric" in json.dumps(o)) and o not in visuals and o.get("type") != "read"]
          and not any("drumfunk" in json.dumps(c) for c in calls), str([o for o in out if "drumfunk" in json.dumps(o)]))
    check("the story carries on", len(story_of(out)) == 4, str(story_of(out)))


def edging():
    """!edge and !roller, typed: the two dials for the edge, whose they are, a lip, and how long a riff is held."""
    from story_feed import edge_typed, edge_said
    print("the edge and the roller, typed")
    check("each dial is read, 0..1 or as a percentage",
          edge_typed("!edge lock 0.7") == {"edge": {"lock": 0.7}} and edge_typed("!edge derange 0.3") == {"edge": {"derange": 0.3}}
          and edge_typed("!EDGE Derangement 30") == {"edge": {"derange": 0.3}} and edge_typed("!edge lock 0") == {"edge": {"lock": 0.0}}
          and edge_typed("!edge lock 1") == {"edge": {"lock": 1.0}} and edge_typed("!edge lock 85%") == {"edge": {"lock": 0.85}})
    check("auto gives the dials back to the session, and a lip is set by ear",
          edge_typed("!edge auto") == {"edge": {"auto": True}} and edge_typed("!edge lip lock 0.6") == {"edge": {"lip": {"lock": 0.6}}}
          and edge_typed(" !edge lip derange 40 ") == {"edge": {"lip": {"derange": 0.4}}})
    check("the roller is read in bars, kept to 2..32",
          edge_typed("!roller 16") == {"roller": 16} and edge_typed("!roller 2") == {"roller": 2} and edge_typed("!roller 1") == {"roller": 2}
          and edge_typed("!roller 64") == {"roller": 32} and edge_typed("!roller 7.6") == {"roller": 8})
    check("anything else is not",
          all(edge_typed(line) is None for line in ("!edge", "!edge lock", "!edge lock high", "!edge lock 140", "!edge lock -1", "!edge tempo 0.5",
                                                    "!edge lock 0.5 now", "edge lock 0.5", "!edge lip 0.5", "!edge lip lock", "!roller", "!roller fast",
                                                    "!roller 16 bars", "!rollers 16", "!edges 0.4", "!edge nan", "!roller nan")))
    check("what is said back names the dial and its value",
          "lock 0.7" in edge_said({"edge": {"lock": 0.7}}) and "16 bars" in edge_said({"roller": 16}) and "session" in edge_said({"edge": {"auto": True}}))
    out, calls = run("written", "--beats", "4", typed=[('"type": "story", "seq": 1', "!edge lock 0.7"), ('"edge": {"lock": 0.7}', "!edge derange 30"),
                                                        ('"edge": {"derange": 0.3}', "!roller 4"), ('"roller": 4', "!edge lip lock 0.6"),
                                                        ('"lip": {"lock": 0.6}', "!edge auto")])
    visuals = [o for o in out if o.get("type") == "visual" and ("edge" in o or "roller" in o)]
    check("each goes to the viewer as a visual message, in order", visuals == [
        {"type": "visual", "seq": 0, "edge": {"lock": 0.7}}, {"type": "visual", "seq": 0, "edge": {"derange": 0.3}},
        {"type": "visual", "seq": 0, "roller": 4}, {"type": "visual", "seq": 0, "edge": {"lip": {"lock": 0.6}}},
        {"type": "visual", "seq": 0, "edge": {"auto": True}}], str(visuals))
    check("and nothing else is made of them: no steer, no call to the model",
          not any("!edge" in json.dumps(c) or "!roller" in json.dumps(c) for c in calls)
          and not [o for o in out if ("!edge" in json.dumps(o) or "!roller" in json.dumps(o)) and o.get("type") not in ("read", "say")],
          str([o for o in out if "!edge" in json.dumps(o) or "!roller" in json.dumps(o)]))
    check("the story carries on", len(story_of(out)) == 4, str(story_of(out)))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        child(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        units()
        away()
        kept()
        chopping()
        edging()
        feeds("--show" in sys.argv, sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv[:-1] else "")
        print(f"\n{len(FAILED)} failed" + ("".join("\n  " + f for f in FAILED) if FAILED else ""))
        sys.exit(1 if FAILED else 0)
