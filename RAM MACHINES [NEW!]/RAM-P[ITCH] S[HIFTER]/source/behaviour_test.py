#!/usr/bin/env python3
"""Behaviour tests of RAM-PS (frequencies within the shifter's window sidebands, about 3 %), run on the DSP code in the simulator (simrun.py),
checked against plain expectations: PTCH 96 plays an octave up, PTCH 32 an
octave down, PTC2 adds a second interval, HOLD keeps the last window after the
input changes, FB rings on after the input stops, ENTI swoops after a trig.
(The simulator's main output does not contain the machine's own output, so the
spiral through the main output is not part of these tests.)

  python behaviour_test.py [name ...]
"""
import math
import sys
from pathlib import Path

import simrun as sr

HERE = Path(__file__).resolve().parent
MDS = HERE / "sim_uncert.mds"
P = dict(PTCH=1, PTC2=2, ENTI=3, FB=4, DLAY=5, MODE=6, WIN=7, SCAT=8)
KIND = dict(PTCH="raw14", PTC2="raw14", ENTI="raw14", FB="q23", WIN="raw14", SCAT="q23", DLAY="q23", MODE="raw14")
BASE = dict(PTCH=96, PTC2=64, ENTI=64, FB=0, WIN=40, SCAT=0, DLAY=0, MODE=0)
T = 100                                 # the 16K ring is clear from block 64


def enc(**kw):
    return {P[k]: sr.encode(KIND[k], v, 120) for k, v in kw.items()}


def run(tag, settings, inp, blocks, events=None):
    pcm = [round(max(-1, min(1 - 2 ** -23, v)) * 0x7FFFFF) & 0xFFFFFF for v in inp]
    ev = {}
    for b, e in (events or {}).items():
        d = {}
        if "set" in e:
            d["params"] = enc(**e["set"])
        if "trig" in e:
            d["trig"] = e["trig"]
        ev[b] = d
    got, _ = sr.run(MDS, HERE / "sim" / tag, tag, enc(**dict(BASE, **settings)), ev, pcm, blocks)
    return [sr.s24(w) / 0x800000 for blk in got for w in blk]


def tones(blocks, parts):
    out, ph = [], 0.0
    for i in range(32 * blocks):
        hz = [h for b, h in parts if 32 * b <= i][-1]
        ph += 2 * math.pi * hz / 44100
        out.append(0.4 * math.sin(ph) if hz else 0.0)
    return out


def power(v, hz):
    c = sum(x * math.cos(2 * math.pi * hz * i / 44100) for i, x in enumerate(v))
    s = sum(x * math.sin(2 * math.pi * hz * i / 44100) for i, x in enumerate(v))
    return (c * c + s * s) / len(v) ** 2


def peak(v, lo=100, hi=3000, step=10):
    return max(range(lo, hi, step), key=lambda hz: power(v, hz))


def rms(v):
    return math.sqrt(sum(x * x for x in v) / max(1, len(v)))


ok = True


def check(name, cond, detail):
    global ok
    ok &= bool(cond)
    print(f"   {'OK  ' if cond else 'FAIL'} {name}: {detail}", flush=True)


def seg(v, b0, b1):
    return v[32 * b0:32 * b1]


def t_shift():
    inp = tones(300, [(0, 500)])
    up = run("up", {}, inp, 300)
    down = run("down", dict(PTCH=32), inp, 300)
    two = run("two", dict(PTC2=32), inp, 300)
    f1, f2 = peak(seg(up, 150, 290)), peak(seg(down, 150, 290))
    check("PTCH 96: an octave up", abs(f1 - 1000) <= 30, f"{f1} Hz from 500 Hz")
    check("PTCH 32: an octave down", abs(f2 - 250) <= 15, f"{f2} Hz")
    s = seg(two, 150, 290)
    a, b, c = power(s, 1000), power(s, 250), power(s, 500)
    check("PTC2 32 adds the octave below", a > 10 * c and b > 10 * c, f"1000 Hz {a:.2e}, 250 Hz {b:.2e}, 500 Hz {c:.2e}")
    peak_lvl = max(map(abs, two))
    check("output in range with both voices", peak_lvl < 1.0, f"peak {peak_lvl:.3f}")


def t_hold_fb():
    inp = tones(400, [(0, 500), (200, 700)])
    held = run("hold", {}, inp, 400, {190: dict(set=dict(MODE=1))})
    f = peak(seg(held, 250, 390))
    check("HOLD keeps playing the last window", abs(f - 1000) <= 50, f"{f} Hz while the input is 700 Hz")
    inp = tones(400, [(0, 500), (200, 0)])
    fb = run("fb", dict(FB=110), inp, 400)
    a, b = rms(seg(fb, 150, 190)), rms(seg(fb, 260, 300))
    nofb = run("nofb", {}, inp, 400)
    c = rms(seg(nofb, 260, 300))
    check("FB rings on after the input stops", b > 0.05 * a and c < 0.01 * a, f"{a:.3f} -> {b:.3f} (without FB {c:.4f})")


def t_enti():
    inp = tones(1000, [(0, 500)])
    got = run("enti", dict(ENTI=127, PTCH=64), inp, 1000, {200: dict(trig=0)})
    f0, f1 = peak(seg(got, 202, 212)), peak(seg(got, 900, 990))
    check("ENTI 127: a swoop up after the trig, back to PTCH", f0 > 650 and abs(f1 - 500) <= 10, f"{f0} Hz -> {f1} Hz")


def t_scat():
    inp = tones(400, [(0, 500)])
    plain = run("scat0", dict(WIN=90), inp, 400)
    scat = run("scat", dict(WIN=90, SCAT=127), inp, 400)
    d = rms([a - b for a, b in zip(seg(plain, 150, 390), seg(scat, 150, 390))])
    f = peak(seg(scat, 150, 390))
    check("SCAT 127: the heads land elsewhere, the pitch stays", d > 0.05 and abs(f - 1000) <= 30,
          f"difference {d:.3f}, {f} Hz")


TESTS = {"scat": t_scat, "shift": t_shift, "hold_fb": t_hold_fb, "enti": t_enti}

if __name__ == "__main__":
    for name in sys.argv[1:] or TESTS:
        print(name, flush=True)
        TESTS[name]()
    sys.exit(0 if ok else 1)
