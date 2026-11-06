; Shared RAM-slot ring for murdenihcam RAM machines (RAM-ST, RAM-LP, ...).
; Include it at the start of RENDER, after "movec #>$ffffff,m6". It calls
; RAM_WORKSPACE (the machine's JSON imports the label WORKSPACE as symbol 11)
; once a block, which every holder must do to keep its slot.
;
; Slot hunting: the machine starts on any slot (INIT: track number mod 4). While
; the slot lends nothing (it holds a recording, another track holds it, or the
; unit has no such slot, as R3/R4 on MKI), the next slot is tried in the next
; block. So up to 4 RAM machines (2 on MKI) share the slots with RAM-R, first
; come, first served, without any setting.
;
; Ring: the largest power of two, RING_MAX down to RING_MIN words, that fits
; aligned in the lent memory: base = Y:(r6+S_RB), mask = Y:(r6+S_RM), CAP =
; size - MARGIN in Y:(r6+S_CAP). A new ring (first use, or the memory moved)
; is cleared CHUNK words a block, the machine silent meanwhile. Address a ring
; offset in the ALU as base | (offset & mask): modulo registers stop at 2^15.
; Certifier note: its emulator has no BRKcc, so loops here are software loops.
;
; The machine defines: S_SLOT, S_RB, S_RM, S_CLR, S_CAP (Y offsets), RING_MAX,
; RING_MIN, CHUNK, MARGIN, and the labels
;   RING_RESET  bsr: a new ring; reset the machine's own ring state (keep R6, R7)
;   RING_LOST   bsr: no memory this block (keep R6, R7)
;   SILENCE     bra: write a silent block and return from RENDER
;   RING_READY  where RENDER continues with the ring ready (M0..M5 linear)
; INIT sets S_RB = S_RM = 0 and S_SLOT. Uses every register but R6, R7, M6, M7.

        move    y:(r6+S_SLOT),a
        and     #>3,a
        move    a1,x0
WORKSPACE:
        jsr     >$000000        ; kind 5 / RAM_WORKSPACE: A1 first word, B1 words
        movec   #>$ffffff,m0    ; services leave M0..M5 undefined
        movec   #>$ffffff,m1
        movec   #>$ffffff,m2
        movec   #>$ffffff,m3
        movec   #>$ffffff,m4
        movec   #>$ffffff,m5
        move    a1,x1           ; first lent word
        move    a1,a
        tst     a
        beq     R_NOMEM
        ; ---- the ring: the largest aligned power of two in the lent words ----
        move    b1,b
        add     x1,b
        move    b1,y1           ; end of the lent words
        move    #>RING_MAX,x0
R_FIT:
        move    x0,b
        move    #>RING_MIN,y0
        cmp     y0,b
        blt     R_NOMEM         ; none fits
        neg     b
        move    b1,y0           ; -P = ~(P - 1)
        move    x1,a
        add     x0,a
        sub     #1,a
        and     y0,a            ; first multiple of P
        add     x0,a
        cmp     y1,a
        ble     R_FIT_END       ; fits
        move    x0,a
        asr     a
        move    a1,x0
        bra     R_FIT
R_FIT_END:
        move    x0,b
        sub     x0,a            ; ring base
        sub     #1,b            ; ring mask
        move    y:(r6+S_RB),y0
        cmp     y0,a
        bne     R_NEWRING
        move    y:(r6+S_RM),y0
        cmp     y0,b
        beq     R_RING_OK
R_NEWRING:
        move    a1,y:(r6+S_RB)
        move    b1,y:(r6+S_RM)
        move    #>MARGIN-1,y0
        sub     y0,b
        move    b1,y:(r6+S_CAP) ; size - MARGIN
        clr     a
        move    a,y:(r6+S_CLR)
        bsr     RING_RESET      ; the machine's own state for a new ring
R_RING_OK:
        ; ---- a new ring is cleared first, silent meanwhile ----
        move    y:(r6+S_RM),a
        move    y:(r6+S_CLR),x0
        cmp     x0,a
        bgt     R_CLEAR
        bra     RING_READY
R_CLEAR:
        move    y:(r6+S_RB),a
        add     x0,a
        move    a1,r0
        clr     a
        rep     #CHUNK
        move    a,y:(r0)+
        move    #>CHUNK,a
        add     x0,a
        move    a1,y:(r6+S_CLR)
        bra     SILENCE
R_NOMEM:
        clr     a               ; no memory: try the next slot in the next block
        move    a,y:(r6+S_RB)
        move    a,y:(r6+S_RM)
        bsr     RING_LOST       ; the machine's own state without memory
        move    y:(r6+S_SLOT),a
        add     #1,a
        and     #>3,a
        move    a1,y:(r6+S_SLOT)
        bra     SILENCE

