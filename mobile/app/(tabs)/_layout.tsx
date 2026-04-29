import { Tabs } from 'expo-router';
import React from 'react';
import { FontAwesome5 } from '@expo/vector-icons';

import { HapticTab } from '@/components/haptic-tab';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

export default function TabLayout() {
  const colorScheme = useColorScheme();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Colors[colorScheme ?? 'light'].tint,
        headerShown: false,
        tabBarButton: HapticTab,
        tabBarStyle: {
          backgroundColor: '#0F172A', // Slate 900
          borderTopColor: 'rgba(255, 255, 255, 0.1)',
        }
      }}>
      <Tabs.Screen
        name="agenda"
        options={{
          title: 'Agenda',
          tabBarIcon: ({ color }) => <FontAwesome5 size={24} name="calendar-alt" color={color} />,
        }}
      />
      <Tabs.Screen
        name="empresas"
        options={{
          title: 'Empresas',
          tabBarIcon: ({ color }) => <FontAwesome5 size={24} name="building" color={color} />,
        }}
      />
      <Tabs.Screen
        name="contatoes"
        options={{
          title: 'Contatoes',
          tabBarIcon: ({ color }) => <FontAwesome5 size={24} name="chalkboard-teacher" color={color} />,
        }}
      />
    </Tabs>
  );
}
