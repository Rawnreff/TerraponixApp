"""
MySQL Database Configuration for Terraponix Application
"""

import mysql.connector
from mysql.connector import Error, pooling
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MySQL Database Configuration
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'terraponix_user'),
    'password': os.getenv('MYSQL_PASSWORD', 'terraponix_password'),
    'database': os.getenv('MYSQL_DATABASE', 'terraponix'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True,
    'raise_on_warnings': True
}

# Connection Pool Configuration
POOL_CONFIG = {
    'pool_name': 'terraponix_pool',
    'pool_size': 10,
    'pool_reset_session': True,
    'pool_timeout': 30,
    **MYSQL_CONFIG
}

# Global connection pool
connection_pool = None

def create_connection_pool():
    """Create MySQL connection pool"""
    global connection_pool
    try:
        connection_pool = pooling.MySQLConnectionPool(**POOL_CONFIG)
        logger.info("MySQL connection pool created successfully")
        return True
    except Error as e:
        logger.error(f"Error creating connection pool: {e}")
        return False

def get_connection():
    """Get connection from pool"""
    try:
        if connection_pool is None:
            create_connection_pool()
        return connection_pool.get_connection()
    except Error as e:
        logger.error(f"Error getting connection from pool: {e}")
        return None

def test_connection():
    """Test MySQL database connection"""
    try:
        connection = get_connection()
        if connection and connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            logger.info(f"Connected to MySQL Server version: {version[0]}")
            cursor.close()
            connection.close()
            return True
    except Error as e:
        logger.error(f"Error testing connection: {e}")
    return False

class MySQLDatabase:
    """MySQL Database handler class"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def __enter__(self):
        """Context manager entry"""
        self.connection = get_connection()
        if self.connection:
            self.cursor = self.connection.cursor(dictionary=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            if exc_type is not None:
                self.connection.rollback()
            else:
                self.connection.commit()
            self.connection.close()
    
    def execute_query(self, query, params=None):
        """Execute a SELECT query"""
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"Error executing query: {e}")
            return []
    
    def execute_single(self, query, params=None):
        """Execute a SELECT query and return single result"""
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except Error as e:
            logger.error(f"Error executing single query: {e}")
            return None
    
    def execute_insert(self, query, params=None):
        """Execute INSERT query and return last insert id"""
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.lastrowid
        except Error as e:
            logger.error(f"Error executing insert: {e}")
            return None
    
    def execute_update(self, query, params=None):
        """Execute UPDATE/DELETE query and return affected rows"""
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.rowcount
        except Error as e:
            logger.error(f"Error executing update: {e}")
            return 0

# Database operations for sensor data
class SensorDataDB:
    """Sensor data database operations"""
    
    @staticmethod
    def insert_sensor_data(device_id, data):
        """Insert sensor data into database"""
        with MySQLDatabase() as db:
            query = """
                INSERT INTO sensor_data (
                    device_id, temperature, humidity, ph, tds, 
                    light_intensity, co2, soil_moisture, water_level,
                    electrical_conductivity, dissolved_oxygen, 
                    water_temperature, ambient_pressure
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            params = (
                device_id,
                data.get('temperature'),
                data.get('humidity'),
                data.get('ph'),
                data.get('tds'),
                data.get('light_intensity'),
                data.get('co2'),
                data.get('soil_moisture'),
                data.get('water_level'),
                data.get('electrical_conductivity'),
                data.get('dissolved_oxygen'),
                data.get('water_temperature'),
                data.get('ambient_pressure')
            )
            return db.execute_insert(query, params)
    
    @staticmethod
    def get_latest_sensor_data(device_id=None):
        """Get latest sensor data"""
        with MySQLDatabase() as db:
            if device_id:
                query = """
                    SELECT * FROM sensor_data 
                    WHERE device_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                return db.execute_single(query, (device_id,))
            else:
                query = """
                    SELECT sd.*, d.device_name
                    FROM sensor_data sd
                    INNER JOIN devices d ON sd.device_id = d.id
                    INNER JOIN (
                        SELECT device_id, MAX(timestamp) as max_timestamp
                        FROM sensor_data
                        GROUP BY device_id
                    ) latest ON sd.device_id = latest.device_id 
                    AND sd.timestamp = latest.max_timestamp
                """
                return db.execute_query(query)
    
    @staticmethod
    def get_historical_data(device_id=None, hours=24, limit=100):
        """Get historical sensor data"""
        with MySQLDatabase() as db:
            if device_id:
                query = """
                    SELECT * FROM sensor_data 
                    WHERE device_id = %s 
                    AND timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """
                params = (device_id, hours, limit)
            else:
                query = """
                    SELECT sd.*, d.device_name
                    FROM sensor_data sd
                    INNER JOIN devices d ON sd.device_id = d.id
                    WHERE sd.timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                    ORDER BY sd.timestamp DESC 
                    LIMIT %s
                """
                params = (hours, limit)
            
            return db.execute_query(query, params)

# Database operations for devices
class DeviceDB:
    """Device database operations"""
    
    @staticmethod
    def update_device_heartbeat(device_id, battery_level=None, solar_power=None):
        """Update device heartbeat and status"""
        with MySQLDatabase() as db:
            query = """
                UPDATE devices 
                SET last_heartbeat = NOW()
            """
            params = []
            
            if battery_level is not None:
                query += ", battery_level = %s"
                params.append(battery_level)
            
            if solar_power is not None:
                query += ", solar_power = %s"
                params.append(solar_power)
            
            query += " WHERE id = %s"
            params.append(device_id)
            
            return db.execute_update(query, params)
    
    @staticmethod
    def get_device_status(device_id=None):
        """Get device status"""
        with MySQLDatabase() as db:
            if device_id:
                query = "SELECT * FROM device_status WHERE id = %s"
                return db.execute_single(query, (device_id,))
            else:
                query = "SELECT * FROM device_status"
                return db.execute_query(query)

# Database operations for control settings
class ControlDB:
    """Control settings database operations"""
    
    @staticmethod
    def get_control_settings(device_id=1):
        """Get control settings for device"""
        with MySQLDatabase() as db:
            query = """
                SELECT * FROM control_settings 
                WHERE device_id = %s 
                ORDER BY id DESC 
                LIMIT 1
            """
            return db.execute_single(query, (device_id,))
    
    @staticmethod
    def update_control_settings(device_id, settings):
        """Update control settings"""
        with MySQLDatabase() as db:
            # Build dynamic update query
            set_clauses = []
            params = []
            
            for key, value in settings.items():
                if key != 'id':  # Skip id field
                    set_clauses.append(f"{key} = %s")
                    params.append(value)
            
            if not set_clauses:
                return 0
            
            params.append(device_id)
            
            query = f"""
                UPDATE control_settings 
                SET {', '.join(set_clauses)}, updated_at = NOW()
                WHERE device_id = %s
            """
            
            return db.execute_update(query, params)
    
    @staticmethod
    def log_control_action(device_id, action_type, action, old_value, new_value, 
                          triggered_by='manual', user_id=None, reason=None):
        """Log control action"""
        with MySQLDatabase() as db:
            query = """
                INSERT INTO control_actions (
                    device_id, action_type, action, old_value, new_value,
                    triggered_by, user_id, reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (device_id, action_type, action, old_value, new_value,
                     triggered_by, user_id, reason)
            return db.execute_insert(query, params)

# Database operations for alerts
class AlertDB:
    """Alert database operations"""
    
    @staticmethod
    def create_alert(device_id, alert_type, severity, title, message, 
                    sensor_value=None, threshold_value=None):
        """Create new alert"""
        with MySQLDatabase() as db:
            query = """
                INSERT INTO alerts (
                    device_id, alert_type, severity, title, message,
                    sensor_value, threshold_value
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            params = (device_id, alert_type, severity, title, message,
                     sensor_value, threshold_value)
            return db.execute_insert(query, params)
    
    @staticmethod
    def get_active_alerts(device_id=None):
        """Get active alerts"""
        with MySQLDatabase() as db:
            if device_id:
                query = """
                    SELECT * FROM active_alerts 
                    WHERE device_id = %s
                    ORDER BY severity DESC, created_at DESC
                """
                return db.execute_query(query, (device_id,))
            else:
                query = """
                    SELECT * FROM active_alerts
                    ORDER BY severity DESC, created_at DESC
                """
                return db.execute_query(query)
    
    @staticmethod
    def acknowledge_alert(alert_id, user_id):
        """Acknowledge an alert"""
        with MySQLDatabase() as db:
            query = """
                UPDATE alerts 
                SET is_acknowledged = TRUE, acknowledged_by = %s, acknowledged_at = NOW()
                WHERE id = %s
            """
            return db.execute_update(query, (user_id, alert_id))

# Initialize database connection on import
def initialize_database():
    """Initialize database connection"""
    try:
        if create_connection_pool():
            if test_connection():
                logger.info("MySQL database initialized successfully")
                return True
            else:
                logger.error("Failed to test MySQL connection")
        else:
            logger.error("Failed to create MySQL connection pool")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    
    return False

# Export main classes and functions
__all__ = [
    'MySQLDatabase', 'SensorDataDB', 'DeviceDB', 'ControlDB', 'AlertDB',
    'initialize_database', 'test_connection'
]