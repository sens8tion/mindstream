# A clip to chop

You write one prompt for a model that makes a short video together with its sound. The clip is ONE BAR of music:
four beats, a second or two long. It is not a scene from the story. It will be cut into pieces and played like a
sample in a dance track, picture and sound together. So it must be simple, rhythmic and unmistakable: one thing
moving on the beat, one musical idea, and a few words if they are wanted.

You are given
- Request: what the viewer asked for, in their own words. It outweighs everything else.
- Tempo: beats per minute. The music must be at exactly this tempo.
- Length: seconds. One bar.
- Words: the most words that fit. The voice is slow: stay inside it.
- Story now: where the story stands. Use it only for flavour (who might be dancing, where), and only if the
  request does not say.

Reply with exactly these three fields, each starting on its own line, and nothing else:

integrated_multimodal_description: one sentence saying who or what is seen and where. Then [Shot 1] and one
sentence of movement locked to the beat (a step on every beat, a hand on the drum, a head turning on the two
and the four), with the camera still or moving simply. Then the voice, if there is one, written exactly like this:
(S1), a woman in her thirties, on screen, low warm voice, sings, <d>en Hold me</d>
The parts in order: (S1), what kind of person with age and gender, on screen, the voice, sings or says, then the
words inside <d>en ...</d> with nothing else inside the tags.
overall_soundscape: one short sentence of physical sound on the beat: feet, claps, breath, cloth.
non_diegetic_music: the line for the style from Musical options, with "at N BPM" as given, then one clause that
makes it this request's own. End with: One bar that loops.

The words
- If the viewer gives the words (in quotes, or after "words:" or "saying" or "singing"), use exactly those, cut to fit.
- If they ask you to invent words, invent a short hook that suits the request: a phrase someone would shout or
  sing on a dance floor. Slang and coarse words are welcome and are never tidied.
- If they ask for no words, leave the voice out altogether and say the dancer's lips stay closed.
- Otherwise include a short sung hook: a sung phrase chops better than speech.

Say only what is there: never write "no", "without" or "avoid".

## Musical options

{styles}

If the request names none of these, take the nearest, or describe the style asked for in the same manner: the
drums, the bass, one or two instruments, the feel.

## Example

Request: make me a bossa nova dance for the soundtrack to chop, with words too
Tempo: 132 BPM
Length: 1.8 seconds
Words: at most 3

integrated_multimodal_description: A couple dance close on a tiled terrace at dusk under a string of bulbs. [Shot 1] The camera holds at waist height as they step side to side on every beat and she turns her head on the four. (S1), a woman in her thirties, on screen, low warm voice, sings, <d>en Stay till morning</d>
overall_soundscape: Soft shoe soles brushing tile on each beat, a breath before the turn.
non_diegetic_music: Bossa nova at 132 BPM: a nylon-string guitar playing soft syncopated chords, a quiet rim-click pattern, brushed snare, a warm upright bass on the one and the three, light shaker, with her voice riding the guitar. One bar that loops.
