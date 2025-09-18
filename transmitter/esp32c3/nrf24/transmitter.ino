#include <SPI.h>
#include <RF24.h>
#include <EEPROM.h>
#include "beacon.h"

#define EEPROM_ID_ADDR 0

RF24 radio(1, 7);

const byte address[5] = {0xE7, 0xE7, 0xE7, 0xE7, 0xE7};

BeaconPacket beacon = {
    .device_id = UNASSIGNED_ID,
    .sequence_num = 0
};

const int SLEEP_TIME = 60;

void setup() {
  EEPROM.begin(512);
  
  SPI.begin(4, 5, 6, 7);
  
  radio.begin();
  radio.openWritingPipe(address);
  radio.openReadingPipe(1, address);
  radio.setPALevel(RF24_PA_LOW);
  radio.setDataRate(RF24_250KBPS);
  radio.stopListening();
  
  EEPROM.get(EEPROM_ID_ADDR, beacon.device_id);
  if (beacon.device_id == 0 || beacon.device_id == 0xFFFFFFFF) {
    beacon.device_id = UNASSIGNED_ID;
  }
}

void checkForCommand() {
  radio.startListening();
  delay(10);
  
  if (radio.available()) {
    uint8_t buffer[6];
    radio.read(buffer, 6);
    
    uint32_t assigned_id = *((uint32_t*)buffer);
    uint8_t command = buffer[4];
    
    if (command == 0x01 && beacon.device_id == UNASSIGNED_ID) {
      beacon.device_id = assigned_id;
      EEPROM.put(EEPROM_ID_ADDR, beacon.device_id);
      EEPROM.commit();
      delay(10);
    }
  }
  
  radio.stopListening();
}

void loop() {
  radio.powerUp();
  delay(5);
  
  checkForCommand();
  
  beacon.sequence_num++;
  radio.write(&beacon, sizeof(BeaconPacket));
  delay(10);
  
  radio.powerDown();
  
  esp_deep_sleep(SLEEP_TIME * 1000000ULL);
}