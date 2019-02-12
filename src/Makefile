DEVICE     = atmega8a
CLOCK      = 20000000
ADARGS     = -c usbtiny -B 6 -p m8

main.hex: main.elf
	rm -f main.hex
	avr-objcopy -j .text -j .data -O ihex main.elf main.hex

main.elf: main.c i2c.c loop.S get_state.S delay_cycles.S
	avr-gcc -g -DF_CPU=$(CLOCK) -mmcu=$(DEVICE) -o $@ -O3 $^ -flto
	avr-size -C --mcu=$(DEVICE) $@

loop.S get_state.S: gen.py
	./$< quiet

.PHONY: dump
dump: main.elf
	# avr-objdump -d $<
	avr-objdump -Ssd $<
	# rm main.elf

.PHONY: flash
flash: main.hex
	avrdude $(ADARGS) -U flash:w:main.hex:i

.PHONY: reset
reset:
	avrdude $(ADARGS) -U lfuse:r:/tmp/test.hex:h

.PHONY: clean
clean:
	rm -f main.hex
	rm -f main.elf
	rm -f loop.S
	rm -f get_state.S
