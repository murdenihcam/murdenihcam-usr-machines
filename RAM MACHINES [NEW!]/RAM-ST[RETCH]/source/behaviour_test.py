#!/usr/bin/env python3
"""Behaviour checks of the RAM-ST model (bit-exact with the DSP, see simtest.py):
what a trig plays must be the recent input at the right pitch and level, at
every capture rate D, and a slowed take must keep its pitch.

  python behaviour_test.py
"""
import math

import ram_stretch_model as m

LENT = (0x180000, 0x10000)        # 64K ring, CAP 63,488 frames


def tone(n, hz, amp=0.5):
    return [round(amp * math.sin(2 * math.pi * hz * i / 44100) * 0x7FFFFF) & 0xFFFFFF for i in range(n)]


def run(inp, trig_block, blocks, **params):
    t = m.Track(0)
    t.set_params(**params)
    out = []
    for b in range(blocks):
        if b == trig_block:
            t.trig()
        blk = inp[32 * b:32 * b + 32] if 32 * b < len(inp) else [0] * 32
        out += t.render([w for w in blk for _ in (0, 1)], LENT)   # the same on left and right
    return t, out


def power(v, hz):
    c, s = 0.0, 0.0
    for i, x in enumerate(v):
        c += x * math.cos(2 * math.pi * hz * i / 44100)
        s += x * math.sin(2 * math.pi * hz * i / 44100)
    return c * c + s * s


def freq(words):
    """The strongest frequency (0.5 Hz steps near the zero-crossing estimate): splice
    crossfades add zero crossings, so the spectrum peak is the pitch."""
    v = [m.s24(w) for w in words][:16384]
    ups = [i for i in range(1, len(v)) if v[i - 1] < 0 <= v[i]]
    guess = (len(ups) - 1) * 44100 / (ups[-1] - ups[0]) if len(ups) > 2 else 0
    cands = [guess * (1 + k / 400) for k in range(-40, 41)]
    return max(cands, key=lambda hz: power(v, hz)) if guess else 0


def rms_db(words):
    v = [m.s24(w) / 0x7FFFFF for w in words]
    return 10 * math.log10(sum(x * x for x in v) / len(v) + 1e-20)


ok = True


def check(name, cond, detail):
    global ok
    ok &= cond
    print(f"   {'OK  ' if cond else 'FAIL'} {name}: {detail}")


if __name__ == "__main__":
    # REC: the take is the buffer, at most half the ring, at 44.1 kHz (HOLD: all of it)
    inp = tone(32 * 2600, 440)
    t, out = run(inp, 2400, 2700, gran=40)
    seg = out[2420 * 32:2680 * 32]
    f, lvl = freq(seg), rms_db(seg) - rms_db(inp[:44100])
    check("REC take = half the ring", t.y[m.S_LEN] == t.y[m.S_RM] >> 1 and abs(f - 440) < 3 and abs(lvl) < 1.0,
          f"take {t.y[m.S_LEN]} frames ({t.y[m.S_LEN] / 44100:.2f} s), played {f:.1f} Hz, level {lvl:+.2f} dB")
    # HOLD stops recording; a later trig still plays the held audio
    inp = tone(32 * 600, 440) + tone(32 * 600, 1000)
    t = m.Track(0); t.set_params(gran=127)
    out = []
    for b in range(1200):
        if b == 590:
            t.set_params(mode=1, gran=127)
        if b == 900:
            t.trig()
        blk = inp[32 * b:32 * b + 32]
        out += t.render([w for w in blk for _ in (0, 1)], LENT)
    f = freq(out[905 * 32:1100 * 32])
    check("HOLD keeps the old audio", abs(f - 440) < 3, f"input now 1000 Hz, trig played {f:.1f} Hz")
    # MREC: records with the output muted; HOLD then plays what it recorded
    inp = tone(32 * 1200, 660)
    t = m.Track(0); t.set_params(mode=2, gran=127)
    out = []
    for b in range(1200):
        if b in (700, 1000):
            t.trig()
        if b == 900:
            t.set_params(mode=1, gran=127)
        out += t.render([w for w in inp[32 * b:32 * b + 32] for _ in (0, 1)], LENT)
    muted = max(abs(m.s24(w)) for w in out[:1000 * 32])
    f = freq(out[1005 * 32:1190 * 32])
    check("MREC mutes, HOLD plays it", muted == 0 and abs(f - 660) < 4, f"MREC peak {muted}, HOLD trig {f:.1f} Hz")
    # TIME 42 (half speed) keeps the pitch; PTCH 88 (+12 semitones) doubles it
    inp = tone(32 * 900, 440)
    for name, params, want in (("TIME 42 keeps pitch", dict(time=42), 440), ("PTCH 88 = +12 st", dict(ptch=88), 880)):
        t, out = run(inp, 600, 900, gran=127, **params)  # short grains shift the peak (as on SMP-ST)
        f = freq(out[620 * 32:890 * 32])
        check(name, abs(f - want) < want * 0.01, f"{f:.1f} Hz")
    # the take is the recent input: no stretch -> the input of FILL frames ago
    inp = tone(32 * 700, 1000, 0.3)
    t, out = run(inp, 600, 700, gran=127)
    n = t.y[m.S_LEN]
    start = 600 * 32 - n
    err = max(abs(m.s24(out[600 * 32 + k]) - m.s24(inp[start + k])) for k in range(64, 2000))
    check("take = recent input", err < 0x7FFFFF * 0.02, f"take {n} frames, max error {err / 0x7FFFFF:.4f}")
    raise SystemExit(0 if ok else 1)
