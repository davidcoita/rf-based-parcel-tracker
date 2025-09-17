#include <SoftwareSerial.h>
#include "beacon.h"

SoftwareSerial ble(D2, D1);

BeaconPacket beacon = {
    .device_id = 0x00000001,
    .sequence_num = 0
};

const int SLEEP_TIME = 60;

void setup() {
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