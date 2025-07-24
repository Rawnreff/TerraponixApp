#!/bin/bash

# Terraponix XAMPP MySQL Database Setup Script
# This script creates the database and tables for XAMPP MySQL

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database configuration for XAMPP
DB_NAME="terraponix"
DB_USER="root"        # Default XAMPP MySQL user
DB_PASSWORD=""        # Default XAMPP MySQL password (empty)
DB_HOST="localhost"
DB_PORT="3306"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if XAMPP MySQL is running
check_xampp_mysql() {
    print_status "Checking XAMPP MySQL service..."
    
    # Check if MySQL process is running (XAMPP usually runs mysqld)
    if pgrep -x "mysqld" > /dev/null || pgrep -f "mysql" > /dev/null; then
        print_success "XAMPP MySQL service is running"
        return 0
    else
        print_error "XAMPP MySQL service is not running"
        print_status "Please start XAMPP and ensure MySQL is running"
        print_status "You can start XAMPP using:"
        print_status "  - XAMPP Control Panel (GUI)"
        print_status "  - sudo /opt/lampp/lampp start (Linux)"
        print_status "  - sudo /Applications/XAMPP/xamppfiles/mampp start (macOS)"
        return 1
    fi
}

# Function to test MySQL connection
test_mysql_connection() {
    print_status "Testing XAMPP MySQL connection..."
    
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -e "SELECT 1;" 2>/dev/null; then
        print_success "Successfully connected to XAMPP MySQL"
        return 0
    else
        print_error "Failed to connect to XAMPP MySQL"
        print_status "Please ensure:"
        print_status "  - XAMPP is running"
        print_status "  - MySQL service is started in XAMPP Control Panel"
        print_status "  - MySQL is accessible on port $DB_PORT"
        return 1
    fi
}

# Function to create database
create_database() {
    print_status "Creating database '$DB_NAME'..."
    
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Database '$DB_NAME' created successfully"
        return 0
    else
        print_error "Failed to create database '$DB_NAME'"
        return 1
    fi
}

# Function to create tables
create_tables() {
    print_status "Creating tables in database '$DB_NAME'..."
    
    # SQL script to create tables
    SQL_SCRIPT="
    USE $DB_NAME;

    -- Create devices table
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
    ) ENGINE=InnoDB;

    -- Create sensor_data table
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
        INDEX idx_device_timestamp (device_id, timestamp),
        INDEX idx_timestamp (timestamp),
        FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;

    -- Create control_settings table
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
        UNIQUE KEY unique_device_settings (device_id),
        FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;

    -- Insert default device if not exists
    INSERT IGNORE INTO devices (id, device_id, name, location) 
    VALUES (1, 'ESP32_001', 'Main Greenhouse', 'Greenhouse 1');

    -- Insert default control settings if not exists
    INSERT IGNORE INTO control_settings (device_id) VALUES (1);

    -- Create view for latest sensor readings
    CREATE OR REPLACE VIEW latest_sensor_readings AS
    SELECT 
        d.device_id,
        d.name as device_name,
        d.location,
        s.*
    FROM devices d
    LEFT JOIN sensor_data s ON d.id = s.device_id
    WHERE s.id = (
        SELECT MAX(s2.id) 
        FROM sensor_data s2 
        WHERE s2.device_id = d.id
    )
    OR s.id IS NULL;
    "
    
    # Execute SQL script
    if echo "$SQL_SCRIPT" | mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" 2>/dev/null; then
        print_success "Tables created successfully in XAMPP MySQL"
        return 0
    else
        print_error "Failed to create tables"
        return 1
    fi
}

# Function to insert sample data
insert_sample_data() {
    print_status "Inserting sample sensor data..."
    
    SAMPLE_DATA_SQL="
    USE $DB_NAME;
    
    -- Insert some sample sensor data for testing charts
    INSERT INTO sensor_data (device_id, timestamp, temperature, humidity, ph, tds, light_intensity, co2, soil_moisture, water_level) VALUES
    (1, DATE_SUB(NOW(), INTERVAL 60 MINUTE), 25.5, 70.2, 6.1, 350.0, 800.0, 420.0, 65.0, 75.0),
    (1, DATE_SUB(NOW(), INTERVAL 50 MINUTE), 26.1, 68.5, 6.0, 365.0, 820.0, 430.0, 62.0, 74.0),
    (1, DATE_SUB(NOW(), INTERVAL 40 MINUTE), 26.8, 65.8, 5.9, 380.0, 850.0, 445.0, 58.0, 73.0),
    (1, DATE_SUB(NOW(), INTERVAL 30 MINUTE), 27.2, 63.2, 5.8, 395.0, 890.0, 460.0, 55.0, 72.0),
    (1, DATE_SUB(NOW(), INTERVAL 20 MINUTE), 27.8, 61.5, 5.7, 410.0, 920.0, 475.0, 52.0, 71.0),
    (1, DATE_SUB(NOW(), INTERVAL 10 MINUTE), 28.1, 59.8, 5.6, 425.0, 940.0, 490.0, 49.0, 70.0),
    (1, NOW(), 28.5, 58.2, 5.5, 440.0, 960.0, 505.0, 46.0, 69.0);
    "
    
    if echo "$SAMPLE_DATA_SQL" | mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" 2>/dev/null; then
        print_success "Sample data inserted for chart testing"
        return 0
    else
        print_warning "Could not insert sample data (this is optional)"
        return 0
    fi
}

# Function to create environment file
create_env_file() {
    print_status "Creating environment configuration file..."
    
    ENV_FILE="../backend/.env"
    
    cat > "$ENV_FILE" << EOF
# XAMPP MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=terraponix

# Application Settings
FLASK_ENV=development
FLASK_DEBUG=true
EOF
    
    if [ $? -eq 0 ]; then
        print_success "Environment file created at: $ENV_FILE"
        return 0
    else
        print_error "Failed to create environment file"
        return 1
    fi
}

# Function to verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    # Test database connection and count records
    RECORD_COUNT=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -D "$DB_NAME" -se "SELECT COUNT(*) FROM sensor_data;" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        print_success "Database verification successful"
        print_status "Found $RECORD_COUNT sensor data records"
        
        # Show table status
        print_status "Database tables:"
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -D "$DB_NAME" -e "SHOW TABLES;" 2>/dev/null | while read table; do
            if [ "$table" != "Tables_in_$DB_NAME" ]; then
                COUNT=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -D "$DB_NAME" -se "SELECT COUNT(*) FROM $table;" 2>/dev/null)
                print_status "  - $table: $COUNT records"
            fi
        done
        
        return 0
    else
        print_error "Database verification failed"
        return 1
    fi
}

# Main installation function
main() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}Terraponix XAMPP MySQL Setup${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    
    # Check if XAMPP MySQL is running
    if ! check_xampp_mysql; then
        exit 1
    fi
    
    # Test MySQL connection
    if ! test_mysql_connection; then
        exit 1
    fi
    
    # Create database
    if ! create_database; then
        exit 1
    fi
    
    # Create tables
    if ! create_tables; then
        exit 1
    fi
    
    # Insert sample data for testing
    insert_sample_data
    
    # Create environment file
    if ! create_env_file; then
        exit 1
    fi
    
    # Verify installation
    if ! verify_installation; then
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}Setup Complete!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    print_success "XAMPP MySQL database is ready for Terraponix"
    print_status "Database: $DB_NAME"
    print_status "Host: $DB_HOST:$DB_PORT"
    print_status "User: $DB_USER"
    echo ""
    print_status "Next steps:"
    print_status "1. Install Python dependencies:"
    print_status "   cd ../backend && pip install -r requirements_xampp.txt"
    print_status ""
    print_status "2. Start the server:"
    print_status "   python app_mysql.py"
    echo ""
    print_status "3. Access the application:"
    print_status "   http://localhost:5000/api/database-status"
    echo ""
    print_status "📊 Charts will now use MySQL data from XAMPP!"
}

# Check if script is run from correct directory
if [ ! -f "terraponix_mysql.sql" ]; then
    print_error "Please run this script from the database directory"
    print_status "Usage: cd database && ./setup_xampp_mysql.sh"
    exit 1
fi

# Run main function
main