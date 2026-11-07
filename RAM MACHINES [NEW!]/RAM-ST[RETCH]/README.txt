RAM-ST "RAM STRETCH" v0.4 (murdenihcam) - slot U10, MDS 1.1, needs MDX 2.0C on a UW unit

Records the main output (mono, as RAM-R does) into a RAM slot; a trig plays the
buffer through the SMP-ST splice time-stretch. MODE switches between recording
(REC), keeping what is there (HOLD) and recording with RAM-ST muted (MREC).

Tracks per model (certified cycles per track; the firmware sums every track in the kit).
  The DSP figures below are not the real limit: RAM slots allow only 4 RAM machines
  per pattern on MKII and 2 on MKI (see the next lines).
  MKII            3,362 cycles  -> up to 14 tracks of RAM-ST alone (16 needs <= 3,000)
  MKI, DRAM       3,919 cycles  -> up to 12 tracks alone (16 needs <= 3,073)
  MKI, SRAM       3,158 cycles  -> up to 15 tracks alone
  Only 4 instances can sound at once on MKII (R1-R4) and 2 on MKI (R1-R2), shared
  first come, first served with RAM-R and other RAM machines; extra copies stay silent.
  4 instances use about 28% (MKII) / 32% (MKI) of the DSP.

Knobs
  PTCH  +-32 semitones, half a semitone per step
  MODE  3 steps: left REC (default): records all the time
                centre HOLD: stops recording, keeps the buffer
                right MREC: records with RAM-ST's own output muted (no spillover)
  DEC   decay, 127 = hold
  TIME  playhead speed: 0 normal, 42 half, 127 frozen (pitch unchanged)
  STRT  start of the window in the take
  END   end of the window; END before STRT plays it reversed
  GRAN  grain length (300..5000 samples)
  FLUX  random grain position/length jitter

Notes
  - Take length, always 44.1 kHz: HOLD plays the whole buffer, about 1.44 s with a
    64K-word slot (up to 5.9 s in bigger slots, when fewer UW samples are loaded).
    REC plays the newest half (about 0.74 s / up to 3 s), so a slowed take has time
    before new recording reaches it; past that, new audio smears into it.
  - Use STRT/END to pick the part of the buffer to play.
  - In REC, RAM-ST hears itself: its own output is in the main mix it records, as
    with RAM-R. MREC avoids that by muting it (a playing take stops); switch to
    HOLD to play what was recorded.
  - Slot: found automatically; slots holding a recording or used by another track
    are skipped. A new slot is cleared first: about 0.2-0.7 s of silence after
    assignment or a sample-bank load.
  - Retrig repeats replay the same take; other trigs take a new one.
  - C6/64 rejects MDS 1.1 files; send with SysEx Librarian.
