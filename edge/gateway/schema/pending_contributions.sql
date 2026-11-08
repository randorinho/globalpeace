-- Edge buffer for public contributions (dark-origin phase 2,
-- docs/DARK_ORIGIN.md). Rows are written by the worker's POST handler and
-- drained by the origin (pipelines/contributions); ack marks drained=1
-- instead of deleting so the hourly rate limit stays exact across drains,
-- and drained rows are purged after 25 h.
CREATE TABLE IF NOT EXISTS pending_contributions (
  id TEXT PRIMARY KEY,
  event_id TEXT,
  text TEXT NOT NULL,
  url TEXT,
  client_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  drained INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_pending_client ON pending_contributions (client_hash, created_at);
CREATE INDEX IF NOT EXISTS idx_pending_drained ON pending_contributions (drained, created_at);
