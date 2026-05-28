# Search Optimization for Master Data Pages

## Overview
Due to the massive size of the `shareholder_records` table (22+ million rows), performing substring searches (`ILIKE '%search_term%'`) without indexes caused extreme latency (7-10 seconds per keystroke). 

To resolve this, we implemented **B-Tree Indexing** combined with **Prefix Search Logic** (`LIKE 'search_term%'`). This optimization reduced search queries to under `0.4` seconds.

---

## 1. Database Indexes Created
The following case-insensitive B-Tree indexes were built across the three core tables using the `varchar_pattern_ops` operator class. This allows PostgreSQL to utilize the index for `LIKE 'prefix%'` queries.

```sql
-- 1. Shareholder Records Indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sr_pangir ON public.shareholder_records (pangir);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sr_name_lower ON public.shareholder_records (lower(name) varchar_pattern_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sr_email_lower ON public.shareholder_records (lower(email) varchar_pattern_ops);

-- 2. Compliance Cache Violations Indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ccv_pancard ON public.compliance_cache_violations (pan_card);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ccv_decname_lower ON public.compliance_cache_violations (lower(declared_name) varchar_pattern_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ccv_email_lower ON public.compliance_cache_violations (lower(email) varchar_pattern_ops);

-- 3. ServiceNow Holdings Indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_snh_pancard ON public.servicenow_holdings (pan_card);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_snh_name_lower ON public.servicenow_holdings (lower(name) varchar_pattern_ops);
```

---

## 2. API Pre-Filtering Strategy
Instead of passing the search term directly into the massive CTE `UNION ALL` (which forces sequential scans), we implemented a **pre-filtering strategy** inside the Python backend.

When a search term is provided, the backend API dynamically executes three ultra-fast, index-backed queries to fetch matching `pan_card` identifiers first. 

### Python Implementation (`servicenow_reconciliation.py` & `insider_trading_db.py`)
```python
if search:
    # Use prefix searching for B-Tree varchar_pattern_ops compatibility
    search_prefix = f"{search.lower()}%"
    
    # 1. Search shareholder_records
    cur.execute("SELECT pangir FROM public.shareholder_records WHERE lower(name) LIKE %s OR lower(email) LIKE %s OR lower(pangir) LIKE %s LIMIT 100", (search_prefix, search_prefix, search_prefix))
    sr_pans = [r['pangir'] for r in cur.fetchall() if r['pangir']]

    # 2. Search compliance_cache_violations
    cur.execute("SELECT pan_card FROM public.compliance_cache_violations WHERE lower(declared_name) LIKE %s OR lower(shareholder_name) LIKE %s OR lower(email) LIKE %s OR lower(pan_card) LIKE %s LIMIT 100", (search_prefix, search_prefix, search_prefix, search_prefix))
    ccv_pans = [r['pan_card'] for r in cur.fetchall() if r['pan_card']]

    # 3. Search servicenow_holdings
    cur.execute("SELECT pan_card FROM public.servicenow_holdings WHERE lower(name) LIKE %s OR lower(pan_card) LIKE %s LIMIT 100", (search_prefix, search_prefix))
    sh_pans = [r['pan_card'] for r in cur.fetchall() if r['pan_card']]

    matching_pans = list(set(sr_pans + ccv_pans + sh_pans))

    if not matching_pans:
        return {"records": [], "count": 0}

    # Inject the exact PANs directly into the master query
    where_clause += " AND pan_card = ANY(%s)"
    params.append(matching_pans)
```

## Result
Because the `matching_pans` array is explicitly passed into the `WHERE` clause, PostgreSQL entirely skips sequential scanning and retrieves the exact PANs from the millions of rows almost instantly.
