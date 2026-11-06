#!/usr/bin/env python3
"""Run the packaged RAM-ST machine in the Motorola DSP56300 simulator and check it.

The .mds package is loaded the way the firmware loader does it: at a nonzero
program base, with its relocations applied and its imports patched (temporary
memory at X/Y:$0000, TRIGGER_INFO at X:$7F4, RAM_WORKSPACE replaced by the
stand-in in sim/stubs.asm56k, which returns X:$7F2 / X:$7F3).

Every RENDER's 32 output words must equal ram_stretch_model.py, and so must
the track's state words after the last block (Y+9..63). The input (the main
output) is a stereo test signal, written block by block into a 256-word ring at
X:$2000; the position word at X:$7F6 points at the block, sometimes one ring
past it (the machine folds it back as MAIN REC does).
Cycle costs come from the certifier (build.sh), not from here.

Usage:  python simtest.py [scenario ...]
"""
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r"C:\work\mds-tools\tools")
from lib.mds_format import parse_package          # noqa: E402
import ram_stretch_model as model                 # noqa: E402

TOOLS = Path(r"C:\DSP56300Tools\clas")
SIM = TOOLS.parent / "sim" / "sim56300.exe"
WORK = HERE / "sim"
BASE = 0x400
R6, R7 = 0x100, 0x200
SERVICES = {11: 0xE00}
DRIVER, RETURN = 0xEF0, 0xEF2
INFO_AT, LENT_AT, MAIN_AT, RING_AT = 0x7F4, 0x7F2, 0x7F6, 0x2000
STATE = range(9, 64)


def assemble_stubs():
    (WORK / "stubs.asm").write_text((WORK / "stubs.asm56k").read_text())
    subprocess.run(f'"{TOOLS / "asm56300.exe"}" -a -b stubs.asm > stubs_asm.txt', cwd=WORK, shell=True,
                   check=True)
    lod = subprocess.run(f'"{TOOLS / "cldlod.exe"}" stubs.cld', cwd=WORK, shell=True, check=True,
                         capture_output=True, text=True).stdout
    return [line for line in lod.splitlines() if not line.startswith(("_START", "_END", "_SYMBOL"))
            and not (line[:1].isalpha() and " I " in line)]


def program_words(package):
    p = parse_package(Path(package).read_bytes())
    code = p["program"]
    words = [int.from_bytes(code[i:i + 3], "big") for i in range(0, len(code), 3)]
    for w in p["relocations"]:
        words[w] = (words[w] + BASE) & 0xFFFFFF
    for imp in p["imports"]:
        if imp.kind == 5:
            assert words[imp.patch_word] == 0
            words[imp.patch_word] = SERVICES[imp.symbol]
        elif imp.symbol == 13:
            words[imp.patch_word] = INFO_AT
        elif imp.symbol == 5:
            words[imp.patch_word] = MAIN_AT
        elif imp.symbol == 4:
            words[imp.patch_word] = RING_AT
        # kinds 3/4 keep their offset: the temporary areas start at X/Y:$0000
    entries = {"INIT": p["init_word"], "TRIG": p["mutate_word"], "RENDER": p["execute_word"]}
    return words, entries


def lod_block(space, addr, words):
    lines = [f"_DATA {space} {addr:04X}"]
    for i in range(0, len(words), 8):
        lines.append(" ".join(f"{w & 0xFFFFFF:06X}" for w in words[i:i + 8]))
    return lines


class Session:
    def __init__(self):
        self.cmds = ["break pc=$%x" % RETURN]
        self.calls = []

    def call(self, address, track=0, capture=False):
        c = self.cmds
        c += ["change r6 $%x" % R6, "change r7 $%x" % R7, "change m7 $1f", "change r1 $%x" % track]
        c += ["change m%d $ffffff" % i for i in range(6)]
        c += ["change p:$%x $%x" % (DRIVER + 1, address), "change pc $%x" % DRIVER, "change cyc 0", "go"]
        if capture:
            c.append("display y:$%x..$%x" % (R7, R7 + 31))
        self.calls.append(capture)

    def change(self, space, addr, value):
        self.cmds.append("change %s:$%x $%x" % (space, addr, value & 0xFFFFFF))

    def run(self, lod_lines, tag):
        (WORK / f"{tag}.lod").write_text("\n".join(["_START TEST 0000 0000 0000 DSP56300 6.3.15", ""]
                                                   + lod_lines + ["_END 0000", ""]))
        log = WORK / f"{tag}.log"
        script = ["device dv0 56303", f"log s {log.name} -o", f"load {tag}.lod"] + self.cmds \
            + ["log off s", "quit"]
        (WORK / f"{tag}.cmd").write_text("\n".join(script) + "\n")
        subprocess.run([str(SIM), f"{tag}.cmd"], cwd=WORK, check=True, timeout=1800)
        blocks, lines = [], log.read_text().splitlines()
        i = 0
        for capture in self.calls:
            while not lines[i].startswith("Break #1"):
                i += 1
            i += 1
            if capture:
                while not lines[i].startswith("y:$%06x=" % R7):
                    i += 1
                words = []
                while len(words) < 32:
                    words += [int(t[1:], 16) for t in lines[i].split("=")[-1].split()]
                    i += 1
                blocks.append(words)
        return blocks, lines


def test_signal(n):
    """Two tones with a click every 700 frames, so splices and the rate are visible."""
    out = []
    for i in range(n):
        v = 0.4 * math.sin(2 * math.pi * 441 * i / 44100) + 0.2 * math.sin(2 * math.pi * 3150 * i / 44100)
        if i % 700 == 0:
            v = 0.9
        out.append(round(v * 0x7FFFFF) & 0xFFFFFF)
    return out


SMALL = (0x190000, 0x4000)        # a 16K ring: 32 clearing blocks
MID = (0x181000, 0xF000)          # 32K ring at $188000
FULL = (0x180000, 0x10000)        # 64K ring


def scenario(tag, params, events, blocks, lent=SMALL, track=3, free=4):
    """events: {block: dict(trig=info word, params={...}, lent=(first, words))}."""
    words, entries = program_words(HERE / "sim_uncert.mds")
    shift = lent[1] // 512 if lent[0] else 0   # the ring clears CHUNK = 256 words a block:
    events = {b + shift: e for b, e in events.items()}   # events were written for 512
    blocks += shift
    pcm = test_signal(blocks * 32)
    right = test_signal(blocks * 32 + 350)[350:]           # a delayed copy on the right
    pairs = [w for lr in zip(pcm, right) for w in lr]
    s = Session()
    mem = {}
    t = model.Track(track, mem)
    t.set_params(**params)
    for k in range(1, 9):
        s.change("y", R6 + k, t.y[k])
    s.change("x", LENT_AT, lent[0])
    s.change("x", LENT_AT + 1, lent[1])
    s.change("x", LENT_AT + 3, free)
    s.call(BASE + entries["INIT"], track)
    want = []
    for b in range(blocks):
        ev = events.get(b, {})
        if "params" in ev:
            params = {**params, **ev["params"]}
            t.set_params(**params)
            for k in range(1, 9):
                s.change("y", R6 + k, t.y[k])
        if "free" in ev:
            free = ev["free"]
            s.change("x", LENT_AT + 3, free)
        if "lent" in ev:
            lent = ev["lent"]
            s.change("x", LENT_AT, lent[0])
            s.change("x", LENT_AT + 1, lent[1])
        if "trig" in ev:
            s.change("x", INFO_AT, ev["trig"])
            s.call(BASE + entries["TRIG"], track)
            t.trig(ev["trig"])
        at = RING_AT + 64 * (b % 4)                      # the 256-word main-output ring
        for k in range(64):
            s.change("x", at + k, pairs[64 * b + k])
        s.change("x", MAIN_AT, at + 256 * (b % 2))       # a position may point one ring past
        s.call(BASE + entries["RENDER"], track, capture=True)
        slot_lent = lent if free in (4, t.y[model.S_SLOT]) else (0, 0)
        want.append(t.render(pairs[64 * b:64 * b + 64], slot_lent))
    s.cmds.append("display y:$%x..$%x" % (R6 + STATE[0], R6 + STATE[-1]))
    lod = lod_block("P", BASE, words) + STUB_LOD
    got, lines = s.run(lod, tag)
    bad = [i for i, (g, w) in enumerate(zip(got, want)) if g != w]
    status = "OK" if not bad and len(got) == blocks else f"MISMATCH in blocks {bad[:8]}"
    start = max(i for i, line in enumerate(lines) if line.startswith("display y:$%x" % (R6 + STATE[0])))
    state = []
    for line in lines[start + 1:]:
        if not line.startswith("y:$"):
            break
        state += [int(v[1:], 16) for v in line.split("=")[-1].split()]
    wrong = [k for k, v in zip(STATE, state) if v != t.y[k] & 0xFFFFFF]
    if wrong or len(state) != len(STATE):
        status += f", STATE DIFFERS at Y+{wrong[:6]}"
    played = sum(1 for w in want if any(w))
    return status, played, want, got, t


REPEAT = 0x010000
BASEP = dict(ptch=64, mode=0, dec=127, time=0, strt=0, end=127, gran=10, flux=0)
RUNS = {
    "neutral": (BASEP, {40: dict(trig=0)}, 90),
    "stretch_d2": ({**BASEP, "time": 60, "flux": 100, "gran": 40},
                   {50: dict(trig=0), 100: dict(trig=0)}, 140),
    "long_clamped": ({**BASEP, "time": 30, "ptch": 80}, {70: dict(trig=0)}, 130),
    "reverse": ({**BASEP, "strt": 100, "end": 20, "time": 20}, {45: dict(trig=0)}, 110),
    "repeats": ({**BASEP, "time": 64, "flux": 60},
                {50: dict(trig=0), 70: dict(trig=REPEAT), 90: dict(trig=REPEAT), 100: dict(trig=0)}, 130),
    "hold": ({**BASEP, "time": 30}, {60: dict(params={"mode": 1}), 90: dict(trig=0),
                                               110: dict(trig=REPEAT), 130: dict(params={"mode": 0}),
                                               150: dict(trig=0)}, 170),
    "mrec": ({**BASEP, "mode": 2, "time": 40}, {40: dict(trig=0), 70: dict(params={"mode": 1}),
                                              80: dict(trig=0), 110: dict(params={"mode": 0})}, 130),
    "memory_lost": ({**BASEP, "time": 90},
                    {45: dict(trig=0), 60: dict(lent=(0, 0)), 70: dict(lent=MID), 72: dict(trig=0),
                     208: dict(trig=0)}, 270),
    "pitch_freeze": ({**BASEP, "ptch": 127, "time": 127, "gran": 0, "flux": 127, "dec": 100},
                     {40: dict(trig=0), 80: dict(params={"ptch": 0})}, 120),
    "full_ring": ({**BASEP, "time": 42, "gran": 90}, {150: dict(trig=0)}, 200, FULL, 5),
    "slot_hunt": (BASEP, {40: dict(trig=0), 50: dict(free=2), 130: dict(trig=0)}, 160, SMALL, 3, 1),
    "early_trig": ({**BASEP}, {-32: dict(trig=0), -12: dict(trig=0), 1: dict(trig=0), 2: dict(trig=REPEAT)}, 28),
}

if __name__ == "__main__":
    STUB_LOD = assemble_stubs()
    names = sys.argv[1:] or list(RUNS)
    all_ok = True
    for name in names:
        status, played, *_ = scenario(name, *RUNS[name])
        all_ok &= status == "OK"
        print(f"   {name:14s} {status}   ({played} sounding blocks)", flush=True)
    sys.exit(0 if all_ok else 1)
