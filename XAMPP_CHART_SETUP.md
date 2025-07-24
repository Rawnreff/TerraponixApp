# 📊 Terraponix Chart Implementation dengan XAMPP MySQL

## 🎯 Overview

Panduan ini akan mengubah implementasi chart dari SQLite ke MySQL yang berjalan di XAMPP. Chart akan menggunakan data historis dari database MySQL untuk visualisasi yang lebih baik dan performa yang optimal.

## 🔧 Prerequisites

### 1. Install XAMPP
Download dan install XAMPP dari [https://www.apachefriends.org/](https://www.apachefriends.org/)

**Windows:**
- Download XAMPP installer
- Run installer sebagai Administrator
- Install di `C:\xampp\` (default)

**Linux:**
```bash
# Download XAMPP for Linux
wget https://www.apachefriends.org/xampp-files/8.2.12/xampp-linux-x64-8.2.12-0-installer.run

# Make executable
chmod +x xampp-linux-x64-8.2.12-0-installer.run

# Install (as root)
sudo ./xampp-linux-x64-8.2.12-0-installer.run
```

**macOS:**
- Download XAMPP .dmg file
- Mount and run installer
- Install di `/Applications/XAMPP/`

### 2. Start XAMPP Services
Buka XAMPP Control Panel dan start:
- ✅ Apache
- ✅ MySQL

## 🚀 Installation Steps

### Step 1: Setup Database
```bash
# Navigate to database directory
cd database

# Make setup script executable (Linux/macOS)
chmod +x setup_xampp_mysql.sh

# Run XAMPP setup script
./setup_xampp_mysql.sh
```

**Windows (Git Bash atau WSL):**
```bash
bash setup_xampp_mysql.sh
```

### Step 2: Install Python Dependencies
```bash
# Navigate to backend directory
cd backend

# Install XAMPP-specific requirements
pip install -r requirements_xampp.txt
```

### Step 3: Start Backend Server
```bash
# Use the XAMPP MySQL version
python app_mysql.py
```

## 📝 Konfigurasi Manual (Jika Diperlukan)

### 1. MySQL Connection Settings
File: `backend/.env`
```env
# XAMPP MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=terraponix
```

### 2. Manual Database Setup (Alternative)
Jika script otomatis gagal, bisa setup manual via phpMyAdmin:

1. Buka `http://localhost/phpmyadmin`
2. Create database `terraponix`
3. Import file `database/terraponix_mysql.sql`

### 3. Test Database Connection
```bash
# Test via command line
mysql -u root -h localhost -e "USE terraponix; SHOW TABLES;"

# Test via API
curl http://localhost:5000/api/database-status
```

## 📊 Chart Features dengan XAMPP MySQL

### 1. Real-time Data Visualization
- **Historical Data**: Chart menggunakan data dari MySQL
- **Performance**: Lebih cepat dengan indexing MySQL
- **Scalability**: Dapat handle lebih banyak data

### 2. Chart Types yang Tersedia
```typescript
// Line Charts untuk data kontinyu
- Temperature Over Time
- Humidity Trends  
- pH Levels
- CO2 Concentration

// Bar Charts untuk data diskrit
- TDS Values
- Soil Moisture
- Water Levels
- Light Intensity
```

### 3. Data Query Optimization
```sql
-- Query yang dioptimasi untuk charts
SELECT * FROM sensor_data 
WHERE device_id = 1 
AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY timestamp DESC 
LIMIT 100;

-- Index untuk performa
CREATE INDEX idx_device_timestamp ON sensor_data(device_id, timestamp);
```

## 🔄 API Endpoints untuk Charts

### 1. Historical Data untuk Charts
```http
GET /api/historical-data?hours=24&limit=100&device_id=1
```

Response:
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "timestamp": "2024-12-12T10:30:00",
      "temperature": 25.5,
      "humidity": 70.2,
      "ph": 6.1,
      "tds": 350.0,
      "light_intensity": 800.0,
      "co2": 420.0,
      "soil_moisture": 65.0,
      "water_level": 75.0
    }
  ],
  "count": 50
}
```

### 2. Database Status
```http
GET /api/database-status
```

Response:
```json
{
  "status": "connected",
  "database": "MySQL (XAMPP)",
  "last_reading": "2024-12-12T10:30:00",
  "message": "XAMPP MySQL connection active"
}
```

### 3. Current Sensor Data
```http
GET /api/sensor-data
```

## 🛠️ Troubleshooting

### ❌ XAMPP MySQL Not Starting
**Problem:** MySQL service fails to start

**Solution:**
1. Check if port 3306 is used by another service
2. Stop other MySQL services
3. Reset MySQL data directory
4. Check XAMPP error logs

```bash
# Windows - Check port usage
netstat -ano | findstr :3306

# Linux/macOS - Check port usage  
lsof -i :3306

# Stop conflicting MySQL service (Linux)
sudo systemctl stop mysql
```

### ❌ Connection Refused Error
**Problem:** `mysql.connector.errors.InterfaceError: 2003`

**Solutions:**
1. **Check XAMPP Status:**
   - Open XAMPP Control Panel
   - Ensure MySQL is running (green status)

2. **Verify MySQL Port:**
   ```bash
   # Test connection
   mysql -u root -h localhost -P 3306 -e "SELECT 1;"
   ```

3. **Reset MySQL Password:**
   ```sql
   -- In phpMyAdmin or MySQL command line
   ALTER USER 'root'@'localhost' IDENTIFIED BY '';
   FLUSH PRIVILEGES;
   ```

### ❌ Database Creation Failed
**Problem:** Cannot create `terraponix` database

**Manual Solution:**
1. Open phpMyAdmin: `http://localhost/phpmyadmin`
2. Click "New" to create database
3. Name: `terraponix`
4. Collation: `utf8mb4_unicode_ci`
5. Click "Create"

### ❌ Python Dependencies Error
**Problem:** `ModuleNotFoundError: No module named 'mysql.connector'`

**Solution:**
```bash
# Install MySQL connector
pip install mysql-connector-python

# Or install all requirements
pip install -r requirements_xampp.txt
```

### ❌ Charts Not Loading
**Problem:** Charts show empty or loading state

**Diagnostic Steps:**
1. **Check API Response:**
   ```bash
   curl http://localhost:5000/api/historical-data
   ```

2. **Verify Sample Data:**
   ```sql
   USE terraponix;
   SELECT COUNT(*) FROM sensor_data;
   SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 5;
   ```

3. **Check Browser Console:**
   - Open Developer Tools (F12)
   - Look for JavaScript errors
   - Check Network tab for failed API calls

## 📈 Performance Optimization

### 1. Database Optimization
```sql
-- Add indexes for better query performance
CREATE INDEX idx_timestamp ON sensor_data(timestamp);
CREATE INDEX idx_device_timestamp ON sensor_data(device_id, timestamp);

-- Optimize table
OPTIMIZE TABLE sensor_data;

-- Check table status
SHOW TABLE STATUS WHERE Name = 'sensor_data';
```

### 2. Connection Pool Settings
File: `backend/xampp_mysql_config.py`
```python
POOL_CONFIG = {
    'pool_name': 'terraponix_pool',
    'pool_size': 5,  # Reduced for XAMPP
    'pool_reset_session': True,
    'pool_timeout': 30,
}
```

### 3. Data Cleanup (Optional)
```sql
-- Remove old data (older than 30 days)
DELETE FROM sensor_data 
WHERE timestamp < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Reset auto-increment
ALTER TABLE sensor_data AUTO_INCREMENT = 1;
```

## 🎨 Frontend Chart Integration

### 1. Chart Component Usage
```typescript
import SensorDashboard from '../components/SensorDashboard';

// Replace existing sensor display with dashboard
<SensorDashboard 
  sensorData={sensorData}
  showCharts={true} 
/>
```

### 2. Chart Configuration
```typescript
const chartConfigs = [
  {
    title: 'Temperature',
    dataKey: 'temperature',
    color: '#FF6B6B',
    unit: '°C',
    chartType: 'line'
  },
  {
    title: 'Humidity', 
    dataKey: 'humidity',
    color: '#4ECDC4',
    unit: '%',
    chartType: 'line'
  },
  {
    title: 'Soil Moisture',
    dataKey: 'soil_moisture', 
    color: '#96CEB4',
    unit: '%',
    chartType: 'bar'
  }
];
```

## 📱 Testing Charts

### 1. Insert Test Data
```bash
# Via API (if ESP32 not available)
curl -X POST http://localhost:5000/api/sensor-data \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 26.5,
    "humidity": 65.0,
    "ph": 6.0,
    "tds": 380.0,
    "light_intensity": 850.0,
    "co2": 450.0,
    "soil_moisture": 60.0,
    "water_level": 72.0
  }'
```

### 2. View Charts
1. Start backend: `python app_mysql.py`
2. Start frontend: `npm start`
3. Navigate to dashboard
4. Toggle between Card and Chart view

## 📚 Migration dari SQLite

Jika sudah ada data di SQLite:

### 1. Export SQLite Data
```bash
# Export existing SQLite data
sqlite3 terraponix.db ".dump" > sqlite_export.sql
```

### 2. Convert untuk MySQL
```bash
# Convert SQLite SQL to MySQL format
sed -i 's/INTEGER PRIMARY KEY AUTOINCREMENT/INT AUTO_INCREMENT PRIMARY KEY/g' sqlite_export.sql
sed -i 's/AUTOINCREMENT/AUTO_INCREMENT/g' sqlite_export.sql
sed -i 's/BOOLEAN/TINYINT(1)/g' sqlite_export.sql
```

### 3. Import ke MySQL
```bash
# Import to XAMPP MySQL
mysql -u root -h localhost terraponix < sqlite_export.sql
```

## 🔒 Security (Optional)

### 1. Create Dedicated User
```sql
-- Create user for application
CREATE USER 'terraponix_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON terraponix.* TO 'terraponix_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Update Configuration
```env
MYSQL_USER=terraponix_user
MYSQL_PASSWORD=your_password
```

## ✅ Verification Checklist

- [ ] XAMPP MySQL is running
- [ ] Database `terraponix` exists
- [ ] Tables are created (devices, sensor_data, control_settings)
- [ ] Sample data is inserted
- [ ] Backend connects to MySQL successfully
- [ ] API endpoints return data
- [ ] Charts display historical data
- [ ] Real-time updates work

## 📞 Support

Jika mengalami masalah:

1. **Check XAMPP Status**: Pastikan MySQL service berjalan
2. **Verify Connection**: Test dengan `mysql -u root -h localhost`
3. **Check Logs**: Lihat error logs di XAMPP Control Panel
4. **API Testing**: Test endpoints dengan curl atau Postman
5. **Browser Console**: Check for JavaScript errors

---

**🎉 Selamat! Chart implementation dengan XAMPP MySQL sudah siap digunakan! 📊**