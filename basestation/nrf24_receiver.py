import spidev
import lgpio
import struct
import time
from datetime import datetime
import sys

class NRF24Receiver:
    def __init__(self, station_id=1):
        self.station_id = station_id
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
        self.next_device_id = (station_id << 24) | 0x00000001
        self.log_file = f"nrf24_station{station_id}_log.csv"
        
        with open(self.log_file, "w") as f:
            f.write("timestamp,station_id,device_id,sequence,status\n")
        
        self.init_radio()
    
    def assign_device_id(self):
        device_id = self.next_device_id
        self.next_device_id += 1
        return device_id
    
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
        self.write_register(0x01, 0x3F)
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
        
        lgpio.gpio_write(self.h, self.CSN, 0)
        self.spi.xfer2([0x20] + address)
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
    
    def send_id_assignment(self, device_id):
        lgpio.gpio_write(self.h, self.CE, 0)
        self.write_register(0x00, 0x0E)
        
        cmd_packet = struct.pack('<IB', device_id, 0x01)
        cmd_packet = cmd_packet + b'\x00' * (6 - len(cmd_packet))
        
        lgpio.gpio_write(self.h, self.CSN, 0)
        self.spi.xfer2([0xA0] + list(cmd_packet))
        lgpio.gpio_write(self.h, self.CSN, 1)
        
        lgpio.gpio_write(self.h, self.CE, 1)
        time.sleep(0.001)
        lgpio.gpio_write(self.h, self.CE, 0)
        
        self.write_register(0x00, 0x0F)
        lgpio.gpio_write(self.h, self.CE, 1)
        
        print(f"  └─ Sent ID assignment: 0x{device_id:08X}")
    
    def check_packet_loss(self, device_id, sequence):
        if device_id in self.packet_count:
            expected = (self.packet_count[device_id] + 1) % 65536
            if sequence != expected:
                lost = (sequence - expected) % 65536
                return lost
        return 0
    
    def log_packet(self, timestamp, device_id, sequence, status):
        with open(self.log_file, "a") as f:
            f.write(f"{timestamp},{self.station_id},{device_id:08X},{sequence},{status}\n")
    
    def process_packet(self, payload):
        try:
            device_id = struct.unpack('<I', bytes(payload[0:4]))[0]
            sequence = struct.unpack('<H', bytes(payload[4:6]))[0]
            
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            if device_id == 0xFFFFFFFF:
                new_id = self.assign_device_id()
                print(f"[{timestamp}] NEW UNASSIGNED DEVICE")
                print(f"  ├─ Temp ID: 0x{device_id:08X}")
                print(f"  ├─ Assigned ID: 0x{new_id:08X}")
                self.send_id_assignment(new_id)
                self.log_packet(timestamp, new_id, sequence, "assigned")
                return
            
            lost = self.check_packet_loss(device_id, sequence)
            if lost > 0:
                print(f"  └─ Packet loss: {lost} packets")
            
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
            
            self.log_packet(timestamp, device_id, sequence, status.lower())
            
        except Exception as e:
            print(f"  └─ Error processing packet: {e}")
    
    def listen(self):
        print("=" * 70)
        print(f"nRF24L01+ Base Station {self.station_id}")
        print("=" * 70)
        print("\nListening for beacon packets...\n")
        
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
            for device_id, info in self.tracked_devices.items():
                print(f"\nDevice ID: 0x{device_id:08X}")
                print(f"  ├─ First seen: {info['first_seen']}")
                print(f"  ├─ Total packets: {info['packet_count']}")
                print(f"  └─ Last sequence: {self.packet_count.get(device_id, 0)}")
        
        print(f"\nData logged to: {self.log_file}")
    
    def cleanup(self):
        lgpio.gpio_write(self.h, self.CE, 0)
        lgpio.gpiochip_close(self.h)
        self.spi.close()

if __name__ == "__main__":
    station_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    receiver = NRF24Receiver(station_id)
    try:
        receiver.listen()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        receiver.cleanup()
        sys.exit(0)