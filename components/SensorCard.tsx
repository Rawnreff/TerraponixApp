import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface SensorCardProps {
  title: string;
  value: number | string;
  unit: string;
  icon: keyof typeof Ionicons.glyphMap;
  status: 'normal' | 'warning' | 'critical';
  min?: number;
  max?: number;
}

const SensorCard: React.FC<SensorCardProps> = ({
  title,
  value,
  unit,
  icon,
  status,
  min,
  max
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'critical':
        return '#FF6B6B';
      case 'warning':
        return '#FFB347';
      case 'normal':
      default:
        return '#4ECDC4';
    }
  };

  const getStatusBackground = () => {
    switch (status) {
      case 'critical':
        return '#FFE5E5';
      case 'warning':
        return '#FFF4E5';
      case 'normal':
      default:
        return '#E5F9F7';
    }
  };

  const formatValue = (val: number | string) => {
    if (typeof val === 'number') {
      return val.toFixed(1);
    }
    return val;
  };

  return (
    <View style={[styles.container, { backgroundColor: getStatusBackground() }]}>
      <View style={styles.header}>
        <Ionicons 
          name={icon} 
          size={24} 
          color={getStatusColor()} 
        />
        <Text style={styles.title}>{title}</Text>
      </View>
      
      <View style={styles.content}>
        <Text style={[styles.value, { color: getStatusColor() }]}>
          {formatValue(value)}
        </Text>
        <Text style={styles.unit}>{unit}</Text>
      </View>
      
      {(min !== undefined && max !== undefined) && (
        <View style={styles.range}>
          <Text style={styles.rangeText}>
            Range: {min} - {max} {unit}
          </Text>
        </View>
      )}
      
      <View style={[styles.statusIndicator, { backgroundColor: getStatusColor() }]} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    minWidth: 150,
    maxWidth: 180,
    margin: 8,
    padding: 16,
    borderRadius: 12,
    position: 'relative',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginLeft: 8,
    flex: 1,
  },
  content: {
    alignItems: 'center',
    marginBottom: 8,
  },
  value: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  unit: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
  },
  range: {
    marginTop: 8,
  },
  rangeText: {
    fontSize: 10,
    color: '#888',
    textAlign: 'center',
  },
  statusIndicator: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 8,
    height: 8,
    borderRadius: 4,
  },
});

export default SensorCard;