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
import sqlite3
import urllib.parse
from datetime import datetime
from typing import Union
import uuid
import subprocess
import platform
from starlette.exceptions import HTTPException as StarletteHTTPException
from docx import Document as DocxDocument

load_dotenv()

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
    visit_tracking, insider_trading, chat, auth, user_management, rbac
)

app.include_router(health.router)
app.include_router(excel.router)
app.include_router(bse.router)
app.include_router(sebi.router)
app.include_router(rbi.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(directors.router)
app.include_router(directors_disclosure.router)
app.include_router(director_analysis.router)
app.include_router(minutes.router)
app.include_router(ai_assistant.router)
app.include_router(visit_tracking.router)
app.include_router(insider_trading.router)
app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(user_management.router)
app.include_router(rbac.router)

thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

@app.on_event("startup")
async def startup_event():
    try:
        directors_db_path = os.path.join(os.path.dirname(__file__), "directors_data.db")
        conn = sqlite3.connect(directors_db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS document_summaries (id INTEGER PRIMARY KEY AUTOINCREMENT, director_name TEXT NOT NULL, din TEXT, file_path TEXT NOT NULL UNIQUE, full_text TEXT, summary TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_summaries_file_path ON document_summaries (file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_summaries_director_name ON document_summaries (director_name)")
        conn.commit()
        conn.close()

        from routes.director_data_analysis import init_database
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, init_database)

        from chatbot_minutes.database import init_db as init_chatbot_db
        init_chatbot_db()
        logger.info("Databases initialized")
    except Exception as e:
        logger.error(f"Startup error: {e}")

class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        normalized_path = path.lstrip("/")
        if normalized_path.startswith("api/"):
            raise StarletteHTTPException(status_code=404)
        try:
            return await super().get_response(path, scope)
        except (StarletteHTTPException, HTTPException) as ex:
            if ex.status_code == 404:
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
    return {"message": "Success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
