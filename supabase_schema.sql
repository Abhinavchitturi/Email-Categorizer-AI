-- Run this in Supabase SQL Editor to create the emails table
-- Go to: https://supabase.com/dashboard/project/YOUR_PROJECT/sql

CREATE TABLE IF NOT EXISTS emails (
    message_id TEXT PRIMARY KEY,
    sender TEXT,
    subject TEXT,
    snippet TEXT,
    category TEXT,
    confidence REAL,
    reasoning TEXT,
    processed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_category ON emails(category);
CREATE INDEX IF NOT EXISTS idx_processed_at ON emails(processed_at DESC);

-- Enable Row Level Security (optional, for future auth)
ALTER TABLE emails ENABLE ROW LEVEL SECURITY;

-- Allow all operations for now (adjust for production)
CREATE POLICY "Allow all" ON emails FOR ALL USING (true);