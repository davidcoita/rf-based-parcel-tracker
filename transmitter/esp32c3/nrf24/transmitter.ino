#include <SPI.h>
#include <RF24.h>
#include "beacon.h"

RF24 radio(1, 7);

const byte address[5] = {0xE7, 0xE7, 0xE7, 0xE7, 0xE7};

BeaconPacket beacon = {
    .device_id = 0x00000001,
    .sequence_num = 0
};

const int SLEEP_TIME = 60;

void setup() {
  SPI.begin(4, 5, 6, 7);
  
  radio.begin();
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_LOW);
  radio.setDataRate(RF24_250KBPS);
  radio.stopListening();
}

void loop() {
  radio.powerUp();
  delay(5);
  
  beacon.sequence_num++;
  radio.write(&beacon, sizeof(BeaconPacket));
  delay(10);
  
  radio.powerDown();
  
  esp_deep_sleep(SLEEP_TIME * 1000000ULL);
}