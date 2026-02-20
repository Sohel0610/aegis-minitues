"""
Database Initialization Script

Creates schema 'minutes_chatbot_db' and all tables 
in the 'minutes_preparation_system' database.

Usage:
    python -m database.init_db
"""

import logging
from sqlalchemy import create_engine, text
from minutes_chatbot.config.settings import settings
from minutes_chatbot.database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database schema and tables"""
    try:
        # Create connection string
        connection_string = (
            f"postgresql://{settings.PGUSER}:{settings.PGPASSWORD}"
            f"@{settings.PGHOST}:{settings.PGPORT}/{settings.PGDATABASE}"
        )
        
        logger.info(f"Connecting to database: {settings.PGDATABASE}")
        logger.info(f"Host: {settings.PGHOST}")
        
        # Create engine
        engine = create_engine(connection_string)
        
        # Create schema if it doesn't exist
        with engine.connect() as conn:
            logger.info("Creating schema 'minutes_chatbot_db' if not exists...")
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS minutes_chatbot_db"))
            
            # Enable pgvector extension
            logger.info("Enabling pgvector extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            conn.commit()
        
        # Create all tables
        logger.info("Creating all tables in schema 'minutes_chatbot_db'...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("\n" + "="*60)
        logger.info("✅ Database initialization completed successfully!")
        logger.info("="*60)
        logger.info(f"Database: {settings.PGDATABASE}")
        logger.info("Schema: minutes_chatbot_db")
        logger.info("\nTables created:")
        logger.info("  1. users - User information")
        logger.info("  2. agendas - Meeting agenda items")
        logger.info("  3. decisions - Meeting decisions ✨ NEW!")
        logger.info("  4. action_items - Tasks with assignees ✨ NEW!")
        logger.info("  5. attendees - Meeting participants ✨ NEW!")
        logger.info("  6. documents - Uploaded documents")
        logger.info("  7. embeddings - Vector embeddings for search")
        logger.info("  8. chat_history - Conversation history")
        logger.info("="*60)
        logger.info("\nNext steps:")
        logger.info("1. Verify tables in pgAdmin")
        logger.info("2. Start the server: python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload")
        logger.info("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"\n❌ Error initializing database: {str(e)}")
        logger.error("\nPlease check:")
        logger.error("1. PostgreSQL credentials in .env file")
        logger.error("2. Database 'minutes_preparation_system' exists")
        logger.error("3. User has permission to create schemas")
        raise


if __name__ == "__main__":
    init_database()
