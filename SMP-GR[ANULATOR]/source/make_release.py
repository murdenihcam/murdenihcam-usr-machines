#!/usr/bin/env python3
"""Assemble a release folder: one subfolder per machine plus the shared source.

python make_release.py release_v0.3
  SMP-GR_allbanks/, SMP-GM_rom/, SMP-G2_e12/: .syx .mds .json .asm56k .pbm, the
      32x24 logo and a web logo (6x, black on #CD2824)
  source/: the shared engine, generated includes and tools. To rebuild, work in
      the build folder (C:\\work\\granular) with the original file names (BUILD_NAME).
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MACHINES = [  # release name, build name, logo
    ("SMP-GR_allbanks", "granular", "logo_gr_all.png"),
    ("SMP-GM_rom", "rom_granular", "logo_gm_rom.png"),
    ("SMP-G2_e12", "e12_granular", "logo_g2_e12.png"),
]
SOURCE = ["granular_engine.inc", "tables.inc", "gen_tables.py",
          "make_variants.py", "make_release.py", "png_sprite.py", "granular_dsp_model.py", "simtest.py",
          "build.cmd"]

out = HERE / sys.argv[1]
if out.exists():
    shutil.rmtree(out)
for rel, build, logo in MACHINES:
    d = out / rel
    d.mkdir(parents=True)
    for ext in ("syx", "mds", "json", "asm56k", "pbm"):
        shutil.copy2(HERE / f"{build}.{ext}", d / f"{rel}.{ext}")
    shutil.copy2(HERE / f"{build}_cert.json", d / f"{rel}_cert.json")
    shutil.copy2(HERE / logo, d / f"{rel}_logo.png")
    subprocess.run([sys.executable, str(HERE / "png_sprite.py"), str(HERE / logo), "--web",
                    str(d / f"{rel}_web.png")], check=True, capture_output=True)
    print(rel, sorted(p.name for p in d.iterdir()))
src = out / "source"
src.mkdir()
for name in SOURCE:
    shutil.copy2(HERE / name, src / name)
(out / "README.txt").write_text(
    "SMP-GR granular machines, " + out.name.replace("release_", "") + "\n\n"
    "SMP-GR_allbanks  ROM+E12 GRANULAR  UW ROM 1..48 then E1..E21   (build name: granular)\n"
    "SMP-GM_rom       ROM GRANULAR      UW ROM 1..48                (build name: rom_granular)\n"
    "SMP-G2_e12       E12 GRANULAR      internal E12 1..21          (build name: e12_granular)\n\n"
    "Each folder: .syx to send to the Machinedrum, .mds package, .json definition, .asm56k wrapper,\n"
    ".pbm sprite, the 32x24 logo and a web logo (black on #CD2824).\n"
    "source/: shared engine (granular_engine.inc), generated includes and the Python tools.\n"
    "The builds were made in C:\\work\\granular under the build names above.\n\n"
    "MDS 1.1, certified with mds-certifier (mds-tools). All three variants measure the same\n"
    "cycles per track: MKII 5298, MKI 5962, MKI with the program in SRAM 5255 (worst case at\n"
    "GRAN 0 with SPRY 127). Each folder holds the certifier report (_cert.json).\n\n"
    "Tracks of this machine one kit can hold (X.20 / MDX firmware):\n"
    "  MKII  about 9 tracks\n"
    "  MKI   about 8 tracks (about 9 when the firmware puts the program in SRAM)\n"
    "Fewer beside other expensive machines: the firmware refuses a kit over its DSP limit.\n")
print("wrote", out)
