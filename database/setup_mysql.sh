#!/bin/bash

# Terraponix MySQL Database Setup Script
# This script creates the database, user, and imports the schema

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database configuration
DB_NAME="terraponix"
DB_USER="terraponix_user"
DB_PASSWORD="terraponix_password"
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

# Function to check if MySQL is running
check_mysql() {
    print_status "Checking MySQL service..."
    if ! systemctl is-active --quiet mysql && ! systemctl is-active --quiet mysqld; then
        print_error "MySQL service is not running"
        print_status "Attempting to start MySQL..."
        if sudo systemctl start mysql 2>/dev/null || sudo systemctl start mysqld 2>/dev/null; then
            print_success "MySQL service started"
        else
            print_error "Failed to start MySQL service"
            print_status "Please start MySQL manually and run this script again"
            exit 1
        fi
    else
        print_success "MySQL service is running"
    fi
}

# Function to prompt for MySQL root password
get_mysql_root_password() {
    echo -n "Enter MySQL root password: "
    read -s MYSQL_ROOT_PASSWORD
    echo
}

# Function to test MySQL connection
test_mysql_connection() {
    print_status "Testing MySQL connection..."
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"$MYSQL_ROOT_PASSWORD" -e "SELECT 1;" > /dev/null 2>&1; then
        print_success "MySQL connection successful"
        return 0
    else
        print_error "Failed to connect to MySQL"
        return 1
    fi
}

# Function to create database and user
setup_database() {
    print_status "Creating database and user..."
    
    mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"$MYSQL_ROOT_PASSWORD" << EOF
-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user if it doesn't exist
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';

-- Grant privileges
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'%';

-- Flush privileges
FLUSH PRIVILEGES;

-- Show created database
SHOW DATABASES LIKE '$DB_NAME';
EOF

    if [ $? -eq 0 ]; then
        print_success "Database and user created successfully"
    else
        print_error "Failed to create database and user"
        exit 1
    fi
}

# Function to import schema
import_schema() {
    print_status "Importing database schema..."
    
    # Get the directory where this script is located
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    SCHEMA_FILE="$SCRIPT_DIR/terraponix_mysql.sql"
    
    if [ ! -f "$SCHEMA_FILE" ]; then
        print_error "Schema file not found: $SCHEMA_FILE"
        exit 1
    fi
    
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" < "$SCHEMA_FILE"; then
        print_success "Schema imported successfully"
    else
        print_error "Failed to import schema"
        exit 1
    fi
}

# Function to verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    # Check if tables were created
    TABLE_COUNT=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -D "$DB_NAME" -e "SHOW TABLES;" | wc -l)
    
    if [ "$TABLE_COUNT" -gt 1 ]; then
        print_success "Database tables created successfully"
        print_status "Total tables created: $((TABLE_COUNT - 1))"
    else
        print_error "No tables found in database"
        exit 1
    fi
    
    # Test data insertion
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -D "$DB_NAME" << EOF
INSERT INTO sensor_data (device_id, temperature, humidity, ph, tds, light_intensity, co2, soil_moisture, water_level) 
VALUES (1, 25.5, 70.2, 6.1, 950.0, 30000.0, 400.0, 65.0, 80.0);
EOF

    if [ $? -eq 0 ]; then
        print_success "Test data insertion successful"
        
        # Clean up test data
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" -D "$DB_NAME" -e "DELETE FROM sensor_data WHERE temperature = 25.5;"
        print_status "Test data cleaned up"
    else
        print_warning "Test data insertion failed, but database structure is correct"
    fi
}

# Function to create environment file
create_env_file() {
    print_status "Creating environment configuration..."
    
    ENV_FILE="../backend/.env"
    
    cat > "$ENV_FILE" << EOF
# MySQL Database Configuration
MYSQL_HOST=$DB_HOST
MYSQL_PORT=$DB_PORT
MYSQL_USER=$DB_USER
MYSQL_PASSWORD=$DB_PASSWORD
MYSQL_DATABASE=$DB_NAME

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=$(openssl rand -hex 32)

# Application Settings
DEFAULT_DEVICE_ID=1
DATA_RETENTION_DAYS=365
ALERT_CHECK_INTERVAL=60

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=terraponix.log
EOF
    
    if [ $? -eq 0 ]; then
        print_success "Environment file created: $ENV_FILE"
    else
        print_warning "Failed to create environment file"
    fi
}

# Function to show connection info
show_connection_info() {
    print_success "Setup completed successfully!"
    echo
    echo "Database Connection Information:"
    echo "================================"
    echo "Host: $DB_HOST"
    echo "Port: $DB_PORT"
    echo "Database: $DB_NAME"
    echo "Username: $DB_USER"
    echo "Password: $DB_PASSWORD"
    echo
    echo "To connect to the database:"
    echo "mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD $DB_NAME"
    echo
    echo "Environment file created at: ../backend/.env"
    echo "You can now start your Flask application!"
}

# Main execution
main() {
    echo "Terraponix MySQL Database Setup"
    echo "==============================="
    echo
    
    # Check if running as root for system operations
    if [ "$EUID" -ne 0 ] && ! groups | grep -q mysql; then
        print_warning "You may need sudo privileges for some operations"
    fi
    
    # Check MySQL service
    check_mysql
    
    # Get MySQL root password
    get_mysql_root_password
    
    # Test connection
    if ! test_mysql_connection; then
        print_error "Cannot proceed without valid MySQL connection"
        exit 1
    fi
    
    # Setup database
    setup_database
    
    # Import schema
    import_schema
    
    # Verify installation
    verify_installation
    
    # Create environment file
    create_env_file
    
    # Show connection info
    show_connection_info
}

# Handle script interruption
trap 'print_error "Script interrupted"; exit 1' INT TERM

# Run main function
main "$@"