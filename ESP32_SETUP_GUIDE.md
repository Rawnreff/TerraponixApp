# 🌱 ESP32 TERRAPONIX - Setup Guide

## 📋 Overview

Panduan ini menjelaskan cara mengintegrasikan ESP32 Terraponix dengan API sensor yang telah dibuat. ESP32 akan berfungsi sebagai client yang mengirim data sensor ke API server melalui hotspot seluler.

## 🔧 Hardware Requirements

### ESP32 Development Board
- ESP32-WROOM-32 atau ESP32-DevKit
- Pin GPIO yang tersedia untuk sensor

### Sensor Components
| Sensor | Model | Pin ESP32 | Purpose |
|--------|-------|-----------|---------|
| DHT11 | Temperature & Humidity | GPIO 25 | Monitoring suhu & kelembapan |
| pH Sensor | Analog pH meter | GPIO 34 (ADC) | Kualitas air |
| LDR | Light sensor | GPIO 35 (ADC) | Intensitas cahaya |
| Water Level | Analog sensor | GPIO 32 (ADC) | Level air |
| Servo Motor | SG90 | GPIO 13 | Kontrol tirai |

### Power Supply
- 5V via USB atau external power
- Current: ~500mA (dengan semua sensor aktif)

## 📚 Library Requirements

Install library berikut di Arduino IDE:

### Core Libraries
```
WiFi (built-in ESP32)
HTTPClient (built-in ESP32)
```

### External Libraries
```
ArduinoJson by Benoit Blanchon (v6.x)
DHT sensor library by Adafruit
ESP32Servo by Kevin Harrington
```

### Installation Steps
1. Buka Arduino IDE
2. Go to **Tools > Manage Libraries**
3. Search dan install:
   - `ArduinoJson` (version 6.x)
   - `DHT sensor library`
   - `ESP32Servo`

## 🔌 Wiring Diagram

```
ESP32 Pin Connections:
├── DHT11
│   ├── VCC → 3.3V
│   ├── GND → GND
│   └── DATA → GPIO 25
├── pH Sensor
│   ├── VCC → 3.3V
│   ├── GND → GND
│   └── ANALOG → GPIO 34
├── LDR Module
│   ├── VCC → 3.3V
│   ├── GND → GND
│   └── ANALOG → GPIO 35
├── Water Level Sensor
│   ├── VCC → 3.3V
│   ├── GND → GND
│   └── ANALOG → GPIO 32
└── Servo Motor
    ├── VCC → 5V (VUSB)
    ├── GND → GND
    └── SIGNAL → GPIO 13
```

## ⚙️ Arduino IDE Setup

### 1. Install ESP32 Board
```
File > Preferences > Additional Board Manager URLs:
https://dl.espressif.com/dl/package_esp32_index.json

Tools > Board > Boards Manager > Search "ESP32" > Install
```

### 2. Board Configuration
```
Board: "ESP32 Dev Module"
CPU Frequency: "240MHz (WiFi/BT)"
Flash Frequency: "80MHz"
Flash Mode: "QIO"
Flash Size: "4MB (32Mb)"
Partition Scheme: "Default 4MB with spiffs"
Core Debug Level: "None"
PSRAM: "Disabled"
Port: [Select your ESP32 port]
```

## 📝 Code Configuration

### 1. WiFi Credentials
```cpp
const char* ssid = "Xiaomi 14T Pro";        // Ganti dengan nama hotspot Anda
const char* password = "jougen92";          // Ganti dengan password hotspot
```

### 2. API Server IP
```cpp
const char* api_server = "http://192.168.43.100:5000";  // Ganti dengan IP server API
```

**Cara mendapatkan IP server:**
1. Jalankan API server di laptop/PC
2. Hubungkan laptop ke hotspot yang sama
3. Check IP dengan command:
   - Linux/macOS: `ip addr show` atau `ifconfig`
   - Windows: `ipconfig`
   - Script otomatis: `./quickstart.sh` → pilih menu 6

### 3. Sensor Calibration
```cpp
// Kalibrasi pH sensor
float pH_offset = 0.0;  // Sesuaikan berdasarkan kalibrasi

// Threshold values
const float TEMP_THRESHOLD = 29.0;      // Suhu untuk tutup tirai (°C)
const int LDR_THRESHOLD = 2200;         // Cahaya terang (ADC value)
const int WATER_LEVEL_THRESHOLD = 1500; // Level air minimum
```

## 🚀 Upload & Testing

### 1. Upload Code
1. Connect ESP32 via USB
2. Select correct board and port
3. Click **Upload** button
4. Wait for "Hard resetting via RTS pin..." message

### 2. Monitor Serial Output
```
Tools > Serial Monitor > Set baud rate to 115200
```

### Expected Output:
```
🌱 ESP32 TERRAPONIX - API Integration
====================================
📡 API Server: http://192.168.43.100:5000
====================================
📶 Connecting to WiFi.........
✅ WiFi Connected!
📍 IP: 192.168.43.102
📋 Registering sensors...
✅ ESP32_TEMP_001 registered
✅ ESP32_HUM_001 registered
✅ ESP32_PH_001 registered
✅ ESP32_LIGHT_001 registered
✅ ESP32_WATER_001 registered
✅ All sensors registered!

🌱 === TERRAPONIX SENSOR DATA ===
🌡️  Temperature: 25.40 °C
💧 Humidity: 65.20 %
⚗️  pH: 7.15
☀️  Light: 1850
🚰 Water Level: 1650 (OK ✅)
🎚️  Curtain: OPEN 🔓
📶 WiFi: OK (-45 dBm)
🔗 API: REGISTERED ✅
⏱️  Uptime: 15 sec
==============================
```

## 🌐 Network Setup

### 1. Hotspot Configuration
1. **Enable hotspot** di smartphone
2. **Set hotspot name** dan password
3. **Connect ESP32** ke hotspot
4. **Connect API server device** ke hotspot yang sama

### 2. IP Address Setup
```
Typical hotspot IP range: 192.168.43.x
├── Router (phone): 192.168.43.1
├── ESP32: 192.168.43.102
└── API Server: 192.168.43.100
```

### 3. Verification
```bash
# Di perangkat API server, test koneksi:
ping 192.168.43.102  # IP ESP32

# Di browser, cek API:
http://192.168.43.100:5000/api/sensors/all
```

## 📊 Data Flow

```
ESP32 Sensors → HTTP POST → API Server → SQLite DB
     ↓                           ↓
Serial Monitor           App Client (real-time view)
```

### Sensor Registration
```json
POST /api/sensor/register
{
  "sensor_id": "ESP32_TEMP_001",
  "sensor_type": "temperature",
  "sensor_name": "ESP32 Temperature Sensor"
}
```

### Data Transmission
```json
POST /api/sensor/data
{
  "sensor_id": "ESP32_TEMP_001",
  "sensor_type": "temperature",
  "value": 25.4,
  "unit": "°C"
}
```

## 🔧 Troubleshooting

### WiFi Connection Issues
```cpp
❌ WiFi Failed!
```
**Solutions:**
- Check SSID and password
- Move ESP32 closer to hotspot
- Restart ESP32
- Check hotspot is active

### API Connection Issues
```cpp
❌ Error sending ESP32_TEMP_001: -1
```
**Solutions:**
- Verify API server IP address
- Check if API server is running
- Test with browser: `http://IP:5000/`
- Verify both devices on same network

### Sensor Reading Issues
```cpp
❌ DHT read error!
```
**Solutions:**
- Check DHT11 wiring
- Verify 3.3V power supply
- Add delay in sensor reading
- Replace faulty sensor

### Registration Failures
```cpp
❌ ESP32_TEMP_001 failed: 400
```
**Solutions:**
- Check JSON format
- Verify API endpoints
- Restart both ESP32 and API server
- Check ArduinoJson library version

## 📈 Monitoring & Analytics

### Real-time Monitoring
1. **Serial Monitor** - Local ESP32 data
2. **App Client** - Remote monitoring via API
3. **API endpoints** - Direct data access

### Data Visualization
Access via API client or direct HTTP:
```
GET /api/sensors/all           - Current data
GET /api/sensor/history/ESP32_TEMP_001  - Historical data
GET /api/sensor/status         - System status
```

## 🔄 Automatic Features

### Auto-Registration
- ESP32 automatically registers all 5 sensors on startup
- Re-registration on connection restore

### Auto-Reconnection
- WiFi reconnection on disconnection
- API error handling with retry logic
- Servo control continues during network issues

### Data Buffering
- Continues local operation during API downtime
- Error counting with circuit breaker pattern

## 🎛️ Control Features

### Automatic Curtain Control
```cpp
if (temperature >= 29°C && light >= 2200) {
    servo.write(0);   // Close curtain
} else {
    servo.write(90);  // Open curtain
}
```

### Manual Override
Modify thresholds in code:
```cpp
const float TEMP_THRESHOLD = 25.0;  // Lower temperature
const int LDR_THRESHOLD = 1500;     // Lower light threshold
```

## 🔒 Security Notes

- **Local network only** (hotspot security)
- **No authentication** (development mode)
- **Data validation** on sensor readings
- **Error handling** for robust operation

## 🚀 Quick Start Checklist

- [ ] Hardware assembled and wired correctly
- [ ] Arduino IDE setup with ESP32 support
- [ ] Required libraries installed
- [ ] WiFi credentials configured
- [ ] API server IP address updated
- [ ] Code uploaded successfully
- [ ] Serial monitor shows sensor data
- [ ] API server receiving data
- [ ] App client showing ESP32 sensors

## 📞 Support

Jika ada masalah:
1. Check wiring connections
2. Verify network configuration
3. Monitor serial output for errors
4. Test API endpoints manually
5. Check troubleshooting section above

---

**Happy coding with ESP32 Terraponix! 🌱📡**