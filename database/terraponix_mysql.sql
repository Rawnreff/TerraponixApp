-- Terraponix MySQL Database Schema
-- Created for IoT Hydroponic Monitoring System

-- Drop database if exists and create new one
DROP DATABASE IF EXISTS terraponix;
CREATE DATABASE terraponix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE terraponix;

-- ==========================================
-- User and Authentication Tables
-- ==========================================

-- Users table for application access control
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role ENUM('admin', 'user', 'viewer') DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Sessions table for login session management
CREATE TABLE user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ==========================================
-- Device and Sensor Tables
-- ==========================================

-- Devices table for ESP32 and other IoT devices
CREATE TABLE devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    device_type ENUM('esp32', 'raspberry_pi', 'arduino', 'sensor_node') DEFAULT 'esp32',
    mac_address VARCHAR(17) UNIQUE,
    ip_address VARCHAR(15),
    firmware_version VARCHAR(20),
    location VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_heartbeat TIMESTAMP NULL,
    battery_level DECIMAL(5,2) DEFAULT 100.00,
    solar_power DECIMAL(8,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Sensor types configuration
CREATE TABLE sensor_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_name VARCHAR(50) UNIQUE NOT NULL,
    unit VARCHAR(10) NOT NULL,
    min_value DECIMAL(10,3),
    max_value DECIMAL(10,3),
    threshold_min DECIMAL(10,3),
    threshold_max DECIMAL(10,3),
    critical_min DECIMAL(10,3),
    critical_max DECIMAL(10,3),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Sensor data readings - main data table
CREATE TABLE sensor_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperature DECIMAL(5,2) COMMENT 'Temperature in Celsius',
    humidity DECIMAL(5,2) COMMENT 'Humidity percentage',
    ph DECIMAL(4,2) COMMENT 'pH level',
    tds DECIMAL(8,2) COMMENT 'Total Dissolved Solids in ppm',
    light_intensity DECIMAL(10,2) COMMENT 'Light intensity in lux',
    co2 DECIMAL(8,2) COMMENT 'CO2 level in ppm',
    soil_moisture DECIMAL(5,2) COMMENT 'Soil moisture percentage',
    water_level DECIMAL(5,2) COMMENT 'Water level percentage',
    electrical_conductivity DECIMAL(8,2) COMMENT 'EC in μS/cm',
    dissolved_oxygen DECIMAL(5,2) COMMENT 'DO in mg/L',
    water_temperature DECIMAL(5,2) COMMENT 'Water temperature in Celsius',
    ambient_pressure DECIMAL(8,2) COMMENT 'Atmospheric pressure in hPa',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_timestamp (device_id, timestamp),
    INDEX idx_timestamp (timestamp),
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- ==========================================
-- Control and Automation Tables
-- ==========================================

-- Control settings for automated systems
CREATE TABLE control_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    pump_auto BOOLEAN DEFAULT TRUE,
    fan_auto BOOLEAN DEFAULT TRUE,
    curtain_auto BOOLEAN DEFAULT TRUE,
    light_auto BOOLEAN DEFAULT TRUE,
    heater_auto BOOLEAN DEFAULT TRUE,
    pump_status BOOLEAN DEFAULT FALSE,
    fan_status BOOLEAN DEFAULT FALSE,
    curtain_status BOOLEAN DEFAULT FALSE,
    light_status BOOLEAN DEFAULT FALSE,
    heater_status BOOLEAN DEFAULT FALSE,
    temp_threshold_min DECIMAL(5,2) DEFAULT 20.00,
    temp_threshold_max DECIMAL(5,2) DEFAULT 30.00,
    humidity_threshold_min DECIMAL(5,2) DEFAULT 60.00,
    humidity_threshold_max DECIMAL(5,2) DEFAULT 80.00,
    ph_threshold_min DECIMAL(4,2) DEFAULT 5.50,
    ph_threshold_max DECIMAL(4,2) DEFAULT 6.50,
    tds_threshold_min DECIMAL(8,2) DEFAULT 800.00,
    tds_threshold_max DECIMAL(8,2) DEFAULT 1200.00,
    light_threshold_min DECIMAL(10,2) DEFAULT 20000.00,
    light_threshold_max DECIMAL(10,2) DEFAULT 50000.00,
    co2_threshold_min DECIMAL(8,2) DEFAULT 800.00,
    co2_threshold_max DECIMAL(8,2) DEFAULT 1200.00,
    soil_moisture_threshold_min DECIMAL(5,2) DEFAULT 40.00,
    soil_moisture_threshold_max DECIMAL(5,2) DEFAULT 70.00,
    water_level_threshold_min DECIMAL(5,2) DEFAULT 30.00,
    water_level_threshold_max DECIMAL(5,2) DEFAULT 90.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- Control actions log
CREATE TABLE control_actions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    action_type ENUM('pump', 'fan', 'curtain', 'light', 'heater', 'valve', 'other') NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_value BOOLEAN,
    new_value BOOLEAN,
    triggered_by ENUM('manual', 'automatic', 'schedule', 'emergency') DEFAULT 'manual',
    user_id INT NULL,
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_timestamp (device_id, timestamp),
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ==========================================
-- Alerts and Notifications
-- ==========================================

-- Alerts and warnings system
CREATE TABLE alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    alert_type ENUM('temperature', 'humidity', 'ph', 'tds', 'light', 'co2', 'soil_moisture', 'water_level', 'system', 'device', 'other') NOT NULL,
    severity ENUM('INFO', 'WARNING', 'CRITICAL', 'EMERGENCY') DEFAULT 'INFO',
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    sensor_value DECIMAL(10,3),
    threshold_value DECIMAL(10,3),
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by INT NULL,
    acknowledged_at TIMESTAMP NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_severity (device_id, severity),
    INDEX idx_created_at (created_at),
    INDEX idx_unresolved (is_resolved, created_at),
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Notification preferences
CREATE TABLE notification_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    push_enabled BOOLEAN DEFAULT TRUE,
    email_address VARCHAR(100),
    phone_number VARCHAR(20),
    alert_severity_min ENUM('INFO', 'WARNING', 'CRITICAL', 'EMERGENCY') DEFAULT 'WARNING',
    quiet_hours_start TIME DEFAULT '22:00:00',
    quiet_hours_end TIME DEFAULT '07:00:00',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ==========================================
-- Scheduling and Automation
-- ==========================================

-- Automated schedules for controls
CREATE TABLE schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    schedule_name VARCHAR(100) NOT NULL,
    control_type ENUM('pump', 'fan', 'curtain', 'light', 'heater') NOT NULL,
    action ENUM('on', 'off', 'toggle') NOT NULL,
    schedule_type ENUM('daily', 'weekly', 'interval', 'condition') DEFAULT 'daily',
    start_time TIME,
    end_time TIME,
    interval_minutes INT,
    days_of_week SET('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'),
    condition_sensor VARCHAR(50),
    condition_operator ENUM('>', '<', '>=', '<=', '=', '!='),
    condition_value DECIMAL(10,3),
    is_active BOOLEAN DEFAULT TRUE,
    last_executed TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- ==========================================
-- Analytics and Reporting
-- ==========================================

-- Daily aggregated data for faster reporting
CREATE TABLE daily_sensor_summary (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    date DATE NOT NULL,
    temperature_avg DECIMAL(5,2),
    temperature_min DECIMAL(5,2),
    temperature_max DECIMAL(5,2),
    humidity_avg DECIMAL(5,2),
    humidity_min DECIMAL(5,2),
    humidity_max DECIMAL(5,2),
    ph_avg DECIMAL(4,2),
    ph_min DECIMAL(4,2),
    ph_max DECIMAL(4,2),
    tds_avg DECIMAL(8,2),
    tds_min DECIMAL(8,2),
    tds_max DECIMAL(8,2),
    light_intensity_avg DECIMAL(10,2),
    light_intensity_min DECIMAL(10,2),
    light_intensity_max DECIMAL(10,2),
    co2_avg DECIMAL(8,2),
    co2_min DECIMAL(8,2),
    co2_max DECIMAL(8,2),
    soil_moisture_avg DECIMAL(5,2),
    soil_moisture_min DECIMAL(5,2),
    soil_moisture_max DECIMAL(5,2),
    water_level_avg DECIMAL(5,2),
    water_level_min DECIMAL(5,2),
    water_level_max DECIMAL(5,2),
    readings_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_device_date (device_id, date),
    INDEX idx_date (date),
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- System configuration and settings
CREATE TABLE system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type ENUM('string', 'integer', 'float', 'boolean', 'json') DEFAULT 'string',
    description TEXT,
    updated_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ==========================================
-- Insert Initial Data
-- ==========================================

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, full_name, role) VALUES 
('admin', 'admin@terraponix.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewHFm4W3TjOHq5K6', 'System Administrator', 'admin');

-- Insert default device
INSERT INTO devices (device_name, device_type, location) VALUES 
('Main ESP32', 'esp32', 'Greenhouse Zone A');

-- Insert sensor types configuration
INSERT INTO sensor_types (sensor_name, unit, min_value, max_value, threshold_min, threshold_max, critical_min, critical_max, description) VALUES
('temperature', '°C', -50.0, 100.0, 20.0, 30.0, 10.0, 40.0, 'Ambient temperature sensor'),
('humidity', '%', 0.0, 100.0, 60.0, 80.0, 30.0, 95.0, 'Relative humidity sensor'),
('ph', 'pH', 0.0, 14.0, 5.5, 6.5, 4.0, 8.0, 'pH level sensor'),
('tds', 'ppm', 0.0, 5000.0, 800.0, 1200.0, 200.0, 2000.0, 'Total Dissolved Solids sensor'),
('light_intensity', 'lux', 0.0, 100000.0, 20000.0, 50000.0, 5000.0, 80000.0, 'Light intensity sensor'),
('co2', 'ppm', 0.0, 5000.0, 800.0, 1200.0, 300.0, 2000.0, 'CO2 concentration sensor'),
('soil_moisture', '%', 0.0, 100.0, 40.0, 70.0, 20.0, 90.0, 'Soil moisture sensor'),
('water_level', '%', 0.0, 100.0, 30.0, 90.0, 10.0, 100.0, 'Water level sensor');

-- Insert default control settings
INSERT INTO control_settings (device_id) VALUES (1);

-- Insert default system settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('data_retention_days', '365', 'integer', 'Number of days to keep sensor data'),
('alert_check_interval', '60', 'integer', 'Alert check interval in seconds'),
('auto_backup_enabled', 'true', 'boolean', 'Enable automatic database backup'),
('backup_interval_hours', '24', 'integer', 'Backup interval in hours'),
('max_alerts_per_hour', '10', 'integer', 'Maximum alerts per hour per device'),
('system_timezone', 'Asia/Jakarta', 'string', 'System timezone'),
('dashboard_refresh_interval', '30', 'integer', 'Dashboard refresh interval in seconds');

-- ==========================================
-- Create Views for Common Queries
-- ==========================================

-- Latest sensor readings view
CREATE VIEW latest_sensor_readings AS
SELECT 
    d.device_name,
    sd.*
FROM sensor_data sd
INNER JOIN devices d ON sd.device_id = d.id
INNER JOIN (
    SELECT device_id, MAX(timestamp) as max_timestamp
    FROM sensor_data
    GROUP BY device_id
) latest ON sd.device_id = latest.device_id AND sd.timestamp = latest.max_timestamp;

-- Active alerts view
CREATE VIEW active_alerts AS
SELECT 
    a.*,
    d.device_name,
    u.username as acknowledged_by_user
FROM alerts a
INNER JOIN devices d ON a.device_id = d.id
LEFT JOIN users u ON a.acknowledged_by = u.id
WHERE a.is_resolved = FALSE
ORDER BY a.severity DESC, a.created_at DESC;

-- Device status view
CREATE VIEW device_status AS
SELECT 
    d.*,
    CASE 
        WHEN d.last_heartbeat > NOW() - INTERVAL 5 MINUTE THEN 'online'
        WHEN d.last_heartbeat > NOW() - INTERVAL 1 HOUR THEN 'warning'
        ELSE 'offline'
    END as connection_status,
    TIMESTAMPDIFF(MINUTE, d.last_heartbeat, NOW()) as minutes_since_heartbeat
FROM devices d;

-- ==========================================
-- Create Stored Procedures
-- ==========================================

DELIMITER //

-- Procedure to clean old data
CREATE PROCEDURE CleanOldData(IN retention_days INT)
BEGIN
    DELETE FROM sensor_data 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL retention_days DAY);
    
    DELETE FROM alerts 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL retention_days DAY) 
    AND is_resolved = TRUE;
    
    DELETE FROM control_actions 
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL retention_days DAY);
END //

-- Procedure to generate daily summary
CREATE PROCEDURE GenerateDailySummary(IN target_date DATE, IN target_device_id INT)
BEGIN
    INSERT INTO daily_sensor_summary (
        device_id, date,
        temperature_avg, temperature_min, temperature_max,
        humidity_avg, humidity_min, humidity_max,
        ph_avg, ph_min, ph_max,
        tds_avg, tds_min, tds_max,
        light_intensity_avg, light_intensity_min, light_intensity_max,
        co2_avg, co2_min, co2_max,
        soil_moisture_avg, soil_moisture_min, soil_moisture_max,
        water_level_avg, water_level_min, water_level_max,
        readings_count
    )
    SELECT 
        device_id, DATE(timestamp),
        AVG(temperature), MIN(temperature), MAX(temperature),
        AVG(humidity), MIN(humidity), MAX(humidity),
        AVG(ph), MIN(ph), MAX(ph),
        AVG(tds), MIN(tds), MAX(tds),
        AVG(light_intensity), MIN(light_intensity), MAX(light_intensity),
        AVG(co2), MIN(co2), MAX(co2),
        AVG(soil_moisture), MIN(soil_moisture), MAX(soil_moisture),
        AVG(water_level), MIN(water_level), MAX(water_level),
        COUNT(*)
    FROM sensor_data
    WHERE DATE(timestamp) = target_date 
    AND device_id = target_device_id
    GROUP BY device_id, DATE(timestamp)
    ON DUPLICATE KEY UPDATE
        temperature_avg = VALUES(temperature_avg),
        temperature_min = VALUES(temperature_min),
        temperature_max = VALUES(temperature_max),
        humidity_avg = VALUES(humidity_avg),
        humidity_min = VALUES(humidity_min),
        humidity_max = VALUES(humidity_max),
        ph_avg = VALUES(ph_avg),
        ph_min = VALUES(ph_min),
        ph_max = VALUES(ph_max),
        tds_avg = VALUES(tds_avg),
        tds_min = VALUES(tds_min),
        tds_max = VALUES(tds_max),
        light_intensity_avg = VALUES(light_intensity_avg),
        light_intensity_min = VALUES(light_intensity_min),
        light_intensity_max = VALUES(light_intensity_max),
        co2_avg = VALUES(co2_avg),
        co2_min = VALUES(co2_min),
        co2_max = VALUES(co2_max),
        soil_moisture_avg = VALUES(soil_moisture_avg),
        soil_moisture_min = VALUES(soil_moisture_min),
        soil_moisture_max = VALUES(soil_moisture_max),
        water_level_avg = VALUES(water_level_avg),
        water_level_min = VALUES(water_level_min),
        water_level_max = VALUES(water_level_max),
        readings_count = VALUES(readings_count);
END //

DELIMITER ;

-- ==========================================
-- Create Events for Automatic Maintenance
-- ==========================================

-- Enable event scheduler
SET GLOBAL event_scheduler = ON;

-- Event to generate daily summaries
CREATE EVENT IF NOT EXISTS daily_summary_generation
ON SCHEDULE EVERY 1 DAY
STARTS CURDATE() + INTERVAL 1 DAY + INTERVAL 1 HOUR
DO
BEGIN
    CALL GenerateDailySummary(CURDATE() - INTERVAL 1 DAY, 1);
END;

-- Event to clean old data (runs weekly)
CREATE EVENT IF NOT EXISTS weekly_data_cleanup
ON SCHEDULE EVERY 1 WEEK
STARTS CURDATE() + INTERVAL 1 DAY + INTERVAL 2 HOUR
DO
BEGIN
    CALL CleanOldData(365);
END;

-- ==========================================
-- Create Indexes for Performance
-- ==========================================

-- Additional performance indexes
CREATE INDEX idx_sensor_data_device_id_timestamp ON sensor_data(device_id, timestamp);
CREATE INDEX idx_alerts_device_severity_created ON alerts(device_id, severity, created_at);
CREATE INDEX idx_control_actions_device_timestamp ON control_actions(device_id, timestamp);
CREATE INDEX idx_schedules_device_active ON schedules(device_id, is_active);

-- Show created tables
SHOW TABLES;