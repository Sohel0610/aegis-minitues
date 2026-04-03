"""
API endpoints for interactive chart features
"""
from fastapi import APIRouter, Query
from typing import List, Optional
import sys
import os

# Add project root to path so we can import chatbot_backend
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from chatbot_backend.services.analytics_service import compare_companies_notifications
from chatbot_backend.data_layer.models import get_db_session, DailyLog
from sqlalchemy import func

router = APIRouter(prefix="/api", tags=["interactive"])


@router.get("/companies")
async def get_companies(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2030)
):
    """Get list of all companies with notifications for a given period"""
    session = get_db_session()
    try:
        query = session.query(DailyLog.EntityName).distinct()
        
        # Filter out NIL entries
        query = query.filter(
            ~((DailyLog.Link == "NIL") & 
              (DailyLog.Nature == "NIL") & 
              (DailyLog.Summary == "NIL"))
        )
        
        # Filter by month/year if provided
        if month:
            query = query.filter(func.strftime("%m", DailyLog.Date) == f"{month:02d}")
        if year:
            query = query.filter(func.strftime("%Y", DailyLog.Date) == str(year))
        
        query = query.filter(DailyLog.EntityName.isnot(None))
        query = query.order_by(DailyLog.EntityName)
        
        results = query.all()
        companies = [r.EntityName for r in results]
        
        return {"companies": companies, "count": len(companies)}
    finally:
        session.close()


@router.get("/compare")
async def compare_companies(
    companies: str = Query(..., description="Comma-separated company names"),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2030)
):
    """Compare notification counts for multiple companies"""
    company_list = [c.strip() for c in companies.split(",") if c.strip()]
    
    if not company_list:
        return {"error": "No companies provided"}, 400
    
    labels, values = compare_companies_notifications(company_list, month=month, year=year)
    
    return {
        "labels": labels,
        "values": values,
        "count": len(labels)
    }
