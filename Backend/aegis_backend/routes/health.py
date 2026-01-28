# Health Route Module
# This module provides health check endpoints for monitoring the API status
from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create a router instance for health endpoints
router = APIRouter()

# Health check endpoint that returns the status of the API
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Financial Data API",
        "timestamp": datetime.now().isoformat()
    }