-- ============================================================
-- GawdBotE — RLS Security Fix
-- Run in Supabase SQL Editor
-- Locks all tables to service_role only (backend uses service key)
-- ============================================================

-- Drop the open policies
DROP POLICY IF EXISTS "Allow all for service role" ON messages;
DROP POLICY IF EXISTS "Allow all for service role" ON memory;
DROP POLICY IF EXISTS "Allow all for service role" ON logs;
DROP POLICY IF EXISTS "Allow all for service role" ON skills;

-- Create restricted policies: service_role only
CREATE POLICY "service_role_only" ON messages
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_only" ON memory
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_only" ON logs
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "service_role_only" ON skills
  FOR ALL USING (auth.role() = 'service_role');
