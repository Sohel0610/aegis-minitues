-- Initialize Insider Trading and Visit Tracking tables for local Postgres.

-- -------------------------------------------------------------------
-- Insider Trading (DB names used in different .env files)
-- -------------------------------------------------------------------

\connect aegis_insider

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    company_name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS depository_types (
    id SERIAL PRIMARY KEY,
    type_name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS result_batches (
    id SERIAL PRIMARY KEY,
    batch_name TEXT UNIQUE NOT NULL,
    older_date DATE,
    latest_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS summary (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    batch_id INTEGER REFERENCES result_batches(id) ON DELETE CASCADE,
    depository_id INTEGER REFERENCES depository_types(id) ON DELETE CASCADE,
    added_count INTEGER DEFAULT 0,
    removed_count INTEGER DEFAULT 0,
    changed_count INTEGER DEFAULT 0,
    unchanged_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    empty_pangir_latest INTEGER DEFAULT 0,
    empty_pangir_older INTEGER DEFAULT 0
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_summary_company_batch_depository ON summary(company_id, batch_id, depository_id);

CREATE TABLE IF NOT EXISTS shareholder_records (
    id BIGSERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    batch_id INTEGER REFERENCES result_batches(id) ON DELETE CASCADE,
    depository_id INTEGER REFERENCES depository_types(id) ON DELETE CASCADE,
    pangir TEXT,
    name TEXT,
    email TEXT,
    position_latest NUMERIC,
    position_older NUMERIC,
    position_difference NUMERIC,
    status TEXT
);

-- -------------------------------------------------------------------
\connect aegis_insider_trading
-- Same schema as above

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    company_name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS depository_types (
    id SERIAL PRIMARY KEY,
    type_name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS result_batches (
    id SERIAL PRIMARY KEY,
    batch_name TEXT UNIQUE NOT NULL,
    older_date DATE,
    latest_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS summary (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    batch_id INTEGER REFERENCES result_batches(id) ON DELETE CASCADE,
    depository_id INTEGER REFERENCES depository_types(id) ON DELETE CASCADE,
    added_count INTEGER DEFAULT 0,
    removed_count INTEGER DEFAULT 0,
    changed_count INTEGER DEFAULT 0,
    unchanged_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    empty_pangir_latest INTEGER DEFAULT 0,
    empty_pangir_older INTEGER DEFAULT 0
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_summary_company_batch_depository ON summary(company_id, batch_id, depository_id);

CREATE TABLE IF NOT EXISTS shareholder_records (
    id BIGSERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    batch_id INTEGER REFERENCES result_batches(id) ON DELETE CASCADE,
    depository_id INTEGER REFERENCES depository_types(id) ON DELETE CASCADE,
    pangir TEXT,
    name TEXT,
    email TEXT,
    position_latest NUMERIC,
    position_older NUMERIC,
    position_difference NUMERIC,
    status TEXT
);

-- -------------------------------------------------------------------
-- Visit Tracking (schema lives inside whatever DB POSTGRES_DATABASE points to)
-- -------------------------------------------------------------------

\connect aegis_insider

CREATE SCHEMA IF NOT EXISTS visit_tracking;
CREATE TABLE IF NOT EXISTS visit_tracking.visits (
    id INTEGER PRIMARY KEY,
    count INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);
INSERT INTO visit_tracking.visits (id, count)
VALUES (1, 0)
ON CONFLICT (id) DO NOTHING;

\connect aegis_platform

CREATE SCHEMA IF NOT EXISTS visit_tracking;
CREATE TABLE IF NOT EXISTS visit_tracking.visits (
    id INTEGER PRIMARY KEY,
    count INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);
INSERT INTO visit_tracking.visits (id, count)
VALUES (1, 0)
ON CONFLICT (id) DO NOTHING;

\connect visit_tracking_system

CREATE SCHEMA IF NOT EXISTS visit_tracking;
CREATE TABLE IF NOT EXISTS visit_tracking.visits (
    id INTEGER PRIMARY KEY,
    count INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);
INSERT INTO visit_tracking.visits (id, count)
VALUES (1, 0)
ON CONFLICT (id) DO NOTHING;

