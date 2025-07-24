from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import datetime
import sqlite3
import threading
import time
from collections import deque

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

# Database initialization for greenhouse data
def init_greenhouse_db():
    conn = sqlite3.connect('greenhouse_data.db')
    cursor = conn.cursor()
    
    # Greenhouse sensor data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS greenhouse_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            ph REAL,
            light_intensity INTEGER,
            water_level INTEGER,
            water_status TEXT,
            soil_moisture INTEGER,
            curtain_status TEXT,
            pump_status TEXT,
            fan_status TEXT,
            mode TEXT,
            wifi_status TEXT,
            ip_address TEXT,
            wifi_signal INTEGER
        )
    ''')
    
    # Device control commands table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS control_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            command_type TEXT NOT NULL,
            device_name TEXT NOT NULL,
            value TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            executed BOOLEAN DEFAULT FALSE,
            execution_time TEXT
        )
    ''')
    
    # Device registration table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registered_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            device_type TEXT NOT NULL,
            ip_address TEXT,
            capabilities TEXT,
            last_seen TEXT,
            status TEXT DEFAULT 'online'
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_greenhouse_db()

# In-memory storage for real-time data
greenhouse_cache = {}
control_queue = deque()
device_registry = {}

@app.route('/', methods=['GET'])
def home():
    """API status endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'Terraponix Greenhouse API Server',
        'version': '2.0',
        'timestamp': datetime.datetime.now().isoformat(),
        'active_devices': len(device_registry),
        'endpoints': {
            'data_collection': '/api/greenhouse-data',
            'device_control': '/api/greenhouse-control',
            'device_registration': '/api/register',
            'real_time_data': '/api/greenhouse/status',
            'historical_data': '/api/greenhouse/history',
            'dashboard': '/dashboard'
        }
    })

@app.route('/api/register', methods=['POST'])
def register_device():
    """Register a new greenhouse device"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        device_type = data.get('device_type')
        ip_address = data.get('ip_address')
        capabilities = data.get('capabilities', '')
        
        if not device_id or not device_type:
            return jsonify({
                'status': 'error',
                'message': 'device_id and device_type are required'
            }), 400
        
        timestamp = datetime.datetime.now().isoformat()
        
        # Update device registry
        device_registry[device_id] = {
            'device_type': device_type,
            'ip_address': ip_address,
            'capabilities': capabilities,
            'last_seen': timestamp,
            'status': 'online'
        }
        
        # Save to database
        conn = sqlite3.connect('greenhouse_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO registered_devices 
            (device_id, device_type, ip_address, capabilities, last_seen, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (device_id, device_type, ip_address, capabilities, timestamp, 'online'))
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Device {device_id} registered successfully',
            'device_id': device_id,
            'registration_time': timestamp
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/greenhouse-data', methods=['POST'])
def receive_greenhouse_data():
    """Receive data from greenhouse ESP32 device"""
    try:
        data = request.get_json()
        device_id = data.get('device_id', 'unknown')
        timestamp = datetime.datetime.now().isoformat()
        
        # Validate required fields
        required_fields = ['temperature', 'humidity', 'ph', 'light_intensity', 'water_level', 'soil_moisture']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Update cache for real-time access
        greenhouse_cache[device_id] = {
            'timestamp': timestamp,
            'temperature': data.get('temperature'),
            'humidity': data.get('humidity'),
            'ph': data.get('ph'),
            'light_intensity': data.get('light_intensity'),
            'water_level': data.get('water_level'),
            'water_status': data.get('water_status', 'UNKNOWN'),
            'soil_moisture': data.get('soil_moisture'),
            'curtain_status': data.get('curtain_status', 'UNKNOWN'),
            'pump_status': data.get('pump_status', 'UNKNOWN'),
            'fan_status': data.get('fan_status', 'UNKNOWN'),
            'mode': data.get('mode', 'AUTO'),
            'wifi_status': data.get('wifi_status', 'UNKNOWN'),
            'ip_address': data.get('ip_address', ''),
            'wifi_signal': data.get('wifi_signal', 0)
        }
        
        # Update device registry
        if device_id in device_registry:
            device_registry[device_id]['last_seen'] = timestamp
            device_registry[device_id]['status'] = 'online'
        
        # Save to database
        conn = sqlite3.connect('greenhouse_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO greenhouse_data 
            (device_id, timestamp, temperature, humidity, ph, light_intensity, 
             water_level, water_status, soil_moisture, curtain_status, pump_status, 
             fan_status, mode, wifi_status, ip_address, wifi_signal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            device_id, timestamp, data.get('temperature'), data.get('humidity'),
            data.get('ph'), data.get('light_intensity'), data.get('water_level'),
            data.get('water_status'), data.get('soil_moisture'), data.get('curtain_status'),
            data.get('pump_status'), data.get('fan_status'), data.get('mode'),
            data.get('wifi_status'), data.get('ip_address'), data.get('wifi_signal', 0)
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Greenhouse data received successfully',
            'device_id': device_id,
            'timestamp': timestamp
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/greenhouse-control', methods=['GET', 'POST'])
def greenhouse_control():
    """Handle device control commands"""
    if request.method == 'GET':
        # Return pending commands for a device
        device_id = request.args.get('device_id')
        if not device_id:
            return jsonify({
                'status': 'error',
                'message': 'device_id parameter required'
            }), 400
        
        # Get pending commands from database
        conn = sqlite3.connect('greenhouse_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM control_commands 
            WHERE device_id = ? AND executed = FALSE
            ORDER BY timestamp ASC
        ''', (device_id,))
        
        commands = []
        for row in cursor.fetchall():
            commands.append({
                'id': row[0],
                'action': 'control',
                'device': row[2],
                'value': row[3] == 'true' or row[3] == '1',
                'timestamp': row[4]
            })
        
        # Mark commands as executed
        if commands:
            cursor.execute('''
                UPDATE control_commands 
                SET executed = TRUE, execution_time = ?
                WHERE device_id = ? AND executed = FALSE
            ''', (datetime.datetime.now().isoformat(), device_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'device_id': device_id,
            'commands': commands
        })
    
    elif request.method == 'POST':
        # Add new control command
        try:
            data = request.get_json()
            device_id = data.get('device_id', 'greenhouse_esp32')
            command_type = data.get('command_type', 'control')
            device_name = data.get('device')  # pump, fan, curtain, mode
            value = str(data.get('value', False))
            
            if not device_name:
                return jsonify({
                    'status': 'error',
                    'message': 'device parameter required'
                }), 400
            
            timestamp = datetime.datetime.now().isoformat()
            
            # Save command to database
            conn = sqlite3.connect('greenhouse_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO control_commands 
                (device_id, command_type, device_name, value, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (device_id, command_type, device_name, value, timestamp))
            conn.commit()
            conn.close()
            
            return jsonify({
                'status': 'success',
                'message': f'Control command sent to {device_name}',
                'device_id': device_id,
                'command': {
                    'device': device_name,
                    'value': value,
                    'timestamp': timestamp
                }
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

@app.route('/api/greenhouse/status', methods=['GET'])
def get_greenhouse_status():
    """Get current status of all greenhouse devices"""
    try:
        device_id = request.args.get('device_id', 'greenhouse_esp32')
        
        if device_id in greenhouse_cache:
            data = greenhouse_cache[device_id]
            
            # Calculate status indicators
            status_indicators = {
                'temperature_status': 'normal' if 20 <= data['temperature'] <= 30 else 'warning',
                'humidity_status': 'normal' if 40 <= data['humidity'] <= 70 else 'warning',
                'ph_status': 'normal' if 6.0 <= data['ph'] <= 7.5 else 'warning',
                'water_status': 'normal' if data['water_status'] == 'OK' else 'warning',
                'soil_moisture_status': 'normal' if data['soil_moisture'] >= 30 else 'warning'
            }
            
            return jsonify({
                'status': 'success',
                'device_id': device_id,
                'data': data,
                'status_indicators': status_indicators,
                'last_update': data['timestamp']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'No data available for device {device_id}'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/greenhouse/history', methods=['GET'])
def get_greenhouse_history():
    """Get historical greenhouse data"""
    try:
        device_id = request.args.get('device_id', 'greenhouse_esp32')
        limit = request.args.get('limit', 100, type=int)
        hours = request.args.get('hours', 24, type=int)
        
        # Calculate time threshold
        time_threshold = datetime.datetime.now() - datetime.timedelta(hours=hours)
        
        conn = sqlite3.connect('greenhouse_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM greenhouse_data 
            WHERE device_id = ? AND timestamp > ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (device_id, time_threshold.isoformat(), limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'id': row[0],
                'device_id': row[1],
                'timestamp': row[2],
                'temperature': row[3],
                'humidity': row[4],
                'ph': row[5],
                'light_intensity': row[6],
                'water_level': row[7],
                'water_status': row[8],
                'soil_moisture': row[9],
                'curtain_status': row[10],
                'pump_status': row[11],
                'fan_status': row[12],
                'mode': row[13],
                'wifi_status': row[14],
                'ip_address': row[15],
                'wifi_signal': row[16]
            })
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'device_id': device_id,
            'history': history,
            'total_records': len(history),
            'time_range_hours': hours
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/devices', methods=['GET'])
def get_registered_devices():
    """Get all registered devices"""
    try:
        conn = sqlite3.connect('greenhouse_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM registered_devices')
        
        devices = []
        for row in cursor.fetchall():
            devices.append({
                'id': row[0],
                'device_id': row[1],
                'device_type': row[2],
                'ip_address': row[3],
                'capabilities': row[4],
                'last_seen': row[5],
                'status': row[6]
            })
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'devices': devices,
            'total_devices': len(devices)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/dashboard')
def dashboard():
    """Simple web dashboard for greenhouse monitoring"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Terraponix Greenhouse Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { color: #2c5530; margin: 0; }
            .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .card h3 { margin-top: 0; color: #333; }
            .sensor-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
            .sensor-item { padding: 10px; background: #f8f9fa; border-radius: 5px; text-align: center; }
            .sensor-value { font-size: 1.5em; font-weight: bold; color: #28a745; }
            .controls { display: flex; gap: 10px; flex-wrap: wrap; }
            .control-btn { padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; }
            .btn-primary { background: #007bff; color: white; }
            .btn-success { background: #28a745; color: white; }
            .btn-danger { background: #dc3545; color: white; }
            .status-online { color: #28a745; }
            .status-offline { color: #dc3545; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌱 Terraponix Greenhouse Dashboard</h1>
                <p>Real-time Monitoring & Control System</p>
            </div>
            
            <div class="cards">
                <div class="card">
                    <h3>📊 Sensor Readings</h3>
                    <div class="sensor-grid" id="sensorData">
                        <div class="sensor-item">
                            <div>Temperature</div>
                            <div class="sensor-value" id="temperature">--°C</div>
                        </div>
                        <div class="sensor-item">
                            <div>Humidity</div>
                            <div class="sensor-value" id="humidity">--%</div>
                        </div>
                        <div class="sensor-item">
                            <div>pH Level</div>
                            <div class="sensor-value" id="ph">--</div>
                        </div>
                        <div class="sensor-item">
                            <div>Light</div>
                            <div class="sensor-value" id="light">--</div>
                        </div>
                        <div class="sensor-item">
                            <div>Soil Moisture</div>
                            <div class="sensor-value" id="soil">--%</div>
                        </div>
                        <div class="sensor-item">
                            <div>Water Level</div>
                            <div class="sensor-value" id="water">--</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🎛️ Device Controls</h3>
                    <div style="margin-bottom: 15px;">
                        <strong>Water Pump:</strong> <span id="pumpStatus">--</span><br>
                        <div class="controls" style="margin-top: 5px;">
                            <button class="control-btn btn-success" onclick="controlDevice('pump', true)">Turn ON</button>
                            <button class="control-btn btn-danger" onclick="controlDevice('pump', false)">Turn OFF</button>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <strong>Cooling Fan:</strong> <span id="fanStatus">--</span><br>
                        <div class="controls" style="margin-top: 5px;">
                            <button class="control-btn btn-success" onclick="controlDevice('fan', true)">Turn ON</button>
                            <button class="control-btn btn-danger" onclick="controlDevice('fan', false)">Turn OFF</button>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <strong>Curtain:</strong> <span id="curtainStatus">--</span><br>
                        <div class="controls" style="margin-top: 5px;">
                            <button class="control-btn btn-danger" onclick="controlDevice('curtain', true)">Close</button>
                            <button class="control-btn btn-success" onclick="controlDevice('curtain', false)">Open</button>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📡 System Status</h3>
                    <p><strong>Device Status:</strong> <span id="deviceStatus" class="status-offline">Offline</span></p>
                    <p><strong>Control Mode:</strong> <span id="controlMode">--</span></p>
                    <p><strong>WiFi Signal:</strong> <span id="wifiSignal">-- dBm</span></p>
                    <p><strong>Last Update:</strong> <span id="lastUpdate">--</span></p>
                    <button class="control-btn btn-primary" onclick="refreshData()">🔄 Refresh Data</button>
                </div>
            </div>
        </div>
        
        <script>
            function refreshData() {
                fetch('/api/greenhouse/status?device_id=greenhouse_esp32')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            const d = data.data;
                            document.getElementById('temperature').textContent = d.temperature + '°C';
                            document.getElementById('humidity').textContent = d.humidity + '%';
                            document.getElementById('ph').textContent = d.ph.toFixed(2);
                            document.getElementById('light').textContent = d.light_intensity;
                            document.getElementById('soil').textContent = d.soil_moisture + '%';
                            document.getElementById('water').textContent = d.water_status;
                            
                            document.getElementById('pumpStatus').textContent = d.pump_status;
                            document.getElementById('fanStatus').textContent = d.fan_status;
                            document.getElementById('curtainStatus').textContent = d.curtain_status;
                            document.getElementById('controlMode').textContent = d.mode;
                            document.getElementById('wifiSignal').textContent = d.wifi_signal + ' dBm';
                            document.getElementById('lastUpdate').textContent = new Date(d.timestamp).toLocaleString();
                            
                            document.getElementById('deviceStatus').textContent = 'Online';
                            document.getElementById('deviceStatus').className = 'status-online';
                        } else {
                            document.getElementById('deviceStatus').textContent = 'Offline';
                            document.getElementById('deviceStatus').className = 'status-offline';
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        document.getElementById('deviceStatus').textContent = 'Error';
                        document.getElementById('deviceStatus').className = 'status-offline';
                    });
            }
            
            function controlDevice(device, value) {
                fetch('/api/greenhouse-control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_id: 'greenhouse_esp32',
                        device: device,
                        value: value
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        alert('Command sent successfully!');
                        setTimeout(refreshData, 2000);
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to send command');
                });
            }
            
            // Auto refresh every 10 seconds
            setInterval(refreshData, 10000);
            
            // Initial load
            refreshData();
        </script>
    </body>
    </html>
    '''
    return html

if __name__ == '__main__':
    print("🚀 Starting Terraponix Greenhouse API Server...")
    print("📡 Server will run at: http://0.0.0.0:5000")
    print("🌐 Dashboard available at: http://0.0.0.0:5000/dashboard")
    print("📱 Make sure your ESP32 and devices are connected to the same network")
    print("\n🔧 Available API Endpoints:")
    print("   - GET  /                           : API status")
    print("   - POST /api/register               : Register device")
    print("   - POST /api/greenhouse-data        : Receive sensor data")
    print("   - GET/POST /api/greenhouse-control : Device control")
    print("   - GET  /api/greenhouse/status      : Current status")
    print("   - GET  /api/greenhouse/history     : Historical data")
    print("   - GET  /api/devices                : Registered devices")
    print("   - GET  /dashboard                  : Web dashboard")
    print("\n✅ Server starting...\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)