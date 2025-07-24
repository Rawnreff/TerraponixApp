<?php

use App\Http\Controllers\TerraponixController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Terraponix Web Routes
|--------------------------------------------------------------------------
|
| Here are the web routes for the Terraponix Greenhouse monitoring system.
| These routes handle both web interface and API endpoints for ESP32 communication.
|
*/

// Web Interface Routes
Route::prefix('terraponix')->group(function () {
    // Dashboard
    Route::get('/', [TerraponixController::class, 'dashboard'])->name('terraponix.dashboard');
    Route::get('/dashboard', [TerraponixController::class, 'dashboard'])->name('terraponix.dashboard.full');
});

// API Routes for ESP32 Communication
Route::prefix('api/terraponix')->group(function () {
    
    // Data Reception from ESP32
    Route::post('/sensor-data', [TerraponixController::class, 'receiveSensorData'])
        ->name('api.terraponix.sensor-data');
    
    // Data Retrieval for Web Interface
    Route::get('/latest', [TerraponixController::class, 'getLatestSensorData'])
        ->name('api.terraponix.latest');
    
    Route::get('/history', [TerraponixController::class, 'getSensorDataHistory'])
        ->name('api.terraponix.history');
    
    Route::get('/statistics', [TerraponixController::class, 'getSensorStatistics'])
        ->name('api.terraponix.statistics');
    
    // Device Control
    Route::post('/control', [TerraponixController::class, 'sendControlCommand'])
        ->name('api.terraponix.control');
});

/*
|--------------------------------------------------------------------------
| Alternative API Routes (for backward compatibility)
|--------------------------------------------------------------------------
*/

// These routes match the ESP32 code expectations
Route::prefix('api')->group(function () {
    
    // Greenhouse data endpoint (matches ESP32 serverURL)
    Route::post('/greenhouse-data', [TerraponixController::class, 'receiveSensorData'])
        ->name('api.greenhouse-data');
    
    // Control endpoint (matches ESP32 controlURL)
    Route::get('/greenhouse-control', function (Illuminate\Http\Request $request) {
        // This endpoint would return pending commands for the device
        // For now, return empty commands array
        return response()->json([
            'status' => 'success',
            'commands' => []
        ]);
    })->name('api.greenhouse-control');
    
    // Device registration endpoint
    Route::post('/register', function (Illuminate\Http\Request $request) {
        try {
            $validatedData = $request->validate([
                'device_id' => 'required|string',
                'device_type' => 'required|string',
                'ip_address' => 'required|ip',
                'capabilities' => 'string|nullable'
            ]);
            
            // Store or update device registration
            DB::table('terraponix_devices')->updateOrInsert(
                ['device_id' => $validatedData['device_id']],
                [
                    'device_name' => $validatedData['device_id'],
                    'device_id' => $validatedData['device_id'],
                    'ip_address' => $validatedData['ip_address'],
                    'capabilities' => $validatedData['capabilities'],
                    'status' => 'online',
                    'last_seen_at' => now(),
                    'registered_at' => now(),
                    'updated_at' => now(),
                    'created_at' => DB::raw('COALESCE(created_at, NOW())')
                ]
            );
            
            return response()->json([
                'status' => 'success',
                'message' => 'Device registered successfully',
                'device_id' => $validatedData['device_id']
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'status' => 'error',
                'message' => 'Registration failed',
                'error' => $e->getMessage()
            ], 500);
        }
    })->name('api.register');
});

/*
|--------------------------------------------------------------------------
| CORS Middleware for API Routes
|--------------------------------------------------------------------------
*/

// Apply CORS middleware to API routes for cross-origin requests
Route::middleware(['cors'])->group(function () {
    // Add any additional API routes that need CORS here
});

/*
|--------------------------------------------------------------------------
| Development/Testing Routes
|--------------------------------------------------------------------------
*/

if (app()->environment(['local', 'testing'])) {
    
    Route::prefix('terraponix/test')->group(function () {
        
        // Test data insertion
        Route::get('/insert-sample-data', function () {
            $sampleData = [
                'device_name' => 'Terraponix-Greenhouse',
                'version' => 'v2.0',
                'temperature' => 26.5,
                'humidity' => 65.2,
                'ph' => 6.8,
                'light_intensity' => 2500,
                'water_level' => 1800,
                'water_status' => 'OK',
                'soil_moisture' => 45,
                'pump_status' => 'OFF',
                'fan_status' => 'OFF',
                'curtain_status' => 'OPEN',
                'mode' => 'AUTO',
                'system_status' => 'ENABLED',
                'wifi_status' => 'CONNECTED',
                'wifi_signal' => -45,
                'ip_address' => '192.168.1.100',
                'device_timestamp' => time() * 1000,
                'received_at' => now(),
                'created_at' => now(),
                'updated_at' => now(),
            ];
            
            DB::table('terraponix_sensor_data')->insert($sampleData);
            
            return response()->json([
                'status' => 'success',
                'message' => 'Sample data inserted',
                'data' => $sampleData
            ]);
        });
        
        // Test API endpoints
        Route::get('/api-test', function () {
            return response()->json([
                'status' => 'success',
                'message' => 'Terraponix API is working',
                'timestamp' => now()->toISOString(),
                'endpoints' => [
                    'POST /api/terraponix/sensor-data' => 'Receive sensor data from ESP32',
                    'GET /api/terraponix/latest' => 'Get latest sensor data',
                    'GET /api/terraponix/history' => 'Get sensor data history',
                    'GET /api/terraponix/statistics' => 'Get sensor statistics',
                    'POST /api/terraponix/control' => 'Send control commands'
                ]
            ]);
        });
        
        // Clear old data
        Route::delete('/clear-old-data', function (Illuminate\Http\Request $request) {
            $days = $request->get('days', 7);
            $cutoffDate = now()->subDays($days);
            
            $deleted = DB::table('terraponix_sensor_data')
                ->where('created_at', '<', $cutoffDate)
                ->delete();
            
            return response()->json([
                'status' => 'success',
                'message' => "Deleted {$deleted} records older than {$days} days",
                'cutoff_date' => $cutoffDate->toISOString()
            ]);
        });
    });
}

/*
|--------------------------------------------------------------------------
| Health Check Route
|--------------------------------------------------------------------------
*/

Route::get('/terraponix/health', function () {
    try {
        // Check database connection
        $dbCheck = DB::connection()->getPdo() ? 'OK' : 'FAILED';
        
        // Check if tables exist
        $tablesExist = Schema::hasTable('terraponix_sensor_data') && 
                      Schema::hasTable('terraponix_devices') && 
                      Schema::hasTable('terraponix_commands');
        
        // Get latest data timestamp
        $latestData = DB::table('terraponix_sensor_data')
            ->orderBy('created_at', 'desc')
            ->first();
        
        return response()->json([
            'status' => 'healthy',
            'timestamp' => now()->toISOString(),
            'checks' => [
                'database' => $dbCheck,
                'tables_exist' => $tablesExist ? 'OK' : 'MISSING',
                'latest_data' => $latestData ? $latestData->created_at : 'NO_DATA'
            ],
            'version' => 'v2.0',
            'system' => 'Terraponix Greenhouse Monitoring'
        ]);
        
    } catch (\Exception $e) {
        return response()->json([
            'status' => 'unhealthy',
            'timestamp' => now()->toISOString(),
            'error' => $e->getMessage()
        ], 500);
    }
})->name('terraponix.health');