#include <SoftwareSerial.h>
#include "beacon.h"

// RX, TX
SoftwareSerial hc12(2, 1);

BeaconPacket beacon = {
    .device_id = 0x00000001,
    .sequence_num = 0
};

void setup() {
  CLKPR = 0x80;
  CLKPR = 0x02;
  
  hc12.begin(9600);
  delay(100);
}

void loop() {
  beacon.sequence_num++;
  hc12.write((uint8_t*)&beacon, sizeof(BeaconPacket));
  delay(5000);
}



