import requests
import time
import json
from datetime import datetime
import threading

class SensorApp:
    def __init__(self, api_url):
        self.api_url = api_url.rstrip('/')
        self.monitoring = False
        
    def test_connection(self):
        """Test koneksi ke API"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ Koneksi ke API berhasil!")
                print(f"📊 Status: {data.get('message')}")
                print(f"🕒 Waktu server: {data.get('timestamp')}")
                print(f"📡 Sensor terhubung: {data.get('connected_sensors')}")
                return True
            else:
                print("❌ API tidak merespons dengan benar")
                return False
        except Exception as e:
            print(f"❌ Tidak dapat terhubung ke API: {e}")
            return False
    
    def get_all_sensors(self):
        """Ambil data semua sensor"""
        try:
            response = requests.get(f"{self.api_url}/api/sensors/all", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Gagal mengambil data: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def get_sensor_data(self, sensor_id):
        """Ambil data sensor tertentu"""
        try:
            response = requests.get(f"{self.api_url}/api/sensor/data/{sensor_id}", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Sensor {sensor_id} tidak ditemukan")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def get_sensor_history(self, sensor_id, limit=10):
        """Ambil riwayat data sensor"""
        try:
            response = requests.get(f"{self.api_url}/api/sensor/history/{sensor_id}?limit={limit}", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Riwayat sensor {sensor_id} tidak ditemukan")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def get_api_status(self):
        """Ambil status API dan konektivitas"""
        try:
            response = requests.get(f"{self.api_url}/api/sensor/status", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                print("❌ Gagal mengambil status API")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def display_sensor_data(self, data):
        """Tampilkan data sensor dengan format yang rapi"""
        if not data or data.get('status') != 'success':
            print("❌ Tidak ada data sensor")
            return
        
        sensor_data = data.get('data', {})
        connected_sensors = data.get('connected_sensors', {})
        
        print("=" * 60)
        print("📊 DATA SENSOR REAL-TIME")
        print("=" * 60)
        
        if not sensor_data:
            print("📭 Belum ada data sensor")
            return
        
        for sensor_id, info in sensor_data.items():
            sensor_info = connected_sensors.get(sensor_id, {})
            sensor_name = sensor_info.get('sensor_name', sensor_id)
            
            print(f"\n🔹 {sensor_name} ({sensor_id})")
            print(f"   Jenis: {info.get('sensor_type')}")
            print(f"   Nilai: {info.get('value')} {info.get('unit')}")
            print(f"   Update: {info.get('timestamp')}")
            print(f"   Status: {'🟢 Aktif' if info.get('status') == 'active' else '🔴 Tidak Aktif'}")
        
        print(f"\n📈 Total sensor: {len(sensor_data)}")
        print(f"🕒 Update terakhir: {datetime.now().strftime('%H:%M:%S')}")
    
    def display_api_status(self, status_data):
        """Tampilkan status API dan konektivitas"""
        if not status_data or status_data.get('status') != 'success':
            print("❌ Gagal mendapatkan status API")
            return
        
        print("=" * 60)
        print("🔧 STATUS API & KONEKTIVITAS")
        print("=" * 60)
        
        print(f"🚀 Status API: {status_data.get('api_status')}")
        print(f"🕒 Waktu: {status_data.get('timestamp')}")
        print(f"📡 Total sensor terdaftar: {status_data.get('connected_sensors')}")
        print(f"🟢 Sensor aktif: {status_data.get('active_sensors')}")
        print(f"🔴 Sensor tidak aktif: {status_data.get('inactive_sensors')}")
        print(f"📊 Total data points: {status_data.get('total_data_points')}")
        
        sensors_info = status_data.get('sensors_info', {})
        if sensors_info:
            print("\n📋 Detail Sensor:")
            for sensor_id, info in sensors_info.items():
                status_icon = "🟢" if info.get('status') == 'active' else "🔴"
                print(f"   {status_icon} {info.get('sensor_name', sensor_id)} - {info.get('sensor_type')}")
                print(f"       Terhubung: {info.get('connected_at')}")
                print(f"       Update terakhir: {info.get('last_update')}")
    
    def start_monitoring(self, interval=5):
        """Mulai monitoring real-time"""
        self.monitoring = True
        print(f"🔄 Memulai monitoring real-time (update setiap {interval} detik)")
        print("📍 Tekan Ctrl+C untuk berhenti")
        
        try:
            while self.monitoring:
                # Clear screen (works on most terminals)
                print("\033[2J\033[H")
                
                # Tampilkan data sensor
                data = self.get_all_sensors()
                if data:
                    self.display_sensor_data(data)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.monitoring = False
            print("\n🛑 Monitoring dihentikan")
    
    def interactive_menu(self):
        """Menu interaktif untuk aplikasi"""
        while True:
            print("\n" + "=" * 60)
            print("📱 APLIKASI MONITORING SENSOR")
            print("=" * 60)
            print("1. Lihat data semua sensor")
            print("2. Lihat data sensor tertentu")
            print("3. Lihat riwayat sensor")
            print("4. Status API & konektivitas")
            print("5. Monitoring real-time")
            print("6. Test koneksi")
            print("0. Keluar")
            
            choice = input("\nPilih menu (0-6): ").strip()
            
            if choice == "1":
                print("\n🔄 Mengambil data semua sensor...")
                data = self.get_all_sensors()
                if data:
                    self.display_sensor_data(data)
                input("\nTekan Enter untuk melanjutkan...")
                
            elif choice == "2":
                sensor_id = input("Masukkan ID sensor: ").strip()
                if sensor_id:
                    print(f"\n🔄 Mengambil data sensor {sensor_id}...")
                    data = self.get_sensor_data(sensor_id)
                    if data and data.get('status') == 'success':
                        sensor_info = data.get('data')
                        print(f"\n📊 Data Sensor {sensor_id}:")
                        print(f"   Jenis: {sensor_info.get('sensor_type')}")
                        print(f"   Nilai: {sensor_info.get('value')} {sensor_info.get('unit')}")
                        print(f"   Update: {sensor_info.get('timestamp')}")
                        print(f"   Status: {sensor_info.get('status')}")
                input("\nTekan Enter untuk melanjutkan...")
                
            elif choice == "3":
                sensor_id = input("Masukkan ID sensor: ").strip()
                limit = input("Jumlah data (default 10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                
                if sensor_id:
                    print(f"\n🔄 Mengambil riwayat sensor {sensor_id}...")
                    data = self.get_sensor_history(sensor_id, limit)
                    if data and data.get('status') == 'success':
                        history = data.get('data', [])
                        print(f"\n📈 Riwayat {len(history)} data terakhir:")
                        for record in history:
                            print(f"   {record.get('timestamp')}: {record.get('value')} {record.get('unit')}")
                input("\nTekan Enter untuk melanjutkan...")
                
            elif choice == "4":
                print("\n🔄 Mengambil status API...")
                status = self.get_api_status()
                if status:
                    self.display_api_status(status)
                input("\nTekan Enter untuk melanjutkan...")
                
            elif choice == "5":
                interval = input("Interval update (detik, default 5): ").strip()
                interval = int(interval) if interval.isdigit() else 5
                self.start_monitoring(interval)
                
            elif choice == "6":
                print("\n🔄 Testing koneksi...")
                self.test_connection()
                input("\nTekan Enter untuk melanjutkan...")
                
            elif choice == "0":
                print("👋 Terima kasih!")
                break
                
            else:
                print("❌ Pilihan tidak valid")

if __name__ == '__main__':
    # Ganti dengan IP address perangkat yang menjalankan API
    # Contoh: "http://192.168.43.100:5000" untuk hotspot
    API_URL = "http://localhost:5000"
    
    print("📱 Aplikasi Client Sensor")
    print(f"🌐 Menghubungi API di: {API_URL}")
    
    app = SensorApp(API_URL)
    
    # Test koneksi awal
    if app.test_connection():
        print("\n🚀 Aplikasi siap digunakan!")
        app.interactive_menu()
    else:
        print("\n💡 Pastikan:")
        print("   - API server sudah berjalan")
        print("   - IP address sudah benar")
        print("   - Kedua perangkat di jaringan yang sama")
        print("   - Port 5000 tidak diblokir firewall")