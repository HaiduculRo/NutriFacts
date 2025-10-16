import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';
import { LinearGradient } from 'expo-linear-gradient';
import * as MediaLibrary from 'expo-media-library';
import { router } from 'expo-router';
import React, { useState } from 'react';
import { ActivityIndicator, Alert, Image, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { useTheme } from './_layout';

const PRIMARY_COLOR = '#2E7D32'; // Verde închis
const SECONDARY_COLOR = '#4CAF50'; // Verde deschis
const BACKGROUND_COLOR = '#F5F5F5';

interface NutritionalData {
  fat_100g: number;
  'saturated-fat_100g': number;
  'trans-fat_100g': number;
  cholesterol_100g: number;
  sodium_100g: number;
  carbohydrates_100g: number;
  fiber_100g: number;
  sugars_100g: number;
  proteins_100g: number;
  nutri_score: string;
}

// Helper functions for calculations
const calculateCalories = (data: any) => {
  return Math.round(
    (data.proteins_100g * 4) + // 4 calories per gram of protein
    (data.carbohydrates_100g * 4) + // 4 calories per gram of carbs
    (data.fat_100g * 9) // 9 calories per gram of fat
  );
};

const calculateWater = (data: any) => {
  const totalWeight = 100; // 100g
  const otherNutrients = data.proteins_100g + data.carbohydrates_100g + data.fat_100g;
  return Math.round((totalWeight - otherNutrients) * 0.7);
};

export default function HomeScreen() {
  const { isDarkMode } = useTheme();
  const [image, setImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [nutritionalData, setNutritionalData] = useState<NutritionalData | null>(null);
  const [productName, setProductName] = useState('');
  const [showProductNameInput, setShowProductNameInput] = useState(false);

  const takePhoto = async () => {
    try {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Please grant camera permissions to take photos.');
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        quality: 1,
        exif: true,
        base64: false,
      });

      if (!result.canceled && result.assets[0].uri) {
        setImage(result.assets[0].uri);
        setShowProductNameInput(true);
      }
    } catch (error) {
      console.error('Error taking photo:', error);
      Alert.alert('Error', 'Failed to take photo. Please try again.');
    }
  };

  const pickImage = async () => {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Please grant media library permissions to select photos.');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        quality: 1,
        exif: true,
        base64: false,
      });

      if (!result.canceled && result.assets[0].uri) {
        setImage(result.assets[0].uri);
        setShowProductNameInput(true);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to pick image. Please try again.');
    }
  };

  const cancelAction = () => {
    setImage(null);
    setNutritionalData(null);
    setProductName('');
    setShowProductNameInput(false);
  };

  const saveImage = async (uri: string) => {
    try {
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Please grant media library permissions to save photos.');
        return;
      }

      const asset = await MediaLibrary.createAssetAsync(uri);
      await MediaLibrary.createAlbumAsync('NutriFacts', asset, false);
      Alert.alert('Success', 'Photo saved to gallery!');
    } catch (error) {
      console.error('Error saving image:', error);
      Alert.alert('Error', 'Failed to save image to gallery.');
    }
  };

  const sendToAPI = async () => {
    if (!image) {
      Alert.alert('No Image', 'Please take a photo first.');
      return;
    }

    if (!productName.trim()) {
      Alert.alert('Product Name Required', 'Please enter a product name before processing.');
      return;
    }

    setLoading(true);
    try {
      // Get the access token from AsyncStorage
      const accessToken = await AsyncStorage.getItem('access');
      console.log('=== TOKEN INFO ===');
      console.log('Access Token:', accessToken);
      
      if (!accessToken) {
        Alert.alert('Error', 'You need to be logged in to save data.');
        return;
      }

      const formData = new FormData();
      formData.append('image', {
        uri: image,
        type: 'image/jpeg',
        name: 'photo.jpg',
        quality: 1,
      } as any);

      // Verificăm dacă token-ul este valid
      if (!accessToken.startsWith('eyJ')) {
        console.error('Invalid token format');
        Alert.alert('Error', 'Invalid authentication token. Please login again.');
        return;
      }

      console.log('=== REQUEST INFO ===');
      console.log('URL:', 'http://172.20.10.2:8000/api/scan-image/');
      console.log('Headers:', {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${accessToken}`,
      });

      // Create a timeout promise
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Request timeout')), 30000); // 30 seconds
      });

      // Race between the fetch and the timeout
      const response = await Promise.race([
        fetch('http://172.20.10.2:8000/api/scan-image/', {
          method: 'POST',
          body: formData,
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${accessToken}`,
          },
        }),
        timeoutPromise
      ]) as Response;

      console.log('=== RESPONSE INFO ===');
      console.log('Status:', response.status);
      console.log('Status Text:', response.statusText);

      const data = await response.json();
      console.log('Response data:', data);

      if (response.ok && data.success) {
        setNutritionalData(data.data);
        
        // Calculate calories and water
        const calories = calculateCalories(data.data);
        const water = calculateWater(data.data);

        // Save the nutritional data to the database
        try {
          const saveResponse = await fetch('http://172.20.10.2:8000/api/save-nutrition-data/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${accessToken}`,
            },
            body: JSON.stringify({
              // Product fields
              product_name: productName,
              brand: 'Unknown Brand',
              category: 'Other',
              nutri_score: data.data.nutri_score || 'E',

              // Nutrition fields
              fat_100g: data.data.fat_100g || 0,
              'saturated-fat_100g': data.data['saturated-fat_100g'] || 0,
              'trans-fat_100g': data.data['trans-fat_100g'] || 0,
              cholesterol_100g: data.data.cholesterol_100g || 0,
              sodium_100g: data.data.sodium_100g || 0,
              carbohydrates_100g: data.data.carbohydrates_100g || 0,
              fiber_100g: data.data.fiber_100g || 0,
              sugars_100g: data.data.sugars_100g || 0,
              proteins_100g: data.data.proteins_100g || 0,
              
              // Additional required fields
              calories: calories,
              protein: data.data.proteins_100g || 0,
              carbs: data.data.carbohydrates_100g || 0,
              fat: data.data.fat_100g || 0,
              water: water,
              notes: 'Scanned with NutriFacts app'
            }),
          });

          if (!saveResponse.ok) {
            const errorData = await saveResponse.json().catch(() => ({}));
            console.error('Error saving data:', errorData);
            Alert.alert('Warning', 'Data was scanned but could not be saved to history.');
          } else {
            Alert.alert(
              'Success',
              'Data was scanned and saved to history successfully!',
              [
                {
                  text: 'View in History',
                  onPress: () => {
                    router.push('/search');
                  },
                },
                {
                  text: 'OK',
                  style: 'cancel'
                },
              ]
            );
          }
        } catch (saveError) {
          console.error('Error saving data:', saveError);
          Alert.alert('Warning', 'Data was scanned but could not be saved to history.');
        }
      } else {
        throw new Error(data.error || 'Failed to process image');
      }
    } catch (error) {
      console.error('Error sending to API:', error);
      Alert.alert('Error', 'Failed to process image. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderNutritionalData = () => {
    if (!nutritionalData) return null;

    const data = [
      { label: 'Fat', value: nutritionalData.fat_100g, unit: 'g' },
      { label: 'Saturated Fat', value: nutritionalData['saturated-fat_100g'], unit: 'g' },
      { label: 'Trans Fat', value: nutritionalData['trans-fat_100g'], unit: 'g' },
      { label: 'Cholesterol', value: nutritionalData.cholesterol_100g, unit: 'g' },
      { label: 'Sodium', value: nutritionalData.sodium_100g, unit: 'g' },
      { label: 'Carbohydrates', value: nutritionalData.carbohydrates_100g, unit: 'g' },
      { label: 'Fiber', value: nutritionalData.fiber_100g, unit: 'g' },
      { label: 'Sugars', value: nutritionalData.sugars_100g, unit: 'g' },
      { label: 'Proteins', value: nutritionalData.proteins_100g, unit: 'g' },
      { label: 'Nutri-Score', value: nutritionalData.nutri_score, unit: '' },
    ];

    return (
      <View style={[styles.nutritionalDataContainer, isDarkMode && styles.darkNutritionalDataContainer]}>
        <Text style={[styles.nutritionalDataTitle, isDarkMode && styles.darkNutritionalDataTitle]}>Nutritional Information (per 100g)</Text>
        {data.map((item, index) => (
          <View key={index} style={[styles.nutritionalDataRow, isDarkMode && styles.darkNutritionalDataRow]}>
            <Text style={[styles.nutritionalDataLabel, isDarkMode && styles.darkNutritionalDataLabel]}>{item.label}:</Text>
            <Text style={[styles.nutritionalDataValue, isDarkMode && styles.darkNutritionalDataValue]}>
              {item.label === 'Nutri-Score' ? item.value : `${item.value}${item.unit}`}
            </Text>
          </View>
        ))}
      </View>
    );
  };

  return (
    <ScrollView style={[styles.container, isDarkMode && styles.darkContainer]}>
      <LinearGradient
        colors={['#2E7D32', '#4CAF50']}
        style={[styles.header, isDarkMode && styles.darkHeader]}
      >
        <Text style={[styles.title, isDarkMode && styles.darkTitle]}>NutriFacts Scanner</Text>
        <Text style={[styles.subtitle, isDarkMode && styles.darkSubtitle]}>Discover what is in your food</Text>
      </LinearGradient>
      
      {image ? (
        <View style={[styles.imageSection, isDarkMode && styles.darkImageSection]}>
          <View style={[styles.imageContainer, isDarkMode && styles.darkImageContainer]}>
            <Image source={{ uri: image }} style={[styles.image, isDarkMode && styles.darkImage]} />
          </View>
          
          {showProductNameInput && (
            <View style={[styles.inputContainer, isDarkMode && styles.darkInputContainer]}>
              <Ionicons name="pricetag-outline" size={20} color="#666" style={[styles.inputIcon, isDarkMode && styles.darkInputIcon]} />
              <TextInput
                style={[styles.input, isDarkMode && styles.darkInput]}
                placeholder="Enter product name"
                value={productName}
                onChangeText={setProductName}
                autoCapitalize="words"
              />
            </View>
          )}
          
          <View style={[styles.buttonContainer, isDarkMode && styles.darkButtonContainer]}>
            <TouchableOpacity 
              style={[styles.sendButton, loading && styles.disabledButton, isDarkMode && styles.darkSendButton]} 
              onPress={sendToAPI}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <Ionicons name="cloud-upload" size={24} color="#fff" />
                  <Text style={[styles.buttonText, isDarkMode && styles.darkButtonText]}>Process Image</Text>
                </>
              )}
            </TouchableOpacity>
            
            <TouchableOpacity style={[styles.cancelButton, isDarkMode && styles.darkCancelButton]} onPress={cancelAction}>
              <Ionicons name="close-circle" size={24} color="#fff" />
              <Text style={[styles.buttonText, isDarkMode && styles.darkButtonText]}>Cancel</Text>
            </TouchableOpacity>
          </View>

          {renderNutritionalData()}
        </View>
      ) : (
        <View style={[styles.cameraSection, isDarkMode && styles.darkCameraSection]}>
          <View style={[styles.cameraButtonsContainer, isDarkMode && styles.darkCameraButtonsContainer]}>
            <TouchableOpacity style={[styles.cameraButton, isDarkMode && styles.darkCameraButton]} onPress={takePhoto}>
              <LinearGradient
                colors={['#2E7D32', '#4CAF50']}
                style={[styles.cameraIconContainer, isDarkMode && styles.darkCameraIconContainer]}
              >
                <Ionicons name="camera" size={40} color="#fff" />
              </LinearGradient>
              <Text style={[styles.buttonText, isDarkMode && styles.darkButtonText]}>Take Photo</Text>
            </TouchableOpacity>

            <TouchableOpacity style={[styles.cameraButton, isDarkMode && styles.darkCameraButton]} onPress={pickImage}>
              <LinearGradient
                colors={['#4CAF50', '#2E7D32']}
                style={[styles.cameraIconContainer, isDarkMode && styles.darkCameraIconContainer]}
              >
                <Ionicons name="images" size={40} color="#fff" />
              </LinearGradient>
              <Text style={[styles.buttonText, isDarkMode && styles.darkButtonText]}>Choose from Gallery</Text>
            </TouchableOpacity>
          </View>

          <View style={[styles.infoContainer, isDarkMode && styles.darkInfoContainer]}>
            <Ionicons name="information-circle" size={24} color={PRIMARY_COLOR} />
            <Text style={[styles.infoText, isDarkMode && styles.darkInfoText]}>
              Scan food labels to get detailed nutritional information and Nutri-Score
            </Text>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: BACKGROUND_COLOR,
  },
  darkContainer: {
    backgroundColor: '#2C2C2C',
  },
  header: {
    paddingTop: 60,
    paddingBottom: 30,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  darkHeader: {
    backgroundColor: '#2C2C2C',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  darkTitle: {
    color: '#fff',
  },
  subtitle: {
    fontSize: 18,
    color: '#fff',
    opacity: 0.9,
  },
  darkSubtitle: {
    color: '#fff',
    opacity: 0.9,
  },
  imageSection: {
    flex: 1,
    padding: 20,
  },
  darkImageSection: {
    backgroundColor: '#2C2C2C',
  },
  imageContainer: {
    width: '100%',
    height: 'auto',
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: '#fff',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  darkImageContainer: {
    backgroundColor: '#2C2C2C',
  },
  image: {
    width: '100%',
    height: undefined,
    aspectRatio: 1,
    resizeMode: 'contain',
  },
  darkImage: {
    backgroundColor: '#2C2C2C',
  },
  buttonContainer: {
    gap: 12,
    marginTop: 20,
    marginBottom: 20,
  },
  darkButtonContainer: {
    backgroundColor: '#2C2C2C',
  },
  cameraSection: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
  },
  darkCameraSection: {
    backgroundColor: '#2C2C2C',
  },
  cameraButtonsContainer: {
    gap: 20,
    marginBottom: 30,
  },
  darkCameraButtonsContainer: {
    backgroundColor: '#2C2C2C',
  },
  cameraButton: {
    backgroundColor: '#fff',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    borderRadius: 15,
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  darkCameraButton: {
    backgroundColor: '#2C2C2C',
  },
  cameraIconContainer: {
    width: 70,
    height: 70,
    borderRadius: 35,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 15,
  },
  darkCameraIconContainer: {
    backgroundColor: '#2C2C2C',
  },
  sendButton: {
    backgroundColor: PRIMARY_COLOR,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 15,
    borderRadius: 12,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  darkSendButton: {
    backgroundColor: '#2C2C2C',
  },
  disabledButton: {
    opacity: 0.7,
  },
  cancelButton: {
    backgroundColor: '#D32F2F',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 15,
    borderRadius: 12,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  darkCancelButton: {
    backgroundColor: '#2C2C2C',
  },
  buttonText: {
    color: '#333',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  darkButtonText: {
    color: '#fff',
  },
  nutritionalDataContainer: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 15,
    marginTop: 20,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  darkNutritionalDataContainer: {
    backgroundColor: '#2C2C2C',
  },
  nutritionalDataTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: PRIMARY_COLOR,
    marginBottom: 15,
    textAlign: 'center',
  },
  darkNutritionalDataTitle: {
    color: '#fff',
  },
  nutritionalDataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  darkNutritionalDataRow: {
    borderBottomColor: '#2C2C2C',
  },
  nutritionalDataLabel: {
    fontSize: 16,
    color: '#333',
  },
  darkNutritionalDataLabel: {
    color: '#fff',
  },
  nutritionalDataValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: PRIMARY_COLOR,
  },
  darkNutritionalDataValue: {
    color: '#fff',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    marginVertical: 15,
    paddingHorizontal: 15,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  darkInputContainer: {
    backgroundColor: '#2C2C2C',
  },
  inputIcon: {
    marginRight: 10,
  },
  darkInputIcon: {
    color: '#fff',
  },
  input: {
    flex: 1,
    height: 50,
    fontSize: 16,
  },
  darkInput: {
    color: '#fff',
  },
  infoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 12,
    marginTop: 20,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  darkInfoContainer: {
    backgroundColor: '#2C2C2C',
  },
  infoText: {
    flex: 1,
    marginLeft: 10,
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  darkInfoText: {
    color: '#fff',
  },
}); 