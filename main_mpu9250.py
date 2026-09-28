from machine import I2C, Pin
from time import sleep_ms
from mpu9250 import MPU9250


# MPU9250: VCC -> 3V3, GND -> GND, SDA -> GP0, SCL -> GP1.
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
devices = i2c.scan()
print("I2C devices:", [hex(address) for address in devices])
if not devices:
	raise RuntimeError(
		"No I2C devices found. Check SDA=GP0, SCL=GP1, VCC=3V3, and GND."
	)

sensor = MPU9250(i2c)
print("MPU9250/6500 connected")

while True:
	accel, gyro, temperature = sensor.read_accel_gyro()
	magnetometer = sensor.read_magnetometer()
	print("accel g:", accel)
	print("gyro dps:", gyro)
	print("temperature C: %.2f" % temperature)
	print("mag uT:", magnetometer)
	print()
	sleep_ms(500)