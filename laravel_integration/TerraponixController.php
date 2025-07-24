<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Carbon\Carbon;

class TerraponixController extends Controller
{
    /**
     * Receive sensor data from ESP32 Terraponix device
     */
    public function receiveSensorData(Request $request): JsonResponse
    {
        try {
            // Validate incoming data
            $validatedData = $request->validate([
                'device_name' => 'string|nullable',
                'version' => 'string|nullable',
                'temperature' => 'required|numeric',
                'humidity' => 'required|numeric',
                'ph' => 'required|numeric',
                'light_intensity' => 'required|integer',
                'water_level' => 'required|integer',
                'water_status' => 'required|string',
                'soil_moisture' => 'required|integer',
                'pump_status' => 'required|string',
                'fan_status' => 'required|string',
                'curtain_status' => 'required|string',
                'mode' => 'required|string',
                'system_status' => 'string|nullable',
                'wifi_status' => 'required|string',
                'wifi_signal' => 'integer|nullable',
                'ip_address' => 'required|ip',
                'timestamp' => 'required|integer',
            ]);

            // Store data in database
            $sensorData = DB::table('terraponix_sensor_data')->insert([
                'device_name' => $validatedData['device_name'] ?? 'Terraponix-Greenhouse',
                'version' => $validatedData['version'] ?? 'v2.0',
                'temperature' => $validatedData['temperature'],
                'humidity' => $validatedData['humidity'],
                'ph' => $validatedData['ph'],
                'light_intensity' => $validatedData['light_intensity'],
                'water_level' => $validatedData['water_level'],
                'water_status' => $validatedData['water_status'],
                'soil_moisture' => $validatedData['soil_moisture'],
                'pump_status' => $validatedData['pump_status'],
                'fan_status' => $validatedData['fan_status'],
                'curtain_status' => $validatedData['curtain_status'],
                'mode' => $validatedData['mode'],
                'system_status' => $validatedData['system_status'] ?? 'ENABLED',
                'wifi_status' => $validatedData['wifi_status'],
                'wifi_signal' => $validatedData['wifi_signal'],
                'ip_address' => $validatedData['ip_address'],
                'device_timestamp' => $validatedData['timestamp'],
                'received_at' => Carbon::now(),
                'created_at' => Carbon::now(),
                'updated_at' => Carbon::now(),
            ]);

            // Log successful data reception
            Log::info('Terraponix sensor data received', [
                'ip_address' => $validatedData['ip_address'],
                'temperature' => $validatedData['temperature'],
                'humidity' => $validatedData['humidity'],
                'soil_moisture' => $validatedData['soil_moisture'],
            ]);

            return response()->json([
                'status' => 'success',
                'message' => 'Sensor data received and stored successfully',
                'received_at' => Carbon::now()->toISOString(),
                'data_count' => 1
            ], 200);

        } catch (\Illuminate\Validation\ValidationException $e) {
            Log::warning('Invalid sensor data received', [
                'errors' => $e->errors(),
                'request_data' => $request->all()
            ]);

            return response()->json([
                'status' => 'error',
                'message' => 'Invalid sensor data format',
                'errors' => $e->errors()
            ], 422);

        } catch (\Exception $e) {
            Log::error('Error storing sensor data', [
                'error' => $e->getMessage(),
                'request_data' => $request->all()
            ]);

            return response()->json([
                'status' => 'error',
                'message' => 'Internal server error',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get latest sensor data for dashboard
     */
    public function getLatestSensorData(): JsonResponse
    {
        try {
            $latestData = DB::table('terraponix_sensor_data')
                ->orderBy('created_at', 'desc')
                ->first();

            if (!$latestData) {
                return response()->json([
                    'status' => 'success',
                    'message' => 'No sensor data available',
                    'data' => null
                ], 200);
            }

            return response()->json([
                'status' => 'success',
                'message' => 'Latest sensor data retrieved',
                'data' => $latestData,
                'last_updated' => $latestData->received_at
            ], 200);

        } catch (\Exception $e) {
            Log::error('Error retrieving sensor data', [
                'error' => $e->getMessage()
            ]);

            return response()->json([
                'status' => 'error',
                'message' => 'Failed to retrieve sensor data',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get sensor data history with pagination
     */
    public function getSensorDataHistory(Request $request): JsonResponse
    {
        try {
            $perPage = $request->get('per_page', 50);
            $page = $request->get('page', 1);
            $hours = $request->get('hours', 24); // Default last 24 hours

            $query = DB::table('terraponix_sensor_data')
                ->where('created_at', '>=', Carbon::now()->subHours($hours))
                ->orderBy('created_at', 'desc');

            $total = $query->count();
            $data = $query->skip(($page - 1) * $perPage)
                         ->take($perPage)
                         ->get();

            return response()->json([
                'status' => 'success',
                'message' => 'Sensor data history retrieved',
                'data' => $data,
                'pagination' => [
                    'current_page' => $page,
                    'per_page' => $perPage,
                    'total' => $total,
                    'last_page' => ceil($total / $perPage),
                    'hours_range' => $hours
                ]
            ], 200);

        } catch (\Exception $e) {
            Log::error('Error retrieving sensor data history', [
                'error' => $e->getMessage()
            ]);

            return response()->json([
                'status' => 'error',
                'message' => 'Failed to retrieve sensor data history',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get sensor data statistics
     */
    public function getSensorStatistics(Request $request): JsonResponse
    {
        try {
            $hours = $request->get('hours', 24);
            $startTime = Carbon::now()->subHours($hours);

            $stats = DB::table('terraponix_sensor_data')
                ->where('created_at', '>=', $startTime)
                ->selectRaw('
                    COUNT(*) as total_readings,
                    AVG(temperature) as avg_temperature,
                    MIN(temperature) as min_temperature,
                    MAX(temperature) as max_temperature,
                    AVG(humidity) as avg_humidity,
                    MIN(humidity) as min_humidity,
                    MAX(humidity) as max_humidity,
                    AVG(ph) as avg_ph,
                    MIN(ph) as min_ph,
                    MAX(ph) as max_ph,
                    AVG(soil_moisture) as avg_soil_moisture,
                    MIN(soil_moisture) as min_soil_moisture,
                    MAX(soil_moisture) as max_soil_moisture,
                    AVG(light_intensity) as avg_light_intensity,
                    MIN(light_intensity) as min_light_intensity,
                    MAX(light_intensity) as max_light_intensity
                ')
                ->first();

            // Get device status counts
            $deviceStats = DB::table('terraponix_sensor_data')
                ->where('created_at', '>=', $startTime)
                ->selectRaw('
                    SUM(CASE WHEN pump_status = "ON" THEN 1 ELSE 0 END) as pump_on_count,
                    SUM(CASE WHEN fan_status = "ON" THEN 1 ELSE 0 END) as fan_on_count,
                    SUM(CASE WHEN curtain_status = "CLOSED" THEN 1 ELSE 0 END) as curtain_closed_count,
                    SUM(CASE WHEN water_status = "LOW" THEN 1 ELSE 0 END) as water_low_count,
                    SUM(CASE WHEN mode = "AUTO" THEN 1 ELSE 0 END) as auto_mode_count
                ')
                ->first();

            return response()->json([
                'status' => 'success',
                'message' => 'Sensor statistics retrieved',
                'time_range' => [
                    'hours' => $hours,
                    'start_time' => $startTime->toISOString(),
                    'end_time' => Carbon::now()->toISOString()
                ],
                'sensor_stats' => [
                    'total_readings' => $stats->total_readings,
                    'temperature' => [
                        'average' => round($stats->avg_temperature, 2),
                        'minimum' => round($stats->min_temperature, 2),
                        'maximum' => round($stats->max_temperature, 2)
                    ],
                    'humidity' => [
                        'average' => round($stats->avg_humidity, 2),
                        'minimum' => round($stats->min_humidity, 2),
                        'maximum' => round($stats->max_humidity, 2)
                    ],
                    'ph' => [
                        'average' => round($stats->avg_ph, 2),
                        'minimum' => round($stats->min_ph, 2),
                        'maximum' => round($stats->max_ph, 2)
                    ],
                    'soil_moisture' => [
                        'average' => round($stats->avg_soil_moisture, 2),
                        'minimum' => $stats->min_soil_moisture,
                        'maximum' => $stats->max_soil_moisture
                    ],
                    'light_intensity' => [
                        'average' => round($stats->avg_light_intensity, 2),
                        'minimum' => $stats->min_light_intensity,
                        'maximum' => $stats->max_light_intensity
                    ]
                ],
                'device_stats' => [
                    'pump_on_percentage' => $stats->total_readings > 0 ? round(($deviceStats->pump_on_count / $stats->total_readings) * 100, 2) : 0,
                    'fan_on_percentage' => $stats->total_readings > 0 ? round(($deviceStats->fan_on_count / $stats->total_readings) * 100, 2) : 0,
                    'curtain_closed_percentage' => $stats->total_readings > 0 ? round(($deviceStats->curtain_closed_count / $stats->total_readings) * 100, 2) : 0,
                    'water_low_percentage' => $stats->total_readings > 0 ? round(($deviceStats->water_low_count / $stats->total_readings) * 100, 2) : 0,
                    'auto_mode_percentage' => $stats->total_readings > 0 ? round(($deviceStats->auto_mode_count / $stats->total_readings) * 100, 2) : 0
                ]
            ], 200);

        } catch (\Exception $e) {
            Log::error('Error retrieving sensor statistics', [
                'error' => $e->getMessage()
            ]);

            return response()->json([
                'status' => 'error',
                'message' => 'Failed to retrieve sensor statistics',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Send control commands to ESP32 (for future implementation)
     */
    public function sendControlCommand(Request $request): JsonResponse
    {
        try {
            $validatedData = $request->validate([
                'device_ip' => 'required|ip',
                'command' => 'required|string|in:pump,fan,curtain,mode,system',
                'action' => 'required|string',
                'value' => 'required|boolean'
            ]);

            // Store command in database for logging
            DB::table('terraponix_commands')->insert([
                'device_ip' => $validatedData['device_ip'],
                'command' => $validatedData['command'],
                'action' => $validatedData['action'],
                'value' => $validatedData['value'],
                'status' => 'pending',
                'created_at' => Carbon::now(),
                'updated_at' => Carbon::now(),
            ]);

            // In a real implementation, you would send HTTP request to ESP32
            // For now, just return success
            Log::info('Control command stored', $validatedData);

            return response()->json([
                'status' => 'success',
                'message' => 'Control command stored successfully',
                'command' => $validatedData
            ], 200);

        } catch (\Exception $e) {
            Log::error('Error storing control command', [
                'error' => $e->getMessage(),
                'request_data' => $request->all()
            ]);

            return response()->json([
                'status' => 'error',
                'message' => 'Failed to store control command',
                'error' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Dashboard view for web interface
     */
    public function dashboard()
    {
        try {
            $latestData = DB::table('terraponix_sensor_data')
                ->orderBy('created_at', 'desc')
                ->first();

            $recentData = DB::table('terraponix_sensor_data')
                ->orderBy('created_at', 'desc')
                ->take(10)
                ->get();

            return view('terraponix.dashboard', compact('latestData', 'recentData'));

        } catch (\Exception $e) {
            Log::error('Error loading dashboard', [
                'error' => $e->getMessage()
            ]);

            return view('terraponix.dashboard', [
                'latestData' => null,
                'recentData' => collect(),
                'error' => 'Failed to load sensor data'
            ]);
        }
    }
}