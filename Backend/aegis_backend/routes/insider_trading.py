# Insider Trading Route Module
# This module handles insider trading functionality including data access and summary generation
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

# Response models for insider trading
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
    position_latest: int
    position_older: int
    position_difference: int
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

# Helper function to get all company folders
def get_company_folders():
    """Get all company folders in the AdaniInsiderTraders directory"""
    base_path = os.path.join(os.path.dirname(__file__), "..", "public", "AdaniInsiderTraders")
    if not os.path.exists(base_path):
        return []
    
    # Get all directories that match the pattern user_*
    company_folders = []
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and item.startswith("user_"):
            company_folders.append(item)
    
    return company_folders

# Helper function to get database files for a company
def get_company_databases(company_folder):
    """Get all database files for a specific company"""
    base_path = os.path.join(os.path.dirname(__file__), "..", "public", "AdaniInsiderTraders", company_folder)
    if not os.path.exists(base_path):
        return []
    
    # Find all .db files
    db_files = []
    for file in os.listdir(base_path):
        if file.endswith(".db"):
            db_files.append(file)
    
    return db_files

# Helper function to query database
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

# Function to get enhanced summary data with KPIs
def get_enhanced_insider_trading_summary_data(company_filter: str = None, depository_filter: str = None):
    """Get enhanced summary data for insider trading with KPIs"""
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
        
        # Get all company folders
        company_folders = get_company_folders()
        
        # Filter by company if specified
        if company_filter:
            company_folders = [folder for folder in company_folders if company_filter.lower() in folder.lower()]
        
        for company_folder in company_folders:
            total_companies += 1
            company_path = os.path.join(base_path, company_folder)
            
            # Get all database files for this company
            db_files = get_company_databases(company_folder)
            
            # Filter by depository if specified
            if depository_filter:
                db_files = [db for db in db_files if depository_filter.lower() in db.lower()]
            
            for db_file in db_files:
                db_path = os.path.join(company_path, db_file)
                if not os.path.exists(db_path):
                    continue
                
                # Check if database has required tables
                tables = [table[0] for table in query_database(db_path, "SELECT name FROM sqlite_master WHERE type='table'")]
                
                # Query Summary table if it exists
                if 'Summary' in tables:
                    summary_results = query_database(
                        db_path, 
                        "SELECT STATUS, COUNT FROM Summary WHERE STATUS IN ('ADDED', 'REMOVED', 'CHANGED', 'UNCHANGED')"
                    )
                    
                    for status, count in summary_results:
                        if status == 'ADDED':
                            added_count += count
                        elif status == 'REMOVED':
                            removed_count += count
                        elif status == 'CHANGED':
                            changed_count += count
                        elif status == 'UNCHANGED':
                            unchanged_count += count
                
                # Query All_Data table for total records and shares if it exists
                if 'All_Data' in tables:
                    # Check if POSITION_latest column exists
                    columns = [col[0] for col in query_database(db_path, "PRAGMA table_info(All_Data)")]
                    if 'POSITION_latest' in columns:
                        all_data_results = query_database(db_path, "SELECT COUNT(*), SUM(POSITION_latest) FROM All_Data")
                        if all_data_results and all_data_results[0][0]:
                            total_investors += all_data_results[0][0]
                            total_shares += all_data_results[0][1] if all_data_results[0][1] else 0
                    else:
                        # Fallback if POSITION_latest doesn't exist
                        all_data_results = query_database(db_path, "SELECT COUNT(*) FROM All_Data")
                        if all_data_results and all_data_results[0][0]:
                            total_investors += all_data_results[0][0]
        
        # Calculate net changes (simplified for this example)
        net_investors_change = added_count - removed_count
        net_shares_change = 0  # Would need previous period data for accurate calculation
        
        return {
            'total_companies': total_companies,
            'total_investors': total_investors,
            'total_shares': int(total_shares),
            'net_investors_change': net_investors_change,
            'net_shares_change': net_shares_change,
            'added_count': added_count,
            'removed_count': removed_count,
            'changed_count': changed_count,
            'unchanged_count': unchanged_count
        }
    except Exception as e:
        logger.error(f"Error fetching insider trading summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch insider trading summary: {str(e)}")

# Function to get detailed data with specific tables
def get_enhanced_insider_trading_details_data(company_filter: str = None, depository_filter: str = None):
    """Get detailed data for insider trading with specific tables"""
    try:
        base_path = os.path.join(os.path.dirname(__file__), "..", "public", "AdaniInsiderTraders")
        if not os.path.exists(base_path):
            raise HTTPException(status_code=404, detail="Insider trading data not found")
        
        # Initialize lists for each category
        top_new_investors = []
        top_exits = []
        top_buyers = []
        top_sellers = []
        
        # Get all company folders
        company_folders = get_company_folders()
        
        # Filter by company if specified
        if company_filter:
            company_folders = [folder for folder in company_folders if company_filter.lower() in folder.lower()]
        
        for company_folder in company_folders:
            company_name = company_folder.replace("user_", "").split("_")[0]  # Extract company name
            company_path = os.path.join(base_path, company_folder)
            
            # Get all database files for this company
            db_files = get_company_databases(company_folder)
            
            # Filter by depository if specified
            if depository_filter:
                db_files = [db for db in db_files if depository_filter.lower() in db.lower()]
            
            for db_file in db_files:
                db_path = os.path.join(company_path, db_file)
                if not os.path.exists(db_path):
                    continue
                
                # Get tables in database
                tables = [table[0] for table in query_database(db_path, "SELECT name FROM sqlite_master WHERE type='table'")]
                
                # Top New Investors (New PANs) - From Added table
                if "Added" in tables:
                    # Check column structure
                    columns = [col[1] for col in query_database(db_path, "PRAGMA table_info(Added)")]
                    
                    # Build query based on available columns
                    if 'NAME1_latest' in columns and 'EMAIL1_latest' in columns:
                        added_query = "SELECT PANGIR1, NAME1_latest, EMAIL1_latest, POSITION_latest, POSITION_older, POSITION_DIFFERENCE, STATUS FROM Added WHERE POSITION_latest IS NOT NULL ORDER BY POSITION_latest DESC LIMIT 20"
                    elif 'EMAIL1_latest' in columns:
                        added_query = "SELECT PANGIR1, EMAIL1_latest, POSITION_latest, POSITION_older, POSITION_DIFFERENCE, STATUS FROM Added WHERE POSITION_latest IS NOT NULL ORDER BY POSITION_latest DESC LIMIT 20"
                    else:
                        added_query = "SELECT PANGIR1, POSITION_latest, POSITION_older, POSITION_DIFFERENCE, STATUS FROM Added WHERE POSITION_latest IS NOT NULL ORDER BY POSITION_latest DESC LIMIT 20"
                    
                    added_results = query_database(db_path, added_query)
                    for result in added_results:
                        record = {
                            'pangir': result[0] if result[0] else '',
                            'name': '',
                            'email': '',
                            'position_latest': 0,
                            'position_older': 0,
                            'position_difference': 0,
                            'status': result[-1] if result[-1] else '',
                            'source': f"{company_name} - {db_file}"
                        }
                        
                        # Map fields based on column structure
                        if 'NAME1_latest' in columns and 'EMAIL1_latest' in columns:
                            record['name'] = result[1].strip() if result[1] else ''
                            record['email'] = result[2].strip() if result[2] else ''
                            record['position_latest'] = int(result[3]) if result[3] is not None else 0
                            record['position_older'] = int(result[4]) if result[4] is not None else 0
                            record['position_difference'] = int(result[5]) if result[5] is not None else 0
                        elif 'EMAIL1_latest' in columns:
                            record['email'] = result[1].strip() if result[1] else ''
                            record['position_latest'] = int(result[2]) if result[2] is not None else 0
                            record['position_older'] = int(result[3]) if result[3] is not None else 0
                            record['position_difference'] = int(result[4]) if result[4] is not None else 0
                        else:
                            record['position_latest'] = int(result[1]) if result[1] is not None else 0
                            record['position_older'] = int(result[2]) if result[2] is not None else 0
                            record['position_difference'] = int(result[3]) if result[3] is not None else 0
                        
                        top_new_investors.append(record)
                
                # Top Exits (Fully Removed Investors) - From Removed table
                if "Removed" in tables:
                    # Check column structure
                    columns = [col[1] for col in query_database(db_path, "PRAGMA table_info(Removed)")]
                    
                    # Build query based on available columns
                    if 'NAME1_older' in columns and 'EMAIL1_older' in columns:
                        removed_query = "SELECT PANGIR1, NAME1_older, EMAIL1_older, POSITION_latest, POSITION_older, POSITION_DIFFERENCE, STATUS FROM Removed WHERE POSITION_older IS NOT NULL ORDER BY POSITION_older DESC LIMIT 20"
                    elif 'EMAIL1_older' in columns:
                        removed_query = "SELECT PANGIR1, EMAIL1_older, POSITION_latest, POSITION_older, POSITION_DIFFERENCE, STATUS FROM Removed WHERE POSITION_older IS NOT NULL ORDER BY POSITION_older DESC LIMIT 20"
                    else:
                        removed_query = "SELECT PANGIR1, POSITION_latest, POSITION_older, POSITION_DIFFERENCE, STATUS FROM Removed WHERE POSITION_older IS NOT NULL ORDER BY POSITION_older DESC LIMIT 20"
                    
                    removed_results = query_database(db_path, removed_query)
                    for result in removed_results:
                        record = {
                            'pangir': result[0] if result[0] else '',
                            'name': '',
                            'email': '',
                            'position_latest': 0,
                            'position_older': 0,
                            'position_difference': 0,
                            'status': result[-1] if result[-1] else '',
                            'source': f"{company_name} - {db_file}"
                        }
                        
                        # Map fields based on column structure
                        if 'NAME1_older' in columns and 'EMAIL1_older' in columns:
                            record['name'] = result[1].strip() if result[1] else ''
                            record['email'] = result[2].strip() if result[2] else ''
                            record['position_latest'] = int(result[3]) if result[3] is not None else 0
                            record['position_older'] = int(result[4]) if result[4] is not None else 0
                            record['position_difference'] = int(result[5]) if result[5] is not None else 0
                        elif 'EMAIL1_older' in columns:
                            record['email'] = result[1].strip() if result[1] else ''
                            record['position_latest'] = int(result[2]) if result[2] is not None else 0
                            record['position_older'] = int(result[3]) if result[3] is not None else 0
                            record['position_difference'] = int(result[4]) if result[4] is not None else 0
                        else:
                            record['position_latest'] = int(result[1]) if result[1] is not None else 0
                            record['position_older'] = int(result[2]) if result[2] is not None else 0
                            record['position_difference'] = int(result[3]) if result[3] is not None else 0
                        
                        top_exits.append(record)
                
                # Top Buyers (Biggest Increasers) - From Changed table where POSITION_DIFFERENCE > 0
                if "Changed" in tables:
                    # Check column structure
                    columns = [col[1] for col in query_database(db_path, "PRAGMA table_info(Changed)")]
                    
                    # Build query based on available columns
                    if 'NAME1_latest' in columns and 'EMAIL1_latest' in columns:
                        buyers_query = "SELECT PANGIR1, NAME1_latest, EMAIL1_latest, POSITION_latest, POSITION_older, POSITION_DIFFERENCE, STATUS FROM Changed WHERE POSITION_DIFFERENCE > 0 ORDER BY POSITION_DIFFERENCE DESC LIMIT 20"
                    elif 'EMAIL1_latest' in columns:
                        buyers_query = "SELECT PANGIR1, EMAIL1_latest, POSITION_latest, POSITION_older, POSITION_DIFFERENCE, STATUS FROM Changed WHERE POSITION_DIFFERENCE > 0 ORDER BY POSITION_DIFFERENCE DESC LIMIT 20"
                    else:
                        buyers_query = "SELECT PANGIR1, POSITION_latest, POSITION_older, POSITION_DIFFERENCE, STATUS FROM Changed WHERE POSITION_DIFFERENCE > 0 ORDER BY POSITION_DIFFERENCE DESC LIMIT 20"
                    
                    buyers_results = query_database(db_path, buyers_query)
                    for result in buyers_results:
                        record = {
                            'pangir': result[0] if result[0] else '',
                            'name': '',
                            'email': '',
                            'position_latest': 0,
                            'position_older': 0,
                            'position_difference': 0,
                            'status': result[-1] if result[-1] else '',
                            'source': f"{company_name} - {db_file}"
                        }
                        
                        # Map fields based on column structure
                        if 'NAME1_latest' in columns and 'EMAIL1_latest' in columns:
                            record['name'] = result[1].strip() if result[1] else ''
                            record['email'] = result[2].strip() if result[2] else ''
                            record['position_latest'] = int(result[3]) if result[3] is not None else 0
                            record['position_older'] = int(result[4]) if result[4] is not None else 0
                            record['position_difference'] = int(result[5]) if result[5] is not None else 0
                        elif 'EMAIL1_latest' in columns:
                            record['email'] = result[1].strip() if result[1] else ''
                            record['position_latest'] = int(result[2]) if result[2] is not None else 0
                            record['position_older'] = int(result[3]) if result[3] is not None else 0
                            record['position_difference'] = int(result[4]) if result[4] is not None else 0
                        else:
                            record['position_latest'] = int(result[1]) if result[1] is not None else 0
                            record['position_older'] = int(result[2]) if result[2] is not None else 0
                            record['position_difference'] = int(result[3]) if result[3] is not None else 0
                        
                        # Only add if it's a buyer (positive difference)
                        if record['position_difference'] > 0:
                            top_buyers.append(record)
                
                # Top Sellers (Biggest Decreasers) - From Changed table where POSITION_DIFFERENCE < 0
                if "Changed" in tables:
                    # Check column structure
                    columns = [col[1] for col in query_database(db_path, "PRAGMA table_info(Changed)")]
                    
                    # Build query based on available columns
                    if 'NAME1_latest' in columns and 'EMAIL1_latest' in columns:
                        sellers_query = "SELECT PANGIR1, NAME1_latest, EMAIL1_latest, POSITION_latest, POSITION_older, POSITION_DIFFERENCE, STATUS FROM Changed WHERE POSITION_DIFFERENCE < 0 ORDER BY ABS(POSITION_DIFFERENCE) DESC LIMIT 20"
                    elif 'EMAIL1_latest' in columns:
                        sellers_query = "SELECT PANGIR1, EMAIL1_latest, POSITION_latest, POSITION_older, POSITION_DIFFERENCE, STATUS FROM Changed WHERE POSITION_DIFFERENCE < 0 ORDER BY ABS(POSITION_DIFFERENCE) DESC LIMIT 20"
                    else:
                        sellers_query = "SELECT PANGIR1, POSITION_latest, POSITION_older, POSITION_DIFFERENCE, STATUS FROM Changed WHERE POSITION_DIFFERENCE < 0 ORDER BY ABS(POSITION_DIFFERENCE) DESC LIMIT 20"
                    
                    sellers_results = query_database(db_path, sellers_query)
                    for result in sellers_results:
                        record = {
                            'pangir': result[0] if result[0] else '',
                            'name': '',
                            'email': '',
                            'position_latest': 0,
                            'position_older': 0,
                            'position_difference': 0,
                            'status': result[-1] if result[-1] else '',
                            'source': f"{company_name} - {db_file}"
                        }
                        
                        # Map fields based on column structure
                        if 'NAME1_latest' in columns and 'EMAIL1_latest' in columns:
                            record['name'] = result[1].strip() if result[1] else ''
                            record['email'] = result[2].strip() if result[2] else ''
                            record['position_latest'] = int(result[3]) if result[3] is not None else 0
                            record['position_older'] = int(result[4]) if result[4] is not None else 0
                            record['position_difference'] = int(result[5]) if result[5] is not None else 0
                        elif 'EMAIL1_latest' in columns:
                            record['email'] = result[1].strip() if result[1] else ''
                            record['position_latest'] = int(result[2]) if result[2] is not None else 0
                            record['position_older'] = int(result[3]) if result[3] is not None else 0
                            record['position_difference'] = int(result[4]) if result[4] is not None else 0
                        else:
                            record['position_latest'] = int(result[1]) if result[1] is not None else 0
                            record['position_older'] = int(result[2]) if result[2] is not None else 0
                            record['position_difference'] = int(result[3]) if result[3] is not None else 0
                        
                        # Only add if it's a seller (negative difference)
                        if record['position_difference'] < 0:
                            top_sellers.append(record)
        
        # Sort and limit results
        top_new_investors.sort(key=lambda x: x['position_latest'], reverse=True)
        top_exits.sort(key=lambda x: x['position_older'], reverse=True)
        top_buyers.sort(key=lambda x: x['position_difference'], reverse=True)
        top_sellers.sort(key=lambda x: x['position_difference'])  # Ascending to show largest negative values first
        
        # Get summary data
        summary_data = get_enhanced_insider_trading_summary_data(company_filter, depository_filter)
        
        return {
            'summary': summary_data,
            'top_new_investors': top_new_investors[:20],
            'top_exits': top_exits[:20],
            'top_buyers': top_buyers[:20],
            'top_sellers': top_sellers[:20]
        }
    except Exception as e:
        logger.error(f"Error fetching insider trading details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch insider trading details: {str(e)}")

# Function to get list of companies and depositories
def get_filter_options_data():
    """Get filter options (companies and depositories)"""
    try:
        base_path = os.path.join(os.path.dirname(__file__), "..", "public", "AdaniInsiderTraders")
        company_folders = get_company_folders()
        companies = []
        depositories = []
        
        for folder in company_folders:
            # Extract company name from folder name
            company_name = folder.replace("user_", "").split("_")[0]
            if company_name not in companies:
                companies.append(company_name)
            
            # Get database files to extract depositories
            db_files = get_company_databases(folder)
            for db_file in db_files:
                # Extract depository from filename (e.g., BENPOS-CDSL_xxx.db -> CDSL)
                if "CDSL" in db_file:
                    if "CDSL" not in depositories:
                        depositories.append("CDSL")
                elif "NSDL" in db_file:
                    if "NSDL" not in depositories:
                        depositories.append("NSDL")
                elif "PHY" in db_file:
                    if "PHY" not in depositories:
                        depositories.append("PHY")
        
        return {'companies': companies, 'depositories': depositories}
    except Exception as e:
        logger.error(f"Error fetching filter options: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch filter options: {str(e)}")

# Endpoint to get enhanced insider trading details with KPIs
@router.get("/api/insider-trading/enhanced-details", response_model=EnhancedInsiderTradingDetailsResponse)
async def get_enhanced_insider_trading_details(
    company: str = Query(None, description="Filter by company name"),
    depository: str = Query(None, description="Filter by depository (CDSL, NSDL, PHY)")
):
    """Get enhanced insider trading details with KPIs and specific tables"""
    try:
        loop = asyncio.get_event_loop()
        details_data = await loop.run_in_executor(thread_pool, get_enhanced_insider_trading_details_data, company, depository)
        return EnhancedInsiderTradingDetailsResponse(**details_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_enhanced_insider_trading_details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch insider trading details: {str(e)}")

# Endpoint to get filter options
@router.get("/api/insider-trading/filter-options", response_model=FilterOptionsResponse)
async def get_filter_options():
    """Get available filter options (companies and depositories)"""
    try:
        loop = asyncio.get_event_loop()
        filter_data = await loop.run_in_executor(thread_pool, get_filter_options_data)
        return FilterOptionsResponse(**filter_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_filter_options: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch filter options: {str(e)}")

# Endpoint to get insider trading summary
@router.get("/api/insider-trading/summary", response_model=InsiderTradingSummaryResponse)
async def get_insider_trading_summary():
    """Get summary of insider trading data across all companies"""
    try:
        loop = asyncio.get_event_loop()
        summary_data = await loop.run_in_executor(thread_pool, get_enhanced_insider_trading_summary_data)
        return InsiderTradingSummaryResponse(**summary_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_insider_trading_summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch insider trading summary: {str(e)}")

# Endpoint to get insider trading details
@router.get("/api/insider-trading/details", response_model=EnhancedInsiderTradingDetailsResponse)
async def get_insider_trading_details():
    """Get detailed insider trading data across all companies"""
    try:
        loop = asyncio.get_event_loop()
        details_data = await loop.run_in_executor(thread_pool, get_enhanced_insider_trading_details_data)
        return EnhancedInsiderTradingDetailsResponse(**details_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_insider_trading_details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch insider trading details: {str(e)}")

# Endpoint to get list of companies
@router.get("/api/insider-trading/companies", response_model=CompanyListResponse)
async def get_company_list():
    """Get list of all companies with insider trading data"""
    try:
        loop = asyncio.get_event_loop()
        filter_data = await loop.run_in_executor(thread_pool, get_filter_options_data)
        return CompanyListResponse(companies=filter_data['companies'])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_company_list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch company list: {str(e)}")
