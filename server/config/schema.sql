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
    record JSONB;
BEGIN
    FOR record IN
        SELECT payload
        FROM scan_ingest_backlog
        ORDER BY received_at
        LIMIT limit_count
    LOOP
        INSERT INTO part_locations (order_code, location_code, device_id, updated_at)
        VALUES (
            record->>'order_code',
            record->>'location_code',
            record->>'device_id',
            NOW()
        )
        ON CONFLICT (order_code)
        DO UPDATE SET
            location_code = EXCLUDED.location_code,
            device_id = EXCLUDED.device_id,
            updated_at = NOW();

        DELETE FROM scan_ingest_backlog
        WHERE id IN (
            SELECT id
            FROM scan_ingest_backlog
            ORDER BY received_at
            LIMIT 1
        );

        processed := processed + 1;
    END LOOP;

    RETURN processed;
END;
$$;
