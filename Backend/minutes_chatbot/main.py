"""
Minutes Chatbot - Main Application

FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from minutes_chatbot.api import auth_router, documents_router, chatbot_router, history_router, agendas_router
from minutes_chatbot.config import settings, logger
from minutes_chatbot.database.connection import test_connection
import uvicorn


# Create FastAPI app
app = FastAPI(
    title="Minutes Chatbot API",
    description="ChatGPT-style chatbot for meeting minutes with RAG capabilities",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chatbot_router)
app.include_router(history_router)
app.include_router(agendas_router)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 Starting Minutes Chatbot API...")
    
    # Test database connection
    if test_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed")
    
    logger.info(f"📡 API running on http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"📚 API docs available at http://{settings.API_HOST}:{settings.API_PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("👋 Shutting down Minutes Chatbot API...")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Minutes Chatbot API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = test_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,  # Auto-reload on code changes (development only)
        log_level=settings.LOG_LEVEL.lower()
    )
