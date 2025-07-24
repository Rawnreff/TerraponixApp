# 📡 API Konektivitas Sensor - Hotspot Seluler

API sederhana untuk menghubungkan sensor dengan aplikasi menggunakan hotspot seluler sebagai penghubung jaringan.

## 🚀 Fitur Utama

- ✅ **REST API** lengkap untuk komunikasi sensor-aplikasi
- 📊 **Real-time monitoring** data sensor
- 💾 **Penyimpanan data** dengan SQLite database
- 🔄 **Auto-reconnection** untuk sensor yang terputus
- 📱 **Cross-platform** - berjalan di Windows, Linux, macOS
- 🌐 **Hotspot friendly** - dirancang untuk jaringan seluler

## 📋 Persyaratan

### Software
- Python 3.7 atau lebih baru
- pip (package manager Python)

### Hardware
- Perangkat dengan Python (untuk API server)
- Sensor/perangkat IoT (untuk mengirim data)
- Smartphone dengan hotspot (sebagai router)

## 🛠️ Instalasi

### 1. Clone atau Download Project
```bash
# Jika menggunakan git
git clone <repository-url>
cd sensor-api

# Atau download dan extract file
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## 🔧 Penggunaan

### 📡 1. Menjalankan API Server

#### Opsi A: Menjalankan di Laptop/PC (Recommended)
```bash
python sensor_api.py
```

API akan berjalan di: `http://0.0.0.0:5000`

#### Opsi B: Menjalankan di Raspberry Pi/Linux
```bash
python3 sensor_api.py
```

### 📱 2. Setup Hotspot Seluler

1. **Aktifkan hotspot** di smartphone Anda
2. **Hubungkan semua perangkat** ke hotspot yang sama:
   - Perangkat yang menjalankan API server
   - Perangkat sensor/IoT
   - Perangkat aplikasi client

3. **Cari IP address** perangkat API server:
   ```bash
   # Di Linux/macOS
   ip addr show
   
   # Di Windows
   ipconfig
   ```
   
   Contoh IP: `192.168.43.100` (hotspot biasanya 192.168.43.x)

### 🌡️ 3. Menjalankan Sensor Client

Edit file `sensor_client.py`, ganti IP address:
```python
API_URL = "http://192.168.43.100:5000"  # Ganti dengan IP server Anda
```

Jalankan sensor client:
```bash
python sensor_client.py
```

Pilih jenis sensor:
- **1** = Simulasi sensor suhu
- **2** = Simulasi sensor kelembaban  
- **3** = Input manual sensor custom

### 📱 4. Menjalankan Aplikasi Client

Edit file `app_client.py`, ganti IP address:
```python
API_URL = "http://192.168.43.100:5000"  # Ganti dengan IP server Anda
```

Jalankan aplikasi:
```bash
python app_client.py
```

Menu aplikasi:
1. **Lihat data semua sensor** - Tampilkan semua sensor aktif
2. **Lihat data sensor tertentu** - Data sensor spesifik
3. **Lihat riwayat sensor** - Histori data sensor
4. **Status API & konektivitas** - Info status sistem
5. **Monitoring real-time** - Update otomatis setiap N detik
6. **Test koneksi** - Cek koneksi ke API

## 🔌 API Endpoints

### Status & Info
- `GET /` - Status API server
- `GET /api/sensor/status` - Status lengkap & konektivitas

### Sensor Management
- `POST /api/sensor/register` - Registrasi sensor baru
- `POST /api/sensor/data` - Kirim data sensor
- `GET /api/sensor/data/{sensor_id}` - Ambil data sensor terbaru

### Data Retrieval
- `GET /api/sensors/all` - Ambil data semua sensor
- `GET /api/sensor/history/{sensor_id}?limit=N` - Riwayat data sensor

## 📊 Format Data

### Registrasi Sensor
```json
POST /api/sensor/register
{
    "sensor_id": "TEMP_001",
    "sensor_type": "temperature",
    "sensor_name": "Sensor Suhu Ruangan"
}
```

### Kirim Data Sensor
```json
POST /api/sensor/data
{
    "sensor_id": "TEMP_001",
    "sensor_type": "temperature", 
    "value": 25.5,
    "unit": "°C"
}
```

### Response Data
```json
{
    "status": "success",
    "data": {
        "sensor_type": "temperature",
        "value": 25.5,
        "unit": "°C",
        "timestamp": "2024-01-15T10:30:45.123456",
        "status": "active"
    }
}
```

## 🔍 Troubleshooting

### ❌ Tidak bisa terhubung ke API

1. **Cek IP address**
   ```bash
   # Cari IP perangkat server
   ip addr show wlan0  # Linux
   ipconfig            # Windows
   ```

2. **Pastikan semua perangkat di jaringan sama**
   - Semua terhubung ke hotspot yang sama
   - IP dalam range yang sama (192.168.43.x)

3. **Test koneksi manual**
   ```bash
   # Ping server dari perangkat lain
   ping 192.168.43.100
   
   # Cek port dengan curl
   curl http://192.168.43.100:5000/
   ```

### ❌ Sensor tidak terdeteksi

1. **Cek log API server** - Lihat pesan error di terminal
2. **Verifikasi format data** - Pastikan JSON sesuai format
3. **Cek registrasi sensor** - Sensor harus terdaftar dulu

### ❌ Data tidak update

1. **Cek timestamp** - Bandingkan dengan waktu sekarang
2. **Restart sensor client** - Kadang perlu reconnect
3. **Lihat status sensor** - Gunakan endpoint `/api/sensor/status`

## 🔒 Keamanan

- API **tidak menggunakan autentikasi** (untuk kemudahan development)
- Pastikan hotspot menggunakan **password yang kuat**
- Jangan expose ke internet public
- Gunakan hanya di jaringan private/lokal

## 📈 Pengembangan Lanjutan

### Menambah Jenis Sensor Baru
1. Edit `sensor_client.py` - Tambah fungsi simulasi baru
2. Tidak perlu ubah API server (sudah generic)

### Menambah Fitur Notifikasi
```python
# Contoh: Alert jika suhu > 30°C
if sensor_data['value'] > 30:
    send_notification("Suhu tinggi!")
```

### Integrasi dengan Database External
Ganti SQLite dengan MySQL/PostgreSQL di `sensor_api.py`

## 🤝 Kontribusi

Silakan buat pull request atau issue untuk:
- Bug fixes
- Fitur baru
- Dokumentasi
- Optimisasi performa

## 📄 Lisensi

Project ini bersifat open source untuk tujuan edukasi dan development.

---

## 🚀 Quick Start

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Start API server**: `python sensor_api.py`
3. **Get server IP**: Check hotspot connected devices
4. **Update client files**: Change `API_URL` in both client files
5. **Run sensor**: `python sensor_client.py`
6. **Run app**: `python app_client.py`

**✅ Selesai!** Sensor dan aplikasi sekarang terhubung melalui hotspot seluler.

## 📞 Support

Jika ada pertanyaan atau masalah, silakan:
1. Cek troubleshooting guide di atas
2. Buat issue di repository
3. Hubungi developer

**Happy coding! 🎉**
