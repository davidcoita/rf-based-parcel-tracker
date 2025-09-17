import serial
import struct
import time
from datetime import datetime

class HC12Receiver:
    def __init__(self, station_id=1, port='/dev/ttyAMA0', baudrate=9600):
        self.station_id = station_id
        self.ser = serial.Serial(port, baudrate, timeout=0.1)
        self.tracked_devices = {}
        self.next_device_id = (station_id << 24) | 0x00000001
        self.packet_count = {}
        self.log_file = f"hc12_station{station_id}_log.csv"
        
        with open(self.log_file, "w") as f:
            f.write("timestamp,station_id,device_id,sequence,status\n")
    
    def assign_device_id(self):
        device_id = self.next_device_id
        self.next_device_id += 1
        return device_id
    
    def send_id_assignment(self, device_id):
        cmd_packet = struct.pack('<IB', device_id, 0x01)
        self.ser.write(cmd_packet)
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
    
    def process_beacon(self, device_id, sequence):
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
    
    def listen(self):
        print("=" * 70)
        print(f"HC-12 Base Station {self.station_id}")
        print("=" * 70)
        print("\nListening for beacon packets...\n")
        
        buffer = bytearray()
        
        try:
            while True:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    buffer.extend(data)
                    
                    while len(buffer) >= 6:
                        device_id = struct.unpack('<I', buffer[0:4])[0]
                        sequence = struct.unpack('<H', buffer[4:6])[0]
                        
                        self.process_beacon(device_id, sequence)
                        print()
                        
                        buffer = buffer[6:]
                
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
        self.ser.close()

if __name__ == "__main__":
    import sys
    station_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    receiver = HC12Receiver(station_id)
    try:
        receiver.listen()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        receiver.cleanup()
        sys.exit(0)