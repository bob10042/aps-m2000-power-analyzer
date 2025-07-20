#!/usr/bin/env python3
"""
APS M2000 Power Analyzer - Real-Time Web UI
Web-based interface with live data streaming and visualization
"""

import asyncio
import websockets
import json
import threading
import time
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys
from urllib.parse import parse_qs, urlparse

# Import M2000 interfaces
try:
    from m2000_lan import M2000_LAN
    from m2000_rs232 import M2000_RS232  
    from m2000_usb import M2000_USB
    from m2000_units import format_measurement, get_base_unit
except ImportError as e:
    print(f"Error importing M2000 modules: {e}")
    sys.exit(1)


class M2000WebServer:
    def __init__(self, web_port=8080, websocket_port=8081):
        self.web_port = web_port
        self.websocket_port = websocket_port
        self.m2000 = None
        self.running = False
        self.connected_clients = set()
        self.current_data = {}
        self.sample_rate = 2.0
        self.channels = ['CH1']
        self.parameters = ['V', 'A', 'W']
        
    async def websocket_handler(self, websocket):
        """Handle WebSocket connections for real-time data"""
        self.connected_clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.connected_clients)}")
        
        try:
            # Send current configuration
            config_msg = {
                'type': 'config',
                'channels': self.channels,
                'parameters': self.parameters,
                'sample_rate': self.sample_rate,
                'connected': self.m2000 is not None and getattr(self.m2000, 'connected', False)
            }
            await websocket.send(json.dumps(config_msg))
            
            # Send current data if available
            if self.current_data:
                data_msg = {
                    'type': 'data',
                    'timestamp': time.time(),
                    'measurements': self.current_data
                }
                await websocket.send(json.dumps(data_msg))
            
            # Handle incoming messages
            async for message in websocket:
                try:
                    msg = json.loads(message)
                    await self.handle_websocket_message(msg, websocket)
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_clients.discard(websocket)
            print(f"Client disconnected. Total clients: {len(self.connected_clients)}")
    
    async def handle_websocket_message(self, msg, websocket):
        """Handle incoming WebSocket messages"""
        msg_type = msg.get('type')
        
        if msg_type == 'connect':
            # Connect to M2000
            interface = msg.get('interface', 'lan')
            config = msg.get('config', {})
            success = await self.connect_m2000(interface, config)
            
            response = {
                'type': 'connect_response',
                'success': success,
                'message': 'Connected successfully' if success else 'Connection failed'
            }
            await websocket.send(json.dumps(response))
            
        elif msg_type == 'disconnect':
            # Disconnect from M2000
            self.disconnect_m2000()
            response = {
                'type': 'disconnect_response',
                'success': True
            }
            await websocket.send(json.dumps(response))
            
        elif msg_type == 'configure':
            # Update measurement configuration
            self.channels = msg.get('channels', self.channels)
            self.parameters = msg.get('parameters', self.parameters)
            self.sample_rate = msg.get('sample_rate', self.sample_rate)
            
            response = {
                'type': 'configure_response',
                'success': True,
                'config': {
                    'channels': self.channels,
                    'parameters': self.parameters,
                    'sample_rate': self.sample_rate
                }
            }
            await websocket.send(json.dumps(response))
    
    async def connect_m2000(self, interface, config):
        """Connect to M2000 device"""
        try:
            if interface == 'lan':
                host = config.get('host', '192.168.1.100')
                port = config.get('port', 10733)
                self.m2000 = M2000_LAN(host=host, port=port)
                
            elif interface == 'rs232':
                port = config.get('port', '/dev/ttyUSB0')
                baudrate = config.get('baudrate', 9600)
                self.m2000 = M2000_RS232(port=port, baudrate=baudrate)
                
            elif interface == 'usb':
                device_index = config.get('device_index', 0)
                self.m2000 = M2000_USB()
                
            else:
                return False
            
            # Connect in a separate thread to avoid blocking
            success = await asyncio.get_event_loop().run_in_executor(
                None, self.m2000.connect, *([device_index] if interface == 'usb' else [])
            )
            
            if success:
                # Start data streaming
                self.start_data_streaming()
                return True
            else:
                self.m2000 = None
                return False
                
        except Exception as e:
            print(f"Connection error: {e}")
            self.m2000 = None
            return False
    
    def disconnect_m2000(self):
        """Disconnect from M2000 device"""
        if self.m2000:
            try:
                self.m2000.disconnect()
            except:
                pass
            finally:
                self.m2000 = None
    
    def start_data_streaming(self):
        """Start streaming data from M2000"""
        if not self.m2000 or not getattr(self.m2000, 'connected', False):
            return
        
        def stream_worker():
            """Worker thread for data streaming"""
            sample_count = 0
            
            while self.m2000 and getattr(self.m2000, 'connected', False):
                try:
                    # Get measurement data
                    if sample_count == 0:
                        # First reading
                        data = self.m2000.get_measurement(self.channels, self.parameters)
                    else:
                        # Use REREAD? for speed if available
                        try:
                            response = self.m2000.query('REREAD?')
                            if response:
                                values = response.split(',')
                                data = {}
                                idx = 0
                                for param in self.parameters:
                                    for channel in self.channels:
                                        if idx < len(values):
                                            try:
                                                data[f"{channel}_{param}"] = float(values[idx])
                                            except ValueError:
                                                data[f"{channel}_{param}"] = values[idx]
                                            idx += 1
                            else:
                                data = self.m2000.get_measurement(self.channels, self.parameters)
                        except:
                            data = self.m2000.get_measurement(self.channels, self.parameters)
                    
                    if data:
                        self.current_data = data
                        sample_count += 1
                        
                        # Format data for web display
                        formatted_data = {}
                        for key, value in data.items():
                            if '_' in key:
                                channel, param = key.split('_', 1)
                                if channel not in formatted_data:
                                    formatted_data[channel] = {}
                                
                                # Add both raw and formatted values
                                formatted_data[channel][param] = {
                                    'raw': value,
                                    'formatted': format_measurement(value, param, include_units=True),
                                    'unit': get_base_unit(param)
                                }
                        
                        # Send to all connected clients
                        if self.connected_clients:
                            message = {
                                'type': 'data',
                                'timestamp': time.time(),
                                'measurements': formatted_data,
                                'sample_count': sample_count
                            }
                            
                            # Send to all connected clients
                            asyncio.run_coroutine_threadsafe(
                                self.broadcast_to_clients(json.dumps(message)),
                                asyncio.get_event_loop()
                            )
                    
                    # Wait for next sample
                    time.sleep(1.0 / self.sample_rate)
                    
                except Exception as e:
                    print(f"Streaming error: {e}")
                    time.sleep(1.0)  # Wait before retrying
        
        # Start streaming in background thread
        thread = threading.Thread(target=stream_worker, daemon=True)
        thread.start()
    
    async def broadcast_to_clients(self, message):
        """Broadcast message to all connected WebSocket clients"""
        if self.connected_clients:
            disconnected = set()
            for client in self.connected_clients.copy():
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
                except Exception as e:
                    print(f"Error sending to client: {e}")
                    disconnected.add(client)
            
            # Remove disconnected clients
            self.connected_clients -= disconnected
    
    def start_web_server(self):
        """Start HTTP server for web interface"""
        class M2000Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory='/home/bob43/APSM2000', **kwargs)
            
            def do_GET(self):
                if self.path == '/' or self.path == '/index.html':
                    self.path = '/m2000_dashboard.html'
                super().do_GET()
        
        server = HTTPServer(('localhost', self.web_port), M2000Handler)
        print(f"Web server starting on http://localhost:{self.web_port}")
        
        # Start server in background thread
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        return server
    
    async def start_websocket_server(self):
        """Start WebSocket server"""
        print(f"WebSocket server starting on ws://localhost:{self.websocket_port}")
        
        start_server = websockets.serve(
            self.websocket_handler,
            'localhost',
            self.websocket_port
        )
        
        await start_server
    
    async def run(self):
        """Run the complete web interface"""
        # Start HTTP server
        web_server = self.start_web_server()
        
        # Start WebSocket server
        await self.start_websocket_server()
        
        print(f"\n🌐 M2000 Web Interface Ready!")
        print(f"📊 Dashboard: http://localhost:{self.web_port}")
        print(f"🔌 WebSocket: ws://localhost:{self.websocket_port}")
        print("Press Ctrl+C to stop\n")
        
        try:
            # Keep running
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            print("\nShutting down web interface...")
            self.disconnect_m2000()


def main():
    parser = argparse.ArgumentParser(description='APS M2000 Web Interface')
    parser.add_argument('--web-port', type=int, default=8080,
                       help='HTTP server port (default: 8080)')
    parser.add_argument('--websocket-port', type=int, default=8081,
                       help='WebSocket server port (default: 8081)')
    parser.add_argument('--channels', nargs='+', default=['CH1'],
                       choices=['CH1', 'CH2', 'CH3', 'CH4', 'VPA1', 'VPA2', 'VPA3'],
                       help='Default channels to monitor')
    parser.add_argument('--params', nargs='+', default=['V', 'A', 'W'],
                       choices=['V', 'A', 'W', 'VA', 'VAR', 'PF', 'FREQ', 'PHASE'],
                       help='Default parameters to read')
    parser.add_argument('--rate', type=float, default=2.0,
                       help='Default sample rate in Hz')
    
    args = parser.parse_args()
    
    # Create web server
    server = M2000WebServer(args.web_port, args.websocket_port)
    server.channels = args.channels
    server.parameters = args.params
    server.sample_rate = args.rate
    
    try:
        # Check if websockets is available
        import websockets
    except ImportError:
        print("Error: websockets library not found")
        print("Install with: pip install websockets")
        return 1
    
    try:
        # Run the web interface
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("Web interface stopped")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())