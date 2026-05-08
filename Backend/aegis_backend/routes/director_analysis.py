from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import concurrent.futures
import logging
from routes.director_data_analysis import (
    get_all_directors,
    get_company_count,
    get_cross_directorship,
    get_clustering,
    get_network,
    get_wtd_count,
    get_all_companies_with_director_count
)

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for director analysis endpoints
router = APIRouter()

# Response models
class DirectorResponse(BaseModel):
    din: str
    name: str
    source_file: Optional[str] = None

class CompanyCountResponse(BaseModel):
    total: int
    public: int
    private: int

class CrossDirectorshipResponse(BaseModel):
    name: str
    company_count: int

class ClusteringResponse(BaseModel):
    director1: str
    director2: str
    sharedCompanies: int

class NetworkNode(BaseModel):
    id: str
    type: str
    label: str

class NetworkLink(BaseModel):
    source: str
    target: str

class NetworkResponse(BaseModel):
    nodes: List[NetworkNode]
    links: List[NetworkLink]

class WTDCountResponse(BaseModel):
    name: str
    positions: int

class CompanyWithDirectorCountResponse(BaseModel):
    name: str
    cin: Optional[str] = "N/A"
    type: Optional[str] = "Unknown"
    director_count: int

# Endpoint to get all directors
@router.get("/directors", response_model=List[DirectorResponse])
async def get_directors():
    """Get all directors from the database"""
    try:
        def fetch_directors():
            return get_all_directors()
        
        loop = asyncio.get_event_loop()
        directors = await loop.run_in_executor(thread_pool, fetch_directors)
        
        return [DirectorResponse(**director) for director in directors]
    except Exception as e:
        logger.error(f"Error fetching directors: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch directors: {str(e)}")

# Endpoint to get company count statistics
@router.get("/company-count", response_model=CompanyCountResponse)
async def get_company_count_endpoint():
    """Get company count statistics"""
    try:
        def fetch_company_count():
            return get_company_count()
        
        loop = asyncio.get_event_loop()
        company_count = await loop.run_in_executor(thread_pool, fetch_company_count)
        
        return CompanyCountResponse(**company_count)
    except Exception as e:
        logger.error(f"Error fetching company count: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch company count: {str(e)}")

# Endpoint to get cross-directorship information
@router.get("/cross-directorship", response_model=List[CrossDirectorshipResponse])
async def get_cross_directorship_endpoint():
    """Get cross-directorship information"""
    try:
        def fetch_cross_directorship():
            return get_cross_directorship()
        
        loop = asyncio.get_event_loop()
        cross_directorship = await loop.run_in_executor(thread_pool, fetch_cross_directorship)
        
        return [CrossDirectorshipResponse(**item) for item in cross_directorship]
    except Exception as e:
        logger.error(f"Error fetching cross directorship: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch cross directorship: {str(e)}")

# Endpoint to get clustering information
@router.get("/clustering", response_model=List[ClusteringResponse])
async def get_clustering_endpoint():
    """Get director clustering information"""
    try:
        def fetch_clustering():
            return get_clustering()
        
        loop = asyncio.get_event_loop()
        clustering = await loop.run_in_executor(thread_pool, fetch_clustering)
        
        return [ClusteringResponse(**item) for item in clustering]
    except Exception as e:
        logger.error(f"Error fetching clustering: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch clustering: {str(e)}")

# Endpoint to get network data for visualization
@router.get("/network", response_model=NetworkResponse)
async def get_network_endpoint():
    """Get network data for visualization"""
    try:
        def fetch_network():
            return get_network()
        
        loop = asyncio.get_event_loop()
        network = await loop.run_in_executor(thread_pool, fetch_network)
        
        # Convert to proper response models
        nodes = [NetworkNode(**node) for node in network["nodes"]]
        links = [NetworkLink(**link) for link in network["links"]]
        
        return NetworkResponse(nodes=nodes, links=links)
    except Exception as e:
        logger.error(f"Error fetching network: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch network: {str(e)}")

# Endpoint to get whole-time director count
@router.get("/wtd-count", response_model=List[WTDCountResponse])
async def get_wtd_count_endpoint():
    """Get whole-time director count"""
    try:
        def fetch_wtd_count():
            return get_wtd_count()
        
        loop = asyncio.get_event_loop()
        wtd_count = await loop.run_in_executor(thread_pool, fetch_wtd_count)
        
        return [WTDCountResponse(**item) for item in wtd_count]
    except Exception as e:
        logger.error(f"Error fetching WTD count: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch WTD count: {str(e)}")

# Endpoint to get all companies with director count (already exists in directors.py but adding here for completeness)
@router.get("/companies-with-director-count", response_model=List[CompanyWithDirectorCountResponse])
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