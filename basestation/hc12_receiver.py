import serial
import struct
import time

ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)

print("...")
print("Listening")
print("...")

try:
    buffer = bytearray()
    while True:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            buffer.extend(data)
            
            print(f"Buffer length: {len(buffer)}")

            while len(buffer) >= 6:
                device_id = struct.unpack('<I', buffer[0:4])[0]
                seq = struct.unpack('<H', buffer[4:6])[0]
                
                print(f"Device: 0x{device_id:08X} | Seq: {seq}")
                
                buffer = buffer[6:]
        
        time.sleep(0.01)
        
except KeyboardInterrupt:
    ser.close()