-- GawdBotE Supabase Schema
-- Run this in Supabase SQL Editor
-- Adapted from claude-telegram-relay with multi-channel support

-- Required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_net;

-- ============================================================
-- MESSAGES TABLE (Conversation History)
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  channel TEXT DEFAULT 'web',  -- 'web', 'telegram', 'discord', 'voice', 'cli'
  session_id TEXT,             -- Optional: group messages by session
  metadata JSONB DEFAULT '{}',
  embedding VECTOR(1536)       -- For semantic search (auto-generated via Edge Function)
);

CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);

-- ============================================================
-- MEMORY TABLE (Facts, Goals, Preferences)
-- ============================================================
CREATE TABLE IF NOT EXISTS memory (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  type TEXT NOT NULL CHECK (type IN ('fact', 'goal', 'completed_goal', 'preference')),
  content TEXT NOT NULL,
  source TEXT DEFAULT 'chat',  -- Where this memory came from
  deadline TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  priority INTEGER DEFAULT 0,
  metadata JSONB DEFAULT '{}',
  embedding VECTOR(1536)
);

CREATE INDEX IF NOT EXISTS idx_memory_type ON memory(type);
CREATE INDEX IF NOT EXISTS idx_memory_created_at ON memory(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_priority ON memory(priority DESC);

-- ============================================================
-- LOGS TABLE (Observability)
-- ============================================================
CREATE TABLE IF NOT EXISTS logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  level TEXT DEFAULT 'info' CHECK (level IN ('debug', 'info', 'warn', 'error')),
  event TEXT NOT NULL,
  message TEXT,
  metadata JSONB DEFAULT '{}',
  session_id TEXT,
  duration_ms INTEGER,
  channel TEXT
);

CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_event ON logs(event);

-- ============================================================
-- SKILLS TABLE (Skill registry state)
-- ============================================================
CREATE TABLE IF NOT EXISTS skills (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  enabled BOOLEAN DEFAULT true,
  config JSONB DEFAULT '{}',
  last_used TIMESTAMPTZ,
  use_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for service role" ON messages FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON memory FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON logs FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON skills FOR ALL USING (true);

-- ============================================================
-- HELPER FUNCTIONS
-- ============================================================

CREATE OR REPLACE FUNCTION get_recent_messages(
  limit_count INTEGER DEFAULT 20,
  channel_filter TEXT DEFAULT NULL
)
RETURNS TABLE (id UUID, created_at TIMESTAMPTZ, role TEXT, content TEXT, channel TEXT) AS $$
BEGIN
  RETURN QUERY
  SELECT m.id, m.created_at, m.role, m.content, m.channel
  FROM messages m
  WHERE (channel_filter IS NULL OR m.channel = channel_filter)
  ORDER BY m.created_at DESC
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_active_goals()
RETURNS TABLE (id UUID, content TEXT, deadline TIMESTAMPTZ, priority INTEGER) AS $$
BEGIN
  RETURN QUERY
  SELECT m.id, m.content, m.deadline, m.priority
  FROM memory m
  WHERE m.type = 'goal'
  ORDER BY m.priority DESC, m.created_at DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_facts()
RETURNS TABLE (id UUID, content TEXT) AS $$
BEGIN
  RETURN QUERY
  SELECT m.id, m.content
  FROM memory m
  WHERE m.type = 'fact'
  ORDER BY m.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SEMANTIC SEARCH
-- ============================================================

CREATE OR REPLACE FUNCTION match_messages(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id UUID, content TEXT, role TEXT, created_at TIMESTAMPTZ, similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT m.id, m.content, m.role, m.created_at,
    1 - (m.embedding <=> query_embedding) AS similarity
  FROM messages m
  WHERE m.embedding IS NOT NULL
    AND 1 - (m.embedding <=> query_embedding) > match_threshold
  ORDER BY m.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION match_memory(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id UUID, content TEXT, type TEXT, created_at TIMESTAMPTZ, similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT m.id, m.content, m.type, m.created_at,
    1 - (m.embedding <=> query_embedding) AS similarity
  FROM memory m
  WHERE m.embedding IS NOT NULL
    AND 1 - (m.embedding <=> query_embedding) > match_threshold
  ORDER BY m.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
