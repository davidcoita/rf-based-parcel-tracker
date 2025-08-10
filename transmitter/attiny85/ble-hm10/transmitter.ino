#include <SoftwareSerial.h>
#include "beacon.h"

SoftwareSerial ble(2, 1);

BeaconPacket beacon = {
    .device_id = 0x00000001,
    .sequence_num = 0
};

void setup() {
    CLKPR = 0x80;
    CLKPR = 0x02;
    
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
    delay(10000);
}