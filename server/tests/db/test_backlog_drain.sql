-- setup for drain_scan_backlog tests
CREATE TEMP TABLE test_scan_ingest_backlog AS
SELECT 1 AS id, '{"order_code":"TEST-001","location_code":"RACK-A1"}'::jsonb AS payload, NOW() AS received_at
UNION ALL
SELECT 2, '{"order_code":"TEST-002","location_code":"RACK-A2"}'::jsonb, NOW();

CREATE TEMP TABLE test_part_locations (
    order_code TEXT PRIMARY KEY,
    location_code TEXT NOT NULL,
    device_id TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
