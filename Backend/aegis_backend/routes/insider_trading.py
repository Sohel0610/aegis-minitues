# Insider Trading Route Module
# This module handles insider trading functionality using PostgreSQL
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import asyncio
import concurrent.futures
from routes.insider_trading_db import (
    fetch_companies as pg_fetch_companies,
    fetch_batches as pg_fetch_batches,
    fetch_depository_types as pg_fetch_depository_types,
    fetch_summary as pg_fetch_summary,
    fetch_records as pg_fetch_records,
    fetch_record_counts as pg_fetch_record_counts,
    fetch_filter_options as pg_fetch_filter_options,
)

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=8)

# Create a router instance for insider trading endpoints
router = APIRouter()

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

# ═══════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/insider-trading/companies")
async def get_company_list():
    """Get list of all companies"""
    def _fetch():
        rows = pg_fetch_companies()
        return {"companies": [r['company_name'] for r in rows]}
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)

@router.get("/insider-trading/batches")
async def get_batches():
    """Get all result batches (newest first)"""
    def _fetch():
        return {"batches": pg_fetch_batches()}
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)

@router.get("/insider-trading/filter-options")
async def get_filter_options():
    def _fetch():
        return pg_fetch_filter_options()
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)

@router.get("/insider-trading/summary")
async def get_insider_trading_summary(
    company: str = Query(None),
    batch: str = Query(None),
    depository: str = Query(None),
):
    """Get summary data using PostgreSQL"""
    def _fetch():
        rows = pg_fetch_summary(company, batch, depository)
        if not rows:
            return {
                "total_companies": 0, "total_investors": 0, "total_shares": 0,
                "net_investors_change": 0, "net_shares_change": 0,
                "added_count": 0, "removed_count": 0, "changed_count": 0, "unchanged_count": 0
            }
        
        total_added = sum(r.get('added', 0) for r in rows)
        total_removed = sum(r.get('removed', 0) for r in rows)
        total_changed = sum(r.get('changed', 0) for r in rows)
        total_unchanged = sum(r.get('unchanged', 0) for r in rows)
        total_count = sum(r.get('total', 0) for r in rows)
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

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)

@router.get("/insider-trading/summary/detail")
async def get_insider_trading_summary_detail(
    company: str = Query(None),
    batch: str = Query(None),
    depository: str = Query(None),
):
    """Get per-company summary rows (for Data Source tab)"""
    def _fetch():
        return {"summary": pg_fetch_summary(company, batch, depository)}
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)

@router.get("/insider-trading/counts")
async def get_record_counts(
    company: str = Query(None),
    batch: str = Query(None),
    depository: str = Query(None),
    adani_only: bool = Query(False),
):
    """Get record counts grouped by status"""
    def _fetch():
        return pg_fetch_record_counts(company, batch, depository, adani_only)
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)

@router.get("/insider-trading/records")
async def get_records(
    status: str = Query(None),
    company: str = Query(None),
    batch: str = Query(None),
    depository: str = Query(None),
    search: str = Query(None),
    limit: int = Query(15),
    offset: int = Query(0),
    cursor: int = Query(None),
    adani_only: bool = Query(False),
):
    def _fetch():
        return pg_fetch_records(status, company, batch, depository, search, limit, offset, cursor, adani_only)
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)

@router.get("/insider-trading/enhanced-details")
async def get_enhanced_insider_trading_details(
    company: str = Query(None),
    batch: str = Query(None),
    depository: str = Query(None),
):
    """Production-ready enhanced details using PostgreSQL only"""
    def _fetch():
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

            added = pg_fetch_records("ADDED", company, batch, depository, None, 15, 0)
            removed = pg_fetch_records("REMOVED", company, batch, depository, None, 15, 0)
            changed_all = pg_fetch_records("CHANGED", company, batch, depository, None, 30, 0)
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
            logger.error(f"Enhanced details failed: {e}")
            raise HTTPException(status_code=500, detail="Database error")

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, _fetch)

@router.get("/insider-trading/details")
async def get_insider_trading_details():
    """Alias for enhanced-details with no filters"""
    return await get_enhanced_insider_trading_details()
