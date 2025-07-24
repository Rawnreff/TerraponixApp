import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
  TouchableOpacity,
  Alert as RNAlert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { apiService, Alert } from '../../services/apiService';

interface AlertCardProps {
  alert: Alert;
  onPress: () => void;
}

const AlertCard: React.FC<AlertCardProps> = ({ alert, onPress }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return '#FF6B6B';
      case 'WARNING':
        return '#FFB347';
      case 'INFO':
      default:
        return '#4ECDC4';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'alert-circle';
      case 'WARNING':
        return 'warning';
      case 'INFO':
      default:
        return 'information-circle';
    }
  };

  const getAlertTypeIcon = (alertType: string) => {
    switch (alertType.toLowerCase()) {
      case 'temperature':
        return 'thermometer';
      case 'humidity':
        return 'water';
      case 'ph':
        return 'flask';
      case 'tds':
        return 'analytics';
      case 'light':
        return 'sunny';
      case 'co2':
        return 'cloud';
      case 'system':
        return 'settings';
      default:
        return 'alert-circle-outline';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <TouchableOpacity style={styles.alertCard} onPress={onPress}>
      <View style={styles.alertHeader}>
        <View style={styles.alertTypeContainer}>
          <Ionicons
            name={getAlertTypeIcon(alert.alert_type)}
            size={20}
            color={getSeverityColor(alert.severity)}
          />
          <Text style={[styles.alertType, { color: getSeverityColor(alert.severity) }]}>
            {alert.alert_type}
          </Text>
        </View>
        <View style={styles.severityContainer}>
          <Ionicons
            name={getSeverityIcon(alert.severity)}
            size={16}
            color={getSeverityColor(alert.severity)}
          />
          <Text style={[styles.severity, { color: getSeverityColor(alert.severity) }]}>
            {alert.severity}
          </Text>
        </View>
      </View>
      <Text style={styles.alertMessage}>{alert.message}</Text>
      <Text style={styles.alertTime}>{formatTimestamp(alert.timestamp)}</Text>
    </TouchableOpacity>
  );
};

export default function AlertsScreen() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'ALL' | 'CRITICAL' | 'WARNING' | 'INFO'>('ALL');

  const fetchAlerts = async () => {
    setError(null);
    try {
      const response = await apiService.getAlerts(100);
      setAlerts(response);
    } catch (err: any) {
      console.error('Error fetching alerts:', err);
      setError(err.message);
      // Use mock data for development when server is not available
      if (err.message.includes('Network error')) {
        const { mockAlerts } = await import('../../services/apiService');
        // Generate more mock alerts for demo
        const additionalMockAlerts: Alert[] = [
          {
            id: 3,
            timestamp: new Date(Date.now() - 1800000).toISOString(),
            alert_type: 'HUMIDITY',
            message: 'Humidity level is too low: 45%',
            severity: 'WARNING'
          },
          {
            id: 4,
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            alert_type: 'SYSTEM',
            message: 'System started successfully',
            severity: 'INFO'
          },
          {
            id: 5,
            timestamp: new Date(Date.now() - 10800000).toISOString(),
            alert_type: 'TDS',
            message: 'TDS value is critically low: 650 ppm',
            severity: 'CRITICAL'
          }
        ];
        setAlerts([...mockAlerts, ...additionalMockAlerts]);
        setError('Using mock data - Server not available');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    apiService.initialize().then(() => {
      fetchAlerts();
    });

    // Auto refresh every 2 minutes
    const interval = setInterval(fetchAlerts, 120000);
    return () => clearInterval(interval);
  }, []);

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    fetchAlerts();
  }, []);

  const filteredAlerts = alerts.filter(alert => 
    filter === 'ALL' || alert.severity === filter
  );

  const getFilterButtonStyle = (filterType: typeof filter) => [
    styles.filterButton,
    filter === filterType && styles.activeFilterButton
  ];

  const getFilterTextStyle = (filterType: typeof filter) => [
    styles.filterButtonText,
    filter === filterType && styles.activeFilterButtonText
  ];

  const showAlertDetails = (alert: Alert) => {
    RNAlert.alert(
      `${alert.alert_type} Alert`,
      `${alert.message}\n\nSeverity: ${alert.severity}\nTime: ${new Date(alert.timestamp).toLocaleString()}`,
      [{ text: 'OK' }]
    );
  };

  const getAlertCounts = () => {
    const counts = {
      ALL: alerts.length,
      CRITICAL: alerts.filter(a => a.severity === 'CRITICAL').length,
      WARNING: alerts.filter(a => a.severity === 'WARNING').length,
      INFO: alerts.filter(a => a.severity === 'INFO').length,
    };
    return counts;
  };

  const alertCounts = getAlertCounts();

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4ECDC4" />
        <Text style={styles.loadingText}>Loading alerts...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.titleContainer}>
          <Text style={styles.title}>🔔 Alerts & Logs</Text>
          <Text style={styles.subtitle}>System notifications and alerts</Text>
        </View>
        <TouchableOpacity
          style={styles.clearButton}
          onPress={() => {
            RNAlert.alert(
              'Clear All Alerts',
              'This will remove all alerts from the list. Are you sure?',
              [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Clear', style: 'destructive', onPress: () => setAlerts([]) }
              ]
            );
          }}
        >
          <Ionicons name="trash-outline" size={20} color="#666" />
        </TouchableOpacity>
      </View>

      {/* Error Message */}
      {error && (
        <View style={styles.errorContainer}>
          <Ionicons name="warning" size={20} color="#FF6B6B" />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {/* Alert Summary */}
      <View style={styles.summaryContainer}>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryNumber}>{alertCounts.CRITICAL}</Text>
          <Text style={[styles.summaryLabel, { color: '#FF6B6B' }]}>Critical</Text>
        </View>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryNumber}>{alertCounts.WARNING}</Text>
          <Text style={[styles.summaryLabel, { color: '#FFB347' }]}>Warning</Text>
        </View>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryNumber}>{alertCounts.INFO}</Text>
          <Text style={[styles.summaryLabel, { color: '#4ECDC4' }]}>Info</Text>
        </View>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryNumber}>{alertCounts.ALL}</Text>
          <Text style={styles.summaryLabel}>Total</Text>
        </View>
      </View>

      {/* Filter Buttons */}
      <View style={styles.filterContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <TouchableOpacity
            style={getFilterButtonStyle('ALL')}
            onPress={() => setFilter('ALL')}
          >
            <Text style={getFilterTextStyle('ALL')}>All ({alertCounts.ALL})</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={getFilterButtonStyle('CRITICAL')}
            onPress={() => setFilter('CRITICAL')}
          >
            <Text style={getFilterTextStyle('CRITICAL')}>Critical ({alertCounts.CRITICAL})</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={getFilterButtonStyle('WARNING')}
            onPress={() => setFilter('WARNING')}
          >
            <Text style={getFilterTextStyle('WARNING')}>Warning ({alertCounts.WARNING})</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={getFilterButtonStyle('INFO')}
            onPress={() => setFilter('INFO')}
          >
            <Text style={getFilterTextStyle('INFO')}>Info ({alertCounts.INFO})</Text>
          </TouchableOpacity>
        </ScrollView>
      </View>

      {/* Alerts List */}
      <ScrollView
        style={styles.alertsList}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={['#4ECDC4']}
            tintColor="#4ECDC4"
          />
        }
      >
        {filteredAlerts.length > 0 ? (
          filteredAlerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onPress={() => showAlertDetails(alert)}
            />
          ))
        ) : (
          <View style={styles.noAlertsContainer}>
            <Ionicons name="checkmark-circle-outline" size={48} color="#4ECDC4" />
            <Text style={styles.noAlertsText}>
              {filter === 'ALL' ? 'No alerts available' : `No ${filter.toLowerCase()} alerts`}
            </Text>
            <Text style={styles.noAlertsSubtext}>
              Your system is running smoothly
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
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
  clearButton: {
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
  summaryContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  summaryCard: {
    alignItems: 'center',
    backgroundColor: '#FFF',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    minWidth: 70,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 1,
  },
  summaryNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    fontWeight: '500',
  },
  filterContainer: {
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  filterButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#E8E8E8',
    marginRight: 8,
  },
  activeFilterButton: {
    backgroundColor: '#4ECDC4',
  },
  filterButtonText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  activeFilterButtonText: {
    color: '#FFF',
  },
  alertsList: {
    flex: 1,
    paddingHorizontal: 20,
  },
  alertCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  alertTypeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  alertType: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  severityContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  severity: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  alertMessage: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
    marginBottom: 8,
  },
  alertTime: {
    fontSize: 12,
    color: '#888',
  },
  noAlertsContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
    marginTop: 40,
  },
  noAlertsText: {
    fontSize: 18,
    color: '#CCC',
    marginTop: 16,
    fontWeight: '500',
  },
  noAlertsSubtext: {
    fontSize: 14,
    color: '#999',
    marginTop: 8,
  },
});