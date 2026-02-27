"""
Minutes Chatbot - Standalone Module

Auto-registers with aegis_backend when imported.
Provides RAG-based chatbot functionality.
"""

__version__ = "1.0.0"

import logging

logger = logging.getLogger(__name__)


def register_chatbot_routes(app, thread_pool=None):
    """
    Register chatbot routes with main FastAPI app.
    
    This function is called by aegis_backend/fastapi_server.py during startup.
    It automatically integrates all chatbot functionality into the main app.
    
    Args:
        app: FastAPI application instance
        thread_pool: Thread pool executor for async operations
    
    Returns:
        bool: True if registration successful
    """
    try:
        logger.info("Initializing minutes_chatbot module...")
        
        # Import routers
        from .api.chatbot import router as chatbot_router
        from .api.documents import router as documents_router
        from .api.history import router as history_router
        from .api.agendas import router as agendas_router
        
        # Register routes with main app
        app.include_router(chatbot_router)
        app.include_router(documents_router)
        app.include_router(history_router)
        app.include_router(agendas_router)
        
        logger.info("✓ Chatbot routes registered")
        
        # Initialize database
        from .database.init_db import init_chatbot_database
        
        if thread_pool:
            # Run in thread pool to avoid blocking
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                loop.run_in_executor(thread_pool, init_chatbot_database)
            )
        else:
            init_chatbot_database()
        
        logger.info("✓ Chatbot database initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to register chatbot routes: {e}")
        raise


__all__ = ["register_chatbot_routes"]
