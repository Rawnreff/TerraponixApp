# 🌱 Terraponix Greenhouse Web System

Sistem monitoring dan kontrol greenhouse otomatis berbasis web untuk tanaman hidroponik dan tanah. Menggunakan ESP32 sebagai controller dan dapat diintegrasikan dengan Laravel untuk backend yang lebih powerful.

## 📋 Daftar Isi

- [Fitur Utama](#fitur-utama)
- [Komponen Hardware](#komponen-hardware)
- [Instalasi ESP32](#instalasi-esp32)
- [Instalasi Laravel (Opsional)](#instalasi-laravel-opsional)
- [Konfigurasi](#konfigurasi)
- [Penggunaan](#penggunaan)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

## 🚀 Fitur Utama

### ESP32 Standalone Features
- ✅ Web server lokal di ESP32
- ✅ Monitoring real-time sensor (suhu, kelembapan, pH, cahaya, kelembapan tanah, level air)
- ✅ Kontrol otomatis pompa air, kipas, dan tirai
- ✅ Mode manual dan otomatis
- ✅ Interface web responsif dengan auto-refresh
- ✅ Data logging internal (100 entries)
- ✅ mDNS support (akses via terraponix.local)
- ✅ Status LED untuk indikasi sistem
- ✅ WiFi auto-reconnect

### Laravel Integration Features (Opsional)
- ✅ Database storage untuk historical data
- ✅ RESTful API endpoints
- ✅ Advanced analytics dan statistik
- ✅ Alert system
- ✅ Multi-device support
- ✅ Web dashboard yang lebih advanced

## 🔧 Komponen Hardware

### Sensor yang Digunakan
- **DHT11/DHT22** - Sensor suhu dan kelembapan udara
- **pH Sensor** - Sensor pH air untuk hidroponik
- **LDR** - Sensor intensitas cahaya
- **Water Level Sensor** - Sensor level air
- **Soil Moisture Sensor** - Sensor kelembapan tanah

### Actuator yang Digunakan
- **Servo Motor** - Untuk menggerakkan tirai/shade
- **Water Pump** - Pompa air untuk irigasi
- **Cooling Fan** - Kipas pendingin
- **LED Status** - Indikator status sistem

### Pin Configuration (ESP32)
```cpp
#define DHTPIN 25         // Pin DHT11
#define PH_PIN 34         // Pin pH sensor (Analog)
#define LDR_PIN 35        // Pin LDR (Analog)
#define SERVO_PIN 13      // Pin Servo (Curtain)
#define WATER_LEVEL_PIN 32 // Pin Water Level Sensor (Analog)
#define PUMP_PIN 14       // Pin Water Pump
#define FAN_PIN 12        // Pin Fan
#define SOIL_MOISTURE_PIN 33 // Pin Soil Moisture Sensor (Analog)
#define LED_STATUS_PIN 2  // Built-in LED for status indication
```

## 📦 Instalasi ESP32

### 1. Persiapan Arduino IDE
```bash
# Install ESP32 Board di Arduino IDE
# File > Preferences > Additional Board Manager URLs:
https://dl.espressif.com/dl/package_esp32_index.json

# Tools > Board > Boards Manager > Search "ESP32" > Install
```

### 2. Install Library yang Diperlukan
```cpp
// Library yang harus diinstall via Library Manager:
- WiFi (built-in)
- WebServer (built-in)
- ArduinoJson by Benoit Blanchon
- DHT sensor library by Adafruit
- ESP32Servo by Kevin Harrington
- SPIFFS (built-in)
- ESPmDNS (built-in)
```

### 3. Upload Code ke ESP32
1. Buka file `esp32/terraponix_web_optimized.ino`
2. Ubah kredensial WiFi:
```cpp
const char* ssid = "NAMA_WIFI_ANDA";
const char* password = "PASSWORD_WIFI_ANDA";
```
3. Pilih board ESP32 dan port yang sesuai
4. Upload code ke ESP32

### 4. Monitoring Serial
```bash
# Buka Serial Monitor dengan baud rate 115200
# Anda akan melihat output seperti:
🌱 TERRAPONIX Greenhouse Web System
=====================================
Version: v2.0
Device: Terraponix-Greenhouse
=====================================
✅ SPIFFS Mounted Successfully
🔧 Hardware initialized
🔗 Connecting to WiFi: NAMA_WIFI_ANDA
✅ WiFi Connected Successfully!
📍 IP Address: 192.168.1.100
🌐 mDNS responder started: http://terraponix.local
🌐 Web server started successfully
✅ System fully initialized!
🌐 Web Interface: http://192.168.1.100
🌐 Local Domain: http://terraponix.local
```

## 🌐 Instalasi Laravel (Opsional)

Jika Anda ingin menggunakan backend Laravel untuk fitur yang lebih advanced:

### 1. Setup Laravel Project
```bash
# Create new Laravel project
composer create-project laravel/laravel terraponix-backend

cd terraponix-backend

# Install dependencies
composer install
npm install
```

### 2. Database Setup
```bash
# Copy migration file
cp laravel_integration/create_terraponix_tables.php database/migrations/

# Copy controller
cp laravel_integration/TerraponixController.php app/Http/Controllers/

# Run migration
php artisan migrate
```

### 3. Routes Setup
```php
// Add to routes/web.php or routes/api.php
include 'laravel_integration/web_routes.php';
```

### 4. Start Laravel Server
```bash
php artisan serve --host=0.0.0.0 --port=8000
```

## ⚙️ Konfigurasi

### ESP32 Configuration
Ubah konfigurasi di bagian atas file `.ino`:

```cpp
// WiFi credentials - GANTI SESUAI WIFI ANDA
const char* ssid = "Xiaomi 14T Pro";
const char* password = "jougen92";

// Thresholds and Calibration
const float TEMP_THRESHOLD_HIGH = 29.0;  // Suhu tinggi (°C)
const float TEMP_THRESHOLD_LOW = 25.0;   // Suhu rendah (°C)
const int LDR_THRESHOLD = 2200;          // Threshold intensitas cahaya
const int WATER_LEVEL_THRESHOLD = 1500;  // Threshold level air
const int SOIL_MOISTURE_THRESHOLD_LOW = 30;  // Kelembapan tanah minimum %
const int SOIL_MOISTURE_THRESHOLD_HIGH = 80; // Kelembapan tanah maksimum %
```

### Kalibrasi Sensor pH
```cpp
// Sesuaikan pH offset berdasarkan kalibrasi sensor Anda
float pH_offset = 0.0; // Sesuaikan nilai ini
```

## 🖥️ Penggunaan

### Akses Web Interface

1. **Via IP Address**: `http://192.168.1.100` (sesuai IP ESP32 Anda)
2. **Via mDNS**: `http://terraponix.local` (lebih mudah diingat)

### Fitur Web Interface

#### Dashboard Utama
- **Sensor Readings**: Menampilkan data real-time dari semua sensor
- **Device Controls**: Kontrol manual untuk pompa, kipas, tirai
- **System Status**: Status WiFi, sistem, dan mode operasi
- **Auto Refresh**: Otomatis refresh setiap 15 detik

#### Control Features
- **Water Pump**: ON/OFF manual atau otomatis berdasarkan kelembapan tanah
- **Cooling Fan**: ON/OFF manual atau otomatis berdasarkan suhu
- **Shade Curtain**: Open/Close manual atau otomatis berdasarkan suhu + cahaya
- **Control Mode**: Switch antara AUTO dan MANUAL
- **System Control**: Enable/Disable seluruh sistem

#### Data Logging
- **View Logs**: Klik tombol "📊 View Logs" untuk melihat history data
- **Auto Logging**: Sistem otomatis menyimpan 100 entry terakhir
- **Action Logging**: Mencatat semua aksi otomatis yang dilakukan sistem

### Logika Kontrol Otomatis

#### Kontrol Tirai (Curtain)
```cpp
// Tutup tirai jika: Suhu >= 29°C DAN Cahaya >= 2200
// Buka tirai jika: Suhu <= 25°C ATAU Cahaya < 2200
```

#### Kontrol Pompa Air
```cpp
// Nyalakan pompa jika: Kelembapan tanah < 30%
// Matikan pompa jika: Kelembapan tanah > 80%
```

#### Kontrol Kipas
```cpp
// Nyalakan kipas jika: Suhu > 29°C
// Matikan kipas jika: Suhu < 25°C
```

## 🔌 API Endpoints

### ESP32 Local API

#### GET `/` - Main Dashboard
Menampilkan interface web utama

#### GET `/data` - Sensor Data JSON
```json
{
  "device_name": "Terraponix-Greenhouse",
  "version": "v2.0",
  "temperature": 26.5,
  "humidity": 65.2,
  "ph": 6.8,
  "light_intensity": 2500,
  "water_level": 1800,
  "soil_moisture": 45,
  "pump_status": "OFF",
  "fan_status": "OFF",
  "curtain_status": "OPEN",
  "mode": "AUTO",
  "timestamp": 1234567890
}
```

#### POST `/control/{device}` - Device Control
```bash
# Control pump
curl -X POST http://192.168.1.100/control/pump -d "state=on"

# Control fan
curl -X POST http://192.168.1.100/control/fan -d "state=off"

# Control curtain
curl -X POST http://192.168.1.100/control/curtain -d "state=close"

# Change mode
curl -X POST http://192.168.1.100/control/mode -d "mode=manual"

# System control
curl -X POST http://192.168.1.100/control/system -d "state=on"
```

#### GET `/logs` - Data Logs Page
Menampilkan halaman history data dalam bentuk tabel

### Laravel API (Jika digunakan)

#### POST `/api/terraponix/sensor-data` - Receive Data
```json
{
  "status": "success",
  "message": "Sensor data received and stored successfully"
}
```

#### GET `/api/terraponix/latest` - Latest Data
```json
{
  "status": "success",
  "data": { /* latest sensor data */ }
}
```

#### GET `/api/terraponix/statistics` - Statistics
```json
{
  "status": "success",
  "sensor_stats": {
    "temperature": {
      "average": 26.5,
      "minimum": 22.1,
      "maximum": 31.2
    }
    // ... more stats
  }
}
```

## 🔧 Troubleshooting

### WiFi Connection Issues
```cpp
// Problem: ESP32 tidak bisa connect ke WiFi
// Solution:
1. Pastikan SSID dan password benar
2. Pastikan ESP32 dalam jangkauan WiFi
3. Restart ESP32 dan router
4. Check Serial Monitor untuk error messages
```

### Sensor Reading Issues
```cpp
// Problem: Sensor DHT memberikan nilai NaN
// Solution:
1. Check koneksi kabel sensor
2. Pastikan power supply cukup (3.3V atau 5V)
3. Ganti sensor jika rusak
4. Check pin configuration

// Problem: Sensor pH tidak akurat
// Solution:
1. Kalibrasi sensor dengan larutan pH standar
2. Adjust pH_offset value
3. Bersihkan probe sensor
```

### Web Interface Issues
```cpp
// Problem: Tidak bisa akses web interface
// Solution:
1. Check IP address di Serial Monitor
2. Pastikan device dan komputer dalam network yang sama
3. Try both IP address dan terraponix.local
4. Disable firewall sementara

// Problem: Interface tidak responsive
// Solution:
1. Refresh browser (Ctrl+F5)
2. Clear browser cache
3. Try different browser
4. Check ESP32 memory dengan Serial Monitor
```

### Performance Issues
```cpp
// Problem: ESP32 restart terus-menerus
// Solution:
1. Check power supply (minimum 1A)
2. Reduce sensor reading frequency
3. Check for memory leaks di Serial Monitor
4. Remove unnecessary Serial.println statements

// Problem: Web interface lambat
// Solution:
1. Reduce auto-refresh interval
2. Optimize HTML generation
3. Use SPIFFS for static files
4. Check WiFi signal strength
```

### Memory Issues
```cpp
// Problem: ESP32 out of memory
// Solution:
1. Reduce MAX_LOG_ENTRIES value
2. Use F() macro for string constants
3. Optimize JSON document sizes
4. Monitor free heap di Serial Monitor
```

## 📱 Mobile Access

Interface web sudah responsive dan dapat diakses dari:
- **Smartphone** - Interface otomatis menyesuaikan layar kecil
- **Tablet** - Layout grid optimal untuk layar medium
- **Desktop** - Full feature dengan layout lengkap

## 🔐 Security Notes

Untuk penggunaan production:
1. **Change default credentials** - Ganti SSID dan password
2. **Use HTTPS** - Implement SSL/TLS jika diperlukan
3. **Access Control** - Implement authentication untuk web interface
4. **Network Security** - Gunakan WPA2/WPA3 untuk WiFi
5. **Regular Updates** - Update firmware secara berkala

## 📈 Future Enhancements

Fitur yang bisa ditambahkan:
- **Mobile App** - React Native atau Flutter app
- **Cloud Integration** - AWS IoT atau Google Cloud IoT
- **Machine Learning** - Predictive analytics untuk optimasi
- **Multiple Zones** - Support untuk multiple greenhouse zones
- **Weather Integration** - API cuaca untuk prediksi
- **Email/SMS Alerts** - Notifikasi via email atau SMS
- **Voice Control** - Integration dengan Google Assistant/Alexa

## 🤝 Contributing

Jika Anda ingin berkontribusi:
1. Fork repository ini
2. Create feature branch
3. Commit changes
4. Push ke branch
5. Create Pull Request

## 📄 License

MIT License - bebas digunakan untuk project personal dan komersial.

## 📞 Support

Jika ada pertanyaan atau butuh bantuan:
- **Email**: support@terraponix.com
- **GitHub Issues**: Create issue di repository
- **Documentation**: Check file ini dan komentar di code

---

**Happy Growing! 🌱**

*Terraponix - Smart Greenhouse for Smart Farmers*