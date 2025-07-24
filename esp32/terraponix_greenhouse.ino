#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <ESP32Servo.h>
#include <WebServer.h>

// WiFi credentials
const char* ssid = "Xiaomi 14T Pro";
const char* password = "jougen92";

// Server configuration - Update with your server IP
const char* serverURL = "http://192.168.106.38:5000/api/greenhouse-data";
const char* controlURL = "http://192.168.106.38:5000/api/greenhouse-control";

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

// Thresholds and Calibration
float pH_offset = 0.0;
const float TEMP_THRESHOLD = 29.0;  // Temperature threshold (°C)
const int LDR_THRESHOLD = 2200;     // Light intensity threshold
const int WATER_LEVEL_THRESHOLD = 1500; // Water level threshold
const int SOIL_MOISTURE_THRESHOLD = 30; // Minimum soil moisture %

// Initialize sensors and actuators
DHT dht(DHTPIN, DHTTYPE);
Servo curtainServo;
WebServer localServer(80); // Local web server for direct control

// Timing variables
unsigned long lastSensorRead = 0;
unsigned long lastDataSend = 0;
unsigned long lastControlCheck = 0;
const unsigned long SENSOR_INTERVAL = 5000;   // Read sensors every 5 seconds
const unsigned long SEND_INTERVAL = 30000;    // Send data every 30 seconds
const unsigned long CONTROL_INTERVAL = 10000; // Check for commands every 10 seconds

// Control states
bool manualMode = false;
bool pumpState = false;
bool fanState = false;
int curtainPosition = 90; // 0 = closed, 90 = open

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
  String mode; // "auto" or "manual"
  unsigned long timestamp;
};

GreenhouseData currentData;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n🌱 TERRAPONIX Greenhouse Automation System");
  Serial.println("==========================================");
  
  // Initialize sensors and actuators
  dht.begin();
  curtainServo.attach(SERVO_PIN);
  curtainServo.write(90);  // Initial position (open)
  
  pinMode(PUMP_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, LOW);
  digitalWrite(FAN_PIN, LOW);
  
  // Connect to WiFi
  connectToWiFi();
  
  // Setup local web server for direct control
  setupLocalServer();
  
  // Register with main server
  registerWithServer();
  
  Serial.println("✅ System initialized successfully!");
  Serial.println("📊 Starting monitoring...");
  Serial.println("==========================================\n");
}

void loop() {
  // Handle local web server requests
  localServer.handleClient();
  
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("📡 WiFi disconnected! Attempting to reconnect...");
    connectToWiFi();
    delay(5000);
    return;
  }

  // Read sensors at specified interval
  if (millis() - lastSensorRead >= SENSOR_INTERVAL) {
    readSensors();
    lastSensorRead = millis();
  }
  
  // Send data to server at specified interval
  if (millis() - lastDataSend >= SEND_INTERVAL && WiFi.status() == WL_CONNECTED) {
    sendGreenhouseData();
    lastDataSend = millis();
  }
  
  // Check for control commands from server
  if (millis() - lastControlCheck >= CONTROL_INTERVAL && WiFi.status() == WL_CONNECTED) {
    checkForControlCommands();
    lastControlCheck = millis();
  }
  
  // Automatic control system (only if not in manual mode)
  if (!manualMode) {
    automaticControl();
  }
  
  delay(100);
}

void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("🔗 Connecting to WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected!");
    Serial.print("📍 IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("📶 Signal Strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\n❌ WiFi connection failed!");
  }
}

void setupLocalServer() {
  // Root endpoint
  localServer.on("/", HTTP_GET, []() {
    String html = generateWebInterface();
    localServer.send(200, "text/html", html);
  });
  
  // Control endpoints
  localServer.on("/control/pump", HTTP_POST, handlePumpControl);
  localServer.on("/control/fan", HTTP_POST, handleFanControl);
  localServer.on("/control/curtain", HTTP_POST, handleCurtainControl);
  localServer.on("/control/mode", HTTP_POST, handleModeControl);
  localServer.on("/data", HTTP_GET, handleDataRequest);
  
  localServer.begin();
  Serial.println("🌐 Local web server started at http://" + WiFi.localIP().toString());
}

void registerWithServer() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  http.begin(serverURL.replace("/greenhouse-data", "/register"));
  http.addHeader("Content-Type", "application/json");
  
  DynamicJsonDocument doc(256);
  doc["device_id"] = "greenhouse_esp32";
  doc["device_type"] = "greenhouse_controller";
  doc["ip_address"] = WiFi.localIP().toString();
  doc["capabilities"] = "temperature,humidity,ph,light,water_level,soil_moisture,pump,fan,curtain";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  if (httpResponseCode > 0) {
    Serial.println("✅ Registered with server successfully");
  } else {
    Serial.println("⚠️ Failed to register with server");
  }
  
  http.end();
}

void readSensors() {
  // Read DHT11 (Temperature & Humidity)
  currentData.temperature = dht.readTemperature();
  currentData.humidity = dht.readHumidity();
  
  // Validate DHT readings
  if (isnan(currentData.temperature) || isnan(currentData.humidity)) {
    Serial.println("⚠️ Failed to read DHT sensor!");
    currentData.temperature = 25.0; // Default fallback
    currentData.humidity = 60.0;    // Default fallback
  }
  
  // Read pH sensor
  currentData.ph = readPH();
  
  // Read light intensity (LDR)
  currentData.light_intensity = analogRead(LDR_PIN);
  
  // Read water level
  int waterRaw = analogRead(WATER_LEVEL_PIN);
  currentData.water_level = waterRaw;
  currentData.water_status = (waterRaw < WATER_LEVEL_THRESHOLD) ? "LOW" : "OK";
  
  // Read soil moisture
  int soilRaw = analogRead(SOIL_MOISTURE_PIN);
  currentData.soil_moisture = map(soilRaw, 0, 4095, 100, 0); // Convert to percentage (inverted)
  
  // Update status strings
  currentData.curtain_status = (curtainPosition == 0) ? "CLOSED" : "OPEN";
  currentData.pump_status = pumpState ? "ON" : "OFF";
  currentData.fan_status = fanState ? "ON" : "OFF";
  currentData.wifi_status = (WiFi.status() == WL_CONNECTED) ? "CONNECTED" : "DISCONNECTED";
  currentData.ip_address = WiFi.localIP().toString();
  currentData.mode = manualMode ? "MANUAL" : "AUTO";
  currentData.timestamp = millis();
  
  // Display sensor data on Serial Monitor
  printSensorData();
}

float readPH() {
  int pH_raw = analogRead(PH_PIN);
  float voltage = pH_raw * (3.3 / 4095.0);
  float ph_value = 7.0 - ((voltage - pH_offset) / 0.18);
  
  // Constrain pH to realistic range
  ph_value = constrain(ph_value, 0.0, 14.0);
  return ph_value;
}

void printSensorData() {
  Serial.println("📊 === GREENHOUSE SENSOR DATA ===");
  Serial.printf("🌡️  Temperature: %.1f°C\n", currentData.temperature);
  Serial.printf("💧  Humidity: %.1f%%\n", currentData.humidity);
  Serial.printf("🧪  pH Level: %.2f\n", currentData.ph);
  Serial.printf("☀️  Light Intensity: %d\n", currentData.light_intensity);
  Serial.printf("🚰  Water Level: %s (%d)\n", currentData.water_status.c_str(), currentData.water_level);
  Serial.printf("🌱  Soil Moisture: %d%%\n", currentData.soil_moisture);
  Serial.printf("🚿  Pump: %s\n", currentData.pump_status.c_str());
  Serial.printf("🌀  Fan: %s\n", currentData.fan_status.c_str());
  Serial.printf("🏠  Curtain: %s\n", currentData.curtain_status.c_str());
  Serial.printf("🎛️  Mode: %s\n", currentData.mode.c_str());
  Serial.printf("📡  WiFi: %s (%s)\n", currentData.wifi_status.c_str(), currentData.ip_address.c_str());
  Serial.println("================================\n");
}

void sendGreenhouseData() {
  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");
  
  // Create comprehensive JSON payload
  DynamicJsonDocument doc(1024);
  doc["device_id"] = "greenhouse_esp32";
  doc["timestamp"] = currentData.timestamp;
  doc["temperature"] = currentData.temperature;
  doc["humidity"] = currentData.humidity;
  doc["ph"] = currentData.ph;
  doc["light_intensity"] = currentData.light_intensity;
  doc["water_level"] = currentData.water_level;
  doc["water_status"] = currentData.water_status;
  doc["soil_moisture"] = currentData.soil_moisture;
  doc["curtain_status"] = currentData.curtain_status;
  doc["pump_status"] = currentData.pump_status;
  doc["fan_status"] = currentData.fan_status;
  doc["mode"] = currentData.mode;
  doc["wifi_status"] = currentData.wifi_status;
  doc["ip_address"] = currentData.ip_address;
  doc["wifi_signal"] = WiFi.RSSI();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("📡 Sending data to server...");
  Serial.println("📦 JSON: " + jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("✅ Server Response: %d\n", httpResponseCode);
    Serial.println("📨 Response: " + response);
  } else {
    Serial.printf("❌ HTTP Error: %d\n", httpResponseCode);
    Serial.println("⚠️ Failed to send data to server");
  }
  
  http.end();
}

void checkForControlCommands() {
  HTTPClient http;
  String controlCheckURL = String(controlURL) + "?device_id=greenhouse_esp32";
  
  http.begin(controlCheckURL);
  int httpResponseCode = http.GET();
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    DynamicJsonDocument doc(512);
    
    if (deserializeJson(doc, response) == DeserializationError::Ok) {
      if (doc.containsKey("commands")) {
        JsonArray commands = doc["commands"];
        for (JsonObject cmd : commands) {
          executeControlCommand(cmd);
        }
      }
    }
  }
  
  http.end();
}

void executeControlCommand(JsonObject command) {
  String action = command["action"];
  String device = command["device"];
  bool value = command["value"];
  
  Serial.printf("🎛️ Executing command: %s %s = %s\n", 
                action.c_str(), device.c_str(), value ? "ON/CLOSE" : "OFF/OPEN");
  
  if (device == "pump") {
    controlPump(value);
  } else if (device == "fan") {
    controlFan(value);
  } else if (device == "curtain") {
    controlCurtain(value);
  } else if (device == "mode") {
    manualMode = value;
    Serial.printf("🔄 Mode changed to: %s\n", manualMode ? "MANUAL" : "AUTO");
  }
}

void automaticControl() {
  // Automatic curtain control based on temperature and light
  if (currentData.temperature >= TEMP_THRESHOLD && currentData.light_intensity >= LDR_THRESHOLD) {
    if (curtainPosition != 0) {
      controlCurtain(true); // Close curtain
      Serial.println("🏠 [AUTO] Curtain CLOSED - High temperature + bright light");
    }
  } else {
    if (curtainPosition != 90) {
      controlCurtain(false); // Open curtain
      Serial.println("🏠 [AUTO] Curtain OPENED - Normal conditions");
    }
  }
  
  // Automatic pump control based on soil moisture
  if (currentData.soil_moisture < SOIL_MOISTURE_THRESHOLD) {
    if (!pumpState) {
      controlPump(true);
      Serial.println("🚿 [AUTO] Pump ON - Low soil moisture");
    }
  } else if (currentData.soil_moisture > 80) {
    if (pumpState) {
      controlPump(false);
      Serial.println("🚿 [AUTO] Pump OFF - High soil moisture");
    }
  }
  
  // Automatic fan control based on temperature
  if (currentData.temperature > TEMP_THRESHOLD) {
    if (!fanState) {
      controlFan(true);
      Serial.println("🌀 [AUTO] Fan ON - High temperature");
    }
  } else if (currentData.temperature < 25.0) {
    if (fanState) {
      controlFan(false);
      Serial.println("🌀 [AUTO] Fan OFF - Normal temperature");
    }
  }
}

void controlPump(bool state) {
  pumpState = state;
  digitalWrite(PUMP_PIN, state ? HIGH : LOW);
  currentData.pump_status = state ? "ON" : "OFF";
}

void controlFan(bool state) {
  fanState = state;
  digitalWrite(FAN_PIN, state ? HIGH : LOW);
  currentData.fan_status = state ? "ON" : "OFF";
}

void controlCurtain(bool close) {
  curtainPosition = close ? 0 : 90;
  curtainServo.write(curtainPosition);
  currentData.curtain_status = close ? "CLOSED" : "OPEN";
  delay(500); // Allow servo to move
}

// Local web server handlers
void handlePumpControl() {
  if (localServer.hasArg("state")) {
    bool state = localServer.arg("state") == "on";
    controlPump(state);
    localServer.send(200, "application/json", "{\"status\":\"success\",\"pump\":\"" + String(state ? "ON" : "OFF") + "\"}");
  } else {
    localServer.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Missing state parameter\"}");
  }
}

void handleFanControl() {
  if (localServer.hasArg("state")) {
    bool state = localServer.arg("state") == "on";
    controlFan(state);
    localServer.send(200, "application/json", "{\"status\":\"success\",\"fan\":\"" + String(state ? "ON" : "OFF") + "\"}");
  } else {
    localServer.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Missing state parameter\"}");
  }
}

void handleCurtainControl() {
  if (localServer.hasArg("state")) {
    bool close = localServer.arg("state") == "close";
    controlCurtain(close);
    localServer.send(200, "application/json", "{\"status\":\"success\",\"curtain\":\"" + String(close ? "CLOSED" : "OPEN") + "\"}");
  } else {
    localServer.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Missing state parameter\"}");
  }
}

void handleModeControl() {
  if (localServer.hasArg("mode")) {
    manualMode = localServer.arg("mode") == "manual";
    localServer.send(200, "application/json", "{\"status\":\"success\",\"mode\":\"" + String(manualMode ? "MANUAL" : "AUTO") + "\"}");
  } else {
    localServer.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Missing mode parameter\"}");
  }
}

void handleDataRequest() {
  DynamicJsonDocument doc(1024);
  doc["temperature"] = currentData.temperature;
  doc["humidity"] = currentData.humidity;
  doc["ph"] = currentData.ph;
  doc["light_intensity"] = currentData.light_intensity;
  doc["water_level"] = currentData.water_level;
  doc["soil_moisture"] = currentData.soil_moisture;
  doc["pump_status"] = currentData.pump_status;
  doc["fan_status"] = currentData.fan_status;
  doc["curtain_status"] = currentData.curtain_status;
  doc["mode"] = currentData.mode;
  doc["timestamp"] = currentData.timestamp;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  localServer.send(200, "application/json", jsonString);
}

String generateWebInterface() {
  String html = R"(
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terraponix Greenhouse Control</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #2c5530; margin-bottom: 30px; }
        .sensors, .controls { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .card { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745; }
        .control-btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }
        .btn-on { background: #28a745; color: white; }
        .btn-off { background: #dc3545; color: white; }
        .btn-auto { background: #007bff; color: white; }
        .status { font-weight: bold; }
        .refresh { text-align: center; margin: 20px 0; }
    </style>
    <script>
        function controlDevice(device, state) {
            fetch('/control/' + device, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: 'state=' + state
            }).then(() => setTimeout(() => location.reload(), 500));
        }
        
        function refreshData() {
            location.reload();
        }
        
        setInterval(refreshData, 10000); // Auto refresh every 10 seconds
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌱 Terraponix Greenhouse</h1>
            <p>Real-time Monitoring & Control</p>
        </div>
        
        <div class="sensors">
            <div class="card">
                <h3>🌡️ Temperature</h3>
                <div class="status">)" + String(currentData.temperature) + R"(°C</div>
            </div>
            <div class="card">
                <h3>💧 Humidity</h3>
                <div class="status">)" + String(currentData.humidity) + R"(%</div>
            </div>
            <div class="card">
                <h3>🧪 pH Level</h3>
                <div class="status">)" + String(currentData.ph) + R"(</div>
            </div>
            <div class="card">
                <h3>☀️ Light</h3>
                <div class="status">)" + String(currentData.light_intensity) + R"(</div>
            </div>
            <div class="card">
                <h3>🌱 Soil Moisture</h3>
                <div class="status">)" + String(currentData.soil_moisture) + R"(%</div>
            </div>
            <div class="card">
                <h3>🚰 Water Level</h3>
                <div class="status">)" + currentData.water_status + R"(</div>
            </div>
        </div>
        
        <div class="controls">
            <div class="card">
                <h3>🚿 Water Pump</h3>
                <div class="status">Status: )" + currentData.pump_status + R"(</div>
                <button class="control-btn btn-on" onclick="controlDevice('pump', 'on')">Turn ON</button>
                <button class="control-btn btn-off" onclick="controlDevice('pump', 'off')">Turn OFF</button>
            </div>
            <div class="card">
                <h3>🌀 Cooling Fan</h3>
                <div class="status">Status: )" + currentData.fan_status + R"(</div>
                <button class="control-btn btn-on" onclick="controlDevice('fan', 'on')">Turn ON</button>
                <button class="control-btn btn-off" onclick="controlDevice('fan', 'off')">Turn OFF</button>
            </div>
            <div class="card">
                <h3>🏠 Curtain</h3>
                <div class="status">Status: )" + currentData.curtain_status + R"(</div>
                <button class="control-btn btn-off" onclick="controlDevice('curtain', 'close')">Close</button>
                <button class="control-btn btn-on" onclick="controlDevice('curtain', 'open')">Open</button>
            </div>
            <div class="card">
                <h3>🎛️ Control Mode</h3>
                <div class="status">Mode: )" + currentData.mode + R"(</div>
                <button class="control-btn btn-auto" onclick="controlDevice('mode', 'auto')">AUTO</button>
                <button class="control-btn btn-on" onclick="controlDevice('mode', 'manual')">MANUAL</button>
            </div>
        </div>
        
        <div class="refresh">
            <button class="control-btn btn-auto" onclick="refreshData()">🔄 Refresh Data</button>
            <p><small>Last updated: )" + String(millis()) + R"( ms</small></p>
        </div>
    </div>
</body>
</html>
  )";
  
  return html;
}