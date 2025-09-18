#include <SoftwareSerial.h>
#include <EEPROM.h>
#include "beacon.h"

#define HC12_SET_PIN D3
#define EEPROM_ID_ADDR 0

SoftwareSerial hc12(D2, D1);

BeaconPacket beacon = {
    .device_id = UNASSIGNED_ID,
    .sequence_num = 0
};

const int SLEEP_TIME = 60;

void setup() {
  EEPROM.begin(512);
  
  pinMode(HC12_SET_PIN, OUTPUT);
  digitalWrite(HC12_SET_PIN, HIGH);
  
  hc12.begin(9600);
  delay(100);
  
  EEPROM.get(EEPROM_ID_ADDR, beacon.device_id);
  if (beacon.device_id == 0 || beacon.device_id == 0xFFFFFFFF) {
    beacon.device_id = UNASSIGNED_ID;
  }
}

void hc12Sleep() {
  digitalWrite(HC12_SET_PIN, LOW);
  delay(50);
}

void hc12Wake() {
  digitalWrite(HC12_SET_PIN, HIGH);
  delay(120);
}

void checkForCommand() {
  if (hc12.available() >= 5) {
    uint8_t buffer[5];
    hc12.readBytes(buffer, 5);
    
    uint32_t assigned_id = *((uint32_t*)buffer);
    uint8_t command = buffer[4];
    
    if (command == 0x01 && beacon.device_id == UNASSIGNED_ID) {
      beacon.device_id = assigned_id;
      EEPROM.put(EEPROM_ID_ADDR, beacon.device_id);
      EEPROM.commit();
      delay(10);
    }
  }
}

void loop() {
  hc12Wake();
  
  checkForCommand();
  
  beacon.sequence_num++;
  hc12.write((uint8_t*)&beacon, sizeof(BeaconPacket));
  delay(100);
  
  hc12Sleep();
  
  ESP.deepSleep(SLEEP_TIME * 1000000ULL);
}