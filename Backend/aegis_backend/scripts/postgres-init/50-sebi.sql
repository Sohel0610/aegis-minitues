-- SEBI PostgreSQL schema used by routes/sebi.py and chatbot_backend.
\connect aegis_sebi_db

CREATE TABLE IF NOT EXISTS aegis_sebi_data (
    id BIGSERIAL PRIMARY KEY,
    date_key VARCHAR(20),
    row_index INTEGER,
    pdf_link TEXT,
    summary TEXT,
    inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_aegis_sebi_data_date_key ON aegis_sebi_data(date_key);
CREATE INDEX IF NOT EXISTS idx_aegis_sebi_data_inserted_at ON aegis_sebi_data(inserted_at DESC);
