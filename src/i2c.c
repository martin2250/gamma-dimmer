#include <avr/io.h>
#include <util/twi.h>
#include <avr/interrupt.h>

extern volatile uint8_t brightness[];

void i2c_init(uint8_t address)
{
	// load address into TWI address register
	TWAR = (address << 1);
	// set the TWCR to enable address matching and enable TWI, clear TWINT, enable TWI interrupt
	TWCR = (1<<TWIE) | (1<<TWEA) | (1<<TWINT) | (1<<TWEN);
}

// 0xFF means receive buffer address next
uint8_t buffer_address = 0xFF;

ISR(TWI_vect){
	uint8_t i2c_twsr = (TWSR & 0xF8);

	// own address has been acknowledged
	if(i2c_twsr == TW_SR_SLA_ACK )
	{
		buffer_address = 0xFF;

		// clear TWI interrupt flag, prepare to receive next byte and acknowledge
		TWCR |= (1<<TWIE) | (1<<TWINT) | (1<<TWEA) | (1<<TWEN);
		return;
	}

	// data has been received in slave receiver mode
	if( i2c_twsr  == TW_SR_DATA_ACK )
	{
		uint8_t i2c_data = TWDR;

		if(buffer_address == 0xFF)
		{
			buffer_address = i2c_data % 8;

			// clear TWI interrupt flag, prepare to receive next byte and acknowledge
			TWCR |= (1<<TWIE) | (1<<TWINT) | (1<<TWEA) | (1<<TWEN);
		}
		else
		{
			brightness[buffer_address % 8] = i2c_data;
			buffer_address = buffer_address + 1;

			if(buffer_address < 8)
				// clear TWI interrupt flag, prepare to receive next byte and acknowledge
				TWCR |= (1<<TWIE) | (1<<TWINT) | (1<<TWEA) | (1<<TWEN);
			else
				// clear TWI interrupt flag, prepare to receive next byte, do not acknowledge
				TWCR |= (1<<TWIE) | (1<<TWINT) | (0<<TWEA) | (1<<TWEN);
		}
		return;
	}

	// device has been addressed to be a transmitter
	if( i2c_twsr  == TW_ST_DATA_ACK )
	{
		uint8_t i2c_data = TWDR;

		if( buffer_address == 0xFF ){
			buffer_address = i2c_data % 8;
		}

		TWDR = brightness[buffer_address % 8];
		buffer_address = buffer_address + 1;

		if(buffer_address < 8)
			// clear TWI interrupt flag, prepare to send next byte and receive acknowledge
			TWCR |= (1<<TWIE) | (1<<TWINT) | (1<<TWEA) | (1<<TWEN);
		else
			// clear TWI interrupt flag, prepare to send next byte and receive no acknowledge
			TWCR |= (1<<TWIE) | (1<<TWINT) | (0<<TWEA) | (1<<TWEN);

		return;
	}

	// if none of the above apply prepare TWI to be addressed again
	TWCR |= (1<<TWIE) | (1<<TWEA) | (1<<TWEN);
	return;
}
