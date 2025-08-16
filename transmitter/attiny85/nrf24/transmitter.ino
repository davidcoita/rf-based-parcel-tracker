#include <SPI.h>
#include <RF24.h>
#include "beacon.h"

 // CE, CSN pin
RF24 radio(2, 3);

const byte address[5] = {0xE7, 0xE7, 0xE7, 0xE7, 0xE7};

BeaconPacket beacon = {
    .device_id = 0x00000001,
    .sequence_num = 0
};

void setup() {
  CLKPR = 0x80;
  CLKPR = 0x02;
  
  radio.begin();
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_LOW);
  radio.stopListening();
}

void loop() {
  beacon.sequence_num++;
  radio.write(&beacon, sizeof(BeaconPacket));
  delay(5000);
}