#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server configuration
const char* serverURL = "http://192.168.1.100:5000/api/sensor-data"; // Change to your laptop's IP

// Sensor pins
#define DHT_PIN 4
#define DHT_TYPE DHT22
#define PH_PIN A0
#define TDS_PIN A1
#define LDR_PIN A2
#define CO2_PIN A3
#define SOIL_MOISTURE_PIN A4
#define WATER_LEVEL_PIN A5
#define BATTERY_PIN A6

// Control pins
#define PUMP_PIN 2
#define FAN_PIN 3
#define CURTAIN_PIN 5

// Solar monitoring pins
#define SOLAR_VOLTAGE_PIN A7
#define SOLAR_CURRENT_PIN A8

// Initialize DHT sensor
DHT dht(DHT_PIN, DHT_TYPE);

// Variables
unsigned long lastSensorRead = 0;
unsigned long lastDataSend = 0;
const unsigned long SENSOR_INTERVAL = 5000;  // Read sensors every 5 seconds
const unsigned long SEND_INTERVAL = 30000;   // Send data every 30 seconds

struct SensorData {
  float temperature;
  float humidity;
  float ph;
  float tds;
  float light_intensity;
  float co2;
  float soil_moisture;
  float water_level;
  float battery_level;
  float solar_power;
};

SensorData currentData;

void setup() {
  Serial.begin(115200);
  
  // Initialize sensors
  dht.begin();
  
  // Initialize control pins
  pinMode(PUMP_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);
  pinMode(CURTAIN_PIN, OUTPUT);
  
  // Set initial states
  digitalWrite(PUMP_PIN, LOW);
  digitalWrite(FAN_PIN, LOW);
  digitalWrite(CURTAIN_PIN, LOW);
  
  // Connect to WiFi
  connectToWiFi();
  
  Serial.println("🌱 Terraponix ESP32 System Initialized");
  Serial.println("📡 Starting sensor monitoring...");
}

void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Reconnecting...");
    connectToWiFi();
  }
  
  // Read sensors at specified interval
  if (millis() - lastSensorRead >= SENSOR_INTERVAL) {
    readSensors();
    lastSensorRead = millis();
  }
  
  // Send data at specified interval
  if (millis() - lastDataSend >= SEND_INTERVAL) {
    sendSensorData();
    lastDataSend = millis();
  }
  
  // Check for incoming commands
  checkForCommands();
  
  delay(100);
}

void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("✅ WiFi Connected! IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("❌ WiFi connection failed!");
  }
}

void readSensors() {
  // Read DHT22 (Temperature & Humidity)
  currentData.temperature = dht.readTemperature();
  currentData.humidity = dht.readHumidity();
  
  // Check if DHT readings are valid
  if (isnan(currentData.temperature) || isnan(currentData.humidity)) {
    Serial.println("⚠️ Failed to read from DHT sensor!");
    currentData.temperature = 25.0; // Default value
    currentData.humidity = 60.0;    // Default value
  }
  
  // Read pH sensor (analog)
  int phRaw = analogRead(PH_PIN);
  currentData.ph = map(phRaw, 0, 4095, 0, 14) / 10.0; // Convert to pH scale
  
  // Read TDS sensor (analog)
  int tdsRaw = analogRead(TDS_PIN);
  currentData.tds = map(tdsRaw, 0, 4095, 0, 2000); // Convert to ppm
  
  // Read LDR (Light sensor)
  int ldrRaw = analogRead(LDR_PIN);
  currentData.light_intensity = map(ldrRaw, 0, 4095, 0, 100); // Convert to percentage
  
  // Read CO2 sensor (analog)
  int co2Raw = analogRead(CO2_PIN);
  currentData.co2 = map(co2Raw, 0, 4095, 300, 2000); // Convert to ppm
  
  // Read soil moisture sensor
  int soilRaw = analogRead(SOIL_MOISTURE_PIN);
  currentData.soil_moisture = map(soilRaw, 0, 4095, 100, 0); // Inverted: wet = high value
  
  // Read water level sensor
  int waterRaw = analogRead(WATER_LEVEL_PIN);
  currentData.water_level = map(waterRaw, 0, 4095, 0, 100); // Convert to percentage
  
  // Read battery level
  int batteryRaw = analogRead(BATTERY_PIN);
  currentData.battery_level = map(batteryRaw, 0, 4095, 0, 100); // Convert to percentage
  
  // Calculate solar power
  int solarVoltageRaw = analogRead(SOLAR_VOLTAGE_PIN);
  int solarCurrentRaw = analogRead(SOLAR_CURRENT_PIN);
  float voltage = (solarVoltageRaw / 4095.0) * 3.3 * 4; // Assuming voltage divider
  float current = (solarCurrentRaw / 4095.0) * 3.3; // Assuming current sensor
  currentData.solar_power = voltage * current; // Power = V * I
  
  // Print sensor readings to Serial Monitor
  Serial.println("📊 Sensor Readings:");
  Serial.printf("   🌡️  Temperature: %.1f°C\n", currentData.temperature);
  Serial.printf("   💧  Humidity: %.1f%%\n", currentData.humidity);
  Serial.printf("   🧪  pH: %.1f\n", currentData.ph);
  Serial.printf("   📈  TDS: %.0f ppm\n", currentData.tds);
  Serial.printf("   ☀️  Light: %.0f%%\n", currentData.light_intensity);
  Serial.printf("   💨  CO2: %.0f ppm\n", currentData.co2);
  Serial.printf("   🌱  Soil Moisture: %.0f%%\n", currentData.soil_moisture);
  Serial.printf("   🚰  Water Level: %.0f%%\n", currentData.water_level);
  Serial.printf("   🔋  Battery: %.0f%%\n", currentData.battery_level);
  Serial.printf("   ⚡  Solar Power: %.1fW\n", currentData.solar_power);
  Serial.println();
}

void sendSensorData() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi not connected. Cannot send data.");
    return;
  }
  
  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  DynamicJsonDocument doc(1024);
  doc["temperature"] = currentData.temperature;
  doc["humidity"] = currentData.humidity;
  doc["ph"] = currentData.ph;
  doc["tds"] = currentData.tds;
  doc["light_intensity"] = currentData.light_intensity;
  doc["co2"] = currentData.co2;
  doc["soil_moisture"] = currentData.soil_moisture;
  doc["water_level"] = currentData.water_level;
  doc["battery_level"] = currentData.battery_level;
  doc["solar_power"] = currentData.solar_power;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("📡 Sending data to server...");
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

void checkForCommands() {
  // This function would check for incoming commands from the server
  // For now, we'll implement basic automatic control based on sensor readings
  
  // Automatic pump control based on soil moisture
  if (currentData.soil_moisture < 30) {
    digitalWrite(PUMP_PIN, HIGH);
    Serial.println("💧 Auto: Pump ON - Low soil moisture");
  } else if (currentData.soil_moisture > 80) {
    digitalWrite(PUMP_PIN, LOW);
    Serial.println("💧 Auto: Pump OFF - High soil moisture");
  }
  
  // Automatic fan control based on temperature
  if (currentData.temperature > 30) {
    digitalWrite(FAN_PIN, HIGH);
    Serial.println("🌀 Auto: Fan ON - High temperature");
  } else if (currentData.temperature < 25) {
    digitalWrite(FAN_PIN, LOW);
    Serial.println("🌀 Auto: Fan OFF - Normal temperature");
  }
  
  // Automatic curtain control based on light intensity
  if (currentData.light_intensity > 80) {
    digitalWrite(CURTAIN_PIN, HIGH);
    Serial.println("🏠 Auto: Curtain CLOSED - High light intensity");
  } else if (currentData.light_intensity < 40) {
    digitalWrite(CURTAIN_PIN, LOW);
    Serial.println("🏠 Auto: Curtain OPEN - Low light intensity");
  }
}

// Helper function to map float values
float mapFloat(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

// Function to handle manual control commands (for future HTTP endpoint)
void handleControlCommand(String command, bool value) {
  if (command == "pump") {
    digitalWrite(PUMP_PIN, value ? HIGH : LOW);
    Serial.printf("🎛️ Manual: Pump %s\n", value ? "ON" : "OFF");
  } else if (command == "fan") {
    digitalWrite(FAN_PIN, value ? HIGH : LOW);
    Serial.printf("🎛️ Manual: Fan %s\n", value ? "ON" : "OFF");
  } else if (command == "curtain") {
    digitalWrite(CURTAIN_PIN, value ? HIGH : LOW);
    Serial.printf("🎛️ Manual: Curtain %s\n", value ? "CLOSED" : "OPEN");
  } else if (command == "reset_system") {
    Serial.println("🔄 System Reset Requested");
    ESP.restart();
  } else if (command == "emergency_stop") {
    Serial.println("🛑 Emergency Stop Activated");
    digitalWrite(PUMP_PIN, LOW);
    digitalWrite(FAN_PIN, LOW);
    digitalWrite(CURTAIN_PIN, LOW);
  }
}