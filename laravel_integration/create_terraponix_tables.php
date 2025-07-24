<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        // Create sensor data table
        Schema::create('terraponix_sensor_data', function (Blueprint $table) {
            $table->id();
            $table->string('device_name')->default('Terraponix-Greenhouse');
            $table->string('version')->default('v2.0');
            $table->decimal('temperature', 5, 2)->comment('Temperature in Celsius');
            $table->decimal('humidity', 5, 2)->comment('Humidity percentage');
            $table->decimal('ph', 4, 2)->comment('pH level (0-14)');
            $table->integer('light_intensity')->comment('Light intensity from LDR sensor');
            $table->integer('water_level')->comment('Water level sensor raw value');
            $table->enum('water_status', ['LOW', 'OK'])->default('OK');
            $table->integer('soil_moisture')->comment('Soil moisture percentage');
            $table->enum('pump_status', ['ON', 'OFF'])->default('OFF');
            $table->enum('fan_status', ['ON', 'OFF'])->default('OFF');
            $table->enum('curtain_status', ['OPEN', 'CLOSED'])->default('OPEN');
            $table->enum('mode', ['AUTO', 'MANUAL'])->default('AUTO');
            $table->enum('system_status', ['ENABLED', 'DISABLED'])->default('ENABLED');
            $table->enum('wifi_status', ['CONNECTED', 'DISCONNECTED'])->default('DISCONNECTED');
            $table->integer('wifi_signal')->nullable()->comment('WiFi signal strength in dBm');
            $table->ipAddress('ip_address');
            $table->bigInteger('device_timestamp')->comment('Timestamp from ESP32 device (millis)');
            $table->timestamp('received_at')->comment('When data was received by server');
            $table->timestamps();
            
            // Indexes for better query performance
            $table->index(['created_at']);
            $table->index(['device_name', 'created_at']);
            $table->index(['ip_address', 'created_at']);
        });

        // Create commands table for device control
        Schema::create('terraponix_commands', function (Blueprint $table) {
            $table->id();
            $table->ipAddress('device_ip');
            $table->enum('command', ['pump', 'fan', 'curtain', 'mode', 'system']);
            $table->string('action');
            $table->boolean('value');
            $table->enum('status', ['pending', 'sent', 'acknowledged', 'failed'])->default('pending');
            $table->timestamp('sent_at')->nullable();
            $table->timestamp('acknowledged_at')->nullable();
            $table->text('response')->nullable();
            $table->text('error_message')->nullable();
            $table->timestamps();
            
            // Indexes
            $table->index(['device_ip', 'status']);
            $table->index(['created_at']);
        });

        // Create device registry table
        Schema::create('terraponix_devices', function (Blueprint $table) {
            $table->id();
            $table->string('device_name')->unique();
            $table->string('device_id')->unique();
            $table->string('version')->nullable();
            $table->ipAddress('ip_address');
            $table->string('mac_address')->nullable();
            $table->text('capabilities')->nullable()->comment('JSON array of device capabilities');
            $table->enum('status', ['online', 'offline', 'maintenance'])->default('offline');
            $table->timestamp('last_seen_at')->nullable();
            $table->timestamp('registered_at');
            $table->timestamps();
            
            // Indexes
            $table->index(['status']);
            $table->index(['last_seen_at']);
        });

        // Create alerts table for monitoring
        Schema::create('terraponix_alerts', function (Blueprint $table) {
            $table->id();
            $table->string('device_name');
            $table->enum('alert_type', [
                'temperature_high', 
                'temperature_low', 
                'humidity_high', 
                'humidity_low',
                'ph_high', 
                'ph_low',
                'water_low',
                'soil_moisture_low',
                'device_offline',
                'sensor_error'
            ]);
            $table->string('title');
            $table->text('message');
            $table->decimal('trigger_value', 8, 2)->nullable();
            $table->decimal('threshold_value', 8, 2)->nullable();
            $table->enum('severity', ['low', 'medium', 'high', 'critical'])->default('medium');
            $table->enum('status', ['active', 'acknowledged', 'resolved'])->default('active');
            $table->timestamp('triggered_at');
            $table->timestamp('acknowledged_at')->nullable();
            $table->timestamp('resolved_at')->nullable();
            $table->timestamps();
            
            // Indexes
            $table->index(['device_name', 'status']);
            $table->index(['alert_type', 'status']);
            $table->index(['severity', 'status']);
            $table->index(['triggered_at']);
        });

        // Create configuration table
        Schema::create('terraponix_config', function (Blueprint $table) {
            $table->id();
            $table->string('device_name');
            $table->string('config_key');
            $table->text('config_value');
            $table->string('data_type')->default('string'); // string, integer, float, boolean, json
            $table->text('description')->nullable();
            $table->boolean('is_editable')->default(true);
            $table->timestamps();
            
            // Unique constraint
            $table->unique(['device_name', 'config_key']);
            
            // Indexes
            $table->index(['device_name']);
            $table->index(['config_key']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('terraponix_config');
        Schema::dropIfExists('terraponix_alerts');
        Schema::dropIfExists('terraponix_devices');
        Schema::dropIfExists('terraponix_commands');
        Schema::dropIfExists('terraponix_sensor_data');
    }
};