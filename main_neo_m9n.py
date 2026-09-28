from machine import UART, Pin
from time import sleep_ms


# u-blox NEO-M9N -> Raspberry Pi Pico
# NEO-M9N TX  -> Pico GP5 (UART1 RX)
# NEO-M9N RX  -> Pico GP4 (UART1 TX)
# NEO-M9N GND -> Pico GND
# NEO-M9N VCC/VIN -> suitable 3.3 V supply; check your breakout board

gps = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

while True:
    if gps.any():
        message = gps.readline()
        if message is not None:
            try:
                print(message.decode("ascii").strip())
            except UnicodeError:
                pass
    sleep_ms(100)