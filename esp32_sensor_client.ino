#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <ESP32Servo.h>

// Pin Definitions
#define DHTPIN 25       // Pin DHT11
#define DHTTYPE DHT11
#define PH_PIN 34       // Pin pH sensor (Analog)
#define LDR_PIN 35      // Pin LDR (Analog)
#define SERVO_PIN 13    // Pin Servo
#define WATER_LEVEL_PIN 32  // Pin Water Level Sensor (Analog)

// WiFi Credentials
const char* ssid = "Xiaomi 14T Pro";
const char* password = "jougen92";

// API Server Configuration
// GANTI IP INI DENGAN IP ADDRESS PERANGKAT YANG MENJALANKAN API SERVER
const char* api_server = "http://192.168.43.100:5000";  // Ganti dengan IP hotspot Anda
const char* sensor_id = "ESP32_TERRAPONIX_001";
const char* register_endpoint = "/api/sensor/register";
const char* data_endpoint = "/api/sensor/data";

DHT dht(DHTPIN, DHTTYPE);
Servo servo;

// Kalibrasi
float pH_offset = 0.0;
const float TEMP_THRESHOLD = 29.0;  // Suhu panas (°C)
const int LDR_THRESHOLD = 2200;     // Cahaya terang (LDR ≥2200)
const int WATER_LEVEL_THRESHOLD = 1500;  // Threshold level air (sesuaikan)

// Status tracking
bool sensor_registered = false;
unsigned long last_api_call = 0;
const unsigned long API_INTERVAL = 10000;  // Kirim data setiap 10 detik
int api_error_count = 0;
const int MAX_API_ERRORS = 5;

void setup() {
  Serial.begin(115200);
  
  // Mulai koneksi WiFi
  connectToWiFi();
  
  // Inisialisasi sensor dan servo
  dht.begin();
  servo.attach(SERVO_PIN);
  servo.write(90);  // Posisi awal servo
  pinMode(WATER_LEVEL_PIN, INPUT);
  
  Serial.println("\n🌱 SISTEM TERRAPONIX ESP32 Started!");
  Serial.println("=====================================");
  Serial.print("📡 API Server: ");
  Serial.println(api_server);
  Serial.print("🆔 Sensor ID: ");
  Serial.println(sensor_id);
  Serial.println("=====================================");
  
  // Registrasi sensor ke API
  if (WiFi.status() == WL_CONNECTED) {
    registerSensor();
  }
}

void loop() {
  // Periksa status WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ Koneksi WiFi terputus! Mencoba menghubungkan kembali...");
    connectToWiFi();
    return;
  }

  // Baca semua sensor
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  int ldr_value = analogRead(LDR_PIN);
  float pH_value = read_pH();
  int water_level = analogRead(WATER_LEVEL_PIN);

  // Validasi pembacaan DHT
  if (isnan(temp) || isnan(hum)) {
    Serial.println("❌ Gagal membaca sensor DHT!");
    temp = 0.0;
    hum = 0.0;
  }

  // Kontrol servo otomatis
  controlServo(temp, ldr_value);

  // Tampilkan data di Serial Monitor
  printSensorData(temp, hum, pH_value, ldr_value, water_level);

  // Kirim data ke API server (setiap interval tertentu)
  if (millis() - last_api_call >= API_INTERVAL) {
    if (WiFi.status() == WL_CONNECTED) {
      sendSensorDataToAPI(temp, hum, pH_value, ldr_value, water_level);
    }
    last_api_call = millis();
  }

  delay(2000);
}

void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.println("📶 Menghubungkan ke WiFi...");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Terhubung!");
    Serial.print("📍 Alamat IP: ");
    Serial.println(WiFi.localIP());
    api_error_count = 0;  // Reset error count saat WiFi terhubung
  } else {
    Serial.println("\n❌ Gagal terhubung ke WiFi!");
  }
}

void registerSensor() {
  if (sensor_registered) return;
  
  Serial.println("📋 Mendaftarkan sensor ke API server...");
  
  HTTPClient http;
  http.begin(String(api_server) + register_endpoint);
  http.addHeader("Content-Type", "application/json");
  
  // Buat JSON untuk registrasi
  StaticJsonDocument<200> doc;
  doc["sensor_id"] = sensor_id;
  doc["sensor_type"] = "terraponix_multi";
  doc["sensor_name"] = "ESP32 Terraponix Multi-Sensor";
  
  String json_string;
  serializeJson(doc, json_string);
  
  int http_code = http.POST(json_string);
  
  if (http_code > 0) {
    String response = http.getString();
    Serial.print("📡 Response: ");
    Serial.println(response);
    
    if (http_code == 200) {
      sensor_registered = true;
      Serial.println("✅ Sensor berhasil terdaftar!");
    } else {
      Serial.println("⚠️ Registrasi gagal, akan dicoba lagi nanti");
    }
  } else {
    Serial.print("❌ Error registrasi: ");
    Serial.println(http.errorToString(http_code));
  }
  
  http.end();
}

void sendSensorDataToAPI(float temp, float hum, float pH, int ldr, int water_level) {
  if (!sensor_registered) {
    registerSensor();
    if (!sensor_registered) return;
  }
  
  // Cek error count
  if (api_error_count >= MAX_API_ERRORS) {
    Serial.println("⚠️ Terlalu banyak error API, skip pengiriman data");
    return;
  }
  
  Serial.println("📤 Mengirim data sensor ke API...");
  
  HTTPClient http;
  http.begin(String(api_server) + data_endpoint);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);  // 5 detik timeout
  
  // Buat JSON dengan semua data sensor
  StaticJsonDocument<500> doc;
  doc["sensor_id"] = sensor_id;
  doc["sensor_type"] = "terraponix_multi";
  
  // Data sensor utama
  doc["temperature"] = temp;
  doc["humidity"] = hum;
  doc["ph"] = pH;
  doc["light_intensity"] = ldr;
  doc["water_level"] = water_level;
  
  // Status tambahan
  doc["servo_position"] = servo.read();
  doc["curtain_status"] = (servo.read() == 0) ? "closed" : "open";
  doc["water_status"] = (water_level < WATER_LEVEL_THRESHOLD) ? "low" : "sufficient";
  doc["light_status"] = (ldr >= LDR_THRESHOLD) ? "bright" : "dim";
  doc["temp_status"] = (temp >= TEMP_THRESHOLD) ? "hot" : "normal";
  
  // Info sistem
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["ip_address"] = WiFi.localIP().toString();
  doc["uptime"] = millis();
  
  String json_string;
  serializeJson(doc, json_string);
  
  int http_code = http.POST(json_string);
  
  if (http_code > 0) {
    String response = http.getString();
    
    if (http_code == 200) {
      Serial.println("✅ Data berhasil dikirim ke API");
      api_error_count = 0;  // Reset error count
    } else {
      Serial.print("⚠️ HTTP Error: ");
      Serial.println(http_code);
      Serial.println(response);
      api_error_count++;
    }
  } else {
    Serial.print("❌ Connection Error: ");
    Serial.println(http.errorToString(http_code));
    api_error_count++;
  }
  
  http.end();
}

void controlServo(float temp, int ldr_value) {
  static int last_servo_position = 90;
  int new_position;
  
  if (temp >= TEMP_THRESHOLD && ldr_value >= LDR_THRESHOLD) {
    new_position = 0;  // Tutup tirai
    if (last_servo_position != 0) {
      Serial.println("🔒 [Aksi] Tirai ditutup (Suhu Panas + Cahaya Terang)");
    }
  } else {
    new_position = 90; // Buka tirai
    if (last_servo_position != 90) {
      Serial.println("🔓 [Aksi] Tirai dibuka");
    }
  }
  
  if (new_position != last_servo_position) {
    servo.write(new_position);
    last_servo_position = new_position;
  }
}

float read_pH() {
  int pH_raw = analogRead(PH_PIN);
  float voltage = pH_raw * (3.3 / 4095.0);
  float pH_value = 7.0 - ((voltage - pH_offset) / 0.18);
  
  // Batasi nilai pH dalam range yang wajar
  if (pH_value < 0) pH_value = 0;
  if (pH_value > 14) pH_value = 14;
  
  return pH_value;
}

void printSensorData(float temp, float hum, float pH, int ldr, int water_level) {
  Serial.println("\n🌱 === DATA SENSOR TERRAPONIX ===");
  Serial.print("🌡️  Suhu: "); Serial.print(temp); Serial.println(" °C");
  Serial.print("💧 Kelembapan: "); Serial.print(hum); Serial.println(" %");
  Serial.print("⚗️  pH Air: "); Serial.print(pH, 2); Serial.println(" (0-14)");
  Serial.print("☀️  Cahaya (LDR): "); Serial.println(ldr);
  
  // Water Level Information
  Serial.print("🚰 Level Air: ");
  if (water_level < WATER_LEVEL_THRESHOLD) {
    Serial.print("RENDAH ⚠️");
  } else {
    Serial.print("CUKUP ✅");
  }
  Serial.print(" ("); Serial.print(water_level); Serial.println(")");
  
  // Status sistem
  Serial.print("🎚️  Status Tirai: ");
  Serial.println(servo.read() == 0 ? "Tertutup 🔒" : "Terbuka 🔓");
  
  Serial.print("📶 Status WiFi: ");
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Terhubung ✅ (");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm)");
    Serial.print("📍 IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Terputus ❌");
  }
  
  Serial.print("🔗 API Status: ");
  if (sensor_registered) {
    Serial.print("Terdaftar ✅");
  } else {
    Serial.print("Belum terdaftar ⚠️");
  }
  
  if (api_error_count > 0) {
    Serial.print(" (Errors: ");
    Serial.print(api_error_count);
    Serial.print(")");
  }
  Serial.println();
  
  Serial.print("⏱️  Uptime: ");
  Serial.print(millis() / 1000);
  Serial.println(" detik");
  
  Serial.println("================================\n");
}