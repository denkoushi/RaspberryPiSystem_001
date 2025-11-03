-- Schema placeholder for RaspberryPiServer database objects.

CREATE TABLE IF NOT EXISTS scan_ingest_backlog (
    id BIGSERIAL PRIMARY KEY,
    payload JSONB NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scan_ingest_backlog_received_at
    ON scan_ingest_backlog (received_at DESC);
