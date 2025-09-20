# RF-Based Parcel Tracking System

Low-cost tracking modules for parcel delivery using 433MHz, 2.4GHz nRF24L01+, and BLE protocols.

## Overview

Research implementation comparing RF technologies for parcel tracking in delivery vehicles. Base station assigns unique IDs to tracking modules and monitors beacons.

## Hardware Configurations

**Transmitters (Tracking Modules)**
- ATtiny85 / ESP8266 / ESP32-C3
- HC-12 (433MHz) / nRF24L01+ (2.4GHz) / HM-10 BLE

**Receiver (Base Station)**
- Raspberry Pi 5
- Protocol-specific receiver modules

## Requirements

**Python:** `pyserial`, `spidev`, `lgpio`, `bleak`


## Usage

**Run Base Station:**

Run base station script with desired id:

```bash
python hc12_receiver.py 1
python nrf24_receiver.py 1
python ble_receiver.py 1
```
To flash the flash transmitter:
Use ArduinoIDE to upload appropriate .ino for your MCU + module combination.

## License

MIT License - see [LICENSE](LICENSE) file for details.

This project is part of the implementation of a bachelors thesis on RF-based parcel tracking systems.