// Machine data for the murdenihcam USR machines page.
// Parameter labels and defaults come from each machine's .json (MDS source);
// descriptions, notes and track counts follow the repo READMEs.
// params: [label, default, valueTexts|null, min, max, "what it does"]
//   valueTexts with several entries = a list parameter (shown as text on the screen);
//   a single entry = the name of the default position (e.g. SCAN 0 = LIVE).
var INFINITE_DECAY = "Infinite decay keeps sounding after a pattern change until that track gets a new trig, and until then it takes on the new pattern's LEV for that track (keep them the same to avoid a jump).";

window.MACHINES = [
  {
    id: "SMP-SL",
    name: "SMP-SL[ICE]",
    version: "0.6",
    category: "SMP",
    lcdName: "ROM+E12 SLICER",
    desc: "A transient-detecting sample slicer and looper. Most fun with longer samples; the magic is in p-locking SLNO (slice number).",
    demo: { file: "audio/SMP-SL-demo.wav", label: "SMP-SL demo", volume: 0.75 },
    params: [
      ["PTCH", 64, null, 0, 127, "Half a semitone per step (±32 semitones). Changes speed as well, and interacts with TIME."],
      ["SMPL", 1, null, 1, 69, "Which sample: 1–48 are the UW ROM slots, E1–E21 the internal samples. Takes effect at the next trig."],
      ["DEC", 0, null, 0, 127, "0 plays the slice once; 1–126 decay from about 0.03 s to 30 s while the slice loops in the PLAY direction; 127 loops forever."],
      ["TIME", 0, null, 0, 127, "0 is normal playback; above 0 the slice slows down at the same pitch (42 = half speed). Past halfway the grains get smaller; 127 freezes."],
      ["PLAY", 0, ["FWD", "REV", "BI"], 0, 2, "Direction: forwards, backwards, or turning round at each end. Checked on every loop, so it can change while a slice is held."],
      ["THRS", 27, null, 0, 127, "Threshold for a transient to start a slice: higher means fewer slices."],
      ["SLIC", 32, null, 1, 32, "Number of slices across the whole sample (up to 32). Takes effect at the next trig."],
      ["SLNO", 1, null, 1, 32, "Which slice plays. Values above SLIC wrap round (SLNO 10 with 8 slices plays slice 2). Takes effect at the next trig."]
    ],
    aware: [
      INFINITE_DECAY,
      "A newly selected sample is analysed in the background (well under a second while the track is quiet); until then SLIC gives equal slices."
    ],
    tracks: { mk2: "7", mk1: "7", sram: "8" },
    variants: [
      { id: "SMP-SL", scope: "All banks: UW ROM + E12", compat: "UW only", file: "downloads/SMP-SL/SMP-SL.syx", logo: "assets/logos/SMP-SL.png" },
      { id: "SMP-SM", scope: "UW ROM bank only", compat: "UW only", file: "downloads/SMP-SL/SMP-SM.syx", logo: "assets/logos/SMP-SM.png" },
      { id: "SMP-SN", scope: "E12 bank only", compat: "all models", file: "downloads/SMP-SL/SMP-SN.syx", logo: "assets/logos/SMP-SN.png" }
    ]
  },
  {
    id: "SMP-ST",
    name: "SMP-ST[RETCH]",
    version: "0.7",
    category: "SMP",
    lcdName: "ROM+E12 STRETCH",
    desc: "A sample timestretcher in homage to Ableton's texture warp: that gritty, S950 kind of stretch. Slow it down, freeze it, and modulate GRAN and FLUX.",
    demo: { file: "audio/SMP-ST-demo.wav", label: "SMP-ST demo" },
    params: [
      ["PTCH", 64, null, 0, 127, "Pitch, ±32 semitones."],
      ["SMPL", 1, null, 1, 69, "Which sample: 1–48 are the UW ROM slots, E1–E21 the internal samples. P-lockable, so no digging through ROM/E12."],
      ["DEC", 127, null, 0, 127, "Decay; 127 = none (the sound holds)."],
      ["TIME", 0, null, 0, 127, "Slows the playback at unchanged pitch: 0 normal, 42 half speed, 127 frozen."],
      ["STRT", 0, null, 0, 127, "Start point in the sample."],
      ["END", 127, null, 0, 127, "End point; END before STRT plays the sample in reverse."],
      ["GRAN", 64, null, 0, 127, "Grain length, like the grain size of Ableton's texture warp."],
      ["FLUX", 0, null, 0, 127, "Random jitter of the grains, like texture warp's flux."]
    ],
    aware: [
      "Infinite decay/timestretch keeps sounding after a pattern change until that track gets a new trig, and until then it takes on the new pattern's LEV for that track (keep them the same to avoid a jump)."
    ],
    tracks: { mk2: "10", mk1: "9", sram: "10" },
    variants: [
      { id: "SMP-ST", scope: "All banks: UW ROM + E12", compat: "UW only", file: "downloads/SMP-ST/SMP-ST_allbanks.syx", logo: "assets/logos/SMP-ST.png" },
      { id: "SMP-SR", scope: "UW ROM bank only", compat: "UW only", file: "downloads/SMP-ST/SMP-SR_rom.syx", logo: "assets/logos/SMP-SR.png" },
      { id: "SMP-S2", scope: "E12 bank only", compat: "all models", file: "downloads/SMP-ST/SMP-S2_e12.syx", logo: "assets/logos/SMP-S2.png" }
    ]
  },
  {
    id: "SMP-GR",
    name: "SMP-GR[ANULATOR]",
    version: "0.6",
    category: "SMP",
    lcdName: "ROM+E12 GRANULAR",
    desc: "An experimental granulator for ROM and E12 samples. Up to 3 grains at once, scanning and spraying through the sample, with infinite decay for endless clouds.",
    demo: { file: "audio/SMP-GR-demo.wav", label: "SMP-GR demo" },
    params: [
      ["PTCH", 64, null, 0, 127, "Grain pitch in half-semitone steps (±32); 64 is the original pitch. Doesn't change scan speed or grain length."],
      ["SMPL", 1, null, 1, 69, "Which sample to granulate: SMP-GR ROM 1–48 then E1–E21, SMP-GM ROM only, SMP-G2 E12 only. Read when the track is triggered."],
      ["DEC", 64, null, 0, 127, "Fade time from about 30 ms to 30 s (64 ≈ 1 s); 127 holds forever, with the grains looping round."],
      ["DENS", 64, null, 0, 127, "Grains at once, 0.5 (sparse) to 3. Up to about 49 one grain at full rate; above that they overlap at half rate."],
      ["SEEK", 0, null, 0, 127, "Where in the sample grains come from, start (0) to end (127). Matters less the further SCAN is from 64."],
      ["SCAN", 64, null, 0, 127, "Moves the grain position over time: 64 locked, higher forward, lower reverse, up to about 2×. Wraps at the ends."],
      ["GRAN", 64, null, 0, 127, "Grain length, about 3 ms to 740 ms (64 ≈ 46 ms)."],
      ["SPRY", 0, null, 0, 127, "Random variation in where grains start; above 64 grains may also play backwards (up to 50%)."]
    ],
    aware: [
      "SMPL is only read on a trig: with full DEC, a new SMPL won't sound until the track is triggered again.",
      INFINITE_DECAY
    ],
    tracks: { mk2: "9", mk1: "8", sram: "9" },
    variants: [
      { id: "SMP-GR", scope: "All banks: UW ROM + E12", compat: "UW only", file: "downloads/SMP-GR/SMP-GR_allbanks.syx", logo: "assets/logos/SMP-GR.png" },
      { id: "SMP-GM", scope: "UW ROM bank only", compat: "UW only", file: "downloads/SMP-GR/SMP-GM_rom.syx", logo: "assets/logos/SMP-GM.png" },
      { id: "SMP-G2", scope: "E12 bank only", compat: "all models", file: "downloads/SMP-GR/SMP-G2_e12.syx", logo: "assets/logos/SMP-G2.png" }
    ]
  },
  {
    id: "NFX-MO",
    name: "NFX-MO[DULATOR]",
    version: "0.11",
    category: "NFX",
    lcdName: "SPACE MOD",
    desc: "A multi-mode modulation effect on the tracks before it: flanger, chorus, doubler, plus pitch- and frequency-shifting delays. Lots of spiralling sweet spots.",
    demo: { file: "audio/NFX-MO-demo-bode.wav", label: "NFX-MO demo (BODE setting)" },
    params: [
      ["MODE", 0, ["SPIN", "FLNG", "CHOR", "DBLR", "BODE"], 0, 4, "SPIN pitch-shifting delay, FLNG flanger, CHOR three-voice chorus, DBLR doubler, BODE frequency-shifting delay."],
      ["RATE", 64, null, 0, 127, "LFO speed in FLNG/CHOR/DBLR. In SPIN the shift (±12 semitones), in BODE the shift (±1 kHz); 64 = no shift."],
      ["DPTH", 64, null, 0, 127, "LFO depth. Window size (1.5–20 ms) in SPIN. In BODE 0 = ring mod, 127 = pure shift."],
      ["FB", 64, null, 0, 127, "Feedback: 64 none, about 124 unity, 125–127 self-oscillation, below 64 negative. CHOR stops just below unity."],
      ["SPRD", 64, null, 0, 127, "Spread, per mode: a second tap, voice spread, or a wobble of the shift or delay. Subtle, nice when modulated."],
      ["ENTI", 64, null, 0, 127, "Envelope on the delay time, fired by trigs. 64 off; left shorter → longer, right longer → shorter; further = slower."],
      ["DLAY", 40, null, 0, 127, "Delay time; the range depends on the mode (0.5–12 ms in CHOR)."],
      ["NBAL", 127, null, 0, 127, "Input blend: right = the track just before, left = two tracks before, centre = both."]
    ],
    aware: [
      "It processes the tracks before it (wet only); an empty neighbour track is ignored.",
      "Switching MODE does a short fade (about 1.5 ms out and in), no trig needed. A feedback tail carries over, but switching into a short delay (e.g. FLNG with low DLAY) can cut it off."
    ],
    tracks: { mk2: "10", mk1: "8", sram: "9" },
    variants: [
      { id: "NFX-MO", scope: "Effect", compat: "all models", file: "downloads/NFX-MO/mo.syx", logo: "assets/logos/NFX-MO.png" }
    ]
  },
  {
    id: "RAM-GR",
    name: "RAM-GR[ANULAR]",
    version: "0.3",
    category: "RAM",
    lcdName: "RAM GRANULAR",
    desc: "Granulation of live audio. By default a granular delay; turn SCAN up and a trig freezes the buffer for up to 3 grains to play.",
    params: [
      ["PTCH", 64, null, 0, 127, "Grain pitch, ±32 semitones."],
      ["MODE", 0, ["REC", "HOLD"], 0, 1, "REC records all the time; HOLD stops recording and keeps the buffer."],
      ["DEC", 127, null, 0, 127, "Fade after a trig; 127 = none."],
      ["DENS", 64, null, 0, 127, "Grain overlap, 0.5 to 3 (up to 3 grains)."],
      ["SEEK", 0, null, 0, 127, "Where the playhead starts in the frozen buffer; in LIVE, how far behind the recording the grains read."],
      ["SCAN", 0, ["LIVE"], 0, 127, "0 = LIVE (default). Above 0: playhead speed through the frozen buffer, −2× to +2×, 64 = still."],
      ["GRAN", 64, null, 0, 127, "Grain length, 3–116 ms."],
      ["SPRY", 0, null, 0, 127, "Random grain position (up to half the window) and reverse chance (up to 1/2)."]
    ],
    aware: [
      "LIVE mode (SCAN 0) is the default: nothing freezes, the grains read just behind the recording, so it acts as a granular delay. Turn SCAN up from 0 and a trig freezes the buffer instead.",
      "The slot is used as two halves: a trig freezes one and recording moves to the other, so every trig freezes fresh audio; retrig repeats keep the frozen audio. In HOLD a trig freezes what was recorded before the hold.",
      "Records the main output into the first free RAM slot (R1–R4). The frozen window is about 0.7 s on a 64K slot."
    ],
    tracks: { mk2: "10", mk1: "10", sram: "11" },
    variants: [
      { id: "RAM-GR", scope: "Records live audio to RAM", compat: "UW only", file: "downloads/RAM-GR/RAM-GR_U11.syx", logo: "assets/logos/RAM-GR.png" }
    ]
  },
  {
    id: "RAM-PS",
    name: "RAM-P[ITCH] S[HIFTER]",
    version: "0.2",
    category: "RAM",
    lcdName: "RAM PITCH",
    desc: "A two-voice pitch shifter that records its own output, so the shifted sound comes back and shifts again: a shimmer spiral that follows the track level.",
    params: [
      ["PTCH", 96, null, 0, 127, "Voice 1 interval, ±24 semitones (default 96 = an octave up)."],
      ["PTC2", 64, ["OFF"], 0, 127, "Voice 2 interval, ±24 semitones; 64 = off. Both voices sit at −3 dB when it's on."],
      ["ENTI", 64, null, 0, 127, "A pitch swoop fired by trigs, up to ±12 semitones, settling in about 0.5 s; 64 = off."],
      ["FB", 0, null, 0, 127, "The shifted sound back into the buffer (shimmer)."],
      ["DLAY", 0, null, 0, 127, "Predelay, up to 200 ms."],
      ["MODE", 0, ["REC", "HOLD"], 0, 1, "REC records all the time; HOLD stops recording, so the last window keeps playing (a pitched freeze)."],
      ["WIN", 40, null, 0, 127, "Window, 12 ms (smooth, buzzy) to 370 ms (smeared, grainy)."],
      ["SCAT", 0, null, 0, 127, "Each read head lands up to a window further back at random when it jumps: grainy, scattered shifts."]
    ],
    aware: [
      "Its own output is part of the main output it records, so the shifted sound is shifted again: a spiral whose depth follows the track's level, on top of FB. Turn the track down for a cleaner shift.",
      "Records the main output into the first free RAM slot (R1–R4)."
    ],
    tracks: { mk2: "9", mk1: "8", sram: "10" },
    variants: [
      { id: "RAM-PS", scope: "Records live audio to RAM", compat: "UW only", file: "downloads/RAM-PS/RAM-PS_U04.syx", logo: "assets/logos/RAM-PS.png" }
    ]
  },
  {
    id: "RAM-ST",
    name: "RAM-ST[RETCH]",
    version: "0.4",
    category: "RAM",
    lcdName: "RAM STRETCH",
    desc: "The SMP-ST splice time-stretch on recorded audio: a trig plays the buffer through TIME, STRT/END, GRAN and FLUX, all the way to a frozen take.",
    params: [
      ["PTCH", 64, null, 0, 127, "±32 semitones, half a semitone per step."],
      ["MODE", 0, ["REC", "HOLD", "MREC"], 0, 2, "Three positions, left to right: REC (default) records all the time; HOLD, in the middle between the two record modes, stops recording and keeps the buffer; MREC, after HOLD, records with RAM-ST's own output muted."],
      ["DEC", 127, null, 0, 127, "Decay; 127 = hold."],
      ["TIME", 0, null, 0, 127, "Playhead speed at unchanged pitch: 0 normal, 42 half, 127 frozen."],
      ["STRT", 0, null, 0, 127, "Start of the window in the take."],
      ["END", 127, null, 0, 127, "End of the window; END before STRT plays it reversed."],
      ["GRAN", 64, null, 0, 127, "Grain length, 300–5000 samples."],
      ["FLUX", 0, null, 0, 127, "Random grain position/length jitter."]
    ],
    aware: [
      "With MODE on HOLD it plays the whole buffer (about 1.44 s on a 64K slot); on REC it plays the newest half (about 0.74 s), so a slowed take has time before new recording reaches it. Past that, new audio smears in.",
      "With MODE on REC it hears itself (its output is in the main mix it records); turning MODE past HOLD to MREC avoids that by muting its own output while recording. Retrig repeats replay the same take; other trigs take a new one.",
      "Only 4 copies can sound at once on an MKII (R1–R4) and 2 on an MKI, shared with RAM-R and other RAM machines. A new slot is cleared first: about 0.2–0.7 s of silence after assignment or a sample-bank load."
    ],
    tracks: { mk2: "14", mk1: "12", sram: "15" },
    variants: [
      { id: "RAM-ST", scope: "Records live audio to RAM", compat: "UW only", file: "downloads/RAM-ST/RAM-ST_U10.syx", logo: "assets/logos/RAM-ST.png" }
    ]
  }
];
