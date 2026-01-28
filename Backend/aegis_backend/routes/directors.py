from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import asyncio
import concurrent.futures
import logging
from routes.director_data_analysis import get_all_companies_with_director_count

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for directors endpoints
router = APIRouter()

# Response model for company with director count
class CompanyWithDirectorCountResponse(BaseModel):
    name: str
    type: str
    director_count: int

@router.get("/api/companies-with-director-count", response_model=List[CompanyWithDirectorCountResponse])
async def get_companies_with_director_count():
    """Get all companies with their director counts and types"""
    try:
        def fetch_companies_with_director_count():
            return get_all_companies_with_director_count()
        
        loop = asyncio.get_event_loop()
        companies = await loop.run_in_executor(thread_pool, fetch_companies_with_director_count)
        
        return [CompanyWithDirectorCountResponse(**company) for company in companies]
    except Exception as e:
        logger.error(f"Error fetching companies with director count: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch companies with director count: {str(e)}")