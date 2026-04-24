# Insole Monitor Handoff

This repo is now reduced to a firmware-only handoff for the ESP32 insole integration.

The GUI was intentionally removed so another developer can build their own app on top of a simple serial data stream.

## Hardware Summary

- Board: `Adafruit Feather ESP32 V2`
- ADCs: `2x ADS1115`
- IMU: `LSM6DSOX`
- Framework: `Arduino` via PlatformIO

## Required PlatformIO Libraries

These are already listed in [`platformio.ini`](/Users/kamronsoltani/Desktop/Product%20Design/Insole%20monitor/platformio.ini#L11):

- `Adafruit ADS1X15`
- `Adafruit BusIO`
- `Adafruit LSM6DS`
- `Adafruit Unified Sensor`

## Wiring Summary

### I2C Bus 0

- ESP32 `SDA = 22`
- ESP32 `SCL = 20`
- `ADS1115 #1` at `0x48`
- `ADS1115 #2` at `0x49`

### I2C Bus 1

- ESP32 `SDA = 15`
- ESP32 `SCL = 32`
- `LSM6DSOX` at default I2C address

## Fixed FSR Mapping

The current agreed logical mapping is:

- `LeftToe -> ADS1_A0`
- `RightToe -> ADS1_A1`
- `LeftBall -> ADS1_A2`
- `RightBall -> ADS2_A0`
- `HeelLeft -> ADS2_A1`
- `HeelCenter -> ADS2_A2`
- `HeelRight -> ADS2_A3`

The main place to change this later is the mapping table in [`src/main.cpp`](/Users/kamronsoltani/Desktop/Product%20Design/Insole%20monitor/src/main.cpp#L73).

## Serial Output Format

The firmware prints one CSV row per sample:

```text
LeftToe,RightToe,LeftBall,RightBall,HeelLeft,HeelCenter,HeelRight,AccX,AccY,AccZ,GyroX,GyroY,GyroZ,IMUTempC
```

### Units

- `LeftToe ... HeelRight`
  Raw ADS1115 ADC counts
- `AccX, AccY, AccZ`
  Acceleration in `m/s^2`
- `GyroX, GyroY, GyroZ`
  Angular velocity in `rad/s`
- `IMUTempC`
  Temperature in degrees Celsius

### Serial Settings

- Baud rate: `115200`
- Stream interval: `50 ms`
- Approximate update rate: `20 Hz`

## What The Next Developer Should Know

### Main firmware file

- [`src/main.cpp`](/Users/kamronsoltani/Desktop/Product%20Design/Insole%20monitor/src/main.cpp#L1)

This file now contains:

- all hardware setup
- the fixed logical FSR mapping
- IMU configuration
- serial CSV output
- comments explaining where to edit mappings and how the stream is structured

### Best place to modify sensor meaning

If physical wiring changes, update the `kRegionMap` table in [`src/main.cpp`](/Users/kamronsoltani/Desktop/Product%20Design/Insole%20monitor/src/main.cpp#L73).

### Best place to modify stream format

If a future app needs a different CSV schema, edit:

- [`src/main.cpp`](/Users/kamronsoltani/Desktop/Product%20Design/Insole%20monitor/src/main.cpp#L109) for the header
- [`src/main.cpp`](/Users/kamronsoltani/Desktop/Product%20Design/Insole%20monitor/src/main.cpp#L208) for the data row

## Build / Upload

Build:

```bash
~/.platformio/penv/bin/pio run
```

Upload:

```bash
~/.platformio/penv/bin/pio run --target upload
```

If upload fails because the serial port is busy, close any serial monitor first.

## Handoff Intent

This repo is intentionally left in a simple state:

- firmware only
- fixed mapping
- documented serial output
- no desktop or web GUI code

That should make it easier for another person to build the next layer without reverse-engineering earlier experiments.
