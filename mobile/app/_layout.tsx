import { Tabs } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

export default function RootLayout() {
  return (
    <>
      <StatusBar style="light" />
      <Tabs
        screenOptions={{
          tabBarStyle: { backgroundColor: '#111827', borderTopColor: '#1f2937' },
          tabBarActiveTintColor: '#22c55e',
          tabBarInactiveTintColor: '#6b7280',
          headerStyle: { backgroundColor: '#111827' },
          headerTintColor: '#f9fafb',
        }}
      >
        <Tabs.Screen name="(tabs)/index" options={{ title: 'Chat', tabBarLabel: 'Chat', tabBarIcon: ({ color }) => <TabIcon label="💬" color={color} /> }} />
        <Tabs.Screen name="(tabs)/memory" options={{ title: 'Memory', tabBarLabel: 'Memory', tabBarIcon: ({ color }) => <TabIcon label="🧠" color={color} /> }} />
        <Tabs.Screen name="(tabs)/skills" options={{ title: 'Skills', tabBarLabel: 'Skills', tabBarIcon: ({ color }) => <TabIcon label="⚡" color={color} /> }} />
        <Tabs.Screen name="(tabs)/settings" options={{ title: 'Settings', tabBarLabel: 'Settings', tabBarIcon: ({ color }) => <TabIcon label="⚙️" color={color} /> }} />
      </Tabs>
    </>
  );
}

function TabIcon({ label }: { label: string; color: string }) {
  const { Text } = require('react-native');
  return <Text style={{ fontSize: 18 }}>{label}</Text>;
}
