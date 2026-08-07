-- AEGIS Insider Trading - Index Optimization Migration
-- Run this against the aegis_insider_trading database

-- 1. Composite index for the most common filter combination (batch + company + depository + status)
CREATE INDEX IF NOT EXISTS idx_records_batch_company_depository_status
ON shareholder_records(batch_id, company_id, depository_id, status);

-- 2. Composite index for batch + company (the two most frequent filters)
CREATE INDEX IF NOT EXISTS idx_records_batch_company
ON shareholder_records(batch_id, company_id);

-- 3. Index on status for status-only filtering
CREATE INDEX IF NOT EXISTS idx_records_status
ON shareholder_records(status);

-- 4. Index for cursor-based pagination (id is PK but explicit index helps planner)
CREATE INDEX IF NOT EXISTS idx_records_pagination
ON shareholder_records(id);

-- 5. Covering index for the summary table lookups
CREATE INDEX IF NOT EXISTS idx_summary_batch_company_depository
ON summary(batch_id, company_id, depository_id);

-- 6. FK indexes on lookup tables (usually auto-created but ensure they exist)
CREATE INDEX IF NOT EXISTS idx_records_company_id ON shareholder_records(company_id);
CREATE INDEX IF NOT EXISTS idx_records_batch_id ON shareholder_records(batch_id);
CREATE INDEX IF NOT EXISTS idx_records_depository_id ON shareholder_records(depository_id);
CREATE INDEX IF NOT EXISTS idx_summary_company_id ON summary(company_id);
CREATE INDEX IF NOT EXISTS idx_summary_batch_id ON summary(batch_id);
CREATE INDEX IF NOT EXISTS idx_summary_depository_id ON summary(depository_id);

-- 7. Analyze tables so PostgreSQL planner uses fresh statistics
ANALYZE companies;
ANALYZE result_batches;
ANALYZE depository_types;
ANALYZE summary;
ANALYZE shareholder_records;
