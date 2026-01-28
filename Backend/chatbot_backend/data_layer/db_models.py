"""
Database Models for Separate Databases
Models for BSE, SEBI, and RBI databases
"""
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

Base = declarative_base()

# BSE Database Model
class BSENotification(Base):
    __tablename__ = "DailyLogs"
    
    SrNo = Column(Integer, primary_key=True)
    EntityName = Column(String(255))
    Link = Column(String(500))
    Nature = Column(String(100))
    Summary = Column(Text)
    Date = Column(Date)

# SEBI Database Model
class SEBINotification(Base):
    __tablename__ = "excel_summaries"
    
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
    run_date = Column(String(20))  # e.g. "28-09-2025"
    pdf_link = Column(String(500))
    summary = Column(Text)
    created_at = Column(String(50))  # timestamp when row was inserted

# Database engines and sessions for each database
def get_bse_engine():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'notifications.db'))
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

def get_sebi_engine():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'sebi_excel_master.db'))
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

def get_rbi_engine():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'rbi.db'))
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

def get_bse_session():
    engine = get_bse_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def get_sebi_session():
    engine = get_sebi_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def get_rbi_session():
    engine = get_rbi_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()