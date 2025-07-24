from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import datetime
import sqlite3
import threading
import time

app = Flask(__name__)
CORS(app)  # Mengizinkan cross-origin requests

# Database untuk menyimpan data sensor
def init_db():
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            sensor_type TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT,
            timestamp TEXT NOT NULL,
            status TEXT DEFAULT 'active'
        )
    ''')
    conn.commit()
    conn.close()

# Inisialisasi database saat startup
init_db()

# Storage untuk data sensor real-time
sensor_data_cache = {}
connected_sensors = {}

@app.route('/', methods=['GET'])
def home():
    """Endpoint untuk check status API"""
    return jsonify({
        'status': 'success',
        'message': 'Sensor API Server Running',
        'timestamp': datetime.datetime.now().isoformat(),
        'connected_sensors': len(connected_sensors)
    })

@app.route('/api/sensor/register', methods=['POST'])
def register_sensor():
    """Endpoint untuk registrasi sensor baru"""
    try:
        data = request.get_json()
        sensor_id = data.get('sensor_id')
        sensor_type = data.get('sensor_type')
        sensor_name = data.get('sensor_name', f'Sensor_{sensor_id}')
        
        if not sensor_id or not sensor_type:
            return jsonify({
                'status': 'error',
                'message': 'sensor_id dan sensor_type harus diisi'
            }), 400
        
        # Simpan info sensor yang terhubung
        connected_sensors[sensor_id] = {
            'sensor_type': sensor_type,
            'sensor_name': sensor_name,
            'connected_at': datetime.datetime.now().isoformat(),
            'last_update': datetime.datetime.now().isoformat(),
            'status': 'connected'
        }
        
        return jsonify({
            'status': 'success',
            'message': f'Sensor {sensor_id} berhasil terdaftar',
            'sensor_id': sensor_id
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/sensor/data', methods=['POST'])
def receive_sensor_data():
    """Endpoint untuk menerima data dari sensor"""
    try:
        data = request.get_json()
        sensor_id = data.get('sensor_id')
        sensor_type = data.get('sensor_type')
        value = data.get('value')
        unit = data.get('unit', '')
        
        if not all([sensor_id, sensor_type, value is not None]):
            return jsonify({
                'status': 'error',
                'message': 'Data tidak lengkap: sensor_id, sensor_type, dan value harus diisi'
            }), 400
        
        timestamp = datetime.datetime.now().isoformat()
        
        # Simpan ke cache untuk real-time access
        sensor_data_cache[sensor_id] = {
            'sensor_type': sensor_type,
            'value': value,
            'unit': unit,
            'timestamp': timestamp,
            'status': 'active'
        }
        
        # Update status sensor yang terhubung
        if sensor_id in connected_sensors:
            connected_sensors[sensor_id]['last_update'] = timestamp
            connected_sensors[sensor_id]['status'] = 'active'
        
        # Simpan ke database
        conn = sqlite3.connect('sensor_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sensor_readings (sensor_id, sensor_type, value, unit, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (sensor_id, sensor_type, value, unit, timestamp))
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Data sensor berhasil diterima',
            'timestamp': timestamp
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/sensor/data/<sensor_id>', methods=['GET'])
def get_sensor_data(sensor_id):
    """Endpoint untuk mendapatkan data sensor terbaru"""
    try:
        if sensor_id in sensor_data_cache:
            return jsonify({
                'status': 'success',
                'data': sensor_data_cache[sensor_id]
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Sensor {sensor_id} tidak ditemukan atau tidak ada data'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/sensors/all', methods=['GET'])
def get_all_sensors():
    """Endpoint untuk mendapatkan data semua sensor"""
    try:
        return jsonify({
            'status': 'success',
            'data': sensor_data_cache,
            'connected_sensors': connected_sensors,
            'total_sensors': len(sensor_data_cache)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/sensor/history/<sensor_id>', methods=['GET'])
def get_sensor_history(sensor_id):
    """Endpoint untuk mendapatkan riwayat data sensor"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        conn = sqlite3.connect('sensor_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM sensor_readings 
            WHERE sensor_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (sensor_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'sensor_id': row[1],
                'sensor_type': row[2],
                'value': row[3],
                'unit': row[4],
                'timestamp': row[5],
                'status': row[6]
            })
        
        return jsonify({
            'status': 'success',
            'data': history,
            'total_records': len(history)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/sensor/status', methods=['GET'])
def get_api_status():
    """Endpoint untuk status lengkap API dan konektivitas"""
    try:
        # Cek sensor yang tidak aktif (tidak update > 5 menit)
        current_time = datetime.datetime.now()
        inactive_sensors = []
        
        for sensor_id, sensor_info in connected_sensors.items():
            last_update = datetime.datetime.fromisoformat(sensor_info['last_update'])
            if (current_time - last_update).seconds > 300:  # 5 menit
                inactive_sensors.append(sensor_id)
                connected_sensors[sensor_id]['status'] = 'inactive'
        
        return jsonify({
            'status': 'success',
            'api_status': 'running',
            'timestamp': current_time.isoformat(),
            'connected_sensors': len(connected_sensors),
            'active_sensors': len([s for s in connected_sensors.values() if s['status'] == 'active']),
            'inactive_sensors': len(inactive_sensors),
            'total_data_points': len(sensor_data_cache),
            'sensors_info': connected_sensors
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Sensor API Server...")
    print("📡 API akan berjalan di: http://0.0.0.0:5000")
    print("📱 Pastikan perangkat sensor dan aplikasi terhubung ke hotspot yang sama")
    print("🔧 Endpoint yang tersedia:")
    print("   - GET  /                     : Status API")
    print("   - POST /api/sensor/register  : Registrasi sensor")
    print("   - POST /api/sensor/data      : Kirim data sensor")
    print("   - GET  /api/sensor/data/<id> : Ambil data sensor")
    print("   - GET  /api/sensors/all      : Ambil semua data sensor")
    print("   - GET  /api/sensor/history/<id> : Riwayat data sensor")
    print("   - GET  /api/sensor/status    : Status konektivitas")
    
    app.run(host='0.0.0.0', port=5000, debug=True)