from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import logging
import os
from .config import settings
from .models import Base, User, Agenda, Decision, ActionItem, Attendee, Document, ChatHistory, Embedding, SessionSummary, UserPreference, ConversationEntity, MeetingMetadata

logger = logging.getLogger(__name__)

# Create database engine. SQLite is supported for local demos; PostgreSQL remains
# the production database. check_same_thread is needed because FastAPI can serve
# synchronous database work from different worker threads.
def _create_engine_with_fallback():
    url = settings.DATABASE_URL
    options = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    else:
        options.update({"pool_size": 5, "max_overflow": 10})
    try:
        eng = create_engine(url, **options)
        # Test connection
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return eng
    except Exception as exc:
        if not url.startswith("sqlite"):
            sqlite_url = "sqlite:///./data/minutes_chatbot_demo.db"
            logger.warning(f"PostgreSQL unreachable ({exc}); falling back to local SQLite at {sqlite_url}")
            os.makedirs("./data", exist_ok=True)
            return create_engine(sqlite_url, connect_args={"check_same_thread": False})
        raise

engine = _create_engine_with_fallback()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        db.close()

def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    logger.info("Initializing minutes chatbot tables")
    _ = (User, Agenda, Decision, ActionItem, Attendee, Document, ChatHistory, Embedding, SessionSummary, UserPreference, ConversationEntity, MeetingMetadata)
    Base.metadata.create_all(bind=engine)
    _apply_non_destructive_schema_upgrades()


def _apply_non_destructive_schema_upgrades() -> None:
    """Add newly introduced nullable columns without dropping local or VM data.

    Production should still use a reviewed migration as part of CI/CD. This keeps
    the existing SQLite demo database usable while the project has no migration
    framework configured for this module.
    """
    additions = {
        "chatbot_documents": {
            "processing_status": "VARCHAR(32)",
            "extraction_method": "VARCHAR(100)",
            "extraction_metadata": "JSON",
            "page_count": "INTEGER",
            "processing_error": "TEXT",
        },
        "chatbot_embeddings": {"chunk_metadata": "JSON"},
        "chatbot_chat_history": {"response_metadata": "JSON"},
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table_name, columns in additions.items():
            if table_name not in inspector.get_table_names():
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_type in columns.items():
                if column_name not in existing:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
