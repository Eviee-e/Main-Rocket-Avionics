# Main Rocket Avionics

An embedded-systems learning and portfolio project exploring how a Raspberry Pi Pico running MicroPython can communicate with common pressure, inertial, and GPS modules. The repository contains focused sensor bring-up programs and driver experiments rather than a single integrated avionics application.

This overview is written for recruiters and engineering hiring teams evaluating practical work with microcontrollers, peripheral buses, sensor registers, and measurement processing. It describes what is present in the code today and distinguishes that work from capabilities that would require further implementation and validation.

## Project At A Glance

- **Platform:** Raspberry Pi Pico-class MicroPython board
- **Language:** MicroPython / Python
- **Interfaces explored:** I2C, SPI, and UART
- **Sensors explored:** BMP388, BMP280, MPU9250-family IMU, and u-blox NEO-M9N GPS
- **Current form:** Independent examples, each focused on one sensor or interface
- **Automated tests:** None included
- **Flight readiness:** Not flight-qualified; bench and educational use only

## Engineering Work

The examples explore the lower-level steps involved in bringing up embedded sensors:

- Configuring I2C, SPI, and UART peripherals with MicroPython's `machine` API.
- Reading and writing sensor registers and working with binary measurement data.
- Reading factory calibration coefficients and applying temperature and pressure compensation for barometric sensors.
- Converting raw inertial measurements into scaled acceleration, angular velocity, and temperature readings.
- Polling for measurement readiness and handling selected I2C read failures in the reusable BMP388 driver.
- Printing sensor measurements and receiving GPS serial text for interactive bench inspection.
- Converting latitude and longitude from supported NMEA GGA sentences to decimal degrees, and displaying fix status, satellite count, and the reported altitude field.

The repository also makes the current boundaries visible: examples run separately, do not combine measurements into a common telemetry stream, and do not implement a flight-control or navigation stack.

## Hardware And Interfaces

| Device | Example files | Interface | Purpose |
| --- | --- | --- | --- |
| BMP388 barometer / temperature sensor | `main.py`, `main_bmp388.py`, `bmp388.py` | I2C or SPI, depending on the example | Read compensated pressure and temperature measurements. |
| BMP280 barometer / temperature sensor | `main1.py` | I2C | Read pressure and temperature using BMP280 calibration data. |
| MPU9250-family inertial measurement unit | `mpu9250.py`, `main_mpu9250.py` | I2C | Read accelerometer, gyroscope, and temperature data; the demo also attempts magnetometer readings. |
| u-blox NEO-M9N GPS module | `main_neo_m9n.py`, `neo-m9n.py` | UART1 or UART0, depending on the example | `main_neo_m9n.py` displays received serial lines; `neo-m9n.py` parses selected GGA sentences and displays fix status, coordinates, satellite count, and altitude. |

The scripts contain example Pico GPIO assignments, including I2C on GP0/GP1, SPI on GP2-GP5, UART1 on GP4/GP5, and UART0 on GP0/GP1 for `neo-m9n.py` at 38,400 baud. These assignments belong to individual examples, not a combined wiring plan; pins are reused by different demos. Check each script and the documentation for the specific breakout board before connecting hardware. Confirm supply voltage and logic-level compatibility for the exact boards in use.

## Repository Guide

| File | Role |
| --- | --- |
| `bmp388_driver.py` | Reusable BMP388 I2C driver experiment, including calibration handling, compensation, readiness polling, and retry behavior. |
| `main_bmp388.py` | BMP388 I2C polling example that uses `bmp388_driver.py`. |
| `bmp388.py` | BMP388 SPI polling example. |
| `main.py` | Separate BMP388 I2C experiment with its own inline register and compensation implementation. |
| `main_bmp280.py` | SPI barometer experiment that communicates with a BMP388. The filename is historical/misleading; it does not select a BMP280. |
| `main1.py` | BMP280 I2C implementation and polling example. |
| `mpu9250.py` | MPU9250-family I2C register access and measurement scaling. |
| `main_mpu9250.py` | IMU demonstration script using `mpu9250.py`, with magnetometer readings when available. |
| `main_neo_m9n.py` | UART1 receive loop for displaying raw GPS module text. |
| `neo-m9n.py` | UART0 GPS example that converts latitude/longitude from `$GNGGA` and `$GPGGA` sentences to decimal degrees and displays fix status, satellite count, and altitude. It does not parse `$GPRMC` despite the broader wording in its function docstring. |
| `.vscode/extensions.json` | Suggested VS Code extensions for working in this project. |

## Running An Example

### Requirements

- A Raspberry Pi Pico or compatible MicroPython board.
- A matching sensor breakout board and suitable wiring for the selected example.
- MicroPython firmware installed on the board.
- A serial connection and an editor/tool that can run scripts on the board, such as Thonny.

The code uses MicroPython-provided modules such as `machine` and `time`, along with the project's local driver modules. There is no host-side package manifest; an external Python package installation is not currently part of the setup.

### Steps

1. Connect one sensor using the pin assignments in its selected example. These scripts are independent; do not assume that their pin maps can be combined.
2. Open the desired script in a MicroPython-capable editor and select the connected board/interpreter.
3. For `main_bmp388.py`, also copy `bmp388_driver.py` to the board. For `main_mpu9250.py`, also copy `mpu9250.py`. The GPS examples are standalone; use the UART pins and baud rate specified by the selected script.
4. Run one example and inspect its output in the serial/REPL console. The polling examples continue until interrupted; stop them with the editor's stop control or a keyboard interrupt.

Use the file descriptions above to select the sensor and transport. In particular, `main_bmp280.py` is a BMP388 SPI example despite its name.

## Current Scope And Limitations

- These are separate bring-up and polling examples, not a consolidated avionics program. They do not synchronize or fuse measurements from multiple sensors.
- `main_neo_m9n.py` prints raw received serial text. `neo-m9n.py` parses only `$GNGGA` and `$GPGGA` sentences for fix status, latitude, longitude, satellite count, and altitude; it does not parse `$GPRMC`, decode velocity or time, or produce a structured navigation solution.
- The GGA parser does not validate NMEA checksums and has limited malformed-field handling. GPS parsing and fix behavior should be tested against captured receiver output before being relied upon.
- The IMU example reads scaled sensor values; it does not estimate attitude or orientation.
- There is no data logger, telemetry protocol, command interface, actuator output, or flight-control logic.
- No automated test suite, recorded test vectors, or documented hardware validation results are included. Hardware-dependent behavior should be verified on the intended board and sensor revision.
- The BMP388 implementations are not yet fully consistent: pressure compensation scaling for coefficients P9-P11 differs between `main.py` / `main_bmp280.py` and `bmp388_driver.py` / `bmp388.py`. Resolve that difference against the BMP388 datasheet and known-good reference measurements before relying on pressure output.
- Firmware versions and a complete, reproducible bench setup are not yet documented.

## Safety And Data Handling

This repository is educational sensor-interface work, not a flight-qualified or safety-certified avionics system. It has no demonstrated fault-tolerant acquisition, redundant sensing, validated timing, environmental qualification, or flight-test evidence. Do not use it to control or make safety-critical decisions for a rocket or other vehicle.

GPS modules can emit live location data. Treat captured serial output and logs as sensitive location information, and do not publish real tracking data in issues, screenshots, or test artifacts.

## Possible Next Engineering Steps

1. Reconcile BMP388 compensation formulas against the datasheet and add reference-vector tests for both I2C and SPI paths.
2. Add repeatable host-side tests for sensor scaling, byte decoding, BMP compensation, and GPS coordinate/NMEA parsing, with hardware-independent mocks for bus access.
3. Document exact breakout-board models, wiring, firmware versions, startup behavior, and expected measurement ranges.
4. Extend GPS parsing with validated sentence handling and timestamps, then define a common sample format if an integrated telemetry demonstration is desired.
5. Define and verify error handling, sampling timing, and data-quality behavior before expanding toward any higher-level system.

These are future improvements, not features currently implemented in this repository.