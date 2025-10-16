import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Tabs } from 'expo-router';
import { createContext, useContext, useEffect, useState } from 'react';

const PRIMARY_COLOR = '#2E7D32';
const SECONDARY_COLOR = '#4CAF50';

// Create Theme Context
export const ThemeContext = createContext({
  isDarkMode: false,
  toggleTheme: () => {},
});

export const useTheme = () => useContext(ThemeContext);

export default function TabLayout() {
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    loadThemePreference();
  }, []);

  const loadThemePreference = async () => {
    try {
      const savedTheme = await AsyncStorage.getItem('theme');
      if (savedTheme) {
        setIsDarkMode(savedTheme === 'dark');
      }
    } catch (error) {
      console.error('Error loading theme preference:', error);
    }
  };

  const toggleTheme = async () => {
    try {
      const newTheme = !isDarkMode;
      setIsDarkMode(newTheme);
      await AsyncStorage.setItem('theme', newTheme ? 'dark' : 'light');
    } catch (error) {
      console.error('Error saving theme preference:', error);
    }
  };

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme }}>
      <Tabs
        screenOptions={{
          tabBarStyle: {
            backgroundColor: isDarkMode ? '#2C2C2C' : '#fff',
            borderTopColor: isDarkMode ? '#404040' : '#e0e0e0',
          },
          tabBarActiveTintColor: isDarkMode ? '#4A90E2' : '#007AFF',
          tabBarInactiveTintColor: isDarkMode ? '#999' : '#666',
          headerStyle: {
            backgroundColor: isDarkMode ? '#2C2C2C' : '#fff',
          },
          headerTintColor: isDarkMode ? '#fff' : '#000',
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            title: 'Home',
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="home" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="search"
          options={{
            title: 'Search',
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="search" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="profile"
          options={{
            title: 'Profile',
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="person" size={size} color={color} />
            ),
          }}
        />
      </Tabs>
    </ThemeContext.Provider>
  );
} 