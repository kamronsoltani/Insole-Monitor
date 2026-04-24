#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include <Adafruit_LSM6DSOX.h>
#include <Adafruit_Sensor.h>

/*
  ---------------------------------------------------------------------------
  Insole Monitor - Firmware Handoff Version
  ---------------------------------------------------------------------------

  What this file does:
  - Reads 7 FSR channels through 2 ADS1115 ADCs.
  - Reads IMU data from the LSM6DSOX.
  - Prints a single CSV row to Serial every sample period.

  Why this version exists:
  - The Python GUI was intentionally removed.
  - This file is meant to be easy for another developer to take over.
  - The FSR mapping is fixed and documented in one place.

  IMPORTANT:
  - If the physical sensor wiring changes, the main place to update is the
    `kRegionMap` table below.
  - The serial output format is also documented below so another person can
    build a desktop app, web dashboard, data logger, or BLE bridge on top.
*/

// ---------------------------------------------------------------------------
// I2C BUS / DEVICE CONFIGURATION
// ---------------------------------------------------------------------------

// Bus 0 is used for both ADS1115 boards.
// static constexpr int SDA_BUS0 = 22;
// static constexpr int SCL_BUS0 = 20;

static constexpr int SDA_BUS0 = SDA;
static constexpr int SCL_BUS0 = SCL;

// Bus 1 is used for the IMU.
static constexpr int SDA_BUS1 = 15;
static constexpr int SCL_BUS1 = 32;

static constexpr uint8_t ADS1_ADDRESS = 0x48;
static constexpr uint8_t ADS2_ADDRESS = 0x49;
static constexpr uint8_t IMU_ADDRESS = LSM6DS_I2CADDR_DEFAULT;

// 50 ms = 20 Hz stream.
static constexpr uint32_t STREAM_INTERVAL_MS = 50;

// ---------------------------------------------------------------------------
// SENSOR OBJECTS
// ---------------------------------------------------------------------------

Adafruit_ADS1115 ads1;
Adafruit_ADS1115 ads2;
Adafruit_LSM6DSOX imu;

// ---------------------------------------------------------------------------
// LOGICAL FOOT REGIONS
// ---------------------------------------------------------------------------

/*
  These are the 7 logical regions used everywhere else in the project.

  The current agreed mapping is:
  - LeftToe
  - RightToe
  - LeftBall
  - RightBall
  - HeelLeft
  - HeelCenter
  - HeelRight
*/
enum FootRegion : uint8_t {
  LEFT_TOE = 0,
  RIGHT_TOE,
  LEFT_BALL,
  RIGHT_BALL,
  HEEL_LEFT,
  HEEL_CENTER,
  HEEL_RIGHT,
  FOOT_REGION_COUNT
};

struct RegionConfig {
  const char *csvLabel;
  const char *hardwareChannel;
  Adafruit_ADS1115 *ads;
  uint8_t adsChannel;
};

/*
  ---------------------------------------------------------------------------
  MAIN FSR MAPPING TABLE
  ---------------------------------------------------------------------------

  This is the key handoff table.

  If someone later discovers:
  - "LeftToe is actually wired to ADS2 A0"
  - "HeelCenter and HeelRight are swapped"
  - etc.

  ...they should update only this table first.
*/
RegionConfig kRegionMap[FOOT_REGION_COUNT] = {
    {"LeftToe", "ADS1_A0", &ads1, 0},
    {"RightToe", "ADS1_A1", &ads1, 1},
    {"LeftBall", "ADS1_A2", &ads1, 2},
    {"RightBall", "ADS2_A0", &ads2, 0},
    {"HeelLeft", "ADS2_A1", &ads2, 1},
    {"HeelCenter", "ADS2_A2", &ads2, 2},
    {"HeelRight", "ADS2_A3", &ads2, 3},
};

uint32_t lastSampleAtMs = 0;

// ---------------------------------------------------------------------------
// HELPER FUNCTIONS
// ---------------------------------------------------------------------------

int16_t readRegion(FootRegion region) {
  const RegionConfig &config = kRegionMap[region];
  return config.ads->readADC_SingleEnded(config.adsChannel);
}

void printMappingLegend() {
  Serial.println("Fixed sensor mapping:");
  for (uint8_t region = 0; region < FOOT_REGION_COUNT; ++region) {
    Serial.print("  ");
    Serial.print(kRegionMap[region].csvLabel);
    Serial.print(" -> ");
    Serial.println(kRegionMap[region].hardwareChannel);
  }
}

void printCsvHeader() {
  /*
    Serial CSV format:

    LeftToe,RightToe,LeftBall,RightBall,HeelLeft,HeelCenter,HeelRight,
    AccX,AccY,AccZ,GyroX,GyroY,GyroZ,IMUTempC

    Units:
    - FSR values are raw ADS1115 ADC counts.
    - Accel values are m/s^2 from Adafruit Unified Sensor.
    - Gyro values are rad/s from Adafruit Unified Sensor.
    - Temperature is degrees C.
  */
  for (uint8_t region = 0; region < FOOT_REGION_COUNT; ++region) {
    Serial.print(kRegionMap[region].csvLabel);
    Serial.print(",");
  }
  Serial.println("AccX,AccY,AccZ,GyroX,GyroY,GyroZ,IMUTempC");
}

void initAdsBoards() {

  // Both ADC boards share the same ESP32 I2C bus.
  Wire.begin(SDA_BUS0, SCL_BUS0);
  
  ads1.setGain(GAIN_TWOTHIRDS);
  ads2.setGain(GAIN_TWOTHIRDS);

  ads1.setDataRate(RATE_ADS1115_128SPS);
  if (!ads1.begin(ADS1_ADDRESS, &Wire)) {
    Serial.println("ERROR: ADS1115 #1 (0x48) not found.");
    Serial.println("Check wiring and confirm ADDR is tied for address 0x48.");
    while (true) {
      delay(10);
    }
  }

  ads2.setDataRate(RATE_ADS1115_128SPS);
  if (!ads2.begin(ADS2_ADDRESS, &Wire)) {
    Serial.println("ERROR: ADS1115 #2 (0x49) not found.");
    Serial.println("Check wiring and confirm ADDR is tied for address 0x49.");
    while (true) {
      delay(10);
    }
  }
}

void initImu() {
  // The ESP32 core exposes Wire1 for the second I2C bus.
  Wire1.begin(SDA_BUS1, SCL_BUS1);

  if (!imu.begin_I2C(IMU_ADDRESS, &Wire1)) {
    Serial.println("ERROR: LSM6DSOX not found on Wire1.");
    Serial.println("Check IMU wiring on SDA=15 and SCL=32.");
    while (true) {
      delay(10);
    }
  }

  // These settings are reasonable defaults for a general integration test.
  imu.setAccelRange(LSM6DS_ACCEL_RANGE_4_G);
  imu.setGyroRange(LSM6DS_GYRO_RANGE_500_DPS);
  imu.setAccelDataRate(LSM6DS_RATE_104_HZ);
  imu.setGyroDataRate(LSM6DS_RATE_104_HZ);
}

void printStartupSummary() {
  Serial.println();
  Serial.println("=== Insole Monitor Integration Test ===");
  Serial.println();
  Serial.println("Devices found:");
  Serial.println("  ADS1115 #1 at 0x48");
  Serial.println("  ADS1115 #2 at 0x49");
  Serial.println("  LSM6DSOX on Wire1");
  Serial.println();
  printMappingLegend();
  Serial.println("-------------------------------------------------------");
  printCsvHeader();
}

// ---------------------------------------------------------------------------
// ARDUINO ENTRY POINTS
// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  initAdsBoards();
  initImu();
  printStartupSummary();
}

void loop() {
  if (millis() - lastSampleAtMs < STREAM_INTERVAL_MS) {
    delay(5);
    return;
  }
  lastSampleAtMs = millis();

  // Read all FSR regions in logical order so the CSV columns stay stable.
  const int16_t leftToe = readRegion(LEFT_TOE);
  const int16_t rightToe = readRegion(RIGHT_TOE);
  const int16_t leftBall = readRegion(LEFT_BALL);
  const int16_t rightBall = readRegion(RIGHT_BALL);
  const int16_t heelLeft = readRegion(HEEL_LEFT);
  const int16_t heelCenter = readRegion(HEEL_CENTER);
  const int16_t heelRight = readRegion(HEEL_RIGHT);

  // Read one full IMU event packet.
  sensors_event_t accel;
  sensors_event_t gyro;
  sensors_event_t temp;
  imu.getEvent(&accel, &gyro, &temp);

  // Print one CSV row.
  Serial.print(leftToe);
  Serial.print(",");
  Serial.print(rightToe);
  Serial.print(",");
  Serial.print(leftBall);
  Serial.print(",");
  Serial.print(rightBall);
  Serial.print(",");
  Serial.print(heelLeft);
  Serial.print(",");
  Serial.print(heelCenter);
  Serial.print(",");
  Serial.print(heelRight);
  Serial.print(",");

  Serial.print(accel.acceleration.x, 3);
  Serial.print(",");
  Serial.print(accel.acceleration.y, 3);
  Serial.print(",");
  Serial.print(accel.acceleration.z, 3);
  Serial.print(",");

  Serial.print(gyro.gyro.x, 3);
  Serial.print(",");
  Serial.print(gyro.gyro.y, 3);
  Serial.print(",");
  Serial.print(gyro.gyro.z, 3);
  Serial.print(",");

  Serial.println(temp.temperature, 2);
}
