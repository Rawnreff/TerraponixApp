# Terraponix Chart Implementation & MySQL Database Setup

## 📊 Overview

Implementasi ini menambahkan fitur visualisasi data sensor dalam bentuk chart/grafik yang interaktif dan mengubah database dari SQLite ke MySQL untuk performa dan skalabilitas yang lebih baik.

## 🎯 Fitur Baru

### 1. Visualisasi Data Sensor
- **Toggle View**: Bisa beralih antara tampilan Card dan Chart
- **Multiple Chart Types**: Line chart dan Bar chart
- **Real-time Data**: Grafik menampilkan 12 pembacaan terakhir
- **Statistics**: Menampilkan nilai current, average, max, dan min
- **Responsive Design**: Dapat di-scroll horizontal untuk layar kecil

### 2. Komponen Chart yang Dibuat
- `SensorChart.tsx`: Komponen chart individual untuk setiap sensor
- `SensorDashboard.tsx`: Dashboard utama dengan toggle antara cards dan charts

### 3. Database MySQL
- **Schema Lengkap**: Tabel untuk users, devices, sensor data, controls, alerts, dll
- **Indexing**: Optimasi performa dengan index yang tepat
- **Views**: View untuk query yang sering digunakan
- **Stored Procedures**: Fungsi untuk maintenance otomatis
- **Events**: Scheduled tasks untuk cleanup dan summary

## 🚀 Installation Guide

### Prerequisites
```bash
# Install MySQL Server
sudo apt update
sudo apt install mysql-server

# Start MySQL service
sudo systemctl start mysql
sudo systemctl enable mysql

# Secure MySQL installation (optional)
sudo mysql_secure_installation
```

### 1. Setup Database
```bash
# Navigate to database directory
cd database

# Make setup script executable
chmod +x setup_mysql.sh

# Run setup script
./setup_mysql.sh
```

Script ini akan:
- Membuat database `terraponix`
- Membuat user `terraponix_user`
- Import schema lengkap
- Setup environment variables
- Verify installation

### 2. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment
File `.env` akan dibuat otomatis oleh setup script dengan konfigurasi:
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=terraponix_user
MYSQL_PASSWORD=terraponix_password
MYSQL_DATABASE=terraponix
```

### 4. Update Backend Code
Backend perlu diupdate untuk menggunakan MySQL. Contoh perubahan dalam `app.py`:

```python
from mysql_config import SensorDataDB, DeviceDB, ControlDB, AlertDB, initialize_database

# Initialize database connection
if not initialize_database():
    print("Failed to initialize MySQL database")
    exit(1)

# Replace SQLite code with MySQL
@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.get_json()
        device_id = data.get('device_id', 1)
        
        # Insert using MySQL
        sensor_id = SensorDataDB.insert_sensor_data(device_id, data)
        
        # Update device heartbeat
        DeviceDB.update_device_heartbeat(
            device_id, 
            data.get('battery_level'), 
            data.get('solar_power')
        )
        
        return jsonify({'status': 'success', 'id': sensor_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/historical-data', methods=['GET'])
def get_historical_data():
    hours = request.args.get('hours', 24, type=int)
    limit = request.args.get('limit', 100, type=int)
    device_id = request.args.get('device_id', 1, type=int)
    
    data = SensorDataDB.get_historical_data(device_id, hours, limit)
    return jsonify(data)
```

## 📱 Frontend Implementation

### 1. Chart Components
Komponen `SensorChart` mendukung berbagai jenis chart:

```typescript
// Line Chart untuk temperature, humidity, pH, CO2
<SensorChart
  data={historicalData}
  title="Temperature"
  dataKey="temperature"
  color="#FF6B6B"
  unit="°C"
  chartType="line"
/>

// Bar Chart untuk TDS, soil moisture, water level
<SensorChart
  data={historicalData}
  title="TDS"
  dataKey="tds"
  color="#96CEB4"
  unit="ppm"
  chartType="bar"
/>
```

### 2. Dashboard Integration
Update halaman dashboard untuk menggunakan `SensorDashboard`:

```typescript
import SensorDashboard from '../../components/SensorDashboard';

// Replace existing sensor cards with dashboard
<SensorDashboard sensorData={sensorData} />
```

### 3. Chart Configuration
Setiap sensor memiliki konfigurasi chart yang dapat disesuaikan:

```typescript
const sensorConfigs = [
  {
    title: 'Temperature',
    dataKey: 'temperature',
    color: '#FF6B6B',
    unit: '°C',
    chartType: 'line',
    min: 20,
    max: 30
  },
  // ... other sensors
];
```

## 🗄️ Database Schema

### Tabel Utama

1. **devices**: Informasi ESP32 dan device lainnya
2. **sensor_data**: Data pembacaan sensor (tabel utama)
3. **control_settings**: Pengaturan otomatis
4. **alerts**: Sistem peringatan
5. **users**: Manajemen pengguna
6. **daily_sensor_summary**: Agregasi data harian

### Views
- `latest_sensor_readings`: Data sensor terbaru
- `active_alerts`: Alert yang belum diselesaikan
- `device_status`: Status koneksi device

### Stored Procedures
- `CleanOldData()`: Hapus data lama
- `GenerateDailySummary()`: Buat ringkasan harian

### Automatic Events
- `daily_summary_generation`: Jalankan setiap hari
- `weekly_data_cleanup`: Cleanup mingguan

## 📊 Chart Features

### 1. Interactive Charts
- **Zoom & Pan**: Chart dapat di-zoom dan di-pan
- **Tooltips**: Hover untuk melihat nilai detail
- **Animations**: Smooth transition saat data update

### 2. Statistics Display
- **Current Value**: Nilai pembacaan terakhir
- **Average**: Rata-rata dari semua data
- **Maximum**: Nilai tertinggi
- **Minimum**: Nilai terendah

### 3. Chart Types
- **Line Charts**: Untuk data kontinyu (temperature, humidity, pH, CO2)
- **Bar Charts**: Untuk data diskrit (TDS, soil moisture, water level)

## 🔧 Configuration

### Chart Styling
Charts menggunakan `react-native-chart-kit` dengan konfigurasi:
```typescript
const chartConfig = {
  backgroundGradientFrom: '#ffffff',
  backgroundGradientTo: '#ffffff',
  color: (opacity = 1) => color,
  strokeWidth: 2,
  decimalPlaces: 1,
  // ... other configs
};
```

### Database Connection Pooling
MySQL menggunakan connection pooling untuk performa:
```python
POOL_CONFIG = {
    'pool_name': 'terraponix_pool',
    'pool_size': 10,
    'pool_reset_session': True,
    'pool_timeout': 30,
}
```

## 🚀 Usage Examples

### 1. Menjalankan Aplikasi
```bash
# Start backend
cd backend
python app.py

# Start frontend (terminal baru)
cd ..
npm start
```

### 2. Mengakses Database
```bash
# Connect to MySQL
mysql -h localhost -u terraponix_user -pterraponix_password terraponix

# Query latest data
SELECT * FROM latest_sensor_readings;

# Query active alerts
SELECT * FROM active_alerts;
```

### 3. Backup Database
```bash
# Create backup
mysqldump -u terraponix_user -pterraponix_password terraponix > backup_$(date +%Y%m%d).sql

# Restore backup
mysql -u terraponix_user -pterraponix_password terraponix < backup_20241212.sql
```

## 🛠️ Troubleshooting

### Database Connection Issues
```bash
# Check MySQL service status
sudo systemctl status mysql

# Check MySQL logs
sudo tail -f /var/log/mysql/error.log

# Test connection
mysql -u terraponix_user -pterraponix_password -e "SELECT 1;"
```

### Chart Display Issues
1. **Charts not loading**: Check historical data API endpoint
2. **Empty charts**: Verify data format in database
3. **Performance issues**: Limit data points to 50-100

### Memory Issues
1. **Large datasets**: Use pagination in queries
2. **Chart performance**: Implement data decimation
3. **Database size**: Run cleanup procedures regularly

## 📈 Performance Optimization

### Database
- Index pada kolom yang sering di-query
- Connection pooling untuk concurrent access
- Regular cleanup old data
- Daily summary tables untuk reporting

### Frontend
- Lazy loading untuk historical data
- Chart data pagination
- Memoization untuk expensive calculations
- Virtualization untuk large datasets

## 🔒 Security

### Database Security
- Dedicated user dengan minimal privileges
- Password encryption
- Connection timeout
- SQL injection prevention

### API Security
- Input validation
- Rate limiting
- Error handling tanpa information disclosure
- CORS configuration

## 📚 Additional Resources

- [React Native Chart Kit Documentation](https://github.com/indiespirit/react-native-chart-kit)
- [MySQL Connector Python](https://dev.mysql.com/doc/connector-python/en/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [React Native Performance](https://reactnative.dev/docs/performance)

## 🔄 Migration from SQLite

Jika sudah ada data di SQLite, gunakan script migration:

```bash
# Export SQLite data
sqlite3 terraponix.db ".dump" > sqlite_export.sql

# Convert to MySQL format
sed 's/INTEGER PRIMARY KEY AUTOINCREMENT/INT AUTO_INCREMENT PRIMARY KEY/g' sqlite_export.sql > mysql_import.sql

# Import to MySQL
mysql -u terraponix_user -pterraponix_password terraponix < mysql_import.sql
```

## 📞 Support

Untuk pertanyaan atau masalah:
1. Check dokumentasi ini
2. Review error logs
3. Test dengan data sample
4. Verify database connections

---

**Happy Coding! 🚀**