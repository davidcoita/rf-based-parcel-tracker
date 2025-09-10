#include <SoftwareSerial.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include "beacon.h"

#define HC12_SET_PIN 3

SoftwareSerial hc12(2, 1);

BeaconPacket beacon = {
    .device_id = 0x00000001,
    .sequence_num = 0
};

const int SLEEP_TIME = 60;
volatile bool wakeup = false;

ISR(WDT_vect) {
  wakeup = true;
}

void setup() {
  cli();
  wdt_reset();
  MCUSR &= ~(1<<WDRF);
  WDTCR |= (1<<WDCE) | (1<<WDE);
  WDTCR = 0x00;
  sei();
  
  CLKPR = 0x80;
  CLKPR = 0x02;
  
  pinMode(HC12_SET_PIN, OUTPUT);
  digitalWrite(HC12_SET_PIN, HIGH);
  
  hc12.begin(2400);
  delay(100);
}

int getSleepCycles(int sleepTime) {
  return sleepTime / 8;
}

void hc12Sleep() {
  digitalWrite(HC12_SET_PIN, LOW);
  delay(50);
}

void hc12Wake() {
  digitalWrite(HC12_SET_PIN, HIGH);
  delay(120);
}

void enterSleep() {
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  
  cli();
  wdt_reset();
  MCUSR &= ~(1<<WDRF);
  WDTCR |= (1<<WDCE) | (1<<WDE);
  WDTCR = (1<<WDIE) | (1<<WDP3) | (1<<WDP0);
  sei();
  
  sleep_enable();
  sleep_cpu();
  sleep_disable();
  
  wdt_disable();
}

void loop() {
  hc12Wake();
  
  beacon.sequence_num++;
  hc12.write((uint8_t*)&beacon, sizeof(BeaconPacket));
  delay(100);
  
  hc12Sleep();
  
  int cycles = getSleepCycles(SLEEP_TIME);
  for(int i = 0; i < cycles; i++) {
    enterSleep();
  }
}