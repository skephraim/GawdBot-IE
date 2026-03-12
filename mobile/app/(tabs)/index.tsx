import { useState, useEffect, useRef, useCallback } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator } from 'react-native';
import { useFocusEffect } from 'expo-router';
import * as SMS from 'expo-sms';
import * as MailComposer from 'expo-mail-composer';
import { WSManager } from '../../lib/websocket';
import { api } from '../../lib/api';
import { VoiceButton } from '../../components/VoiceButton';
import { MediaPicker } from '../../components/MediaPicker';

interface Message { id: string; role: 'user' | 'assistant' | 'system'; content: string; }

const ws = new WSManager();

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [connected, setConnected] = useState(false);
  const listRef = useRef<FlatList>(null);

  const addMessage = (role: Message['role'], content: string) => {
    const msg: Message = { id: `${Date.now()}-${Math.random()}`, role, content };
    setMessages(prev => [...prev, msg]);
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    return msg;
  };

  useFocusEffect(useCallback(() => {
    ws.connect((msg) => {
      if (msg.type === 'typing') setTyping(!!msg.value);
      if (msg.type === 'message' && msg.content) {
        setTyping(false);
        addMessage('assistant', msg.content);
      }
      setConnected(ws.isConnected);
    });
    setConnected(ws.isConnected);
    return () => { ws.disconnect(); };
  }, []));

  const send = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    addMessage('user', trimmed);
    setInput('');
    if (!ws.send(trimmed)) {
      // Fallback to REST if WS not connected
      setTyping(true);
      api.chat(trimmed).then(r => {
        setTyping(false);
        addMessage('assistant', r.response);
      }).catch(() => {
        setTyping(false);
        addMessage('system', 'Connection error. Is the backend running?');
      });
    }
  };

  const handleImage = (uri: string, caption: string) => {
    send(`[Image]: ${caption}\n(Photo: ${uri})`);
  };

  const handleSMS = async () => {
    const available = await SMS.isAvailableAsync();
    if (available) await SMS.sendSMSAsync([], '');
  };

  const handleEmail = async () => {
    const available = await MailComposer.isAvailableAsync();
    if (available) await MailComposer.composeAsync({});
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined} keyboardVerticalOffset={90}>
      {/* Status bar */}
      <View style={styles.statusBar}>
        <View style={[styles.dot, { backgroundColor: connected ? '#22c55e' : '#6b7280' }]} />
        <Text style={styles.statusText}>{connected ? 'Connected' : 'Connecting...'}</Text>
      </View>

      {/* Messages */}
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={m => m.id}
        contentContainerStyle={styles.messageList}
        renderItem={({ item }) => (
          <View style={[styles.bubble, item.role === 'user' ? styles.userBubble : item.role === 'system' ? styles.systemBubble : styles.aiBubble]}>
            <Text style={[styles.bubbleText, item.role === 'system' && styles.systemText]}>{item.content}</Text>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.empty}>Say something to GawdBot-IE 👋</Text>}
      />

      {/* Typing indicator */}
      {typing && (
        <View style={styles.typingRow}>
          <ActivityIndicator size="small" color="#22c55e" />
          <Text style={styles.typingText}> GawdBot-IE is thinking...</Text>
        </View>
      )}

      {/* Input row */}
      <View style={styles.inputRow}>
        <VoiceButton onTranscribed={(t) => send(t)} />
        <MediaPicker onImage={handleImage} />
        <TouchableOpacity style={styles.iconBtn} onPress={handleSMS}><Text style={styles.iconLabel}>💬</Text></TouchableOpacity>
        <TouchableOpacity style={styles.iconBtn} onPress={handleEmail}><Text style={styles.iconLabel}>📧</Text></TouchableOpacity>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Message GawdBot-IE..."
          placeholderTextColor="#6b7280"
          multiline
          onSubmitEditing={() => send(input)}
          returnKeyType="send"
        />
        <TouchableOpacity style={styles.sendBtn} onPress={() => send(input)}>
          <Text style={styles.sendLabel}>↑</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#111827' },
  statusBar: { flexDirection: 'row', alignItems: 'center', padding: 8, paddingHorizontal: 16, borderBottomWidth: 1, borderBottomColor: '#1f2937' },
  dot: { width: 8, height: 8, borderRadius: 4, marginRight: 6 },
  statusText: { color: '#9ca3af', fontSize: 12 },
  messageList: { padding: 16, paddingBottom: 8 },
  bubble: { maxWidth: '80%', borderRadius: 16, padding: 12, marginBottom: 8 },
  userBubble: { backgroundColor: '#22c55e', alignSelf: 'flex-end', borderBottomRightRadius: 4 },
  aiBubble: { backgroundColor: '#1f2937', alignSelf: 'flex-start', borderBottomLeftRadius: 4 },
  systemBubble: { backgroundColor: '#374151', alignSelf: 'center' },
  bubbleText: { color: '#f9fafb', fontSize: 15, lineHeight: 21 },
  systemText: { color: '#9ca3af', fontSize: 13 },
  empty: { color: '#6b7280', textAlign: 'center', marginTop: 60, fontSize: 15 },
  typingRow: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingBottom: 4 },
  typingText: { color: '#22c55e', fontSize: 13 },
  inputRow: { flexDirection: 'row', alignItems: 'flex-end', padding: 8, borderTopWidth: 1, borderTopColor: '#1f2937', backgroundColor: '#111827' },
  input: { flex: 1, backgroundColor: '#1f2937', borderRadius: 20, paddingHorizontal: 14, paddingVertical: 10, color: '#f9fafb', fontSize: 15, maxHeight: 100, marginHorizontal: 4 },
  sendBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#22c55e', alignItems: 'center', justifyContent: 'center', marginLeft: 4 },
  sendLabel: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  iconBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#374151', alignItems: 'center', justifyContent: 'center', marginHorizontal: 2 },
  iconLabel: { fontSize: 18 },
});
