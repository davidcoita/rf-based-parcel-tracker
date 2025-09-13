#include <SoftwareSerial.h>
#include "beacon.h"

#define HC12_SET_PIN D3

SoftwareSerial hc12(D2, D1);

BeaconPacket beacon = {
    .device_id = 0x00000001,
    .sequence_num = 0
};

const int SLEEP_TIME = 60;

void setup() {
  pinMode(HC12_SET_PIN, OUTPUT);
  digitalWrite(HC12_SET_PIN, HIGH);
  
  hc12.begin(9600);
  delay(100);
}

void hc12Sleep() {
  digitalWrite(HC12_SET_PIN, LOW);
  delay(50);
}

void hc12Wake() {
  digitalWrite(HC12_SET_PIN, HIGH);
  delay(120);
}

void loop() {
  hc12Wake();
  
  beacon.sequence_num++;
  hc12.write((uint8_t*)&beacon, sizeof(BeaconPacket));
  delay(100);
  
  hc12Sleep();
  
  ESP.deepSleep(SLEEP_TIME * 1000000ULL);
}