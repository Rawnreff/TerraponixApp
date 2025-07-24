import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
  Alert,
  TouchableOpacity,
  TextInput,
  Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import ControlCard from '../../components/ControlCard';
import { apiService, ControlSettings } from '../../services/apiService';

export default function ControlScreen() {
  const [controls, setControls] = useState<ControlSettings | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [settingsModalVisible, setSettingsModalVisible] = useState<boolean>(false);
  const [tempSettings, setTempSettings] = useState<ControlSettings | null>(null);

  const fetchControlData = async () => {
    setError(null);
    try {
      const response = await apiService.getControlSettings();
      setControls(response);
    } catch (err: any) {
      console.error('Error fetching control data:', err);
      setError(err.message);
      // Use mock data for development when server is not available
      if (err.message.includes('Network error')) {
        const { mockControlSettings } = await import('../../services/apiService');
        setControls(mockControlSettings);
        setError('Using mock data - Server not available');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    apiService.initialize().then(() => {
      fetchControlData();
    });
  }, []);

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    fetchControlData();
  }, []);

  const updateControlSetting = async (key: string, value: boolean) => {
    if (!controls) return;

    const updatedControls = { ...controls, [key]: value };
    setControls(updatedControls);

    try {
      await apiService.updateControlSettings(updatedControls);
    } catch (err: any) {
      console.error('Error updating control:', err);
      // Revert on error
      setControls(controls);
      Alert.alert('Error', 'Failed to update control settings');
    }
  };

  const sendDeviceCommand = async (command: string, value?: any) => {
    try {
      await apiService.sendDeviceCommand(command, value);
      Alert.alert('Success', `Command ${command} sent successfully`);
    } catch (err: any) {
      console.error('Error sending command:', err);
      Alert.alert('Error', 'Failed to send command to device');
    }
  };

  const openSettingsModal = () => {
    if (controls) {
      setTempSettings({ ...controls });
      setSettingsModalVisible(true);
    }
  };

  const saveThresholdSettings = async () => {
    if (!tempSettings) return;

    try {
      await apiService.updateControlSettings(tempSettings);
      setControls(tempSettings);
      setSettingsModalVisible(false);
      Alert.alert('Success', 'Threshold settings updated successfully');
    } catch (err: any) {
      console.error('Error updating thresholds:', err);
      Alert.alert('Error', 'Failed to update threshold settings');
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4ECDC4" />
        <Text style={styles.loadingText}>Loading control settings...</Text>
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
          <Text style={styles.title}>🎛️ Device Controls</Text>
          <Text style={styles.subtitle}>Manage your Terraponix system</Text>
        </View>
        <TouchableOpacity
          style={styles.settingsButton}
          onPress={openSettingsModal}
        >
          <Ionicons name="settings" size={24} color="#666" />
        </TouchableOpacity>
      </View>

      {/* Error Message */}
      {error && (
        <View style={styles.errorContainer}>
          <Ionicons name="warning" size={20} color="#FF6B6B" />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {/* Device Controls */}
      {controls ? (
        <>
          <Text style={styles.sectionTitle}>Automated Systems</Text>
          <View style={styles.controlsGrid}>
            <ControlCard
              title="Water Pump"
              icon="water"
              isActive={controls.pump_status}
              isAuto={controls.pump_auto}
              onToggle={() => {
                updateControlSetting('pump_status', !controls.pump_status);
                sendDeviceCommand('pump', !controls.pump_status);
              }}
              onAutoToggle={() => updateControlSetting('pump_auto', !controls.pump_auto)}
            />
            <ControlCard
              title="Ventilation Fan"
              icon="fan"
              isActive={controls.fan_status}
              isAuto={controls.fan_auto}
              onToggle={() => {
                updateControlSetting('fan_status', !controls.fan_status);
                sendDeviceCommand('fan', !controls.fan_status);
              }}
              onAutoToggle={() => updateControlSetting('fan_auto', !controls.fan_auto)}
            />
            <ControlCard
              title="Solar Curtain"
              icon="sunny-outline"
              isActive={controls.curtain_status}
              isAuto={controls.curtain_auto}
              onToggle={() => {
                updateControlSetting('curtain_status', !controls.curtain_status);
                sendDeviceCommand('curtain', !controls.curtain_status);
              }}
              onAutoToggle={() => updateControlSetting('curtain_auto', !controls.curtain_auto)}
            />
          </View>

          {/* Quick Actions */}
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.quickActions}>
            <TouchableOpacity
              style={[styles.actionButton, styles.primaryButton]}
              onPress={() => sendDeviceCommand('reset_system')}
            >
              <Ionicons name="refresh" size={20} color="#FFF" />
              <Text style={styles.actionButtonText}>Reset System</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionButton, styles.warningButton]}
              onPress={() => {
                Alert.alert(
                  'Emergency Stop',
                  'This will stop all automated systems. Are you sure?',
                  [
                    { text: 'Cancel', style: 'cancel' },
                    {
                      text: 'Stop',
                      style: 'destructive',
                      onPress: () => sendDeviceCommand('emergency_stop')
                    }
                  ]
                );
              }}
            >
              <Ionicons name="stop" size={20} color="#FFF" />
              <Text style={styles.actionButtonText}>Emergency Stop</Text>
            </TouchableOpacity>
          </View>

          {/* Current Thresholds */}
          <Text style={styles.sectionTitle}>Current Thresholds</Text>
          <View style={styles.thresholdContainer}>
            <View style={styles.thresholdRow}>
              <Text style={styles.thresholdLabel}>Temperature:</Text>
              <Text style={styles.thresholdValue}>
                {controls.temp_threshold_min}°C - {controls.temp_threshold_max}°C
              </Text>
            </View>
            <View style={styles.thresholdRow}>
              <Text style={styles.thresholdLabel}>Humidity:</Text>
              <Text style={styles.thresholdValue}>
                {controls.humidity_threshold_min}% - {controls.humidity_threshold_max}%
              </Text>
            </View>
            <View style={styles.thresholdRow}>
              <Text style={styles.thresholdLabel}>pH Level:</Text>
              <Text style={styles.thresholdValue}>
                {controls.ph_threshold_min} - {controls.ph_threshold_max}
              </Text>
            </View>
          </View>
        </>
      ) : (
        <View style={styles.noDataContainer}>
          <Ionicons name="alert-circle-outline" size={48} color="#CCC" />
          <Text style={styles.noDataText}>No control data available</Text>
          <Text style={styles.noDataSubtext}>Pull down to refresh</Text>
        </View>
      )}

      {/* Settings Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={settingsModalVisible}
        onRequestClose={() => setSettingsModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Threshold Settings</Text>
              <TouchableOpacity
                onPress={() => setSettingsModalVisible(false)}
              >
                <Ionicons name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>

            {tempSettings && (
              <ScrollView style={styles.modalBody}>
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Temperature Range (°C)</Text>
                  <View style={styles.rangeInput}>
                    <TextInput
                      style={styles.input}
                      value={tempSettings.temp_threshold_min.toString()}
                      onChangeText={(text) => setTempSettings({
                        ...tempSettings,
                        temp_threshold_min: parseFloat(text) || 0
                      })}
                      keyboardType="numeric"
                      placeholder="Min"
                    />
                    <Text style={styles.rangeSeparator}>-</Text>
                    <TextInput
                      style={styles.input}
                      value={tempSettings.temp_threshold_max.toString()}
                      onChangeText={(text) => setTempSettings({
                        ...tempSettings,
                        temp_threshold_max: parseFloat(text) || 0
                      })}
                      keyboardType="numeric"
                      placeholder="Max"
                    />
                  </View>
                </View>

                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Humidity Range (%)</Text>
                  <View style={styles.rangeInput}>
                    <TextInput
                      style={styles.input}
                      value={tempSettings.humidity_threshold_min.toString()}
                      onChangeText={(text) => setTempSettings({
                        ...tempSettings,
                        humidity_threshold_min: parseFloat(text) || 0
                      })}
                      keyboardType="numeric"
                      placeholder="Min"
                    />
                    <Text style={styles.rangeSeparator}>-</Text>
                    <TextInput
                      style={styles.input}
                      value={tempSettings.humidity_threshold_max.toString()}
                      onChangeText={(text) => setTempSettings({
                        ...tempSettings,
                        humidity_threshold_max: parseFloat(text) || 0
                      })}
                      keyboardType="numeric"
                      placeholder="Max"
                    />
                  </View>
                </View>

                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>pH Range</Text>
                  <View style={styles.rangeInput}>
                    <TextInput
                      style={styles.input}
                      value={tempSettings.ph_threshold_min.toString()}
                      onChangeText={(text) => setTempSettings({
                        ...tempSettings,
                        ph_threshold_min: parseFloat(text) || 0
                      })}
                      keyboardType="numeric"
                      placeholder="Min"
                    />
                    <Text style={styles.rangeSeparator}>-</Text>
                    <TextInput
                      style={styles.input}
                      value={tempSettings.ph_threshold_max.toString()}
                      onChangeText={(text) => setTempSettings({
                        ...tempSettings,
                        ph_threshold_max: parseFloat(text) || 0
                      })}
                      keyboardType="numeric"
                      placeholder="Max"
                    />
                  </View>
                </View>
              </ScrollView>
            )}

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => setSettingsModalVisible(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.saveButton]}
                onPress={saveThresholdSettings}
              >
                <Text style={styles.saveButtonText}>Save</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
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
  settingsButton: {
    padding: 8,
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
  controlsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    minWidth: 140,
    justifyContent: 'center',
  },
  primaryButton: {
    backgroundColor: '#4ECDC4',
  },
  warningButton: {
    backgroundColor: '#FF6B6B',
  },
  actionButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 8,
  },
  thresholdContainer: {
    backgroundColor: '#FFF',
    marginHorizontal: 20,
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  thresholdRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  thresholdLabel: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  thresholdValue: {
    fontSize: 16,
    color: '#4ECDC4',
    fontWeight: '600',
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
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalContent: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 20,
    width: '90%',
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  modalBody: {
    maxHeight: 400,
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  rangeInput: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#E8E8E8',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    backgroundColor: '#FFF',
  },
  rangeSeparator: {
    marginHorizontal: 12,
    fontSize: 16,
    color: '#666',
  },
  modalFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
  },
  modalButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginHorizontal: 8,
  },
  cancelButton: {
    backgroundColor: '#E8E8E8',
  },
  saveButton: {
    backgroundColor: '#4ECDC4',
  },
  cancelButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  saveButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
});