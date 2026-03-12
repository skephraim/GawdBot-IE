import { useState, useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { api } from '../../lib/api';

export default function MemoryScreen() {
  const [facts, setFacts] = useState<{ id: string; content: string }[]>([]);
  const [goals, setGoals] = useState<{ id: string; content: string; deadline?: string }[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    setRefreshing(true);
    const [f, g] = await Promise.all([api.getFacts(), api.getGoals()]).finally(() => setRefreshing(false));
    setFacts(f.facts);
    setGoals(g.goals);
  };

  useFocusEffect(useCallback(() => { load(); }, []));

  const deleteFact = (id: string) => {
    Alert.alert('Delete fact?', undefined, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: async () => {
        await api.deleteFact(id);
        setFacts(prev => prev.filter(f => f.id !== id));
      }},
    ]);
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={[]}
        renderItem={null}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={load} tintColor="#22c55e" />}
        ListHeaderComponent={
          <>
            <Section title={`🎯 Goals (${goals.length})`}>
              {goals.length === 0
                ? <EmptyState text="No active goals" />
                : goals.map(g => (
                  <View key={g.id} style={styles.card}>
                    <Text style={styles.cardText}>{g.content}</Text>
                    {g.deadline && <Text style={styles.badge}>📅 {g.deadline.slice(0, 10)}</Text>}
                  </View>
                ))}
            </Section>

            <Section title={`💡 Facts (${facts.length})`}>
              {facts.length === 0
                ? <EmptyState text="No facts stored yet" />
                : facts.map(f => (
                  <TouchableOpacity key={f.id} style={styles.card} onLongPress={() => deleteFact(f.id)}>
                    <Text style={styles.cardText}>{f.content}</Text>
                    <Text style={styles.hint}>Hold to delete</Text>
                  </TouchableOpacity>
                ))}
            </Section>
          </>
        }
      />
    </View>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={{ marginBottom: 24 }}>
      <Text style={sectionStyles.title}>{title}</Text>
      {children}
    </View>
  );
}

function EmptyState({ text }: { text: string }) {
  return <Text style={sectionStyles.empty}>{text}</Text>;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#111827', padding: 16 },
  card: { backgroundColor: '#1f2937', borderRadius: 12, padding: 14, marginBottom: 8 },
  cardText: { color: '#f9fafb', fontSize: 14, lineHeight: 20 },
  badge: { color: '#22c55e', fontSize: 12, marginTop: 6 },
  hint: { color: '#4b5563', fontSize: 11, marginTop: 4 },
});

const sectionStyles = StyleSheet.create({
  title: { color: '#9ca3af', fontSize: 13, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 },
  empty: { color: '#4b5563', fontSize: 14, fontStyle: 'italic', padding: 8 },
});
