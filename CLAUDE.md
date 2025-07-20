# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains three Python scripts for remote control and data acquisition from APS M2000 Power Analyzers via different communication interfaces. The codebase is focused on instrumentation control for electrical power measurement applications.

## Key Components

### Core Interface Scripts
- **`m2000_lan.py`** - LAN/Ethernet interface (TCP port 10733, recommended for performance)
- **`m2000_rs232.py`** - RS232 serial interface (with critical hardware handshaking requirements)
- **`m2000_usb.py`** - USB HID interface (VID/PID: 4292/34869, native drivers)

### Documentation
- **`APS_M2000_Power_Analyzer_Manual.pdf`** - Official 284-page manual (extracted as `manual_text.txt`)
- **`README.md`** - Comprehensive usage guide and troubleshooting
- **`requirements.txt`** - Python dependencies (pyserial, hidapi, optional analysis libs)

## Architecture

### Common Interface Pattern
All three scripts follow the same object-oriented architecture:

```python
class M2000_<Interface>:
    def __init__(self, connection_params)     # Interface-specific parameters
    def connect(self)                         # Establish connection with validation
    def disconnect(self)                      # Clean shutdown with LOCAL command
    def send_command(self, command)           # Send ASCII command with termination
    def read_response(self)                   # Read ASCII response until LF
    def query(self, command)                  # Combined send/receive
    def check_errors(self)                    # Query *ERR? register
    def get_measurement(self, channels, params) # Structured data acquisition
    def stream_data(self, ...)                # Continuous data collection
```

### Command Protocol
The M2000 uses a **proprietary ASCII-based protocol** (NOT SCPI):
- **Terminators**: LF, CR, FF, or NULL (commands must end with \r\n)
- **Separators**: Semicolon (;) between commands, comma (,) between fields
- **Case insensitive**
- **Commands vs Queries**:
  - Commands (*RST, *CLS, LOCAL) produce **NO response**
  - Queries (*IDN?, *ERR?, READ?) **return responses**
- **READ command syntax**: `READ?,ch1:VOLTS:ACDC` (NOT `READ? V:CH1`)
- **Parameter mapping**: V→VOLTS, A→AMPS, W→WATTS, channel format: CH1→ch1

### Measurement System
- **Channels**: CH1-CH4 (individual), VPA1-VPA3 (3-phase virtual analyzers)
- **Parameters**: V, A, W, VA, VAR, PF, FREQ, PHASE, harmonics (H1-H500)
- **Data format**: CSV strings parsed to dictionaries with `{channel}_{param}` keys

## Development Commands

### Setup and Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt

# Linux USB support
sudo apt install libhidapi-hidraw0

# Make scripts executable
chmod +x m2000_*.py
```

### Testing Interface Connections
```bash
# Test LAN connection
python3 m2000_lan.py --host 192.168.1.100 --channels CH1 --params V A W

# Test RS232 connection
python3 m2000_rs232.py --port /dev/ttyUSB0 --channels CH1 --params V A W

# Test USB connection
python3 m2000_usb.py --list
python3 m2000_usb.py --channels CH1 --params V A W
```

### Data Acquisition Examples
```bash
# High-speed LAN streaming
python3 m2000_lan.py --host IP --stream --rate 10.0 --duration 60 --log data.csv

# 3-phase power analysis
python3 m2000_lan.py --host IP --3phase

# Network device discovery
python3 m2000_lan.py --discover --network 192.168.1
```

## Critical Implementation Details

### Protocol Corrections Applied (Based on Corrected Program Info)
**Major Issue Discovered**: All scripts initially used wrong protocol assumptions
- **Error**: Assumed SCPI-like protocol with `READ? V:CH1` syntax
- **Correct**: M2000 uses proprietary format `READ?,ch1:VOLTS:ACDC`
- **Commands (*RST, *CLS)**: No response expected
- **Queries (*IDN?, *ERR?)**: Return responses
- **Multiple commands**: Use semicolon separation: `cmd1;cmd2;cmd3`

### RS232 Hardware Requirements
The RS232 implementation requires strict adherence to M2000 hardware signaling:
- **DTR signal MUST be asserted** - M2000 discards all data without DTR
- **Bi-directional hardware handshaking (RTS/CTS)** - software handshaking not supported
- **9-wire null modem cable** - all control signals (DTR, RTS, CTS, DSR) required
- **Command termination**: Must use `\r\n` (not just `\n`)
- **Timeouts**: 100ms read/write timeouts required
- **Control signal config**: Must set `cts_state` and `dsr_state`
- **USB-to-serial converters** often problematic (10ms+ latency, buffer issues)

### Performance Characteristics
- **LAN**: ~500Hz max, lowest latency, most reliable
- **RS232**: ~50Hz max, medium latency, good for legacy systems
- **USB**: ~10Hz practical max, highest latency, simplest setup

### Error Handling Strategy
All scripts implement:
1. Connection validation via `*IDN?` query expecting "APS" in response
2. Error checking via `*ERR?` command (returns 0-10 error codes)
3. Graceful shutdown sending `LOCAL` command to return M2000 to front panel control
4. Interface-specific timeout and reconnection handling

### Data Streaming Optimization
For high-throughput applications:
1. Use `READ?` once to define measurement set
2. Use `REREAD?` for subsequent readings (reduces command overhead)
3. LAN interface preferred for sustained high-speed acquisition
4. CSV logging with timestamps for data persistence

## Manual Integration

The repository includes the extracted text of the official M2000 manual in `manual_text.txt`. Key sections for development:
- Remote Control Programming (page 232)
- Command syntax and field definitions (page 243)
- RS232 control signals specification (page 233)
- Measurement command reference (page 248+)

When modifying communication protocols, always verify against the manual specifications to ensure compatibility with M2000 firmware requirements.