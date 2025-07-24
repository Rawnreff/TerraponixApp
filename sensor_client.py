import requests
import time
import random
import json
from datetime import datetime

class SensorClient:
    def __init__(self, api_url, sensor_id, sensor_type):
        self.api_url = api_url.rstrip('/')
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.is_registered = False
        
    def register_sensor(self, sensor_name=None):
        """Registrasi sensor ke API"""
        url = f"{self.api_url}/api/sensor/register"
        data = {
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type,
            'sensor_name': sensor_name or f'Sensor_{self.sensor_id}'
        }
        
        try:
            response = requests.post(url, json=data, timeout=5)
            if response.status_code == 200:
                print(f"✅ Sensor {self.sensor_id} berhasil terdaftar")
                self.is_registered = True
                return True
            else:
                print(f"❌ Gagal registrasi: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error registrasi: {e}")
            return False
    
    def send_data(self, value, unit=''):
        """Kirim data sensor ke API"""
        if not self.is_registered:
            print("⚠️ Sensor belum terdaftar, mencoba registrasi...")
            if not self.register_sensor():
                return False
        
        url = f"{self.api_url}/api/sensor/data"
        data = {
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type,
            'value': value,
            'unit': unit
        }
        
        try:
            response = requests.post(url, json=data, timeout=5)
            if response.status_code == 200:
                print(f"📤 Data terkirim: {value} {unit} pada {datetime.now().strftime('%H:%M:%S')}")
                return True
            else:
                print(f"❌ Gagal kirim data: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error kirim data: {e}")
            return False

def simulate_temperature_sensor(api_url):
    """Simulasi sensor suhu"""
    sensor = SensorClient(api_url, "TEMP_001", "temperature")
    
    # Registrasi sensor
    sensor.register_sensor("Sensor Suhu Ruangan")
    
    print("🌡️ Memulai simulasi sensor suhu...")
    print("📍 Tekan Ctrl+C untuk berhenti")
    
    try:
        while True:
            # Simulasi data suhu (20-35°C)
            temperature = round(random.uniform(20.0, 35.0), 2)
            sensor.send_data(temperature, "°C")
            time.sleep(5)  # Kirim data setiap 5 detik
            
    except KeyboardInterrupt:
        print("\n🛑 Simulasi sensor dihentikan")

def simulate_humidity_sensor(api_url):
    """Simulasi sensor kelembaban"""
    sensor = SensorClient(api_url, "HUM_001", "humidity")
    
    # Registrasi sensor
    sensor.register_sensor("Sensor Kelembaban")
    
    print("💧 Memulai simulasi sensor kelembaban...")
    print("📍 Tekan Ctrl+C untuk berhenti")
    
    try:
        while True:
            # Simulasi data kelembaban (40-90%)
            humidity = round(random.uniform(40.0, 90.0), 2)
            sensor.send_data(humidity, "%")
            time.sleep(7)  # Kirim data setiap 7 detik
            
    except KeyboardInterrupt:
        print("\n🛑 Simulasi sensor dihentikan")

if __name__ == '__main__':
    # Ganti dengan IP address perangkat yang menjalankan API
    # Contoh: "http://192.168.43.100:5000" untuk hotspot
    API_URL = "http://localhost:5000"
    
    print("🔧 Contoh penggunaan Sensor Client")
    print("📱 Pastikan API server sudah berjalan")
    print(f"🌐 Menghubungi API di: {API_URL}")
    print()
    
    # Test koneksi ke API
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Koneksi ke API berhasil!")
            print()
        else:
            print("❌ API tidak merespons dengan benar")
            exit(1)
    except Exception as e:
        print(f"❌ Tidak dapat terhubung ke API: {e}")
        print("💡 Pastikan:")
        print("   - API server sudah berjalan")
        print("   - IP address sudah benar")
        print("   - Kedua perangkat di jaringan yang sama")
        exit(1)
    
    # Menu pilihan sensor
    print("Pilih jenis sensor untuk disimulasikan:")
    print("1. Sensor Suhu")
    print("2. Sensor Kelembaban")
    print("3. Kirim data custom")
    
    choice = input("\nMasukkan pilihan (1-3): ").strip()
    
    if choice == "1":
        simulate_temperature_sensor(API_URL)
    elif choice == "2":
        simulate_humidity_sensor(API_URL)
    elif choice == "3":
        # Custom sensor
        sensor_id = input("Masukkan ID sensor: ").strip()
        sensor_type = input("Masukkan jenis sensor: ").strip()
        sensor_name = input("Masukkan nama sensor (opsional): ").strip()
        
        sensor = SensorClient(API_URL, sensor_id, sensor_type)
        sensor.register_sensor(sensor_name if sensor_name else None)
        
        print(f"\n📤 Sensor {sensor_id} siap mengirim data")
        print("📍 Format: masukkan nilai lalu unit (pisahkan dengan spasi)")
        print("📍 Contoh: 25.5 °C atau 100 mm")
        print("📍 Ketik 'exit' untuk keluar")
        
        while True:
            try:
                user_input = input(f"\n[{sensor_id}] Masukkan data: ").strip()
                if user_input.lower() == 'exit':
                    break
                
                parts = user_input.split()
                if len(parts) >= 1:
                    try:
                        value = float(parts[0])
                        unit = ' '.join(parts[1:]) if len(parts) > 1 else ''
                        sensor.send_data(value, unit)
                    except ValueError:
                        print("❌ Format nilai tidak valid, gunakan angka")
                else:
                    print("❌ Masukkan minimal nilai sensor")
                    
            except KeyboardInterrupt:
                break
        
        print(f"\n🛑 Sensor {sensor_id} dihentikan")
    else:
        print("❌ Pilihan tidak valid")