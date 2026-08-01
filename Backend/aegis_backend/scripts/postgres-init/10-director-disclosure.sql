-- Initialize the Director Disclosure Postgres database used by routes/directors_disclosure.py
-- and routes/director_data_analysis.py.

\connect director_disclosure_system

CREATE SCHEMA IF NOT EXISTS directors_master;
CREATE SCHEMA IF NOT EXISTS directors_data;
CREATE SCHEMA IF NOT EXISTS directors_profile;
CREATE SCHEMA IF NOT EXISTS family_information;

-- Primary list used by /api/directors-master
CREATE TABLE IF NOT EXISTS directors_master.directors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    din TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_directors_master_din ON directors_master.directors(din);

-- Analytics source used by director_analysis endpoints
CREATE TABLE IF NOT EXISTS directors_data.directors (
    din TEXT PRIMARY KEY,
    name TEXT,
    source_file TEXT
);

CREATE TABLE IF NOT EXISTS directors_data.companies (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE,
    type TEXT
);

CREATE TABLE IF NOT EXISTS directors_data.directorships (
    id SERIAL PRIMARY KEY,
    din TEXT REFERENCES directors_data.directors(din) ON DELETE CASCADE,
    company_id INTEGER REFERENCES directors_data.companies(id) ON DELETE CASCADE,
    position TEXT,
    appointment_date TEXT
);
CREATE INDEX IF NOT EXISTS idx_directorships_din ON directors_data.directorships(din);
CREATE INDEX IF NOT EXISTS idx_directorships_company_id ON directors_data.directorships(company_id);

-- Used by llm_utils.py summary storage (UPSERT relies on file_path being unique)
CREATE TABLE IF NOT EXISTS directors_data.document_summaries (
    id SERIAL PRIMARY KEY,
    director_name TEXT NOT NULL,
    din TEXT,
    file_path TEXT NOT NULL UNIQUE,
    full_text TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_document_summaries_file_path ON directors_data.document_summaries(file_path);
CREATE INDEX IF NOT EXISTS idx_document_summaries_director_name ON directors_data.document_summaries(director_name);
CREATE INDEX IF NOT EXISTS idx_document_summaries_din ON directors_data.document_summaries(din);

-- Profile data used by /api/directors-profile and PAN endpoints
CREATE TABLE IF NOT EXISTS directors_profile.directors_profile (
    id SERIAL PRIMARY KEY,
    din TEXT UNIQUE,
    pan TEXT,
    name_of_director TEXT,
    address TEXT,
    date_of_birth DATE,
    qualification TEXT,
    experience TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_directors_profile_din ON directors_profile.directors_profile(din);
CREATE INDEX IF NOT EXISTS idx_directors_profile_pan ON directors_profile.directors_profile(pan);

-- Family info used by /api/directors/{director_name}/family-info
CREATE TABLE IF NOT EXISTS family_information.director_family (
    id SERIAL PRIMARY KEY,
    director_name TEXT NOT NULL,
    section_2_77_i TEXT,
    section_2_77_ii TEXT,
    section_2_77_iii TEXT,
    father TEXT,
    mother TEXT,
    son TEXT,
    sons_wife TEXT,
    daughter TEXT,
    daughters_husband TEXT,
    brother TEXT,
    sister TEXT,
    father_pan TEXT,
    mother_pan TEXT,
    father_pan_file TEXT,
    mother_pan_file TEXT,
    is_submitted INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_director_family_name ON family_information.director_family(director_name);

