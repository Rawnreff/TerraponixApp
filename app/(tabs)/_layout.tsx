// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import React from 'react';
import { Platform } from 'react-native';

import { HapticTab } from '@/components/HapticTab';
import { IconSymbol } from '@/components/ui/IconSymbol';
import TabBarBackground from '@/components/ui/TabBarBackground';
import { Colors } from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';
// import { MaterialCommunityIcons } from '@expo/vector-icons'; // Jika Anda ingin menggunakan ini untuk ikon selain IconSymbol

export default function TabLayout() {
  const colorScheme = useColorScheme();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Colors[colorScheme ?? 'light'].tint,
        headerShown: false, // Disarankan false jika Anda mengelola header di setiap layar
        tabBarButton: HapticTab,
        tabBarBackground: TabBarBackground,
        tabBarStyle: Platform.select({
          ios: {
            position: 'absolute',
          },
          default: {},
        }),
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="house.fill" color={color} />,
        }}
      />
      {/* Tambahkan Tab untuk Dashboard Anda di sini */}
      <Tabs.Screen
        name="dashboard" // Nama file: app/(tabs)/dashboard.tsx
        options={{
          title: 'Dashboard',
          // Jika Anda menggunakan IconSymbol dan punya ikon yang cocok:
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="chart.bar.fill" color={color} />,
          // Alternatif jika menggunakan MaterialCommunityIcons:
          // tabBarIcon: ({ color, focused }) => <MaterialCommunityIcons name={focused ? 'chart-bar' : 'chart-bar-outline'} size={28} color={color} />,
        }}
      />
      {/* Tambahkan Tab untuk Control Anda di sini */}
      <Tabs.Screen
        name="control" // Nama file: app/(tabs)/control.tsx
        options={{
          title: 'Controls',
          // Jika Anda menggunakan IconSymbol dan punya ikon yang cocok:
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="slider.horizontal.3" color={color} />,
          // Alternatif jika menggunakan MaterialCommunityIcons:
          // tabBarIcon: ({ color, focused }) => <MaterialCommunityIcons name={focused ? 'tune' : 'tune-vertical'} size={28} color={color} />,
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: 'Alerts',
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="bell.fill" color={color} />,
        }}
      />
    </Tabs>
  );
}