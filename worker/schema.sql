-- Chat log for "Ask TechForDad". Applied on every deploy (idempotent). Emails, phone numbers and postal codes are
-- removed from questions before they are stored; no IP address is stored. Rows older than 365 days are deleted daily.
CREATE TABLE IF NOT EXISTS chats (
  id TEXT PRIMARY KEY,
  ts TEXT NOT NULL,
  session TEXT,
  page TEXT,
  country TEXT,
  question TEXT NOT NULL,
  answer TEXT,
  sources TEXT,
  products TEXT,
  mode TEXT NOT NULL,
  model TEXT,
  top_score REAL,
  latency_ms INTEGER,
  helpful INTEGER
);
CREATE INDEX IF NOT EXISTS chats_ts ON chats (ts);
