#include <stdint.h>
#include <avr/io.h>
#include <avr/sleep.h>
#include <avr/interrupt.h>
#include <avr/pgmspace.h>
#include <util/delay.h>

extern void loop();
volatile uint8_t brightness[8];
volatile uint8_t pinstates[20];	// not needed in C, just can't get initialization working in ASM

extern void i2c_init(uint8_t address);

void main()
{
	i2c_init(0x33);
	sei();
	DDRD = 0xFF;
	loop();
}
