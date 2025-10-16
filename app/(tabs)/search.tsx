import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useFocusEffect } from 'expo-router';
import React, { useCallback, useState } from 'react';
import { ActivityIndicator, FlatList, Modal, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { useTheme } from './_layout';

interface NutritionHistory {
  id: string;
  product_name: string;
  scan_date: string;
  nutri_score: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  fat_100g: number;
  saturated_fat_100g: number;
  trans_fat_100g: number;
  cholesterol_100g: number;
  sodium_100g: number;
  carbohydrates_100g: number;
  fiber_100g: number;
  sugars_100g: number;
  proteins_100g: number;
}

export default function SearchScreen() {
  const { isDarkMode } = useTheme();
  const [searchQuery, setSearchQuery] = useState('');
  const [history, setHistory] = useState<NutritionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<NutritionHistory | null>(null);
  const [modalVisible, setModalVisible] = useState(false);

  const fetchHistory = async () => {
    try {
      const accessToken = await AsyncStorage.getItem('access');
      if (!accessToken) {
        setError('You need to be logged in to view history');
        setLoading(false);
        return;
      }

      console.log('Fetching nutrition history...');
      const response = await fetch('http://172.20.10.2:8000/api/nutrition-history/', {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Error response:', errorData);
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Received history data:', data);
      setHistory(data);
    } catch (err) {
      console.error('Error fetching history:', err);
      setError(err instanceof Error ? err.message : 'Failed to load history. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      console.log('Search screen focused - refreshing data...');
      fetchHistory();
    }, [])
  );

  const filteredHistory = history.filter(item =>
    item.product_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const renderHistoryItem = ({ item }: { item: NutritionHistory }) => (
    <TouchableOpacity 
      style={styles.historyItem}
      onPress={() => {
        setSelectedItem(item);
        setModalVisible(true);
      }}
    >
      <View style={styles.historyItemHeader}>
        <Text style={styles.productName}>{item.product_name}</Text>
        <View style={[styles.nutriScoreBadge, { backgroundColor: getNutriScoreColor(item.nutri_score) }]}>
          <Text style={styles.nutriScoreText}>{item.nutri_score}</Text>
        </View>
      </View>
      
      <View style={styles.nutritionInfo}>
        {/* <View style={styles.nutritionItem}>
          <Text style={styles.nutritionLabel}>Calories</Text>
          <Text style={styles.nutritionValue}>{item.calories} kcal</Text>
        </View> */}
        <View style={styles.nutritionItem}>
          <Text style={styles.nutritionLabel}>Protein</Text>
          <Text style={styles.nutritionValue}>{item.proteins_100g}g</Text>
        </View>
        <View style={styles.nutritionItem}>
          <Text style={styles.nutritionLabel}>Carbs</Text>
          <Text style={styles.nutritionValue}>{item.carbohydrates_100g}g</Text>
        </View>
        <View style={styles.nutritionItem}>
          <Text style={styles.nutritionLabel}>Fat</Text>
          <Text style={styles.nutritionValue}>{item.fat_100g}g</Text>
        </View>
      </View>
      
      <Text style={styles.scanDate}>Scanned on: {formatDate(item.scan_date)}</Text>
    </TouchableOpacity>
  );

  const renderDetailedInfo = () => {
    if (!selectedItem) return null;

    const nutritionData = [
      { label: 'Total Fat', value: `${selectedItem.fat_100g}g` },
      { label: 'Saturated Fat', value: `${selectedItem.saturated_fat_100g}g` },
      { label: 'Trans Fat', value: `${selectedItem.trans_fat_100g}g` },
      { label: 'Cholesterol', value: `${selectedItem.cholesterol_100g}g` },
      { label: 'Sodium', value: `${selectedItem.sodium_100g}g` },
      { label: 'Total Carbohydrates', value: `${selectedItem.carbohydrates_100g}g` },
      { label: 'Dietary Fiber', value: `${selectedItem.fiber_100g}g` },
      { label: 'Sugars', value: `${selectedItem.sugars_100g}g` },
      { label: 'Protein', value: `${selectedItem.proteins_100g}g` },
      { label: 'Calories', value: `${selectedItem.calories} kcal` },
    ];

    return (
      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{selectedItem.product_name}</Text>
              <TouchableOpacity 
                style={styles.closeButton}
                onPress={() => setModalVisible(false)}
              >
                <Ionicons name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              <View style={styles.nutriScoreContainer}>
                <Text style={styles.nutriScoreLabel}>Nutri-Score</Text>
                <View style={[styles.nutriScoreBadgeLarge, { backgroundColor: getNutriScoreColor(selectedItem.nutri_score) }]}>
                  <Text style={styles.nutriScoreTextLarge}>{selectedItem.nutri_score}</Text>
                </View>
              </View>

              <Text style={styles.sectionTitle}>Nutritional Information (per 100g)</Text>
              {nutritionData.map((item, index) => (
                <View key={index} style={styles.nutritionRow}>
                  <Text style={styles.nutritionLabel}>{item.label}</Text>
                  <Text style={styles.nutritionValue}>{item.value}</Text>
                </View>
              ))}

              <Text style={styles.scanDate}>Scanned on: {formatDate(selectedItem.scan_date)}</Text>
            </ScrollView>
          </View>
        </View>
      </Modal>
    );
  };

  const getNutriScoreColor = (score: string) => {
    const colors: { [key: string]: string } = {
      'A': '#2E7D32', // Green
      'B': '#4CAF50', // Light Green
      'C': '#FFC107', // Yellow
      'D': '#FF9800', // Orange
      'E': '#F44336', // Red
    };
    return colors[score] || '#666';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2E7D32" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, isDarkMode && styles.darkContainer]}>
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color="#666" style={styles.searchIcon} />
        <TextInput
          style={[styles.searchInput, isDarkMode && styles.darkSearchInput]}
          placeholder="Search in your history..."
          placeholderTextColor={isDarkMode ? "#999" : "#666"}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      <FlatList
        data={filteredHistory}
        renderItem={renderHistoryItem}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.listContainer}
        showsVerticalScrollIndicator={false}
      />

      {renderDetailedInfo()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 20,
  },
  darkContainer: {
    backgroundColor: '#2C2C2C',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 20,
  },
  errorText: {
    color: '#D32F2F',
    fontSize: 16,
    textAlign: 'center',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 10,
    paddingHorizontal: 15,
    height: 50,
    marginBottom: 20,
    marginTop: 40,
  },
  searchIcon: {
    marginRight: 10,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#333',
    backgroundColor: '#f5f5f5',
  },
  darkSearchInput: {
    flex: 1,
    fontSize: 16,
    color: '#333',
    backgroundColor: '#f5f5f5',
  },
  listContainer: {
    paddingBottom: 20,
  },
  historyItem: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    marginBottom: 15,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  historyItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  productName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  nutriScoreBadge: {
    width: 30,
    height: 30,
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 10,
  },
  nutriScoreText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  nutritionInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  nutritionItem: {
    alignItems: 'center',
  },
  nutritionLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  nutritionValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  scanDate: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 20,
    width: '90%',
    maxHeight: '80%',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  closeButton: {
    padding: 5,
  },
  modalBody: {
    padding: 20,
  },
  nutriScoreContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  nutriScoreLabel: {
    fontSize: 16,
    color: '#666',
    marginBottom: 10,
  },
  nutriScoreBadgeLarge: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
  },
  nutriScoreTextLarge: {
    color: '#fff',
    fontSize: 32,
    fontWeight: 'bold',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  nutritionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  text: {
    color: '#000',
  },
  darkText: {
    color: '#fff',
  },
}); 