import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, RefreshControl } from 'react-native';

const API_BASE_URL = 'http://YOUR_FLASK_SERVER_IP:5000/api/mobile'; // sesuaikan dengan ip flask yang baru

interface SensorData {
  temperature: number;
  humidity: number;
  ph: number;
  tds: number;
  ldr: number;
  co2: number;
  timestamp: string;
}

export default function DashboardScreen() { // Pastikan export default function di sini
  const [sensorData, setSensorData] = useState<SensorData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/sensor_data`);
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("No sensor data available yet.");
        }
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data: SensorData = await response.json();
      setSensorData(data);
    } catch (err: any) {
      console.error('Error fetching sensor data:', err);
      setError(`Failed to fetch sensor data: ${err.message}`);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh data setiap 10 detik
    return () => clearInterval(interval); // Cleanup on unmount
  }, []);

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    fetchData();
  }, []);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text>Loading sensor data...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <Text style={styles.header}>Terraponix Dashboard</Text>
      {error && <Text style={styles.errorText}>{error}</Text>}
      {sensorData ? (
        <View style={styles.dataContainer}>
          <Text style={styles.dataText}>Temperature: {sensorData.temperature}°C</Text>
          <Text style={styles.dataText}>Humidity: {sensorData.humidity}%</Text>
          <Text style={styles.dataText}>pH: {sensorData.ph}</Text>
          <Text style={styles.dataText}>TDS: {sensorData.tds} ppm</Text>
          <Text style={styles.dataText}>LDR: {sensorData.ldr}</Text>
          <Text style={styles.dataText}>CO₂: {sensorData.co2} ppm</Text>
          <Text style={styles.timestampText}>Last updated: {new Date(sensorData.timestamp).toLocaleString()}</Text>
        </View>
      ) : (
        <Text style={styles.noDataText}>No sensor data available. Pull down to refresh.</Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 20,
    backgroundColor: '#f5f5f5',
    alignItems: 'center',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 30,
    color: '#333',
  },
  dataContainer: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 20,
    width: '90%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  dataText: {
    fontSize: 20,
    marginBottom: 10,
    color: '#555',
  },
  timestampText: {
    fontSize: 14,
    color: '#888',
    marginTop: 15,
    textAlign: 'right',
  },
  noDataText: {
    fontSize: 18,
    color: '#888',
    marginTop: 50,
  },
  errorText: {
    color: 'red',
    fontSize: 16,
    marginBottom: 20,
    textAlign: 'center',
  }
});