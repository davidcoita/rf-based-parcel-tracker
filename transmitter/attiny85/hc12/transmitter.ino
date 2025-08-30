#include <SoftwareSerial.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include "beacon.h"

SoftwareSerial hc12(2, 1);

BeaconPacket beacon = {
    .device_id = 0x00000001,
    .sequence_num = 0
};

int SLEEP_TIME = 60;

volatile bool wakeup = false;

ISR(WDT_vect) {
  wakeup = true;
}

void setup() {
  CLKPR = 0x80;
  CLKPR = 0x02;
  
  hc12.begin(9600);
  delay(100);
}

int getSleepCycles(int sleepTime) {
  return sleepTime / 8;
}

void enterSleep() {
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  // 8s sleep
  WDTCR = (1<<WDE) | (1<<WDIE) | (1<<WDP3) | (1<<WDP0);
  sleep_enable();
  sleep_cpu();
  sleep_disable();
}

void loop() {
  beacon.sequence_num++;
  hc12.write((uint8_t*)&beacon, sizeof(BeaconPacket));
  delay(100);
  

  int cycles = getSleepCycles(SLEEP_TIME);
  
  for(int i = 0; i < cycles; i++) {
    enterSleep();
  }
}