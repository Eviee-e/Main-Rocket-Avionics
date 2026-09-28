from machine import I2C, Pin
from time import sleep

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


def read_calibration(i2c, address):
    data = i2c.readfrom_mem(address, CALIBRATION, 21)
    return {
        "t1": (data[1] << 8 | data[0]) / 0.00390625,
        "t2": signed16(data[2], data[3]) / 1073741824.0,
        "t3": signed8(data[4]) / 281474976710656.0,
        "p1": (signed16(data[5], data[6]) - 16384) / 1048576.0,
        "p2": (signed16(data[7], data[8]) - 16384) / 536870912.0,
        "p3": signed8(data[9]) / 4294967296.0,
        "p4": signed8(data[10]) / 137438953472.0,
        "p5": (data[12] << 8 | data[11]) / 0.125,
        "p6": (data[14] << 8 | data[13]) / 64.0,
        "p7": signed8(data[15]) / 256.0,
        "p8": signed8(data[16]) / 32768.0,
        "p9": signed16(data[17], data[18]) / 0.5,
        "p10": signed8(data[19]) / 8192.0,
        "p11": signed8(data[20]) / 131072.0,
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


def read_measurement(i2c, address, calibration):
    data = i2c.readfrom_mem(address, DATA, 6)
    raw_pressure = data[0] | (data[1] << 8) | (data[2] << 16)
    raw_temperature = data[3] | (data[4] << 8) | (data[5] << 16)
    temperature = compensate_temperature(raw_temperature, calibration)
    pressure = compensate_pressure(raw_pressure, temperature, calibration)
    return temperature, pressure


# BMP388 -> Pico: VCC to 3V3, GND to GND, SDA/SDI to GP0, SCL/SCK to GP1.
# Connect CSB to 3V3 for I2C mode and SDO to GND for address 0x76.
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
addresses = i2c.scan()
print("I2C devices:", [hex(address) for address in addresses])

bmp388_address = next(
    (address for address in BMP388_ADDRESSES if address in addresses), None
)
if bmp388_address is None:
    raise RuntimeError("BMP388 not found. Check power, SDA, SCL, and CSB.")

chip_id = i2c.readfrom_mem(bmp388_address, CHIP_ID, 1)[0]
if chip_id != 0x50:
    raise RuntimeError("Unexpected BMP388 chip ID: " + hex(chip_id))

calibration = read_calibration(i2c, bmp388_address)
i2c.writeto_mem(bmp388_address, OSR, b"\x00")
i2c.writeto_mem(bmp388_address, CONFIG, b"\x00")
i2c.writeto_mem(bmp388_address, PWR_CTRL, b"\x33")
print("BMP388 connected at", hex(bmp388_address), "chip ID:", hex(chip_id))

while True:
    temperature, pressure = read_measurement(i2c, bmp388_address, calibration)
    print("temperature: %.2f C, pressure: %.2f hPa" % (
        temperature,
        pressure / 100.0,
    ))
    sleep(1)
