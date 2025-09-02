import spidev
import lgpio
import struct
import time
from datetime import datetime
import sys

class NRF24Receiver:
    
    def __init__(self):
        self.h = lgpio.gpiochip_open(0)
        self.CE = 25
        self.CSN = 8
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 5000000
        
        lgpio.gpio_claim_output(self.h, self.CE)
        lgpio.gpio_claim_output(self.h, self.CSN)
        
        self.tracked_devices = {}
        self.packet_count = {}
        
        self.init_radio()
    
    def write_register(self, reg, value):
        lgpio.gpio_write(self.h, self.CSN, 0)
        self.spi.xfer2([0x20 | reg, value])
        lgpio.gpio_write(self.h, self.CSN, 1)
    
    def read_register(self, reg):
        lgpio.gpio_write(self.h, self.CSN, 0)
        result = self.spi.xfer2([reg & 0x1F, 0x00])
        lgpio.gpio_write(self.h, self.CSN, 1)
        return result[1]
    
    def init_radio(self):
        lgpio.gpio_write(self.h, self.CE, 0)
        time.sleep(0.1)
        
        self.write_register(0x00, 0x0F)
        self.write_register(0x01, 0x00)
        self.write_register(0x02, 0x03)
        self.write_register(0x03, 0x03)
        self.write_register(0x04, 0x5F)
        self.write_register(0x05, 0x4C)
        self.write_register(0x06, 0x07)
        self.write_register(0x11, 6)
        
        address = [0xE7, 0xE7, 0xE7, 0xE7, 0xE7]
        lgpio.gpio_write(self.h, self.CSN, 0)
        self.spi.xfer2([0x2A] + address)
        lgpio.gpio_write(self.h, self.CSN, 1)
        
        self.write_register(0x07, 0x70)
        
        lgpio.gpio_write(self.h, self.CE, 1)
        time.sleep(0.01)
        
        print("nRF24L01+ receiver initialized")
    
    def read_payload(self):
        lgpio.gpio_write(self.h, self.CSN, 0)
        payload = self.spi.xfer2([0x61] + [0xFF] * 6)
        lgpio.gpio_write(self.h, self.CSN, 1)
        return payload[1:7]
    
    def check_packet_loss(self, device_id, sequence):
        if device_id in self.packet_count:
            expected = (self.packet_count[device_id] + 1) % 65536
            if sequence != expected:
                lost = (sequence - expected) % 65536
                return lost
        return 0
    
    def process_packet(self, payload):
        try:
            device_id = struct.unpack('<I', bytes(payload[0:4]))[0]
            sequence = struct.unpack('<H', bytes(payload[4:6]))[0]
            
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            lost = self.check_packet_loss(device_id, sequence)
            if lost > 0:
                print(f"  └─ Packet loss detected: {lost} packets")
            
            self.packet_count[device_id] = sequence
            
            if device_id not in self.tracked_devices:
                self.tracked_devices[device_id] = {
                    'first_seen': timestamp,
                    'packet_count': 1
                }
                status = "NEW DEVICE"
            else:
                self.tracked_devices[device_id]['packet_count'] += 1
                status = "UPDATE"
            
            count = self.tracked_devices[device_id]['packet_count']
            
            print(f"[{timestamp}] {status}")
            print(f"  ├─ Device ID: 0x{device_id:08X}")
            print(f"  ├─ Sequence: {sequence}")
            print(f"  └─ Total packets: {count}")
            
            self.log_packet(timestamp, device_id, sequence, count)
            
        except Exception as e:
            print(f"  └─ Error processing packet: {e}")
    
    def log_packet(self, timestamp, device_id, sequence, count):
        try:
            with open("nrf24_log.csv", "a") as f:
                f.write(f"{timestamp},{device_id:08X},{sequence},{count}\n")
        except Exception as e:
            print(f"  └─ Logging error: {e}")
    
    def listen(self):
        print("=" * 70)
        print("nRF24L01+ Parcel Tracking Receiver")
        print("=" * 70)
        print("\nListening for beacon packets...\n")
        
        try:
            with open("nrf24_log.csv", "w") as f:
                f.write("timestamp,device_id,sequence,packet_count\n")
            print("Created nrf24_log.csv for data logging\n")
        except Exception as e:
            print(f"Warning: Could not create log file: {e}\n")
        
        try:
            while True:
                status = self.read_register(0x07)
                
                if status & 0x40:
                    payload = self.read_payload()
                    self.process_packet(payload)
                    self.write_register(0x07, 0x40)
                    print()
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n\nReceiver stopped.")
            self.print_summary()
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("TRACKING SUMMARY")
        print("=" * 70)
        print(f"\nTotal devices tracked: {len(self.tracked_devices)}\n")
        
        if self.tracked_devices:
            print("Device Details:")
            print("-" * 70)
            for device_id, info in self.tracked_devices.items():
                print(f"\nDevice ID: 0x{device_id:08X}")
                print(f"  ├─ First seen: {info['first_seen']}")
                print(f"  ├─ Total packets: {info['packet_count']}")
                print(f"  └─ Last sequence: {self.packet_count.get(device_id, 0)}")
        
        print("\n" + "=" * 70)
        print("Data logged to: nrf24_log.csv")
    
    def cleanup(self):
        lgpio.gpio_write(self.h, self.CE, 0)
        lgpio.gpiochip_close(self.h)
        self.spi.close()

if __name__ == "__main__":
    receiver = NRF24Receiver()
    try:
        receiver.listen()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        receiver.cleanup()
        sys.exit(0)