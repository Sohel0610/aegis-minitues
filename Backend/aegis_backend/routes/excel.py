# Excel Data Route Module
# This module handles Excel file data processing and retrieval operations
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import pandas as pd
import json
import logging
import asyncio
import concurrent.futures
from functools import partial
import uuid
from datetime import datetime
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Create a router instance for Excel data endpoints
router = APIRouter()

# Response model for Excel data
class ExcelDataResponse(BaseModel):
    data: List[Dict[str, Any]]
    columns: List[str]
    count: int

# Helper function to read Excel sheets asynchronously
async def read_excel_sheet(file_path: str, sheet_name: str):
    """Read a specific sheet from an Excel file asynchronously using thread pool"""
    loop = asyncio.get_event_loop()
    func = partial(pd.read_excel, file_path, sheet_name=sheet_name)
    return await loop.run_in_executor(thread_pool, func)

# Endpoint to get data from an Excel file
@router.get("/excel-data/{file_name}", response_model=ExcelDataResponse)
async def get_excel_data(file_name: str, sheet_name: str = "Sheet1"):
    """Get data from an Excel file"""
    try:
        # Define the path to the Excel file in the public folder
        excel_folder = os.path.join(os.path.dirname(__file__), "..", "public", "excel")
        file_path = os.path.join(excel_folder, file_name)
        
        # Check if file exists in excel subdirectory
        if not os.path.exists(file_path):
            # Try with different case in excel subdirectory
            if file_name.lower() != file_name:
                file_path = os.path.join(excel_folder, file_name.lower())
            else:
                file_path = os.path.join(excel_folder, file_name.upper())
                
            # If still not found, check in the main public directory
            if not os.path.exists(file_path):
                # Check in main public directory
                public_folder = os.path.join(os.path.dirname(__file__), "..", "public")
                file_path = os.path.join(public_folder, file_name)
                
                # Try with different case in main public directory
                if not os.path.exists(file_path):
                    if file_name.lower() != file_name:
                        file_path = os.path.join(public_folder, file_name.lower())
                    else:
                        file_path = os.path.join(public_folder, file_name.upper())
                
                if not os.path.exists(file_path):
                    raise HTTPException(status_code=404, detail=f"Excel file {file_name} not found")
        
        # Read the Excel file asynchronously
        df = await read_excel_sheet(file_path, sheet_name)
        
        # Convert to list of dictionaries
        data = df.to_dict('records')
        columns = df.columns.tolist()
        
        return ExcelDataResponse(
            data=data,
            columns=columns,
            count=len(data)
        )
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error reading Excel file {file_name}: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to read Excel file: {error_message}")