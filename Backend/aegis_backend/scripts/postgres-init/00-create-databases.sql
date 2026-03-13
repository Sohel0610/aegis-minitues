-- Create local dev databases used by Aegis.
-- Note: This file is executed by the official postgres docker image entrypoint via `psql`.

SELECT 'CREATE DATABASE director_disclosure_system'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'director_disclosure_system')\gexec

SELECT 'CREATE DATABASE aegis_bse_notification'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'aegis_bse_notification')\gexec

-- Common local DB name used in Backend/aegis_backend/.env
SELECT 'CREATE DATABASE aegis_insider'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'aegis_insider')\gexec

-- Alternative DB name used in Backend/aegis_backend/.env.example
SELECT 'CREATE DATABASE aegis_insider_trading'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'aegis_insider_trading')\gexec

-- Optional umbrella DB name used in Backend/aegis_backend/.env.example
SELECT 'CREATE DATABASE aegis_platform'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'aegis_platform')\gexec

-- Optional DB for visit tracking if you prefer isolating it.
SELECT 'CREATE DATABASE visit_tracking_system'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'visit_tracking_system')\gexec

