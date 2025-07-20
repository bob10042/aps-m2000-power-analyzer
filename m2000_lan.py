#!/usr/bin/env python3
"""
APS M2000 Power Analyzer - LAN/Ethernet Interface
Fully functional script for remote control via TCP/IP
"""

import socket
import time
import sys
import argparse
import threading
import os

# Import unit formatting module
try:
    from m2000_units import format_measurement, format_measurement_table, create_csv_header, format_csv_row
except ImportError:
    # Fallback if m2000_units.py not available
    def format_measurement(value, param, include_units=True):
        return f"{value}"
    def format_measurement_table(data, title=""):
        return str(data)
    def create_csv_header(channels, params):
        header = "Timestamp"
        for param in params:
            for channel in channels:
                header += f",{channel}_{param}"
        return header
    def format_csv_row(timestamp, data, channels, params):
        row = f"{timestamp:.3f}"
        for param in params:
            for channel in channels:
                key = f"{channel}_{param}"
                row += f",{data.get(key, '')}"
        return row


class M2000_LAN:
    def __init__(self, host='192.168.1.100', port=10733, timeout=5.0):
        """
        Initialize LAN connection to M2000 Power Analyzer
        
        Args:
            host: IP address or hostname of M2000 (or identity.local)
            port: TCP port (always 10733 for M2000)
            timeout: Socket timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.connected = False
        
    def connect(self):
        """Establish TCP connection"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            
            print(f"Connecting to M2000 at {self.host}:{self.port}...")
            self.socket.connect((self.host, self.port))
            
            # Wait for connection to stabilize
            time.sleep(0.1)
            
            # Initialize device using correct M2000 protocol
            self.send_command('*RST')  # Reset device - no response
            self.send_command('*CLS')  # Clear device - no response
            
            # Check connection with query (queries return responses)
            response = self.query('*IDN?')
            
            if response and 'APS' in response:
                self.connected = True
                print(f"Connected to: {response}")
                return True
            else:
                print(f"Unexpected response: {response}")
                return False
                
        except socket.gaierror as e:
            print(f"DNS resolution failed: {e}")
            return False
        except socket.timeout:
            print("Connection timeout - check IP address and network")
            return False
        except ConnectionRefusedError:
            print("Connection refused - check if M2000 is powered on and LAN enabled")
            return False
        except Exception as e:
            print(f"LAN connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close TCP connection"""
        if self.socket:
            try:
                if self.connected:
                    self.send_command('LOCAL')  # Return to local control
                self.socket.close()
            except:
                pass
            finally:
                self.connected = False
                self.socket = None
                print("LAN connection closed")
    
    def send_command(self, command):
        """Send command to M2000"""
        if not self.connected or not self.socket:
            raise Exception("Not connected to M2000")
        
        try:
            # Add line feed terminator and encode to ASCII
            cmd_bytes = (command + '\n').encode('ascii')
            self.socket.sendall(cmd_bytes)
            
        except socket.timeout:
            raise Exception("Send timeout")
        except Exception as e:
            print(f"Send command error: {e}")
            raise
    
    def read_response(self):
        """Read response from M2000"""
        if not self.connected or not self.socket:
            raise Exception("Not connected to M2000")
        
        try:
            # Read until line feed
            response = ""
            while True:
                data = self.socket.recv(1).decode('ascii')
                if not data:
                    break
                if data == '\n':
                    break
                if data != '\r':  # Skip carriage return
                    response += data
            
            return response
            
        except socket.timeout:
            raise Exception("Read timeout")
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
    
    def get_3phase_power(self, vpa='VPA1'):
        """Get comprehensive 3-phase power measurements"""
        parameters = ['W', 'VA', 'VAR', 'PF', 'FREQ']
        channels = [vpa]
        
        # Also get individual phase measurements
        phase_channels = ['CH1', 'CH2', 'CH3']
        
        # Get VPA measurements
        vpa_data = self.get_measurement(channels, parameters)
        
        # Get individual phase V and A
        phase_data = self.get_measurement(phase_channels, ['V', 'A'])
        
        if vpa_data and phase_data:
            return {**vpa_data, **phase_data}
        return None
    
    def stream_data(self, channels=['CH1'], parameters=['V', 'A', 'W'], 
                   duration=10, sample_rate=5.0, log_file=None):
        """
        Stream measurement data for specified duration
        
        Args:
            channels: List of channels to monitor
            parameters: List of parameters to read
            duration: Duration in seconds (0 = infinite)
            sample_rate: Samples per second (max ~500Hz for LAN)
            log_file: Optional CSV file to log data
        """
        print(f"Streaming data from {channels} for {duration}s at {sample_rate}Hz")
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
        
        # Prepare CSV header with units
        if log_file:
            header = create_csv_header(channels, parameters) + "\n"
            
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
                    
                    # Format console output with proper units
                    output = f"[{timestamp:8.2f}s] "
                    idx = 0
                    for param in parameters:
                        for channel in channels:
                            if idx < len(values):
                                try:
                                    val = float(values[idx])
                                    formatted = format_measurement(val, param, include_units=True)
                                    output += f"{channel}_{param}={formatted:>12} "
                                except ValueError:
                                    output += f"{channel}_{param}={values[idx]:>12} "
                                idx += 1
                    
                    print(output)
                    sample_count += 1
                    
                    # Log to file with properly formatted CSV
                    if log_file:
                        # Create data dictionary for CSV formatting
                        csv_data = {}
                        idx = 0
                        for param in parameters:
                            for channel in channels:
                                if idx < len(values):
                                    csv_data[f"{channel}_{param}"] = values[idx]
                                    idx += 1
                        
                        log_line = format_csv_row(timestamp, csv_data, channels, parameters) + "\n"
                        
                        with open(log_file, 'a') as f:
                            f.write(log_line)
                
                # Wait for next sample (accounting for processing time)
                elapsed = time.time() - sample_start
                sleep_time = max(0, (1.0 / sample_rate) - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print(f"\nStreaming stopped. Collected {sample_count} samples")
    
    def discover_m2000(self, network_base="192.168.1", timeout=2.0):
        """
        Discover M2000 devices on network
        
        Args:
            network_base: Network base (e.g., "192.168.1")
            timeout: Timeout per IP check
        """
        print(f"Scanning network {network_base}.1-254 for M2000 devices...")
        found_devices = []
        
        def check_ip(ip):
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(timeout)
                result = test_socket.connect_ex((ip, 10733))
                if result == 0:
                    # Try to get identification
                    test_socket.send(b'*IDN?\n')
                    response = test_socket.recv(1024).decode('ascii').strip()
                    if 'APS' in response:
                        found_devices.append((ip, response))
                        print(f"Found M2000 at {ip}: {response}")
                test_socket.close()
            except:
                pass
        
        # Use threading for faster scanning
        threads = []
        for i in range(1, 255):
            ip = f"{network_base}.{i}"
            thread = threading.Thread(target=check_ip, args=(ip,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        return found_devices


def main():
    parser = argparse.ArgumentParser(description='APS M2000 LAN Interface')
    parser.add_argument('--host', default='192.168.1.100',
                       help='M2000 IP address or hostname (default: 192.168.1.100)')
    parser.add_argument('--port', type=int, default=10733,
                       help='TCP port (default: 10733)')
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
    parser.add_argument('--rate', type=float, default=5.0,
                       help='Sample rate in Hz (default: 5.0, max ~500)')
    parser.add_argument('--log', type=str,
                       help='CSV file to log streaming data')
    parser.add_argument('--3phase', action='store_true',
                       help='Get comprehensive 3-phase measurements')
    parser.add_argument('--discover', action='store_true',
                       help='Scan network for M2000 devices')
    parser.add_argument('--network', default='192.168.1',
                       help='Network base for discovery (default: 192.168.1)')
    
    args = parser.parse_args()
    
    # Discovery mode
    if args.discover:
        m2000 = M2000_LAN()
        found = m2000.discover_m2000(args.network)
        if found:
            print(f"\nFound {len(found)} M2000 device(s)")
            for ip, info in found:
                print(f"  {ip}: {info}")
        else:
            print("No M2000 devices found")
        return 0
    
    # Create M2000 interface
    m2000 = M2000_LAN(host=args.host, port=args.port)
    
    try:
        # Connect
        if not m2000.connect():
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
        elif args.threephase:
            # 3-phase measurement
            print("Getting 3-phase power measurements...")
            data = m2000.get_3phase_power('VPA1')
            if data:
                print(format_measurement_table(data, "3-Phase Power Analysis"))
            else:
                print("No data received")
        else:
            # Single measurement
            print("Getting single measurement...")
            data = m2000.get_measurement(args.channels, args.params)
            if data:
                print(format_measurement_table(data, "Measurement Results"))
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
    sys.exit(main())