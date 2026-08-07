from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
import concurrent.futures
import sqlite3
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.shared_env import load_backend_env

# Load the single backend environment file for every component started here.
load_backend_env()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Financial Data API", version="1.0.0", docs_url="/api/docs", redoc_url="/api/redoc")

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

# Custom thread pool for handling blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# Import all route modules
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.dirname(SCRIPT_DIR))
from routes import (
    health,
    excel,
    sebi,
    bse,
    rbi,
    analytics,
    admin,
    directors,
    minutes,
    ai_assistant,
    chat
)

# Include all routers
app.include_router(health.router)
app.include_router(excel.router)
app.include_router(sebi.router)
app.include_router(bse.router)
app.include_router(rbi.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(directors.router)
app.include_router(minutes.router)
app.include_router(ai_assistant.router)
app.include_router(chat.router)

# Initialize visits database
def init_visits_db():
    """Initialize the visits database with a visits table"""
    db_path = os.path.join(os.path.dirname(__file__), "..", "public", "visits.db")
    
    # Create database and table if they don't exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create visits table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY,
            count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Initialize with a default row if table is empty
    cursor.execute("SELECT COUNT(*) FROM visits")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO visits (count) VALUES (0)")
    
    conn.commit()
    conn.close()

# Initialize places database
def init_places_db():
    """Initialize places database with default Adani Corporate House"""
    db_path = os.path.join(os.path.dirname(__file__), "..", "public", "places.db")
    
    # Create public directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create places table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            is_default BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if default place exists
    cursor.execute("SELECT COUNT(*) FROM places WHERE is_default = 1")
    if cursor.fetchone()[0] == 0:
        # Insert default Adani Corporate House
        cursor.execute('''
            INSERT INTO places (name, address, is_default)
            VALUES (?, ?, ?)
        ''', (
            'Adani Corporate House',
            'Adani Corporate House, Shantigram, Near Vaishno Devi Circle, S. G. Highway, Khodiyar, Ahmedabad - 382421, Gujarat, India',
            1
        ))
    
    conn.commit()
    conn.close()

# Call init functions on startup
@app.on_event("startup")
async def startup_event():
    init_visits_db()
    init_places_db()

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
                return await super().get_response("index.html", scope)
            else:
                raise ex

# Serve static files from the dist directory (React build) - this must be the last route
# Only add this if the dist directory exists
DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")
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
