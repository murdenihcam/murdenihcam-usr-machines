#!/usr/bin/env python3
"""Bit-exact model of ram_stretch.asm56k (RAM-ST), for checking the DSP code and for listening.

The model repeats the machine's integer arithmetic step by step, so the simulator
output must match it word for word (see simtest.py). The stretch engine is the
SMP-ST one; what is new is the ring in lent RAM-slot memory, the capture of
the main output and the take latched at TRIG. It can also render a WAV: the input WAV is the
main output (mono, as both channels), and a trig every --every sixteenths at --bpm
plays the whole buffer:

  python ram_stretch_model.py in.wav out.wav --time 42 --bpm 120 --every 16
"""
import argparse
import wave

from gen_tables import DECAY, PITCH, QTR, SPEED

M24 = 0xFFFFFF
(P_PTCH, P_MODE, P_DEC, P_TIME, P_STRT, P_END, P_GRAN, P_FLUX, T_SCR, S_ACT, S_GI, S_GF, S_PI, S_PF,
 S_LO, S_HI, S_WIN, S_STEP, S_CNT, S_GAIN, S_SEED, S_SLOT, S_REV, S_MIR, S_ENV, S_REL, S_FADE, S_OGI,
 S_OGF, T_RGI, T_RGF, T_RQ, T_F, T_OCT, T_VBI, T_VBF, T_RPQ, T_G0, T_G1, T_CO0, T_COS, T_CN0, T_CNS,
 T_K, T_GRAN, T_L64, T_J, T_CTR, T_R2I, T_R2F, S_RB, S_RM, S_CLR, S_W, S_FILL, S_SINCE, S_D, S_PH,
 S_LP, S_WOFF, S_CAP, S_LEN, S_LFR) = range(1, 64)
SEED0 = 0x2A5B3D
ONE = 0x7FFFFF
MIN_WIN = 64
RING_MAX, RING_MIN, CHUNK, MARGIN = 0x40000, 0x4000, 256, 2048


def s24(v):
    v &= M24
    return v - (1 << 24) if v & 0x800000 else v


def acc(word):                 # move word,a: into A1, sign-extended, A0 cleared
    return s24(word) << 24


def hi(a):                     # A1
    return (a >> 24) & M24


def lo(a):                     # A0
    return a & M24


def mpy(x, y):                 # fractional multiply: A = 2 * x * y
    return 2 * s24(x) * s24(y)


def lim(a):                    # move a,dest: saturate to 48 bits, take A1
    a = max(-(1 << 47), min((1 << 47) - 1, a))
    return hi(a)


class Track:
    """One track: Y:(r6+0..63) as self.y; mem is the external memory (dict)."""

    def __init__(self, track=0, mem=None):
        self.y = [0] * 64
        self.mem = {} if mem is None else mem
        self.init(track)

    def set_params(self, ptch=64, mode=0, dec=127, time=0, strt=0, end=127, gran=64, flux=0):
        y = self.y
        y[P_PTCH] = ptch * 128                       # raw14
        y[P_MODE] = (63 + mode) * 128                # raw14: 63 REC, 64 HOLD, 65 MREC (mode 0/1/2)
        y[P_DEC] = dec * 128
        y[P_TIME] = time * 128
        y[P_STRT] = strt << 16                       # unipolar Q23
        y[P_END] = end << 16
        y[P_GRAN] = (gran * gran) << 9               # squared Q23
        y[P_FLUX] = flux << 16

    def init(self, track):
        y = self.y
        for i in (S_ACT, S_GAIN, S_CNT, S_REL, S_FADE, S_RB, S_RM, S_FILL, S_SINCE, S_CAP,
                  S_LEN, S_LFR):
            y[i] = 0
        y[S_SEED] = (track + SEED0) & M24
        y[S_SLOT] = track & 3

    def hold(self):
        return 8192 - 64 <= s24(self.y[P_MODE]) <= 8192 + 64

    def gran_len(self):
        return hi(mpy(4776, self.y[P_GRAN]) + acc(300))

    def rand(self):
        y = self.y
        a = mpy(y[S_SEED], 0x19660D) >> 1
        y[S_SEED] = hi(acc(lo(a)) + acc(0x6EF35F))
        return y[S_SEED]

    def trig(self, info=0):
        """info: the TRIGGER_INFO word (bit 16 = a retrig repeat)."""
        y = self.y
        if y[S_RB] == 0:
            y[S_ACT] = 0
            return
        keep = False
        if info & 0x010000 and acc(y[S_LEN]) >= acc(MIN_WIN):
            keep = acc(y[S_LEN]) + acc(y[S_SINCE]) <= acc(y[S_CAP])
        if not keep:
            n = y[S_FILL]                            # HOLD: the whole buffer
            if not self.hold():
                half = y[S_RM] >> 1                  # REC: at most half the ring
                if acc(n) > acc(half):
                    n = half
            y[S_LEN] = n
            y[S_WOFF] = (y[S_W] - n) & y[S_RM] & M24
            y[S_SINCE] = 0
            y[S_STEP] = 0x010000
        length = y[S_LEN]
        if length == 0:
            y[S_ACT] = 0
            return

        def frame_at(u):
            return length if acc(u) >= acc(0x7F0000) else hi(mpy(length, u))
        start, end = frame_at(y[P_STRT]), frame_at(y[P_END])
        y[S_REV] = int(acc(end) < acc(start))
        if y[S_REV]:
            y[S_LO], y[S_HI] = end, start
        else:
            y[S_LO], y[S_HI] = start, end
        y[S_GI] = y[S_PI] = y[S_LO]
        y[S_MIR] = hi(acc(y[S_LO]) + acc(y[S_HI]) - acc(1))
        b = acc(y[S_HI]) - acc(y[S_LO])
        y[S_WIN] = hi(b)
        if b < acc(MIN_WIN):
            y[S_ACT] = 0
            return
        y[S_GF] = y[S_PF] = y[S_REL] = y[S_FADE] = 0
        y[S_CNT] = self.gran_len()
        y[S_ENV] = y[S_GAIN] = ONE
        y[S_ACT] = 1

    def splice(self):
        y = self.y
        y[S_FADE] = 1
        y[S_OGI], y[S_OGF] = y[S_GI], y[S_GF]
        u = self.rand()
        y[T_K] = hi(mpy(hi(mpy(y[P_FLUX], 0x600000)), u))
        g = self.gran_len()
        y[T_GRAN] = g
        y[T_L64] = hi(acc(g) << 6)
        y[T_J] = hi(mpy(y[T_L64], y[T_RQ]))
        jp = hi(mpy(y[T_L64], y[T_RPQ]))
        y[T_CTR] = hi((acc(y[T_J]) - acc(jp)) >> 1)
        b = mpy(y[T_J], y[T_K])
        b = (b & ~M24) | y[S_PF]
        b += acc(y[S_PI])
        b -= acc(y[T_CTR])
        if b < acc(y[S_LO]):
            b = acc(y[S_LO])
        top = hi(acc(y[S_HI]) - acc(1))
        if b > acc(top):
            b = acc(top)
        y[S_GI], y[S_GF] = hi(b), lo(b)
        u = self.rand()
        k1 = hi(mpy(hi(mpy(y[P_FLUX], 0x300000)), u))
        y[S_CNT] = hi(mpy(y[T_GRAN], k1) + acc(y[T_GRAN]) + acc(y[S_CNT]))

    def grain(self, gi, gf):
        """32 PCM words of the grain at gi.gf and the next position (POSGEN + RREAD)."""
        y = self.y
        a = acc(gi) + gf
        x = acc(y[T_RGI]) + y[T_RGF]
        if y[S_REV]:
            a = acc(y[S_MIR]) - a
            x = -x
        pcm = []
        for _ in range(32):
            addr = ((hi(a) + y[S_WOFF]) & y[S_RM]) | y[S_RB]
            pcm.append(self.mem.get(addr, 0))
            a += x
        if y[S_REV]:
            a = acc(y[S_MIR]) - a
        return pcm, a

    def ring(self, lent):
        """RAM_WORKSPACE result (first word, words) -> ring ok (True) or silent block (False)."""
        y = self.y
        first, words = lent
        if first == 0:
            y[S_RB] = y[S_RM] = y[S_LEN] = 0
            y[S_SLOT] = (y[S_SLOT] + 1) & 3          # try the next slot
            return False
        end = first + words
        p = RING_MAX
        while True:
            if p < RING_MIN:
                y[S_RB] = y[S_RM] = y[S_LEN] = 0
                y[S_SLOT] = (y[S_SLOT] + 1) & 3
                return False
            base = (first + p - 1) & ~(p - 1) & M24
            if base + p <= end:
                break
            p >>= 1
        if base != y[S_RB] or p - 1 != y[S_RM]:
            y[S_RB], y[S_RM], y[S_CAP] = base, p - 1, p - MARGIN
            y[S_CLR] = y[S_W] = y[S_FILL] = y[S_LEN] = y[S_ACT] = 0
        if y[S_CLR] < p:
            for k in range(CHUNK):
                self.mem[y[S_RB] + y[S_CLR] + k] = 0
            y[S_CLR] += CHUNK
            return False
        return True

    def capture(self, inp):
        """This block's 32 frames (mono) into the ring; MODE HOLD records nothing."""
        y = self.y
        if self.hold():
            return
        for i, f in enumerate(inp):
            self.mem[y[S_RB] + ((y[S_W] + i) & y[S_RM])] = f
        y[T_SCR] = 32
        y[S_W] = (y[S_W] + 32) & y[S_RM]
        y[S_FILL] = min(y[S_FILL] + 32, y[S_CAP])
        y[S_SINCE] = min(y[S_SINCE] + 32, y[S_CAP])

    def render(self, inp, lent):
        """inp: this block's main output, 32 left/right pairs (64 words);
        lent: RAM_WORKSPACE (first word, words)."""
        y = self.y
        if not self.ring(lent):
            y[S_ACT] = 0
            return [0] * 32
        self.capture([hi((acc(inp[2 * k]) + acc(inp[2 * k + 1])) >> 1) for k in range(32)])
        if s24(y[P_MODE]) > 8192 + 64:               # MREC: muted, the voice ends
            y[S_ACT] = 0
            return [0] * 32
        if y[S_ACT] == 0:
            return [0] * 32
        fading = y[S_FADE] != 0
        if not fading:
            a = (acc(y[P_PTCH]) - acc(8192)) >> 1
            a = max(acc(-4096), min(acc(4095), a))
            s = s24(hi(a)) >> 7
            y[T_F] = ((hi(a) & 0x7F) << 16) & M24
            t = s + 72
            y[T_OCT] = octave = hi(mpy(t, 0x0AAAAB))
            n = t - 12 * octave
            m0, m1 = PITCH[n], PITCH[n + 1]
            m = hi(mpy(y[T_F], hi(acc(m1) - acc(m0))) + acc(m0))
            a = mpy(y[S_STEP], m) >> (20 - octave)
            y[T_RGI], y[T_RGF] = hi(a), lo(a)
            y[T_RQ] = hi(a << 17)
            speed = SPEED[max(0, min(127, s24(hi(acc(y[P_TIME]) >> 7))))]
            a = mpy(y[S_STEP], speed) >> 1
            y[T_VBI], y[T_VBF] = hi(a), lo(a)
            y[T_RPQ] = hi(a << 12)
        if y[S_REL]:
            y[S_REL] += 1
        elif acc(y[S_PI]) >= acc(y[S_HI]):
            y[S_REL] = 1
        d = max(0, min(127, s24(hi(acc(y[P_DEC]) >> 7))))
        mul = DECAY[d]
        env = y[S_ENV] if mul == ONE else hi(mpy(y[S_ENV], mul))
        y[S_ENV] = env
        if acc(env) < acc(0x40):
            y[S_ACT] = 0
        y[T_G1] = hi(mpy(env, QTR[y[S_REL]]))
        y[T_G0] = y[S_GAIN]
        y[S_GAIN] = y[T_G1]
        if y[S_REL] >= 4:
            y[S_ACT] = 0
        g0, g1 = y[T_G0], y[T_G1]
        if fading:
            j = y[S_FADE] - 1
            b = mpy(g0, QTR[j])
            y[T_CO0] = hi(b)
            y[T_COS] = hi((mpy(g1, QTR[j + 1]) - b) >> 5)
            b = mpy(g0, QTR[4 - j])
            y[T_CN0] = hi(b)
            y[T_CNS] = hi((mpy(g1, QTR[3 - j]) - b) >> 5)
        else:
            y[T_CN0] = g0
            y[T_CNS] = hi((acc(g1) - acc(g0)) >> 5)
        out = [0] * 32
        if fading:
            pcm, a = self.grain(y[S_OGI], y[S_OGF])
            y[S_OGI], y[S_OGF] = hi(a), lo(a)
            b = acc(y[T_CO0])
            for k in range(32):
                out[k] = lim(mpy(pcm[k], hi(b)))
                b += acc(y[T_COS])
        pcm, a = self.grain(y[S_GI], y[S_GF])
        y[S_GI], y[S_GF] = hi(a), lo(a)
        b = acc(y[S_PI]) + y[S_PF] + acc(y[T_VBI]) + y[T_VBF]
        y[S_PI], y[S_PF] = hi(b), lo(b)
        b = acc(y[T_CN0])
        for k in range(32):
            a = mpy(pcm[k], hi(b))
            if fading:
                a += acc(out[k])
            b += acc(y[T_CNS])
            out[k] = lim(a)
        if fading:
            y[S_FADE] = 0 if y[S_FADE] + 1 >= 5 else y[S_FADE] + 1
        if y[S_REL] == 0:
            y[S_CNT] = hi(acc(y[S_CNT]) - acc(32))
            if not fading:
                if acc(y[S_CNT]) <= 0:
                    self.splice()
                elif ((acc(y[T_RGI]) + y[T_RGF]) << 8) + acc(y[S_GI]) + y[S_GF] >= acc(y[S_HI]):
                    y[S_CNT] = 0
                    self.splice()
        return out


def read_wav(path):
    with wave.open(path, "rb") as w:
        ch, width, n = w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    if width != 2:
        raise SystemExit("only 16-bit WAV files are supported")
    vals = [int.from_bytes(raw[i:i + 2], "little", signed=True) for i in range(0, len(raw), 2)]
    mono = [sum(vals[i:i + ch]) // ch for i in range(0, len(vals), ch)]
    return [(v << 8) & M24 for v in mono]


def write_wav(path, words):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100)
        w.writeframes(b"".join((s24(v) >> 8).to_bytes(2, "little", signed=True) for v in words))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input"); ap.add_argument("output")
    for name, default in (("ptch", 64), ("mode", 0), ("dec", 127), ("time", 0), ("strt", 0), ("end", 127),
                          ("gran", 64), ("flux", 0), ("bpm", 120), ("every", 16)):
        ap.add_argument("--" + name, type=int, default=default)
    ap.add_argument("--ring", type=lambda v: int(v, 0), default=0x10000, help="lent words (default 65536)")
    a = ap.parse_args()
    words = read_wav(a.input)
    t = Track()
    t.set_params(ptch=a.ptch, mode=a.mode, dec=a.dec, time=a.time, strt=a.strt, end=a.end, gran=a.gran,
                 flux=a.flux)
    lent = (0x180000, a.ring)
    every = 44100 * 60 / a.bpm / 4 * a.every        # samples between trigs
    out, nxt = [], every
    for b in range(len(words) // 32):
        if b * 32 >= nxt:
            t.trig()
            nxt += every
        out += t.render([w for w in words[b * 32:b * 32 + 32] for _ in (0, 1)], lent)
    write_wav(a.output, out)
    print("wrote", a.output, "take", t.y[S_LEN], "frames")
