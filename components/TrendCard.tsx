import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { VictoryChart, VictoryLine, VictoryArea, VictoryAxis, VictoryTheme, VictoryScatter } from 'victory-native';
import { apiService } from '../services/apiService';

interface TrendCardProps {
  title: string;
  sensorType: string;
  unit: string;
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
  currentValue: number;
  min?: number;
  max?: number;
}

interface ChartDataPoint {
  x: Date;
  y: number;
}

const TrendCard: React.FC<TrendCardProps> = ({
  title,
  sensorType,
  unit,
  icon,
  color,
  currentValue,
  min,
  max
}) => {
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [trend, setTrend] = useState<'up' | 'down' | 'stable'>('stable');
  const [changePercent, setChangePercent] = useState(0);
  const [changeValue, setChangeValue] = useState(0);
  const [stats, setStats] = useState({ avg: 0, min: 0, max: 0 });

  const screenWidth = Dimensions.get('window').width;
  const cardWidth = screenWidth - 32; // Account for margins
  const chartHeight = 120;

  useEffect(() => {
    fetchTrendData();
  }, [sensorType]);

  const fetchTrendData = async () => {
    setLoading(true);
    try {
      // Get last 6 hours of data for trend analysis
      const response = await apiService.getHistoricalData(6, 50, sensorType);
      
      const formattedData: ChartDataPoint[] = response.map(item => ({
        x: new Date(item.timestamp),
        y: parseFloat(item.value || item[sensorType] || 0)
      })).filter(item => !isNaN(item.y));

      setChartData(formattedData);
      calculateTrend(formattedData);
      calculateStats(formattedData);
    } catch (error) {
      console.error('Error fetching trend data:', error);
      // Generate mock data for development
      const mockData = generateMockTrendData();
      setChartData(mockData);
      calculateTrend(mockData);
      calculateStats(mockData);
    } finally {
      setLoading(false);
    }
  };

  const generateMockTrendData = (): ChartDataPoint[] => {
    const points: ChartDataPoint[] = [];
    let baseValue = currentValue;
    
    for (let i = 50; i >= 0; i--) {
      const time = new Date();
      time.setMinutes(time.getMinutes() - (i * 7)); // 7 minute intervals
      
      // Simulate trend - slight upward/downward movement
      const trendDirection = Math.random() > 0.5 ? 1 : -1;
      const variation = baseValue * 0.05; // 5% variation
      baseValue += (Math.random() - 0.5) * variation * trendDirection;
      
      points.push({
        x: time,
        y: Math.max(0, baseValue)
      });
    }
    
    return points;
  };

  const calculateTrend = (data: ChartDataPoint[]) => {
    if (data.length < 2) return;

    const recent = data.slice(-10); // Last 10 points
    const older = data.slice(0, 10); // First 10 points
    
    const recentAvg = recent.reduce((sum, point) => sum + point.y, 0) / recent.length;
    const olderAvg = older.reduce((sum, point) => sum + point.y, 0) / older.length;
    
    const change = recentAvg - olderAvg;
    const percentChange = ((recentAvg - olderAvg) / olderAvg) * 100;
    
    setChangeValue(change);
    setChangePercent(percentChange);
    
    if (Math.abs(percentChange) < 1) {
      setTrend('stable');
    } else if (percentChange > 0) {
      setTrend('up');
    } else {
      setTrend('down');
    }
  };

  const calculateStats = (data: ChartDataPoint[]) => {
    if (data.length === 0) return;
    
    const values = data.map(d => d.y);
    setStats({
      avg: values.reduce((a, b) => a + b, 0) / values.length,
      min: Math.min(...values),
      max: Math.max(...values)
    });
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return 'trending-up';
      case 'down': return 'trending-down';
      case 'stable': return 'remove';
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up': return '#4ECDC4';
      case 'down': return '#FF6B6B';
      case 'stable': return '#95A5A6';
    }
  };

  const getStatusColor = () => {
    if (min !== undefined && max !== undefined) {
      if (currentValue < min || currentValue > max) {
        return currentValue < min * 0.8 || currentValue > max * 1.2 ? '#FF6B6B' : '#FFB347';
      }
    }
    return color;
  };

  const formatValue = (value: number) => {
    if (sensorType === 'ph') return value.toFixed(1);
    if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
    return value.toFixed(0);
  };

  const formatChange = (value: number) => {
    const prefix = value > 0 ? '+' : '';
    if (sensorType === 'ph') return `${prefix}${value.toFixed(1)}`;
    return `${prefix}${value.toFixed(0)}`;
  };

  return (
    <View style={styles.container}>
      {/* Header with current value and trend */}
      <View style={styles.header}>
        <View style={styles.sensorInfo}>
          <View style={styles.iconContainer}>
            <Ionicons name={icon} size={24} color={getStatusColor()} />
          </View>
          <View style={styles.titleContainer}>
            <Text style={styles.title}>{title}</Text>
            <View style={styles.valueRow}>
              <Text style={[styles.currentValue, { color: getStatusColor() }]}>
                {formatValue(currentValue)}
              </Text>
              <Text style={styles.unit}>{unit}</Text>
            </View>
          </View>
        </View>
        
        <View style={styles.trendContainer}>
          <View style={[styles.trendIndicator, { backgroundColor: getTrendColor() }]}>
            <Ionicons name={getTrendIcon()} size={16} color="#FFF" />
            <Text style={styles.trendPercent}>
              {Math.abs(changePercent).toFixed(1)}%
            </Text>
          </View>
          <Text style={[styles.changeValue, { color: getTrendColor() }]}>
            {formatChange(changeValue)} {unit}
          </Text>
        </View>
      </View>

      {/* Mini Chart */}
      <View style={styles.chartContainer}>
        {loading ? (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Loading...</Text>
          </View>
        ) : chartData.length > 0 ? (
          <VictoryChart
            theme={VictoryTheme.material}
            width={cardWidth}
            height={chartHeight}
            padding={{ left: 0, right: 0, top: 10, bottom: 10 }}
            scale={{ x: 'time' }}
          >
            {/* Hide axes for cleaner look */}
            <VictoryAxis dependentAxis style={{ axis: { stroke: 'none' }, tickLabels: { fill: 'none' } }} />
            <VictoryAxis style={{ axis: { stroke: 'none' }, tickLabels: { fill: 'none' } }} />
            
            {/* Threshold area if defined */}
            {min !== undefined && max !== undefined && (
              <VictoryArea
                data={[
                  { x: chartData[0]?.x, y: min },
                  { x: chartData[chartData.length - 1]?.x, y: min },
                  { x: chartData[chartData.length - 1]?.x, y: max },
                  { x: chartData[0]?.x, y: max }
                ]}
                style={{
                  data: { fill: '#E8F5E8', fillOpacity: 0.3 }
                }}
              />
            )}
            
            {/* Main trend line */}
            <VictoryArea
              data={chartData}
              style={{
                data: { 
                  fill: color, 
                  fillOpacity: 0.2,
                  stroke: color,
                  strokeWidth: 2
                }
              }}
              animate={{
                duration: 1000,
                onLoad: { duration: 500 }
              }}
            />
            
            {/* Current value point */}
            <VictoryScatter
              data={[chartData[chartData.length - 1]]}
              size={4}
              style={{
                data: { fill: color, stroke: '#FFF', strokeWidth: 2 }
              }}
            />
          </VictoryChart>
        ) : (
          <View style={styles.noDataContainer}>
            <Text style={styles.noDataText}>No data</Text>
          </View>
        )}
      </View>

      {/* Stats footer */}
      <View style={styles.footer}>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>6h Low</Text>
          <Text style={styles.statValue}>{formatValue(stats.min)}</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>6h Avg</Text>
          <Text style={styles.statValue}>{formatValue(stats.avg)}</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>6h High</Text>
          <Text style={styles.statValue}>{formatValue(stats.max)}</Text>
        </View>
      </View>

      {/* Status indicator bar */}
      <View style={styles.statusBar}>
        <View 
          style={[
            styles.statusIndicator, 
            { 
              backgroundColor: getStatusColor(),
              width: min && max ? `${Math.min(Math.max(((currentValue - min) / (max - min)) * 100, 0), 100)}%` : '50%'
            }
          ]} 
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 4,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  sensorInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#F8F9FA',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  titleContainer: {
    flex: 1,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  valueRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  currentValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginRight: 4,
  },
  unit: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  trendContainer: {
    alignItems: 'flex-end',
  },
  trendIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 4,
  },
  trendPercent: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  changeValue: {
    fontSize: 12,
    fontWeight: '600',
  },
  chartContainer: {
    height: 120,
    marginBottom: 12,
    overflow: 'hidden',
  },
  loadingContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    height: 120,
  },
  loadingText: {
    color: '#666',
    fontSize: 12,
  },
  noDataContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    height: 120,
  },
  noDataText: {
    color: '#CCC',
    fontSize: 14,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 8,
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    marginBottom: 12,
  },
  statItem: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 10,
    color: '#666',
    marginBottom: 2,
  },
  statValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
  },
  statusBar: {
    height: 4,
    backgroundColor: '#E8E8E8',
    borderRadius: 2,
    overflow: 'hidden',
  },
  statusIndicator: {
    height: '100%',
    borderRadius: 2,
  },
});

export default TrendCard;