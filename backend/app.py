from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List
import mysql.connector
from mysql.connector import Error
import threading
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'terraponix'),
    'charset': 'utf8mb4',
    'autocommit': True
}

# Database connection pool
connection_pool = None

def init_db():
    """Initialize MySQL database and create tables"""
    global connection_pool
    
    try:
        # Create database if not exists
        temp_config = DB_CONFIG.copy()
        temp_config.pop('database')
        
        connection = mysql.connector.connect(**temp_config)
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.close()
        connection.close()
        
        # Create connection pool
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="terraponix_pool",
            pool_size=10,
            pool_reset_session=True,
            **DB_CONFIG
        )
        
        # Create tables
        connection = connection_pool.get_connection()
        cursor = connection.cursor()
        
        # Sensor data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                temperature DECIMAL(5,2),
                humidity DECIMAL(5,2),
                ph DECIMAL(4,2),
                tds DECIMAL(6,2),
                light_intensity DECIMAL(5,2),
                co2 DECIMAL(6,2),
                soil_moisture DECIMAL(5,2),
                water_level DECIMAL(5,2),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB
        ''')
        
        # Control settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS control_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                pump_auto BOOLEAN DEFAULT TRUE,
                fan_auto BOOLEAN DEFAULT TRUE,
                curtain_auto BOOLEAN DEFAULT TRUE,
                pump_status BOOLEAN DEFAULT FALSE,
                fan_status BOOLEAN DEFAULT FALSE,
                curtain_status BOOLEAN DEFAULT FALSE,
                temp_threshold_min DECIMAL(5,2) DEFAULT 20.0,
                temp_threshold_max DECIMAL(5,2) DEFAULT 30.0,
                humidity_threshold_min DECIMAL(5,2) DEFAULT 60.0,
                humidity_threshold_max DECIMAL(5,2) DEFAULT 80.0,
                ph_threshold_min DECIMAL(4,2) DEFAULT 5.5,
                ph_threshold_max DECIMAL(4,2) DEFAULT 6.5,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        ''')
        
        # Alert logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type VARCHAR(50),
                message TEXT,
                severity ENUM('INFO', 'WARNING', 'CRITICAL') DEFAULT 'INFO',
                INDEX idx_timestamp (timestamp),
                INDEX idx_severity (severity)
            ) ENGINE=InnoDB
        ''')
        
        # Device status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_status (
                id INT AUTO_INCREMENT PRIMARY KEY,
                esp32_connected BOOLEAN DEFAULT FALSE,
                last_heartbeat DATETIME,
                battery_level DECIMAL(5,2) DEFAULT 100,
                solar_power DECIMAL(6,2) DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        ''')
        
        # Insert default control settings if not exists
        cursor.execute('SELECT COUNT(*) FROM control_settings')
        result = cursor.fetchone()
        if result[0] == 0:
            cursor.execute('''
                INSERT INTO control_settings (pump_auto, fan_auto, curtain_auto)
                VALUES (TRUE, TRUE, TRUE)
            ''')
        
        # Insert default device status if not exists
        cursor.execute('SELECT COUNT(*) FROM device_status')
        result = cursor.fetchone()
        if result[0] == 0:
            cursor.execute('''
                INSERT INTO device_status (esp32_connected, battery_level, solar_power)
                VALUES (FALSE, 100, 0)
            ''')
        
        cursor.close()
        connection.close()
        
        print("✅ MySQL database initialized successfully")
        
    except Error as e:
        print(f"❌ Error initializing database: {e}")
        raise e

def get_db_connection():
    """Get database connection from pool"""
    try:
        return connection_pool.get_connection()
    except Error as e:
        print(f"Error getting database connection: {e}")
        raise e

# Global variables for real-time data
current_sensor_data = {}
device_status = {
    'esp32_connected': False,
    'last_heartbeat': None,
    'battery_level': 100,
    'solar_power': 0
}

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
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO sensor_data (temperature, humidity, ph, tds, light_intensity, co2, soil_moisture, water_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
        
        # Update device status
        cursor.execute('''
            UPDATE device_status SET 
                esp32_connected = TRUE,
                last_heartbeat = NOW(),
                battery_level = %s,
                solar_power = %s
            WHERE id = 1
        ''', (
            data.get('battery_level', 100),
            data.get('solar_power', 0)
        ))
        
        cursor.close()
        connection.close()
        
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
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get latest sensor data
        cursor.execute('''
            SELECT * FROM sensor_data 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        sensor_data = cursor.fetchone()
        
        # Get device status
        cursor.execute('SELECT * FROM device_status WHERE id = 1')
        device_status = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'sensor_data': sensor_data or {},
            'device_status': device_status or {},
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/historical-data', methods=['GET'])
def get_historical_data():
    """Get historical sensor data for charts"""
    try:
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        sensor_type = request.args.get('sensor', None)
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        if sensor_type:
            # Get data for specific sensor
            cursor.execute(f'''
                SELECT timestamp, {sensor_type} as value
                FROM sensor_data 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                AND {sensor_type} IS NOT NULL
                ORDER BY timestamp ASC
                LIMIT %s
            ''', (hours, limit))
        else:
            # Get all sensor data
            cursor.execute('''
                SELECT * FROM sensor_data 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                ORDER BY timestamp ASC
                LIMIT %s
            ''', (hours, limit))
        
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        
        # Format timestamps for JavaScript
        for result in results:
            if 'timestamp' in result:
                result['timestamp'] = result['timestamp'].isoformat()
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensor-stats', methods=['GET'])
def get_sensor_stats():
    """Get sensor statistics for dashboard"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get statistics for each sensor
        stats = {}
        sensors = ['temperature', 'humidity', 'ph', 'tds', 'light_intensity', 'co2', 'soil_moisture', 'water_level']
        
        for sensor in sensors:
            cursor.execute(f'''
                SELECT 
                    AVG({sensor}) as avg_value,
                    MIN({sensor}) as min_value,
                    MAX({sensor}) as max_value,
                    COUNT({sensor}) as data_points
                FROM sensor_data 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                AND {sensor} IS NOT NULL
            ''', (hours,))
            
            result = cursor.fetchone()
            if result and result['data_points'] > 0:
                stats[sensor] = {
                    'avg': round(float(result['avg_value']), 2) if result['avg_value'] else 0,
                    'min': float(result['min_value']) if result['min_value'] else 0,
                    'max': float(result['max_value']) if result['max_value'] else 0,
                    'data_points': result['data_points']
                }
            else:
                stats[sensor] = {'avg': 0, 'min': 0, 'max': 0, 'data_points': 0}
        
        cursor.close()
        connection.close()
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/controls', methods=['GET'])
def get_controls():
    """Get current control settings"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM control_settings ORDER BY id DESC LIMIT 1')
        
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if result:
            # Convert Decimal to float for JSON serialization
            for key, value in result.items():
                if hasattr(value, '__float__'):
                    result[key] = float(value)
        
        return jsonify(result or {})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/controls', methods=['POST'])
def update_controls():
    """Update control settings"""
    try:
        data = request.get_json()
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Update control settings
        cursor.execute('''
            UPDATE control_settings SET
                pump_auto = %s,
                fan_auto = %s,
                curtain_auto = %s,
                pump_status = %s,
                fan_status = %s,
                curtain_status = %s,
                temp_threshold_min = %s,
                temp_threshold_max = %s,
                humidity_threshold_min = %s,
                humidity_threshold_max = %s,
                ph_threshold_min = %s,
                ph_threshold_max = %s
            WHERE id = (SELECT id FROM (SELECT id FROM control_settings ORDER BY id DESC LIMIT 1) as t)
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
        
        cursor.close()
        connection.close()
        
        return jsonify({'status': 'success', 'message': 'Controls updated successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get recent alerts"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT * FROM alerts 
            ORDER BY timestamp DESC
            LIMIT %s
        ''', (limit,))
        
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        
        # Format timestamps
        for result in results:
            if 'timestamp' in result:
                result['timestamp'] = result['timestamp'].isoformat()
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_thresholds(sensor_data):
    """Check sensor data against thresholds and generate alerts"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get current thresholds
        cursor.execute('SELECT * FROM control_settings ORDER BY id DESC LIMIT 1')
        settings = cursor.fetchone()
        
        if not settings:
            cursor.close()
            connection.close()
            return
        
        alerts = []
        
        # Temperature check
        temp = sensor_data.get('temperature', 0)
        if temp < settings['temp_threshold_min']:
            alerts.append(('TEMPERATURE', f'Temperature too low: {temp}°C', 'WARNING'))
        elif temp > settings['temp_threshold_max']:
            alerts.append(('TEMPERATURE', f'Temperature too high: {temp}°C', 'WARNING'))
        
        # Humidity check
        humidity = sensor_data.get('humidity', 0)
        if humidity < settings['humidity_threshold_min']:
            alerts.append(('HUMIDITY', f'Humidity too low: {humidity}%', 'WARNING'))
        elif humidity > settings['humidity_threshold_max']:
            alerts.append(('HUMIDITY', f'Humidity too high: {humidity}%', 'WARNING'))
        
        # pH check
        ph = sensor_data.get('ph', 0)
        if ph < settings['ph_threshold_min']:
            alerts.append(('PH', f'pH too low: {ph}', 'CRITICAL'))
        elif ph > settings['ph_threshold_max']:
            alerts.append(('PH', f'pH too high: {ph}', 'CRITICAL'))
        
        # Insert alerts
        for alert_type, message, severity in alerts:
            cursor.execute('''
                INSERT INTO alerts (alert_type, message, severity)
                VALUES (%s, %s, %s)
            ''', (alert_type, message, severity))
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error checking thresholds: {e}")

@app.route('/api/device-command', methods=['POST'])
def send_device_command():
    """Send command to ESP32 device"""
    try:
        data = request.get_json()
        command = data.get('command')
        value = data.get('value')
        
        return jsonify({
            'status': 'success', 
            'message': f'Command {command} sent successfully',
            'command': command,
            'value': value
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Background task to check device connectivity
def check_device_connectivity():
    """Background task to monitor device connectivity"""
    while True:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Check if ESP32 has sent data recently
            cursor.execute('''
                UPDATE device_status 
                SET esp32_connected = CASE 
                    WHEN last_heartbeat >= DATE_SUB(NOW(), INTERVAL 5 MINUTE) THEN TRUE 
                    ELSE FALSE 
                END
                WHERE id = 1
            ''')
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"Error checking device connectivity: {e}")
        
        time.sleep(60)  # Check every minute

# Initialize database
try:
    init_db()
    
    # Start background thread
    connectivity_thread = threading.Thread(target=check_device_connectivity)
    connectivity_thread.daemon = True
    connectivity_thread.start()
    
except Exception as e:
    print(f"Failed to initialize application: {e}")
    exit(1)

if __name__ == '__main__':
    print("🌱 Terraponix Backend Server Starting...")
    print("📊 Using MySQL Database")
    print("🔌 ESP32 can send data to: http://localhost:5000/api/sensor-data")
    app.run(debug=True, host='0.0.0.0', port=5000)