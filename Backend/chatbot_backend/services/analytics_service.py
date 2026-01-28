from sqlalchemy import func
from chatbot_backend.data_layer.models import get_db_session, DailyLog
from datetime import datetime

def month_wise_notification_count(month: int, year: int):
    session = get_db_session()
    try:
        results = (
            session.query(
                func.strftime("%d", DailyLog.Date).label("day"),
                func.count().label("count")
            )
            .filter(func.strftime("%m", DailyLog.Date) == f"{month:02d}")
            .filter(func.strftime("%Y", DailyLog.Date) == str(year))
            .group_by("day")
            .order_by("day")
            .all()
        )

        labels = [f"Day {r.day}" for r in results]
        values = [r.count for r in results]

        return labels, values
    finally:
        session.close()
