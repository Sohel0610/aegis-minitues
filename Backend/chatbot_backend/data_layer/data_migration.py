"""
Data Migration Script
Migrates existing databases to unified schema
"""
from sqlalchemy.orm import Session
from src.data_layer.models import RegulatoryNotification, get_db_session, init_db
# Using the old database models for migration
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.models.database import SessionLocalBSE, SessionLocalSEBI, SessionLocalRBI, BSENotification, SEBINotification, RBINotification
from datetime import datetime
import re

def parse_date(date_str):
    """
    Parse date string to datetime object
    """
    if not date_str or date_str == "NIL":
        return None
    
    # Try different date formats
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y/%m/%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    return None

def migrate_bse_data():
    """
    Migrate BSE data to unified schema
    """
    # Get BSE session
    bse_session = SessionLocalBSE()
    
    # Get all BSE notifications
    bse_notifications = bse_session.query(BSENotification).all()
    
    # Get unified session
    unified_session = get_db_session()
    
    migrated_count = 0
    
    for notification in bse_notifications:
        # Skip NIL entries ONLY if ALL fields are NIL
        if (notification.Link == "NIL" and 
            notification.Nature == "NIL" and 
            notification.Summary == "NIL"):
            continue
            
        # Create new unified notification
        unified_notification = RegulatoryNotification(
            source_system="BSE",
            entity_name=notification.EntityName or "",
            notice_date=notification.Date,
            notice_type=notification.Nature or "",
            summary=notification.Summary or "",
            link=notification.Link or "",
            data_quality_score=1.0 if notification.Link != "NIL" else 0.5
        )
        
        unified_session.add(unified_notification)
        migrated_count += 1
    
    # Commit changes
    unified_session.commit()
    unified_session.close()
    bse_session.close()
    
    print(f"Migrated {migrated_count} BSE notifications")

def migrate_sebi_data():
    """
    Migrate SEBI data to unified schema
    """
    # Get SEBI session
    sebi_session = SessionLocalSEBI()
    
    # Get all SEBI notifications
    sebi_notifications = sebi_session.query(SEBINotification).all()
    
    # Get unified session
    unified_session = get_db_session()
    
    migrated_count = 0
    
    for notification in sebi_notifications:
        # Skip NIL entries
        if not notification.summary or notification.summary == "NIL":
            continue
            
        # Parse date
        notice_date = parse_date(notification.date_key)
        if not notice_date:
            continue
            
        # Extract entity name from summary if possible
        entity_name = "SEBI"
        # Try to extract company name from summary
        summary_lower = notification.summary.lower()
        if "limited" in summary_lower or "ltd" in summary_lower:
            # Simple extraction - in real implementation, use more sophisticated NER
            words = summary_lower.split()
            for i, word in enumerate(words):
                if word in ["limited", "ltd"]:
                    # Get a few words before and after
                    start = max(0, i-3)
                    end = min(len(words), i+2)
                    entity_name = " ".join(words[start:end]).title()
                    break
        
        # Create new unified notification
        unified_notification = RegulatoryNotification(
            source_system="SEBI",
            entity_name=entity_name,
            notice_date=notice_date,
            summary=notification.summary or "",
            link=notification.pdf_link or "",
            data_quality_score=1.0 if notification.pdf_link != "NIL" else 0.5
        )
        
        unified_session.add(unified_notification)
        migrated_count += 1
    
    # Commit changes
    unified_session.commit()
    unified_session.close()
    sebi_session.close()
    
    print(f"Migrated {migrated_count} SEBI notifications")

def migrate_rbi_data():
    """
    Migrate RBI data to unified schema
    """
    # Get RBI session
    rbi_session = SessionLocalRBI()
    
    # Get all RBI notifications
    rbi_notifications = rbi_session.query(RBINotification).all()
    
    # Get unified session
    unified_session = get_db_session()
    
    migrated_count = 0
    
    for notification in rbi_notifications:
        # Skip NIL entries
        if not notification.summary or notification.summary == "NIL":
            continue
            
        # Parse date
        notice_date = parse_date(notification.run_date)
        if not notice_date:
            continue
            
        # Create new unified notification
        unified_notification = RegulatoryNotification(
            source_system="RBI",
            entity_name="Reserve Bank of India",
            notice_date=notice_date,
            summary=notification.summary or "",
            link=notification.pdf_link or "",
            data_quality_score=1.0 if notification.pdf_link != "NIL" else 0.5
        )
        
        unified_session.add(unified_notification)
        migrated_count += 1
    
    # Commit changes
    unified_session.commit()
    unified_session.close()
    rbi_session.close()
    
    print(f"Migrated {migrated_count} RBI notifications")

def migrate_all_data():
    """
    Migrate all data to unified schema
    """
    print("Initializing unified database...")
    init_db()
    
    print("Migrating BSE data...")
    migrate_bse_data()
    
    print("Migrating SEBI data...")
    migrate_sebi_data()
    
    print("Migrating RBI data...")
    migrate_rbi_data()
    
    print("Data migration completed!")

if __name__ == "__main__":
    migrate_all_data()