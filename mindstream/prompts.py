"""Prompts put together in code. llama fills in a few short slots; everything that is structure or repetition
is written here: the order of a picture prompt, the film format with its labels and speaker references, the
music line, and the people of the story, who are described once and then repeated word for word.

    Cast          the individuals of the story: what they are, how they look, how they sound
    Notebook      the cast, the present place and light, and the card of each recent beat; makes the prompts
    read_slots    a reply of labelled lines -> {slot: text}, read leniently
    split_beat    a story reply with a card after it -> (beat, card)
    music_line    the music as it stands -> the film's background music, in words

What llama writes goes into the prompts word for word: nothing is tidied. Whatever it leaves out is filled in
here, and it is never asked twice. With no reply from llama at all, both prompts can still be made, in a plainer
way, from the guide, the beats (or what the viewer typed) and the score: that is what is used while llama is
away or busy. Nothing here talks to a model or touches the disk: the cast lives in memory and is gone with the
process.
"""
import json
import re

AGE_WORDS = re.compile(r"\b(\d{1,3}|child|kid|boy|girl|teen\w*|young|youth|twenties|thirties|forties|fifties|sixties|seventies|"
                       r"eighties|nineties|middle-aged|elderly|old|aged|adult|infant|toddler)\b", re.I)
GENDER_WORDS = re.compile(r"\b(man|woman|men|women|boy|girl|male|female|lad|lass|gentleman|lady|mother|father|son|daughter|"
                          r"brother|sister|he|she|his|her|nonbinary|androgynous)\b", re.I)
VOICE_WORDS = re.compile(r"\b(voice\w*|accent\w*|pitch\w*|spoken|speaks|tone|drawl|rasp\w*|growl\w*|whisper\w*|lilt|brogue|"
                         r"baritone|tenor|alto|soprano)\b", re.I)

# The labels llama may use, and the slot each one fills. Several spellings are taken for the same slot.
CARD = {"who": "who", "present": "who", "people": "who", "cast": "who",
        "does": "does", "doing": "does", "action": "does", "what": "does", "subject": "does",
        "where": "where", "place": "where", "setting": "where", "location": "where",
        "light": "light", "lighting": "light", "lit by": "light",
        "mood": "mood", "palette": "mood", "shot": "shot", "framing": "shot", "composition": "shot",
        "style": "style", "medium": "style", "new": "new", "beat": "beat"}
FILM = {"moves": "moves", "move": "moves", "journey": "moves", "camera": "moves", "shot": "moves", "happens": "moves",
        "voice": "voice", "speaker": "voice", "who": "voice", "how": "how", "delivery": "how",
        "says": "says", "say": "says", "line": "says", "words": "says", "sings": "says", "shouts": "says",
        "whispers": "says", "calls": "says", "chants": "says",
        "sound": "sound", "sounds": "sound", "soundscape": "sound", "lang": "lang", "language": "lang", "new": "new"}
MANY = ("new",)                      # slots that may be given more than once
SAME = ("same", "unchanged", "as before", "no change", "the same", "same as before")
NOTHING = ("", "-", "--", "none", "n/a", "na", "nothing", "...", "nobody", "no one", "no-one", "noone", "empty")
VERBS = {"says": "says", "say": "says", "said": "says", "speaks": "says", "sings": "sings", "sing": "sings", "sung": "sings",
         "singing": "sings", "shouts": "shouts", "shout": "shouts", "yells": "shouts", "screams": "shouts",
         "whispers": "whispers", "whisper": "whispers", "murmurs": "whispers", "mutters": "whispers",
         "calls": "calls", "call": "calls", "cries": "calls", "chants": "chants", "chant": "chants"}

# What code supplies when llama gives no framing: chosen by how many are in the picture, turning with the beats.
FRAMING = {0: ("Wide shot from a low angle, the horizon in the upper third, everything sharp from foreground to distance",
               "Wide shot from above, looking down the length of the place, deep focus"),
           1: ("Medium shot at eye level, the figure just left of centre, the background falling soft behind",
               "Close shot from slightly below, face and hands large in the frame, shallow depth of field",
               "Full-length shot from across the space, the figure small against the setting, deep focus"),
           2: ("Medium shot at eye level, every figure sharp, the background soft behind them",
               "Wide shot at eye level taking in the whole group and the place around them, deep focus")}
PLACES = ("On the left", "On the right", "Behind them")
LOOK = "A realistic 35mm photograph, natural colour, fine film grain"        # until the guide or a steer names a style
_MEDIUM = (r"(?:photo(?:graph)?|painting|watercolou?r|drawing|sketch|illustration|cartoon|anime|comic|woodcut|engraving|etching|"
           r"render|pixel art|collage|fresco|mosaic|linocut|claymation)")
# "as a woodcut", "in thick oil painting", "a watercolour of ...", "in the style of ...": the words name their own medium
MEDIUM_WORDS = re.compile(rf"\b(?:as|in) (?:an? |the )?(?:[\w-]+ ){{0,2}}{_MEDIUM}\b|\b{_MEDIUM} (?:of|showing)\b|\bstyle of\b", re.I)
CAMERA = ("The camera pushes slowly forward through the scene, one place giving way to the next",
          "The camera rises and turns, the first place falling away as the second opens out",
          "The camera is carried sideways past what stands nearest, into the next place",
          "The camera pulls back and the scene changes around it")
SOUND = "The natural sounds of the place and of what is done in it"
# A voice for anyone llama did not give one, dealt out in turn so that two people do not sound alike.
SPARE_VOICES = ("low dry voice, slow", "high clear voice, quick", "deep worn voice, unhurried", "light bright voice, even",
                "rough mid voice, clipped")
NARRATOR = {"name": "narrator", "kind": "a storyteller, a woman in her forties", "look": "", "voice": "low even voice, unhurried"}

# The film's background music, style by style, worded to match what the rhythm section plays (groove.STYLES).
BEATS = {
    "four": "House music at {bpm} BPM: a punchy kick drum on every beat, a clap on beats two and four, a crisp open hi-hat on every off-beat",
    "twostep": "UK garage 2-step at {bpm} BPM: a skipping kick on the first beat and again just after the third, a tight snare on "
               "beats two and four, swung shuffling hi-hats",
    "broken": "A syncopated broken-beat groove at {bpm} BPM: the kick drum lands off the beat, pushing ahead of each bar, "
              "rimshots answer between the kicks, shakers keep steady sixteenths",
    "dnb": "Drum and bass at {bpm} BPM: a fast rolling breakbeat with a snare cracking on beats two and four",
    "half": "Slow, heavy half-time at {bpm} BPM: one deep kick at the start of each bar, a single snare on the third beat, sparse closed hi-hats",
    "none": "Ambient music at {bpm} BPM, with a pulse but no drums",
    "rolling": "Rolling drum and bass at {bpm} BPM: a busy, even breakbeat that never lets up, ghost snares between the hits",
    "shuffled_two_step": "Shuffling UK garage at {bpm} BPM: a skipping kick, a tight snare on beats two and four, hi-hats swung hard and late",
    "stutter": "A stuttering, syncopated beat at {bpm} BPM: kicks that trip and repeat, snares landing where they are least expected",
    "amen": "Jungle at {bpm} BPM: a chopped, rolling breakbeat with a snare cracking on beats two and four",
    "breakbeat_hardcore": "Breakbeat hardcore at {bpm} BPM: a fast syncopated breakbeat, the kick pushing ahead of the bar, busy snares",
    "happy_hardcore": "Happy hardcore at {bpm} BPM: a pounding kick drum on every beat, bright off-beat stabs, rushing hi-hats",
    "gabber": "Gabber at {bpm} BPM: a hard distorted kick drum on every beat, relentless and overdriven",
}
BEATS.update(four_on_the_floor=BEATS["four"], two_step=BEATS["twostep"], half_step=BEATS["half"])
MODE_MOOD = {"minor": "sorrowful and tense", "major": "bright and relieved", "dorian": "warm with an edge", "phrygian": "dark and menacing"}
MOOD_WORDS = {"minor": "sorrow", "major": "brightness", "dorian": "warmth", "phrygian": "dread"}


def music_line(music, bpm, continuing=False):
    """The `non_diegetic_music:` line for a film, from the score as it stands: style, key, how much sub and
    how many bells, how full it is. The same words every time the score is the same."""
    get = lambda name, default: float(music.get(name, default) or 0)      # noqa: E731
    style = str(music.get("style", "four"))
    parts = [BEATS.get(style, BEATS["four"]).format(bpm=round(bpm))]
    sub, twinkle, chaos = get("sub", 0.8), get("twinkle", 0.3), get("chaos", 1.0)
    if sub >= 0.7:
        parts.append("a huge deep sub bass holding long notes")
    elif sub >= 0.3:
        parts.append("a warm sub bass under it")
    elif sub >= 0.05:
        parts.append("a light bass line")
    if twinkle >= 0.7:
        parts.append("bright twinkling bell arpeggios showering down high above")
    elif twinkle >= 0.25:
        parts.append("a few glinting bell notes high above")
    if 0.5 < chaos < 1.3 and style != "none":
        parts.append("a short synth riff that repeats every bar")
    line = parts[0] + ((", " if ":" in parts[0] else ": ") + ", ".join(parts[1:]) if parts[1:] else "") + "."
    mode = str(music.get("key", "A minor")).split()[-1].lower()
    line += f" In {music.get('key', 'A minor')}" + (f", {MODE_MOOD[mode]}." if mode in MODE_MOOD else ".")
    if chaos <= 0.5:
        line += " Stripped back to almost nothing but the bass." if style == "none" else " Stripped back to little more than kick and bass."
    elif chaos >= 1.3:
        line += " Full and relentless, every part playing at once."
    if get("swing", 0.0) > 0.15 and style not in ("twostep", "two_step", "shuffled_two_step"):
        line += " The off-beats fall late and loose."
    return line + (" The same piece continuing." if continuing else "")


def tidy(text):
    """One line, without the quotes, brackets or markdown a model may wrap round it."""
    text = " ".join(str(text).replace("**", "").replace("`", "").split())
    while len(text) > 1 and text[0] in "\"'[" and text[-1] in "\"']":
        text = text[1:-1].strip()
    return text.strip()


def clip(text, words):
    """At most this many words, cut at a word."""
    parts = text.split()
    return text if len(parts) <= words else " ".join(parts[:words]).rstrip(",;:-")


def sentence(text):
    """A capital to start and a full stop to end; the words between are left alone."""
    text = text.strip().rstrip(",;:")
    if not text:
        return ""
    return text[0].upper() + text[1:] + ("" if text[-1] in ".!?\"'" else ".")


def _label(line, labels):
    """(slot, label, value) if the line opens with a known label, else None. Bullets, numbers and bold are ignored."""
    clean = re.sub(r"^[\s>*#\-\d.)`_]+", "", line).replace("**", "").replace("__", "")
    found = re.match(r"([A-Za-z][A-Za-z ]{1,15}?)\s*[:=]\s*(.*)$", clean)
    if not found or found.group(1).strip().lower() not in labels:
        return None
    return labels[found.group(1).strip().lower()], found.group(1).strip().lower(), found.group(2).strip()


def strip_fence(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text.strip()


def read_slots(reply, labels):
    """A reply of labelled lines -> {slot: text}; slots in MANY -> a list. Read leniently: any order, any of the
    known spellings, bullets or bold round the labels, a JSON object instead, everything run together on one
    line. A line with no label carries on the slot above it. Unknown labels and empty slots are dropped."""
    reply, slots = strip_fence(reply or ""), {}
    if reply.startswith("{"):                                  # some models answer a form with JSON
        try:
            raw = json.loads(reply[:reply.rfind("}") + 1])
            reply = "\n".join(f"{k}: {x}" for k, v in raw.items() for x in (v if isinstance(v, list) else [v]))
        except (ValueError, AttributeError):
            pass
    lines = reply.splitlines()
    if sum(1 for line in lines if _label(line, labels)) <= 1:  # run together: break before each label
        names = "|".join(sorted((re.escape(k) for k in labels), key=len, reverse=True))
        lines = re.sub(rf"(?<=[\s.;|])({names})\s*:", r"\n\1:", reply, flags=re.I).splitlines()
    slot = None
    for line in lines:
        found = _label(line, labels)
        if found:
            slot, label, value = found
            value = tidy(value)
            if slot in MANY:
                if value:
                    slots.setdefault(slot, []).append(value)
                slot = None                                    # one line each: nothing carries on from it
            else:
                slots[slot] = value
                if slot == "says" and label in VERBS:
                    slots["verb"] = VERBS[label]               # "sings: ..." says how as well as what
        elif slot and line.strip():
            slots[slot] = (slots[slot] + " " + tidy(line)).strip()
    return {k: v for k, v in slots.items() if isinstance(v, list) or v.lower().strip(". ") not in NOTHING or k == "who"}


def split_beat(reply):
    """A story reply that carries a card -> (beat, card). The beat is what comes before the first labelled
    line (or, if the card came first, the paragraph after it); with no labelled line the card is ''."""
    reply = re.sub(r"(?<=[.!?\"'])\s+(who\s*:)", r"\n\1", strip_fence(reply or ""), count=1, flags=re.I)    # a card run on from the beat
    lines = reply.splitlines()
    marks =[i for i, line in enumerate(lines) if _label(line, CARD) and _label(line, CARD)[0] != "beat"]
    if not marks:
        return " ".join(re.sub(r"^\s*beat\s*:\s*", "", " ".join(lines), flags=re.I).split()), ""
    before = [line for line in lines[:marks[0]] if not re.fullmatch(r"[\s\-_*=#]*(shot )?(card)?:?[\s\-_*=#]*", line, re.I)]
    beat, card = " ".join(" ".join(before).split()), "\n".join(lines[marks[0]:])
    if not beat:                                               # the card came first: the beat is the paragraph after it
        tail = lines[marks[-1] + 1:]
        gap = next((i for i, line in enumerate(tail) if not line.strip()), None)
        if gap is not None:
            beat = " ".join(" ".join(tail[gap:]).split())
            card = "\n".join(lines[marks[0]:marks[-1] + 1 + gap])
    return re.sub(r"^\s*beat\s*:\s*", "", beat, flags=re.I), card


def split_names(text):
    """'Maggie; the dog and Tam (her son)' -> ['Maggie', 'the dog', 'Tam']. 'nobody' -> []."""
    names = []
    for part in re.split(r"\s*(?:[;,/&|]|\band\b|\bwith\b)\s*", re.sub(r"\([^)]*\)", "", text)):
        part = tidy(part).strip(".:")
        if part.lower() not in NOTHING and len(part.split()) <= 5 and part not in names:
            names.append(part)
    return names


def _key(name):
    return " ".join(re.sub(r"[^\w\s'-]", "", re.sub(r"^(the|a|an)\s+", "", name.strip().lower())).split())


def _gender(text):
    """'female' or 'male' if the text's pronouns lean clearly one way, else ''."""
    low = text.lower()
    she, he = len(re.findall(r"\b(she|her|hers)\b", low)), len(re.findall(r"\b(he|him|his)\b", low))
    return "female" if she > he else "male" if he > she else ""


def _opening(beat, words):
    """The start of a beat, to the end of a sentence if one ends in time."""
    cut = clip(" ".join(beat.split()), words)
    ends = [m.end() for m in re.finditer(r"[.!?](?=\s|$)", cut)]
    return cut[:ends[-1]] if ends else cut


class Cast:
    """The individuals of the story. Each is described once, by llama, when they first appear; after that code
    writes the same description into every picture they are in and the same voice into every film they speak in."""

    def __init__(self, limit=24):
        self.people, self.limit, self.count = {}, limit, 0

    def find(self, name):
        """The person meant by a name, said loosely: 'Maggie' finds 'Maggie Rudd', 'the Dog' finds 'the dog'."""
        key = _key(name)
        if not key:
            return None
        if key in self.people:
            return self.people[key]
        words = set(key.split())
        near = [p for k, p in self.people.items() if words <= set(k.split()) or set(k.split()) <= words]
        return max(near, key=lambda p: p["seen"]) if near else None

    def meet(self, name, beat="", seq=0):
        """The person of that name, made known by name alone if they are new."""
        person = self.find(name)
        if person is None:
            if not _key(name):
                return None
            person = {"name": tidy(name), "kind": "", "look": "", "voice": "", "seen": seq, "guess": _gender(beat),
                      "spare": SPARE_VOICES[self.count % len(SPARE_VOICES)]}
            self.count += 1
            self.people[_key(name)] = person
            while len(self.people) > self.limit:               # the longest unseen makes room
                del self.people[min(self.people, key=lambda k: self.people[k]["seen"])]
        person["seen"] = max(person["seen"], seq)
        return person

    def learn(self, line, beat="", seq=0):
        """One 'new:' line -> a person: name | what they are, age and gender | how they look | how they sound.
        Parts may be missing, labelled, out of order, or run together with commas. Someone already described
        keeps their description: only what was missing is filled in."""
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 1:
            parts = [p.strip() for p in line.split(";")]
        found = re.match(r"(.+?)\s*(?:[:=(]|\s-\s)\s*(.*)$", parts[0])
        if found and len(found.group(1).split()) <= 5:         # "Maggie: a woman ..." shares the first part
            name, parts = found.group(1), [found.group(2).rstrip(")")] + parts[1:]
        elif len(parts) == 1 and "," in parts[0]:
            name, _, rest = parts[0].partition(",")
            parts = [rest.strip()]
        else:
            name, parts = parts[0], parts[1:]
        parts = [p for p in parts if p]
        kind = look = voice = ""
        if len(parts) == 1:                                    # all in one, by commas: sort it out by its words
            items = [i.strip() for i in parts[0].split(",") if i.strip()]
            start = next((i for i, item in enumerate(items) if VOICE_WORDS.search(item)), len(items))
            voice, items, taken = ", ".join(items[start:]), items[:start], 1
            while taken < min(len(items), 3) and not (AGE_WORDS.search(", ".join(items[:taken]))
                                                      and GENDER_WORDS.search(", ".join(items[:taken]))):
                taken += 1
            kind, look = ", ".join(items[:taken]), ", ".join(items[taken:])
        elif parts:
            plain = []
            for part in parts:
                labelled = re.match(r"(voice|sounds?|speaks?)\s*:\s*(.*)$", part, re.I)
                if not voice and (labelled or (VOICE_WORDS.search(part) and plain)):
                    voice = labelled.group(2) if labelled else part
                else:
                    plain.append(re.sub(r"^(is|kind|looks?|appearance|wears?)\s*:\s*", "", part, flags=re.I))
            kind, look = (plain + ["", ""])[0], ", ".join(p for p in plain[1:] if p)
        person = self.meet(clip(tidy(name), 5), beat, seq)
        if person is None:
            return None
        voice = re.sub(r"^(their |the )?(voice|sounds?|speaks?)\s*:\s*", "", tidy(voice), flags=re.I)
        if voice and not re.search(r"\bvoice", voice, re.I):   # "low and gravelly, slow" -> "low and gravelly voice, slow"
            first, comma, rest = voice.partition(",")
            voice = first.strip() + " voice" + comma + rest
        for slot, value, most in (("kind", kind, 20), ("look", look, 40), ("voice", voice, 16)):
            if not person[slot] and tidy(value).lower() not in NOTHING:
                person[slot] = clip(tidy(value).rstrip(".,;"), most)
        return person

    def named_in(self, text):
        """Those of the cast whose name appears in a piece of text."""
        low = text.lower()
        return [p for k, p in self.people.items() if re.search(rf"\b{re.escape(k)}\b", low)]

    def appearance(self, person, place=""):
        """How a person is written into a picture: the same words every time. `place` is where they stand
        when there are several ("On the left")."""
        name, kind, look = person["name"], person["kind"], person["look"]
        if place:
            return f"{place} is " + ", ".join(x for x in (name, kind) if x) + (f": {look}" if look else "")
        if re.match(r"(a|an|the)\s", kind, re.I):
            return f"{name} is {kind}" + (f": {look}" if look else "")
        return ", ".join(x for x in (name, kind, look) if x)

    def identity(self, person):
        """The identifying phrase of a speaker reference: what kind of person, age, gender. Age and gender are
        never left out: where llama gave none, 'adult' and the lean of the beat's pronouns stand in."""
        kind = person["kind"] or "a person"
        if not AGE_WORDS.search(kind):
            kind += ", adult"
        if not GENDER_WORDS.search(kind) and person.get("guess"):
            kind += ", " + person["guess"]
        return kind

    def voice(self, person):
        return person["voice"] or person.get("spare") or SPARE_VOICES[0]

    def listing(self, limit=8):
        """The cast as llama is shown it: names, with what each is, the most recently seen first."""
        people = sorted(self.people.values(), key=lambda p: -p["seen"])[:limit]
        return "; ".join(p["name"] + (f" ({clip(p['kind'], 12)})" if p["kind"] else "") for p in people) or "nobody yet"


class Notebook:
    """What code remembers of the story so far: its cast, the present place, light and style, and the card of
    each recent beat. From these it writes the picture prompt and the film prompt."""

    def __init__(self):
        self.cast, self.scene, self.cards, self.filmed = Cast(), {}, {}, None

    def card_request(self, beat, notes=()):
        """What llama is shown when asked for a beat's card on its own."""
        last = self.cards.get(max(self.cards)) if self.cards else None
        before = ("Before: " + "; ".join(f"{k}: {v}" for k, v in (("who", "; ".join(self.name(k) for k in last["who"]) or "nobody"),
                                                                     ("where", last["where"]), ("light", last["light"])) if v) + "\n") if last else ""
        return f"Cast: {self.cast.listing()}\n{before}" + "".join(f"Steer: {n}\n" for n in notes) + f"Beat: {beat}"

    def film_request(self, beat_from, beat_to, words, notes=()):
        return (f"Cast: {self.cast.listing()}\n" + "".join(f"Steer: {n}\n" for n in notes)
                + f"From: {beat_from}\n\nTo: {beat_to}\n\nWords: at most {words}")

    def name(self, key):
        return self.cast.people[key]["name"] if key in self.cast.people else key

    def take_card(self, seq, reply, beat):
        """Read a beat's card, learn anyone new in it, and keep it. Returns the card; card['filled'] names what
        llama left out and code supplied."""
        slots, filled = read_slots(reply, CARD), []
        known = {k for k, p in self.cast.people.items() if p["kind"] or p["look"]}
        new = [p for p in (self.cast.learn(line, "", seq) for line in slots.get("new", [])) if p and _key(p["name"]) not in known]
        if "who" in slots:
            names = split_names(slots["who"])                  # the beat's pronouns say something only of one who is there alone
            people = [p for p in (self.cast.meet(name, beat if len(names) == 1 else "", seq) for name in names) if p]
            people = [p for i, p in enumerate(people) if p not in people[:i]]
        else:                                                  # not said: whoever of the cast the beat names
            people = self.cast.named_in(beat) + [p for p in new if p not in self.cast.named_in(beat)]
            filled.append("who")
        for person in people:
            person["seen"] = max(person["seen"], seq)
        card = {"seq": seq, "who": [_key(p["name"]) for p in people if p], "new": [_key(p["name"]) for p in new],
                "does": clip(slots.get("does", ""), 60), "shot": clip(slots.get("shot", ""), 30)}
        if not card["does"]:
            filled.append("does")
        for slot, most in (("where", 40), ("light", 25)):      # these hold until llama says otherwise
            value = slots.get(slot, "")
            if value and value.lower().strip(". ") not in SAME:
                self.scene[slot] = clip(value, most)
            elif not value and slot not in self.scene:
                filled.append(slot)
            card[slot] = self.scene.get(slot, "")
        card["mood"] = "" if slots.get("mood", "").lower().strip(". ") in SAME else clip(slots.get("mood", ""), 12)
        if slots.get("style"):
            self.scene["style"] = clip(slots["style"], 25)
        card["filled"] = filled
        self.cards[seq] = card
        for old in [k for k in self.cards if k < seq - 3]:     # a film needs this beat's card and the one before
            del self.cards[old]
        return card

    def render(self, card):
        """A card as llama would have written it: shown back to it so the form is always in front of it."""
        lines = [f"who: {'; '.join(self.name(k) for k in card['who']) or 'nobody'}"]
        lines += [f"{slot}: {card[slot]}" for slot in ("does", "where", "light", "mood") if card.get(slot)]
        for key in card.get("new", []):
            p = self.cast.people.get(key)
            if p:
                lines.append(f"new: {p['name']} | {p['kind']} | {p['look']} | {p['voice']}")
        return "\n".join(lines)

    def picture(self, seq, beat, music=None, guide="", lead="", before="", written=""):
        """The picture prompt for a beat: who is there (as the cast has them), what they do, the place, the
        framing, the light, the medium, the mood. One paragraph.

        With no card from llama it is made in a plainer way: the beat's own words are the subject, and until a
        place is known the beat before and the guide stand in for one. `lead` is something the viewer has just
        typed, which goes first, word for word. `written` is a prompt llama wrote out in full for this beat: the
        lead is put in front of it and nothing else is changed."""
        if written:
            return " ".join(x for x in (sentence(clip(lead, 60)), written) if x)
        card = self.cards.get(seq) or {"who": [], "does": "", "where": self.scene.get("where", ""), "light": self.scene.get("light", ""),
                                       "mood": "", "shot": ""}
        people = [self.cast.people[k] for k in card["who"] if k in self.cast.people]
        told = [p for p in people if p["kind"] or p["look"]]   # someone known by name alone adds nothing here
        parts = [clip(lead, 60)]
        if len(told) == 1:
            parts.append(self.cast.appearance(told[0]))
        else:                                                  # several: each in their own place, so their looks do not mix
            parts += [self.cast.appearance(p, place) for place, p in zip(PLACES, told)]
        parts.append(card["does"] or _opening(beat, 60))
        if card["where"]:
            parts.append(card["where"])
        else:                                                  # no place known yet: what came before, and the guide, set the scene
            parts += [x for x in (_opening(before, 30), clip(guide, 60)) if x and x.strip(". ") != beat.strip(". ")]
        framing = FRAMING[min(len(people), 2)]
        parts.append(card["shot"] or framing[seq % len(framing)])
        light = card["light"]
        parts.append(light if not light or re.match(r"(lit|light|the light|it is|there)\b", light, re.I) else "Lit by " + light)
        named = MEDIUM_WORDS.search(" ".join(str(p) for p in parts) + " " + guide)     # the words themselves name a medium: leave it to them
        parts.append(self.scene.get("style") or ("" if named else LOOK))
        mode = str((music or {}).get("key", "")).split()[-1:] or [""]
        parts.append(card["mood"] or (f"A mood of {MOOD_WORDS[mode[0].lower()]}" if card["does"] and mode[0].lower() in MOOD_WORDS else ""))
        return " ".join(sentence(p) for p in parts if p)

    def film(self, n, reply, beat_from, beat_to, music, bpm, words, lang="en", start=None, line=""):
        """The three labelled fields of the film prompt from beat `start` (n-1 unless given) to beat n, from
        llama's film card and what is already known. Returns (prompt, filled): `filled` names what llama left
        out and code supplied.

        With an empty reply this is the plain film made while llama is away: the place and what happens from
        the beat's card or its own words, whoever of the cast is there, a camera move, the sounds of the place,
        and the music from the score. Nobody speaks, unless `line` is given (something short the viewer typed),
        which a voice off screen then says."""
        slots, filled = read_slots(reply, FILM), []
        for new in slots.get("new", []):
            self.cast.learn(new, beat_to, n)
        here, there = self.cards.get(n) or {}, self.cards.get(n - 1 if start is None else start) or {}
        on_screen = list(dict.fromkeys(here.get("who", []) + there.get("who", [])))
        # who is heard, and what they say
        said = re.sub(r"</?d>|\(S\d+\)", " ", slots.get("says", ""))
        said = re.sub(r"^\s*[a-z]{2}\s+", "", said) if "<d>" in slots.get("says", "") else said
        said = tidy(said)
        asked = slots.get("voice", "")
        person = None
        if said and asked and not re.match(r"(narrator|off|voice-?over|nobody|none)\b", asked.lower()):
            person = self.cast.meet(clip(re.sub(r"[,(].*$", "", asked), 5), "", n)
        elif said and not asked and here.get("who"):           # a line with no speaker: the first one in the picture says it
            person = self.cast.people.get(here["who"][0])
            filled.append("voice")
        if not said:
            said, person = tidy(line), None
            filled.append("line" if said else "nobody speaks")
        if len(said.split()) > words:
            said = clip(said, words)
            filled.append("line shortened")
        seen = person is not None and _key(person["name"]) in on_screen and not re.search(r"\boff[ -]?screen\b|\bunseen\b", asked.lower())
        person = person or NARRATOR
        how = slots.get("how", "").split(None, 1)              # "sings, a thin rising melody", or only "hoarse, half laughing"
        verb = VERBS.get(how[0].lower().strip(",.:"), "") if how else ""
        manner = tidy((how[1] if len(how) > 1 else "") if verb else slots.get("how", "")).strip(",. ")
        verb = verb or slots.get("verb") or "says"
        telling = verb + (f", {clip(manner, 14)}," if manner else "") if seen else "says in an off-screen voiceover"
        tag = slots["lang"].lower() if re.fullmatch(r"[A-Za-z]{2}", slots.get("lang", "")) else lang
        if not person["voice"]:
            filled.append("the speaker's voice")
        if not GENDER_WORDS.search(self.cast.identity(person)):
            filled.append("the speaker's gender is not known")
        speaker = (f" (S1), {self.cast.identity(person)}, {'on screen' if seen else 'off screen'}, {self.cast.voice(person)}, "
                   f"{telling} <d>{tag} {said}</d>" + ("" if seen or not on_screen else " Everyone on screen keeps their lips closed."))
        if not said:
            speaker = ""
        # what is seen
        there_now = [self.cast.people[k] for k in here.get("who", []) if k in self.cast.people and self.cast.people[k]["kind"]][:2]
        opening = " ".join(sentence(x) for x in (here.get("where", ""), here.get("does", "") or _opening(beat_to, 30),
                                                 "On screen: " + "; ".join(f"{p['name']}, {p['kind']}" for p in there_now) if there_now else "") if x)
        moves = clip(slots.get("moves", ""), 45)
        if not moves:
            moves = CAMERA[n % len(CAMERA)]
            filled.append("camera")
        sound = clip(slots.get("sound", ""), 40)
        if not sound:
            sound = SOUND
            filled.append("sound")
        score = (music.get("style"), music.get("key"))
        continuing, self.filmed = self.filmed == score, score
        return (f"integrated_multimodal_description: {opening} [Shot 1] {sentence(moves)}{speaker}\n"
                f"overall_soundscape: {sentence(sound)}\n"
                f"non_diegetic_music: {music_line(music, bpm, continuing)}"), filled
