-- Run this in Supabase SQL Editor to fix RLS policy
-- Go to: https://supabase.com/dashboard/project/YOUR_PROJECT/sql

-- Disable RLS for now (simplest for personal use)
ALTER TABLE emails DISABLE ROW LEVEL SECURITY;

-- Or if you want RLS enabled with a permissive policy:
-- ALTER TABLE emails ENABLE ROW LEVEL SECURITY;
-- DROP POLICY IF EXISTS "Allow all" ON emails;
-- CREATE POLICY "Allow all" ON emails FOR ALL USING (true);