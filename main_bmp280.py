from machine import I2C, Pin
from time import sleep


BMP280_ADDRESSES = (0x76, 0x77)


def signed_16(value):
    return value - 65536 if value & 0x8000 else value


def read_u16(data, index):
    return data[index] | (data[index + 1] << 8)


def read_s16(data, index):
    return signed_16(read_u16(data, index))


class BMP280:
    def __init__(self, i2c):
        self.i2c = i2c
        found = [address for address in i2c.scan()
                 if address in BMP280_ADDRESSES]
        if not found:
            raise RuntimeError("BMP280 not found. Check wiring and I2C address.")

        self.address = found[0]
        calibration = i2c.readfrom_mem(self.address, 0x88, 24)

        self.dig_t1 = read_u16(calibration, 0)
        self.dig_t2 = read_s16(calibration, 2)
        self.dig_t3 = read_s16(calibration, 4)
        self.dig_p1 = read_u16(calibration, 6)
        self.dig_p2 = read_s16(calibration, 8)
        self.dig_p3 = read_s16(calibration, 10)
        self.dig_p4 = read_s16(calibration, 12)
        self.dig_p5 = read_s16(calibration, 14)
        self.dig_p6 = read_s16(calibration, 16)
        self.dig_p7 = read_s16(calibration, 18)
        self.dig_p8 = read_s16(calibration, 20)
        self.dig_p9 = read_s16(calibration, 22)

        # Normal mode, temperature x1, pressure x1.
        i2c.writeto_mem(self.address, 0xF4, b'\x27')
        # Standby 1 second, filter off.
        i2c.writeto_mem(self.address, 0xF5, b'\xA0')
        sleep(1)

    def read(self):
        data = self.i2c.readfrom_mem(self.address, 0xF7, 6)
        raw_pressure = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_temperature = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)

        var1 = (((raw_temperature >> 3) - (self.dig_t1 << 1))
                * self.dig_t2) >> 11
        var2 = (((((raw_temperature >> 4) - self.dig_t1)
                  * ((raw_temperature >> 4) - self.dig_t1)) >> 12)
                * self.dig_t3) >> 14
        temperature_fine = var1 + var2
        temperature = (temperature_fine * 5 + 128) >> 8

        var1 = temperature_fine - 128000
        var2 = var1 * var1 * self.dig_p6
        var2 += (var1 * self.dig_p5) << 17
        var2 += self.dig_p4 << 35
        var1 = ((var1 * var1 * self.dig_p3) >> 8)
        var1 += ((var1 * self.dig_p2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_p1) >> 33

        if var1 == 0:
            raise RuntimeError("Invalid BMP280 pressure calibration")

        pressure = 1048576 - raw_pressure
        pressure = (((pressure << 31) - var2) * 3125) // var1
        var1 = (self.dig_p9 * (pressure >> 13) * (pressure >> 13)) >> 25
        var2 = (self.dig_p8 * pressure) >> 19
        pressure = ((pressure + var1 + var2) >> 8) + (self.dig_p7 << 4)

        return temperature / 100.0, pressure / 25600.0


# BMP280 -> Pico:
# VCC/VIN -> 3V3, GND -> GND, SDA/SDI -> GP0, SCL/SCK -> GP1.
# Connect CSB -> 3V3 for I2C. SDO -> GND gives address 0x76;
# SDO -> 3V3 gives address 0x77.
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
print("I2C devices:", [hex(address) for address in i2c.scan()])
sensor = BMP280(i2c)
print("BMP280 connected at", hex(sensor.address))

while True:
    temperature, pressure = sensor.read()
    print("temperature: %.2f C, pressure: %.2f hPa" % (
        temperature,
        pressure,
    ))
    sleep(1)
