"""
MySQL Database Configuration for Terraponix Application with XAMPP
"""

import mysql.connector
from mysql.connector import Error, pooling
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# XAMPP MySQL Database Configuration
XAMPP_MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),  # Default XAMPP user
    'password': os.getenv('MYSQL_PASSWORD', ''),  # Default XAMPP password (empty)
    'database': os.getenv('MYSQL_DATABASE', 'terraponix'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True,
    'raise_on_warnings': True
}

# Connection Pool Configuration for XAMPP
POOL_CONFIG = {
    'pool_name': 'terraponix_pool',
    'pool_size': 5,  # Reduced for XAMPP
    'pool_reset_session': True,
    'pool_timeout': 30,
    **XAMPP_MYSQL_CONFIG
}

# Global connection pool
connection_pool = None

def create_connection_pool():
    """Create MySQL connection pool for XAMPP"""
    global connection_pool
    try:
        connection_pool = pooling.MySQLConnectionPool(**POOL_CONFIG)
        logger.info("XAMPP MySQL connection pool created successfully")
        return True
    except Error as e:
        logger.error(f"Error creating XAMPP connection pool: {e}")
        return False

def get_connection():
    """Get connection from pool"""
    global connection_pool
    if connection_pool is None:
        if not create_connection_pool():
            return None
    
    try:
        return connection_pool.get_connection()
    except Error as e:
        logger.error(f"Error getting connection from pool: {e}")
        return None

def test_connection():
    """Test database connection"""
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            logger.info("XAMPP MySQL connection test successful")
            return True
        return False
    except Error as e:
        logger.error(f"XAMPP MySQL connection test failed: {e}")
        return False

def initialize_database():
    """Initialize database connection and create database if not exists"""
    try:
        # First, connect without specifying database to create it
        temp_config = XAMPP_MYSQL_CONFIG.copy()
        temp_config.pop('database', None)
        
        conn = mysql.connector.connect(**temp_config)
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {XAMPP_MYSQL_CONFIG['database']}")
        cursor.execute(f"USE {XAMPP_MYSQL_CONFIG['database']}")
        
        logger.info(f"Database {XAMPP_MYSQL_CONFIG['database']} ready")
        
        cursor.close()
        conn.close()
        
        # Now create the connection pool
        return create_connection_pool()
        
    except Error as e:
        logger.error(f"Error initializing XAMPP database: {e}")
        return False

class SensorDataDB:
    """Sensor Data Database Operations"""
    
    @staticmethod
    def create_tables():
        """Create sensor data tables"""
        conn = get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # Create devices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_id VARCHAR(100) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    location VARCHAR(255),
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    battery_level FLOAT,
                    solar_power FLOAT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create sensor_data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_id INT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    temperature FLOAT,
                    humidity FLOAT,
                    ph FLOAT,
                    tds FLOAT,
                    light_intensity FLOAT,
                    co2 FLOAT,
                    soil_moisture FLOAT,
                    water_level FLOAT,
                    FOREIGN KEY (device_id) REFERENCES devices(id)
                )
            """)
            
            # Create control_settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS control_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_id INT NOT NULL,
                    pump_auto BOOLEAN DEFAULT TRUE,
                    fan_auto BOOLEAN DEFAULT TRUE,
                    curtain_auto BOOLEAN DEFAULT TRUE,
                    pump_status BOOLEAN DEFAULT FALSE,
                    fan_status BOOLEAN DEFAULT FALSE,
                    curtain_status BOOLEAN DEFAULT FALSE,
                    temp_threshold_min FLOAT DEFAULT 20.0,
                    temp_threshold_max FLOAT DEFAULT 30.0,
                    humidity_threshold_min FLOAT DEFAULT 60.0,
                    humidity_threshold_max FLOAT DEFAULT 80.0,
                    ph_threshold_min FLOAT DEFAULT 5.5,
                    ph_threshold_max FLOAT DEFAULT 6.5,
                    tds_threshold_min FLOAT DEFAULT 300.0,
                    tds_threshold_max FLOAT DEFAULT 800.0,
                    soil_moisture_threshold_min FLOAT DEFAULT 40.0,
                    soil_moisture_threshold_max FLOAT DEFAULT 70.0,
                    water_level_threshold_min FLOAT DEFAULT 20.0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices(id)
                )
            """)
            
            # Insert default device if not exists
            cursor.execute("""
                INSERT IGNORE INTO devices (id, device_id, name, location) 
                VALUES (1, 'ESP32_001', 'Main Greenhouse', 'Greenhouse 1')
            """)
            
            # Insert default control settings if not exists
            cursor.execute("""
                INSERT IGNORE INTO control_settings (device_id) VALUES (1)
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("XAMPP MySQL tables created successfully")
            return True
            
        except Error as e:
            logger.error(f"Error creating tables: {e}")
            return False
    
    @staticmethod
    def insert_sensor_data(device_id, data):
        """Insert sensor data"""
        conn = get_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            
            query = """
                INSERT INTO sensor_data 
                (device_id, temperature, humidity, ph, tds, light_intensity, co2, soil_moisture, water_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                device_id,
                data.get('temperature'),
                data.get('humidity'),
                data.get('ph'),
                data.get('tds'),
                data.get('light_intensity'),
                data.get('co2'),
                data.get('soil_moisture'),
                data.get('water_level')
            )
            
            cursor.execute(query, values)
            sensor_id = cursor.lastrowid
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return sensor_id
            
        except Error as e:
            logger.error(f"Error inserting sensor data: {e}")
            return None
    
    @staticmethod
    def get_latest_data(device_id=1):
        """Get latest sensor data"""
        conn = get_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT * FROM sensor_data 
                WHERE device_id = %s 
                ORDER BY timestamp DESC 
                LIMIT 1
            """
            
            cursor.execute(query, (device_id,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return result
            
        except Error as e:
            logger.error(f"Error getting latest data: {e}")
            return None
    
    @staticmethod
    def get_historical_data(device_id=1, hours=24, limit=100):
        """Get historical sensor data for charts"""
        conn = get_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT * FROM sensor_data 
                WHERE device_id = %s 
                AND timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                ORDER BY timestamp DESC 
                LIMIT %s
            """
            
            cursor.execute(query, (device_id, hours, limit))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Convert timestamp to string for JSON serialization
            for row in results:
                if row['timestamp']:
                    row['timestamp'] = row['timestamp'].isoformat()
            
            return list(reversed(results))  # Return in chronological order
            
        except Error as e:
            logger.error(f"Error getting historical data: {e}")
            return []

class ControlDB:
    """Control Settings Database Operations"""
    
    @staticmethod
    def get_control_settings(device_id=1):
        """Get control settings"""
        conn = get_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = "SELECT * FROM control_settings WHERE device_id = %s"
            cursor.execute(query, (device_id,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return result
            
        except Error as e:
            logger.error(f"Error getting control settings: {e}")
            return None
    
    @staticmethod
    def update_control_settings(device_id, settings):
        """Update control settings"""
        conn = get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # Build dynamic update query
            set_clauses = []
            values = []
            
            for key, value in settings.items():
                if key != 'device_id':
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            if not set_clauses:
                return True
            
            values.append(device_id)
            
            query = f"""
                UPDATE control_settings 
                SET {', '.join(set_clauses)}
                WHERE device_id = %s
            """
            
            cursor.execute(query, values)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return True
            
        except Error as e:
            logger.error(f"Error updating control settings: {e}")
            return False

class DeviceDB:
    """Device Database Operations"""
    
    @staticmethod
    def update_device_heartbeat(device_id, battery_level=None, solar_power=None):
        """Update device heartbeat"""
        conn = get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            query = """
                UPDATE devices 
                SET last_seen = CURRENT_TIMESTAMP
            """
            values = []
            
            if battery_level is not None:
                query += ", battery_level = %s"
                values.append(battery_level)
            
            if solar_power is not None:
                query += ", solar_power = %s"
                values.append(solar_power)
            
            query += " WHERE id = %s"
            values.append(device_id)
            
            cursor.execute(query, values)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return True
            
        except Error as e:
            logger.error(f"Error updating device heartbeat: {e}")
            return False