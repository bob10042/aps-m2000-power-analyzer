#!/usr/bin/env python3
"""
APS M2000 Power Analyzer - RS232 Serial Interface
Fully functional script for remote control via RS232

CRITICAL RS232 REQUIREMENTS (from M2000 Manual):
- Handshake: Bi-directional, hardware (RTS/CTS) - MANDATORY
- DTR signal: MUST be asserted - M2000 discards data without DTR
- CTS signal: Used by M2000 to handshake data from computer - REQUIRED
- RTS signal: Used by M2000 to handshake data to computer - REQUIRED
- Cable: 9-wire female-female null modem cable, fully wired
- All signals (DTR, RTS, CTS, DSR) must be supported by cable and software
"""

import serial
import time
import sys
import argparse


class M2000_RS232:
    def __init__(self, port='COM1', baudrate=115200, timeout=1.0):
        """
        Initialize RS232 connection to M2000 Power Analyzer
        
        Args:
            port: Serial port (e.g., 'COM1' on Windows, '/dev/ttyUSB0' on Linux)
            baudrate: 9600, 19200, 57600, or 115200 (recommended)
            timeout: Read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None
        self.connected = False
        
    def connect(self):
        """Establish RS232 connection"""
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1,          # 100ms timeout (pyserial expects seconds)
                write_timeout=0.1,    # 100ms write timeout
                rtscts=True,          # Bi-directional hardware handshaking (RTS/CTS) - REQUIRED
                dsrdtr=True           # DTR signal MUST be asserted - REQUIRED by M2000
            )
            
            # Configure control signal states (from corrected info)
            try:
                self.connection.cts_state = self.connection.cts
                self.connection.dsr_state = self.connection.dsr
            except AttributeError:
                # Some serial implementations may not support these attributes
                pass
            
            # Clear buffers
            self.connection.reset_input_buffer()
            self.connection.reset_output_buffer()
            
            # Wait for connection to stabilize
            time.sleep(0.1)
            
            # Initialize device (commands don't return responses)
            self.send_command('*RST')  # Reset device - no response
            self.send_command('*CLS')  # Clear device - no response
            
            # Check connection with query (queries do return responses)
            response = self.query('*IDN?')
            
            if response and 'APS' in response:
                self.connected = True
                print(f"Connected to: {response}")
                return True
            else:
                print(f"Unexpected response: {response}")
                return False
                
        except serial.SerialException as e:
            print(f"RS232 connection failed: {e}")
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Close RS232 connection"""
        if self.connection and self.connection.is_open:
            self.send_command('LOCAL')  # Return to local control
            self.connection.close()
            self.connected = False
            print("RS232 connection closed")
    
    def send_command(self, command):
        """Send command to M2000"""
        if not self.connected or not self.connection.is_open:
            raise Exception("Not connected to M2000")
        
        try:
            # Add proper termination (from corrected info)
            if not command.endswith('\r\n'):
                command += '\r\n'
            cmd_bytes = command.encode('ascii')
            self.connection.write(cmd_bytes)
            self.connection.flush()
            
        except Exception as e:
            print(f"Send command error: {e}")
            raise
    
    def read_response(self):
        """Read response from M2000"""
        if not self.connected or not self.connection.is_open:
            raise Exception("Not connected to M2000")
        
        try:
            # Use read_until() method as shown in corrected info
            read_val = self.connection.read_until()
            response = read_val.decode("utf-8")[:-2].replace(";", "\r\n")
            return response.strip()
            
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
            channels: List of channels ['CH1', 'CH2', 'CH3', 'CH4']
            parameters: List of parameters ['V', 'A', 'W', 'VA', 'PF', 'FREQ']
        
        Returns:
            Dictionary with measurement data
        """
        # Build READ command using corrected M2000 syntax
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
                
                # Use M2000 command format: READ?,ch2:VOLTS:ACDC
                read_fields.append(f"READ?,{channel.lower()}:{m2000_param}:ACDC")
        
        # Send multiple READ commands (can also combine with semicolons)
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
                   duration=10, sample_rate=1.0):
        """
        Stream measurement data for specified duration
        
        Args:
            channels: List of channels to monitor
            parameters: List of parameters to read
            duration: Duration in seconds (0 = infinite)
            sample_rate: Samples per second
        """
        print(f"Streaming data from {channels} for {duration}s at {sample_rate}Hz")
        print("Press Ctrl+C to stop\n")
        
        # Set up initial READ command
        read_fields = []
        for param in parameters:
            for channel in channels:
                read_fields.append(f"{param}:{channel}")
        
        command = "READ? " + ",".join(read_fields)
        
        start_time = time.time()
        sample_count = 0
        
        try:
            while True:
                # Check duration
                if duration > 0 and (time.time() - start_time) > duration:
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
                    timestamp = time.time() - start_time
                    
                    # Format output
                    output = f"[{timestamp:8.2f}s] "
                    idx = 0
                    for param in parameters:
                        for channel in channels:
                            if idx < len(values):
                                output += f"{channel}_{param}={values[idx]:>8} "
                                idx += 1
                    
                    print(output)
                    sample_count += 1
                
                # Wait for next sample
                time.sleep(1.0 / sample_rate)
                
        except KeyboardInterrupt:
            print(f"\nStreaming stopped. Collected {sample_count} samples")


def main():
    parser = argparse.ArgumentParser(description='APS M2000 RS232 Interface')
    parser.add_argument('--port', default='/dev/ttyUSB0', 
                       help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('--baud', type=int, default=115200,
                       choices=[9600, 19200, 57600, 115200],
                       help='Baud rate (default: 115200)')
    parser.add_argument('--channels', nargs='+', default=['CH1'],
                       choices=['CH1', 'CH2', 'CH3', 'CH4'],
                       help='Channels to monitor (default: CH1)')
    parser.add_argument('--params', nargs='+', default=['V', 'A', 'W'],
                       choices=['V', 'A', 'W', 'VA', 'VAR', 'PF', 'FREQ'],
                       help='Parameters to read (default: V A W)')
    parser.add_argument('--stream', action='store_true',
                       help='Stream data continuously')
    parser.add_argument('--duration', type=float, default=10,
                       help='Stream duration in seconds (default: 10)')
    parser.add_argument('--rate', type=float, default=1.0,
                       help='Sample rate in Hz (default: 1.0)')
    
    args = parser.parse_args()
    
    # Create M2000 interface
    m2000 = M2000_RS232(port=args.port, baudrate=args.baud)
    
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
                sample_rate=args.rate
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
    sys.exit(main())