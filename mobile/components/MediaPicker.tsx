import { TouchableOpacity, Text, StyleSheet, Alert } from 'react-native';
import * as ImagePicker from 'expo-image-picker';

interface Props {
  onImage: (uri: string, caption: string) => void;
}

export function MediaPicker({ onImage }: Props) {
  const pick = async () => {
    const { granted } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!granted) { Alert.alert('Gallery permission required'); return; }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!result.canceled && result.assets[0]) {
      onImage(result.assets[0].uri, 'Analyze this image.');
    }
  };

  const camera = async () => {
    const { granted } = await ImagePicker.requestCameraPermissionsAsync();
    if (!granted) { Alert.alert('Camera permission required'); return; }
    const result = await ImagePicker.launchCameraAsync({ quality: 0.8 });
    if (!result.canceled && result.assets[0]) {
      onImage(result.assets[0].uri, 'Analyze this image.');
    }
  };

  return (
    <>
      <TouchableOpacity style={styles.btn} onPress={camera}>
        <Text style={styles.label}>📷</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.btn} onPress={pick}>
        <Text style={styles.label}>🖼️</Text>
      </TouchableOpacity>
    </>
  );
}

const styles = StyleSheet.create({
  btn: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#374151', alignItems: 'center', justifyContent: 'center', marginHorizontal: 4 },
  label: { fontSize: 20 },
});
