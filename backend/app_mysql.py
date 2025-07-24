from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List
import threading
import time

# Import XAMPP MySQL configuration
from xampp_mysql_config import SensorDataDB, ControlDB, DeviceDB, initialize_database, test_connection

app = Flask(__name__)
CORS(app)

# Global variables for sensor data and control settings
current_sensor_data = {}
control_settings = {
    'pump_auto': True,
    'fan_auto': True,
    'curtain_auto': True,
    'pump_status': False,
    'fan_status': False,
    'curtain_status': False,
    'temp_threshold_min': 20.0,
    'temp_threshold_max': 30.0,
    'humidity_threshold_min': 60.0,
    'humidity_threshold_max': 80.0,
    'ph_threshold_min': 5.5,
    'ph_threshold_max': 6.5,
    'tds_threshold_min': 300.0,
    'tds_threshold_max': 800.0,
    'soil_moisture_threshold_min': 40.0,
    'soil_moisture_threshold_max': 70.0,
    'water_level_threshold_min': 20.0
}

def init_db():
    """Initialize MySQL database with XAMPP"""
    print("Initializing XAMPP MySQL database...")
    
    # Test connection first
    if not test_connection():
        print("❌ Failed to connect to XAMPP MySQL")
        return False
    
    # Initialize database
    if not initialize_database():
        print("❌ Failed to initialize database")
        return False
    
    # Create tables
    if not SensorDataDB.create_tables():
        print("❌ Failed to create tables")
        return False
    
    print("✅ XAMPP MySQL database initialized successfully")
    return True

def load_control_settings():
    """Load control settings from MySQL database"""
    global control_settings
    try:
        settings = ControlDB.get_control_settings(device_id=1)
        if settings:
            # Remove database-specific fields
            settings.pop('id', None)
            settings.pop('device_id', None)
            settings.pop('updated_at', None)
            control_settings.update(settings)
            print("✅ Control settings loaded from MySQL")
        else:
            print("ℹ️ Using default control settings")
    except Exception as e:
        print(f"⚠️ Error loading control settings: {e}")

def save_control_settings():
    """Save control settings to MySQL database"""
    try:
        ControlDB.update_control_settings(device_id=1, settings=control_settings)
        print("✅ Control settings saved to MySQL")
    except Exception as e:
        print(f"⚠️ Error saving control settings: {e}")

@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """Receive sensor data from ESP32 and save to MySQL"""
    global current_sensor_data
    
    try:
        data = request.get_json()
        print(f"📊 Received sensor data: {data}")
        
        # Update current sensor data
        current_sensor_data = data
        
        # Save to MySQL database
        device_id = data.get('device_id', 1)
        sensor_id = SensorDataDB.insert_sensor_data(device_id, data)
        
        if sensor_id:
            # Update device heartbeat
            DeviceDB.update_device_heartbeat(
                device_id, 
                data.get('battery_level'), 
                data.get('solar_power')
            )
            
            print(f"✅ Sensor data saved to MySQL with ID: {sensor_id}")
            
            # Check and handle automatic controls
            handle_automatic_controls(data)
            
            return jsonify({
                'status': 'success',
                'message': 'Sensor data received and saved to MySQL',
                'id': sensor_id
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save sensor data to MySQL'
            }), 500
            
    except Exception as e:
        print(f"❌ Error receiving sensor data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error processing sensor data: {str(e)}'
        }), 500

@app.route('/api/sensor-data', methods=['GET'])
def get_current_data():
    """Get current sensor data"""
    try:
        # Try to get latest data from MySQL
        latest_data = SensorDataDB.get_latest_data(device_id=1)
        
        if latest_data:
            # Remove database-specific fields
            latest_data.pop('id', None)
            latest_data.pop('device_id', None)
            
            # Convert timestamp to string if exists
            if 'timestamp' in latest_data and latest_data['timestamp']:
                if hasattr(latest_data['timestamp'], 'isoformat'):
                    latest_data['timestamp'] = latest_data['timestamp'].isoformat()
            
            return jsonify(latest_data)
        else:
            # Fallback to in-memory data
            return jsonify(current_sensor_data)
            
    except Exception as e:
        print(f"❌ Error getting current data: {str(e)}")
        # Fallback to in-memory data
        return jsonify(current_sensor_data)

@app.route('/api/historical-data', methods=['GET'])
def get_historical_data():
    """Get historical sensor data for charts"""
    try:
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        device_id = request.args.get('device_id', 1, type=int)
        
        print(f"📈 Fetching historical data: {hours}h, limit={limit}, device={device_id}")
        
        data = SensorDataDB.get_historical_data(device_id, hours, limit)
        
        print(f"✅ Retrieved {len(data)} historical records from MySQL")
        
        return jsonify({
            'status': 'success',
            'data': data,
            'count': len(data)
        })
        
    except Exception as e:
        print(f"❌ Error getting historical data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error retrieving historical data: {str(e)}',
            'data': []
        }), 500

@app.route('/api/controls', methods=['GET'])
def get_controls():
    """Get current control settings"""
    try:
        # Try to get latest settings from MySQL
        db_settings = ControlDB.get_control_settings(device_id=1)
        
        if db_settings:
            # Remove database-specific fields
            db_settings.pop('id', None)
            db_settings.pop('device_id', None)
            db_settings.pop('updated_at', None)
            return jsonify(db_settings)
        else:
            # Fallback to in-memory settings
            return jsonify(control_settings)
            
    except Exception as e:
        print(f"❌ Error getting control settings: {str(e)}")
        # Fallback to in-memory settings
        return jsonify(control_settings)

@app.route('/api/controls', methods=['POST'])
def update_controls():
    """Update control settings"""
    global control_settings
    
    try:
        data = request.get_json()
        print(f"🎛️ Updating controls: {data}")
        
        # Update in-memory settings
        control_settings.update(data)
        
        # Save to MySQL database
        success = ControlDB.update_control_settings(device_id=1, settings=data)
        
        if success:
            print("✅ Control settings updated in MySQL")
            return jsonify({
                'status': 'success',
                'message': 'Control settings updated in MySQL',
                'settings': control_settings
            })
        else:
            print("⚠️ Failed to update MySQL, using in-memory settings")
            return jsonify({
                'status': 'warning',
                'message': 'Settings updated locally, MySQL update failed',
                'settings': control_settings
            })
            
    except Exception as e:
        print(f"❌ Error updating controls: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error updating controls: {str(e)}'
        }), 500

@app.route('/api/esp32-config', methods=['GET'])
def get_esp32_config():
    """Get ESP32 configuration (control outputs)"""
    try:
        db_settings = ControlDB.get_control_settings(device_id=1)
        
        if db_settings:
            esp32_config = {
                'pump_status': db_settings.get('pump_status', False),
                'fan_status': db_settings.get('fan_status', False),
                'curtain_status': db_settings.get('curtain_status', False),
                'pump_auto': db_settings.get('pump_auto', True),
                'fan_auto': db_settings.get('fan_auto', True),
                'curtain_auto': db_settings.get('curtain_auto', True)
            }
        else:
            esp32_config = {
                'pump_status': control_settings.get('pump_status', False),
                'fan_status': control_settings.get('fan_status', False),
                'curtain_status': control_settings.get('curtain_status', False),
                'pump_auto': control_settings.get('pump_auto', True),
                'fan_auto': control_settings.get('fan_auto', True),
                'curtain_auto': control_settings.get('curtain_auto', True)
            }
        
        return jsonify(esp32_config)
        
    except Exception as e:
        print(f"❌ Error getting ESP32 config: {str(e)}")
        return jsonify({
            'pump_status': False,
            'fan_status': False,
            'curtain_status': False,
            'pump_auto': True,
            'fan_auto': True,
            'curtain_auto': True
        })

@app.route('/api/database-status', methods=['GET'])
def get_database_status():
    """Get database connection status"""
    try:
        if test_connection():
            # Get some basic stats
            latest_data = SensorDataDB.get_latest_data(device_id=1)
            
            return jsonify({
                'status': 'connected',
                'database': 'MySQL (XAMPP)',
                'last_reading': latest_data['timestamp'] if latest_data else None,
                'message': 'XAMPP MySQL connection active'
            })
        else:
            return jsonify({
                'status': 'disconnected',
                'database': 'MySQL (XAMPP)',
                'message': 'Failed to connect to XAMPP MySQL'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'database': 'MySQL (XAMPP)',
            'message': f'Database error: {str(e)}'
        }), 500

def handle_automatic_controls(sensor_data):
    """Handle automatic control logic based on sensor readings"""
    global control_settings
    
    try:
        temp = sensor_data.get('temperature')
        humidity = sensor_data.get('humidity')
        soil_moisture = sensor_data.get('soil_moisture')
        water_level = sensor_data.get('water_level')
        
        settings_updated = False
        
        # Auto pump control based on soil moisture and water level
        if control_settings.get('pump_auto', True):
            if (soil_moisture is not None and 
                soil_moisture < control_settings.get('soil_moisture_threshold_min', 40.0) and
                water_level is not None and 
                water_level > control_settings.get('water_level_threshold_min', 20.0)):
                
                if not control_settings.get('pump_status', False):
                    control_settings['pump_status'] = True
                    settings_updated = True
                    print("🚰 Auto: Pump turned ON (low soil moisture)")
            else:
                if control_settings.get('pump_status', False):
                    control_settings['pump_status'] = False
                    settings_updated = True
                    print("🚰 Auto: Pump turned OFF")
        
        # Auto fan control based on temperature
        if control_settings.get('fan_auto', True) and temp is not None:
            if temp > control_settings.get('temp_threshold_max', 30.0):
                if not control_settings.get('fan_status', False):
                    control_settings['fan_status'] = True
                    settings_updated = True
                    print(f"🌪️ Auto: Fan turned ON (temp: {temp}°C)")
            elif temp < control_settings.get('temp_threshold_min', 20.0):
                if control_settings.get('fan_status', False):
                    control_settings['fan_status'] = False
                    settings_updated = True
                    print(f"🌪️ Auto: Fan turned OFF (temp: {temp}°C)")
        
        # Auto curtain control based on temperature
        if control_settings.get('curtain_auto', True) and temp is not None:
            if temp > control_settings.get('temp_threshold_max', 30.0):
                if not control_settings.get('curtain_status', False):
                    control_settings['curtain_status'] = True
                    settings_updated = True
                    print(f"🪟 Auto: Curtain CLOSED (temp: {temp}°C)")
            elif temp < control_settings.get('temp_threshold_min', 20.0):
                if control_settings.get('curtain_status', False):
                    control_settings['curtain_status'] = False
                    settings_updated = True
                    print(f"🪟 Auto: Curtain OPENED (temp: {temp}°C)")
        
        # Save updated settings to MySQL if any changes were made
        if settings_updated:
            ControlDB.update_control_settings(device_id=1, settings=control_settings)
            
    except Exception as e:
        print(f"❌ Error in automatic controls: {str(e)}")

def database_monitor():
    """Monitor database connection and reconnect if needed"""
    while True:
        try:
            if not test_connection():
                print("⚠️ Database connection lost, attempting to reconnect...")
                if initialize_database():
                    print("✅ Database reconnected successfully")
                else:
                    print("❌ Failed to reconnect to database")
            
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            print(f"❌ Database monitor error: {str(e)}")
            time.sleep(30)

if __name__ == '__main__':
    print("🚀 Starting Terraponix Server with XAMPP MySQL...")
    
    # Initialize database
    if not init_db():
        print("❌ Failed to initialize database. Please check XAMPP MySQL is running.")
        exit(1)
    
    # Load existing control settings
    load_control_settings()
    
    # Start database monitor in background
    monitor_thread = threading.Thread(target=database_monitor, daemon=True)
    monitor_thread.start()
    
    print("✅ Server ready with XAMPP MySQL!")
    print("📊 Chart implementation using MySQL database")
    print("🌐 Server starting on http://localhost:5000")
    print("📱 ESP32 can send data to: http://localhost:5000/api/sensor-data")
    print("📈 Historical data API: http://localhost:5000/api/historical-data")
    print("💾 Database status: http://localhost:5000/api/database-status")
    
    app.run(host='0.0.0.0', port=5000, debug=True)