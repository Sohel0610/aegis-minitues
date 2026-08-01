"""
Database Models for Separate PostgreSQL databases.
"""
import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import Column, Date, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "aegis_backend", ".env"))

# BSE Database Model
class BSENotification(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True)
    SrNo = Column("sr_no", Integer, unique=True, index=True)
    EntityName = Column("entity_name", String(255))
    Link = Column("link", String(500))
    Nature = Column("nature", String(100))
    Summary = Column("summary", Text)
    Date = Column("record_date", Date)

# SEBI Database Model
class SEBINotification(Base):
    # This is the production table used by routes/sebi.py.  The old
    # ``excel_summaries`` name only existed in the retired SQLite implementation.
    __tablename__ = "aegis_sebi_data"
    
    id = Column(Integer, primary_key=True)
    date_key = Column(String(20))  # e.g. "01-09-2025"
    row_index = Column(Integer)
    pdf_link = Column(String(500))
    summary = Column(Text)
    inserted_at = Column(DateTime, default=datetime.utcnow)

# RBI Database Model
class RBINotification(Base):
    __tablename__ = "master_summaries"

    id = Column(Integer, primary_key=True)
    run_date = Column(Date)
    pdf_link = Column(Text)
    summary = Column(Text)
    created_at = Column(DateTime)

def _pg_engine(database_name: str):
    return create_engine(
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', '5432')}/{database_name}",
        pool_pre_ping=True,
        connect_args={"sslmode": os.getenv("POSTGRES_SSLMODE", "require")},
    )

def get_bse_engine():
    return _pg_engine(os.getenv("POSTGRES_DATABASE_BSE"))

def get_sebi_engine():
    # SEBI is intentionally kept in PostgreSQL with BSE/RBI.  A SQLite file
    # makes production pods diverge and prevents fresh regulatory data sharing.
    return _pg_engine(os.getenv("POSTGRES_DATABASE_SEBI"))

def get_rbi_engine():
    return _pg_engine(os.getenv("POSTGRES_DATABASE_RBI"))

def get_bse_session():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_bse_engine())()

def get_sebi_session():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_sebi_engine())()

def get_rbi_session():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_rbi_engine())()
