import asyncio
from bleak import BleakScanner
from datetime import datetime

class BLEReceiver:
    def __init__(self, station_id=1):
        self.station_id = station_id
        self.tracked_devices = {}
        self.log_file = f"ble_station{station_id}_log.csv"
        
        with open(self.log_file, "w") as f:
            f.write("timestamp,station_id,device_id,rssi,status\n")
    
    def log_packet(self, timestamp, device_id, rssi, status):
        with open(self.log_file, "a") as f:
            f.write(f"{timestamp},{self.station_id},{device_id:08X},{rssi},{status}\n")
    
    def process_device(self, device_id, rssi):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
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
        print(f"  ├─ RSSI: {rssi} dBm")
        print(f"  └─ Total packets: {count}")
        
        self.log_packet(timestamp, device_id, rssi, status.lower())
    
    async def listen(self):
        print("=" * 70)
        print(f"BLE Base Station {self.station_id}")
        print("=" * 70)
        print("\nScanning for BLE beacons...\n")
        
        try:
            while True:
                devices = await BleakScanner.discover(timeout=1.0)
                
                for device in devices:
                    if device.name and device.name.startswith("TRACK"):
                        try:
                            device_id = int(device.name[5:], 16)
                            self.process_device(device_id, device.rssi)
                            print()
                        except ValueError:
                            pass
                
                await asyncio.sleep(0.1)
                
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
                print(f"  └─ Total packets: {info['packet_count']}")
        
        print(f"\nData logged to: {self.log_file}")

if __name__ == "__main__":
    import sys
    station_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    receiver = BLEReceiver(station_id)
    try:
        asyncio.run(receiver.listen())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)