#include <BLEDevice.h>
#include <BLEAdvertising.h>
#include "beacon.h"

BLEAdvertising *pAdvertising;

BeaconPacket beacon = {
    .device_id = 0x00000001,
    .sequence_num = 0
};

const int SLEEP_TIME = 60;

void setup() {
  char deviceName[20];
  sprintf(deviceName, "TRACK%08X", beacon.device_id);
  
  BLEDevice::init(deviceName);
  pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->setMinInterval(0x20);
  pAdvertising->setMaxInterval(0x40);
}

void loop() {
  beacon.sequence_num++;
  
  char deviceName[20];
  sprintf(deviceName, "TRACK%08X", beacon.device_id);
  
  BLEDevice::init(deviceName);
  pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->start();
  delay(100);
  pAdvertising->stop();
  
  BLEDevice::deinit(true);
  
  esp_deep_sleep(SLEEP_TIME * 1000000ULL);
}