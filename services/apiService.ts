import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Configuration
const BASE_URL = 'http://192.168.1.100:5000/api'; // Change this to your laptop's IP address
const API_TIMEOUT = 10000;

// Create axios instance
const api = axios.create({
  baseURL: BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface SensorData {
  temperature: number;
  humidity: number;
  ph: number;
  tds: number;
  light_intensity: number;
  co2: number;
  soil_moisture?: number;
  water_level?: number;
  battery_level?: number;
  solar_power?: number;
}

export interface DeviceStatus {
  esp32_connected: boolean;
  last_heartbeat: string | null;
  battery_level: number;
  solar_power: number;
}

export interface CurrentDataResponse {
  sensor_data: SensorData;
  device_status: DeviceStatus;
  timestamp: string;
}

export interface ControlSettings {
  id?: number;
  pump_auto: boolean;
  fan_auto: boolean;
  curtain_auto: boolean;
  pump_status: boolean;
  fan_status: boolean;
  curtain_status: boolean;
  temp_threshold_min: number;
  temp_threshold_max: number;
  humidity_threshold_min: number;
  humidity_threshold_max: number;
  ph_threshold_min: number;
  ph_threshold_max: number;
  updated_at?: string;
}

export interface Alert {
  id: number;
  timestamp: string;
  alert_type: string;
  message: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
}

export interface HistoricalData {
  id: number;
  timestamp: string;
  temperature: number;
  humidity: number;
  ph: number;
  tds: number;
  light_intensity: number;
  co2: number;
  soil_moisture: number;
  water_level: number;
}

// API Service Class
class ApiService {
  
  // Get current sensor data and device status
  async getCurrentData(): Promise<CurrentDataResponse> {
    try {
      const response = await api.get<CurrentDataResponse>('/current-data');
      return response.data;
    } catch (error) {
      console.error('Error getting current data:', error);
      throw this.handleError(error);
    }
  }

  // Get historical sensor data
  async getHistoricalData(hours: number = 24, limit: number = 100, sensor?: string): Promise<HistoricalData[]> {
    try {
      const params: any = { hours, limit };
      if (sensor) {
        params.sensor = sensor;
      }
      
      const response = await api.get<HistoricalData[]>('/historical-data', {
        params
      });
      return response.data;
    } catch (error) {
      console.error('Error getting historical data:', error);
      throw this.handleError(error);
    }
  }

  // Get sensor statistics
  async getSensorStats(hours: number = 24): Promise<any> {
    try {
      const response = await api.get('/sensor-stats', {
        params: { hours }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting sensor stats:', error);
      throw this.handleError(error);
    }
  }

  // Get control settings
  async getControlSettings(): Promise<ControlSettings> {
    try {
      const response = await api.get<ControlSettings>('/controls');
      return response.data;
    } catch (error) {
      console.error('Error getting control settings:', error);
      throw this.handleError(error);
    }
  }

  // Update control settings
  async updateControlSettings(settings: Partial<ControlSettings>): Promise<void> {
    try {
      await api.post('/controls', settings);
    } catch (error) {
      console.error('Error updating control settings:', error);
      throw this.handleError(error);
    }
  }

  // Get alerts
  async getAlerts(limit: number = 50): Promise<Alert[]> {
    try {
      const response = await api.get<Alert[]>('/alerts', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting alerts:', error);
      throw this.handleError(error);
    }
  }

  // Send device command
  async sendDeviceCommand(command: string, value?: any): Promise<void> {
    try {
      await api.post('/device-command', { command, value });
    } catch (error) {
      console.error('Error sending device command:', error);
      throw this.handleError(error);
    }
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await api.get('/health');
      return true;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  // Set server URL
  async setServerUrl(url: string): Promise<void> {
    api.defaults.baseURL = `${url}/api`;
    await AsyncStorage.setItem('server_url', url);
  }

  // Get server URL from storage
  async getStoredServerUrl(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem('server_url');
    } catch (error) {
      console.error('Error getting stored server URL:', error);
      return null;
    }
  }

  // Initialize API service
  async initialize(): Promise<void> {
    const storedUrl = await this.getStoredServerUrl();
    if (storedUrl) {
      api.defaults.baseURL = `${storedUrl}/api`;
    }
  }

  // Error handler
  private handleError(error: any): Error {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.error || error.response.data?.message || `HTTP ${error.response.status}`;
      return new Error(message);
    } else if (error.request) {
      // Request was made but no response received
      return new Error('Network error: Unable to connect to server');
    } else {
      // Something else happened
      return new Error(error.message || 'Unknown error occurred');
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Mock data for development/testing
export const mockSensorData: SensorData = {
  temperature: 25.5,
  humidity: 68.2,
  ph: 6.1,
  tds: 850,
  light_intensity: 75,
  co2: 450,
  soil_moisture: 82,
  water_level: 90,
  battery_level: 85,
  solar_power: 120
};

export const mockDeviceStatus: DeviceStatus = {
  esp32_connected: true,
  last_heartbeat: new Date().toISOString(),
  battery_level: 85,
  solar_power: 120
};

export const mockControlSettings: ControlSettings = {
  pump_auto: true,
  fan_auto: true,
  curtain_auto: true,
  pump_status: false,
  fan_status: true,
  curtain_status: false,
  temp_threshold_min: 20.0,
  temp_threshold_max: 30.0,
  humidity_threshold_min: 60.0,
  humidity_threshold_max: 80.0,
  ph_threshold_min: 5.5,
  ph_threshold_max: 6.5
};

export const mockAlerts: Alert[] = [
  {
    id: 1,
    timestamp: new Date().toISOString(),
    alert_type: 'TEMPERATURE',
    message: 'Temperature is within optimal range',
    severity: 'INFO'
  },
  {
    id: 2,
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    alert_type: 'PH',
    message: 'pH level needs adjustment: 7.2',
    severity: 'WARNING'
  }
];

export default apiService;