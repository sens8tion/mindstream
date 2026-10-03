# The canon of feel

The words for how heavy dance music takes hold of someone, fixed so they can be a control pad. This page is
written out from `mindstream/feel.py` (`python -m mindstream.feel > FEEL.md`); change the canon there, not here.

Where it stands: the words, the rungs, how a line is read and what each feel asks of the engine are fixed here.
The engine does not act on them yet, and there is no pad on screen yet.

## Inversion

1. **Inverted praise.** On the dirty side, a word that would be a complaint anywhere else asks for *more*.
   "filthy", "disgusting", "punishing", "sick": none is ever read as a complaint.
2. **The inverse pole.** Every feel has an opposite with words of its own. To have less, say "less" or "too",
   or use the other pole: "cleaner", "gentler", "no menace". The inverse is not weakness: it is the breakdown,
   the held breath, what the drop is measured against.
3. **The flip.** "invert menace" swaps a feel for its inverse at the same depth. "invert" alone flips the whole
   pad, and again brings it back: the breakdown and the drop as one move.

## The pad

| | | |
|---|---|---|
| **weight** / weightless | **violence** / tender | **grit** / polish |
| **menace** / safe | **lock** / restless | **release** / tension |
| **filth** / clean | **swagger** / earnest | **derangement** / composed |

Rows: the body, the head, the attitude. Each pad stands on a rung from -4 (deep in its inverse) through 0 (not in
play) to 5. A press is a rung up; the inverse is a rung down; invert flips the sign.

## weight / weightless

Felt in the chest, not heard in the ears.

| Rung | Word | Also |
|---|---|---|
| +5 | **tectonic** | seismic, planetary |
| +4 | **crushing** | chest-rattling, colossal, monolithic |
| +3 | **thick** | dense, swollen, massive, leaden |
| +2 | **heavy** | weighty, subby, fat, deep |
| +1 | **solid** | grounded, sturdy |
| 0 | | not in play |
| -1 | **light** | lean, slim |
| -2 | **airy** | thin, hollow, breezy |
| -3 | **floating** | buoyant, drifting, hovering |
| -4 | **weightless** | featherlight, zero-gravity |

Nouns: weight, heft, pressure, bottom end, low end; for the inverse, lightness, air, weightless.

Asks of the engine, at the extreme: sub level +0.7; sub length +0.6; kick length +0.5; kick tone -0.3; bass tone -0.3; score sub +0.3.

## violence / tender

Taking a beating and wanting more.

| Rung | Word | Also |
|---|---|---|
| +5 | **merciless** | annihilating, obliterating, pitiless |
| +4 | **brutal** | ferocious, barbaric, murderous |
| +3 | **punishing** | pummelling, pummeling, savage, vicious |
| +2 | **bruising** | battering, hammering, thumping |
| +1 | **hard** | banging, slamming, pounding |
| 0 | | not in play |
| -1 | **soft** | easy, mild |
| -2 | **gentle** | kind, light-handed |
| -3 | **tender** | soothing, delicate |
| -4 | **caressing** | cradling, stroking |

Nouns: violence, aggression, punishment, force; for the inverse, tenderness, gentleness, tender.

Asks of the engine, at the extreme: kick punch +0.7; kick drive +0.3; kick level +0.3; snare punch +0.6; snare level +0.25; hats length -0.2; score energy +0.3.

## grit / polish

The surface of the sound itself: dry, mineral, damaged.

| Rung | Word | Also |
|---|---|---|
| +5 | **blown-out** | shredded, destroyed, pulverised, pulverized |
| +4 | **corroded** | rusty, scorched, eroded |
| +3 | **abrasive** | serrated, harsh, metallic, industrial, rasping |
| +2 | **gritty** | crunchy, fuzzy, distorted, grainy |
| +1 | **rough** | raw, coarse, lo-fi |
| 0 | | not in play |
| -1 | **smooth** | even, rounded |
| -2 | **silky** | sleek, velvet, satin |
| -3 | **polished** | glossy, hi-fi, lacquered |
| -4 | **glassy** | crystalline, mirror-finished |

Nouns: grit, dirt, crunch, distortion, texture; for the inverse, polish, sheen, gloss.

Asks of the engine, at the extreme: bass drive +0.5; tune drive +0.4; snare drive +0.3; hats drive +0.3; layers drive +0.4; hats tone +0.2.
Past 0.6 toward the feel: tune add_fx {'type': 'crush', 'bits': 6, 'rate': 0.3}.
Past 0.8 toward the feel: layers add_fx {'type': 'crush', 'bits': 5, 'rate': 0.25}.

## menace / safe

Unease: something is coming.

| Rung | Word | Also |
|---|---|---|
| +5 | **dread** | dreadful, doom-laden, apocalyptic, nightmarish |
| +4 | **sinister** | evil, claustrophobic, dystopian, malevolent |
| +3 | **ominous** | menacing, threatening, paranoid, cavernous |
| +2 | **brooding** | looming, bleak, murky, haunted |
| +1 | **uneasy** | moody, shadowy, dark, cold |
| 0 | | not in play |
| -1 | **calm** | settled, untroubled |
| -2 | **warm** | cosy, cozy, comforting |
| -3 | **friendly** | sunny, benign, welcoming |
| -4 | **safe** | sheltered, innocent |

Nouns: menace, dread, threat, darkness, doom; for the inverse, safety, warmth, comfort, safe.

Asks of the engine, at the extreme: tune tone -0.5; drones tone -0.4; drones level +0.4; bells level -0.5; snare room +0.4; tune room +0.3; layers room +0.3; score twinkle -0.3; look trails +0.15.
Past 0.4 toward the feel: score mode minor.
Past 0.5 toward the inverse: score mode major.

## lock / restless

Hypnotised: no longer counting bars.

| Rung | Word | Also |
|---|---|---|
| +5 | **relentless** | unrelenting, endless, unstoppable, remorseless |
| +4 | **hypnotic** | mesmeric, tunnelling, tunneling, trance-like, locked in |
| +3 | **driving** | grinding, insistent, motorik, locked |
| +2 | **rolling** | chugging, cruising, motoring |
| +1 | **steady** | even-paced, constant |
| 0 | | not in play |
| -1 | **loose** | relaxed, slack |
| -2 | **shifting** | wandering, changing |
| -3 | **restless** | fidgety, twitchy, skittish |
| -4 | **scattered** | broken, fractured, all over the place |

Nouns: lock, hypnosis, roll, drive, the groove; for the inverse, restlessness, variation, restless.

Asks of the engine, at the extreme: layers density -0.2; score swing -0.2; score twinkle -0.2; hats level +0.2; look calm +0.3.
Past 0.6 toward the feel: layers vary False.
Past 0.5 toward the inverse: layers vary True.

## release / tension

The drop as catharsis: hands up, eyes shut.

| Rung | Word | Also |
|---|---|---|
| +5 | **rapturous** | transcendent, heavenly, religious |
| +4 | **ecstatic** | delirious, tearful, overwhelming |
| +3 | **euphoric** | cathartic, blissful, elated, purging |
| +2 | **rushing** | soaring, surging, swelling |
| +1 | **lifting** | uplifting, rising, hopeful |
| 0 | | not in play |
| -1 | **held** | waiting, suspended |
| -2 | **tense** | taut, withheld, on edge, teasing |
| -3 | **coiled** | clenched, wound up, straining |
| -4 | **unbearable** | agonising, agonizing, excruciating |

Nouns: release, euphoria, lift, catharsis, the rush; for the inverse, tension, suspense, the wait.

Asks of the engine, at the extreme: tune level +0.3; tune tone +0.3; bells level +0.4; drones room +0.3; score twinkle +0.4; sub level +0.2; look chaos +0.4.
Past 0.6 toward the feel: tune set {'octave': 1}.
Past 0.5 toward the inverse: all add_fx {'type': 'filter', 'kind': 'high', 'freq': 400, 'q': 0.3}.
Past 0.75 toward the inverse: kick set {'on': False}.

## filth / clean

Disgust as praise: the bass face.

| Rung | Word | Also |
|---|---|---|
| +5 | **rancid** | putrid, revolting, septic, unholy |
| +4 | **dutty** | rank, stinking, vile, rotten |
| +3 | **filthy** | nasty, disgusting, gross, foul, minging |
| +2 | **grimy** | grotty, greasy, slimy, sleazy-sounding |
| +1 | **dirty** | mucky, grubby, naughty-sounding |
| 0 | | not in play |
| -1 | **decent** | tidy, polite |
| -2 | **clean** | proper-sounding, wholesome, fresh |
| -3 | **tasteful** | refined, elegant, classy |
| -4 | **pristine** | spotless, immaculate, hygienic |

Nouns: filth, stank, stink, muck, nastiness; for the inverse, cleanliness, taste, hygiene, clean.

Asks of the engine, at the extreme: bass drive +0.4; bass tone -0.2; sub drive +0.25; layers pitch -3; tune pitch -1.
Past 0.4 toward the feel: bass add_fx {'type': 'sweep', 'from': 2400, 'to': 180, 'time': '1/8'}.
Past 0.4 toward the feel: bass add_fx {'type': 'filter', 'kind': 'low', 'freq': 900, 'q': 0.8}.
Past 0.8 toward the feel: bass add_fx {'type': 'chorus', 'depth': 0.8, 'mix': 0.5}.

## swagger / earnest

Grinning: mischief and attitude.

| Rung | Word | Also |
|---|---|---|
| +5 | **lairy** | shameless, outrageous-sounding, gobby |
| +4 | **sleazy** | louche, lewd, seedy |
| +3 | **rude** | swaggering, strutting, bolshy |
| +2 | **naughty** | saucy, cocky, wonky, slinky |
| +1 | **cheeky** | playful, bouncy, jaunty |
| 0 | | not in play |
| -1 | **plain** | simple, modest |
| -2 | **straight** | sober, sincere |
| -3 | **earnest** | serious, stiff |
| -4 | **solemn** | po-faced, grave, austere |

Nouns: swagger, attitude, cheek, mischief, sleaze; for the inverse, earnestness, sincerity, earnest.

Asks of the engine, at the extreme: score swing +0.3; bass length -0.3; hats level -0.15; snare length +0.2.
Past 0.6 toward the feel: score style two_step.

## derangement / composed

Losing the plot on purpose.

| Rung | Word | Also |
|---|---|---|
| +5 | **demented** | psychotic, insane, possessed |
| +4 | **feral** | rabid, berserk, crazed, deranged |
| +3 | **unhinged** | mental, manic, frenzied, wild, chaotic |
| +2 | **twisted** | warped, bent, mangled |
| +1 | **odd** | strange, skewed, off |
| 0 | | not in play |
| -1 | **sane** | sensible, level |
| -2 | **orderly** | neat, measured |
| -3 | **composed** | controlled, rational |
| -4 | **disciplined** | regimented, clinical |

Nouns: derangement, madness, chaos, mayhem, insanity; for the inverse, composure, order, sanity, composed.

Asks of the engine, at the extreme: layers density +0.5; look chaos +0.6; look spin +0.4; tune pitch +2.
Past 0.4 toward the feel: layers chop finer.
Past 0.6 toward the feel: layers add_fx {'type': 'reverse'}.
Past 0.8 toward the feel: tune add_fx {'type': 'tremolo', 'time': '1/16', 'depth': 0.8}.

## Praise by insult

These have no feel of their own. Said alone, they push whichever feel was last touched one rung further:

sick, wicked, ill, bad, stupid, silly, ridiculous, ignorant, criminal, illegal, obscene, offensive, wrong, outrageous, absurd, dumb, daft, shocking, unreasonable, uncalled for, a disgrace, disgraceful.

## Saying it

    filthy                    to that rung; said again when already there, a rung further
    filthier / more filth     a rung up
    proper filthy             a rung further than the word (also: really, very, absolutely, well, dead ...)
    a bit filthier            half a rung
    less filth / too filthy   a rung back toward clean
    cleaner / pristine        the inverse pole, by its own words
    not filthy                the first rung of the inverse
    no filth                  out of play
    invert filth              the same depth, the other pole
    invert                    the whole pad
    !filth 3 / !menace -2     an exact rung
    filthier and heavier, less swagger       several at once

A line is feel talk only if every part of it is. A line of story that merely contains such words is left alone.
