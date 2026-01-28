"""
Data Layer Models
Unified schema for all regulatory notifications
"""
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, DateTime, DECIMAL, REAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Create base class for declarative models
Base = declarative_base()

# Database connection URLs
import os
DATABASE_URL = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'notifications.db'))}"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class DailyLog(Base):
    """
    Model for DailyLogs table
    """
    __tablename__ = "DailyLogs"
    
    SrNo = Column(REAL, primary_key=True)
    EntityName = Column(Text)
    Link = Column(Text)
    Nature = Column(Text)
    Summary = Column(Text)
    Date = Column(Date)

class RegulatoryNotification(Base):
    """
    Unified model for all regulatory notifications
    """
    __tablename__ = "regulatory_notices"
    
    id = Column(Integer, primary_key=True, index=True)
    source_system = Column(String(10), nullable=False)  # BSE, SEBI, RBI
    entity_name = Column(String(255), nullable=False)
    notice_date = Column(Date, nullable=False)
    notice_type = Column(String(100))
    title = Column(Text)
    summary = Column(Text)
    full_text = Column(Text)
    link = Column(String(500))
    data_quality_score = Column(DECIMAL(3,2))
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    def to_text_chunk(self):
        """
        Convert notification to text chunk for embedding
        """
        return f"EntityName: {self.entity_name}. Date: {self.notice_date}. Nature: {self.notice_type}. Summary: {self.summary}"

# Create tables
def init_db():
    """
    Initialize the database
    """
    Base.metadata.create_all(bind=engine)

def get_db_session():
    """
    Get database session
    """
    return SessionLocal()

def get_non_nil_notifications(entity_name=None, notice_date=None):
    """
    Get notifications that are not all NIL
    Filters out records where Link, Nature, and Summary are all 'NIL'
    """
    session = get_db_session()
    try:
        query = session.query(DailyLog)
        
        # Filter out NIL entries
        query = query.filter(
            ~((DailyLog.Link == "NIL") & 
              (DailyLog.Nature == "NIL") & 
              (DailyLog.Summary == "NIL"))
        )
        
        # Apply entity name filter if provided
        if entity_name:
            query = query.filter(DailyLog.EntityName.contains(entity_name))
            
        # Apply date filter if provided
        if notice_date:
            query = query.filter(DailyLog.Date == notice_date)
            
        return query.all()
    finally:
        session.close()