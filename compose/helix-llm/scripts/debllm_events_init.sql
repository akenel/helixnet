CREATE TABLE IF NOT EXISTS debllm_events (
  id SERIAL PRIMARY KEY,
  container TEXT,
  raw_s3 TEXT,
  summary TEXT,
  suggestion TEXT,
  created_at TIMESTAMP WITH TIME ZONE,
  status TEXT DEFAULT 'new'
);
