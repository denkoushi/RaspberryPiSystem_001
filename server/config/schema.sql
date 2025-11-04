-- Schema placeholder for RaspberryPiServer database objects.

CREATE TABLE IF NOT EXISTS scan_ingest_backlog (
    id BIGSERIAL PRIMARY KEY,
    payload JSONB NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scan_ingest_backlog_received_at
    ON scan_ingest_backlog (received_at DESC);

-- Optional target table (to be adjusted based on final schema)
CREATE TABLE IF NOT EXISTS part_locations (
    order_code TEXT PRIMARY KEY,
    location_code TEXT NOT NULL,
    device_id TEXT,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Stored procedure for draining backlog (placeholder logic)
CREATE OR REPLACE FUNCTION drain_scan_backlog(limit_count INTEGER DEFAULT 100)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    processed INTEGER := 0;
BEGIN
    WITH candidates AS (
        SELECT id, payload
        FROM scan_ingest_backlog
        ORDER BY received_at
        LIMIT limit_count
        FOR UPDATE SKIP LOCKED
    ),
    upsert AS (
        INSERT INTO part_locations (order_code, location_code, device_id, updated_at)
        SELECT
            payload->>'order_code' AS order_code,
            payload->>'location_code' AS location_code,
            payload->>'device_id' AS device_id,
            NOW() AS updated_at
        FROM candidates
        ON CONFLICT (order_code)
        DO UPDATE SET
            location_code = EXCLUDED.location_code,
            device_id = EXCLUDED.device_id,
            updated_at = NOW()
        RETURNING 1
    ),
    deleted AS (
        DELETE FROM scan_ingest_backlog
        WHERE id IN (SELECT id FROM candidates)
        RETURNING 1
    )
    SELECT COALESCE(COUNT(*), 0) INTO processed FROM deleted;

    RETURN processed;
END;
$$;
