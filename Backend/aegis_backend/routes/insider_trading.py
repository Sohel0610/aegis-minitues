# Insider Trading Route Module
# This module handles insider trading functionality including data access and summary generation
# Supports both PostgreSQL (primary) and SQLite (fallback) data sources
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sqlite3
import logging
import asyncio
import concurrent.futures
from collections import defaultdict
import glob
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for insider trading endpoints
router = APIRouter()

try:
    from routes.insider_trading_db import (
        fetch_companies as pg_fetch_companies,
        fetch_batches as pg_fetch_batches,
        fetch_depository_types as pg_fetch_depository_types,
        fetch_summary as pg_fetch_summary,
        fetch_records as pg_fetch_records,
        fetch_record_counts as pg_fetch_record_counts,
        fetch_filter_options as pg_fetch_filter_options,
    )
    PG_AVAILABLE = True
    logger.info("Insider Trading: PostgreSQL handler loaded")
except Exception as e:
    PG_AVAILABLE = False
    logger.warning(f"Insider Trading: PG handler not available ({e}), using SQLite fallback")


# ═══════════════════════════════════════════════════════════════════════
# Response models
# ═══════════════════════════════════════════════════════════════════════

class InsiderTradingSummaryResponse(BaseModel):
    total_companies: int
    total_investors: int
    total_shares: int
    net_investors_change: int
    net_shares_change: int
    added_count: int
    removed_count: int
    changed_count: int
    unchanged_count: int

class CompanyInsiderDataResponse(BaseModel):
    company_name: str
    total_records: int
    added_count: int
    removed_count: int
    changed_count: int
    unchanged_count: int

class InsiderRecordResponse(BaseModel):
    pangir: str
    name: str
    email: str
    position_latest: float
    position_older: float
    position_difference: float
    status: str
    source: str

class EnhancedInsiderTradingDetailsResponse(BaseModel):
    summary: InsiderTradingSummaryResponse
    top_new_investors: List[InsiderRecordResponse]
    top_exits: List[InsiderRecordResponse]
    top_buyers: List[InsiderRecordResponse]
    top_sellers: List[InsiderRecordResponse]

class CompanyListResponse(BaseModel):
    companies: List[str]

class FilterOptionsResponse(BaseModel):
    companies: List[str]
    depositories: List[str]
    batches: List[Dict[str, Any]]

class BatchResponse(BaseModel):
    batches: List[Dict[str, Any]]

class SummaryRow(BaseModel):
    id: Optional[int] = None
    company: str
    batch: str
    depository: str
    added: int
    removed: int
    changed: int
    unchanged: int
    total: int
    empty_pangir_latest: Optional[int] = 0
    empty_pangir_older: Optional[int] = 0

class SummaryListResponse(BaseModel):
    summary: List[SummaryRow]

class RecordRow(BaseModel):
    id: Optional[int] = None
    company: Optional[str] = None
    batch: Optional[str] = None
    depository: Optional[str] = None
    pangir: str
    name: str
    email: str
    position_latest: float
    position_older: float
    position_difference: float
    status: str

class RecordsResponse(BaseModel):
    records: List[RecordRow]
    total: int
    limit: int
    offset: int

class RecordCountsResponse(BaseModel):
    ADDED: int = 0
    REMOVED: int = 0
    CHANGED: int = 0
    UNCHANGED: int = 0
    TOTAL: int = 0


# ═══════════════════════════════════════════════════════════════════════
# SQLite helpers (fallback — kept from original code)
# ═══════════════════════════════════════════════════════════════════════

def get_company_folders():
    """Get all company folders in the AdaniInsiderTraders directory"""
    base_path = os.path.join(os.path.dirname(__file__), "..", "public", "AdaniInsiderTraders")
    if not os.path.exists(base_path):
        return []
    company_folders = []
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and item.startswith("user_"):
            company_folders.append(item)
    return company_folders

def get_company_databases(company_folder):
    """Get all database files for a specific company"""
    base_path = os.path.join(os.path.dirname(__file__), "..", "public", "AdaniInsiderTraders", company_folder)
    if not os.path.exists(base_path):
        return []
    db_files = []
    for file in os.listdir(base_path):
        if file.endswith(".db"):
            db_files.append(file)
    return db_files

def query_database(db_path, query, params=None):
    """Execute a query on a database and return results"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error querying database {db_path}: {str(e)}")
        return []


# ═══════════════════════════════════════════════════════════════════════
# SQLite-based summary (fallback)
# ═══════════════════════════════════════════════════════════════════════

def get_enhanced_insider_trading_summary_data(company_filter: str = None, depository_filter: str = None):
    """Get enhanced summary data for insider trading with KPIs (SQLite fallback)"""
    try:
        base_path = os.path.join(os.path.dirname(__file__), "..", "public", "AdaniInsiderTraders")
        if not os.path.exists(base_path):
            raise HTTPException(status_code=404, detail="Insider trading data not found")

        total_companies = 0
        total_investors = 0
        total_shares = 0
        added_count = 0
        removed_count = 0
        changed_count = 0
        unchanged_count = 0

        company_folders = get_company_folders()
        if company_filter:
            company_folders = [f for f in company_folders if company_filter.lower() in f.lower()]

        for company_folder in company_folders:
            total_companies += 1
            company_path = os.path.join(base_path, company_folder)
            db_files = get_company_databases(company_folder)
            if depository_filter:
                db_files = [db for db in db_files if depository_filter.lower() in db.lower()]

            for db_file in db_files:
                db_path = os.path.join(company_path, db_file)
                if not os.path.exists(db_path):
                    continue
                tables = [t[0] for t in query_database(db_path, "SELECT name FROM sqlite_master WHERE type='table'")]
                if 'Summary' in tables:
                    for status, count in query_database(db_path, "SELECT STATUS, COUNT FROM Summary WHERE STATUS IN ('ADDED','REMOVED','CHANGED','UNCHANGED')"):
                        if status == 'ADDED': added_count += count
                        elif status == 'REMOVED': removed_count += count
                        elif status == 'CHANGED': changed_count += count
                        elif status == 'UNCHANGED': unchanged_count += count
                if 'All_Data' in tables:
                    cols = [c[0] for c in query_database(db_path, "PRAGMA table_info(All_Data)")]
                    if 'POSITION_latest' in cols:
                        r = query_database(db_path, "SELECT COUNT(*), SUM(POSITION_latest) FROM All_Data")
                        if r and r[0][0]:
                            total_investors += r[0][0]
                            total_shares += r[0][1] if r[0][1] else 0
                    else:
                        r = query_database(db_path, "SELECT COUNT(*) FROM All_Data")
                        if r and r[0][0]:
                            total_investors += r[0][0]

        return {
            'total_companies': total_companies,
            'total_investors': total_investors,
            'total_shares': int(total_shares),
            'net_investors_change': added_count - removed_count,
            'net_shares_change': 0,
            'added_count': added_count,
            'removed_count': removed_count,
            'changed_count': changed_count,
            'unchanged_count': unchanged_count,
        }
    except Exception as e:
        logger.error(f"Error fetching insider trading summary (SQLite): {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_enhanced_insider_trading_details_data(company_filter=None, depository_filter=None):
    """Get detailed data (SQLite fallback)"""
    try:
        base_path = os.path.join(os.path.dirname(__file__), "..", "public", "AdaniInsiderTraders")
        if not os.path.exists(base_path):
            raise HTTPException(status_code=404, detail="Insider trading data not found")

        top_new_investors, top_exits, top_buyers, top_sellers = [], [], [], []
        company_folders = get_company_folders()
        if company_filter:
            company_folders = [f for f in company_folders if company_filter.lower() in f.lower()]

        for company_folder in company_folders:
            company_name = company_folder.replace("user_", "").split("_")[0]
            company_path = os.path.join(base_path, company_folder)
            db_files = get_company_databases(company_folder)
            if depository_filter:
                db_files = [db for db in db_files if depository_filter.lower() in db.lower()]

            for db_file in db_files:
                db_path = os.path.join(company_path, db_file)
                if not os.path.exists(db_path):
                    continue
                tables = [t[0] for t in query_database(db_path, "SELECT name FROM sqlite_master WHERE type='table'")]

                def _read_table(table_name, order_col, order_dir, target_list, name_col_key='NAME1_latest', email_col_key='EMAIL1_latest'):
                    if table_name not in tables:
                        return
                    cols = [c[1] for c in query_database(db_path, f"PRAGMA table_info({table_name})")]
                    sel = "PANGIR1"
                    idx = 1
                    name_idx = email_idx = None
                    if name_col_key in cols:
                        sel += f", {name_col_key}"; name_idx = idx; idx += 1
                    if email_col_key in cols:
                        sel += f", {email_col_key}"; email_idx = idx; idx += 1
                    sel += ", POSITION_latest, POSITION_older, POSITION_DIFFERENCE, STATUS"
                    q = f"SELECT {sel} FROM {table_name} WHERE {order_col} IS NOT NULL ORDER BY {order_dir} LIMIT 15"
                    for row in query_database(db_path, q):
                        rec = {'pangir': row[0] or '', 'name': '', 'email': '',
                               'position_latest': 0, 'position_older': 0, 'position_difference': 0,
                               'status': row[-1] or '', 'source': f"{company_name} - {db_file}"}
                        i = 1
                        if name_idx is not None:
                            rec['name'] = (row[name_idx] or '').strip(); i += 1
                        if email_idx is not None:
                            rec['email'] = (row[email_idx] or '').strip(); i += 1
                        rec['position_latest'] = float(row[i]) if row[i] is not None else 0; i += 1
                        rec['position_older'] = float(row[i]) if row[i] is not None else 0; i += 1
                        rec['position_difference'] = float(row[i]) if row[i] is not None else 0
                        target_list.append(rec)

                _read_table('Added', 'POSITION_latest', 'POSITION_latest DESC', top_new_investors)
                _read_table('Removed', 'POSITION_older', 'POSITION_older DESC', top_exits,
                            name_col_key='NAME1_older', email_col_key='EMAIL1_older')
                _read_table('Changed', 'POSITION_DIFFERENCE', 'POSITION_DIFFERENCE DESC', top_buyers)
                _read_table('Changed', 'POSITION_DIFFERENCE', 'POSITION_DIFFERENCE ASC', top_sellers)

        top_new_investors.sort(key=lambda x: x['position_latest'], reverse=True)
        top_exits.sort(key=lambda x: x['position_older'], reverse=True)
        top_buyers = [r for r in top_buyers if r['position_difference'] > 0]
        top_buyers.sort(key=lambda x: x['position_difference'], reverse=True)
        top_sellers = [r for r in top_sellers if r['position_difference'] < 0]
        top_sellers.sort(key=lambda x: x['position_difference'])

        summary_data = get_enhanced_insider_trading_summary_data(company_filter, depository_filter)

        return {
            'summary': summary_data,
            'top_new_investors': top_new_investors[:15],
            'top_exits': top_exits[:15],
            'top_buyers': top_buyers[:15],
            'top_sellers': top_sellers[:15],
        }
    except Exception as e:
        logger.error(f"Error fetching insider trading details (SQLite): {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_filter_options_data():
    """Get filter options from SQLite (fallback)"""
    base_path = os.path.join(os.path.dirname(__file__), "..", "public", "AdaniInsiderTraders")
    company_folders = get_company_folders()
    companies, depositories = [], []
    for folder in company_folders:
        cname = folder.replace("user_", "").split("_")[0]
        if cname not in companies:
            companies.append(cname)
        for db_file in get_company_databases(folder):
            for dep in ["CDSL", "NSDL", "PHY"]:
                if dep in db_file and dep not in depositories:
                    depositories.append(dep)
    return {'companies': companies, 'depositories': depositories, 'batches': []}


# ═══════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

# ── Reference Data ────────────────────────────────────────────────────

@router.get("/api/insider-trading/companies")
async def get_company_list():
    """Get list of all companies"""
    def _fetch():
        if PG_AVAILABLE:
            rows = pg_fetch_companies()
            if rows:
                return {"companies": [r['company_name'] for r in rows]}
        # Fallback
        data = get_filter_options_data()
        return {"companies": data['companies']}

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)


@router.get("/api/insider-trading/batches")
async def get_batches():
    """Get all result batches (newest first)"""
    def _fetch():
        if PG_AVAILABLE:
            return {"batches": pg_fetch_batches()}
        return {"batches": []}

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)


@router.get("/api/insider-trading/filter-options")
async def get_filter_options():
    def _fetch():
        if PG_AVAILABLE:
            data = pg_fetch_filter_options()
            if data.get('companies') or data.get('batches') or data.get('depositories'):
                return data
        return get_filter_options_data()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)


# ── Summary ───────────────────────────────────────────────────────────

@router.get("/api/insider-trading/summary")
async def get_insider_trading_summary(
    company: str = Query(None),
    batch: str = Query(None),
    depository: str = Query(None),
):
    """Get summary data — uses PG if available, SQLite fallback"""
    def _fetch():
        if PG_AVAILABLE:
            rows = pg_fetch_summary(company, batch, depository)
            if rows is not None:
                # Aggregate across all matching rows
                total_added = sum(r.get('added', 0) for r in rows)
                total_removed = sum(r.get('removed', 0) for r in rows)
                total_changed = sum(r.get('changed', 0) for r in rows)
                total_unchanged = sum(r.get('unchanged', 0) for r in rows)
                total_count = sum(r.get('total', 0) for r in rows)
                # Dedupe company names to count unique companies
                unique_companies = set(r.get('company', '') for r in rows)
                return {
                    "total_companies": len(unique_companies),
                    "total_investors": total_count,
                    "total_shares": 0,
                    "net_investors_change": total_added - total_removed,
                    "net_shares_change": 0,
                    "added_count": total_added,
                    "removed_count": total_removed,
                    "changed_count": total_changed,
                    "unchanged_count": total_unchanged,
                }
        # Fallback
        return get_enhanced_insider_trading_summary_data(company, depository)

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)


@router.get("/api/insider-trading/summary/detail")
async def get_insider_trading_summary_detail(
    company: str = Query(None),
    batch: str = Query(None),
    depository: str = Query(None),
):
    """Get per-company summary rows (for Data Source tab)"""
    def _fetch():
        if PG_AVAILABLE:
            rows = pg_fetch_summary(company, batch, depository)
            if rows is not None:
                return {"summary": rows}
        return {"summary": []}

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)


# ── Record Counts ─────────────────────────────────────────────────────

@router.get("/api/insider-trading/counts")
async def get_record_counts(
    company: str = Query(None),
    batch: str = Query(None),
    depository: str = Query(None),
):
    """Get record counts grouped by status"""
    def _fetch():
        if PG_AVAILABLE:
            return pg_fetch_record_counts(company, batch, depository)
        # Fallback: derive from SQLite summary
        s = get_enhanced_insider_trading_summary_data(company, depository)
        return {
            "ADDED": s['added_count'],
            "REMOVED": s['removed_count'],
            "CHANGED": s['changed_count'],
            "UNCHANGED": s['unchanged_count'],
            "TOTAL": s['added_count'] + s['removed_count'] + s['changed_count'] + s['unchanged_count'],
        }

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)


# ── Records ───────────────────────────────────────────────────────────

@router.get("/api/insider-trading/records")
async def get_records(
    status: str = Query(None),
    company: str = Query(None),
    batch: str = Query(None),
    depository: str = Query(None),
    limit: int = Query(15),
    offset: int = Query(0),
    cursor: int = Query(None),
):
    def _fetch():
        if PG_AVAILABLE:
            return pg_fetch_records(status, company, batch, depository, limit, offset, cursor)
        return {"records": [], "total": 0, "limit": limit, "offset": offset, "next_cursor": None}

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)


@router.get("/api/insider-trading/records/added")
async def get_records_added(
    company: str = Query(None), batch: str = Query(None),
    depository: str = Query(None), limit: int = Query(15), offset: int = Query(0),
):
    def _fetch():
        if PG_AVAILABLE:
            return pg_fetch_records("ADDED", company, batch, depository, limit, offset)
        return {"records": [], "total": 0, "limit": limit, "offset": offset}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)


@router.get("/api/insider-trading/records/removed")
async def get_records_removed(
    company: str = Query(None), batch: str = Query(None),
    depository: str = Query(None), limit: int = Query(15), offset: int = Query(0),
):
    def _fetch():
        if PG_AVAILABLE:
            return pg_fetch_records("REMOVED", company, batch, depository, limit, offset)
        return {"records": [], "total": 0, "limit": limit, "offset": offset}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)


@router.get("/api/insider-trading/records/changed")
async def get_records_changed(
    company: str = Query(None), batch: str = Query(None),
    depository: str = Query(None), limit: int = Query(15), offset: int = Query(0),
):
    def _fetch():
        if PG_AVAILABLE:
            return pg_fetch_records("CHANGED", company, batch, depository, limit, offset)
        return {"records": [], "total": 0, "limit": limit, "offset": offset}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)


@router.get("/api/insider-trading/records/unchanged")
async def get_records_unchanged(
    company: str = Query(None), batch: str = Query(None),
    depository: str = Query(None), limit: int = Query(15), offset: int = Query(0),
):
    def _fetch():
        if PG_AVAILABLE:
            return pg_fetch_records("UNCHANGED", company, batch, depository, limit, offset)
        return {"records": [], "total": 0, "limit": limit, "offset": offset}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)


# ── Enhanced Details (backward-compatible) ────────────────────────────

@router.get("/api/insider-trading/enhanced-details")
async def get_enhanced_insider_trading_details(
    company: str = Query(None),
    batch: str = Query(None),
    depository: str = Query(None),
):
    def _fetch():
        if PG_AVAILABLE:
            try:
                counts = pg_fetch_record_counts(company, batch, depository)
                summary = {
                    "total_companies": 1 if company else 0,
                    "total_investors": counts.get('TOTAL', 0),
                    "total_shares": 0,
                    "net_investors_change": counts.get('ADDED', 0) - counts.get('REMOVED', 0),
                    "net_shares_change": 0,
                    "added_count": counts.get('ADDED', 0),
                    "removed_count": counts.get('REMOVED', 0),
                    "changed_count": counts.get('CHANGED', 0),
                    "unchanged_count": counts.get('UNCHANGED', 0),
                }

                def _to_record(r):
                    return {
                        "pangir": r.get('pangir', ''),
                        "name": r.get('name', ''),
                        "email": r.get('email', ''),
                        "position_latest": float(r.get('position_latest', 0)),
                        "position_older": float(r.get('position_older', 0)),
                        "position_difference": float(r.get('position_difference', 0)),
                        "status": r.get('status', ''),
                        "source": f"{r.get('company', '')} - {r.get('depository', '')}",
                    }

                added = pg_fetch_records("ADDED", company, batch, depository, 15, 0)
                removed = pg_fetch_records("REMOVED", company, batch, depository, 15, 0)
                changed_all = pg_fetch_records("CHANGED", company, batch, depository, 30, 0)
                buyers = [r for r in changed_all.get('records', []) if r.get('position_difference', 0) > 0][:15]
                sellers = [r for r in changed_all.get('records', []) if r.get('position_difference', 0) < 0][:15]

                return {
                    "summary": summary,
                    "top_new_investors": [_to_record(r) for r in added.get('records', [])],
                    "top_exits": [_to_record(r) for r in removed.get('records', [])],
                    "top_buyers": [_to_record(r) for r in buyers],
                    "top_sellers": [_to_record(r) for r in sellers],
                }
            except Exception as e:
                logger.error(f"PG enhanced-details failed: {e}")

        return get_enhanced_insider_trading_details_data(company, depository)

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)


@router.get("/api/insider-trading/details")
async def get_insider_trading_details():
    """Alias for enhanced-details with no filters"""
    def _fetch():
        return get_enhanced_insider_trading_details_data()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)
