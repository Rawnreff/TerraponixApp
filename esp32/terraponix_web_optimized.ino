#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <ESP32Servo.h>
#include <SPIFFS.h>
#include <ESPmDNS.h>

// WiFi credentials - GANTI SESUAI WIFI ANDA
const char* ssid = "Xiaomi 14T Pro";
const char* password = "jougen92";

// Device configuration
const String DEVICE_NAME = "Terraponix-Greenhouse";
const String DEVICE_VERSION = "v2.0";

// Pin Definitions
#define DHTPIN 25         // Pin DHT11
#define DHTTYPE DHT11
#define PH_PIN 34         // Pin pH sensor (Analog)
#define LDR_PIN 35        // Pin LDR (Analog)
#define SERVO_PIN 13      // Pin Servo (Curtain)
#define WATER_LEVEL_PIN 32 // Pin Water Level Sensor (Analog)
#define PUMP_PIN 14       // Pin Water Pump
#define FAN_PIN 12        // Pin Fan
#define SOIL_MOISTURE_PIN 33 // Pin Soil Moisture Sensor (Analog)
#define LED_STATUS_PIN 2  // Built-in LED for status indication

// Thresholds and Calibration
float pH_offset = 0.0;
const float TEMP_THRESHOLD_HIGH = 29.0;  // High temperature threshold (°C)
const float TEMP_THRESHOLD_LOW = 25.0;   // Low temperature threshold (°C)
const int LDR_THRESHOLD = 2200;          // Light intensity threshold
const int WATER_LEVEL_THRESHOLD = 1500;  // Water level threshold
const int SOIL_MOISTURE_THRESHOLD_LOW = 30;  // Minimum soil moisture %
const int SOIL_MOISTURE_THRESHOLD_HIGH = 80; // Maximum soil moisture %

// Initialize sensors and actuators
DHT dht(DHTPIN, DHTTYPE);
Servo curtainServo;
WebServer webServer(80); // Web server on port 80

// Timing variables
unsigned long lastSensorRead = 0;
unsigned long lastStatusBlink = 0;
unsigned long lastAutoControl = 0;
const unsigned long SENSOR_INTERVAL = 3000;   // Read sensors every 3 seconds
const unsigned long STATUS_BLINK_INTERVAL = 1000; // Status LED blink interval
const unsigned long AUTO_CONTROL_INTERVAL = 5000; // Auto control check interval

// Control states
bool manualMode = false;
bool pumpState = false;
bool fanState = false;
int curtainPosition = 90; // 0 = closed, 90 = open
bool systemEnabled = true;

// Data logging
const int MAX_LOG_ENTRIES = 100;
int logIndex = 0;

struct GreenhouseData {
  float temperature;
  float humidity;
  float ph;
  int light_intensity;
  int water_level;
  int soil_moisture;
  String water_status;
  String curtain_status;
  String pump_status;
  String fan_status;
  String wifi_status;
  String ip_address;
  String mode;
  String system_status;
  unsigned long timestamp;
  int wifi_signal;
};

struct LogEntry {
  unsigned long timestamp;
  float temperature;
  float humidity;
  float ph;
  int soil_moisture;
  String actions;
};

GreenhouseData currentData;
LogEntry dataLog[MAX_LOG_ENTRIES];

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n🌱 TERRAPONIX Greenhouse Web System");
  Serial.println("=====================================");
  Serial.println("Version: " + DEVICE_VERSION);
  Serial.println("Device: " + DEVICE_NAME);
  Serial.println("=====================================");
  
  // Initialize SPIFFS for web files storage
  if (!SPIFFS.begin(true)) {
    Serial.println("⚠️ SPIFFS Mount Failed");
  } else {
    Serial.println("✅ SPIFFS Mounted Successfully");
  }
  
  // Initialize pins
  pinMode(LED_STATUS_PIN, OUTPUT);
  pinMode(PUMP_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);
  
  // Set initial states
  digitalWrite(PUMP_PIN, LOW);
  digitalWrite(FAN_PIN, LOW);
  digitalWrite(LED_STATUS_PIN, HIGH); // Turn on status LED
  
  // Initialize sensors and actuators
  dht.begin();
  curtainServo.attach(SERVO_PIN);
  curtainServo.write(90);  // Initial position (open)
  
  Serial.println("🔧 Hardware initialized");
  
  // Connect to WiFi
  connectToWiFi();
  
  // Setup mDNS for easy access (terraponix.local)
  if (MDNS.begin("terraponix")) {
    Serial.println("🌐 mDNS responder started: http://terraponix.local");
    MDNS.addService("http", "tcp", 80);
  }
  
  // Setup web server
  setupWebServer();
  
  // Initialize data logging
  initializeDataLog();
  
  Serial.println("✅ System fully initialized!");
  Serial.println("🌐 Web Interface: http://" + WiFi.localIP().toString());
  Serial.println("🌐 Local Domain: http://terraponix.local");
  Serial.println("📊 Starting monitoring...");
  Serial.println("=====================================\n");
}

void loop() {
  // Handle web server requests
  webServer.handleClient();
  
  // Handle mDNS
  MDNS.update();
  
  // Status LED blinking to show system is alive
  if (millis() - lastStatusBlink >= STATUS_BLINK_INTERVAL) {
    digitalWrite(LED_STATUS_PIN, !digitalRead(LED_STATUS_PIN));
    lastStatusBlink = millis();
  }
  
  // Check WiFi connection and reconnect if needed
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("📡 WiFi disconnected! Reconnecting...");
    digitalWrite(LED_STATUS_PIN, LOW); // Turn off LED when disconnected
    connectToWiFi();
    return;
  }
  
  // Read sensors at specified interval
  if (millis() - lastSensorRead >= SENSOR_INTERVAL) {
    readSensors();
    logData();
    lastSensorRead = millis();
  }
  
  // Automatic control system (only if enabled and not in manual mode)
  if (systemEnabled && !manualMode && (millis() - lastAutoControl >= AUTO_CONTROL_INTERVAL)) {
    automaticControl();
    lastAutoControl = millis();
  }
  
  delay(50); // Small delay for stability
}

void connectToWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("🔗 Connecting to WiFi: " + String(ssid));
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
    
    // Blink LED faster while connecting
    digitalWrite(LED_STATUS_PIN, !digitalRead(LED_STATUS_PIN));
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected Successfully!");
    Serial.println("📍 IP Address: " + WiFi.localIP().toString());
    Serial.println("📶 Signal Strength: " + String(WiFi.RSSI()) + " dBm");
    Serial.println("🔒 MAC Address: " + WiFi.macAddress());
    digitalWrite(LED_STATUS_PIN, HIGH); // Keep LED on when connected
  } else {
    Serial.println("\n❌ WiFi Connection Failed!");
    Serial.println("⚠️ System will continue in offline mode");
  }
}

void setupWebServer() {
  // CORS headers for all responses
  webServer.onNotFound([]() {
    webServer.sendHeader("Access-Control-Allow-Origin", "*");
    webServer.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    webServer.sendHeader("Access-Control-Allow-Headers", "Content-Type");
    webServer.send(404, "text/plain", "Not Found");
  });
  
  // Main dashboard
  webServer.on("/", HTTP_GET, handleRoot);
  
  // API endpoints
  webServer.on("/api/data", HTTP_GET, handleApiData);
  webServer.on("/api/control", HTTP_POST, handleApiControl);
  webServer.on("/api/status", HTTP_GET, handleApiStatus);
  webServer.on("/api/logs", HTTP_GET, handleApiLogs);
  webServer.on("/api/config", HTTP_GET, handleApiConfig);
  webServer.on("/api/config", HTTP_POST, handleApiConfigUpdate);
  
  // Control endpoints (backward compatibility)
  webServer.on("/control/pump", HTTP_POST, handlePumpControl);
  webServer.on("/control/fan", HTTP_POST, handleFanControl);
  webServer.on("/control/curtain", HTTP_POST, handleCurtainControl);
  webServer.on("/control/mode", HTTP_POST, handleModeControl);
  webServer.on("/control/system", HTTP_POST, handleSystemControl);
  
  // Data endpoints
  webServer.on("/data", HTTP_GET, handleDataRequest);
  webServer.on("/logs", HTTP_GET, handleLogsPage);
  
  // Enable CORS for all routes
  webServer.enableCORS(true);
  
  webServer.begin();
  Serial.println("🌐 Web server started successfully");
}

void readSensors() {
  // Read DHT11 (Temperature & Humidity)
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  
  // Validate DHT readings with retry
  if (isnan(temp) || isnan(hum)) {
    delay(100);
    temp = dht.readTemperature();
    hum = dht.readHumidity();
    
    if (isnan(temp) || isnan(hum)) {
      Serial.println("⚠️ DHT sensor reading failed!");
      currentData.temperature = (currentData.temperature > 0) ? currentData.temperature : 25.0;
      currentData.humidity = (currentData.humidity > 0) ? currentData.humidity : 60.0;
    } else {
      currentData.temperature = temp;
      currentData.humidity = hum;
    }
  } else {
    currentData.temperature = temp;
    currentData.humidity = hum;
  }
  
  // Read pH sensor with averaging
  float ph_sum = 0;
  for (int i = 0; i < 5; i++) {
    ph_sum += readPH();
    delay(10);
  }
  currentData.ph = ph_sum / 5.0;
  
  // Read light intensity
  currentData.light_intensity = analogRead(LDR_PIN);
  
  // Read water level
  int waterRaw = analogRead(WATER_LEVEL_PIN);
  currentData.water_level = waterRaw;
  currentData.water_status = (waterRaw < WATER_LEVEL_THRESHOLD) ? "LOW" : "OK";
  
  // Read soil moisture with calibration
  int soilRaw = analogRead(SOIL_MOISTURE_PIN);
  currentData.soil_moisture = map(constrain(soilRaw, 0, 4095), 0, 4095, 100, 0);
  
  // Update status strings
  currentData.curtain_status = (curtainPosition == 0) ? "CLOSED" : "OPEN";
  currentData.pump_status = pumpState ? "ON" : "OFF";
  currentData.fan_status = fanState ? "ON" : "OFF";
  currentData.wifi_status = (WiFi.status() == WL_CONNECTED) ? "CONNECTED" : "DISCONNECTED";
  currentData.ip_address = WiFi.localIP().toString();
  currentData.mode = manualMode ? "MANUAL" : "AUTO";
  currentData.system_status = systemEnabled ? "ENABLED" : "DISABLED";
  currentData.timestamp = millis();
  currentData.wifi_signal = WiFi.RSSI();
  
  // Print sensor data periodically
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint >= 15000) { // Print every 15 seconds
    printSensorData();
    lastPrint = millis();
  }
}

float readPH() {
  int pH_raw = analogRead(PH_PIN);
  float voltage = pH_raw * (3.3 / 4095.0);
  float ph_value = 7.0 - ((voltage - pH_offset) / 0.18);
  return constrain(ph_value, 0.0, 14.0);
}

void printSensorData() {
  Serial.println("📊 === GREENHOUSE SENSOR DATA ===");
  Serial.printf("🌡️  Temperature: %.1f°C\n", currentData.temperature);
  Serial.printf("💧  Humidity: %.1f%%\n", currentData.humidity);
  Serial.printf("🧪  pH Level: %.2f\n", currentData.ph);
  Serial.printf("☀️  Light: %d\n", currentData.light_intensity);
  Serial.printf("🚰  Water: %s (%d)\n", currentData.water_status.c_str(), currentData.water_level);
  Serial.printf("🌱  Soil: %d%%\n", currentData.soil_moisture);
  Serial.printf("🚿  Pump: %s | 🌀 Fan: %s | 🏠 Curtain: %s\n", 
                currentData.pump_status.c_str(), 
                currentData.fan_status.c_str(), 
                currentData.curtain_status.c_str());
  Serial.printf("🎛️  Mode: %s | System: %s\n", currentData.mode.c_str(), currentData.system_status.c_str());
  Serial.printf("📡  WiFi: %s (%s) Signal: %d dBm\n", 
                currentData.wifi_status.c_str(), 
                currentData.ip_address.c_str(), 
                currentData.wifi_signal);
  Serial.println("================================\n");
}

void automaticControl() {
  String actions = "";
  
  // Automatic curtain control
  if (currentData.temperature >= TEMP_THRESHOLD_HIGH && currentData.light_intensity >= LDR_THRESHOLD) {
    if (curtainPosition != 0) {
      controlCurtain(true);
      actions += "Curtain closed (hot+bright); ";
      Serial.println("🏠 [AUTO] Curtain CLOSED - High temp + bright light");
    }
  } else if (currentData.temperature <= TEMP_THRESHOLD_LOW || currentData.light_intensity < LDR_THRESHOLD) {
    if (curtainPosition != 90) {
      controlCurtain(false);
      actions += "Curtain opened; ";
      Serial.println("🏠 [AUTO] Curtain OPENED - Normal conditions");
    }
  }
  
  // Automatic pump control
  if (currentData.soil_moisture < SOIL_MOISTURE_THRESHOLD_LOW) {
    if (!pumpState) {
      controlPump(true);
      actions += "Pump ON (dry soil); ";
      Serial.println("🚿 [AUTO] Pump ON - Low soil moisture");
    }
  } else if (currentData.soil_moisture > SOIL_MOISTURE_THRESHOLD_HIGH) {
    if (pumpState) {
      controlPump(false);
      actions += "Pump OFF (wet soil); ";
      Serial.println("🚿 [AUTO] Pump OFF - High soil moisture");
    }
  }
  
  // Automatic fan control
  if (currentData.temperature > TEMP_THRESHOLD_HIGH) {
    if (!fanState) {
      controlFan(true);
      actions += "Fan ON (hot); ";
      Serial.println("🌀 [AUTO] Fan ON - High temperature");
    }
  } else if (currentData.temperature < TEMP_THRESHOLD_LOW) {
    if (fanState) {
      controlFan(false);
      actions += "Fan OFF (cool); ";
      Serial.println("🌀 [AUTO] Fan OFF - Normal temperature");
    }
  }
  
  // Log actions if any
  if (actions.length() > 0) {
    logAction(actions);
  }
}

void controlPump(bool state) {
  pumpState = state;
  digitalWrite(PUMP_PIN, state ? HIGH : LOW);
  currentData.pump_status = state ? "ON" : "OFF";
  Serial.printf("🚿 Pump %s\n", state ? "ON" : "OFF");
}

void controlFan(bool state) {
  fanState = state;
  digitalWrite(FAN_PIN, state ? HIGH : LOW);
  currentData.fan_status = state ? "ON" : "OFF";
  Serial.printf("🌀 Fan %s\n", state ? "ON" : "OFF");
}

void controlCurtain(bool close) {
  curtainPosition = close ? 0 : 90;
  curtainServo.write(curtainPosition);
  currentData.curtain_status = close ? "CLOSED" : "OPEN";
  Serial.printf("🏠 Curtain %s\n", close ? "CLOSED" : "OPEN");
  delay(500);
}

void initializeDataLog() {
  for (int i = 0; i < MAX_LOG_ENTRIES; i++) {
    dataLog[i].timestamp = 0;
    dataLog[i].temperature = 0;
    dataLog[i].humidity = 0;
    dataLog[i].ph = 0;
    dataLog[i].soil_moisture = 0;
    dataLog[i].actions = "";
  }
  logIndex = 0;
}

void logData() {
  dataLog[logIndex].timestamp = millis();
  dataLog[logIndex].temperature = currentData.temperature;
  dataLog[logIndex].humidity = currentData.humidity;
  dataLog[logIndex].ph = currentData.ph;
  dataLog[logIndex].soil_moisture = currentData.soil_moisture;
  dataLog[logIndex].actions = "";
  
  logIndex = (logIndex + 1) % MAX_LOG_ENTRIES;
}

void logAction(String action) {
  if (logIndex > 0) {
    dataLog[logIndex - 1].actions = action;
  } else {
    dataLog[MAX_LOG_ENTRIES - 1].actions = action;
  }
}

// Web Server Handlers
void handleRoot() {
  String html = generateWebInterface();
  webServer.sendHeader("Cache-Control", "no-cache, no-store, must-revalidate");
  webServer.sendHeader("Pragma", "no-cache");
  webServer.sendHeader("Expires", "-1");
  webServer.send(200, "text/html", html);
}

void handleApiData() {
  DynamicJsonDocument doc(1024);
  doc["device_name"] = DEVICE_NAME;
  doc["version"] = DEVICE_VERSION;
  doc["timestamp"] = currentData.timestamp;
  doc["temperature"] = currentData.temperature;
  doc["humidity"] = currentData.humidity;
  doc["ph"] = currentData.ph;
  doc["light_intensity"] = currentData.light_intensity;
  doc["water_level"] = currentData.water_level;
  doc["water_status"] = currentData.water_status;
  doc["soil_moisture"] = currentData.soil_moisture;
  doc["pump_status"] = currentData.pump_status;
  doc["fan_status"] = currentData.fan_status;
  doc["curtain_status"] = currentData.curtain_status;
  doc["mode"] = currentData.mode;
  doc["system_status"] = currentData.system_status;
  doc["wifi_status"] = currentData.wifi_status;
  doc["wifi_signal"] = currentData.wifi_signal;
  doc["ip_address"] = currentData.ip_address;
  doc["uptime"] = millis();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  webServer.sendHeader("Access-Control-Allow-Origin", "*");
  webServer.send(200, "application/json", jsonString);
}

void handleApiControl() {
  if (webServer.hasArg("plain")) {
    DynamicJsonDocument doc(512);
    if (deserializeJson(doc, webServer.arg("plain")) == DeserializationError::Ok) {
      String device = doc["device"];
      String action = doc["action"];
      bool value = doc["value"];
      
      String response = "{\"status\":\"success\",\"message\":\"";
      
      if (device == "pump") {
        controlPump(value);
        response += "Pump " + String(value ? "ON" : "OFF");
      } else if (device == "fan") {
        controlFan(value);
        response += "Fan " + String(value ? "ON" : "OFF");
      } else if (device == "curtain") {
        controlCurtain(value);
        response += "Curtain " + String(value ? "CLOSED" : "OPEN");
      } else if (device == "mode") {
        manualMode = value;
        response += "Mode " + String(value ? "MANUAL" : "AUTO");
      } else if (device == "system") {
        systemEnabled = value;
        response += "System " + String(value ? "ENABLED" : "DISABLED");
      } else {
        response = "{\"status\":\"error\",\"message\":\"Unknown device";
      }
      
      response += "\"}";
      webServer.send(200, "application/json", response);
    } else {
      webServer.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Invalid JSON\"}");
    }
  } else {
    webServer.send(400, "application/json", "{\"status\":\"error\",\"message\":\"No data received\"}");
  }
}

void handleApiStatus() {
  DynamicJsonDocument doc(512);
  doc["system_enabled"] = systemEnabled;
  doc["manual_mode"] = manualMode;
  doc["pump_state"] = pumpState;
  doc["fan_state"] = fanState;
  doc["curtain_position"] = curtainPosition;
  doc["wifi_connected"] = (WiFi.status() == WL_CONNECTED);
  doc["free_heap"] = ESP.getFreeHeap();
  doc["uptime"] = millis();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  webServer.sendHeader("Access-Control-Allow-Origin", "*");
  webServer.send(200, "application/json", jsonString);
}

void handleApiLogs() {
  DynamicJsonDocument doc(4096);
  JsonArray logs = doc.createNestedArray("logs");
  
  for (int i = 0; i < MAX_LOG_ENTRIES; i++) {
    int idx = (logIndex + i) % MAX_LOG_ENTRIES;
    if (dataLog[idx].timestamp > 0) {
      JsonObject entry = logs.createNestedObject();
      entry["timestamp"] = dataLog[idx].timestamp;
      entry["temperature"] = dataLog[idx].temperature;
      entry["humidity"] = dataLog[idx].humidity;
      entry["ph"] = dataLog[idx].ph;
      entry["soil_moisture"] = dataLog[idx].soil_moisture;
      entry["actions"] = dataLog[idx].actions;
    }
  }
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  webServer.sendHeader("Access-Control-Allow-Origin", "*");
  webServer.send(200, "application/json", jsonString);
}

void handleApiConfig() {
  DynamicJsonDocument doc(512);
  doc["temp_threshold_high"] = TEMP_THRESHOLD_HIGH;
  doc["temp_threshold_low"] = TEMP_THRESHOLD_LOW;
  doc["ldr_threshold"] = LDR_THRESHOLD;
  doc["water_level_threshold"] = WATER_LEVEL_THRESHOLD;
  doc["soil_moisture_low"] = SOIL_MOISTURE_THRESHOLD_LOW;
  doc["soil_moisture_high"] = SOIL_MOISTURE_THRESHOLD_HIGH;
  doc["ph_offset"] = pH_offset;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  webServer.sendHeader("Access-Control-Allow-Origin", "*");
  webServer.send(200, "application/json", jsonString);
}

void handleApiConfigUpdate() {
  webServer.send(200, "application/json", "{\"status\":\"success\",\"message\":\"Configuration update not implemented yet\"}");
}

// Backward compatibility handlers
void handlePumpControl() {
  if (webServer.hasArg("state")) {
    bool state = webServer.arg("state") == "on";
    controlPump(state);
    webServer.send(200, "application/json", "{\"status\":\"success\",\"pump\":\"" + String(state ? "ON" : "OFF") + "\"}");
  } else {
    webServer.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Missing state parameter\"}");
  }
}

void handleFanControl() {
  if (webServer.hasArg("state")) {
    bool state = webServer.arg("state") == "on";
    controlFan(state);
    webServer.send(200, "application/json", "{\"status\":\"success\",\"fan\":\"" + String(state ? "ON" : "OFF") + "\"}");
  } else {
    webServer.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Missing state parameter\"}");
  }
}

void handleCurtainControl() {
  if (webServer.hasArg("state")) {
    bool close = webServer.arg("state") == "close";
    controlCurtain(close);
    webServer.send(200, "application/json", "{\"status\":\"success\",\"curtain\":\"" + String(close ? "CLOSED" : "OPEN") + "\"}");
  } else {
    webServer.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Missing state parameter\"}");
  }
}

void handleModeControl() {
  if (webServer.hasArg("mode")) {
    manualMode = webServer.arg("mode") == "manual";
    webServer.send(200, "application/json", "{\"status\":\"success\",\"mode\":\"" + String(manualMode ? "MANUAL" : "AUTO") + "\"}");
  } else {
    webServer.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Missing mode parameter\"}");
  }
}

void handleSystemControl() {
  if (webServer.hasArg("state")) {
    systemEnabled = webServer.arg("state") == "on";
    webServer.send(200, "application/json", "{\"status\":\"success\",\"system\":\"" + String(systemEnabled ? "ENABLED" : "DISABLED") + "\"}");
  } else {
    webServer.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Missing state parameter\"}");
  }
}

void handleDataRequest() {
  handleApiData(); // Use the same handler
}

void handleLogsPage() {
  String html = generateLogsPage();
  webServer.send(200, "text/html", html);
}

String generateWebInterface() {
  String html = F("<!DOCTYPE html><html><head>");
  html += F("<meta charset=\"UTF-8\">");
  html += F("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">");
  html += F("<title>Terraponix Greenhouse Control</title>");
  html += F("<link rel=\"icon\" href=\"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌱</text></svg>\">");
  
  // Enhanced CSS
  html += F("<style>");
  html += F("* { margin: 0; padding: 0; box-sizing: border-box; }");
  html += F("body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }");
  html += F(".container { max-width: 1200px; margin: 0 auto; background: rgba(255, 255, 255, 0.95); border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }");
  html += F(".header { background: linear-gradient(135deg, #2c5530 0%, #4a7c59 100%); color: white; padding: 30px; text-align: center; }");
  html += F(".header h1 { font-size: 2.5em; margin-bottom: 10px; }");
  html += F(".header p { font-size: 1.2em; opacity: 0.9; }");
  html += F(".status-bar { background: #f8f9fa; padding: 15px 30px; border-bottom: 1px solid #dee2e6; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }");
  html += F(".status-item { display: flex; align-items: center; margin: 5px 0; }");
  html += F(".status-indicator { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }");
  html += F(".status-online { background: #28a745; }");
  html += F(".status-offline { background: #dc3545; }");
  html += F(".content { padding: 30px; }");
  html += F(".sensors, .controls { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin: 30px 0; }");
  html += F(".card { background: white; border-radius: 15px; padding: 25px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); border-left: 5px solid #28a745; transition: transform 0.3s ease, box-shadow 0.3s ease; }");
  html += F(".card:hover { transform: translateY(-5px); box-shadow: 0 10px 25px rgba(0,0,0,0.15); }");
  html += F(".card h3 { color: #2c5530; margin-bottom: 15px; font-size: 1.3em; display: flex; align-items: center; }");
  html += F(".card h3 span { font-size: 1.5em; margin-right: 10px; }");
  html += F(".sensor-value { font-size: 2.2em; font-weight: bold; color: #333; margin: 10px 0; }");
  html += F(".sensor-unit { font-size: 0.8em; color: #666; margin-left: 5px; }");
  html += F(".status-text { font-weight: bold; padding: 8px 15px; border-radius: 20px; display: inline-block; margin: 10px 0; }");
  html += F(".status-on { background: #d4edda; color: #155724; }");
  html += F(".status-off { background: #f8d7da; color: #721c24; }");
  html += F(".status-auto { background: #d1ecf1; color: #0c5460; }");
  html += F(".control-btn { padding: 12px 24px; margin: 8px; border: none; border-radius: 25px; cursor: pointer; font-size: 14px; font-weight: bold; transition: all 0.3s ease; text-transform: uppercase; letter-spacing: 0.5px; }");
  html += F(".btn-on { background: linear-gradient(135deg, #28a745, #20c997); color: white; }");
  html += F(".btn-on:hover { background: linear-gradient(135deg, #218838, #1aa085); transform: translateY(-2px); }");
  html += F(".btn-off { background: linear-gradient(135deg, #dc3545, #e83e8c); color: white; }");
  html += F(".btn-off:hover { background: linear-gradient(135deg, #c82333, #d91a72); transform: translateY(-2px); }");
  html += F(".btn-auto { background: linear-gradient(135deg, #007bff, #6610f2); color: white; }");
  html += F(".btn-auto:hover { background: linear-gradient(135deg, #0056b3, #520dc2); transform: translateY(-2px); }");
  html += F(".control-group { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }");
  html += F(".footer { text-align: center; padding: 20px; background: #f8f9fa; border-top: 1px solid #dee2e6; }");
  html += F(".footer button { background: linear-gradient(135deg, #6c757d, #495057); }");
  html += F(".footer button:hover { background: linear-gradient(135deg, #5a6268, #343a40); }");
  html += F("@media (max-width: 768px) { .sensors, .controls { grid-template-columns: 1fr; } .status-bar { flex-direction: column; text-align: center; } }");
  html += F("</style>");
  
  // Enhanced JavaScript
  html += F("<script>");
  html += F("let autoRefresh = true;");
  html += F("function controlDevice(device, state) {");
  html += F("  fetch('/control/' + device, {");
  html += F("    method: 'POST',");
  html += F("    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },");
  html += F("    body: 'state=' + state");
  html += F("  }).then(response => response.json())");
  html += F("  .then(data => {");
  html += F("    console.log('Control response:', data);");
  html += F("    setTimeout(() => { if(autoRefresh) location.reload(); }, 1000);");
  html += F("  }).catch(error => console.error('Error:', error));");
  html += F("}");
  html += F("function toggleAutoRefresh() {");
  html += F("  autoRefresh = !autoRefresh;");
  html += F("  document.getElementById('autoRefreshBtn').textContent = autoRefresh ? '⏸️ Stop Auto Refresh' : '▶️ Start Auto Refresh';");
  html += F("}");
  html += F("function refreshData() { location.reload(); }");
  html += F("function openLogs() { window.open('/logs', '_blank'); }");
  html += F("if(autoRefresh) { setInterval(() => { if(autoRefresh) refreshData(); }, 15000); }");
  html += F("</script>");
  
  html += F("</head><body>");
  
  // Container start
  html += F("<div class=\"container\">");
  
  // Header
  html += F("<div class=\"header\">");
  html += F("<h1>🌱 Terraponix Greenhouse</h1>");
  html += F("<p>Smart Hydroponic & Soil-based Growing System</p>");
  html += F("</div>");
  
  // Status bar
  html += F("<div class=\"status-bar\">");
  html += F("<div class=\"status-item\">");
  html += F("<div class=\"status-indicator ");
  html += (WiFi.status() == WL_CONNECTED) ? F("status-online") : F("status-offline");
  html += F("\"></div>");
  html += F("<span>WiFi: ");
  html += currentData.wifi_status;
  html += F(" (");
  html += currentData.ip_address;
  html += F(")</span>");
  html += F("</div>");
  html += F("<div class=\"status-item\">");
  html += F("<div class=\"status-indicator ");
  html += systemEnabled ? F("status-online") : F("status-offline");
  html += F("\"></div>");
  html += F("<span>System: ");
  html += currentData.system_status;
  html += F("</span>");
  html += F("</div>");
  html += F("<div class=\"status-item\">");
  html += F("<div class=\"status-indicator status-auto\"></div>");
  html += F("<span>Mode: ");
  html += currentData.mode;
  html += F("</span>");
  html += F("</div>");
  html += F("</div>");
  
  // Content
  html += F("<div class=\"content\">");
  
  // Sensors section
  html += F("<h2 style=\"color: #2c5530; margin-bottom: 20px; font-size: 1.8em;\">📊 Sensor Readings</h2>");
  html += F("<div class=\"sensors\">");
  
  // Temperature card
  html += F("<div class=\"card\">");
  html += F("<h3><span>🌡️</span>Temperature</h3>");
  html += F("<div class=\"sensor-value\">");
  html += String(currentData.temperature, 1);
  html += F("<span class=\"sensor-unit\">°C</span></div>");
  html += F("</div>");
  
  // Humidity card
  html += F("<div class=\"card\">");
  html += F("<h3><span>💧</span>Humidity</h3>");
  html += F("<div class=\"sensor-value\">");
  html += String(currentData.humidity, 1);
  html += F("<span class=\"sensor-unit\">%</span></div>");
  html += F("</div>");
  
  // pH card
  html += F("<div class=\"card\">");
  html += F("<h3><span>🧪</span>pH Level</h3>");
  html += F("<div class=\"sensor-value\">");
  html += String(currentData.ph, 2);
  html += F("</div>");
  html += F("</div>");
  
  // Light card
  html += F("<div class=\"card\">");
  html += F("<h3><span>☀️</span>Light Intensity</h3>");
  html += F("<div class=\"sensor-value\">");
  html += String(currentData.light_intensity);
  html += F("</div>");
  html += F("</div>");
  
  // Soil moisture card
  html += F("<div class=\"card\">");
  html += F("<h3><span>🌱</span>Soil Moisture</h3>");
  html += F("<div class=\"sensor-value\">");
  html += String(currentData.soil_moisture);
  html += F("<span class=\"sensor-unit\">%</span></div>");
  html += F("</div>");
  
  // Water level card
  html += F("<div class=\"card\">");
  html += F("<h3><span>🚰</span>Water Level</h3>");
  html += F("<div class=\"status-text ");
  html += (currentData.water_status == "OK") ? F("status-on") : F("status-off");
  html += F("\">");
  html += currentData.water_status;
  html += F("</div>");
  html += F("<div style=\"font-size: 0.9em; color: #666; margin-top: 5px;\">Raw: ");
  html += String(currentData.water_level);
  html += F("</div>");
  html += F("</div>");
  
  html += F("</div>"); // End sensors
  
  // Controls section
  html += F("<h2 style=\"color: #2c5530; margin: 40px 0 20px 0; font-size: 1.8em;\">🎛️ Device Controls</h2>");
  html += F("<div class=\"controls\">");
  
  // Pump control
  html += F("<div class=\"card\">");
  html += F("<h3><span>🚿</span>Water Pump</h3>");
  html += F("<div class=\"status-text ");
  html += pumpState ? F("status-on") : F("status-off");
  html += F("\">Status: ");
  html += currentData.pump_status;
  html += F("</div>");
  html += F("<div class=\"control-group\">");
  html += F("<button class=\"control-btn btn-on\" onclick=\"controlDevice('pump', 'on')\">Turn ON</button>");
  html += F("<button class=\"control-btn btn-off\" onclick=\"controlDevice('pump', 'off')\">Turn OFF</button>");
  html += F("</div>");
  html += F("</div>");
  
  // Fan control
  html += F("<div class=\"card\">");
  html += F("<h3><span>🌀</span>Cooling Fan</h3>");
  html += F("<div class=\"status-text ");
  html += fanState ? F("status-on") : F("status-off");
  html += F("\">Status: ");
  html += currentData.fan_status;
  html += F("</div>");
  html += F("<div class=\"control-group\">");
  html += F("<button class=\"control-btn btn-on\" onclick=\"controlDevice('fan', 'on')\">Turn ON</button>");
  html += F("<button class=\"control-btn btn-off\" onclick=\"controlDevice('fan', 'off')\">Turn OFF</button>");
  html += F("</div>");
  html += F("</div>");
  
  // Curtain control
  html += F("<div class=\"card\">");
  html += F("<h3><span>🏠</span>Shade Curtain</h3>");
  html += F("<div class=\"status-text ");
  html += (curtainPosition == 0) ? F("status-off") : F("status-on");
  html += F("\">Status: ");
  html += currentData.curtain_status;
  html += F("</div>");
  html += F("<div class=\"control-group\">");
  html += F("<button class=\"control-btn btn-off\" onclick=\"controlDevice('curtain', 'close')\">Close</button>");
  html += F("<button class=\"control-btn btn-on\" onclick=\"controlDevice('curtain', 'open')\">Open</button>");
  html += F("</div>");
  html += F("</div>");
  
  // Mode control
  html += F("<div class=\"card\">");
  html += F("<h3><span>🎛️</span>Control Mode</h3>");
  html += F("<div class=\"status-text ");
  html += manualMode ? F("status-off") : F("status-auto");
  html += F("\">Mode: ");
  html += currentData.mode;
  html += F("</div>");
  html += F("<div class=\"control-group\">");
  html += F("<button class=\"control-btn btn-auto\" onclick=\"controlDevice('mode', 'auto')\">AUTO</button>");
  html += F("<button class=\"control-btn btn-on\" onclick=\"controlDevice('mode', 'manual')\">MANUAL</button>");
  html += F("</div>");
  html += F("</div>");
  
  // System control
  html += F("<div class=\"card\">");
  html += F("<h3><span>⚙️</span>System Control</h3>");
  html += F("<div class=\"status-text ");
  html += systemEnabled ? F("status-on") : F("status-off");
  html += F("\">System: ");
  html += currentData.system_status;
  html += F("</div>");
  html += F("<div class=\"control-group\">");
  html += F("<button class=\"control-btn btn-on\" onclick=\"controlDevice('system', 'on')\">Enable</button>");
  html += F("<button class=\"control-btn btn-off\" onclick=\"controlDevice('system', 'off')\">Disable</button>");
  html += F("</div>");
  html += F("</div>");
  
  html += F("</div>"); // End controls
  html += F("</div>"); // End content
  
  // Footer
  html += F("<div class=\"footer\">");
  html += F("<button class=\"control-btn btn-auto\" onclick=\"refreshData()\">🔄 Refresh Now</button>");
  html += F("<button class=\"control-btn btn-auto\" id=\"autoRefreshBtn\" onclick=\"toggleAutoRefresh()\">⏸️ Stop Auto Refresh</button>");
  html += F("<button class=\"control-btn btn-auto\" onclick=\"openLogs()\">📊 View Logs</button>");
  html += F("<p style=\"margin-top: 15px; color: #666; font-size: 0.9em;\">");
  html += F("Terraponix v");
  html += DEVICE_VERSION;
  html += F(" | Uptime: ");
  html += String(millis() / 1000);
  html += F("s | Free Memory: ");
  html += String(ESP.getFreeHeap());
  html += F(" bytes");
  html += F("</p>");
  html += F("</div>");
  
  html += F("</div>"); // End container
  html += F("</body></html>");
  
  return html;
}

String generateLogsPage() {
  String html = F("<!DOCTYPE html><html><head>");
  html += F("<meta charset=\"UTF-8\">");
  html += F("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">");
  html += F("<title>Terraponix - Data Logs</title>");
  html += F("<style>");
  html += F("body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }");
  html += F(".container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }");
  html += F(".header { text-align: center; color: #2c5530; margin-bottom: 30px; }");
  html += F("table { width: 100%; border-collapse: collapse; margin: 20px 0; }");
  html += F("th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }");
  html += F("th { background: #2c5530; color: white; }");
  html += F("tr:nth-child(even) { background: #f2f2f2; }");
  html += F(".back-btn { background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-bottom: 20px; }");
  html += F("</style>");
  html += F("</head><body>");
  
  html += F("<div class=\"container\">");
  html += F("<div class=\"header\">");
  html += F("<h1>📊 Terraponix Data Logs</h1>");
  html += F("<button class=\"back-btn\" onclick=\"window.close()\">← Back to Dashboard</button>");
  html += F("</div>");
  
  html += F("<table>");
  html += F("<tr><th>Time (ms)</th><th>Temp (°C)</th><th>Humidity (%)</th><th>pH</th><th>Soil (%)</th><th>Actions</th></tr>");
  
  for (int i = 0; i < MAX_LOG_ENTRIES; i++) {
    int idx = (logIndex + i) % MAX_LOG_ENTRIES;
    if (dataLog[idx].timestamp > 0) {
      html += F("<tr>");
      html += F("<td>") + String(dataLog[idx].timestamp) + F("</td>");
      html += F("<td>") + String(dataLog[idx].temperature, 1) + F("</td>");
      html += F("<td>") + String(dataLog[idx].humidity, 1) + F("</td>");
      html += F("<td>") + String(dataLog[idx].ph, 2) + F("</td>");
      html += F("<td>") + String(dataLog[idx].soil_moisture) + F("</td>");
      html += F("<td>") + dataLog[idx].actions + F("</td>");
      html += F("</tr>");
    }
  }
  
  html += F("</table>");
  html += F("</div>");
  html += F("</body></html>");
  
  return html;
}