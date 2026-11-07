RAM-GR "RAM GRANULAR" v0.3 - SMP-GR's knobs on the main output, mono, as RAM-R records it (first free RAM slot R1-R4)
Certified: MKII 4,454 / MKI 4,912 / MKI SRAM 4,148 cycles per track.
Tracks it can run on alone (kit budget 16 x 3,000 MKII, 16 x 3,073 MKI): MKII 10, MKI 10, MKI with SRAM 11. But only 4 RAM machines can play per pattern on an MKII (R1-R4) and 2 on an MKI (R1-R2), shared with RAM-R and the other RAM machines. Mixed kits: the sum of all tracks' cycles must stay within the budget.

Knob  Name  Range                         Default  What it does
 1    PTCH  -32..+32 semitones (1/2 steps)  64     Grain pitch
 2    MODE  REC / HOLD                      REC    REC records all the time; HOLD stops recording and keeps the buffer
 3    DEC   0..127                          127    Fade after the trig (127 = none)
 4    DENS  0..127                          64     Grain overlap 0.5..3 (up to 3 grains)
 5    SEEK  0..127                          0      Playhead start in the window (LIVE: distance behind the recorder)
 6    SCAN  bipolar                         LIVE   Playhead speed through the window, -2..+2 (64 = still); 0 = LIVE (the default): no freeze, grains read behind the recorder (granular delay)
 7    GRAN  0..127                          64     Grain length 3..116 ms
 8    SPRY  0..127                          0      Random position (up to half the window) and reverse chance (up to 1/2)

The slot is split in two halves: a trig freezes the whole recording half and recording moves to the
other half, so every trig freezes fresh audio; a retrig repeat keeps the frozen audio. In HOLD a trig
freezes what was recorded before the hold, and later trigs keep that audio. The window holds at most
half the slot minus a margin (about 0.7 s on a 64K slot). Grains read the nearest frame (as SMP-GR).
