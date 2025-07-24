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

DHT dht(DHTPIN, DHTTYPE);
Servo servo;

// Kalibrasi
float pH_offset = 0.0;
const float TEMP_THRESHOLD = 29.0;
const int LDR_THRESHOLD = 2200;
const int WATER_LEVEL_THRESHOLD = 1500;

// Status tracking
bool sensors_registered = false;
unsigned long last_api_call = 0;
const unsigned long API_INTERVAL = 15000;  // Kirim data setiap 15 detik
int api_error_count = 0;

void setup() {
  Serial.begin(115200);
  
  // Koneksi WiFi
  connectToWiFi();
  
  // Inisialisasi hardware
  dht.begin();
  servo.attach(SERVO_PIN);
  servo.write(90);
  pinMode(WATER_LEVEL_PIN, INPUT);
  
  Serial.println("\n🌱 ESP32 TERRAPONIX - API Integration");
  Serial.println("====================================");
  Serial.print("📡 API Server: ");
  Serial.println(api_server);
  Serial.println("====================================");
  
  // Registrasi semua sensor ke API
  if (WiFi.status() == WL_CONNECTED) {
    registerAllSensors();
  }
}

void loop() {
  // Cek koneksi WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi terputus! Reconnecting...");
    connectToWiFi();
    return;
  }

  // Baca semua sensor
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  int ldr_value = analogRead(LDR_PIN);
  float pH_value = read_pH();
  int water_level = analogRead(WATER_LEVEL_PIN);

  // Validasi DHT
  if (isnan(temp) || isnan(hum)) {
    Serial.println("❌ DHT read error!");
    temp = 0.0;
    hum = 0.0;
  }

  // Kontrol servo
  controlServo(temp, ldr_value);

  // Tampilkan data
  printSensorData(temp, hum, pH_value, ldr_value, water_level);

  // Kirim data ke API (setiap interval)
  if (millis() - last_api_call >= API_INTERVAL) {
    if (WiFi.status() == WL_CONNECTED) {
      sendAllSensorData(temp, hum, pH_value, ldr_value, water_level);
    }
    last_api_call = millis();
  }

  delay(3000);
}

void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("📶 Connecting to WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected!");
    Serial.print("📍 IP: ");
    Serial.println(WiFi.localIP());
    api_error_count = 0;
  } else {
    Serial.println("\n❌ WiFi Failed!");
  }
}

void registerAllSensors() {
  Serial.println("📋 Registering sensors...");
  
  // Registrasi 5 sensor terpisah sesuai format API
  registerSensor("ESP32_TEMP_001", "temperature", "ESP32 Temperature Sensor");
  delay(1000);
  registerSensor("ESP32_HUM_001", "humidity", "ESP32 Humidity Sensor");
  delay(1000);
  registerSensor("ESP32_PH_001", "ph", "ESP32 pH Sensor");
  delay(1000);
  registerSensor("ESP32_LIGHT_001", "light", "ESP32 Light Sensor");
  delay(1000);
  registerSensor("ESP32_WATER_001", "water_level", "ESP32 Water Level Sensor");
  
  sensors_registered = true;
  Serial.println("✅ All sensors registered!");
}

bool registerSensor(const char* sensor_id, const char* sensor_type, const char* sensor_name) {
  HTTPClient http;
  http.begin(String(api_server) + "/api/sensor/register");
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<200> doc;
  doc["sensor_id"] = sensor_id;
  doc["sensor_type"] = sensor_type;
  doc["sensor_name"] = sensor_name;
  
  String json_string;
  serializeJson(doc, json_string);
  
  int http_code = http.POST(json_string);
  bool success = false;
  
  if (http_code == 200) {
    Serial.print("✅ ");
    Serial.print(sensor_id);
    Serial.println(" registered");
    success = true;
  } else {
    Serial.print("❌ ");
    Serial.print(sensor_id);
    Serial.print(" failed: ");
    Serial.println(http_code);
  }
  
  http.end();
  return success;
}

void sendAllSensorData(float temp, float hum, float pH, int ldr, int water_level) {
  if (!sensors_registered) {
    registerAllSensors();
  }
  
  if (api_error_count >= 3) {
    Serial.println("⚠️ Too many API errors, skipping...");
    return;
  }
  
  Serial.println("📤 Sending sensor data...");
  
  // Kirim data temperature
  sendSensorData("ESP32_TEMP_001", "temperature", temp, "°C");
  delay(500);
  
  // Kirim data humidity
  sendSensorData("ESP32_HUM_001", "humidity", hum, "%");
  delay(500);
  
  // Kirim data pH
  sendSensorData("ESP32_PH_001", "ph", pH, "pH");
  delay(500);
  
  // Kirim data light
  sendSensorData("ESP32_LIGHT_001", "light", ldr, "lux");
  delay(500);
  
  // Kirim data water level
  sendSensorData("ESP32_WATER_001", "water_level", water_level, "level");
  
  Serial.println("📡 All data sent!");
}

bool sendSensorData(const char* sensor_id, const char* sensor_type, float value, const char* unit) {
  HTTPClient http;
  http.begin(String(api_server) + "/api/sensor/data");
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);
  
  StaticJsonDocument<200> doc;
  doc["sensor_id"] = sensor_id;
  doc["sensor_type"] = sensor_type;
  doc["value"] = value;
  doc["unit"] = unit;
  
  String json_string;
  serializeJson(doc, json_string);
  
  int http_code = http.POST(json_string);
  bool success = false;
  
  if (http_code == 200) {
    success = true;
    api_error_count = 0;
  } else {
    Serial.print("❌ Error sending ");
    Serial.print(sensor_id);
    Serial.print(": ");
    Serial.println(http_code);
    api_error_count++;
  }
  
  http.end();
  return success;
}

void controlServo(float temp, int ldr_value) {
  static int last_position = 90;
  int new_position;
  
  if (temp >= TEMP_THRESHOLD && ldr_value >= LDR_THRESHOLD) {
    new_position = 0;  // Tutup tirai
    if (last_position != 0) {
      Serial.println("🔒 Curtain CLOSED (Hot + Bright)");
    }
  } else {
    new_position = 90; // Buka tirai
    if (last_position != 90) {
      Serial.println("🔓 Curtain OPENED");
    }
  }
  
  if (new_position != last_position) {
    servo.write(new_position);
    last_position = new_position;
  }
}

float read_pH() {
  int raw = analogRead(PH_PIN);
  float voltage = raw * (3.3 / 4095.0);
  float pH_value = 7.0 - ((voltage - pH_offset) / 0.18);
  
  // Clamp pH value
  if (pH_value < 0) pH_value = 0;
  if (pH_value > 14) pH_value = 14;
  
  return pH_value;
}

void printSensorData(float temp, float hum, float pH, int ldr, int water_level) {
  Serial.println("\n🌱 === TERRAPONIX SENSOR DATA ===");
  Serial.print("🌡️  Temperature: "); Serial.print(temp); Serial.println(" °C");
  Serial.print("💧 Humidity: "); Serial.print(hum); Serial.println(" %");
  Serial.print("⚗️  pH: "); Serial.print(pH, 2);
  Serial.print("☀️  Light: "); Serial.println(ldr);
  Serial.print("🚰 Water Level: "); Serial.print(water_level);
  
  if (water_level < WATER_LEVEL_THRESHOLD) {
    Serial.println(" (LOW ⚠️)");
  } else {
    Serial.println(" (OK ✅)");
  }
  
  Serial.print("🎚️  Curtain: ");
  Serial.println(servo.read() == 0 ? "CLOSED 🔒" : "OPEN 🔓");
  
  Serial.print("📶 WiFi: ");
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("OK (");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm)");
  } else {
    Serial.println("DISCONNECTED ❌");
  }
  
  Serial.print("🔗 API: ");
  if (sensors_registered) {
    Serial.print("REGISTERED ✅");
  } else {
    Serial.print("NOT REGISTERED ⚠️");
  }
  
  if (api_error_count > 0) {
    Serial.print(" (Errors: ");
    Serial.print(api_error_count);
    Serial.print(")");
  }
  Serial.println();
  
  Serial.print("⏱️  Uptime: ");
  Serial.print(millis() / 1000);
  Serial.println(" sec");
  Serial.println("==============================\n");
}