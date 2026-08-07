-- RBI PostgreSQL schema used by routes/rbi.py and chatbot_backend.
\connect aegis_rbi_notifications

CREATE TABLE IF NOT EXISTS master_summaries (
    id BIGSERIAL PRIMARY KEY,
    run_date DATE,
    pdf_link TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_master_summaries_run_date ON master_summaries(run_date DESC);
