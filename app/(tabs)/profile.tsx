import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as FileSystem from 'expo-file-system';
import * as ImagePicker from 'expo-image-picker';
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Image, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { useTheme } from './_layout';

// TODO: Replace with your actual API URL
const API_URL = 'http://172.20.10.2:8000'; // For local network
//const API_URL = 'http://10.0.2.2:8000'; // For Android emulator
//const API_URL = 'http://localhost:8000'; // For iOS simulator

export default function ProfileScreen() {
  const { isDarkMode, toggleTheme } = useTheme();
  const [userData, setUserData] = useState({
    email: '',
    username: '',
    first_name: '',
    last_name: '',
    profile_picture: null
  });
  const [profileImage, setProfileImage] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedFirstName, setEditedFirstName] = useState('');
  const [editedLastName, setEditedLastName] = useState('');

  useEffect(() => {
    console.log('ProfileScreen mounted');
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    try {
      console.log('Fetching user data...');
      const token = await AsyncStorage.getItem('access');
      console.log('Token from AsyncStorage:', token);
      
      if (!token) {
        console.log('No token found, redirecting to login');
        router.replace('/(auth)/login');
        return;
      }

      console.log('Making API request to:', `${API_URL}/core/user/profile/`);
      const response = await fetch(`${API_URL}/core/user/profile/`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token.trim()}`
        }
      });

      console.log('API Response status:', response.status);
      console.log('Response headers:', response.headers);
      
      if (response.ok) {
        const data = await response.json();
        console.log('User data received:', data);
        setUserData({
          email: data.email,
          username: data.username || data.email.split('@')[0],
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          profile_picture: data.profile_picture
        });
        setEditedFirstName(data.first_name || '');
        setEditedLastName(data.last_name || '');
        if (data.profile_picture) {
          const fullImageUrl = `${API_URL}${data.profile_picture}`;
          console.log('Full image URL:', fullImageUrl);
          setProfileImage(fullImageUrl);
        }
      } else {
        const errorData = await response.json();
        console.error('Failed to fetch user data:', errorData);
      }
    } catch (error) {
      console.error('Error in fetchUserData:', error);
    }
  };

  const updateProfile = async () => {
    try {
      const token = await AsyncStorage.getItem('access');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch(`${API_URL}/core/user/profile/`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token.trim()}`
        },
        body: JSON.stringify({
          first_name: editedFirstName,
          last_name: editedLastName
        })
      });

      if (response.ok) {
        const data = await response.json();
        setUserData(prev => ({
          ...prev,
          first_name: data.first_name,
          last_name: data.last_name
        }));
        setIsEditing(false);
        Alert.alert('Success', 'Profile updated successfully');
      } else {
        throw new Error('Failed to update profile');
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      Alert.alert('Error', 'Failed to update profile. Please try again.');
    }
  };

  const uploadProfilePicture = async (uri: string) => {
    try {
      setIsUploading(true);
      const token = await AsyncStorage.getItem('access');
      
      if (!token) {
        throw new Error('No authentication token found');
      }

      // Read the file as base64
      const base64 = await FileSystem.readAsStringAsync(uri, {
        encoding: FileSystem.EncodingType.Base64,
      });

      // Create the form data
      const formData = new FormData();
      formData.append('profile_picture', `data:image/jpeg;base64,${base64}`);

      const response = await fetch(`${API_URL}/core/user/profile/`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Authorization': `Bearer ${token.trim()}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        // Construim URL-ul complet al pozei
        const fullImageUrl = `${API_URL}${data.profile_picture}`;
        console.log('Full image URL after upload:', fullImageUrl);
        setProfileImage(fullImageUrl);
        Alert.alert('Success', 'Profile picture updated successfully');
      } else {
        throw new Error('Failed to upload profile picture');
      }
    } catch (error) {
      console.error('Error uploading profile picture:', error);
      Alert.alert('Error', 'Failed to upload profile picture. Please try again.');
    } finally {
      setIsUploading(false);
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
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.5,
      });

      if (!result.canceled && result.assets[0].uri) {
        await uploadProfilePicture(result.assets[0].uri);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to pick image. Please try again.');
    }
  };

  const handleLogout = async () => {
    try {
      console.log('Logging out...');
      await AsyncStorage.multiRemove(['access', 'refresh']);
      console.log('Tokens removed from AsyncStorage');
      router.replace('/(auth)/login');
    } catch (error) {
      console.error('Error during logout:', error);
    }
  };

  return (
    <View style={[styles.container, isDarkMode && styles.darkContainer]}>
      <View style={[styles.header, isDarkMode && styles.darkHeader]}>
        <TouchableOpacity onPress={pickImage} style={styles.avatarContainer} disabled={isUploading}>
          {profileImage ? (
            <Image 
              source={{ uri: profileImage }} 
              style={styles.avatar}
              onError={(e) => {
                console.error('Error loading image:', e.nativeEvent.error);
                setProfileImage(null);
              }}
            />
          ) : (
          <Ionicons name="person" size={40} color="#fff" />
          )}
          <View style={styles.editIconContainer}>
            <Ionicons name="camera" size={20} color="#fff" />
          </View>
          {isUploading && (
            <View style={styles.uploadingOverlay}>
              <ActivityIndicator size="large" color="#fff" />
            </View>
          )}
        </TouchableOpacity>

        {isEditing ? (
          <View style={styles.editContainer}>
            <TextInput
              style={[styles.input, isDarkMode && styles.darkInput]}
              value={editedFirstName}
              onChangeText={setEditedFirstName}
              placeholder="First Name"
              placeholderTextColor={isDarkMode ? "#999" : "#666"}
            />
            <TextInput
              style={[styles.input, isDarkMode && styles.darkInput]}
              value={editedLastName}
              onChangeText={setEditedLastName}
              placeholder="Last Name"
              placeholderTextColor={isDarkMode ? "#999" : "#666"}
            />
            <View style={styles.editButtons}>
              <TouchableOpacity style={styles.editButton} onPress={updateProfile}>
                <Text style={styles.editButtonText}>Save</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.editButton, styles.cancelButton]} onPress={() => setIsEditing(false)}>
                <Text style={styles.editButtonText}>Cancel</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          <View style={styles.nameContainer}>
            <Text style={[styles.name, isDarkMode && styles.darkText]}>
              {userData.first_name && userData.last_name 
                ? `${userData.first_name} ${userData.last_name}`
                : userData.email}
            </Text>
            <TouchableOpacity onPress={() => setIsEditing(true)}>
              <Ionicons name="pencil" size={20} color={isDarkMode ? "#4A90E2" : "#007AFF"} />
            </TouchableOpacity>
          </View>
        )}
      </View>

      <TouchableOpacity 
        style={[styles.themeButton, isDarkMode && styles.darkThemeButton]} 
        onPress={toggleTheme}
      >
        <Ionicons 
          name={isDarkMode ? "sunny" : "moon"} 
          size={24} 
          color={isDarkMode ? "#FFD700" : "#fff"} 
        />
        <Text style={[styles.themeButtonText, isDarkMode && styles.darkText]}>
          {isDarkMode ? "Light Mode" : "Dark Mode"}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    paddingTop: 40,
  },
  darkContainer: {
    backgroundColor: '#2C2C2C',
  },
  header: {
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  darkHeader: {
    borderBottomColor: '#404040',
  },
  avatarContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
    position: 'relative',
  },
  avatar: {
    width: '100%',
    height: '100%',
    borderRadius: 50,
  },
  editIconContainer: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: '#007AFF',
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#fff',
  },
  uploadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 50,
    alignItems: 'center',
    justifyContent: 'center',
  },
  editContainer: {
    width: '100%',
    paddingHorizontal: 20,
    marginTop: 10,
  },
  input: {
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 12,
    marginBottom: 10,
    fontSize: 16,
  },
  darkInput: {
    backgroundColor: '#404040',
    color: '#fff',
  },
  editButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
  },
  editButton: {
    flex: 1,
    backgroundColor: '#007AFF',
    padding: 12,
    borderRadius: 8,
    marginHorizontal: 5,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#ff3b30',
  },
  editButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  nameContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginRight: 10,
  },
  darkText: {
    color: '#fff',
  },
  themeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    margin: 20,
    padding: 15,
    backgroundColor: '#404040',
    borderRadius: 10,
  },
  darkThemeButton: {
    backgroundColor: '#4A90E2',
  },
  themeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  logoutButton: {
    margin: 20,
    padding: 15,
    backgroundColor: '#ff3b30',
    borderRadius: 10,
    alignItems: 'center',
  },
  logoutText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
}); 