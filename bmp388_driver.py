import time


BMP388_ADDRESSES = (0x76, 0x77)
CHIP_ID = 0x00
DATA = 0x04
PWR_CTRL = 0x1B
OSR = 0x1C
CONFIG = 0x1F
CALIBRATION = 0x31
STATUS = 0x03
DATA_READY = 0x60


def signed8(value):
    return value - 256 if value & 0x80 else value


def signed16(low_byte, high_byte):
    value = low_byte | (high_byte << 8)
    return value - 65536 if value & 0x8000 else value


class BMP388:
    def __init__(self, i2c, address=None):
        self.i2c = i2c
        if address is None:
            address = None
            for _ in range(10):
                address = next(
                    (candidate for candidate in BMP388_ADDRESSES
                     if candidate in i2c.scan()),
                    None,
                )
                if address is not None:
                    break
                time.sleep_ms(100)
        if address is None:
            raise RuntimeError("BMP388 not found. Check power, SDA, SCL, and CSB.")

        self.address = address
        chip_id = self._read(CHIP_ID, 1)[0]
        if chip_id != 0x50:
            raise RuntimeError("Unexpected BMP388 chip ID: " + hex(chip_id))

        self.calibration = self._read_calibration()
        self._write(OSR, 0x00)
        self._write(CONFIG, 0x00)
        self._write(PWR_CTRL, 0x33)
        time.sleep_ms(100)

    def _read(self, register, length):
        for attempt in range(3):
            try:
                return self.i2c.readfrom_mem(self.address, register, length)
            except OSError:
                if attempt == 2:
                    raise
                time.sleep_ms(5)

    def _write(self, register, value):
        self.i2c.writeto_mem(self.address, register, bytes((value,)))

    def _read_calibration(self):
        data = self._read(CALIBRATION, 21)
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

    def read(self):
        self._write(PWR_CTRL, 0x13)
        for _ in range(20):
            if self._read(STATUS, 1)[0] & DATA_READY == DATA_READY:
                break
            time.sleep_ms(10)
        else:
            raise RuntimeError("BMP388 measurement is not ready")

        data = self._read(DATA, 6)
        raw_pressure = data[0] | (data[1] << 8) | (data[2] << 16)
        raw_temperature = data[3] | (data[4] << 8) | (data[5] << 16)

        calibration = self.calibration
        difference = raw_temperature - calibration["t1"]
        temperature = (
            difference * calibration["t2"]
            + difference * difference * calibration["t3"]
        )

        temperature_squared = temperature * temperature
        temperature_cubed = temperature_squared * temperature
        pressure = (
            calibration["p5"]
            + calibration["p6"] * temperature
            + calibration["p7"] * temperature_squared
            + calibration["p8"] * temperature_cubed
        )
        pressure += raw_pressure * (
            calibration["p1"]
            + calibration["p2"] * temperature
            + calibration["p3"] * temperature_squared
            + calibration["p4"] * temperature_cubed
        )
        pressure_squared = raw_pressure * raw_pressure
        pressure_cubed = pressure_squared * raw_pressure
        pressure += pressure_squared * (
            calibration["p9"] + calibration["p10"] * temperature
        ) + pressure_cubed * calibration["p11"]
        return temperature, pressure
