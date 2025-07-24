#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <ESP32Servo.h>

// WiFi credentials
const char* ssid = "Xiaomi 14T Pro";
const char* password = "jougen92";

// Server configuration - GANTI DENGAN IP SERVER ANDA
const char* serverURL = "http://192.168.106.38:5000/api/sensor-data";

// Pin Definitions
#define DHTPIN 25         // Pin DHT11
#define DHTTYPE DHT11
#define PH_PIN 34         // Pin pH sensor (Analog)
#define LDR_PIN 35        // Pin LDR (Analog)
#define SERVO_PIN 13      // Pin Servo (Tirai)
#define WATER_LEVEL_PIN 32 // Pin Water Level Sensor (Analog)
#define PUMP_PIN 14       // Pin Pompa Air
#define FAN_PIN 12        // Pin Kipas

// Kalibrasi
float pH_offset = 0.0;
const float TEMP_THRESHOLD = 29.0;  // Suhu panas (°C)
const int LDR_THRESHOLD = 2200;     // Cahaya terang (LDR ≥2200)
const int WATER_LEVEL_THRESHOLD = 1500; // Threshold level air
const int SOIL_MOISTURE_THRESHOLD = 30; // Kelembaban tanah minimal

DHT dht(DHTPIN, DHTTYPE);
Servo servo;

// Variables
unsigned long lastSensorRead = 0;
unsigned long lastDataSend = 0;
const unsigned long SENSOR_INTERVAL = 5000;  // Baca sensor setiap 5 detik
const unsigned long SEND_INTERVAL = 30000;   // Kirim data setiap 30 detik

struct SensorData {
  float temperature;
  float humidity;
  float ph;
  int light_intensity;
  int water_level;
  String water_status;
  String curtain_status;
  String wifi_status;
  String ip_address;
};

SensorData currentData;

void setup() {
  Serial.begin(115200);
  
  // Inisialisasi sensor dan aktuator
  dht.begin();
  servo.attach(SERVO_PIN);
  servo.write(90);  // Posisi awal servo (terbuka)
  pinMode(PUMP_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, LOW);
  digitalWrite(FAN_PIN, LOW);
  
  // Mulai koneksi WiFi
  connectToWiFi();
  
  Serial.println("\nSistem TERRAPONIX Started!");
  Serial.println("==========================");
}

void loop() {
  // Periksa status WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Koneksi WiFi terputus! Mencoba menghubungkan kembali...");
    connectToWiFi();
    delay(5000);
    return;
  }

  // Baca sensor pada interval yang ditentukan
  if (millis() - lastSensorRead >= SENSOR_INTERVAL) {
    readSensors();
    lastSensorRead = millis();
  }
  
  // Kirim data ke server pada interval yang ditentukan
  if (millis() - lastDataSend >= SEND_INTERVAL && WiFi.status() == WL_CONNECTED) {
    sendSensorData();
    lastDataSend = millis();
  }
  
  // Kontrol otomatis sistem
  automaticControl();
  
  delay(100);
}

void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Menghubungkan ke WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Terhubung!");
    Serial.print("Alamat IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nGagal terhubung ke WiFi!");
  }
}

void readSensors() {
  // Baca DHT (Suhu & Kelembapan)
  currentData.temperature = dht.readTemperature();
  currentData.humidity = dht.readHumidity();
  
  // Validasi pembacaan DHT
  if (isnan(currentData.temperature) || isnan(currentData.humidity)) {
    Serial.println("⚠️ Gagal membaca DHT sensor!");
    currentData.temperature = 25.0;
    currentData.humidity = 60.0;
  }
  
  // Baca sensor pH
  currentData.ph = read_pH();
  
  // Baca intensitas cahaya
  currentData.light_intensity = analogRead(LDR_PIN);
  
  // Baca level air
  int waterRaw = analogRead(WATER_LEVEL_PIN);
  currentData.water_level = waterRaw;
  currentData.water_status = (waterRaw < WATER_LEVEL_THRESHOLD) ? "RENDAH" : "CUKUP";
  
  // Status tirai
  currentData.curtain_status = (servo.read() == 0) ? "Tertutup" : "Terbuka";
  
  // Status WiFi
  currentData.wifi_status = (WiFi.status() == WL_CONNECTED) ? "Terhubung" : "Terputus";
  currentData.ip_address = WiFi.localIP().toString();
  
  // Tampilkan data di Serial Monitor
  printSensorData();
}

float read_pH() {
  int pH_raw = analogRead(PH_PIN);
  float voltage = pH_raw * (3.3 / 4095.0);
  return 7.0 - ((voltage - pH_offset) / 0.18);  // Rumus kalibrasi pH
}

void printSensorData() {
  Serial.println("=== DATA SENSOR ===");
  Serial.printf("Suhu: %.1f °C\n", currentData.temperature);
  Serial.printf("Kelembapan: %.1f %%\n", currentData.humidity);
  Serial.printf("pH Air: %.2f (0-14)\n", currentData.ph);
  Serial.printf("Cahaya (LDR): %d\n", currentData.light_intensity);
  Serial.printf("Level Air: %s\n", currentData.water_status.c_str());
  Serial.printf("Nilai Tinggi Air Sensor: %d\n", currentData.water_level);
  Serial.printf("Status Tirai: %s\n", currentData.curtain_status.c_str());
  Serial.printf("Status WiFi: %s\n", currentData.wifi_status.c_str());
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("Alamat IP: %s\n", currentData.ip_address.c_str());
  }
  Serial.println("===================");
}

void sendSensorData() {
  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");
  
  // Buat payload JSON
  DynamicJsonDocument doc(512);
  doc["temperature"] = currentData.temperature;
  doc["humidity"] = currentData.humidity;
  doc["ph"] = currentData.ph;
  doc["light_intensity"] = currentData.light_intensity;
  doc["water_level"] = currentData.water_level;
  doc["water_status"] = currentData.water_status;
  doc["curtain_status"] = currentData.curtain_status;
  doc["wifi_status"] = currentData.wifi_status;
  doc["ip_address"] = currentData.ip_address;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("📡 Mengirim data ke server...");
  Serial.println("JSON: " + jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("✅ HTTP Response: %d\n", httpResponseCode);
    Serial.println("Response: " + response);
  } else {
    Serial.printf("❌ HTTP Error: %d\n", httpResponseCode);
  }
  
  http.end();
}

void automaticControl() {
  // Kontrol tirai otomatis
  if (currentData.temperature >= TEMP_THRESHOLD && currentData.light_intensity >= LDR_THRESHOLD) {
    servo.write(0);  // Tutup tirai
    Serial.println("[Aksi] Tirai ditutup (Suhu Panas + Cahaya Terang)");
    currentData.curtain_status = "Tertutup";
  } else {
    servo.write(90); // Buka tirai
    currentData.curtain_status = "Terbuka";
  }
  
  // Kontrol pompa air otomatis
  if (currentData.water_level < WATER_LEVEL_THRESHOLD) {
    digitalWrite(PUMP_PIN, HIGH);
    Serial.println("[Aksi] Pompa ON - Level air rendah");
  } else {
    digitalWrite(PUMP_PIN, LOW);
  }
  
  // Kontrol kipas otomatis
  if (currentData.temperature > TEMP_THRESHOLD) {
    digitalWrite(FAN_PIN, HIGH);
    Serial.println("[Aksi] Kipas ON - Suhu tinggi");
  } else {
    digitalWrite(FAN_PIN, LOW);
  }
}