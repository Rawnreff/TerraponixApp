# 🌱 Terraponix Greenhouse Automation System

A complete IoT-based greenhouse automation system using ESP32, featuring real-time monitoring, automated irrigation, climate control, and remote management capabilities.

## 🎯 Features

### 📊 Real-time Monitoring
- **Temperature & Humidity** monitoring with DHT11 sensor
- **pH Level** measurement for water quality
- **Soil Moisture** detection for irrigation control
- **Light Intensity** monitoring for curtain automation
- **Water Level** sensing for reservoir management

### 🎛️ Automated Controls
- **Smart Irrigation** - Automatic pump control based on soil moisture
- **Climate Control** - Fan activation based on temperature
- **Light Management** - Automated curtain control for optimal lighting
- **Manual Override** - Switch between automatic and manual modes

### 🌐 Remote Access
- **Web Dashboard** - Real-time monitoring and control interface
- **RESTful API** - Complete API for integration and automation
- **Historical Data** - Data logging and trend analysis
- **Mobile Friendly** - Responsive design for mobile devices

### 🔧 ESP32 Integration
- **WiFi Connectivity** - Wireless sensor data transmission
- **Local Web Server** - Direct device control interface
- **OTA Updates** - Over-the-air firmware updates support
- **Serial Monitoring** - Debug and maintenance via serial interface

## 📁 Project Structure

```
greenhouse-automation/
├── esp32/
│   └── terraponix_greenhouse.ino     # ESP32 Arduino code
├── greenhouse_api.py                 # Main API server
├── test_greenhouse_system.py         # System testing utility
├── start_greenhouse_system.py        # Easy startup script
├── GREENHOUSE_README.md              # This documentation
└── requirements.txt                  # Python dependencies
```

## 🚀 Quick Start

### 1. System Setup

```bash
# Clone or download the project files
# Navigate to the project directory

# Start the complete system
python start_greenhouse_system.py
```

The startup script will:
- Check and install dependencies
- Start the API server
- Display setup instructions
- Show network information

### 2. ESP32 Setup

#### Hardware Requirements
- ESP32 development board
- DHT11 temperature/humidity sensor
- pH sensor module
- LDR (Light Dependent Resistor)
- Soil moisture sensor
- Water level sensor
- Servo motor (for curtain)
- Water pump
- Cooling fan
- Relay modules for pump/fan control

#### Pin Configuration
```cpp
#define DHTPIN 25         // DHT11 sensor
#define PH_PIN 34         // pH sensor (analog)
#define LDR_PIN 35        // Light sensor (analog)
#define SERVO_PIN 13      // Servo motor
#define WATER_LEVEL_PIN 32 // Water level sensor
#define PUMP_PIN 14       // Water pump relay
#define FAN_PIN 12        // Fan relay
#define SOIL_MOISTURE_PIN 33 // Soil moisture sensor
```

#### Arduino IDE Setup
1. Install required libraries:
   - `ArduinoJson` by Benoit Blanchon
   - `DHT sensor library` by Adafruit
   - `ESP32Servo` by Kevin Harrington

2. Open `esp32/terraponix_greenhouse.ino`

3. Update configuration:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* serverURL = "http://YOUR_SERVER_IP:5000/api/greenhouse-data";
   ```

4. Upload to ESP32

### 3. Access the System

Once running, access these interfaces:

- **Main Dashboard**: `http://your-ip:5000/dashboard`
- **API Status**: `http://your-ip:5000/`
- **ESP32 Interface**: `http://esp32-ip/` (shown in serial monitor)

## 📊 API Documentation

### Core Endpoints

#### Device Registration
```http
POST /api/register
Content-Type: application/json

{
  "device_id": "greenhouse_esp32",
  "device_type": "greenhouse_controller",
  "ip_address": "192.168.1.100",
  "capabilities": "temperature,humidity,ph,light,water_level,soil_moisture,pump,fan,curtain"
}
```

#### Send Sensor Data
```http
POST /api/greenhouse-data
Content-Type: application/json

{
  "device_id": "greenhouse_esp32",
  "temperature": 25.5,
  "humidity": 65.0,
  "ph": 6.8,
  "light_intensity": 1500,
  "water_level": 1200,
  "soil_moisture": 45,
  "pump_status": "OFF",
  "fan_status": "OFF",
  "curtain_status": "OPEN",
  "mode": "AUTO"
}
```

#### Get Current Status
```http
GET /api/greenhouse/status?device_id=greenhouse_esp32
```

#### Send Control Commands
```http
POST /api/greenhouse-control
Content-Type: application/json

{
  "device_id": "greenhouse_esp32",
  "device": "pump",
  "value": true
}
```

#### Get Historical Data
```http
GET /api/greenhouse/history?device_id=greenhouse_esp32&hours=24&limit=100
```

## 🎛️ Control Features

### Automatic Mode
The system automatically controls devices based on sensor readings:

- **Irrigation**: Pump activates when soil moisture < 30%
- **Cooling**: Fan starts when temperature > 29°C
- **Shading**: Curtain closes when temperature > 29°C AND light > 2200

### Manual Mode
Override automatic controls for manual operation:
- Individual device control (pump, fan, curtain)
- Real-time status monitoring
- Instant command execution

### Thresholds (Configurable)
```cpp
const float TEMP_THRESHOLD = 29.0;        // Temperature limit (°C)
const int LDR_THRESHOLD = 2200;           // Light intensity limit
const int WATER_LEVEL_THRESHOLD = 1500;   // Water level minimum
const int SOIL_MOISTURE_THRESHOLD = 30;   // Soil moisture minimum (%)
```

## 🔧 Testing & Debugging

### Run System Tests
```bash
python test_greenhouse_system.py
```

Test features:
- API connectivity
- Device registration
- Data transmission
- Control commands
- Historical data retrieval

### ESP32 Serial Monitor
Monitor ESP32 status via Arduino IDE Serial Monitor:
- WiFi connection status
- Sensor readings
- Server communication
- Control actions
- Error messages

### Debug Commands
```bash
# Test API manually
curl -X GET http://localhost:5000/

# Send test data
curl -X POST http://localhost:5000/api/greenhouse-data \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test","temperature":25.0,"humidity":60.0,"ph":7.0,"light_intensity":1000,"water_level":1500,"soil_moisture":50}'

# Send control command
curl -X POST http://localhost:5000/api/greenhouse-control \
  -H "Content-Type: application/json" \
  -d '{"device":"pump","value":true}'
```

## 📱 Web Dashboard Features

### Real-time Monitoring
- Live sensor data updates every 10 seconds
- Visual status indicators
- Historical trend charts
- Alert notifications

### Device Control
- One-click device control buttons
- Mode switching (Auto/Manual)
- Instant feedback
- Status confirmation

### Data Visualization
- Temperature and humidity graphs
- pH level monitoring
- Soil moisture trends
- Light intensity charts

## 🔒 Security & Best Practices

### Network Security
- Use WPA2/WPA3 WiFi encryption
- Consider VPN for remote access
- Regular password updates
- Network isolation for IoT devices

### System Maintenance
- Regular sensor calibration
- Database backup
- Log rotation
- Firmware updates

### Monitoring
- Set up alerts for critical thresholds
- Monitor system uptime
- Track data transmission errors
- Regular system health checks

## 🛠️ Troubleshooting

### Common Issues

#### ESP32 Won't Connect to WiFi
1. Check SSID and password
2. Verify WiFi signal strength
3. Check 2.4GHz network availability
4. Reset ESP32 and retry

#### No Data on Dashboard
1. Verify ESP32 is connected
2. Check server IP address in ESP32 code
3. Ensure firewall allows port 5000
4. Check serial monitor for errors

#### Sensors Reading Incorrect Values
1. Check sensor connections
2. Calibrate sensors if needed
3. Verify power supply voltage
4. Replace faulty sensors

#### Controls Not Working
1. Check relay connections
2. Verify control pin assignments
3. Test manual mode
4. Check power supply to actuators

### Error Codes
- `HTTP Error 404`: Server endpoint not found
- `HTTP Error 500`: Server internal error
- `WiFi Connection Failed`: Network connectivity issue
- `Sensor Read Error`: Hardware connection problem

## 📈 Future Enhancements

### Planned Features
- [ ] Mobile app development
- [ ] Weather API integration
- [ ] Machine learning predictions
- [ ] Multi-greenhouse support
- [ ] Advanced scheduling
- [ ] Email/SMS notifications
- [ ] Solar power monitoring
- [ ] Camera integration

### Expansion Ideas
- Add more sensor types (CO2, nutrients)
- Implement greenhouse zones
- Add weather station integration
- Create mobile notifications
- Develop predictive analytics
- Add voice control integration

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open-source and available under the MIT License.

## 📞 Support

For support and questions:
- Check the troubleshooting section
- Review the API documentation
- Test with the provided test utilities
- Check ESP32 serial monitor output

## 🎉 Acknowledgments

- Arduino community for ESP32 libraries
- Flask framework for the web API
- Open-source sensor libraries
- IoT agriculture community

---

**Happy Growing! 🌱**

*Terraponix - Automated IoT Agriculture for the Future*