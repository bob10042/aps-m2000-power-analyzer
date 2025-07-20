# APS M2000 Power Analyzer Remote Control Scripts

Three fully functional Python scripts for controlling the APS M2000 Power Analyzer via different interfaces.

## Files

- `m2000_rs232.py` - RS232 serial interface
- `m2000_lan.py` - LAN/Ethernet interface (enhanced with unit formatting)
- `m2000_usb.py` - USB HID interface
- `m2000_units.py` - Unit formatting and display helper module
- `requirements.txt` - Python dependencies
- `APS_M2000_Power_Analyzer_Manual.pdf` - Official manual (284 pages)

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# For USB interface on Linux, you may also need:
sudo apt install libhidapi-hidraw0

# Make scripts executable
chmod +x m2000_*.py
```

## Quick Start Examples

### RS232 Interface
```bash
# Single measurement from channel 1
python3 m2000_rs232.py --port /dev/ttyUSB0 --channels CH1 --params V A W

# Stream data for 30 seconds at 2Hz
python3 m2000_rs232.py --port /dev/ttyUSB0 --stream --duration 30 --rate 2.0

# Monitor all 4 channels
python3 m2000_rs232.py --port COM3 --channels CH1 CH2 CH3 CH4 --params V A
```

### LAN Interface (Recommended for best performance)
```bash
# Discover M2000 devices on network
python3 m2000_lan.py --discover --network 192.168.1

# Single measurement
python3 m2000_lan.py --host 192.168.1.100 --channels CH1 --params V A W PF FREQ

# High-speed streaming to CSV file
python3 m2000_lan.py --host 192.168.1.100 --stream --rate 10.0 --duration 60 --log power_data.csv

# 3-phase power analysis
python3 m2000_lan.py --host 192.168.1.100 --3phase
```

### USB Interface
```bash
# List available USB devices
python3 m2000_usb.py --list

# Single measurement
python3 m2000_usb.py --channels CH1 --params V A W

# Stream data (USB is slower than LAN/RS232)
python3 m2000_usb.py --stream --duration 30 --rate 1.0 --log usb_data.csv
```

## Configuration Requirements

### RS232 Setup
- **Port**: /dev/ttyUSB0 (Linux) or COM1 (Windows)
- **Baud Rate**: 115200 (recommended), 57600, 19200, or 9600
- **Cable**: 9-wire female-female null modem cable, fully wired
- **Handshaking**: Bi-directional hardware (RTS/CTS) - MANDATORY
- **Control Signals**: DTR MUST be asserted (M2000 discards data without DTR)
- **Settings**: 8-N-1, all control signals (DTR, RTS, CTS, DSR) required

### LAN Setup
- **Port**: TCP 10733 (fixed)
- **IP Address**: Configure M2000 with static IP, DHCP, or Auto-IP
- **Cable**: Standard CAT5/CAT5e Ethernet cable
- **Network**: Direct connection or through switch/router

### USB Setup
- **VID/PID**: 4292/34869 (fixed for M2000)
- **Driver**: None required (uses native HID)
- **Cable**: Standard USB A-B cable
- **Permissions**: May require sudo/admin rights on some systems

## Available Channels

- **CH1, CH2, CH3, CH4**: Individual measurement channels
- **VPA1, VPA2, VPA3**: Virtual Power Analyzers (3-phase calculations)

## Available Parameters

- **V**: Voltage (RMS)
- **A**: Current (RMS)  
- **W**: Real Power
- **VA**: Apparent Power
- **VAR**: Reactive Power
- **PF**: Power Factor
- **FREQ**: Frequency
- **PHASE**: Phase Angle

## Performance Comparison

| Interface | Max Sample Rate | Latency | Reliability | Best Use Case |
|-----------|----------------|---------|-------------|---------------|
| LAN       | ~500 Hz        | Low     | Excellent   | High-speed data acquisition |
| RS232     | ~50 Hz         | Medium  | Good        | Legacy systems, long cables |
| USB       | ~10 Hz         | High    | Good        | Simple setup, no network |

## Script Features

### Common Features (all scripts)
- Error checking and recovery
- Single measurements and continuous streaming
- CSV data logging
- Comprehensive command-line options
- Graceful shutdown (Ctrl+C)

### LAN-specific Features
- Network device discovery
- 3-phase power analysis
- High-speed streaming (up to 500 Hz)
- Connection timeout handling
- **Automatic unit formatting** (V, mV, μV / A, mA, μA / W, mW, μW etc.)
- **CSV with unit headers** for data analysis

### RS232-specific Features
- Multiple baud rate support
- Hardware handshaking validation
- USB-to-serial adapter compatibility

### USB-specific Features
- Multiple device enumeration
- HID report handling
- Device path resolution

## Command Reference

### M2000 Commands Used
```
*CLS        - Clear interface
*IDN?       - Get identification
*ERR?       - Check errors
READ?       - Read measurements
REREAD?     - Repeat last read (faster)
LOCAL       - Return to local control
HOLD,0/1    - Disable/enable measurement hold
```

### Measurement Examples
```
READ? V:CH1                    # Channel 1 voltage
READ? V:CH1,A:CH1,W:CH1       # Multiple parameters
READ? W:VPA1                   # 3-phase total power
READ? V:CH1:H1                # Fundamental voltage
READ? THDF:CH1                # Total harmonic distortion
```

## Troubleshooting

### RS232 Issues
- **DTR Signal**: If DTR not asserted, M2000 treats data as interference and discards it
- **Cable Wiring**: Must be 9-wire null modem with ALL control signals (DTR, RTS, CTS, DSR)
- **USB Converters**: Many have poor performance (10ms+ latency) and buffer issues
  - Use direct RS232 port if possible
  - If using USB converter, limit packets to 64 characters max
  - Add delays between commands if experiencing data loss
  - Ensure converter supports ALL control signals
- **Control Signal Test**: If DTR unavailable, tie DSR and DTR together in cable
- **Handshaking**: MUST use hardware (RTS/CTS) - software handshaking not supported
- Try different baud rates if connection unstable
- Check COM port permissions and driver installation

### LAN Issues
- Verify M2000 IP address
- Check network connectivity (ping test)
- Ensure port 10733 not blocked by firewall
- Try discovery mode to find devices

### USB Issues
- Install hidapi: `pip install hidapi`
- Check USB cable connection
- Verify device permissions
- Try different USB ports

### General Issues
- Ensure M2000 is powered on
- Check interface is enabled in M2000 settings
- Verify Python dependencies installed
- Use `--help` for command options

## Data Format

### CSV Output Format
```
Timestamp,CH1_V,CH1_A,CH1_W
0.000,230.45,1.234,284.2
0.200,230.48,1.235,284.5
0.400,230.42,1.233,284.0
```

### Console Output Format (with automatic unit scaling)
```
[    0.00s] CH1_V=   230.450 V CH1_A=      1.2 mA CH1_W=   284.2 mW
[    0.20s] CH1_V=   230.480 V CH1_A=      1.2 mA CH1_W=   284.5 mW  
[    0.40s] CH1_V=   230.420 V CH1_A=      1.2 mA CH1_W=   284.0 mW
```

### Measurement Table Format
```
Measurement Results:
-------------------

CH1:
       A:       1.2 mA
    FREQ:    50.000 Hz
      PF:       0.9850
       V:    230.450 V
       W:     284.2 mW
```

## License

These scripts are provided as-is for interfacing with APS M2000 Power Analyzers. Refer to the official M2000 manual for complete command reference and specifications.