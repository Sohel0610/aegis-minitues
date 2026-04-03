from sqlalchemy import extract, func
from chatbot_backend.data_layer.models import get_db_session, DailyLog
from datetime import datetime, timedelta

def month_wise_notification_count(month: int, year: int):
    """Get notification count by day for a specific month"""
    session = get_db_session()
    try:
        results = (
            session.query(
                func.to_char(DailyLog.Date, "DD").label("day"),
                func.count().label("count")
            )
            .filter(extract("month", DailyLog.Date) == month)
            .filter(extract("year", DailyLog.Date) == year)
            .group_by(func.to_char(DailyLog.Date, "DD"))
            .order_by(func.to_char(DailyLog.Date, "DD"))
            .all()
        )

        labels = [f"Day {r.day}" for r in results]
        values = [r.count for r in results]

        return labels, values
    finally:
        session.close()


def get_notification_trends(database: str = "all", days: int = 30):
    """Get notification trends for the last N days"""
    session = get_db_session()
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = session.query(
            func.to_char(DailyLog.Date, "YYYY-MM-DD").label("date"),
            func.count().label("count")
        ).filter(DailyLog.Date >= start_date.date())

        results = (
            query.group_by(func.to_char(DailyLog.Date, "YYYY-MM-DD"))
            .order_by(func.to_char(DailyLog.Date, "YYYY-MM-DD"))
            .all()
        )
        
        labels = [r.date for r in results]
        values = [r.count for r in results]
        
        return labels, values
    finally:
        session.close()


def get_company_wise_counts(limit: int = 10):
    """Get top companies by notification count"""
    session = get_db_session()
    try:
        results = (
            session.query(
                DailyLog.EntityName,
                func.count().label("count")
            )
            .filter(DailyLog.EntityName.isnot(None))
            .group_by(DailyLog.EntityName)
            .order_by(func.count().desc())
            .limit(limit)
            .all()
        )
        
        labels = [r.EntityName for r in results]
        values = [r.count for r in results]
        
        return labels, values
    finally:
        session.close()


def compare_companies_notifications(company_names: list, month: int = None, year: int = None):
    """Compare notification counts for multiple companies
    
    Args:
        company_names: List of company names to compare
        month: Optional month filter (1-12)
        year: Optional year filter
        
    Returns:
        labels: List of company names
        values: List of notification counts (total matching rows)
    """
    from chatbot_backend.chat_orchestrator.router_logic import execute_structured_query

    labels = []
    values = []
    month_year = (month, year) if month and year else None

    # Use the same structured retrieval path as the chatbot so chart counts
    # match the table/text counts exactly.
    for company in company_names:
        results = execute_structured_query(
            strict_entity=company,
            dates=None,
            month_year=month_year,
            limit=5000,
            database="all",
        )
        labels.append(company)
        values.append(len(results))

    return labels, values
