; ldi = 1 cycles
; call = 4 cycles

; subi = 1 cycle
; brne = 2 cycles	-> 3 cycles per loop

; brne (final) = 1 cycle
; ret = 4 cycles

; total = 11 + 3*(r28 - 1) cycles
; total = 8 + 3*r28 cycles

.global delay_cycles
delay_cycles:
loop:
	SUBI	r28, 0x01	; 3 cycles per loop
	BRNE	loop		;
	RET
