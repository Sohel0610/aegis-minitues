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
import urllib.parse
from datetime import datetime
from typing import Union
import uuid
import subprocess
import platform
from starlette.exceptions import HTTPException as StarletteHTTPException
from docx import Document as DocxDocument

# Ensure we load the backend-local .env even when the server is started from `Backend/`.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Financial Data API", version="1.0.0", docs_url="/api/docs", redoc_url="/api/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex="https?://.*",
    expose_headers=["*"]
)

from routes import (
    health, excel, bse, sebi, rbi, analytics, admin, directors,
    directors_disclosure, director_analysis, minutes, ai_assistant,
    visit_tracking, insider_trading, chat, auth, user_management, rbac,
    director_family_info, director_changes
)

from chatbot_minutes.router import router as chatbot_minutes_router

app.include_router(health.router, prefix="/api")
app.include_router(excel.router, prefix="/api")
app.include_router(bse.router, prefix="/api")
app.include_router(sebi.router, prefix="/api")
app.include_router(rbi.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(director_analysis.router, prefix="/api")
app.include_router(directors_disclosure.router, prefix="/api")
app.include_router(directors.router, prefix="/api")
app.include_router(minutes.router, prefix="/api")
app.include_router(ai_assistant.router, prefix="/api")
app.include_router(visit_tracking.router, prefix="/api")
app.include_router(insider_trading.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(user_management.router, prefix="/api")
app.include_router(rbac.router, prefix="/api")
app.include_router(director_family_info.router, prefix="/api")
app.include_router(director_changes.router, prefix="/api")
app.include_router(chatbot_minutes_router)

thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

@app.on_event("startup")
async def startup_event():
    try:
        from routes.director_data_analysis import init_database
        from routes.rbac import init_rbac_pg_tables
        from routes.user_management import init_rbac_db
        from utils.db_init import init_postgres_tracking
        from routes.minutes import init_minutes_pg
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, init_database)
        await loop.run_in_executor(thread_pool, init_rbac_pg_tables)
        await loop.run_in_executor(thread_pool, init_rbac_db)
        await loop.run_in_executor(thread_pool, init_postgres_tracking)
        await loop.run_in_executor(thread_pool, init_minutes_pg)

        from chatbot_minutes.database import init_db as init_chatbot_db
        init_chatbot_db()
        logger.info("PostgreSQL databases initialized")
    except Exception as e:
        logger.error(f"Startup error: {e}")

# ---------------------------------------------------------
# Static File Serving (strictly via FastAPI)
# ---------------------------------------------------------

# Define important directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_PUBLIC_DIR = os.path.join(BASE_DIR, "public")
FRONTEND_DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "Frontend", "dist")

# Custom static files class to handle SPA routing (frontend)
class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        # Normalize path
        normalized_path = path.lstrip("/")
        
        # Don't serve index.html for API paths that aren't found
        if normalized_path.startswith("api/"):
            raise StarletteHTTPException(status_code=404)
            
        try:
            return await super().get_response(path, scope)
        except (StarletteHTTPException, HTTPException) as ex:
            if ex.status_code == 404:
                # Return index.html for any non-existent file path (SPA routing)
                # This only applies to the root mount
                return await super().get_response("index.html", scope)
            raise ex

# Custom class for backend public files (forbid sensitive files)
class SafeStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        # Prevent downloading database files or hidden files
        if path.endswith(".db") or path.startswith("."):
            logger.warning(f"Forbidden access attempt to: {path}")
            raise StarletteHTTPException(status_code=403)
        return await super().get_response(path, scope)

# 1. Serve backend public files at /public
if os.path.exists(BACKEND_PUBLIC_DIR):
    logger.info(f"Mounting backend public directory: {BACKEND_PUBLIC_DIR}")
    app.mount("/public", SafeStaticFiles(directory=BACKEND_PUBLIC_DIR), name="public-assets")
else:
    logger.warning(f"Backend public directory not found: {BACKEND_PUBLIC_DIR}")

# 2. Serve frontend dist files at / (SPA routing)
if os.path.exists(FRONTEND_DIST_DIR):
    logger.info(f"Mounting frontend dist directory: {FRONTEND_DIST_DIR}")
    app.mount("/", SPAStaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend-spa")
else:
    logger.warning(f"Frontend dist directory not found: {FRONTEND_DIST_DIR}")

@app.get("/api/test-static")
async def test_static_serving():
    return {"message": "Success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
