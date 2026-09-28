from machine import SPI, Pin
from time import sleep_ms, sleep_us


BMP388_ADDRESSES = (0x76, 0x77)
CHIP_ID = 0x00
DATA = 0x04
PWR_CTRL = 0x1B
OSR = 0x1C
CONFIG = 0x1F
CALIBRATION = 0x31


def signed8(value):
	return value - 256 if value & 0x80 else value


def signed16(low_byte, high_byte):
	value = low_byte | (high_byte << 8)
	return value - 65536 if value & 0x8000 else value


def read_registers(spi, chip_select, register, length):
	chip_select.value(0)
	sleep_us(1)
	spi.write(bytes((register | 0x80,)))
	response = spi.read(length, 0)
	chip_select.value(1)
	sleep_us(1)
	return response


def write_register(spi, chip_select, register, value):
	chip_select.value(0)
	spi.write(bytes((register & 0x7F, value)))
	chip_select.value(1)


def read_calibration(spi, chip_select):
	data = read_registers(spi, chip_select, CALIBRATION, 21)
	return {
		"t1": (data[1] << 8 | data[0]) / 0.00390625,
		"t2": signed16(data[2], data[3]) / 1073741824.0,
		"t3": signed8(data[4]) / 281474976710656.0,
		"p1": (signed16(data[5], data[6]) - 16384) / 1048576.0,
		"p2": (signed16(data[7], data[8]) - 16384) / 536870912.0,
		"p3": signed8(data[9]) / 4294967296.0,
		"p4": signed8(data[10]) / 137438953472.0,
		"p5": (data[12] << 8 | data[11]) / 0.125,
		"p6": signed16(data[14], data[13]) / 64.0,
		"p7": signed8(data[15]) / 256.0,
		"p8": signed8(data[16]) / 32768.0,
		"p9": signed16(data[17], data[18]) / 281474976710656.0,
		"p10": signed8(data[19]) / 281474976710656.0,
		"p11": signed8(data[20]) / 36893488147419103232.0,
	}


def compensate_temperature(raw_temperature, calibration):
	difference = raw_temperature - calibration["t1"]
	return difference * calibration["t2"] + difference * difference * calibration["t3"]


def compensate_pressure(raw_pressure, temperature, calibration):
	temperature_squared = temperature * temperature
	temperature_cubed = temperature_squared * temperature
	output1 = (
		calibration["p5"]
		+ calibration["p6"] * temperature
		+ calibration["p7"] * temperature_squared
		+ calibration["p8"] * temperature_cubed
	)
	output2 = raw_pressure * (
		calibration["p1"]
		+ calibration["p2"] * temperature
		+ calibration["p3"] * temperature_squared
		+ calibration["p4"] * temperature_cubed
	)
	pressure_squared = raw_pressure * raw_pressure
	pressure_cubed = pressure_squared * raw_pressure
	output3 = pressure_squared * (
		calibration["p9"] + calibration["p10"] * temperature
	) + pressure_cubed * calibration["p11"]
	return output1 + output2 + output3


def read_measurement(spi, chip_select, calibration):
	data = read_registers(spi, chip_select, DATA, 6)
	raw_pressure = data[0] | (data[1] << 8) | (data[2] << 16)
	raw_temperature = data[3] | (data[4] << 8) | (data[5] << 16)
	temperature = compensate_temperature(raw_temperature, calibration)
	pressure = compensate_pressure(raw_pressure, temperature, calibration)
	return temperature, pressure


# BMP388 SPI wiring: VCC -> 3V3, GND -> GND, SCK -> GP2,
# SDI/MOSI -> GP3, SDO/MISO -> GP4, CS/CSB -> GP5.
chip_select = Pin(5, Pin.OUT, value=1)
spi = SPI(
	0,
	baudrate=100000,
	polarity=0,
	phase=0,
	sck=Pin(2),
	mosi=Pin(3),
	miso=Pin(4),
)

chip_id = read_registers(spi, chip_select, CHIP_ID, 1)[0]
if chip_id != 0x50:
	raise RuntimeError(
		"BMP388 SPI returned " + hex(chip_id)
		+ ". Check CSB=GP5, SCK=GP2, SDI/MOSI=GP3, SDO/MISO=GP4."
	)

calibration = read_calibration(spi, chip_select)
write_register(spi, chip_select, OSR, 0x00)
write_register(spi, chip_select, CONFIG, 0x00)
write_register(spi, chip_select, PWR_CTRL, 0x33)
sleep_ms(100)
print("BMP388 connected over SPI, chip ID:", hex(chip_id))

while True:
	temperature, pressure = read_measurement(spi, chip_select, calibration)
	print("temperature: %.2f C, pressure: %.2f hPa" % (
		temperature,
		pressure / 100.0,
	))
	sleep_ms(1000)