#!/usr/bin/python
import sys
from dataclasses import dataclass

import numpy as np

gamma = 2.8
total_cycles = 125000
steps = 256
steps_offset = 0

while True:
	perceived_brightness = np.linspace(0, 1, steps + steps_offset)
	cycles = total_cycles * perceived_brightness**gamma
	cycles = cycles.astype(np.int)
	# remove leading zeroes, so there is no duplicate zero
	cycles = cycles[steps_offset:]

	if np.count_nonzero(cycles) == steps - 1:
		break
	steps_offset += 1

diff = np.diff(cycles)

if len(sys.argv) == 1:
	for i in range(steps):
		print(
                    f'{i:4d}:\tC{cycles[i]:6d}\t{100 * cycles[i] / total_cycles:2.2f}%\t{cycles[i]*1e9/20e6:0.0f}ns\t{cycles[i]*1e6/20e6:0.2f}us\t{diff[i] if i < steps - 1 else 0:5d} cycles to next')
	exit()


@dataclass
class PreCalc:
	index_step: int
	index_buffer: int
	calculated: bool = False


register_start = 2
in_registers = []
in_ram = []


def add_delay(cyc, f):
	global in_registers
	global in_ram

	raminfo = None
	reginfo = None

	try:
		raminfo = next(raminfo for raminfo in in_ram if not raminfo.calculated)
	except StopIteration:
		pass
	try:
		reginfo = next(reginfo for reginfo in in_registers if not reginfo.calculated)
	except StopIteration:
		pass

	while cyc > 0:
		if raminfo and not raminfo.calculated and cyc >= 59:
			f.write(f'\tldi		r29, {raminfo.index_step}\n')
			f.write(f'\trcall	get_state\n')
			f.write(f'\tsts		pinstates + {raminfo.index_buffer + 1}, r28\n\n')
			raminfo.calculated = True
			cyc -= 59
			continue

		if reginfo and not reginfo.calculated and cyc >= 58:
			f.write(f'\tldi		r29, {reginfo.index_step}\n')
			f.write(f'\trcall	get_state\n')
			f.write(f'\tmov		r{register_start + reginfo.index_buffer}, r28\n\n')
			reginfo.calculated = True
			cyc -= 58
			continue

		if cyc >= (4 + 6):
			cyc -= (4 + 6)
			r28val = int(cyc / 3)

			if r28val > 254:
				r28val = 254

			f.write(f'	ldi		r28, {r28val + 1}\n')
			f.write(f'	rcall	delay_cycles\n')
			cyc -= 3 * r28val
			continue
		# if cyc >= 2:
		# 	cyc -= 2
		# 	f.write(f'\tlds		r28, pinstates\n')
		if cyc > 0:
			cyc -= 1
			f.write(f'\tnop\n')


with open('loop.S', 'w') as f:
	f.write("""\
# include <avr/io.h>
# define PORTS (PORTD - 0x20)
// pinstates contains the pin states for index 2-10  (index 0 and 1 are stored in r16, r28. delay between index 10 and 11 is 58 cycles. so enough to use get_state)
.data
.extern pinstates

.text
.extern delay_cycles
.extern get_state

// index 0: cycle 0  (= starts at cycle X)

.global loop
loop:
""")
	cycle = 0		# the current cycle, where the next instruction starts

	for i in range(0, steps - 1):
		print(f'{i}\r', end='')
		if cycles[i] - cycle < 3:
			add_delay(cycles[i] - cycle, f)
			regindex = len(in_registers)

			f.write(
				f'\tout		PORTS, r{register_start + regindex}')

			in_registers += [PreCalc(index_step=i, index_buffer=regindex)]

		elif cycles[i] - cycle < 58:
			add_delay(cycles[i] - 2 - cycle, f)
			ramindex = len(in_ram)

			f.write(f'\tlds 	r28,	(pinstates + {ramindex + 1})\n')
			f.write(f'\tout		PORTS, r28')

			in_ram += [PreCalc(index_step=i, index_buffer=ramindex)]
		else:
			add_delay(cycles[i] - 57 - cycle, f)

			f.write(f'\tldi		r29, {i}\n')
			f.write(f'\trcall	get_state\n')
			f.write(f'\tout		PORTS, r28')

		f.write(f'\t\t// index {i}: cycle {cycles[i]}\n\n')
		cycle = cycles[i] + 1

	add_delay(total_cycles - 2 - cycle, f)

	f.write('rjmp loop\n')


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
