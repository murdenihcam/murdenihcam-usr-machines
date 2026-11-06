#!/usr/bin/env python3
"""Run a packaged RAM machine (.mds) in the Motorola DSP56300 simulator, block by
block, the way the firmware does (program at $400, relocations applied, the input
as the main output: identical left/right pairs at X:$2000, position at X:$7F6,
RAM_WORKSPACE replaced by sim/stubs.asm56k, which lends X:$7F2 / X:$7F3).
Shared by the murdenihcam RAM machines (copied from RAM-ST's simtest.py).

run(mds, params_by_block, trig_blocks, pcm, blocks) -> list of 32-word output blocks
"""
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, r"C:\work\mds-tools\tools")
from lib.mds_format import parse_package          # noqa: E402

TOOLS = Path(r"C:\DSP56300Tools\clas")
SIM = TOOLS.parent / "sim" / "sim56300.exe"
BASE = 0x400
R6, R7 = 0x100, 0x200
SERVICES = {11: 0xE00}
DRIVER, RETURN = 0xEF0, 0xEF2
INFO_AT, LENT_AT, DESC, INPUT_AT = 0x7F4, 0x7F2, 0x7E0, 0x1000
MAIN_AT, MAIN_PCM = 0x7F6, 0x2000      # main-output position; the input as stereo pairs in X
SMALL = (0x190000, 0x4000)        # a 16K ring
FULL = (0x180000, 0x10000)        # a 64K ring


def tempo_value(setting, bpm):
    f = 270950400 // (24 * bpm) * 60 // 4096
    return f * setting


def encode(kind, s, bpm=120):
    return {"raw14": s * 128, "tempo": tempo_value(s, bpm), "q23": s << 16, "sq23": (s * s) << 9}[kind]


def s24(v):
    v &= 0xFFFFFF
    return v - (1 << 24) if v & 0x800000 else v


def tone(n, hz, amp=0.3, start=0):
    return [round(amp * math.sin(2 * math.pi * hz * (i + start) / 44100) * 0x7FFFFF) & 0xFFFFFF for i in range(n)]


def assemble_stubs(work):
    src = Path(r"C:\work\ram_stretch\sim\stubs.asm56k")
    (work / "stubs.asm").write_text(src.read_text())
    subprocess.run(f'"{TOOLS / "asm56300.exe"}" -a -b stubs.asm > stubs_asm.txt', cwd=work, shell=True, check=True)
    lod = subprocess.run(f'"{TOOLS / "cldlod.exe"}" stubs.cld', cwd=work, shell=True, check=True,
                         capture_output=True, text=True).stdout
    return [line for line in lod.splitlines() if not line.startswith(("_START", "_END", "_SYMBOL"))
            and not (line[:1].isalpha() and " I " in line)]


ring_word = []   # program word of the main-output ring base, set every block to the block's position


def program_words(package):
    ring_word.clear()
    p = parse_package(Path(package).read_bytes())
    code = p["program"]
    words = [int.from_bytes(code[i:i + 3], "big") for i in range(0, len(code), 3)]
    for w in p["relocations"]:
        words[w] = (words[w] + BASE) & 0xFFFFFF
    for imp in p["imports"]:
        if imp.kind == 5:
            words[imp.patch_word] = SERVICES[imp.symbol]
        elif imp.symbol == 13:
            words[imp.patch_word] = INFO_AT
        elif imp.symbol == 5:
            words[imp.patch_word] = MAIN_AT
        elif imp.symbol == 4:
            ring_word.append(imp.patch_word)
    return words, {"INIT": p["init_word"], "TRIG": p["mutate_word"], "RENDER": p["execute_word"]}


def lod_block(space, addr, words):
    lines = [f"_DATA {space} {addr:04X}"]
    for i in range(0, len(words), 8):
        lines.append(" ".join(f"{w & 0xFFFFFF:06X}" for w in words[i:i + 8]))
    return lines


def run(mds, work, tag, params, events, pcm, blocks, lent=SMALL, track=0, state_words=0, trace_block=None):
    """params: {index: value} for Y:(r6+1..8); events: {block: dict(params={..}, trig=info, lent=(..))}.
    Returns (output blocks, final Y:(r6+0..state_words-1))."""
    work = Path(work)
    work.mkdir(exist_ok=True)
    stub = assemble_stubs(work)
    words, entries = program_words(mds)
    cmds = ["break pc=$%x" % RETURN]
    calls = []

    def call(address, capture=False, trace=False):
        cmds.extend(["change r6 $%x" % R6, "change r7 $%x" % R7, "change m7 $1f", "change r1 $%x" % track]
                    + ["change m%d $ffffff" % i for i in range(6)]
                    + ["change p:$%x $%x" % (DRIVER + 1, address), "change pc $%x" % DRIVER, "change cyc 0"]
                    + (["trace 20000 h"] if trace else ["go"]))
        if capture:
            cmds.append("display y:$%x..$%x" % (R7, R7 + 31))
        calls.append(capture)

    def setp(p):
        for k, v in p.items():
            cmds.append("change y:$%x $%x" % (R6 + k, v & 0xFFFFFF))

    setp(params)
    cmds += ["change x:$%x $%x" % (LENT_AT, lent[0]), "change x:$%x $%x" % (LENT_AT + 1, lent[1]),
             "change x:$%x $4" % (LENT_AT + 3)]
    call(BASE + entries["INIT"])
    for b in range(blocks):
        ev = events.get(b, {})
        if "params" in ev:
            setp(ev["params"])
        if "lent" in ev:
            cmds += ["change x:$%x $%x" % (LENT_AT, ev["lent"][0]), "change x:$%x $%x" % (LENT_AT + 1, ev["lent"][1])]
        if "trig" in ev:
            cmds.append("change x:$%x $%x" % (INFO_AT, ev["trig"]))
            call(BASE + entries["TRIG"])
        cmds.append("change y:$%x $%x" % (DESC + 1, INPUT_AT + 32 * b))
        cmds.append("change x:$%x $%x" % (MAIN_AT, MAIN_PCM + 64 * b))
        for w in ring_word:
            cmds.append("change p:$%x $%x" % (BASE + w, MAIN_PCM + 64 * b))
        if b == trace_block:
            call(BASE + entries["RENDER"], trace=True)
            break
        call(BASE + entries["RENDER"], capture=True)
    if state_words:
        cmds.append("display y:$%x..$%x" % (R6, R6 + state_words - 1))
    lod = lod_block("P", BASE, words) + stub + lod_block("Y", 0x7F0, [DESC]) + lod_block("Y", INPUT_AT, pcm)         + lod_block("X", MAIN_PCM, [w for v in pcm for w in (v, v)])
    (work / f"{tag}.lod").write_text("\n".join(["_START TEST 0000 0000 0000 DSP56300 6.3.15", ""] + lod
                                               + ["_END 0000", ""]))
    log = work / f"{tag}.log"
    script = ["device dv0 56303", "change x:$fffffb $020000", f"log s {log.name} -o", f"load {tag}.lod"] + cmds + ["log off s", "quit"]
    (work / f"{tag}.cmd").write_text("\n".join(script) + "\n")
    subprocess.run([str(SIM), f"{tag}.cmd"], cwd=work, check=True, timeout=3600, capture_output=True)
    if trace_block is not None:
        return log.read_text().splitlines(), words
    out, lines = [], log.read_text().splitlines()
    i = 0
    for capture in calls:
        while not lines[i].startswith("Break #1"):
            i += 1
        i += 1
        if capture:
            while not lines[i].startswith("y:$%06x=" % R7):
                i += 1
            w = []
            while len(w) < 32:
                w += [int(t[1:], 16) for t in lines[i].split("=")[-1].split()]
                i += 1
            out.append(w)
    state = []
    if state_words:
        start = max(k for k, line in enumerate(lines) if line.startswith("display y:$%x" % R6))
        for line in lines[start + 1:]:
            if not line.startswith("y:$"):
                break
            state += [int(v[1:], 16) for v in line.split("=")[-1].split()]
    return out, state


def profile(lines, lst, base=BASE):
    """Cycles per label of the traced RENDER (lines from run(..., trace_block=b))."""
    import re
    lines = lines[next(i for i, line in enumerate(lines) if line.startswith("trace ")):]
    labels, current = {}, "?"
    for line in Path(lst).read_text().splitlines():
        m1 = re.match(r"\s*\d+\s+([A-Z_][A-Z0-9_]*):(?![0-9A-F]{6})", line)
        if m1:
            current = m1.group(1)
        m2 = re.match(r"\s*\d+\s+P:([0-9A-F]{6})", line)
        if m2:
            labels[int(m2.group(1), 16)] = current
    per, last_cyc, last_pc, cyc, pc = {}, 0, None, 0, 0
    for line in lines:
        m3 = re.search(r"cyc=\s*\{?(\d+)", line)
        if m3:
            cyc = int(m3.group(1))
        m5 = re.search(r"pc=\{?\$([0-9a-f]{6})", line)
        if m5:
            pc = int(m5.group(1), 16)
        if line.startswith(" cnt1"):
            if last_pc is not None:
                name = labels.get(last_pc - base, "service/driver")
                per[name] = per.get(name, 0) + cyc - last_cyc
            last_cyc, last_pc = cyc, pc
            if pc == RETURN:
                break
    return per


def distinct_words(lines, base=BASE):
    """Program words the traced call executed (its instruction-cache footprint), from the trace."""
    import re
    lines = lines[next(i for i, line in enumerate(lines) if line.startswith("trace ")):]
    pcs = set()
    for line in lines:
        m5 = re.search(r"pc=\{?\$([0-9a-f]{6})", line)
        if m5:
            pcs.add(int(m5.group(1), 16))
    return pcs
