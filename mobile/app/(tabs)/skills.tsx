import { useState, useCallback } from 'react';
import { View, Text, FlatList, Switch, StyleSheet, RefreshControl } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { api } from '../../lib/api';

interface Skill { name: string; description: string; commands: string[]; enabled: boolean; }

export default function SkillsScreen() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    setRefreshing(true);
    const data = await api.getSkills().finally(() => setRefreshing(false));
    setSkills(data.skills);
  };

  useFocusEffect(useCallback(() => { load(); }, []));

  const toggle = async (name: string, enabled: boolean) => {
    setSkills(prev => prev.map(s => s.name === name ? { ...s, enabled } : s));
    await api.toggleSkill(name, enabled);
  };

  return (
    <FlatList
      style={styles.container}
      data={skills}
      keyExtractor={s => s.name}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={load} tintColor="#22c55e" />}
      renderItem={({ item }) => (
        <View style={styles.card}>
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={styles.name}>{item.name}</Text>
              {item.description ? <Text style={styles.desc}>{item.description}</Text> : null}
            </View>
            <Switch
              value={item.enabled}
              onValueChange={(v) => toggle(item.name, v)}
              trackColor={{ false: '#374151', true: '#22c55e' }}
              thumbColor="#fff"
            />
          </View>
          {item.commands?.length > 0 && (
            <View style={styles.commands}>
              {item.commands.map(c => (
                <Text key={c} style={styles.chip}>/{c}</Text>
              ))}
            </View>
          )}
        </View>
      )}
      ListEmptyComponent={
        <View style={styles.empty}>
          <Text style={styles.emptyIcon}>⚡</Text>
          <Text style={styles.emptyText}>No skills installed yet</Text>
          <Text style={styles.emptyHint}>Add skills to ~/GawdBotE/skills/</Text>
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#111827', padding: 16 },
  card: { backgroundColor: '#1f2937', borderRadius: 12, padding: 14, marginBottom: 10 },
  row: { flexDirection: 'row', alignItems: 'center' },
  name: { color: '#f9fafb', fontSize: 15, fontWeight: '600' },
  desc: { color: '#9ca3af', fontSize: 13, marginTop: 2 },
  commands: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 10, gap: 6 },
  chip: { backgroundColor: '#374151', color: '#22c55e', fontSize: 12, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, fontFamily: 'monospace' },
  empty: { alignItems: 'center', marginTop: 80 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: { color: '#9ca3af', fontSize: 16 },
  emptyHint: { color: '#4b5563', fontSize: 13, marginTop: 4 },
});
