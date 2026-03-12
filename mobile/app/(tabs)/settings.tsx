import { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Alert, ActivityIndicator } from 'react-native';
import { getBackendUrl, setBackendUrl, api } from '../../lib/api';

export default function SettingsScreen() {
  const [url, setUrl] = useState('');
  const [health, setHealth] = useState<{ status: string; memory: string; model: string } | null>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => { getBackendUrl().then(setUrl); }, []);

  const save = async () => {
    await setBackendUrl(url.trim());
    Alert.alert('Saved', 'Backend URL updated. Test connection to verify.');
  };

  const test = async () => {
    setTesting(true);
    setHealth(null);
    try {
      const h = await api.health();
      setHealth(h);
    } catch {
      Alert.alert('Connection failed', 'Could not reach the backend. Check the URL and make sure the backend + Cloudflare tunnel are running.');
    } finally {
      setTesting(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
      <Section title="Backend URL">
        <Text style={styles.hint}>Set this to your Cloudflare Tunnel URL so the app works from anywhere.</Text>
        <TextInput
          style={styles.input}
          value={url}
          onChangeText={setUrl}
          placeholder="https://xxxx.trycloudflare.com"
          placeholderTextColor="#6b7280"
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
        />
        <View style={styles.btnRow}>
          <TouchableOpacity style={styles.btn} onPress={save}>
            <Text style={styles.btnText}>Save</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.btn, styles.outlineBtn]} onPress={test} disabled={testing}>
            {testing ? <ActivityIndicator color="#22c55e" size="small" /> : <Text style={styles.outlineBtnText}>Test Connection</Text>}
          </TouchableOpacity>
        </View>

        {health && (
          <View style={styles.healthCard}>
            <HealthRow label="Status" value={health.status === 'ok' ? '✅ Online' : '❌ Error'} />
            <HealthRow label="Memory" value={health.memory} />
            <HealthRow label="Model" value={health.model} />
          </View>
        )}
      </Section>

      <Section title="How to Run">
        <Text style={styles.mono}>{'# Terminal 1 — Backend\ncd ~/GawdBotE\n.venv/bin/python backend/main.py\n\n# Terminal 2 — Tunnel\ncloudflared tunnel --url http://localhost:8000\n\n# Terminal 3 — Telegram\ncd ~/GawdBotE/interfaces/telegram\nbun run bot.ts'}</Text>
      </Section>

      <Section title="About">
        <HealthRow label="App" value="GawdBot-IE Mobile" />
        <HealthRow label="Stack" value="Expo + React Native" />
        <HealthRow label="Repo" value="github.com/skephraim/GawdBot-IE" />
      </Section>
    </ScrollView>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={{ marginBottom: 28 }}>
      <Text style={sStyles.title}>{title}</Text>
      {children}
    </View>
  );
}

function HealthRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={sStyles.row}>
      <Text style={sStyles.label}>{label}</Text>
      <Text style={sStyles.value}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#111827', padding: 16 },
  hint: { color: '#9ca3af', fontSize: 13, marginBottom: 10, lineHeight: 19 },
  input: { backgroundColor: '#1f2937', color: '#f9fafb', borderRadius: 10, padding: 12, fontSize: 14, marginBottom: 10 },
  btnRow: { flexDirection: 'row', gap: 10 },
  btn: { backgroundColor: '#22c55e', borderRadius: 10, paddingVertical: 10, paddingHorizontal: 18 },
  btnText: { color: '#fff', fontWeight: '600', fontSize: 14 },
  outlineBtn: { backgroundColor: 'transparent', borderWidth: 1, borderColor: '#22c55e' },
  outlineBtnText: { color: '#22c55e', fontWeight: '600', fontSize: 14 },
  healthCard: { backgroundColor: '#1f2937', borderRadius: 10, padding: 12, marginTop: 12 },
  mono: { backgroundColor: '#1f2937', color: '#22c55e', fontFamily: 'monospace', fontSize: 12, padding: 14, borderRadius: 10, lineHeight: 20 },
});

const sStyles = StyleSheet.create({
  title: { color: '#9ca3af', fontSize: 12, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: '#1f2937' },
  label: { color: '#9ca3af', fontSize: 13 },
  value: { color: '#f9fafb', fontSize: 13 },
});
