import asyncio
from bleak import BleakScanner
from datetime import datetime
import sys

class BLETrackerReceiver:
    
    def __init__(self):
        self.tracked_devices = {}
        self.scan_count = 0
        
    async def scan_for_trackers(self):
        print("=" * 70)
        print("BLE Parcel Tracking System - Base Station Receiver")
        print("=" * 70)
        print("\nInitializing BLE scanner...\n")
        
        await asyncio.sleep(1)
        
        while True:
            self.scan_count += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] Scan #{self.scan_count} - Searching for beacons...")
            
            try:
                devices = await BleakScanner.discover(timeout=5.0)
                
                trackers_found = 0
                for device in devices:
                    if device.name and device.name.startswith("TRACK"):
                        self.process_tracker(device)
                        trackers_found += 1
                
                if trackers_found == 0:
                    print(f"  └─ No trackers detected in this scan")
                
                print()
                
            except Exception as e:
                print(f"  └─ Scan error: {e}")
                print()
            
            await asyncio.sleep(2)
    
    def process_tracker(self, device):
        try:
            if len(device.name) >= 13:
                device_id_hex = device.name[5:13]
            else:
                device_id_hex = "UNKNOWN"
            
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            if device.address not in self.tracked_devices:
                self.tracked_devices[device.address] = {
                    'device_id': device_id_hex,
                    'name': device.name,
                    'first_seen': timestamp,
                    'last_seen': timestamp,
                    'detection_count': 1
                }
                status = "NEW DEVICE"
            else:
                self.tracked_devices[device.address]['last_seen'] = timestamp
                self.tracked_devices[device.address]['detection_count'] += 1
                status = "UPDATE"
            
            count = self.tracked_devices[device.address]['detection_count']
            first_seen = self.tracked_devices[device.address]['first_seen']
            
            print(f"  [{timestamp}] {status}: {device.name}")
            print(f"    ├─ Address: {device.address}")
            print(f"    ├─ Device ID: 0x{device_id_hex}")
            print(f"    ├─ RSSI: {device.rssi} dBm")
            print(f"    ├─ Detections: {count}")
            print(f"    └─ First seen: {first_seen}")
            
            self.log_detection(timestamp, device_id_hex, device.address, 
                             device.rssi, count)
            
        except Exception as e:
            print(f"  └─ Error processing {device.address}: {e}")
    
    def log_detection(self, timestamp, device_id, address, rssi, count):
        try:
            with open("tracker_log.csv", "a") as f:
                f.write(f"{timestamp},{device_id},{address},{rssi},{count}\n")
        except Exception as e:
            print(f"  └─ Logging error: {e}")
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("TRACKING SUMMARY")
        print("=" * 70)
        print(f"\nTotal devices tracked: {len(self.tracked_devices)}")
        print(f"Total scans performed: {self.scan_count}\n")
        
        if self.tracked_devices:
            print("Device Details:")
            print("-" * 70)
            for addr, info in self.tracked_devices.items():
                print(f"\nDevice: {info['name']}")
                print(f"  ├─ ID: 0x{info['device_id']}")
                print(f"  ├─ Address: {addr}")
                print(f"  ├─ First seen: {info['first_seen']}")
                print(f"  ├─ Last seen: {info['last_seen']}")
                print(f"  └─ Total detections: {info['detection_count']}")
        
        print("\n" + "=" * 70)

async def main():
    print("\n" + "=" * 70)
    print("BLE Parcel Tracker - Raspberry Pi 5 Base Station")
    print("=" * 70)
    print("\nThis receiver scans for BLE beacons from ATtiny85 + HM-10")
    print("tracking modules and logs their presence for parcel tracking.")
    print("\nPress Ctrl+C to stop and view summary\n")
    
    await asyncio.sleep(2)
    
    try:
        with open("tracker_log.csv", "w") as f:
            f.write("timestamp,device_id,address,rssi,detection_count\n")
        print("Created tracker_log.csv for data logging\n")
    except Exception as e:
        print(f"Warning: Could not create log file: {e}\n")
    
    receiver = BLETrackerReceiver()
    
    try:
        await receiver.scan_for_trackers()
    except KeyboardInterrupt:
        print("\n\nReceiver stopped by user.")
        receiver.print_summary()
        print(f"\nData logged to: tracker_log.csv")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)