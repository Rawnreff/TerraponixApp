import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Switch } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface ControlCardProps {
  title: string;
  icon: keyof typeof Ionicons.glyphMap;
  isActive: boolean;
  isAuto: boolean;
  onToggle: () => void;
  onAutoToggle: () => void;
  disabled?: boolean;
}

const ControlCard: React.FC<ControlCardProps> = ({
  title,
  icon,
  isActive,
  isAuto,
  onToggle,
  onAutoToggle,
  disabled = false
}) => {
  const getStatusColor = () => {
    if (disabled) return '#CCC';
    return isActive ? '#4ECDC4' : '#E8E8E8';
  };

  const getIconColor = () => {
    if (disabled) return '#999';
    return isActive ? '#FFF' : '#666';
  };

  const getTextColor = () => {
    if (disabled) return '#999';
    return '#333';
  };

  return (
    <View style={[styles.container, disabled && styles.disabled]}>
      <View style={styles.header}>
        <View style={[styles.iconContainer, { backgroundColor: getStatusColor() }]}>
          <Ionicons 
            name={icon} 
            size={24} 
            color={getIconColor()} 
          />
        </View>
        <Text style={[styles.title, { color: getTextColor() }]}>{title}</Text>
      </View>
      
      <View style={styles.controls}>
        <View style={styles.autoControl}>
          <Text style={[styles.label, { color: getTextColor() }]}>Auto</Text>
          <Switch
            value={isAuto}
            onValueChange={onAutoToggle}
            disabled={disabled}
            trackColor={{ false: '#E8E8E8', true: '#4ECDC4' }}
            thumbColor={isAuto ? '#FFF' : '#FFF'}
          />
        </View>
        
        <TouchableOpacity
          style={[
            styles.manualButton,
            {
              backgroundColor: isActive ? '#4ECDC4' : '#E8E8E8',
              opacity: (isAuto || disabled) ? 0.5 : 1
            }
          ]}
          onPress={onToggle}
          disabled={isAuto || disabled}
        >
          <Text style={[
            styles.buttonText,
            { color: isActive ? '#FFF' : '#666' }
          ]}>
            {isActive ? 'ON' : 'OFF'}
          </Text>
        </TouchableOpacity>
      </View>
      
      <View style={styles.status}>
        <View style={[
          styles.statusIndicator,
          { backgroundColor: isActive ? '#4ECDC4' : '#E8E8E8' }
        ]} />
        <Text style={[styles.statusText, { color: getTextColor() }]}>
          {isActive ? 'Active' : 'Inactive'}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    minWidth: 160,
    margin: 8,
    padding: 16,
    backgroundColor: '#FFF',
    borderRadius: 12,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
  },
  disabled: {
    opacity: 0.6,
  },
  header: {
    alignItems: 'center',
    marginBottom: 16,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
  controls: {
    marginBottom: 16,
  },
  autoControl: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
  },
  manualButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  status: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  statusIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '500',
  },
});

export default ControlCard;