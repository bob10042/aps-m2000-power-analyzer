#!/usr/bin/env python3
"""
APS M2000 Power Analyzer - Simple Web Interface
Basic web interface that works without external dependencies
"""

import socket
import threading
import json
import time
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os


class SimpleM2000Web:
    def __init__(self, web_port=8080):
        self.web_port = web_port
        self.m2000 = None
        self.running = False
        self.current_data = {}
        
    def start_web_server(self):
        """Start HTTP server for web interface"""
        
        class M2000Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory='/home/bob43/APSM2000', **kwargs)
            
            def do_GET(self):
                # Route requests
                if self.path == '/' or self.path == '/index.html':
                    self.serve_dashboard()
                elif self.path == '/api/data':
                    self.serve_api_data()
                elif self.path == '/api/status':
                    self.serve_api_status()
                else:
                    super().do_GET()
            
            def serve_dashboard(self):
                """Serve the main dashboard page"""
                html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APS M2000 Power Analyzer - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 2rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 {
            color: #2c3e50;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .status {
            font-size: 1.2rem;
            color: #7f8c8d;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 8px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .card:hover { transform: translateY(-5px); }
        .card h2 {
            color: #2c3e50;
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
            text-align: center;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 0.5rem;
        }
        .measurement {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            margin: 0.5rem 0;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            font-size: 1.1rem;
        }
        .measurement-label {
            font-weight: 600;
            color: #495057;
        }
        .measurement-value {
            font-weight: 700;
            color: #2c3e50;
            font-size: 1.2rem;
        }
        .controls {
            background: rgba(255, 255, 255, 0.9);
            margin: 2rem;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
        }
        .control-group {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin: 1rem 0;
            flex-wrap: wrap;
        }
        .control-item {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            align-items: center;
        }
        .control-item label {
            font-weight: 600;
            color: #2c3e50;
        }
        .control-item input, .control-item select, .control-item button {
            padding: 0.7rem 1rem;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
        }
        .control-item button {
            background: #3498db;
            color: white;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            min-width: 120px;
        }
        .control-item button:hover {
            background: #2980b9;
            transform: translateY(-2px);
        }
        .info-box {
            background: rgba(255, 255, 255, 0.9);
            margin: 2rem;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
        }
        .auto-refresh {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔋 APS M2000 Power Analyzer</h1>
        <div class="status">Real-Time Monitoring Dashboard</div>
    </div>
    
    <div class="controls">
        <h3>Quick Test Interface</h3>
        <div class="control-group">
            <div class="control-item">
                <label>Interface:</label>
                <select id="interface">
                    <option value="lan">LAN (192.168.1.100)</option>
                    <option value="rs232">RS232 (/dev/ttyUSB0)</option>
                    <option value="usb">USB HID</option>
                </select>
            </div>
            <div class="control-item">
                <label>Test Connection:</label>
                <button onclick="testConnection()">Connect & Test</button>
            </div>
            <div class="control-item">
                <label>Auto Refresh:</label>
                <button onclick="toggleAutoRefresh()" id="refreshBtn">Start Auto Refresh</button>
            </div>
        </div>
    </div>
    
    <div class="dashboard" id="dashboard">
        <div class="card">
            <h2>📊 Channel 1 (CH1)</h2>
            <div class="measurement">
                <span class="measurement-label">Voltage:</span>
                <span class="measurement-value" id="ch1-voltage">-- V</span>
            </div>
            <div class="measurement">
                <span class="measurement-label">Current:</span>
                <span class="measurement-value" id="ch1-current">-- A</span>
            </div>
            <div class="measurement">
                <span class="measurement-label">Power:</span>
                <span class="measurement-value" id="ch1-power">-- W</span>
            </div>
            <div class="measurement">
                <span class="measurement-label">Power Factor:</span>
                <span class="measurement-value" id="ch1-pf">--</span>
            </div>
        </div>
        
        <div class="card">
            <h2>⚡ Channel 2 (CH2)</h2>
            <div class="measurement">
                <span class="measurement-label">Voltage:</span>
                <span class="measurement-value" id="ch2-voltage">-- V</span>
            </div>
            <div class="measurement">
                <span class="measurement-label">Current:</span>
                <span class="measurement-value" id="ch2-current">-- A</span>
            </div>
            <div class="measurement">
                <span class="measurement-label">Power:</span>
                <span class="measurement-value" id="ch2-power">-- W</span>
            </div>
            <div class="measurement">
                <span class="measurement-label">Frequency:</span>
                <span class="measurement-value" id="ch2-freq">-- Hz</span>
            </div>
        </div>
        
        <div class="card">
            <h2>🔌 3-Phase Power (VPA1)</h2>
            <div class="measurement">
                <span class="measurement-label">Total Power:</span>
                <span class="measurement-value" id="vpa1-power">-- W</span>
            </div>
            <div class="measurement">
                <span class="measurement-label">Apparent Power:</span>
                <span class="measurement-value" id="vpa1-va">-- VA</span>
            </div>
            <div class="measurement">
                <span class="measurement-label">Reactive Power:</span>
                <span class="measurement-value" id="vpa1-var">-- VAR</span>
            </div>
            <div class="measurement">
                <span class="measurement-label">Power Factor:</span>
                <span class="measurement-value" id="vpa1-pf">--</span>
            </div>
        </div>
    </div>
    
    <div class="info-box">
        <h3>📋 M2000 Interface Status</h3>
        <p><strong>Available Scripts:</strong></p>
        <p>• LAN Interface: <code>python3 m2000_lan.py --host 192.168.1.100</code></p>
        <p>• RS232 Interface: <code>python3 m2000_rs232.py --port /dev/ttyUSB0</code></p>
        <p>• USB Interface: <code>python3 m2000_usb.py --list</code></p>
        <br>
        <p><strong>For Real-Time WebSocket Interface:</strong></p>
        <p>Install websockets: <code>pip install websockets</code></p>
        <p>Then run: <code>python3 m2000_web_ui.py</code></p>
        <br>
        <p id="status-message">Click "Connect & Test" to test M2000 communication</p>
    </div>

    <script>
        let autoRefreshInterval = null;
        let isAutoRefresh = false;
        
        function testConnection() {
            const interface = document.getElementById('interface').value;
            const statusMsg = document.getElementById('status-message');
            
            statusMsg.innerHTML = '🔄 Testing connection to M2000...';
            statusMsg.className = 'auto-refresh';
            
            // Simulate test results (replace with actual API call when implemented)
            setTimeout(() => {
                statusMsg.className = '';
                if (interface === 'lan') {
                    updateMockData();
                    statusMsg.innerHTML = '✅ LAN connection test complete. Mock data displayed.';
                } else if (interface === 'rs232') {
                    statusMsg.innerHTML = '⚠️ RS232 test: Check cable and port permissions.';
                } else {
                    statusMsg.innerHTML = '⚠️ USB test: Ensure hidapi is installed and device connected.';
                }
            }, 2000);
        }
        
        function updateMockData() {
            // Mock measurement data for demonstration
            document.getElementById('ch1-voltage').textContent = (230 + Math.random() * 2).toFixed(2) + ' V';
            document.getElementById('ch1-current').textContent = (1.2 + Math.random() * 0.1).toFixed(3) + ' A';
            document.getElementById('ch1-power').textContent = (276 + Math.random() * 10).toFixed(1) + ' W';
            document.getElementById('ch1-pf').textContent = (0.85 + Math.random() * 0.1).toFixed(3);
            
            document.getElementById('ch2-voltage').textContent = (229 + Math.random() * 3).toFixed(2) + ' V';
            document.getElementById('ch2-current').textContent = (1.1 + Math.random() * 0.2).toFixed(3) + ' A';
            document.getElementById('ch2-power').textContent = (252 + Math.random() * 15).toFixed(1) + ' W';
            document.getElementById('ch2-freq').textContent = (50.0 + Math.random() * 0.1).toFixed(2) + ' Hz';
            
            document.getElementById('vpa1-power').textContent = (1.25 + Math.random() * 0.1).toFixed(2) + ' kW';
            document.getElementById('vpa1-va').textContent = (1.47 + Math.random() * 0.1).toFixed(2) + ' kVA';
            document.getElementById('vpa1-var').textContent = (0.85 + Math.random() * 0.1).toFixed(2) + ' kVAR';
            document.getElementById('vpa1-pf').textContent = (0.851 + Math.random() * 0.05).toFixed(3);
        }
        
        function toggleAutoRefresh() {
            const btn = document.getElementById('refreshBtn');
            
            if (!isAutoRefresh) {
                // Start auto refresh
                autoRefreshInterval = setInterval(updateMockData, 2000);
                btn.textContent = 'Stop Auto Refresh';
                btn.style.background = '#e74c3c';
                isAutoRefresh = true;
                updateMockData(); // Initial update
            } else {
                // Stop auto refresh
                clearInterval(autoRefreshInterval);
                btn.textContent = 'Start Auto Refresh';
                btn.style.background = '#3498db';
                isAutoRefresh = false;
            }
        }
        
        // Initial page load
        document.addEventListener('DOMContentLoaded', function() {
            console.log('M2000 Dashboard loaded');
        });
    </script>
</body>
</html>
                """
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html_content.encode('utf-8'))
            
            def serve_api_data(self):
                """Serve API data endpoint"""
                # Mock data for now - replace with actual M2000 data
                data = {
                    "timestamp": time.time(),
                    "channels": {
                        "CH1": {
                            "V": 230.45,
                            "A": 1.234,
                            "W": 284.5,
                            "PF": 0.851
                        },
                        "CH2": {
                            "V": 229.12,
                            "A": 1.156,
                            "W": 264.8,
                            "FREQ": 50.02
                        }
                    }
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))
            
            def serve_api_status(self):
                """Serve API status endpoint"""
                status = {
                    "connected": False,
                    "interface": "none",
                    "message": "No M2000 connection established"
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(status).encode('utf-8'))
        
        server = HTTPServer(('localhost', self.web_port), M2000Handler)
        print(f"🌐 Simple M2000 Web Interface")
        print(f"📊 Dashboard: http://localhost:{self.web_port}")
        print(f"🔧 Test interface without external dependencies")
        print("Press Ctrl+C to stop\n")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nWeb interface stopped")
            server.shutdown()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Simple M2000 Web Interface')
    parser.add_argument('--port', type=int, default=8080,
                       help='Web server port (default: 8080)')
    
    args = parser.parse_args()
    
    # Create and start simple web interface
    web_interface = SimpleM2000Web(args.port)
    web_interface.start_web_server()


if __name__ == "__main__":
    main()