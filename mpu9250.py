from machine import I2C
from time import sleep_ms


MPU9250_ADDRESSES = (0x68, 0x69)
AK8963_ADDRESS = 0x0C


class MPU9250:
	def __init__(self, i2c, address=None):
		self.i2c = i2c
		if address is None:
			address = next(
				(address for address in MPU9250_ADDRESSES if address in i2c.scan()),
				None,
			)
		if address is None:
			raise RuntimeError("MPU9250 not found. Check VCC, GND, SDA, and SCL.")
		self.address = address
		self._write(0x6B, 0x00)
		sleep_ms(100)
		who_am_i = self._read(0x75, 1)[0]
		if who_am_i not in (0x70, 0x71, 0x73):
			raise RuntimeError("Unexpected MPU9250/6500 WHO_AM_I value")
		self.is_mpu9250 = who_am_i in (0x71, 0x73)
		self._write(0x1B, 0x00)
		self._write(0x1C, 0x00)
		self._write(0x1A, 0x03)
		self.mag_adjustment = self._setup_magnetometer() if self.is_mpu9250 else None

	def _write(self, register, value):
		self.i2c.writeto_mem(self.address, register, bytes((value,)))

	def _read(self, register, length):
		return self.i2c.readfrom_mem(self.address, register, length)

	def _setup_magnetometer(self):
		self._write(0x37, 0x02)
		if AK8963_ADDRESS not in self.i2c.scan():
			return None
		self.i2c.writeto_mem(AK8963_ADDRESS, 0x0A, b"\x00")
		sleep_ms(10)
		self.i2c.writeto_mem(AK8963_ADDRESS, 0x0A, b"\x0F")
		sleep_ms(10)
		adjustment = self.i2c.readfrom_mem(AK8963_ADDRESS, 0x10, 3)
		self.i2c.writeto_mem(AK8963_ADDRESS, 0x0A, b"\x00")
		sleep_ms(10)
		self.i2c.writeto_mem(AK8963_ADDRESS, 0x0A, b"\x16")
		return tuple((value - 128) / 256.0 + 1.0 for value in adjustment)

	def read_accel_gyro(self):
		data = self._read(0x3B, 14)
		values = []
		for index in range(0, 14, 2):
			value = (data[index] << 8) | data[index + 1]
			values.append(value - 65536 if value & 0x8000 else value)
		accel = tuple(value / 16384.0 for value in values[0:3])
		temperature = values[3] / 333.87 + 21.0
		gyro = tuple(value / 131.0 for value in values[4:7])
		return accel, gyro, temperature

	def read_magnetometer(self):
		if self.mag_adjustment is None:
			return None
		status = self.i2c.readfrom_mem(AK8963_ADDRESS, 0x02, 1)[0]
		if not status & 0x01:
			return None
		data = self.i2c.readfrom_mem(AK8963_ADDRESS, 0x03, 7)
		if data[6] & 0x08:
			return None
		values = []
		for index in range(0, 6, 2):
			value = data[index] | (data[index + 1] << 8)
			values.append(value - 65536 if value & 0x8000 else value)
		return tuple(
			value * adjustment * 0.15
			for value, adjustment in zip(values, self.mag_adjustment)
		)
