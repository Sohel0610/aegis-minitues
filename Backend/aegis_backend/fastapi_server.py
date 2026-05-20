from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
import os
import pandas as pd
import json
import logging
from dotenv import load_dotenv
import asyncio
import concurrent.futures
from functools import partial

# Load environment variables from current directory
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

import sqlite3  # Add this import for database access
import urllib.parse
from datetime import datetime
from typing import Union
import uuid
import subprocess
import platform
from starlette.exceptions import HTTPException as StarletteHTTPException
from docx import Document as DocxDocument

# Environment variables loaded above

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

# Initialize directors data database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    try:
        # Ensure directors_data.db exists and has required tables
        directors_db_path = os.path.join(os.path.dirname(__file__), "directors_data.db")

        # Create database and tables if they don't exist
        conn = sqlite3.connect(directors_db_path)
        cursor = conn.cursor()

        # Create document_summaries table with full_text and summary
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                director_name TEXT NOT NULL,
                din TEXT,
                file_path TEXT NOT NULL UNIQUE,
                full_text TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_summaries_file_path ON document_summaries (file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_summaries_director_name ON document_summaries (director_name)")

        conn.commit()
        conn.close()

        # Initialize core directors tables in PostgreSQL
        from routes.director_data_analysis import init_database
        # Run in thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, init_database)

        # Initialize chatbot database
        from chatbot_minutes.database import init_db as init_chatbot_db
        init_chatbot_db()

        # Initialize RBAC tables
        from routes.rbac import init_rbac_pg_tables
        from routes.user_management import init_rbac_db
        await loop.run_in_executor(thread_pool, init_rbac_pg_tables)
        await loop.run_in_executor(thread_pool, init_rbac_db)

        logger.info("Directors data, chatbot, and RBAC databases initialized")
        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        yield

# Initialize FastAPI app
app = FastAPI(title="Financial Data API", version="1.0.0", docs_url="/api/docs", redoc_url="/api/redoc", lifespan=lifespan)

# Add CORS middleware with more permissive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:8081", "http://127.0.0.1:8080", "http://127.0.0.1:8081", "http://localhost:5173", "https://localhost", "http://localhost:9000", "http://127.0.0.1:9000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex="https?://.*",
    expose_headers=["*"]
)

# Import route modules
from routes import (
    health,
    excel,
    bse,
    sebi,
    rbi,
    analytics,
    admin,
    directors,
    directors_disclosure,
    director_analysis,
    director_changes,
    director_family_info,
    minutes,
    ai_assistant,
    visit_tracking,
    insider_trading,
    chat,
    auth,
    user_management,
    interactive,
    rbac,  # New RBAC module
    director_intelligence, # Added newly for registry enrichment
    institutional_risk,     # Institutional Risk Monitor
    disclosure_downloader,
    registry_management,
    director_exports,
    mca_sync,
    servicenow_reconciliation
)
import chatbot_minutes

# Include all route modules with /api prefix where needed
app.include_router(health.router, prefix="/api")
app.include_router(servicenow_reconciliation.router, prefix="/api")
app.include_router(excel.router, prefix="/api")
app.include_router(bse.router, prefix="/api")
app.include_router(sebi.router, prefix="/api")
app.include_router(rbi.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(directors.router, prefix="/api")
app.include_router(directors_disclosure.router, prefix="/api")
app.include_router(director_analysis.router, prefix="/api")
app.include_router(director_changes.router, prefix="/api")
app.include_router(director_family_info.router, prefix="/api")
app.include_router(minutes.router, prefix="/api")
app.include_router(ai_assistant.router, prefix="/api")
app.include_router(visit_tracking.router, prefix="/api")
app.include_router(insider_trading.router, prefix="/api")
app.include_router(chat.router) # Already has /api/chat prefix in its definition
app.include_router(auth.router, prefix="/api")
app.include_router(user_management.router, prefix="/api")
app.include_router(interactive.router) # Already has /api prefix in its definition

app.include_router(rbac.router, prefix="/api")  # Register RBAC routes with /api prefix
app.include_router(director_intelligence.router, prefix="/api") # Register Director Intelligence Registry routes
app.include_router(institutional_risk.router, prefix="/api")   # Register Institutional Risk Monitor routes
app.include_router(disclosure_downloader.router, prefix="/api")
app.include_router(registry_management.router, prefix="/api")
app.include_router(director_exports.router, prefix="/api")
app.include_router(mca_sync.router)
app.include_router(chatbot_minutes.router) # Router already has /api/minutes-chatbot prefix

# Print all registered routes for debugging
logger.info("Registered Routes:")
for route in app.routes:
    if hasattr(route, "path"):
        logger.info(f"Route: {route.path} [Methods: {getattr(route, 'methods', 'N/A')}]")

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# NOTE: The root endpoint (/) is intentionally not defined here to allow
# the React app to be served from the root path via static file serving.
# All API endpoints are available at their respective paths.

# Custom static files class to handle SPA routing
class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        # Normalize path to check for API routes
        normalized_path = path.lstrip("/")
        
        # Skip API routes entirely - let FastAPI handle them
        # FastAPI routes are checked before mounted static files, but this is a safety check
        if normalized_path.startswith("api/"):
            raise StarletteHTTPException(status_code=404)
        
        try:
            return await super().get_response(path, scope)
        except (StarletteHTTPException, HTTPException) as ex:
            if ex.status_code == 404:
                # Skip API routes - don't serve index.html for them
                normalized_path = path.lstrip("/")
                if normalized_path.startswith("api/"):
                    raise ex
                # Return index.html for any non-existent file (SPA routing)
                # But only if it's not an API request
                if not normalized_path.startswith("api"):
                    return await super().get_response("index.html", scope)
                else:
                    raise ex
            else:
                raise ex

# Serve static files from the dist directory (React build) - this must be the last route
# Only add this if the dist directory exists
DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Frontend", "dist")
if os.path.exists(DIST_DIR):
    
    app.mount("/", SPAStaticFiles(directory=DIST_DIR, html=True), name="static")

# Add a test endpoint to verify static file serving is working
@app.get("/test-static")
async def test_static_serving():
    """Test endpoint to verify static file serving is working"""
    return {"message": "Static file serving should be working correctly"}

if __name__ == "__main__":
    import uvicorn
    
    # Run without SSL on port 8001
    uvicorn.run(app, host="0.0.0.0", port=8000)