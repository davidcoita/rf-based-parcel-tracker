#include <SoftwareSerial.h>
#include <EEPROM.h>
#include "beacon.h"

#define EEPROM_ID_ADDR 0

SoftwareSerial ble(D2, D1);

BeaconPacket beacon = {
    .device_id = UNASSIGNED_ID,
    .sequence_num = 0
};

const int SLEEP_TIME = 60;

void setup() {
  EEPROM.begin(512);
  
  EEPROM.get(EEPROM_ID_ADDR, beacon.device_id);
  if (beacon.device_id == 0 || beacon.device_id == 0xFFFFFFFF) {
    beacon.device_id = UNASSIGNED_ID;
  }
  
  ble.begin(9600);
  delay(2000);
  
  char nameCmd[30];
  sprintf(nameCmd, "AT+NAMETRACK%08X", beacon.device_id);
  ble.print(nameCmd);
  delay(500);
  
  ble.print("AT+DELO2");
  delay(500);
  
  ble.print("AT+ADVI5");
  delay(500);
}

void loop() {
  beacon.sequence_num++;
  
  ESP.deepSleep(SLEEP_TIME * 1000000ULL);
}