RAM-PS "RAM PITCH" v0.2 - two-voice pitch shifter on the main output, mono, as RAM-R records it (first free RAM slot R1-R4)
Certified: MKII 5,232 / MKI 5,507 / MKI SRAM 4,890 cycles per track.
Tracks it can run on alone (kit budget 16 x 3,000 MKII, 16 x 3,073 MKI): MKII 9, MKI 8, MKI with SRAM 10. But only 4 RAM machines can play per pattern on an MKII (R1-R4) and 2 on an MKI (R1-R2), shared with RAM-R and the other RAM machines. Mixed kits: the sum of all tracks' cycles must stay within the budget.

Knob  Name  Range                          Default  What it does
 1    PTCH  -24..+24 semitones (3/8 steps)  96     Voice 1 interval (96 = an octave up)
 2    PTC2  -24..+24 semitones; 64 = OFF    64     Voice 2 interval (both voices at -3 dB when on)
 3    ENTI  bipolar, 64 = off               64     Pitch swoop fired by a trig: up to +-12 semitones, settling in about 0.5 s
 4    FB    0..127                          0      The shifted sound back into the buffer (shimmer spiral); 127 = the old 90, so it no longer cuts out
 5    DLAY  0..127                          0      Predelay up to 200 ms
 6    MODE  REC / HOLD                      REC    HOLD stops recording: the last window keeps playing (a pitched freeze)
 7    WIN   12 .. 370 ms                    40     Window: short = smooth and buzzy, long = smeared and grainy
 8    SCAT  0..127                          0      Each head lands up to one window further back at random when it jumps: grainy, scattered

The machine's own output is part of the main output, so its shifted sound comes back in and is
shifted again: a spiral whose depth follows the track's level, on top of FB. Turn the track down
for a cleaner shift.
