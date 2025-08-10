import asyncio
from bleak import BleakScanner

async def test_ble():
    print("---")
    print("Scanning for 5 seconds")
    print("---")
    devices = await BleakScanner.discover(timeout=5.0)
    
    print(f"\nFound {len(devices)} devices:")
    for device in devices:
        if device.name and device.name.startswith("TRACK"):
            print(f"TRACKER: {device.name} | {device.address} | {device.rssi} dBm")
        elif device.name:
            print(f"  {device.name} | {device.address}")

asyncio.run(test_ble())