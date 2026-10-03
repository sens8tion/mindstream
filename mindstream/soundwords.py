"""Words for pulling samples. Two jobs, both pure text (no numpy), so the story feed can use them:

- reading a typed request ("pull a vinyl crackle loop from splice") into what to look for, as what, and where;
- sanitising what the STORY may ask for. A search goes to an outside service, which will log it, so nothing of
  the story itself may ride along: a request from the story is cut down to at most three words from a fixed
  list of plain sound words. Anything else is dropped; if nothing is left, nothing is asked for.
"""
import re

SAFE = frozenset("""
rain thunder storm wind breeze gale sea ocean waves surf tide river stream brook waterfall water drip dripping splash bubbles underwater
fire crackle bonfire campfire embers forest woods jungle swamp desert mountain field meadow farm garden park beach harbour harbor cave tunnel
birds birdsong gulls seagulls crows owl crickets insects bees flies frogs dog dogs wolf wolves horse horses cattle sheep cat
night dawn dusk morning evening city street traffic car cars engine motor motorbike bus lorry truck train trains railway station subway
plane aeroplane airport helicopter boat ship ferry foghorn crowd people chatter murmur applause cheering laughter children playground
footsteps walking running door doors creak knock gate lock keys chains coins bell bells church clock ticking chime glass metal wood stone
machine machines machinery factory industrial workshop hammer saw drill welding steam hiss hum buzz drone static radio vinyl tape hiss
market cafe restaurant kitchen kettle boiling frying cutlery plates pouring bar pub club party wedding funeral fairground carnival parade
stadium arena school office typewriter keyboard phone telephone television arcade lift elevator escalator construction crane
heartbeat breath breathing whisper whispers choir chant chanting humming singing voices organ piano guitar violin cello flute trumpet
saxophone accordion harmonica tambourine gong cymbal drum drums snare kick hat hats bass synth pad noise ambience atmosphere room hall
cathedral warehouse garage stairwell corridor basement attic snow ice hail fireworks siren sirens alarm horn horns whistle
heavy light distant close busy quiet empty big small old wooden metallic wet dry slow fast soft loud low high deep bright dark
white pink warm cold hollow muffled echo echoing reverb loop break beat rhythm percussion shaker clap claps stomp
window windows roof tin floor floorboards wall walls stairs staircase bridge road path gravel sand mud leaves grass trees branches
puddle puddles gutter drain pipe pipes tap sink bath shower fountain pond lake shore cliff rocks pebbles shingle dock quay pier
wheels brakes tyres hooves cart wagon bicycle sails rope ropes canvas flag paper pages book cloth zip cutlery cup cups
hall hallway cellar yard courtyard square alley shop factory mill church chapel tower barn shed tent
cracking creaking howling rumbling roaring rattling ringing buzzing crashing lapping rustling dripping pouring falling blowing
""".split())
STOP = frozenset("a an the of on in at by with and or to from for under over through against into onto near behind inside outside "
                 "sound sounds noise noises some its their his her".split())


def sort_request(text, most=4):
    """What to do with a sound the STORY has asked for. The story is written by a language model and may ask for
    anything, in any words; an outside archive will log whatever it is sent. So:
      ("ask", query)   every word of it is a plain sound word: it may be asked of an archive, as it stands
      ("make", text)   it has words that are not: it is never sent anywhere, and is made here instead
      ("none", "")     there is nothing in it to go on"""
    words = [w for w in re.findall(r"[a-z]+", str(text).lower()) if w not in STOP]
    if not words:
        return "none", ""
    if all(w in SAFE for w in words) and len(words) <= most:
        return "ask", " ".join(dict.fromkeys(words))
    return "make", " ".join(str(text).split())[:120]

ROLES = (("kick", r"\bkicks?\b|\bbass drum\b"), ("snare", r"\bsnares?\b|\bclaps?\b|\brimshot\b"), ("hats", r"\bhi-?hats?\b|\bhats?\b|\bcymbals?\b|\bshaker\b"),
         ("tune", r"\bvocals?\b|\bvoice\b|\bvox\b|\bsung\b|\bchoir\b|\bchord\b|\bnote\b|\bstab\b|\bpluck\b|\bpad\b|\bkeys\b|\bpiano\b|\bstrings\b"),
         ("loop", r"\bloops?\b|\bbreaks?\b|\bbreakbeat\b|\bgroove\b|\brhythm\b|\bpercussion\b|\bdrums\b"))
WHERE = (("splice", r"\bsplice\b|\bmy (?:own )?(?:library|samples)\b"), ("bbc", r"\bbbc\b"), ("freesound", r"\bfreesound\b|\bfree sound\b"),
         ("internet_archive", r"\b(?:internet )?archive\b|\barchive\.org\b"), ("nasa", r"\bnasa\b|\bspace\b"))
# a typed line is a pull only if it opens with one of these verbs AND names a sound thing or a place to get it:
# "pull a knife on him" is story
_VERB = r"(?:(?:please|now|ok|okay|can you|could you)[ ,]+)*(?:pull(?: in| up)?|grab|fetch|find|dig (?:out|up)|download|load)\s+(?:me\s+|us\s+)?"
_THING = (r"\b(samples?|loops?|sounds?|noises?|breaks?|hits?|one[- ]?shots?|recordings?|kicks?|snares?|hi-?hats?|hats?|vocals?|vox|bass|pads?|"
          r"fx|ambien\w+|atmos\w*|textures?|drums?|percussion|splice|bbc|freesound|archive|nasa)\b")


def pull_in(text):
    """A typed line -> {"query", "role", "where"} if it asks for a sample to be pulled, else None."""
    line = " ".join(str(text).split())
    bare = re.match(r"^!\s*pull\b\s*(.+)$", line, re.I)
    said = re.match(r"^" + _VERB + r"(.+)$", line, re.I)
    if not bare and not (said and re.search(_THING, line, re.I)):
        return None
    what = (bare or said).group(1)
    called = re.search(r"\b(?:as|called|call it|named|name it)\s+([a-z][a-z0-9]{1,15})\s*$", what, re.I)     # "... as dust": the layer's name,
    if called:                                                                                                # read before the place is cut off
        what = what[:called.start()].strip()
    low = what.lower()
    role = next((name for name, pattern in ROLES if re.search(pattern, low)), "texture")
    where = next((name for name, pattern in WHERE if re.search(pattern, low)), "any")
    query = re.sub(r"\b(?:from|off|out of|on|in)\s+(?:the\s+)?(?:my\s+)?(?:splice|bbc|freesound|free sound|internet archive|archive(?:\.org)?|nasa|library)\b.*$",
                   "", what, flags=re.I)
    query = re.sub(r"^(?:a|an|some|another|the|any)\s+", "", query.strip(), flags=re.I)
    query = re.sub(r"\b(?:samples?|sounds?|recordings?|one[- ]?shots?|noises?)\b", " ", query, flags=re.I)
    query = " ".join(re.sub(r"[^\w\s'-]", " ", query).split())[:80]
    if not (query or role != "texture"):
        return None
    return {"query": query or role, "role": role, "where": where, "name": (called.group(1).lower() if called else layer_name(query or role))}


GENERIC = frozenset("a an the some any of on in at with and loop loops break breaks sample samples sound sounds one shot big small old new "
                    "heavy light dark bright my your kick snare hat hats sub bass tune bells drones clip sample "
                    "make me us give render film shoot get do please for to chop chopping chopped soundtrack track words too video "
                    "with nobody speaking invent short little bit something".split())


def layer_name(query):
    """What a pulled sample is called as a layer: the first telling word of what was asked for ("rain on a tin roof" -> rain)."""
    words = [w for w in re.findall(r"[a-z][a-z0-9]+", str(query).lower()) if w not in GENERIC]
    return (words[0] if words else "sample")[:16]


def safe_query(text, most=3):
    """What the story may ask an outside service for: at most `most` plain sound words from the list, or ''."""
    kept = []
    for word in re.findall(r"[a-z]+", str(text).lower()):
        if word in SAFE and word not in kept:
            kept.append(word)
    return " ".join(kept[:most])
