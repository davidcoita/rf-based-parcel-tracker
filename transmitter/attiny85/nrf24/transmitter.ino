#include <SPI.h>
#include <RF24.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include <EEPROM.h>
#include "beacon.h"

#define EEPROM_ID_ADDR 0

RF24 radio(2, 3);

const byte address[5] = {0xE7, 0xE7, 0xE7, 0xE7, 0xE7};

BeaconPacket beacon = {
    .device_id = UNASSIGNED_ID,
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

int getSleepCycles(int sleepTime) {
  return sleepTime / 8;
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
      delay(10);
    }
  }
  
  radio.stopListening();
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
  radio.powerUp();
  delay(5);
  
  checkForCommand();
  
  beacon.sequence_num++;
  radio.write(&beacon, sizeof(BeaconPacket));
  delay(10);
  
  radio.powerDown();
  
  int cycles = getSleepCycles(SLEEP_TIME);
  for(int i = 0; i < cycles; i++) {
    enterSleep();
  }
}