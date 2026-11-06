#!/bin/sh
# Assemble, pack and certify (MDS 1.1). Usage: ./build.sh [slot]
set -e
cd "$(dirname "$0")"
N=ram_stretch
python gen_tables.py >/dev/null
cp $N.asm56k $N.asm
/c/DSP56300Tools/clas/asm56300.exe -a -b -l -I../ram_shared/ $N.asm > asm_out.txt 2>&1 || true
grep -i "error" asm_out.txt && exit 1
BMP=""; [ -f $N.pbm ] && BMP="--bitmap $N.pbm"
python /c/work/mds-tools/tools/mds_pack.py $N.json $N.cld --dsp-tools /c/DSP56300Tools/clas $BMP \
  --certify --certifier /c/work/mds-tools/build/Release/mds-certifier.exe --report cert_report.json -o $N.mds
python /c/work/mds-tools/tools/mds_to_syx.py $N.mds --slot ${1:-1} -o $N.syx
