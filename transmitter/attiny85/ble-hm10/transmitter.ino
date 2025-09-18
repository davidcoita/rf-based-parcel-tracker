#include <SoftwareSerial.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include <EEPROM.h>
#include "beacon.h"

#define EEPROM_ID_ADDR 0

SoftwareSerial ble(2, 1);

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
    
    EEPROM.get(EEPROM_ID_ADDR, beacon.device_id);
    if (beacon.device_id == 0 || beacon.device_id == 0xFFFFFFFF) {
        beacon.device_id = UNASSIGNED_ID;
    }
    
    ble.begin(2400);
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

int getSleepCycles(int sleepTime) {
  return sleepTime / 8;
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
    beacon.sequence_num++;
    
    int cycles = getSleepCycles(SLEEP_TIME);
    for(int i = 0; i < cycles; i++) {
        enterSleep();
    }
}