-- Initialize the BSE notifications Postgres database used by routes/bse.py and routes/analytics.py.

\connect aegis_bse_notification

CREATE TABLE IF NOT EXISTS daily_logs (
    id BIGSERIAL PRIMARY KEY,
    sr_no INTEGER,
    entity_name TEXT,
    link TEXT,
    nature TEXT,
    summary TEXT,
    record_date DATE,
    inserted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_logs_record_date ON daily_logs(record_date);
CREATE INDEX IF NOT EXISTS idx_daily_logs_link ON daily_logs(link);

