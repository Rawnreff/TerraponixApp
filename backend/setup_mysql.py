#!/usr/bin/env python3
"""
MySQL Database Setup Script for Terraponix

This script helps set up the MySQL database for the Terraponix system.
It creates the database, tables, and initial data.
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import sys

load_dotenv()

def get_db_config():
    """Get database configuration from environment variables"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'charset': 'utf8mb4'
    }

def create_database():
    """Create the Terraponix database if it doesn't exist"""
    config = get_db_config()
    database_name = os.getenv('DB_NAME', 'terraponix')
    
    try:
        print("🔗 Connecting to MySQL server...")
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Create database
        print(f"🗃️  Creating database '{database_name}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        print(f"✅ Database '{database_name}' created successfully!")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Error as e:
        print(f"❌ Error creating database: {e}")
        return False

def create_tables():
    """Create all required tables"""
    config = get_db_config()
    config['database'] = os.getenv('DB_NAME', 'terraponix')
    
    try:
        print("📋 Creating tables...")
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Sensor data table
        print("   Creating sensor_data table...")
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
        print("   Creating control_settings table...")
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
        print("   Creating alerts table...")
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
        print("   Creating device_status table...")
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
        
        print("✅ All tables created successfully!")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Error as e:
        print(f"❌ Error creating tables: {e}")
        return False

def insert_initial_data():
    """Insert initial data into tables"""
    config = get_db_config()
    config['database'] = os.getenv('DB_NAME', 'terraponix')
    
    try:
        print("📝 Inserting initial data...")
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Insert default control settings
        cursor.execute('SELECT COUNT(*) FROM control_settings')
        result = cursor.fetchone()
        if result[0] == 0:
            print("   Adding default control settings...")
            cursor.execute('''
                INSERT INTO control_settings (
                    pump_auto, fan_auto, curtain_auto,
                    temp_threshold_min, temp_threshold_max,
                    humidity_threshold_min, humidity_threshold_max,
                    ph_threshold_min, ph_threshold_max
                ) VALUES (TRUE, TRUE, TRUE, 20.0, 30.0, 60.0, 80.0, 5.5, 6.5)
            ''')
        
        # Insert default device status
        cursor.execute('SELECT COUNT(*) FROM device_status')
        result = cursor.fetchone()
        if result[0] == 0:
            print("   Adding default device status...")
            cursor.execute('''
                INSERT INTO device_status (esp32_connected, battery_level, solar_power)
                VALUES (FALSE, 100, 0)
            ''')
        
        # Insert sample sensor data for testing
        cursor.execute('SELECT COUNT(*) FROM sensor_data')
        result = cursor.fetchone()
        if result[0] == 0:
            print("   Adding sample sensor data...")
            sample_data = [
                (25.5, 68.2, 6.1, 850, 75, 450, 82, 90),
                (24.8, 70.1, 6.0, 830, 78, 430, 85, 88),
                (26.2, 65.5, 6.2, 870, 72, 465, 80, 92),
                (25.0, 69.8, 6.1, 845, 76, 440, 83, 89),
                (25.8, 67.3, 6.0, 860, 74, 455, 81, 91)
            ]
            
            for data in sample_data:
                cursor.execute('''
                    INSERT INTO sensor_data 
                    (temperature, humidity, ph, tds, light_intensity, co2, soil_moisture, water_level)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', data)
        
        connection.commit()
        print("✅ Initial data inserted successfully!")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Error as e:
        print(f"❌ Error inserting initial data: {e}")
        return False

def test_connection():
    """Test database connection and display status"""
    config = get_db_config()
    config['database'] = os.getenv('DB_NAME', 'terraponix')
    
    try:
        print("🧪 Testing database connection...")
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Test queries
        cursor.execute("SELECT COUNT(*) FROM sensor_data")
        sensor_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM control_settings")
        control_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM alerts")
        alert_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM device_status")
        device_count = cursor.fetchone()[0]
        
        print("📊 Database Status:")
        print(f"   Sensor records: {sensor_count}")
        print(f"   Control settings: {control_count}")
        print(f"   Alerts: {alert_count}")
        print(f"   Device status: {device_count}")
        
        cursor.close()
        connection.close()
        
        print("✅ Database connection test successful!")
        return True
        
    except Error as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🌱 Terraponix MySQL Database Setup")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please create a .env file with your MySQL configuration:")
        print("DB_HOST=localhost")
        print("DB_PORT=3306")
        print("DB_USER=root")
        print("DB_PASSWORD=your_password")
        print("DB_NAME=terraponix")
        return False
    
    # Get database password if not set
    if not os.getenv('DB_PASSWORD'):
        password = input("Enter MySQL root password: ")
        # Update .env file with password
        with open('.env', 'a') as f:
            f.write(f"\nDB_PASSWORD={password}\n")
        os.environ['DB_PASSWORD'] = password
    
    success = True
    
    # Create database
    if not create_database():
        success = False
    
    # Create tables
    if success and not create_tables():
        success = False
    
    # Insert initial data
    if success and not insert_initial_data():
        success = False
    
    # Test connection
    if success and not test_connection():
        success = False
    
    if success:
        print("\n🎉 Database setup completed successfully!")
        print("You can now run the Terraponix backend server.")
        print("\nTo start the server:")
        print("python app.py")
    else:
        print("\n❌ Database setup failed!")
        print("Please check your MySQL configuration and try again.")
    
    return success

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)