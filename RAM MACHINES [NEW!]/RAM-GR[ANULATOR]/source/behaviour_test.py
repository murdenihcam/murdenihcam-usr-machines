#!/usr/bin/env python3
"""Behaviour tests of RAM-GF, run on the DSP code in the simulator (simrun.py),
checked against plain expectations: a trig freezes the recent input (it keeps
sounding at its pitch after the input changes), PTCH +12 doubles it, the next
trig freezes fresh audio, a retrig repeat keeps the frozen audio, LIVE follows
the input, and the output stays in range at full density.

  python behaviour_test.py [name ...]
"""
import math
import sys
from pathlib import Path

import simrun as sr

HERE = Path(__file__).resolve().parent
MDS = HERE / "sim_uncert.mds"
P = dict(PTCH=1, MODE=2, DEC=3, DENS=4, SEEK=5, SCAN=6, GRAN=7, SPRY=8)
KIND = dict(PTCH="raw14", MODE="raw14", DEC="raw14", DENS="raw14", SEEK="q23", SCAN="raw14", GRAN="sq23",
            SPRY="q23")
BASE = dict(PTCH=64, MODE=0, DEC=127, DENS=64, SEEK=0, SCAN=64, GRAN=64, SPRY=0)
BPM = 300
T = 140                                 # the 16K ring is clear from block 64; 2204 frames by 133
REPEAT = 0x010000


def enc(**kw):
    return {P[k]: sr.encode(KIND[k], v, BPM) for k, v in kw.items()}


def run(tag, settings, inp, blocks, events):
    pcm = [round(max(-1, min(1 - 2 ** -23, v)) * 0x7FFFFF) & 0xFFFFFF for v in inp]
    ev = {}
    for b, e in events.items():
        d = {}
        if "set" in e:
            d["params"] = enc(**e["set"])
        if "trig" in e:
            d["trig"] = e["trig"]
        ev[b] = d
    got, _ = sr.run(MDS, HERE / "sim" / tag, tag, enc(**dict(BASE, **settings)), ev, pcm, blocks)
    return [sr.s24(w) / 0x800000 for blk in got for w in blk]


def tones(blocks, parts):
    """parts: [(from block, hz)]: a sine that changes frequency at those blocks (0 Hz = silence)."""
    out, ph = [], 0.0
    for i in range(32 * blocks):
        hz = [h for b, h in parts if 32 * b <= i][-1]
        ph += 2 * math.pi * hz / 44100
        out.append(0.4 * math.sin(ph) if hz else 0.0)
    return out


def peak_freq(v):
    """The strongest frequency in 25 Hz steps (grain seams make zero crossings unreliable)."""
    best, bf = 0, 0
    for hz in range(100, 4000, 25):
        c = sum(x * math.cos(2 * math.pi * hz * i / 44100) for i, x in enumerate(v))
        s = sum(x * math.sin(2 * math.pi * hz * i / 44100) for i, x in enumerate(v))
        if c * c + s * s > best:
            best, bf = c * c + s * s, hz
    return bf


def rms(v):
    return math.sqrt(sum(x * x for x in v) / max(1, len(v)))


ok = True


def check(name, cond, detail):
    global ok
    ok &= bool(cond)
    print(f"   {'OK  ' if cond else 'FAIL'} {name}: {detail}", flush=True)


def seg(v, b0, b1):
    return v[32 * b0:32 * b1]


def t_freeze():
    # A = 1 kHz until the trig, then silence; at 400 B = 500 Hz; trig at 600, retrig repeat at 700, trig at 800
    inp = tones(900, [(0, 1000), (T, 0), (400, 500)])
    ev = {T: dict(trig=0), 600: dict(trig=0), 700: dict(trig=REPEAT, set=dict(PTCH=64)), 800: dict(trig=0)}
    ev[350] = dict(set=dict(PTCH=88))
    ev[400] = dict(set=dict(PTCH=64))
    got = run("freeze", {}, inp, 900, ev)
    late = seg(got, 300, 340)            # over 2 s after the trig, input silent
    check("a trig freezes the input", rms(late) > 0.05 and abs(peak_freq(late) - 1000) <= 25,
          f"level {rms(late):.3f}, {peak_freq(late)} Hz, 2.3 s after the trig")
    up = seg(got, 360, 395)
    check("PTCH 88 plays it an octave up", abs(peak_freq(up) - 2000) <= 25, f"{peak_freq(up)} Hz")
    held = seg(got, 450, 550)
    check("the frozen audio ignores the new input", abs(peak_freq(held) - 1000) <= 25, f"{peak_freq(held)} Hz")
    fresh = seg(got, 620, 690)
    check("the next trig freezes fresh audio", abs(peak_freq(fresh) - 500) <= 25, f"{peak_freq(fresh)} Hz")
    rep = seg(got, 720, 790)
    check("a retrig repeat keeps the frozen audio", abs(peak_freq(rep) - 500) <= 25 and rms(rep) > 0.05,
          f"{peak_freq(rep)} Hz, level {rms(rep):.3f}")
    peak = max(map(abs, got))
    check("output in range", peak < 1.0, f"peak {peak:.3f}")


def t_live():
    inp = tones(500, [(0, 1000), (300, 600)])
    got = run("live", dict(SCAN=0, DENS=127, SPRY=40), inp, 500, {T: dict(trig=0)})
    a, b = seg(got, 200, 290), seg(got, 400, 490)
    check("LIVE follows the input", abs(peak_freq(a) - 1000) <= 25 and abs(peak_freq(b) - 600) <= 25,
          f"{peak_freq(a)} Hz then {peak_freq(b)} Hz")
    check("LIVE output in range", max(map(abs, got)) < 1.0, f"peak {max(map(abs, got)):.3f}")


def t_dense():
    inp = tones(400, [(0, 700), (T, 0)])
    got = run("dense", dict(DENS=127, GRAN=0, SPRY=127, SCAN=100), inp, 400, {T: dict(trig=0)})
    s = seg(got, 200, 390)
    check("full density, short grains, full spray: sound in range", 0.03 < rms(s) and max(map(abs, s)) < 1.0,
          f"level {rms(s):.3f}, peak {max(map(abs, s)):.3f}")


def t_hold():
    # A until 300, then B; MODE HOLD from 250; trig at 400 must freeze A (recorded before the hold)
    inp = tones(520, [(0, 1000), (300, 500)])
    got = run("hold", {}, inp, 520, {T: dict(trig=0), 250: dict(set=dict(MODE=1)), 400: dict(trig=0)})
    s = seg(got, 420, 510)
    check("HOLD stops recording: a trig freezes audio from before it", abs(peak_freq(s) - 1000) <= 25, f"{peak_freq(s)} Hz")


TESTS = {"hold": t_hold, "freeze": t_freeze, "live": t_live, "dense": t_dense}

if __name__ == "__main__":
    for name in sys.argv[1:] or TESTS:
        print(name, flush=True)
        TESTS[name]()
    sys.exit(0 if ok else 1)
