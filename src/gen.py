#!/usr/bin/python
import sys

import numpy as np

gamma = 2.8
total_cycles = 100000

perceived_brightness = np.linspace(0, 1, 101)
cycles = total_cycles * perceived_brightness**gamma
cycles = cycles.astype(np.int)

# remove first zero, so there is no duplicate zero
cycles = cycles[1:]
diff = np.diff(cycles)

if len(sys.argv) == 1:
	for i in range(99):
		print(
                    f'{i:4d}:\tC{cycles[i]:6d}\t{100 * cycles[i] / total_cycles:2.2f}%\t{cycles[i]*1e9/20e6:0.0f}ns\t{cycles[i]*1e6/20e6:0.2f}us\t{diff[i]:5d} cycles to next')
	exit()

with open('loop.S', 'w') as f:
	f.write("""\
#include <avr/io.h>
#define PORTS (PORTD - 0x20)
// pinstates contains the pin states for index 2-10  (index 0 and 1 are stored in r16, r28. delay between index 10 and 11 is 58 cycles. so enough to use get_state)
.data
pinstates: .byte	9

.text
.extern delay_cycles
.extern get_state

.global loop
loop:
	out		PORTS, r16			// index 0: cycle 0  (= starts at cycle X)

	out		PORTS, r28			// index 1: cycle 1

	nop
	lds 	r28,	pinstates
	out		PORTS, r28			// index 2: cycle 5

	lds 	r28,	pinstates + 1
	lds 	r28,	pinstates + 1
	lds 	r28,	pinstates + 1
	out		PORTS, r28			// index 3: cycle 12

	nop
	lds 	r28,	pinstates + 2
	lds 	r28,	pinstates + 2
	lds 	r28,	pinstates + 2
	lds 	r28,	pinstates + 2
	out		PORTS, r28			// index 4: cycle 22

	ldi		r28, 1
	rcall	delay_cycles
	lds 	r28,	pinstates + 3
	lds 	r28,	pinstates + 3
	out		PORTS, r28			// index 5: cycle 37

	ldi		r28, 3
	rcall	delay_cycles
	lds 	r28,	pinstates + 4
	lds 	r28,	pinstates + 4
	out		PORTS, r28			// index 6: cycle 58

	nop
	ldi		r28, 5
	rcall	delay_cycles
	lds 	r28,	pinstates + 5
	out		PORTS, r28			// index 7: cycle 84

	ldi		r28, 7
	rcall	delay_cycles
	lds 	r28,	pinstates + 6
	lds 	r28,	pinstates + 6
	out		PORTS, r28			// index 8: cycle 117

	nop
	ldi		r28, 10
	rcall	delay_cycles
	lds 	r28,	pinstates + 7
	out		PORTS, r28			// index 9: cycle 158

	ldi		r28, 12
	rcall	delay_cycles
	lds 	r28,	pinstates + 8
	lds 	r28,	pinstates + 8
	out		PORTS, r28			// index 10: cycle 206

	ldi		r28, 16
	rcall	delay_cycles
	lds 	r28,	pinstates + 9
	out		PORTS, r28			// index 11: cycle 264

""")

	def add_delay(cyc):
		while cyc > 0:
			if cyc >= (4 + 6):
				cyc -= (4 + 6)
				r28val = int(cyc / 3)

				if r28val > 254:
					r28val = 254

				f.write(f'	ldi		r28, {r28val + 1}\n')
				f.write(f'	rcall	delay_cycles\n')
				cyc -= 3 * r28val
				continue
			if cyc >= 2:
				cyc -= 2
				f.write(f'\tlds		r28, pinstates\n')
			if cyc == 1:
				cyc -= 1
				f.write(f'\tnop\n')

	for i in range(12, 99):
		cyc = diff[i - 1]
		cyc -= 58
		add_delay(cyc)

		f.write(f'\tldi		r29, {i}\n')
		f.write(f'\trcall	get_state\n')
		f.write(f'\tout		PORTS, r28			// index {i}: cycle {cycles[i]}\n\n')

	add_delay(2070)

	f.write("""\

	ldi		r29, 2
	rcall	get_state
	sts		pinstates, r28

	ldi		r29, 3
	rcall	get_state
	sts		pinstates + 1, r28

	ldi		r29, 4
	rcall	get_state
	sts		pinstates + 2, r28

	ldi		r29, 5
	rcall	get_state
	sts		pinstates + 3, r28

	ldi		r29, 6
	rcall	get_state
	sts		pinstates + 4, r28

	ldi		r29, 7
	rcall	get_state
	sts		pinstates + 5, r28

	ldi		r29, 8
	rcall	get_state
	sts		pinstates + 6, r28

	ldi		r29, 9
	rcall	get_state
	sts		pinstates + 7, r28

	ldi		r29, 10
	rcall	get_state
	sts		pinstates + 8, r28

	ldi		r29, 11
	rcall	get_state
	sts		pinstates + 9, r28

	ldi		r29, 0
	rcall	get_state
	mov		r16, r28

	ldi		r29, 1
	rcall	get_state


	rjmp loop
""")


with open('get_state.S', 'w') as f:
	f.write("""\
// set r28 to the pin state given by the brightness values and current index
// r29 contains the current cycle index
// modifies r17

// cycles:
// 1 to clear r28
// 6 per bit
// 4 to ret
// = 53 cycles total

.extern brightness

.global get_state
get_state:
	clr		r28	// 1 cycle
""")
	for i in range(8):
		f.write("""\
	// set C if second reg is larger than first
	lds		r17, brightness + %d
	cp		r29, r17		// 1 cycle
	// branch if C set
	brcs	c_set_%d		// 1 cycle if C=0, 2 if C=1
	rjmp	c_clr_%d		// 2 cycles
c_set_%d:
	sbr		r28, %d			// 1 cycle
c_clr_%d:

""" % (i, i, i, i, (2**i), i))

	f.write("""\
	ret		// 4 cycles
""")
