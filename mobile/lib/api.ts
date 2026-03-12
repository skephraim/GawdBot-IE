import AsyncStorage from '@react-native-async-storage/async-storage';

const DEFAULT_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function getBackendUrl(): Promise<string> {
  const stored = await AsyncStorage.getItem('backend_url');
  return stored || DEFAULT_URL;
}

export async function setBackendUrl(url: string): Promise<void> {
  await AsyncStorage.setItem('backend_url', url);
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const base = await getBackendUrl();
  const res = await fetch(`${base}${path}`, options);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  health: () => request<{ status: string; memory: string; model: string; version: string }>('/health'),

  chat: (message: string, channel = 'mobile', sessionId?: string) =>
    request<{ response: string }>('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, channel, session_id: sessionId }),
    }),

  getFacts: () => request<{ facts: { id: string; content: string }[] }>('/memory/facts'),
  getGoals: () => request<{ goals: { id: string; content: string; deadline?: string; priority?: number }[] }>('/memory/goals'),
  getMessages: (limit = 50) => request<{ messages: { id: string; role: string; content: string; created_at: string }[] }>(`/memory/messages?limit=${limit}&channel=mobile`),
  deleteFact: (id: string) => request(`/memory/fact/${id}`, { method: 'DELETE' }),

  getSkills: () => request<{ skills: { name: string; description: string; commands: string[]; enabled: boolean }[] }>('/skills'),
  toggleSkill: (name: string, enabled: boolean) =>
    request(`/skills/${encodeURIComponent(name)}/toggle?enabled=${enabled}`, { method: 'POST' }),

  transcribeAudio: async (uri: string): Promise<string> => {
    const base = await getBackendUrl();
    const formData = new FormData();
    formData.append('audio', { uri, name: 'voice.m4a', type: 'audio/m4a' } as any);
    const res = await fetch(`${base}/voice/transcribe`, { method: 'POST', body: formData });
    if (!res.ok) throw new Error('Transcription failed');
    const data = await res.json();
    return data.text || '';
  },

  registerDevice: (token: string, platform: string) =>
    request('/device/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, platform }),
    }).catch(() => null),

  sendNotification: (token: string, title: string, body: string) =>
    request('/notify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, title, body }),
    }).catch(() => null),
};
