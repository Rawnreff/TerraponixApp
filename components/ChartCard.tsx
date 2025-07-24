import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { VictoryChart, VictoryLine, VictoryArea, VictoryAxis, VictoryTheme, VictoryTooltip, VictoryScatter } from 'victory-native';
import { apiService } from '../services/apiService';

interface ChartCardProps {
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

const ChartCard: React.FC<ChartCardProps> = ({
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
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h'>('6h');
  const [chartType, setChartType] = useState<'line' | 'area'>('area');
  const [stats, setStats] = useState({ avg: 0, min: 0, max: 0 });

  const screenWidth = Dimensions.get('window').width;
  const chartWidth = screenWidth - 40; // Account for margins

  useEffect(() => {
    fetchChartData();
  }, [sensorType, timeRange]);

  const fetchChartData = async () => {
    setLoading(true);
    try {
      const hours = timeRange === '1h' ? 1 : timeRange === '6h' ? 6 : 24;
      const limit = timeRange === '1h' ? 60 : timeRange === '6h' ? 72 : 144;
      
      const response = await apiService.getHistoricalData(hours, limit, sensorType);
      
      const formattedData: ChartDataPoint[] = response.map(item => ({
        x: new Date(item.timestamp),
        y: parseFloat(item.value || item[sensorType] || 0)
      })).filter(item => !isNaN(item.y));

      setChartData(formattedData);

      // Calculate statistics
      if (formattedData.length > 0) {
        const values = formattedData.map(d => d.y);
        setStats({
          avg: values.reduce((a, b) => a + b, 0) / values.length,
          min: Math.min(...values),
          max: Math.max(...values)
        });
      }
    } catch (error) {
      console.error('Error fetching chart data:', error);
      // Generate mock data for development
      const mockData = generateMockData();
      setChartData(mockData);
    } finally {
      setLoading(false);
    }
  };

  const generateMockData = (): ChartDataPoint[] => {
    const points: ChartDataPoint[] = [];
    const hours = timeRange === '1h' ? 1 : timeRange === '6h' ? 6 : 24;
    const intervals = timeRange === '1h' ? 60 : timeRange === '6h' ? 72 : 144;
    
    for (let i = intervals; i >= 0; i--) {
      const time = new Date();
      time.setMinutes(time.getMinutes() - (i * (hours * 60 / intervals)));
      
      let baseValue = currentValue;
      const variation = currentValue * 0.1; // 10% variation
      const value = baseValue + (Math.random() - 0.5) * variation;
      
      points.push({
        x: time,
        y: Math.max(0, value)
      });
    }
    
    return points;
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
    return value.toFixed(sensorType === 'ph' ? 1 : 0);
  };

  const getThresholdLines = () => {
    if (min === undefined || max === undefined) return null;
    
    return (
      <>
        {/* Min threshold line */}
        <VictoryLine
          data={[
            { x: chartData[0]?.x, y: min },
            { x: chartData[chartData.length - 1]?.x, y: min }
          ]}
          style={{
            data: { stroke: '#FFB347', strokeWidth: 1, strokeDasharray: '5,5' }
          }}
        />
        {/* Max threshold line */}
        <VictoryLine
          data={[
            { x: chartData[0]?.x, y: max },
            { x: chartData[chartData.length - 1]?.x, y: max }
          ]}
          style={{
            data: { stroke: '#FFB347', strokeWidth: 1, strokeDasharray: '5,5' }
          }}
        />
      </>
    );
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.titleContainer}>
          <Ionicons name={icon} size={24} color={getStatusColor()} />
          <Text style={styles.title}>{title}</Text>
        </View>
        <View style={styles.valueContainer}>
          <Text style={[styles.currentValue, { color: getStatusColor() }]}>
            {formatValue(currentValue)}
          </Text>
          <Text style={styles.unit}>{unit}</Text>
        </View>
      </View>

      {/* Statistics */}
      <View style={styles.statsContainer}>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>Avg</Text>
          <Text style={styles.statValue}>{formatValue(stats.avg)}</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>Min</Text>
          <Text style={styles.statValue}>{formatValue(stats.min)}</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>Max</Text>
          <Text style={styles.statValue}>{formatValue(stats.max)}</Text>
        </View>
      </View>

      {/* Chart Controls */}
      <View style={styles.controlsContainer}>
        <View style={styles.timeRangeContainer}>
          {(['1h', '6h', '24h'] as const).map((range) => (
            <TouchableOpacity
              key={range}
              style={[
                styles.timeButton,
                timeRange === range && styles.activeTimeButton
              ]}
              onPress={() => setTimeRange(range)}
            >
              <Text style={[
                styles.timeButtonText,
                timeRange === range && styles.activeTimeButtonText
              ]}>
                {range}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        
        <View style={styles.chartTypeContainer}>
          <TouchableOpacity
            style={[
              styles.chartTypeButton,
              chartType === 'area' && styles.activeChartTypeButton
            ]}
            onPress={() => setChartType('area')}
          >
            <Ionicons 
              name="analytics" 
              size={16} 
              color={chartType === 'area' ? '#FFF' : '#666'} 
            />
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.chartTypeButton,
              chartType === 'line' && styles.activeChartTypeButton
            ]}
            onPress={() => setChartType('line')}
          >
            <Ionicons 
              name="trending-up" 
              size={16} 
              color={chartType === 'line' ? '#FFF' : '#666'} 
            />
          </TouchableOpacity>
        </View>
      </View>

      {/* Chart */}
      <View style={styles.chartContainer}>
        {loading ? (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Loading chart...</Text>
          </View>
        ) : chartData.length > 0 ? (
          <VictoryChart
            theme={VictoryTheme.material}
            width={chartWidth}
            height={200}
            padding={{ left: 50, right: 20, top: 20, bottom: 50 }}
            scale={{ x: 'time' }}
          >
            <VictoryAxis 
              dependentAxis
              style={{
                tickLabels: { fontSize: 10, fill: '#666' },
                grid: { stroke: '#E8E8E8', strokeWidth: 0.5 },
                axis: { stroke: '#E8E8E8' }
              }}
              tickFormat={(value) => formatValue(value)}
            />
            <VictoryAxis 
              style={{
                tickLabels: { fontSize: 10, fill: '#666' },
                axis: { stroke: '#E8E8E8' }
              }}
              tickFormat={(date) => {
                const d = new Date(date);
                return timeRange === '1h' 
                  ? d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
                  : d.toLocaleTimeString('en-US', { hour: '2-digit' });
              }}
              fixLabelOverlap={true}
            />
            
            {getThresholdLines()}
            
            {chartType === 'area' ? (
              <VictoryArea
                data={chartData}
                style={{
                  data: { 
                    fill: color, 
                    fillOpacity: 0.3,
                    stroke: color,
                    strokeWidth: 2
                  }
                }}
                animate={{
                  duration: 1000,
                  onLoad: { duration: 500 }
                }}
              />
            ) : (
              <>
                <VictoryLine
                  data={chartData}
                  style={{
                    data: { stroke: color, strokeWidth: 2 }
                  }}
                  animate={{
                    duration: 1000,
                    onLoad: { duration: 500 }
                  }}
                />
                <VictoryScatter
                  data={chartData}
                  size={2}
                  style={{
                    data: { fill: color }
                  }}
                  labelComponent={<VictoryTooltip />}
                />
              </>
            )}
          </VictoryChart>
        ) : (
          <View style={styles.noDataContainer}>
            <Text style={styles.noDataText}>No data available</Text>
          </View>
        )}
      </View>

      {/* Threshold indicator */}
      {min !== undefined && max !== undefined && (
        <View style={styles.thresholdContainer}>
          <Text style={styles.thresholdText}>
            Optimal: {formatValue(min)} - {formatValue(max)} {unit}
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginLeft: 8,
  },
  valueContainer: {
    alignItems: 'flex-end',
  },
  currentValue: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  unit: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    paddingVertical: 8,
    marginBottom: 12,
  },
  statItem: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  statValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  controlsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  timeRangeContainer: {
    flexDirection: 'row',
  },
  timeButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#E8E8E8',
    marginRight: 6,
  },
  activeTimeButton: {
    backgroundColor: '#4ECDC4',
  },
  timeButtonText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
  },
  activeTimeButtonText: {
    color: '#FFF',
  },
  chartTypeContainer: {
    flexDirection: 'row',
  },
  chartTypeButton: {
    padding: 6,
    borderRadius: 6,
    backgroundColor: '#E8E8E8',
    marginLeft: 4,
  },
  activeChartTypeButton: {
    backgroundColor: '#4ECDC4',
  },
  chartContainer: {
    alignItems: 'center',
    minHeight: 200,
  },
  loadingContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    height: 200,
  },
  loadingText: {
    color: '#666',
    fontSize: 14,
  },
  noDataContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    height: 200,
  },
  noDataText: {
    color: '#CCC',
    fontSize: 16,
    fontWeight: '500',
  },
  thresholdContainer: {
    marginTop: 8,
    alignItems: 'center',
  },
  thresholdText: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
});

export default ChartCard;