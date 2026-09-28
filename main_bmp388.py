from machine import I2C, Pin
from time import sleep
from bmp388_driver import BMP388


# BMP388 -> Pico: VCC -> 3V3, GND -> GND, SDA/SDI -> GP0, SCL/SCK -> GP1.
# For I2C mode, connect CSB -> 3V3. Connect SDO -> GND for address 0x76.
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
print("I2C devices:", [hex(address) for address in i2c.scan()])
sensor = BMP388(i2c)

print("BMP388 connected at", hex(sensor.address))

while True:
    temperature, pressure = sensor.read()
    print("temperature: %.2f C, pressure: %.2f hPa" % (
        temperature,
        pressure / 100.0,
    ))
    sleep(1)
