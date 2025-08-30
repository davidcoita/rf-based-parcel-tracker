#include <SPI.h>
#include <RF24.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include "beacon.h"

RF24 radio(2, 3);

const byte address[5] = {0xE7, 0xE7, 0xE7, 0xE7, 0xE7};

BeaconPacket beacon = {
    .device_id = 0x00000001,
    .sequence_num = 0
};

volatile bool wakeup = false;

ISR(WDT_vect) {
  wakeup = true;
}

void setup() {
  CLKPR = 0x80;
  CLKPR = 0x02;
  
  radio.begin();
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_LOW);
  radio.stopListening();
}

void enterSleep() {
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  WDTCR = (1<<WDE) | (1<<WDIE) | (1<<WDP3) | (1<<WDP0);
  sleep_enable();
  sleep_cpu();
  sleep_disable();
}

void loop() {
  beacon.sequence_num++;
  radio.write(&beacon, sizeof(BeaconPacket));
  delay(100);
  
  radio.powerDown();
  
  for(int i = 0; i < 5; i++) {
    enterSleep();
  }
  
  radio.powerUp();
  delay(10);
}