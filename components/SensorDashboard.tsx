import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity, 
  ActivityIndicator,
  Alert
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import SensorCard from './SensorCard';
import SensorChart from './SensorChart';
import { apiService, SensorData, HistoricalData } from '../services/apiService';

interface SensorDashboardProps {
  sensorData: SensorData | null;
}

type ViewMode = 'cards' | 'charts';

const SensorDashboard: React.FC<SensorDashboardProps> = ({ sensorData }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('cards');
  const [historicalData, setHistoricalData] = useState<HistoricalData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const fetchHistoricalData = async () => {
    setLoading(true);
    try {
      const data = await apiService.getHistoricalData(24, 50);
      setHistoricalData(data);
    } catch (error) {
      console.error('Error fetching historical data:', error);
      Alert.alert('Error', 'Failed to load historical data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (viewMode === 'charts') {
      fetchHistoricalData();
    }
  }, [viewMode]);

  const getSensorStatus = (value: number, min: number, max: number) => {
    if (value < min || value > max) {
      return value < min * 0.8 || value > max * 1.2 ? 'critical' : 'warning';
    }
    return 'normal';
  };

  const sensorConfigs = [
    {
      title: 'Temperature',
      value: sensorData?.temperature || 0,
      unit: '°C',
      icon: 'thermometer-outline' as keyof typeof Ionicons.glyphMap,
      min: 20,
      max: 30,
      dataKey: 'temperature' as keyof HistoricalData,
      color: '#FF6B6B',
      chartType: 'line' as const
    },
    {
      title: 'Humidity',
      value: sensorData?.humidity || 0,
      unit: '%',
      icon: 'water-outline' as keyof typeof Ionicons.glyphMap,
      min: 60,
      max: 80,
      dataKey: 'humidity' as keyof HistoricalData,
      color: '#4ECDC4',
      chartType: 'line' as const
    },
    {
      title: 'pH Level',
      value: sensorData?.ph || 0,
      unit: 'pH',
      icon: 'flask-outline' as keyof typeof Ionicons.glyphMap,
      min: 5.5,
      max: 6.5,
      dataKey: 'ph' as keyof HistoricalData,
      color: '#45B7D1',
      chartType: 'line' as const
    },
    {
      title: 'TDS',
      value: sensorData?.tds || 0,
      unit: 'ppm',
      icon: 'analytics-outline' as keyof typeof Ionicons.glyphMap,
      min: 800,
      max: 1200,
      dataKey: 'tds' as keyof HistoricalData,
      color: '#96CEB4',
      chartType: 'bar' as const
    },
    {
      title: 'Light Intensity',
      value: sensorData?.light_intensity || 0,
      unit: 'lux',
      icon: 'sunny-outline' as keyof typeof Ionicons.glyphMap,
      min: 20000,
      max: 50000,
      dataKey: 'light_intensity' as keyof HistoricalData,
      color: '#FFEAA7',
      chartType: 'line' as const
    },
    {
      title: 'CO2 Level',
      value: sensorData?.co2 || 0,
      unit: 'ppm',
      icon: 'cloud-outline' as keyof typeof Ionicons.glyphMap,
      min: 800,
      max: 1200,
      dataKey: 'co2' as keyof HistoricalData,
      color: '#DDA0DD',
      chartType: 'line' as const
    },
    {
      title: 'Soil Moisture',
      value: sensorData?.soil_moisture || 0,
      unit: '%',
      icon: 'leaf-outline' as keyof typeof Ionicons.glyphMap,
      min: 40,
      max: 70,
      dataKey: 'soil_moisture' as keyof HistoricalData,
      color: '#8FBC8F',
      chartType: 'bar' as const
    },
    {
      title: 'Water Level',
      value: sensorData?.water_level || 0,
      unit: '%',
      icon: 'water' as keyof typeof Ionicons.glyphMap,
      min: 30,
      max: 90,
      dataKey: 'water_level' as keyof HistoricalData,
      color: '#87CEEB',
      chartType: 'bar' as const
    }
  ];

  const renderViewToggle = () => (
    <View style={styles.toggleContainer}>
      <TouchableOpacity
        style={[styles.toggleButton, viewMode === 'cards' && styles.toggleButtonActive]}
        onPress={() => setViewMode('cards')}
      >
        <Ionicons 
          name="grid-outline" 
          size={20} 
          color={viewMode === 'cards' ? '#fff' : '#666'} 
        />
        <Text style={[styles.toggleText, viewMode === 'cards' && styles.toggleTextActive]}>
          Cards
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.toggleButton, viewMode === 'charts' && styles.toggleButtonActive]}
        onPress={() => setViewMode('charts')}
      >
        <Ionicons 
          name="analytics-outline" 
          size={20} 
          color={viewMode === 'charts' ? '#fff' : '#666'} 
        />
        <Text style={[styles.toggleText, viewMode === 'charts' && styles.toggleTextActive]}>
          Charts
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderCards = () => (
    <View style={styles.cardsContainer}>
      {sensorConfigs.map((config, index) => (
        <SensorCard
          key={index}
          title={config.title}
          value={config.value}
          unit={config.unit}
          icon={config.icon}
          status={getSensorStatus(config.value, config.min, config.max)}
          min={config.min}
          max={config.max}
        />
      ))}
    </View>
  );

  const renderCharts = () => {
    if (loading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4ECDC4" />
          <Text style={styles.loadingText}>Loading charts...</Text>
        </View>
      );
    }

    if (historicalData.length === 0) {
      return (
        <View style={styles.noDataContainer}>
          <Ionicons name="analytics-outline" size={64} color="#ccc" />
          <Text style={styles.noDataText}>No historical data available</Text>
          <TouchableOpacity style={styles.retryButton} onPress={fetchHistoricalData}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      );
    }

    return (
      <ScrollView style={styles.chartsContainer}>
        {sensorConfigs.map((config, index) => (
          <SensorChart
            key={index}
            data={historicalData}
            title={config.title}
            dataKey={config.dataKey}
            color={config.color}
            unit={config.unit}
            chartType={config.chartType}
          />
        ))}
      </ScrollView>
    );
  };

  return (
    <View style={styles.container}>
      {renderViewToggle()}
      {viewMode === 'cards' ? renderCards() : renderCharts()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  toggleContainer: {
    flexDirection: 'row',
    backgroundColor: '#f8f9fa',
    borderRadius: 25,
    padding: 4,
    margin: 16,
    marginBottom: 8,
  },
  toggleButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 20,
  },
  toggleButtonActive: {
    backgroundColor: '#4ECDC4',
  },
  toggleText: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  toggleTextActive: {
    color: '#fff',
  },
  cardsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingHorizontal: 8,
  },
  chartsContainer: {
    flex: 1,
    paddingHorizontal: 8,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 50,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  noDataContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 50,
  },
  noDataText: {
    fontSize: 16,
    color: '#666',
    marginTop: 16,
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: '#4ECDC4',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 20,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default SensorDashboard;