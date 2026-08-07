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
import asyncio
import concurrent.futures
from functools import partial
from contextlib import asynccontextmanager

from utils.shared_env import load_backend_env

# Load the single backend environment file for every component started here.
env_path = load_backend_env()

import sqlite3
import urllib.parse
from datetime import datetime
from typing import Union
import uuid
import subprocess
import platform
from starlette.exceptions import HTTPException as StarletteHTTPException
from docx import Document as DocxDocument

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Initialize directors data database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    try:
        directors_db_path = os.path.join(os.path.dirname(__file__), "directors_data.db")
        conn = sqlite3.connect(directors_db_path)
        cursor = conn.cursor()
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_summaries_file_path ON document_summaries (file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_summaries_director_name ON document_summaries (director_name)")
        conn.commit()
        conn.close()

        # Initialize optional PostgreSQL tables (swallows connection errors in local mode)
        try:
            from routes.director_data_analysis import init_database
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(thread_pool, init_database)
        except Exception as e:
            logger.warning(f"Skipped PostgreSQL init_database in local mode: {e}")

        # Initialize chatbot database
        try:
            from chatbot_minutes.database import init_db as init_chatbot_db
            init_chatbot_db()
        except Exception as e:
            logger.warning(f"Chatbot DB init note: {e}")

        logger.info("Backend local databases initialized")
        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        yield

# Initialize FastAPI app
app = FastAPI(title="Financial Data API", version="1.0.0", docs_url="/api/docs", redoc_url="/api/redoc", lifespan=lifespan)

# Add CORS middleware with permissive settings for local dev
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
    rbac,
    director_intelligence,
    institutional_risk,
    disclosure_downloader,
    registry_management,
    director_exports,
    mca_sync,
    servicenow_reconciliation,
    teams
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
app.include_router(chat.router)
app.include_router(auth.router, prefix="/api")
app.include_router(user_management.router, prefix="/api")
app.include_router(interactive.router)

app.include_router(rbac.router, prefix="/api")
app.include_router(director_intelligence.router, prefix="/api")
app.include_router(institutional_risk.router, prefix="/api")
app.include_router(disclosure_downloader.router, prefix="/api")
app.include_router(registry_management.router, prefix="/api")
app.include_router(director_exports.router, prefix="/api")
app.include_router(mca_sync.router)
app.include_router(teams.router, prefix="/api")
app.include_router(chatbot_minutes.router)

logger.info("Registered Routes:")
for route in app.routes:
    if hasattr(route, "path"):
        logger.info(f"Route: {route.path} [Methods: {getattr(route, 'methods', 'N/A')}]")

class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        normalized_path = path.lstrip("/")
        if normalized_path.startswith("api/"):
            raise StarletteHTTPException(status_code=404)
        try:
            return await super().get_response(path, scope)
        except (StarletteHTTPException, HTTPException) as ex:
            if ex.status_code == 404:
                normalized_path = path.lstrip("/")
                if not normalized_path.startswith("api"):
                    return await super().get_response("index.html", scope)
                else:
                    raise ex
            else:
                raise ex

DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Frontend", "dist")
if os.path.exists(DIST_DIR):
    app.mount("/", SPAStaticFiles(directory=DIST_DIR, html=True), name="static")

@app.get("/test-static")
async def test_static_serving():
    return {"message": "Static file serving working"}

if __name__ == "__main__":
    import uvicorn
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Frontend")
    dist_dir = os.path.join(frontend_dir, "dist")
    if not os.path.exists(dist_dir):
        logger.info("Building frontend distribution package...")
        try:
            subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=False)
        except Exception as err:
            logger.warning(f"Frontend auto-build note: {err}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
