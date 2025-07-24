# 🌱 Terraponix: Smart Farm System

**Sistem Rumah Tani Pintar berbasis IoT dan Energi Surya**

Terraponix adalah solusi inovatif untuk urban farming yang mengintegrasikan teknologi IoT, energi surya, dan sistem monitoring real-time. Sistem ini dirancang untuk mengoptimalkan produktivitas pertanian perkotaan dengan otomatisasi penuh dan kontrol yang mudah digunakan.

## 🚀 Fitur Utama

### 📊 Monitoring Real-time
- **Sensor Lingkungan**: Suhu, kelembapan, pH, TDS, intensitas cahaya, CO₂
- **Monitoring Tanaman**: Kelembapan tanah, level air nutrisi
- **Status Energi**: Level baterai, produksi panel surya
- **Dashboard Mobile**: Interface modern dan responsif

### 🎛️ Kontrol Otomatis
- **Pompa Nutrisi**: Otomatis berdasarkan kelembapan tanah
- **Kipas Ventilasi**: Kontrol suhu otomatis
- **Tirai Sensorik**: Pengaturan intensitas cahaya
- **Mode Manual**: Override kontrol otomatis kapan saja

### 🔔 System Alerts
- **Notifikasi Real-time**: Alert untuk kondisi kritis
- **Kategorisasi Alert**: Info, Warning, Critical
- **Log History**: Riwayat semua aktivitas sistem
- **Filter & Search**: Mudah menemukan alert spesifik

### ⚡ Sustainable Energy
- **100% Solar Powered**: Mandiri energi dengan panel surya
- **MPPT Controller**: Efisiensi maksimal pengisian baterai
- **Battery Monitoring**: Real-time status dan estimasi durasi

## 🏗️ Arsitektur Sistem

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│    ESP32 IoT    │───▶│  Flask Backend  │───▶│ React Native App│
│   (Sensor Hub)  │    │   (API Server)  │    │   (Dashboard)   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│ Sensors & Relay │    │ SQLite Database │    │  Mobile Device  │
│   Controllers   │    │  (Data Storage) │    │   (Android)     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Hardware Requirements

### ESP32 Development Board
- **Mikrokontroler**: ESP32-WROOM-32
- **WiFi**: 802.11 b/g/n
- **GPIO**: Minimum 15 pin untuk sensor dan kontrol
- **ADC**: 8 channel untuk sensor analog

### Sensor Components
| Sensor | Model | Purpose | Pin Connection |
|--------|-------|---------|----------------|
| DHT22 | Temperature & Humidity | Monitoring lingkungan | Digital Pin 4 |
| pH Sensor | Analog pH meter | Kualitas nutrisi | Analog Pin A0 |
| TDS Sensor | EC/TDS meter | Konsentrasi nutrisi | Analog Pin A1 |
| LDR | Light Dependent Resistor | Intensitas cahaya | Analog Pin A2 |
| CO2 Sensor | MQ-135 | Kualitas udara | Analog Pin A3 |
| Soil Moisture | Capacitive sensor | Kelembapan tanah | Analog Pin A4 |
| Water Level | Ultrasonic/Float | Level air | Analog Pin A5 |

### Control Components
| Device | Purpose | Pin Connection |
|--------|---------|----------------|
| Water Pump | Irigasi otomatis | Digital Pin 2 |
| Exhaust Fan | Ventilasi udara | Digital Pin 3 |
| Servo Motor | Kontrol tirai | Digital Pin 5 |

### Power System
- **Solar Panel**: 50W minimum
- **Battery**: 12V 20Ah LiFePO4
- **MPPT Controller**: 10A rating
- **DC-DC Converter**: 12V to 5V/3.3V

## 💻 Software Setup

### Backend (Flask Server)

1. **Install Python Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Run Flask Server**
```bash
python app.py
```
Server akan berjalan di `http://localhost:5000`

### Mobile App (React Native)

1. **Install Dependencies**
```bash
npm install
```

2. **Configure Server URL**
Edit file `services/apiService.ts`:
```typescript
const BASE_URL = 'http://YOUR_LAPTOP_IP:5000/api';
```

3. **Run Development Server**
```bash
# For Android
npm run android

# For iOS
npm run ios

# Web version
npm run web
```

### ESP32 Firmware

1. **Install Arduino IDE Libraries**
   - WiFi (built-in)
   - HTTPClient (built-in)
   - ArduinoJson
   - DHT sensor library

2. **Configure WiFi & Server**
Edit file `esp32/terraponix_esp32.ino`:
```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverURL = "http://YOUR_LAPTOP_IP:5000/api/sensor-data";
```

3. **Upload to ESP32**
   - Select board: ESP32 Dev Module
   - Upload firmware via USB

## 🔧 Configuration

### 1. Network Setup
- Pastikan ESP32, Laptop, dan Mobile Device dalam jaringan WiFi yang sama
- Catat IP address laptop untuk konfigurasi
- Test konektivitas dengan ping

### 2. Sensor Calibration
```cpp
// pH Sensor Calibration
currentData.ph = mapFloat(phRaw, 0, 4095, 4.0, 10.0);

// TDS Sensor Calibration  
currentData.tds = mapFloat(tdsRaw, 0, 4095, 0, 2000);
```

### 3. Control Thresholds
Dapat disesuaikan melalui mobile app atau langsung di database:
```sql
UPDATE control_settings SET
  temp_threshold_min = 20.0,
  temp_threshold_max = 30.0,
  humidity_threshold_min = 60.0,
  humidity_threshold_max = 80.0;
```

## 🚀 Quick Start Guide

### Step 1: Hardware Assembly
1. Pasang semua sensor sesuai pin diagram
2. Hubungkan relay untuk kontrol pump, fan, servo
3. Install solar panel dan battery system
4. Test semua koneksi hardware

### Step 2: Software Installation
1. Setup Flask backend di laptop
2. Install mobile app di Android device
3. Upload firmware ke ESP32
4. Test komunikasi antar komponen

### Step 3: System Configuration
1. Configure WiFi credentials di ESP32
2. Set server IP address di mobile app
3. Calibrate sensors sesuai kebutuhan
4. Test automatic control functions

### Step 4: Deployment
1. Place system di lokasi greenhouse
2. Ensure solar panel exposure optimal
3. Monitor system melalui mobile app
4. Fine-tune thresholds sesuai tanaman

## 📱 Mobile App Features

### Dashboard Tab
- **Real-time Monitoring**: Live sensor readings
- **Device Status**: Battery, solar, connectivity
- **Visual Indicators**: Color-coded status alerts
- **Auto Refresh**: Data update setiap 30 detik

### Controls Tab
- **Device Management**: Manual control pump, fan, curtain
- **Auto Mode**: Toggle automatic/manual operation
- **Quick Actions**: System reset, emergency stop
- **Threshold Settings**: Adjust automation parameters

### Alerts Tab
- **Real-time Notifications**: Critical system alerts
- **Filter Options**: By severity (Critical/Warning/Info)
- **Alert History**: Complete log with timestamps
- **Alert Details**: Detailed information per alert

## 🛡️ Troubleshooting

### Common Issues

**ESP32 tidak connect ke WiFi:**
- Periksa SSID dan password
- Pastikan signal WiFi kuat
- Reset ESP32 dan coba lagi

**Mobile app tidak terima data:**
- Cek IP address server di apiService.ts
- Pastikan Flask server running
- Test dengan browser: `http://laptop-ip:5000/api/health`

**Sensor readings tidak akurat:**
- Calibrate sensor sesuai datasheet
- Check wiring dan ground connections
- Verify power supply stability

**Automatic control tidak berfungsi:**
- Check relay connections
- Verify control pin assignments
- Monitor Serial output untuk debug

### Debug Commands

**Test Flask API:**
```bash
curl -X GET http://localhost:5000/api/current-data
curl -X POST http://localhost:5000/api/sensor-data \
  -H "Content-Type: application/json" \
  -d '{"temperature":25.5,"humidity":60.0,"ph":6.5,"tds":850,"light_intensity":75,"co2":400}'
```

**ESP32 Serial Monitor:**
```
🌱 Terraponix ESP32 System Initialized
📡 Starting sensor monitoring...
✅ WiFi Connected! IP address: 192.168.1.123
📊 Sensor Readings:
   🌡️  Temperature: 25.5°C
   💧  Humidity: 68.2%
```

## 🤝 Contributing

Kontribusi sangat diterima! Silakan:

1. Fork repository
2. Buat feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

## 📄 License

Project ini dilisensikan di bawah MIT License - lihat file [LICENSE](LICENSE) untuk detail.

## 👥 Team

**Terraponix Development Team:**
- Rafen Sidiq Anggara - Lead Developer
- Timothy Shalom Siadari - Hardware Engineer
- SMK Telkom Sidoarjo - Supporting Institution

## 📞 Support

Untuk bantuan dan pertanyaan:
- Email: rafenrafen1312@gmail.com
- Institution: SMK Telkom Sidoarjo

---

## 🎯 Vision & Mission

**Vision:** Mewujudkan urban farming yang sustainable dan accessible untuk semua kalangan melalui teknologi IoT dan energi terbarukan.

**Mission:**
- Mengoptimalkan produktivitas pertanian perkotaan
- Mendukung ketahanan pangan dengan teknologi smart farming
- Memberikan solusi ramah lingkungan untuk pertanian modern
- Memungkinkan monitoring dan kontrol yang mudah digunakan

---

*Terraponix - Smart Technology for Sustainable Agriculture* 🌱
