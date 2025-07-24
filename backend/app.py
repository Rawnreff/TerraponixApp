from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List
import sqlite3
import threading
import time

app = Flask(__name__)
CORS(app)

# Database initialization
def init_db():
    conn = sqlite3.connect('terraponix.db')
    cursor = conn.cursor()
    
    # Sensor data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            temperature REAL,
            humidity REAL,
            ph REAL,
            tds REAL,
            light_intensity REAL,
            co2 REAL,
            soil_moisture REAL,
            water_level REAL
        )
    ''')
    
    # Control settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS control_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pump_auto BOOLEAN DEFAULT TRUE,
            fan_auto BOOLEAN DEFAULT TRUE,
            curtain_auto BOOLEAN DEFAULT TRUE,
            pump_status BOOLEAN DEFAULT FALSE,
            fan_status BOOLEAN DEFAULT FALSE,
            curtain_status BOOLEAN DEFAULT FALSE,
            temp_threshold_min REAL DEFAULT 20.0,
            temp_threshold_max REAL DEFAULT 30.0,
            humidity_threshold_min REAL DEFAULT 60.0,
            humidity_threshold_max REAL DEFAULT 80.0,
            ph_threshold_min REAL DEFAULT 5.5,
            ph_threshold_max REAL DEFAULT 6.5,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Alert logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            alert_type TEXT,
            message TEXT,
            severity TEXT DEFAULT 'INFO'
        )
    ''')
    
    # Insert default control settings if not exists
    cursor.execute('SELECT COUNT(*) FROM control_settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO control_settings (pump_auto, fan_auto, curtain_auto)
            VALUES (TRUE, TRUE, TRUE)
        ''')
    
    conn.commit()
    conn.close()

# Global variables for real-time data
current_sensor_data = {}
device_status = {
    'esp32_connected': False,
    'last_heartbeat': None,
    'battery_level': 100,
    'solar_power': 0
}

# Initialize database
init_db()

@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """Endpoint to receive sensor data from ESP32"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['temperature', 'humidity', 'ph', 'tds', 'light_intensity', 'co2']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Store in database
        conn = sqlite3.connect('terraponix.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sensor_data (temperature, humidity, ph, tds, light_intensity, co2, soil_moisture, water_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['temperature'],
            data['humidity'],
            data['ph'],
            data['tds'],
            data['light_intensity'],
            data['co2'],
            data.get('soil_moisture', 0),
            data.get('water_level', 0)
        ))
        conn.commit()
        conn.close()
        
        # Update global current data
        global current_sensor_data, device_status
        current_sensor_data = data
        device_status['esp32_connected'] = True
        device_status['last_heartbeat'] = datetime.now()
        device_status['battery_level'] = data.get('battery_level', 100)
        device_status['solar_power'] = data.get('solar_power', 0)
        
        # Check thresholds and generate alerts
        check_thresholds(data)
        
        return jsonify({'status': 'success', 'message': 'Data received successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/current-data', methods=['GET'])
def get_current_data():
    """Get current sensor data for mobile app"""
    return jsonify({
        'sensor_data': current_sensor_data,
        'device_status': device_status,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/historical-data', methods=['GET'])
def get_historical_data():
    """Get historical sensor data"""
    try:
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        conn = sqlite3.connect('terraponix.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM sensor_data 
            WHERE timestamp >= datetime('now', '-{} hours')
            ORDER BY timestamp DESC
            LIMIT ?
        '''.format(hours), (limit,))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/controls', methods=['GET'])
def get_controls():
    """Get current control settings"""
    try:
        conn = sqlite3.connect('terraponix.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM control_settings ORDER BY id DESC LIMIT 1')
        
        columns = [description[0] for description in cursor.description]
        result = cursor.fetchone()
        
        if result:
            controls = dict(zip(columns, result))
        else:
            controls = {}
        
        conn.close()
        return jsonify(controls)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/controls', methods=['POST'])
def update_controls():
    """Update control settings"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('terraponix.db')
        cursor = conn.cursor()
        
        # Update control settings
        cursor.execute('''
            UPDATE control_settings SET
                pump_auto = ?,
                fan_auto = ?,
                curtain_auto = ?,
                pump_status = ?,
                fan_status = ?,
                curtain_status = ?,
                temp_threshold_min = ?,
                temp_threshold_max = ?,
                humidity_threshold_min = ?,
                humidity_threshold_max = ?,
                ph_threshold_min = ?,
                ph_threshold_max = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT MAX(id) FROM control_settings)
        ''', (
            data.get('pump_auto', True),
            data.get('fan_auto', True),
            data.get('curtain_auto', True),
            data.get('pump_status', False),
            data.get('fan_status', False),
            data.get('curtain_status', False),
            data.get('temp_threshold_min', 20.0),
            data.get('temp_threshold_max', 30.0),
            data.get('humidity_threshold_min', 60.0),
            data.get('humidity_threshold_max', 80.0),
            data.get('ph_threshold_min', 5.5),
            data.get('ph_threshold_max', 6.5)
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Controls updated successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get recent alerts"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        conn = sqlite3.connect('terraponix.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM alerts 
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_thresholds(sensor_data):
    """Check sensor data against thresholds and generate alerts"""
    try:
        conn = sqlite3.connect('terraponix.db')
        cursor = conn.cursor()
        
        # Get current thresholds
        cursor.execute('SELECT * FROM control_settings ORDER BY id DESC LIMIT 1')
        settings = cursor.fetchone()
        
        if not settings:
            return
        
        alerts = []
        
        # Temperature check
        temp = sensor_data.get('temperature', 0)
        if temp < settings[7]:  # temp_threshold_min
            alerts.append(('TEMPERATURE', f'Temperature too low: {temp}°C', 'WARNING'))
        elif temp > settings[8]:  # temp_threshold_max
            alerts.append(('TEMPERATURE', f'Temperature too high: {temp}°C', 'WARNING'))
        
        # Humidity check
        humidity = sensor_data.get('humidity', 0)
        if humidity < settings[9]:  # humidity_threshold_min
            alerts.append(('HUMIDITY', f'Humidity too low: {humidity}%', 'WARNING'))
        elif humidity > settings[10]:  # humidity_threshold_max
            alerts.append(('HUMIDITY', f'Humidity too high: {humidity}%', 'WARNING'))
        
        # pH check
        ph = sensor_data.get('ph', 0)
        if ph < settings[11]:  # ph_threshold_min
            alerts.append(('PH', f'pH too low: {ph}', 'CRITICAL'))
        elif ph > settings[12]:  # ph_threshold_max
            alerts.append(('PH', f'pH too high: {ph}', 'CRITICAL'))
        
        # Insert alerts
        for alert_type, message, severity in alerts:
            cursor.execute('''
                INSERT INTO alerts (alert_type, message, severity)
                VALUES (?, ?, ?)
            ''', (alert_type, message, severity))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error checking thresholds: {e}")

@app.route('/api/device-command', methods=['POST'])
def send_device_command():
    """Send command to ESP32 device"""
    try:
        data = request.get_json()
        command = data.get('command')
        value = data.get('value')
        
        # Store command for ESP32 to retrieve
        # In a real implementation, you might use MQTT or WebSocket
        # For now, we'll store it in a simple way
        
        # Here you would implement the actual command sending logic
        # This could be via MQTT, HTTP request to ESP32, or WebSocket
        
        return jsonify({
            'status': 'success', 
            'message': f'Command {command} sent successfully',
            'command': command,
            'value': value
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Background task to check device connectivity
def check_device_connectivity():
    """Background task to monitor device connectivity"""
    while True:
        if device_status['last_heartbeat']:
            time_diff = datetime.now() - device_status['last_heartbeat']
            if time_diff > timedelta(minutes=5):
                device_status['esp32_connected'] = False
        
        time.sleep(60)  # Check every minute

# Start background thread
connectivity_thread = threading.Thread(target=check_device_connectivity)
connectivity_thread.daemon = True
connectivity_thread.start()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    print("🌱 Terraponix Backend Server Starting...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🔌 ESP32 can send data to: http://localhost:5000/api/sensor-data")
    app.run(debug=True, host='0.0.0.0', port=5000)