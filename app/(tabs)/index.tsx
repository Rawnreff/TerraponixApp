import React, { useEffect, useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  ActivityIndicator, 
  RefreshControl,
  TouchableOpacity,
  Alert,
  Switch
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import SensorCard from '../../components/SensorCard';
import ChartCard from '../../components/ChartCard';
import TrendCard from '../../components/TrendCard';
import OverviewPanel from '../../components/OverviewPanel';
import { apiService, SensorData, DeviceStatus } from '../../services/apiService';

export default function DashboardScreen() {
  const [sensorData, setSensorData] = useState<SensorData | null>(null);
  const [deviceStatus, setDeviceStatus] = useState<DeviceStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [sensorStats, setSensorStats] = useState<any>({});
  const [showDetailedCharts, setShowDetailedCharts] = useState<boolean>(false);

  const fetchData = async () => {
    setError(null);
    try {
      const [currentDataResponse, statsResponse] = await Promise.all([
        apiService.getCurrentData(),
        apiService.getSensorStats(24)
      ]);
      
      setSensorData(currentDataResponse.sensor_data);
      setDeviceStatus(currentDataResponse.device_status);
      setLastUpdate(new Date(currentDataResponse.timestamp).toLocaleString());
      setSensorStats(statsResponse);
    } catch (err: any) {
      console.error('Error fetching sensor data:', err);
      setError(err.message);
      // Use mock data for development when server is not available
      if (err.message.includes('Network error')) {
        const { mockSensorData, mockDeviceStatus } = await import('../../services/apiService');
        setSensorData(mockSensorData);
        setDeviceStatus(mockDeviceStatus);
        setLastUpdate(new Date().toLocaleString());
        setSensorStats({
          temperature: { avg: 25.5, min: 20.2, max: 28.9 },
          humidity: { avg: 68.2, min: 55.1, max: 82.3 },
          ph: { avg: 6.1, min: 5.8, max: 6.4 },
          tds: { avg: 850, min: 750, max: 950 },
          light_intensity: { avg: 75, min: 45, max: 95 },
          co2: { avg: 450, min: 380, max: 520 },
        });
        setError('Using mock data - Server not available');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    // Initialize API service
    apiService.initialize().then(() => {
      fetchData();
    });
    
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    fetchData();
  }, []);

  const getSensorStatus = (value: number, min: number, max: number) => {
    if (value < min || value > max) {
      return value < min * 0.8 || value > max * 1.2 ? 'critical' : 'warning';
    }
    return 'normal';
  };

  const handleSystemAlert = () => {
    if (!deviceStatus?.esp32_connected) {
      Alert.alert(
        'Device Disconnected',
        'ESP32 device is not connected. Please check the device connection.',
        [{ text: 'OK' }]
      );
    } else {
      Alert.alert(
        'System Status',
        'All systems are operating normally.',
        [{ text: 'OK' }]
      );
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4ECDC4" />
        <Text style={styles.loadingText}>Loading Terraponix data...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl 
          refreshing={refreshing} 
          onRefresh={onRefresh}
          colors={['#4ECDC4']}
          tintColor="#4ECDC4"
        />
      }
    >
             {/* Header */}
       <View style={styles.header}>
         <View style={styles.titleContainer}>
           <Text style={styles.title}>🌱 Terraponix</Text>
           <Text style={styles.subtitle}>Smart Farm System</Text>
         </View>
                   <View style={styles.headerControls}>
            <TouchableOpacity
              style={[styles.viewToggleButton, showDetailedCharts && styles.activeToggle]}
              onPress={() => setShowDetailedCharts(!showDetailedCharts)}
            >
              <Ionicons 
                name={showDetailedCharts ? "bar-chart" : "analytics"} 
                size={18} 
                color={showDetailedCharts ? '#FFF' : '#666'} 
              />
              <Text style={[styles.toggleText, showDetailedCharts && styles.activeToggleText]}>
                {showDetailedCharts ? 'Detailed' : 'Trends'}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.statusButton}
              onPress={handleSystemAlert}
            >
              <Ionicons 
                name={deviceStatus?.esp32_connected ? "checkmark-circle" : "alert-circle"} 
                size={24} 
                color={deviceStatus?.esp32_connected ? "#4ECDC4" : "#FF6B6B"} 
              />
            </TouchableOpacity>
          </View>
       </View>

      {/* Device Status */}
      {deviceStatus && (
        <View style={styles.deviceStatus}>
          <View style={styles.statusRow}>
            <View style={styles.statusItem}>
              <Ionicons name="wifi" size={16} color={deviceStatus.esp32_connected ? "#4ECDC4" : "#FF6B6B"} />
              <Text style={styles.statusText}>
                {deviceStatus.esp32_connected ? 'Connected' : 'Disconnected'}
              </Text>
            </View>
            <View style={styles.statusItem}>
              <Ionicons name="battery-half" size={16} color="#4ECDC4" />
              <Text style={styles.statusText}>{deviceStatus.battery_level}%</Text>
            </View>
            <View style={styles.statusItem}>
              <Ionicons name="sunny" size={16} color="#FFB347" />
              <Text style={styles.statusText}>{deviceStatus.solar_power}W</Text>
            </View>
          </View>
        </View>
      )}

             {/* Error Message */}
       {error && (
         <View style={styles.errorContainer}>
           <Ionicons name="warning" size={20} color="#FF6B6B" />
           <Text style={styles.errorText}>{error}</Text>
         </View>
       )}

       {/* Overview Panel */}
       {sensorData && (
         <OverviewPanel sensorData={sensorData} />
       )}

       {/* Sensor Data */}
                {sensorData ? (
          <>
            <Text style={styles.sectionTitle}>
              {showDetailedCharts ? 'Detailed Sensor Analysis' : 'Sensor Trends & Indicators'}
            </Text>
            
            {showDetailedCharts ? (
              /* Detailed Chart View */
              <>
                <ChartCard
                  title="Temperature"
                  sensorType="temperature"
                  unit="°C"
                  icon="thermometer"
                  color="#FF6B6B"
                  currentValue={sensorData.temperature}
                  min={20}
                  max={30}
                />
                <ChartCard
                  title="Humidity"
                  sensorType="humidity"
                  unit="%"
                  icon="water"
                  color="#4ECDC4"
                  currentValue={sensorData.humidity}
                  min={60}
                  max={80}
                />
                <ChartCard
                  title="pH Level"
                  sensorType="ph"
                  unit=""
                  icon="flask"
                  color="#45B7D1"
                  currentValue={sensorData.ph}
                  min={5.5}
                  max={6.5}
                />
                <ChartCard
                  title="TDS (Nutrients)"
                  sensorType="tds"
                  unit="ppm"
                  icon="analytics"
                  color="#96CEB4"
                  currentValue={sensorData.tds}
                  min={800}
                  max={1200}
                />
                <ChartCard
                  title="Light Intensity"
                  sensorType="light_intensity"
                  unit="%"
                  icon="sunny"
                  color="#FECA57"
                  currentValue={sensorData.light_intensity}
                  min={40}
                  max={80}
                />
                <ChartCard
                  title="CO₂ Level"
                  sensorType="co2"
                  unit="ppm"
                  icon="cloud"
                  color="#A29BFE"
                  currentValue={sensorData.co2}
                  min={300}
                  max={600}
                />
                
                {/* Additional Sensors Charts */}
                {sensorData.soil_moisture !== undefined && (
                  <ChartCard
                    title="Soil Moisture"
                    sensorType="soil_moisture"
                    unit="%"
                    icon="leaf"
                    color="#6C5CE7"
                    currentValue={sensorData.soil_moisture}
                    min={70}
                    max={90}
                  />
                )}
                {sensorData.water_level !== undefined && (
                  <ChartCard
                    title="Water Level"
                    sensorType="water_level"
                    unit="%"
                    icon="water-outline"
                    color="#00B894"
                    currentValue={sensorData.water_level}
                    min={50}
                    max={90}
                  />
                )}
              </>
            ) : (
              /* Trend View - Default */
              <>
                <TrendCard
                  title="Temperature"
                  sensorType="temperature"
                  unit="°C"
                  icon="thermometer"
                  color="#FF6B6B"
                  currentValue={sensorData.temperature}
                  min={20}
                  max={30}
                />
                <TrendCard
                  title="Humidity"
                  sensorType="humidity"
                  unit="%"
                  icon="water"
                  color="#4ECDC4"
                  currentValue={sensorData.humidity}
                  min={60}
                  max={80}
                />
                <TrendCard
                  title="pH Level"
                  sensorType="ph"
                  unit=""
                  icon="flask"
                  color="#45B7D1"
                  currentValue={sensorData.ph}
                  min={5.5}
                  max={6.5}
                />
                <TrendCard
                  title="TDS (Nutrients)"
                  sensorType="tds"
                  unit="ppm"
                  icon="analytics"
                  color="#96CEB4"
                  currentValue={sensorData.tds}
                  min={800}
                  max={1200}
                />
                <TrendCard
                  title="Light Intensity"
                  sensorType="light_intensity"
                  unit="%"
                  icon="sunny"
                  color="#FECA57"
                  currentValue={sensorData.light_intensity}
                  min={40}
                  max={80}
                />
                <TrendCard
                  title="CO₂ Level"
                  sensorType="co2"
                  unit="ppm"
                  icon="cloud"
                  color="#A29BFE"
                  currentValue={sensorData.co2}
                  min={300}
                  max={600}
                />
                
                {/* Additional Sensors Trends */}
                {sensorData.soil_moisture !== undefined && (
                  <TrendCard
                    title="Soil Moisture"
                    sensorType="soil_moisture"
                    unit="%"
                    icon="leaf"
                    color="#6C5CE7"
                    currentValue={sensorData.soil_moisture}
                    min={70}
                    max={90}
                  />
                )}
                {sensorData.water_level !== undefined && (
                  <TrendCard
                    title="Water Level"
                    sensorType="water_level"
                    unit="%"
                    icon="water-outline"
                    color="#00B894"
                    currentValue={sensorData.water_level}
                    min={50}
                    max={90}
                  />
                )}
              </>
            )}
          </>
        ) : (
        <View style={styles.noDataContainer}>
          <Ionicons name="alert-circle-outline" size={48} color="#CCC" />
          <Text style={styles.noDataText}>No sensor data available</Text>
          <Text style={styles.noDataSubtext}>Pull down to refresh</Text>
        </View>
      )}

      {/* Last Update */}
      <View style={styles.footer}>
        <Ionicons name="time" size={16} color="#888" />
        <Text style={styles.lastUpdate}>Last updated: {lastUpdate}</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F8F9FA',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 60,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E8E8E8',
  },
  titleContainer: {
    flex: 1,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  headerControls: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  viewToggleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0F0F0',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 12,
  },
  activeToggle: {
    backgroundColor: '#4ECDC4',
  },
  toggleText: {
    marginLeft: 6,
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
  },
  activeToggleText: {
    color: '#FFF',
  },
  statusButton: {
    padding: 8,
  },
  deviceStatus: {
    backgroundColor: '#FFF',
    marginHorizontal: 20,
    marginTop: 16,
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statusItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    marginLeft: 6,
    fontSize: 14,
    color: '#333',
    fontWeight: '500',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFE5E5',
    marginHorizontal: 20,
    marginTop: 16,
    padding: 12,
    borderRadius: 8,
  },
  errorText: {
    color: '#FF6B6B',
    fontSize: 14,
    marginLeft: 8,
    flex: 1,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 24,
    marginHorizontal: 20,
    marginBottom: 8,
  },
  sensorsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
  },
  noDataContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
    marginTop: 40,
  },
  noDataText: {
    fontSize: 18,
    color: '#CCC',
    marginTop: 16,
    fontWeight: '500',
  },
  noDataSubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    marginTop: 20,
  },
  lastUpdate: {
    fontSize: 12,
    color: '#888',
    marginLeft: 6,
  },
});