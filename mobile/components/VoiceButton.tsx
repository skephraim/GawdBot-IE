import { useState, useRef } from 'react';
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { Audio } from 'expo-av';
import { api } from '../lib/api';

interface Props {
  onTranscribed: (text: string) => void;
}

export function VoiceButton({ onTranscribed }: Props) {
  const [state, setState] = useState<'idle' | 'recording' | 'processing'>('idle');
  const recording = useRef<Audio.Recording | null>(null);

  const startRecording = async () => {
    try {
      const { granted } = await Audio.requestPermissionsAsync();
      if (!granted) { Alert.alert('Microphone permission required'); return; }
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const { recording: rec } = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      recording.current = rec;
      setState('recording');
    } catch (e) {
      Alert.alert('Could not start recording');
    }
  };

  const stopRecording = async () => {
    if (!recording.current) return;
    setState('processing');
    try {
      await recording.current.stopAndUnloadAsync();
      const uri = recording.current.getURI()!;
      recording.current = null;
      const text = await api.transcribeAudio(uri);
      if (text) onTranscribed(text);
      else Alert.alert('Could not transcribe audio');
    } catch (e) {
      Alert.alert('Transcription failed');
    } finally {
      setState('idle');
    }
  };

  const color = state === 'recording' ? '#ef4444' : '#22c55e';
  const label = state === 'idle' ? '🎤' : state === 'recording' ? '⏹' : '';

  return (
    <TouchableOpacity
      style={[styles.btn, { backgroundColor: color }]}
      onPressIn={startRecording}
      onPressOut={stopRecording}
      disabled={state === 'processing'}
    >
      {state === 'processing'
        ? <ActivityIndicator color="#fff" size="small" />
        : <Text style={styles.label}>{label}</Text>}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  btn: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', marginHorizontal: 4 },
  label: { fontSize: 20 },
});
