# M2000 Web UI - Real-Time Dashboard

A professional web-based interface for monitoring APS M2000 Power Analyzer data in real-time with live charts, gauges, and measurement displays.

## 🚀 **Quick Start**

### **1. Install Dependencies**
```bash
# Install websockets (required for web UI)
sudo apt update && sudo apt install -y python3-websockets python3-asyncio python3-full python3-pip

# Alternative: pip install (if system packages don't work)
pip install --break-system-packages websockets

# Or use virtual environment (recommended)
python3 -m venv /home/bob43/APSM2000/venv
source /home/bob43/APSM2000/venv/bin/activate
pip install websockets
```

### **2. Launch Web Interface**
```bash
# Start the web server and dashboard
python3 m2000_web_ui.py

# Custom ports
python3 m2000_web_ui.py --web-port 8080 --websocket-port 8081

# Simple version (no websockets required)
python3 m2000_simple_web.py
```

### **3. Open Dashboard**
- **Full Dashboard**: `http://localhost:8080` (requires websockets)
- **Simple Dashboard**: `http://localhost:8080` (basic version)
- **WebSocket**: `ws://localhost:8081` (automatic for full version)

## 📊 **Features**

### **Real-Time Visualization**
- **Live Measurements**: Voltage, current, power with automatic unit scaling
- **Interactive Charts**: Real-time line charts with 100-point history
- **Multiple Channels**: Support for CH1-CH4 and VPA1-VPA3
- **Auto-Refresh**: Configurable sample rates from 0.1 to 100 Hz

### **Interface Support**
- **LAN/Ethernet**: TCP connection (recommended for high-speed)
- **RS232**: Serial communication with hardware handshaking
- **USB**: HID interface support

### **Professional UI**
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-Time Status**: Connection indicators and sample rate monitoring
- **Configuration Panel**: Dynamic interface and parameter selection
- **Data Export**: Built-in CSV logging capabilities

## 🖥️ **Dashboard Layout**

### **Header Bar**
- M2000 connection status indicator
- Real-time connection monitoring

### **Control Panel**
- **Interface Selection**: LAN/RS232/USB with dynamic configuration
- **Channel Selection**: Multiple channel monitoring
- **Parameter Selection**: V, A, W, VA, VAR, PF, FREQ
- **Sample Rate**: Adjustable from 0.1 to 100 Hz

### **Statistics Bar**
- Sample count and actual sample rate
- Last update timestamp and total data points

### **Measurement Cards**
- **Live Values**: Auto-scaled units (V, mV, μV, A, mA, μA, etc.)
- **Real-Time Charts**: Interactive line charts with parameter history
- **Channel Organization**: Separate cards for each monitored channel

## 🔧 **Configuration Examples**

### **LAN Interface**
```bash
# Default LAN connection
python3 m2000_web_ui.py --channels CH1 CH2 --params V A W --rate 5.0
```
- Dashboard: Configure Host IP (192.168.1.100)
- Sample Rate: Up to 500 Hz practical

### **RS232 Interface**
```bash
# Serial connection
python3 m2000_web_ui.py --channels CH1 --params V A W PF --rate 2.0
```
- Dashboard: Configure Serial Port (/dev/ttyUSB0)
- Sample Rate: Up to 50 Hz practical

### **USB Interface**
```bash
# USB HID connection
python3 m2000_web_ui.py --channels VPA1 --params W VA VAR --rate 1.0
```
- Dashboard: No additional configuration needed
- Sample Rate: Up to 10 Hz practical

## 📊 **Live Dashboard Screenshots**

### **Connection Interface**
```
🔋 APS M2000 Power Analyzer Dashboard                    ● Connected

┌─ Connection Controls ─────────────────────────────────────────────────┐
│ Interface: [LAN ▼]  Host: 192.168.1.100  Rate: 2.0 Hz  [Connect]    │
│ Channels: [CH1][CH2]  Parameters: [V][A][W]  [Update Config]         │
└───────────────────────────────────────────────────────────────────────┘
```

### **Real-Time Measurements**
```
┌─ CH1 ────────────────────────────┐  ┌─ CH2 ────────────────────────────┐
│ Voltage    │    230.45 V         │  │ Voltage    │    231.20 V         │
│ Current    │     1.234 A         │  │ Current    │     1.189 A         │
│ Power      │   284.5 W           │  │ Power      │   275.2 W           │
│ ┌─────────────────────────────┐ │  │ ┌─────────────────────────────┐ │
│ │     Live Chart (V,A,W)      │ │  │ │     Live Chart (V,A,W)      │ │
│ │ ╭─╮ ╭─╮        ╭──╮        │ │  │ │ ╭─╮ ╭─╮        ╭──╮        │ │
│ │ ╰─╯ ╰─╯ ╭─╮ ╭─╯  ╰─╮      │ │  │ │ ╰─╯ ╰─╯ ╭─╮ ╭─╯  ╰─╮      │ │
│ │         ╰─╯ ╰─╯     ╰──    │ │  │ │         ╰─╯ ╰─╯     ╰──    │ │
│ └─────────────────────────────┘ │  │ └─────────────────────────────┘ │
└───────────────────────────────────┘  └───────────────────────────────────┘
```

## 🌐 **Web API Commands**

### **WebSocket Messages**
```javascript
// Connect to M2000
{
  "type": "connect",
  "interface": "lan",
  "config": {"host": "192.168.1.100", "port": 10733}
}

// Configure measurements
{
  "type": "configure", 
  "channels": ["CH1", "CH2"],
  "parameters": ["V", "A", "W"],
  "sample_rate": 5.0
}

// Receive real-time data
{
  "type": "data",
  "timestamp": 1642678901.234,
  "measurements": {
    "CH1": {
      "V": {"raw": 230.45, "formatted": "230.45 V", "unit": "V"},
      "A": {"raw": 1.234, "formatted": "1.234 A", "unit": "A"}
    }
  }
}
```

## 🔍 **Troubleshooting**

### **WebSocket Connection Issues**
```bash
# Check if ports are available
netstat -an | grep 8080
netstat -an | grep 8081

# Firewall settings
sudo ufw allow 8080
sudo ufw allow 8081

# If websockets not available, use simple interface
python3 m2000_simple_web.py
```

### **M2000 Connection Problems**
- **LAN**: Check IP address and network connectivity
- **RS232**: Verify serial port permissions and cable wiring
- **USB**: Ensure hidapi is installed and device permissions

### **Performance Optimization**
- **High Sample Rates**: Use LAN interface for >10 Hz
- **Multiple Channels**: Reduce sample rate for stability
- **Browser Performance**: Chrome/Firefox recommended for Chart.js

## 📱 **Mobile Support**

The dashboard is fully responsive and works on:
- **Desktop**: Full feature set with large charts
- **Tablet**: Optimized layout with touch controls
- **Mobile**: Compact view with essential measurements

## 🔧 **Advanced Configuration**

### **Custom Sample Rates by Interface**
```bash
# LAN: High-speed monitoring
python3 m2000_web_ui.py --rate 10.0   # Up to 500 Hz

# RS232: Medium-speed monitoring  
python3 m2000_web_ui.py --rate 5.0    # Up to 50 Hz

# USB: Low-speed monitoring
python3 m2000_web_ui.py --rate 1.0    # Up to 10 Hz
```

### **Multi-Channel Power Analysis**
```bash
# 3-phase power monitoring
python3 m2000_web_ui.py --channels VPA1 VPA2 VPA3 --params W VA VAR PF
```

### **Data Logging Integration**
The web UI automatically logs data when CSV logging is enabled in the underlying M2000 scripts.

## 🚀 **Production Deployment**

### **Running as Service**
```bash
# Create systemd service
sudo nano /etc/systemd/system/m2000-web.service

# Service configuration
[Unit]
Description=M2000 Web Interface
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/bob43/APSM2000
ExecStart=/usr/bin/python3 m2000_web_ui.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable m2000-web
sudo systemctl start m2000-web
```

### **Reverse Proxy Setup**
```nginx
# Nginx configuration for production
server {
    listen 80;
    server_name m2000.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8080;
    }
    
    location /ws {
        proxy_pass http://localhost:8081;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🎯 **Next Steps**

### **Option A: Full Web UI (Recommended)**
1. **Install websockets**: `sudo apt install python3-websockets`
2. **Launch interface**: `python3 m2000_web_ui.py`
3. **Open browser**: `http://localhost:8080`
4. **Connect to M2000**: Select interface and configure connection
5. **Monitor data**: View real-time measurements and charts

### **Option B: Simple Web UI (No Dependencies)**
1. **Launch interface**: `python3 m2000_simple_web.py`
2. **Open browser**: `http://localhost:8080`
3. **Test connection**: Use built-in test interface
4. **View mock data**: See dashboard layout and functionality

### **Available Web Interfaces**
- **`m2000_web_ui.py`**: Full WebSocket-based real-time interface
- **`m2000_simple_web.py`**: Basic HTTP-only interface for testing
- **`m2000_dashboard.html`**: Standalone HTML dashboard

The web UI provides a professional, real-time monitoring solution for M2000 Power Analyzer data with enterprise-grade visualization capabilities.