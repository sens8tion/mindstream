"""Musical options: styles the film model can be asked to play, each as one line it understands (the drums,
the bass, an instrument or two, the feel). Used when a clip is asked for to chop ("make me a bossa nova dance
to chop"): llama is shown the menu, and without llama the line is looked up here. `{bpm}` is the session's tempo,
so whatever comes back sits on the rhythm section's beat.
"""
import re

STYLES = {
    "bossa nova": "Bossa nova at {bpm} BPM: a nylon-string guitar playing soft syncopated chords, a quiet rim-click pattern, brushed snare, "
                  "a warm upright bass on the one and the three, light shaker.",
    "samba": "Samba at {bpm} BPM: a rolling surdo bass drum, fast tamborim and shaker, a cavaquinho strumming bright chords, whistles.",
    "salsa": "Salsa at {bpm} BPM: congas and timbales on a clave rhythm, a piano montuno, punchy brass stabs, a walking bass.",
    "afrobeat": "Afrobeat at {bpm} BPM: an interlocking drum kit and shekere groove, a looping muted guitar line, a rubbery bass, short horn stabs.",
    "funk": "Funk at {bpm} BPM: a tight dry drum kit with a ghosted snare, a slapped bass line, a scratching wah guitar, clavinet stabs.",
    "disco": "Disco at {bpm} BPM: four-on-the-floor kick, open hi-hat on every off-beat, an octave-jumping bass, sweeping strings, a clap on two and four.",
    "house": "House music at {bpm} BPM: a punchy kick on every beat, a clap on two and four, an open hi-hat on every off-beat, a deep bass, "
             "a short piano or organ stab.",
    "techno": "Techno at {bpm} BPM: a hard relentless kick on every beat, a metallic hi-hat, a dark rumbling bass, one hypnotic synth note repeating.",
    "garage": "UK garage 2-step at {bpm} BPM: a skipping kick, a tight snare on two and four, swung shuffling hi-hats, a warm rolling sub bass, "
              "a chopped organ chord.",
    "drum and bass": "Drum and bass at {bpm} BPM: a fast rolling breakbeat with a snare cracking on two and four, a huge deep sub bass holding long notes.",
    "jungle": "Jungle at {bpm} BPM: a chopped, tumbling breakbeat, a booming reggae sub bass line, ragga stabs and sirens.",
    "dub": "Dub reggae at {bpm} BPM: a heavy one-drop drum beat, a huge slow bass line, an off-beat guitar skank drenched in echo.",
    "dancehall": "Dancehall at {bpm} BPM: a hard three-three-two drum pattern, a booming bass, sparse bright synth stabs.",
    "hip hop": "Hip hop at {bpm} BPM: a dusty boom-bap drum break, a deep round bass, a chopped piano loop, vinyl crackle.",
    "trap": "Trap at {bpm} BPM: a long booming 808 bass, a sparse hard kick, a clap on the three, fast rolling hi-hats, a dark bell melody.",
    "jazz": "Swing jazz at {bpm} BPM: a ride cymbal swinging, a walking double bass, a piano comping, brushes on the snare.",
    "flamenco": "Flamenco at {bpm} BPM: fierce strummed Spanish guitar, hand claps in a fast pattern, heel stamps, a cajon.",
    "tango": "Tango at {bpm} BPM: a bandoneon in sharp stabbing phrases, staccato strings, a piano and bass marching on every beat.",
    "gospel": "Gospel at {bpm} BPM: a choir in full harmony, hand claps on two and four, a Hammond organ, a driving bass and drums.",
    "rock": "Rock at {bpm} BPM: a loud live drum kit, a driving distorted guitar riff, a bass guitar locked to the kick.",
    "ambient": "Ambient music at {bpm} BPM, with a pulse but no drums: soft sustained synth chords, a low drone, a few glassy notes.",
}
ALIASES = {"bossanova": "bossa nova", "bossa": "bossa nova", "latin": "salsa", "2-step": "garage", "2 step": "garage", "two step": "garage",
           "uk garage": "garage", "dnb": "drum and bass", "d&b": "drum and bass", "drum n bass": "drum and bass", "reggae": "dub",
           "hip-hop": "hip hop", "hiphop": "hip hop", "boom bap": "hip hop", "swing": "jazz", "choir": "gospel", "guitar": "rock",
           "four on the floor": "house", "afro": "afrobeat"}


def find_style(text):
    """The first style named in a line of text, or None."""
    low = " " + re.sub(r"[^a-z0-9&\- ]", " ", str(text).lower()) + " "
    for name in sorted(list(STYLES) + list(ALIASES), key=len, reverse=True):
        if f" {name} " in low:
            return ALIASES.get(name, name)
    return None


def style_line(name, bpm):
    return STYLES[name].format(bpm=round(bpm))


def menu(bpm):
    """The options as llama is shown them."""
    return "\n".join(f"- {name}: {text.format(bpm=round(bpm))}" for name, text in STYLES.items())
