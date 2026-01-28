"""
Database Formatter Utilities
Utilities to convert database-specific results to a common format for LLM processing
"""
from typing import List, Dict, Any
from datetime import datetime

def format_daily_log(notification) -> Dict[str, Any]:
    """Format DailyLog notification to common format"""
    return {
        "entity_name": notification.EntityName or "Unknown",
        "notice_date": notification.Date.strftime("%Y-%m-%d") if notification.Date else "Unknown",
        "notice_type": notification.Nature or "General Notification",
        "title": f"{notification.EntityName} - {notification.Nature}" if notification.EntityName and notification.Nature else "Notification",
        "summary": notification.Summary or "No summary available",
        "full_text": notification.Summary or "No full text available",
        "link": notification.Link or "No link available",
        "source_system": "BSE"
    }

def format_bse_notification(notification) -> Dict[str, Any]:
    """Format BSE notification to common format"""
    return {
        "entity_name": notification.EntityName or "Unknown",
        "notice_date": notification.Date.strftime("%Y-%m-%d") if notification.Date else "Unknown",
        "notice_type": notification.Nature or "General Notification",
        "title": f"{notification.EntityName} - {notification.Nature}" if notification.EntityName and notification.Nature else "Notification",
        "summary": notification.Summary or "No summary available",
        "full_text": notification.Summary or "No full text available",
        "link": notification.Link or "No link available",
        "source_system": "BSE"
    }

def format_sebi_notification(notification) -> Dict[str, Any]:
    """Format SEBI notification to common format"""
    return {
        "entity_name": "SEBI Regulatory Update",
        "notice_date": notification.date_key or "Unknown",
        "notice_type": "Regulatory Update",
        "title": f"SEBI Update - {notification.date_key}" if notification.date_key else "SEBI Regulatory Update",
        "summary": notification.summary or "No summary available",
        "full_text": notification.summary or "No full text available",
        "link": notification.pdf_link or "No link available",
        "source_system": "SEBI"
    }

def format_rbi_notification(notification) -> Dict[str, Any]:
    """Format RBI notification to common format"""
    return {
        "entity_name": "RBI Monetary Policy Update",
        "notice_date": notification.run_date or "Unknown",
        "notice_type": "Monetary Policy Update",
        "title": f"RBI Update - {notification.run_date}" if notification.run_date else "RBI Monetary Policy Update",
        "summary": notification.summary or "No summary available",
        "full_text": notification.summary or "No full text available",
        "link": notification.pdf_link or "No link available",
        "source_system": "RBI"
    }

def convert_to_common_format(results: List[Any], database: str) -> List[Dict[str, Any]]:
    """Convert database-specific results to common format"""
    formatted_results = []
    
    if database == "bse":
        for notification in results:
            formatted_results.append(format_daily_log(notification))
    elif database == "sebi":
        for notification in results:
            formatted_results.append(format_sebi_notification(notification))
    elif database == "rbi":
        for notification in results:
            formatted_results.append(format_rbi_notification(notification))
    else:
        # For unified database, format DailyLog entries
        for notification in results:
            formatted_results.append(format_daily_log(notification))
    
    return formatted_results