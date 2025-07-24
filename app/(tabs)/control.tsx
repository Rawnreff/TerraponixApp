import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, RefreshControl, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

const API_BASE_URL = 'http://YOUR_FLASK_SERVER_IP:5000/api/mobile'; // GANTI INI!

interface DeviceStatus {
  device_id: string;
  status: boolean;
  last_updated: string;
}

export default function ControlScreen() { // Pastikan export default function di sini
  const [deviceStatuses, setDeviceStatuses] = useState<DeviceStatus[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDeviceStatus = async () => {
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/device_status`);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data: DeviceStatus[] = await response.json();
      setDeviceStatuses(data);
    } catch (err: any) {
      console.error('Error fetching device statuses:', err);
      setError(`Failed to fetch device status: ${err.message}`);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const sendCommand = async (deviceId: string, commandType: 'turn_on' | 'turn_off' | 'open' | 'close') => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/send_command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          device_id: deviceId,
          command_type: commandType,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const result = await response.json();
      console.log('Command sent:', result);
      Alert.alert('Success', `Command sent: ${commandType} for ${deviceId}`);
      fetchDeviceStatus();
    } catch (err: any) {
      console.error('Error sending command:', err);
      Alert.alert('Error', `Failed to send command: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeviceStatus();
    const interval = setInterval(fetchDeviceStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    fetchDeviceStatus();
  }, []);

  const getDeviceIcon = (deviceId: string) => {
    switch (deviceId) {
      case 'pump': return 'pump';
      case 'fan': return 'fan';
      case 'curtain': return 'blinds';
      default: return 'help-circle-outline';
    }
  };

  const getDeviceName = (deviceId: string) => {
    switch (deviceId) {
      case 'pump': return 'Nutrient Pump';
      case 'fan': return 'Ventilation Fan';
      case 'curtain': return 'Sensoric Curtain';
      default: return deviceId;
    }
  };

  if (loading && !deviceStatuses.length) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text>Loading device statuses...</Text>
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
      <Text style={styles.header}>Terraponix Controls</Text>
      {error && <Text style={styles.errorText}>{error}</Text>}
      {deviceStatuses.length > 0 ? (
        deviceStatuses.map((device) => (
          <View key={device.device_id} style={styles.deviceCard}>
            <Icon name={getDeviceIcon(device.device_id)} size={40} color="#4CAF50" />
            <View style={styles.deviceInfo}>
              <Text style={styles.deviceName}>{getDeviceName(device.device_id)}</Text>
              <Text style={styles.deviceStatus}>
                Status: <Text style={{ color: device.status ? 'green' : 'red' }}>
                  {device.status ? 'ON' : 'OFF'}
                </Text>
              </Text>
              <Text style={styles.lastUpdated}>Last updated: {new Date(device.last_updated).toLocaleTimeString()}</Text>
            </View>
            <View style={styles.buttonContainer}>
              {device.device_id === 'curtain' ? (
                <>
                  <TouchableOpacity
                    style={[styles.controlButton, styles.openButton]}
                    onPress={() => sendCommand(device.device_id, 'open')}
                  >
                    <Text style={styles.buttonText}>Open</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.controlButton, styles.closeButton]}
                    onPress={() => sendCommand(device.device_id, 'close')}
                  >
                    <Text style={styles.buttonText}>Close</Text>
                  </TouchableOpacity>
                </>
              ) : (
                <>
                  <TouchableOpacity
                    style={[styles.controlButton, styles.onButton]}
                    onPress={() => sendCommand(device.device_id, 'turn_on')}
                  >
                    <Text style={styles.buttonText}>ON</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.controlButton, styles.offButton]}
                    onPress={() => sendCommand(device.device_id, 'turn_off')}
                  >
                    <Text style={styles.buttonText}>OFF</Text>
                  </TouchableOpacity>
                </>
              )}
            </View>
          </View>
        ))
      ) : (
        <Text style={styles.noDataText}>No device statuses found. Make sure your devices are active and sending data.</Text>
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
  deviceCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    width: '95%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  deviceInfo: {
    flex: 1,
    marginLeft: 15,
  },
  deviceName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  deviceStatus: {
    fontSize: 16,
    color: '#666',
    marginBottom: 5,
  },
  lastUpdated: {
    fontSize: 12,
    color: '#888',
  },
  buttonContainer: {
    flexDirection: 'row',
    marginLeft: 10,
  },
  controlButton: {
    paddingVertical: 10,
    paddingHorizontal: 15,
    borderRadius: 5,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 10,
  },
  onButton: {
    backgroundColor: '#4CAF50', // Green
  },
  offButton: {
    backgroundColor: '#F44336', // Red
  },
  openButton: {
    backgroundColor: '#2196F3', // Blue
  },
  closeButton: {
    backgroundColor: '#FF9800', // Orange
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  noDataText: {
    fontSize: 16,
    color: '#888',
    marginTop: 50,
    textAlign: 'center',
  },
  errorText: {
    color: 'red',
    fontSize: 16,
    marginBottom: 20,
    textAlign: 'center',
  },
});