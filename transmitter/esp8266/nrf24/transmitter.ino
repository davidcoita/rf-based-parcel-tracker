#include <SPI.h>
#include <RF24.h>
#include <EEPROM.h>
#include <ESP8266WiFi.h>

typedef struct {
    uint32_t device_id;      
    uint16_t sequence_num;   
} BeaconPacket;

#define EEPROM_ID_ADDR 0
#define UNASSIGNED_ID 0xFFFFFFFF

RF24 radio(D2, D8);

const byte address[5] = {0xE7, 0xE7, 0xE7, 0xE7, 0xE7};

BeaconPacket beacon = {
    .device_id = 0x00000001,
    .sequence_num = 0
};

const int SLEEP_TIME = 30;

void setup() {
  delay(500);
  
  Serial.begin(115200);
  while(!Serial) { delay(10); }
  
  Serial.println("\n\n=== ESP8266 Starting ===");
  Serial.flush();
  
  WiFi.mode(WIFI_OFF);
  WiFi.forceSleepBegin();
  delay(1);
  
  pinMode(LED_BUILTIN, OUTPUT);
  
  /*
  EEPROM.begin(512);
  
  uint32_t stored_id;
  EEPROM.get(EEPROM_ID_ADDR, stored_id);
  
  Serial.print("Stored ID: 0x");
  Serial.println(stored_id, HEX);
  
  if (stored_id != 0 && stored_id != 0xFFFFFFFF) {
    beacon.device_id = stored_id;
    Serial.println("Using stored ID");
    digitalWrite(LED_BUILTIN, LOW);
    delay(200);
    digitalWrite(LED_BUILTIN, HIGH);
  } else {
    beacon.device_id = UNASSIGNED_ID;
    Serial.println("UNASSIGNED - waiting for ID");
    for(int i=0; i<3; i++) {
      digitalWrite(LED_BUILTIN, LOW);
      delay(200);
      digitalWrite(LED_BUILTIN, HIGH);
      delay(200);
    }
  }
  */
  
  Serial.println(beacon.device_id, HEX);
  
  Serial.println("Initializing radio...");
  
  if (!radio.begin()) {
    Serial.println("Radio FAILED!");
    delay(100);
    radio.begin();
  } else {
    Serial.println("Radio initialized OK");
  }
  
  radio.stopListening();
  radio.openWritingPipe(address);
  radio.openReadingPipe(1, address);
  radio.setPALevel(RF24_PA_LOW);
  radio.setDataRate(RF24_1MBPS);
  radio.setChannel(76);
  radio.setPayloadSize(6);
  radio.setRetries(15, 15);
  radio.setAutoAck(true);
  radio.flush_tx();
  radio.flush_rx();
  
  Serial.println("Setup complete");
  Serial.print("Sleep interval: ");
  Serial.print(SLEEP_TIME);
  Serial.println(" seconds");
}

void loop() {
  Serial.println("\n=== WAKING UP ===");
  Serial.print("Device ID: 0x");
  Serial.println(beacon.device_id, HEX);
  Serial.print("Sequence: ");
  Serial.println(beacon.sequence_num);
  
  digitalWrite(LED_BUILTIN, LOW);
  delay(50);
  digitalWrite(LED_BUILTIN, HIGH);
  
  Serial.println("Powering up radio...");
  radio.powerUp();
  delay(150);
  
  beacon.sequence_num++;
  
  radio.stopListening();
  radio.flush_tx();
  
  Serial.println("Transmitting beacon...");
  bool success = radio.write(&beacon, sizeof(BeaconPacket));
  
  Serial.print("Transmission: ");
  Serial.println(success ? "SUCCESS" : "FAILED");
  
  if (!success) {
    Serial.println("  Retry...");
    delay(50);
    success = radio.write(&beacon, sizeof(BeaconPacket));
    Serial.print("  Retry: ");
    Serial.println(success ? "SUCCESS" : "FAILED");
  }
  
  /*
  if (beacon.device_id == UNASSIGNED_ID) {
    Serial.println("Device UNASSIGNED, listening for 10 seconds...");
    
    radio.stopListening();
    delay(10);
    radio.flush_rx();
    radio.startListening();
    
    unsigned long start = millis();
    bool got_command = false;
    
    while (millis() - start < 10000) {
      if (radio.available()) {
        uint8_t buffer[6];
        radio.read(buffer, 6);
        
        uint32_t assigned_id = *((uint32_t*)buffer);
        uint8_t command = buffer[4];
        
        Serial.print("\nGot command: 0x");
        Serial.print(command, HEX);
        Serial.print(", ID: 0x");
        Serial.println(assigned_id, HEX);
        
        if (command == 0x01) {
          beacon.device_id = assigned_id;
          
          EEPROM.put(EEPROM_ID_ADDR, beacon.device_id);
          EEPROM.commit();
          
          Serial.print("Saved ID: 0x");
          Serial.println(beacon.device_id, HEX);
          
          for(int i=0; i<3; i++) {
            digitalWrite(LED_BUILTIN, LOW);
            delay(100);
            digitalWrite(LED_BUILTIN, HIGH);
            delay(100);
          }
          
          got_command = true;
          break;
        }
      }
      
      if ((millis() - start) % 1000 == 0) {
        Serial.print(".");
      }
      
      delay(10);
    }
    
    if (!got_command) {
      Serial.println("\nNo command received");
    }
    
    radio.stopListening();
  } else {
    Serial.println("Device has ID");
  }
  */
  
  Serial.println("Device has fixed ID");
  
  radio.powerDown();
  
  Serial.print("Sleeping for ");
  Serial.print(SLEEP_TIME);
  Serial.println(" seconds...");
  Serial.println("========================\n");
  
  delay(SLEEP_TIME * 1000);
}