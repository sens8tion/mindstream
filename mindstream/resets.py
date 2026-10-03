"""Phrases that ask for something to be done again from scratch: "replace all of the pics", "start the theme
again", "rebuild the musical intent", "reset the look", "redo everything". Plain pattern matching, so it acts
at once. It is deliberately narrow: only a short instruction that opens with the verb counts, so that a line
of story ("she replaces the photo on the wall") is left for the story.

    resets_in("replace all of the pics and rebuild the music")   ->   ["pictures", "music"]

The kinds are "pictures", "story", "music", "visuals"; "everything" comes back as all four.
"""
import re

KINDS = ("pictures", "story", "music", "visuals")
OPENING = r"^(?:(?:please|now|ok|okay|right|and|so|then|can you|could you|let'?s|just|go and|i want(?: you)? to|i'?d like(?: you)? to)[ ,]+)*"
# verbs that mean "again from scratch" on their own, and weaker ones that need "all", "again", "from scratch" ...
STRONG = (r"(?:replace|re-?do|refresh|re-?paint|renew|swap(?: out)?|re-?generate|re-?build|re-?make|re-?work|reset|re-?start|"
          r"re-?think|re-?score|re-?write|scrap|wipe|clear(?: out)?|bin|ditch)")
WEAK = r"(?:change|start|begin|do|make|paint|write|build|give me|try)"
FILLER = r"(?:(?:all|of|the|every|each|those|these|that|this|my|our|whole|entire|current|existing|old|present)\s+){0,4}"
OBJECTS = {
    "pictures": r"(?:pics?|pictures?|photos?|images?|imagery|paintings?|stills?)",
    "story": r"(?:theme|story|tale|narrative|plot)",
    "music": r"(?:music(?:al)?(?:\s+(?:intent|intention|idea|direction|score|side))?|score|sound(?:track)?|tune|drums|rhythm section|groove)",
    "visuals": r"(?:visuals?|motion|movement|look|effects?)",
    "all": r"(?:everything|it all|the lot|the whole (?:thing|lot|show))",
}
AGAIN = r"\b(?:again|afresh|anew|over|from scratch|from the (?:top|start|beginning)|all over)\b"


def _clause(text):
    words = text.split()
    if not words or len(words) > 12:
        return []
    found = []
    for kind, thing in OBJECTS.items():
        strong = re.match(OPENING + STRONG + r"\s+" + FILLER + thing + r"\b", text)
        weak = re.match(OPENING + WEAK + r"\s+" + FILLER + r"(?:new\s+|fresh\s+)?" + thing + r"\b", text)
        fresh = re.match(OPENING + r"(?:all\s+)?(?:new|fresh)\s+" + thing + r"\b", text) and kind != "story"
        if strong or fresh or (weak and (re.search(AGAIN, text) or re.search(r"\b(?:all|every|new|fresh)\b", text))):
            found.append(kind)
    if not found and re.match(OPENING + r"(?:(?:start|begin|go)\s+)?(?:again\s+)?from the (?:top|start|beginning)\s*$", text):
        found.append("story")
    return found


def resets_in(text):
    """Which things a typed line asks to have done again from scratch, in the order asked; [] if none."""
    low = " ".join(str(text).lower().replace("’", "'").split()).strip(" .!")
    kinds = []
    for clause in re.split(r"\s*(?:,|;|\band then\b|\bthen\b|\band\b|\bplus\b|&)\s*", low):
        for kind in _clause(clause.strip()):
            for one in (KINDS if kind == "all" else (kind,)):
                if one not in kinds:
                    kinds.append(one)
    return kinds
