#!/usr/bin/env python3
"""
APS M2000 Power Analyzer - USB HID Interface
Fully functional script for remote control via USB HID
Requires: pip install hidapi
"""

import hid
import time
import sys
import argparse
import struct


class M2000_USB:
    def __init__(self, vid=4292, pid=34869, timeout=5000):
        """
        Initialize USB HID connection to M2000 Power Analyzer
        
        Args:
            vid: Vendor ID (4292 for APS M2000)
            pid: Product ID (34869 for APS M2000)
            timeout: Read timeout in milliseconds
        """
        self.vid = vid
        self.pid = pid
        self.timeout = timeout
        self.device = None
        self.connected = False
        
    def list_devices(self):
        """List all M2000 USB devices"""
        devices = hid.enumerate(self.vid, self.pid)
        return devices
    
    def connect(self, device_index=0):
        """
        Establish USB HID connection
        
        Args:
            device_index: Index of device to connect to (0 for first device)
        """
        try:
            # List available devices
            devices = self.list_devices()
            if not devices:
                print(f"No M2000 devices found (VID:{self.vid}, PID:{self.pid})")
                return False
            
            if device_index >= len(devices):
                print(f"Device index {device_index} not available. Found {len(devices)} device(s)")
                return False
            
            device_info = devices[device_index]
            print(f"Connecting to M2000 USB device:")
            print(f"  Manufacturer: {device_info.get('manufacturer_string', 'Unknown')}")
            print(f"  Product: {device_info.get('product_string', 'Unknown')}")
            print(f"  Serial: {device_info.get('serial_number', 'Unknown')}")
            print(f"  Path: {device_info['path'].decode('utf-8')}")
            
            # Open the device
            self.device = hid.device()
            self.device.open(self.vid, self.pid)
            
            # Set read timeout
            self.device.set_nonblocking(False)
            
            # Wait for connection to stabilize
            time.sleep(0.2)
            
            # Initialize device using correct M2000 protocol
            self.send_command('*RST')  # Reset device - no response
            self.send_command('*CLS')  # Clear device - no response
            time.sleep(0.1)
            
            # Check connection with query (queries return responses)
            response = self.query('*IDN?')
            
            if response and 'APS' in response:
                self.connected = True
                print(f"Connected to: {response}")
                return True
            else:
                print(f"Unexpected response: {response}")
                return False
                
        except Exception as e:
            print(f"USB connection failed: {e}")
            print("Make sure:")
            print("1. M2000 is powered on and USB cable connected")
            print("2. USB drivers are installed")
            print("3. You have permission to access USB devices")
            print("4. hidapi is installed: pip install hidapi")
            return False
    
    def disconnect(self):
        """Close USB connection"""
        if self.device:
            try:
                if self.connected:
                    self.send_command('LOCAL')  # Return to local control
                    time.sleep(0.1)
                self.device.close()
            except:
                pass
            finally:
                self.connected = False
                self.device = None
                print("USB connection closed")
    
    def send_command(self, command):
        """Send command to M2000 via USB HID"""
        if not self.connected or not self.device:
            raise Exception("Not connected to M2000")
        
        try:
            # Add line feed terminator and encode to ASCII
            cmd_str = command + '\n'
            cmd_bytes = cmd_str.encode('ascii')
            
            # USB HID requires specific packet format
            # The M2000 uses 64-byte HID reports
            packet_size = 64
            
            # Send data in chunks if necessary
            for i in range(0, len(cmd_bytes), packet_size - 1):
                chunk = cmd_bytes[i:i + packet_size - 1]
                
                # Create HID report (first byte is report ID, usually 0)
                report = [0] + list(chunk) + [0] * (packet_size - len(chunk) - 1)
                
                # Send the report
                bytes_written = self.device.write(report)
                if bytes_written < 0:
                    raise Exception("USB write failed")
            
        except Exception as e:
            print(f"Send command error: {e}")
            raise
    
    def read_response(self):
        """Read response from M2000 via USB HID"""
        if not self.connected or not self.device:
            raise Exception("Not connected to M2000")
        
        try:
            response = ""
            start_time = time.time()
            
            while True:
                # Check timeout
                if (time.time() - start_time) * 1000 > self.timeout:
                    raise Exception("Read timeout")
                
                # Read HID report
                try:
                    data = self.device.read(64, timeout_ms=100)
                    if not data:
                        continue
                        
                    # Extract ASCII data (skip report ID at index 0)
                    for byte_val in data[1:]:
                        if byte_val == 0:  # Null terminator
                            break
                        elif byte_val == 10:  # Line feed - end of response
                            return response
                        elif byte_val == 13:  # Carriage return - skip
                            continue
                        elif 32 <= byte_val <= 126:  # Printable ASCII
                            response += chr(byte_val)
                        else:
                            break  # Invalid character
                            
                except Exception as read_error:
                    # No data available yet, continue waiting
                    time.sleep(0.01)
                    continue
            
        except Exception as e:
            print(f"Read response error: {e}")
            return None
    
    def query(self, command):
        """Send query command and return response"""
        self.send_command(command)
        return self.read_response()
    
    def check_errors(self):
        """Check for interface errors"""
        error_code = self.query('*ERR?')
        if error_code and error_code != '0':
            print(f"M2000 Error Code: {error_code}")
            return int(error_code)
        return 0
    
    def get_measurement(self, channels=['CH1'], parameters=['V', 'A', 'W']):
        """
        Get measurements from specified channels
        
        Args:
            channels: List of channels ['CH1', 'CH2', 'CH3', 'CH4', 'VPA1', 'VPA2', 'VPA3']
            parameters: List of parameters ['V', 'A', 'W', 'VA', 'VAR', 'PF', 'FREQ']
        
        Returns:
            Dictionary with measurement data
        """
        # Build READ command using correct M2000 syntax
        read_fields = []
        for param in parameters:
            for channel in channels:
                # Convert parameter names to M2000 format
                m2000_param = param
                if param == 'V':
                    m2000_param = 'VOLTS'
                elif param == 'A':
                    m2000_param = 'AMPS'
                elif param == 'W':
                    m2000_param = 'WATTS'
                
                # Use M2000 command format: READ?,ch1:VOLTS:ACDC
                read_fields.append(f"READ?,{channel.lower()}:{m2000_param}:ACDC")
        
        # Send multiple READ commands (can combine with semicolons)
        command = ";".join(read_fields)
        response = self.query(command)
        
        if response:
            values = response.split(',')
            results = {}
            
            idx = 0
            for param in parameters:
                for channel in channels:
                    if idx < len(values):
                        try:
                            results[f"{channel}_{param}"] = float(values[idx])
                        except ValueError:
                            results[f"{channel}_{param}"] = values[idx]
                        idx += 1
            
            return results
        return None
    
    def stream_data(self, channels=['CH1'], parameters=['V', 'A', 'W'], 
                   duration=10, sample_rate=2.0, log_file=None):
        """
        Stream measurement data for specified duration
        
        Args:
            channels: List of channels to monitor
            parameters: List of parameters to read
            duration: Duration in seconds (0 = infinite)
            sample_rate: Samples per second (USB is slower, max ~10Hz practical)
            log_file: Optional CSV file to log data
        """
        print(f"Streaming data from {channels} for {duration}s at {sample_rate}Hz")
        print("Note: USB interface is slower than LAN/RS232")
        if log_file:
            print(f"Logging to: {log_file}")
        print("Press Ctrl+C to stop\n")
        
        # Set up initial READ command using correct M2000 syntax
        read_fields = []
        for param in parameters:
            for channel in channels:
                # Convert parameter names to M2000 format
                m2000_param = param
                if param == 'V':
                    m2000_param = 'VOLTS'
                elif param == 'A':
                    m2000_param = 'AMPS'
                elif param == 'W':
                    m2000_param = 'WATTS'
                
                # Use M2000 command format: READ?,ch1:VOLTS:ACDC
                read_fields.append(f"READ?,{channel.lower()}:{m2000_param}:ACDC")
        
        command = ";".join(read_fields)
        
        # Prepare CSV header
        if log_file:
            header = "Timestamp"
            for param in parameters:
                for channel in channels:
                    header += f",{channel}_{param}"
            header += "\n"
            
            with open(log_file, 'w') as f:
                f.write(header)
        
        start_time = time.time()
        sample_count = 0
        
        try:
            while True:
                sample_start = time.time()
                
                # Check duration
                if duration > 0 and (sample_start - start_time) > duration:
                    break
                
                # Get measurement
                if sample_count == 0:
                    # First reading - use READ?
                    response = self.query(command)
                else:
                    # Subsequent readings - use REREAD? for speed
                    response = self.query('REREAD?')
                
                if response:
                    values = response.split(',')
                    timestamp = sample_start - start_time
                    
                    # Format console output
                    output = f"[{timestamp:8.2f}s] "
                    idx = 0
                    for param in parameters:
                        for channel in channels:
                            if idx < len(values):
                                try:
                                    val = float(values[idx])
                                    output += f"{channel}_{param}={val:>8.3f} "
                                except ValueError:
                                    output += f"{channel}_{param}={values[idx]:>8} "
                                idx += 1
                    
                    print(output)
                    sample_count += 1
                    
                    # Log to file
                    if log_file:
                        log_line = f"{timestamp:.3f}"
                        for value in values:
                            log_line += f",{value}"
                        log_line += "\n"
                        
                        with open(log_file, 'a') as f:
                            f.write(log_line)
                
                # Wait for next sample (accounting for processing time)
                elapsed = time.time() - sample_start
                sleep_time = max(0, (1.0 / sample_rate) - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print(f"\nStreaming stopped. Collected {sample_count} samples")


def main():
    parser = argparse.ArgumentParser(description='APS M2000 USB Interface')
    parser.add_argument('--list', action='store_true',
                       help='List available M2000 USB devices')
    parser.add_argument('--device', type=int, default=0,
                       help='Device index to connect to (default: 0)')
    parser.add_argument('--channels', nargs='+', default=['CH1'],
                       choices=['CH1', 'CH2', 'CH3', 'CH4', 'VPA1', 'VPA2', 'VPA3'],
                       help='Channels to monitor (default: CH1)')
    parser.add_argument('--params', nargs='+', default=['V', 'A', 'W'],
                       choices=['V', 'A', 'W', 'VA', 'VAR', 'PF', 'FREQ', 'PHASE'],
                       help='Parameters to read (default: V A W)')
    parser.add_argument('--stream', action='store_true',
                       help='Stream data continuously')
    parser.add_argument('--duration', type=float, default=10,
                       help='Stream duration in seconds (default: 10)')
    parser.add_argument('--rate', type=float, default=2.0,
                       help='Sample rate in Hz (default: 2.0, USB is slower)')
    parser.add_argument('--log', type=str,
                       help='CSV file to log streaming data')
    parser.add_argument('--timeout', type=int, default=5000,
                       help='Read timeout in milliseconds (default: 5000)')
    
    args = parser.parse_args()
    
    # Create M2000 interface
    m2000 = M2000_USB(timeout=args.timeout)
    
    # List devices mode
    if args.list:
        devices = m2000.list_devices()
        if devices:
            print(f"Found {len(devices)} M2000 USB device(s):")
            for i, dev in enumerate(devices):
                print(f"  [{i}] Manufacturer: {dev.get('manufacturer_string', 'Unknown')}")
                print(f"      Product: {dev.get('product_string', 'Unknown')}")
                print(f"      Serial: {dev.get('serial_number', 'Unknown')}")
                print(f"      Path: {dev['path'].decode('utf-8')}")
                print()
        else:
            print("No M2000 USB devices found")
            print("Make sure:")
            print("1. M2000 is powered on and USB cable connected")
            print("2. USB drivers are installed")
            print("3. hidapi is installed: pip install hidapi")
        return 0
    
    try:
        # Connect
        if not m2000.connect(args.device):
            print("Failed to connect to M2000")
            return 1
        
        # Check for errors
        m2000.check_errors()
        
        if args.stream:
            # Stream data
            m2000.stream_data(
                channels=args.channels,
                parameters=args.params,
                duration=args.duration,
                sample_rate=args.rate,
                log_file=args.log
            )
        else:
            # Single measurement
            print("Getting single measurement...")
            data = m2000.get_measurement(args.channels, args.params)
            if data:
                for key, value in data.items():
                    print(f"{key}: {value}")
            else:
                print("No data received")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        m2000.disconnect()
    
    return 0


if __name__ == "__main__":
    try:
        import hid
    except ImportError:
        print("Error: hidapi library not found")
        print("Install with: pip install hidapi")
        print("On Linux you may also need: sudo apt install libhidapi-hidraw0")
        sys.exit(1)
    
    sys.exit(main())