import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface SensorOverview {
  temperature: number;
  humidity: number;
  ph: number;
  tds: number;
  light_intensity: number;
  co2: number;
  soil_moisture?: number;
  water_level?: number;
}

interface OverviewPanelProps {
  sensorData: SensorOverview;
}

const OverviewPanel: React.FC<OverviewPanelProps> = ({ sensorData }) => {
  const getSensorStatus = (value: number, min: number, max: number) => {
    if (value < min || value > max) {
      return value < min * 0.8 || value > max * 1.2 ? 'critical' : 'warning';
    }
    return 'normal';
  };

  const getStatusColor = (status: 'normal' | 'warning' | 'critical') => {
    switch (status) {
      case 'critical': return '#FF6B6B';
      case 'warning': return '#FFB347';
      case 'normal': return '#4ECDC4';
    }
  };

  const formatValue = (value: number, type: string) => {
    if (type === 'ph') return value.toFixed(1);
    if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
    return Math.round(value).toString();
  };

  const sensors = [
    {
      key: 'temperature',
      icon: 'thermometer' as const,
      value: sensorData.temperature,
      unit: '°C',
      min: 20,
      max: 30,
      color: '#FF6B6B'
    },
    {
      key: 'humidity',
      icon: 'water' as const,
      value: sensorData.humidity,
      unit: '%',
      min: 60,
      max: 80,
      color: '#4ECDC4'
    },
    {
      key: 'ph',
      icon: 'flask' as const,
      value: sensorData.ph,
      unit: '',
      min: 5.5,
      max: 6.5,
      color: '#45B7D1'
    },
    {
      key: 'light_intensity',
      icon: 'sunny' as const,
      value: sensorData.light_intensity,
      unit: '%',
      min: 40,
      max: 80,
      color: '#FECA57'
    },
    {
      key: 'co2',
      icon: 'cloud' as const,
      value: sensorData.co2,
      unit: 'ppm',
      min: 300,
      max: 600,
      color: '#A29BFE'
    },
    {
      key: 'tds',
      icon: 'analytics' as const,
      value: sensorData.tds,
      unit: 'ppm',
      min: 800,
      max: 1200,
      color: '#96CEB4'
    }
  ];

  // Calculate overall system health
  const getOverallHealth = () => {
    const statuses = sensors.map(sensor => 
      getSensorStatus(sensor.value, sensor.min, sensor.max)
    );
    
    const criticalCount = statuses.filter(s => s === 'critical').length;
    const warningCount = statuses.filter(s => s === 'warning').length;
    
    if (criticalCount > 0) return { status: 'critical', text: 'Critical Issues', count: criticalCount };
    if (warningCount > 0) return { status: 'warning', text: 'Needs Attention', count: warningCount };
    return { status: 'normal', text: 'All Systems Normal', count: 0 };
  };

  const overallHealth = getOverallHealth();

  return (
    <View style={styles.container}>
      {/* Overall System Health */}
      <View style={styles.healthHeader}>
        <View style={styles.healthIndicator}>
          <Ionicons 
            name={overallHealth.status === 'normal' ? 'checkmark-circle' : 'alert-circle'} 
            size={20} 
            color={getStatusColor(overallHealth.status)} 
          />
          <Text style={[styles.healthText, { color: getStatusColor(overallHealth.status) }]}>
            {overallHealth.text}
          </Text>
        </View>
        {overallHealth.count > 0 && (
          <View style={[styles.alertBadge, { backgroundColor: getStatusColor(overallHealth.status) }]}>
            <Text style={styles.alertCount}>{overallHealth.count}</Text>
          </View>
        )}
      </View>

      {/* Sensor Grid */}
      <View style={styles.sensorsGrid}>
        {sensors.map((sensor) => {
          const status = getSensorStatus(sensor.value, sensor.min, sensor.max);
          const statusColor = getStatusColor(status);
          
          return (
            <View key={sensor.key} style={styles.sensorItem}>
              <View style={[styles.sensorIcon, { backgroundColor: `${sensor.color}20` }]}>
                <Ionicons name={sensor.icon} size={16} color={sensor.color} />
              </View>
              <View style={styles.sensorInfo}>
                <Text style={styles.sensorValue}>
                  {formatValue(sensor.value, sensor.key)}
                  <Text style={styles.sensorUnit}>{sensor.unit}</Text>
                </Text>
                <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
              </View>
            </View>
          );
        })}
      </View>

      {/* Quick Stats */}
      <View style={styles.quickStats}>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>
            {sensors.filter(s => getSensorStatus(s.value, s.min, s.max) === 'normal').length}
          </Text>
          <Text style={styles.statLabel}>Normal</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={[styles.statNumber, { color: '#FFB347' }]}>
            {sensors.filter(s => getSensorStatus(s.value, s.min, s.max) === 'warning').length}
          </Text>
          <Text style={styles.statLabel}>Warning</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={[styles.statNumber, { color: '#FF6B6B' }]}>
            {sensors.filter(s => getSensorStatus(s.value, s.min, s.max) === 'critical').length}
          </Text>
          <Text style={styles.statLabel}>Critical</Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFF',
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 16,
    padding: 16,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
  },
  healthHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  healthIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  healthText: {
    marginLeft: 8,
    fontSize: 16,
    fontWeight: '600',
  },
  alertBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  alertCount: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  sensorsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  sensorItem: {
    width: '30%',
    marginBottom: 12,
    alignItems: 'center',
  },
  sensorIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 6,
  },
  sensorInfo: {
    alignItems: 'center',
    position: 'relative',
  },
  sensorValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  sensorUnit: {
    fontSize: 10,
    color: '#666',
    fontWeight: '400',
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 4,
  },
  quickStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    paddingVertical: 12,
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#4ECDC4',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  statDivider: {
    width: 1,
    height: 30,
    backgroundColor: '#E8E8E8',
  },
});

export default OverviewPanel;