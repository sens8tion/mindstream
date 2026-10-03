"""How a piece of sound is chopped: where it is cut, and what is played when.

It is cut where things begin in it (a word, a syllable, a hit), never at blind distances. Then four bars are
planned, a phrase at a time, the way someone at a sampler would play it:

- bar 1 states a run of slices in their own order, starting on the one, the rest placed in the gaps the kick
  leaves, so the voice and the drums answer each other instead of piling up;
- bar 2 says it again with one thing changed: the hardest-hitting slice lands on the snare;
- bar 3 is bar 1 again;
- bar 4 turns round: half of bar 1, then the first slice stuttered faster and faster into the next phrase (or,
  when things are quiet, left empty so the return has room).

A slice is played for its own length and then stops, so the next word does not leak in unless things are busy
enough to let it run on. Each new phrase starts further into the sound, so over time the whole of it is heard.
The plan depends only on the sound, the drum pattern, how busy things are and which phrase it is: the same
moment always chops the same way, and changing any of those changes it.

No numpy here; the measuring of slices is in `measure`, which takes the audio.

`plan` is the old four-bar form (A A' A B), which the research measured and rejected; the chop engine that replaces
it is chopper.py, which uses what `measure` finds out about each slice. `plan` stays until nothing calls it.
"""


def measure(mono, rate, starts):
    """What each slice is like, for slices beginning at `starts`: [{"pos", "len", "level", "punch", "tonal", "low",
    "bright", "attack", "rise"}].

    level   how loud it is overall (RMS)
    punch   how hard its first 25 ms hits (the peak there)
    tonal   how much of it is pitch rather than noise, times its level
    low     the share of its sound below 150 Hz: the weight of a kick, the body of a bass note (0 to 1)
    bright  where the middle of its spectrum sits, in Hz: a snare or a consonant high, a kick or a vowel low
    attack  how much louder its first 30 ms are than the 90 ms after them: well over 1 for a hit, about 1 or less
            for a held sound or a swell (measured the same way whatever the slice's length)
    rise    seconds from its start to its loudest moment: a hit peaks at once, a pad swells
    """
    import numpy as np
    out = []
    head_n, body_n, frame = max(int(rate * 0.025), 1), max(int(rate * 0.03), 1), max(int(rate * 0.005), 1)
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(mono)
        piece = np.asarray(mono[start:end], dtype=np.float64)
        if len(piece) < rate // 40:
            continue
        level = float(np.sqrt((piece ** 2).mean()))
        head = float(np.abs(piece[:head_n]).max())
        n = min(len(piece), int(rate * 0.3))
        spec = np.abs(np.fft.rfft(piece[:n] * np.hanning(n)))
        mag = spec[2:] + 1e-9
        flat = float(np.exp(np.log(mag).mean()) / mag.mean())
        freqs = np.fft.rfftfreq(n, 1.0 / rate)[2:]
        power = mag ** 2
        frames = len(piece[:int(rate * 0.5)]) // frame
        env = np.sqrt((piece[:frames * frame].reshape(frames, frame) ** 2).mean(axis=1)) if frames else np.zeros(1)
        after = piece[body_n:body_n * 4] if len(piece) >= body_n * 3 // 2 else piece
        out.append({"pos": int(start), "len": int(len(piece)), "level": level, "punch": head / (level + 1e-6) * level,
                    "tonal": (1.0 - flat) * level,
                    "low": float(power[freqs < 150].sum() / power.sum()),
                    "bright": float((freqs * mag).sum() / mag.sum()),
                    "attack": float(np.sqrt((piece[:body_n] ** 2).mean()) / (np.sqrt((after ** 2).mean()) + 1e-9)),
                    "rise": float(np.argmax(env) * frame / rate)})
    return out


def plan(cuts, kick, snare, density, phrase, slot_len, busy=False, turn=0):
    """Four bars of chopping: a list of 64 sixteenth-note entries, each an index into `cuts` (play that slice
    from its start), "rest" (silence from here) or None (carry on as you are).

    cuts: from `measure`. kick, snare: the sixteenths (0 to 15) the drums fall on. density: 0 sparse to 1 dense.
    phrase: which four-bar phrase this is (0, 1, 2 ...). slot_len: samples in a sixteenth. busy: use the odd
    sixteenths as well. turn: the same slices put in other places (0 = where they would first go): each turn moves
    which gaps are used and which slice leads."""
    n = len(cuts)
    if n == 0:
        return [None] * 64
    density = min(max(float(density), 0.0), 1.0)
    width = min(n, 2 + round(4 * density))                       # how many consecutive slices this phrase works with
    span, stride = n - width + 1, max(width - 1, 1)              # the places a run of that many slices can start
    anchor = (phrase * (1 if stride % span == 0 else stride)) % span   # each phrase starts further into the sound
    window = list(range(anchor, anchor + width))
    if span == 1 and width > 1:                                  # the whole sound is in play: lead with a different slice each phrase
        window = window[phrase % width:] + window[:phrase % width]
    hit = max(range(n), key=lambda i: cuts[i]["punch"])
    # where slices may land, best first: the gaps the kick leaves, then the snare, then the strong beats, then the rest
    order = [s for s in (2, 6, 10, 14) if s not in kick] + [s for s in snare if s not in (2, 6, 10, 14)] + [8, 4, 12]
    order += [s for s in range(0, 16, 2) if s not in order and s != 0]
    if busy or density > 0.75:
        order += [s for s in range(1, 16, 2)]
    order = list(dict.fromkeys(order))
    if turn and order:                                            # the same slices, repositioned: other gaps first, another slice leading
        order = order[turn % len(order):] + order[:turn % len(order)]
        window = window[turn % len(window):] + window[:turn % len(window)]
    count = min(1 + round(5 * density) + (3 if busy else 0), len(order))
    slots = [0] + sorted(order[:count])

    def bar(sequence, upto=16):
        out = [None] * 16
        for j, slot in enumerate(s for s in slots if s < upto):
            which = sequence[j % len(sequence)]
            out[slot] = which
            ends = slot + max(1, -(-cuts[which]["len"] // max(slot_len, 1)))       # the sixteenth after the slice is over
            later = [s for s in slots if s > slot and s < upto]
            if density < 0.7 and ends < (later[0] if later else 16) and out[ends] is None:
                out[ends] = "rest"                                # it stops there: the next word does not leak in
        return out

    first = bar(window)
    varied = list(window)
    if len(varied) > 2:
        varied[-1], varied[-2] = varied[-2], varied[-1]
    second = bar(varied)
    on_snare = [s for s in snare if s in slots]
    if on_snare:
        second[on_snare[-1]] = hit                                # the hardest slice lands on the backbeat
    last = bar(window, upto=8)
    if density < 0.3:
        last[8] = "rest"                                          # quiet: leave the end of the phrase empty
    else:
        for slot in (8, 10, 12, 13, 14, 15):                      # a stutter that quickens into the next phrase
            last[slot] = window[0]
    return first + second + list(first) + last
