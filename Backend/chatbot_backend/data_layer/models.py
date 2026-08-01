"""
Data Layer Models
Unified schema for BSE notifications from PostgreSQL
"""
import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import Column, Date, DateTime, DECIMAL, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "aegis_backend", ".env"))

DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DATABASE_BSE')}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"sslmode": os.getenv("POSTGRES_SSLMODE", "require")},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class DailyLog(Base):
    """Model for daily_logs table in PostgreSQL."""

    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True)
    SrNo = Column("sr_no", Integer, unique=True, index=True)
    EntityName = Column("entity_name", Text)
    Link = Column("link", Text)
    Nature = Column("nature", Text)
    Summary = Column("summary", Text)
    Date = Column("record_date", Date)

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
    Base.metadata.create_all(bind=engine)

def get_db_session():
    return SessionLocal()

def get_non_nil_notifications(entity_name=None, notice_date=None):
    session = get_db_session()
    try:
        query = session.query(DailyLog).filter(
            ~((DailyLog.Link == "NIL") & (DailyLog.Nature == "NIL") & (DailyLog.Summary == "NIL"))
        )

        if entity_name:
            query = query.filter(DailyLog.EntityName.ilike(f"%{entity_name}%"))

        if notice_date:
            query = query.filter(DailyLog.Date == notice_date)

        return query.all()
    finally:
        session.close()
