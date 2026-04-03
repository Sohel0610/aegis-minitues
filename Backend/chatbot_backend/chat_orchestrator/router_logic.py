"""
Router Logic - FINAL FIX (Month Detection Fixed)
✅ Detects "december month", "dec month"
✅ Better month/year parsing
✅ Exact date parsing
✅ Strict month filtering
"""
import re
from datetime import datetime, timedelta
from typing import Tuple, List, Optional
from chatbot_backend.data_layer.models import get_db_session, DailyLog
from chatbot_backend.data_layer.db_models import get_sebi_session, get_rbi_session, SEBINotification, RBINotification
from sqlalchemy import or_, and_, func, extract

# Month name to number mapping
MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}

def get_most_recent_year_from_db() -> int:
    """
    Query database to find the most recent year with data.
    This allows the system to work with both historical and future data.
    
    Returns: Most recent year in database, or current year as fallback
    """
    try:
        session = get_db_session()
        try:
            # Get the maximum date from the database
            max_date = session.query(func.max(DailyLog.Date)).scalar()
            if max_date:
                # Parse the date and extract year
                if isinstance(max_date, str):
                    year = int(max_date.split('-')[0])
                else:
                    year = max_date.year
                print(f" [YEAR_DETECT] Most recent year in database: {year}")
                return year
        finally:
            session.close()
    except Exception as e:
        print(f" [YEAR_DETECT] Error querying database: {e}, using current year")
    
    # Fallback to current year if database query fails
    return datetime.now().year


def extract_month_year(query: str) -> Optional[Tuple[int, int]]:
    """
    Extract month and year from query
     FIX: Detects "december month", "dec month", "december 2025"
    
    Returns: (month, year) or None
    """
    q = query.lower()
    # SMART FIX: Get the most recent year from database
    # This allows: "nov month" → latest year in DB, "jan 2026" → explicit 2026
    current_year = get_most_recent_year_from_db()
    
    # Pattern 1: "december month", "dec month summary"
    for month_name, month_num in MONTH_MAP.items():
        # Check for "month" keyword after month name
        pattern_with_month = rf"\b{month_name}\s+month\b"
        if re.search(pattern_with_month, q):
            print(f" [MONTH_PARSE] '{month_name} month' → ({month_num}, {current_year})")
            return (month_num, current_year)
    
    # Pattern 2: "november 2025", "nov 2025" (month + year)
    for month_name, month_num in MONTH_MAP.items():
        pattern = rf"\b{month_name}\s+(\d{{4}})\b"
        match = re.search(pattern, q)
        if match:
            year = int(match.group(1))
            print(f" [MONTH_PARSE] '{month_name} {year}' → ({month_num}, {year})")
            return (month_num, year)
    
    # Pattern 3: Just month name (e.g., "december summary")
    # Only if no specific date follows
    for month_name, month_num in MONTH_MAP.items():
        pattern = rf"\b{month_name}\b(?!\s+\d{{1,2}})"
        if re.search(pattern, q):
            print(f" [MONTH_PARSE] '{month_name}' only → ({month_num}, {current_year})")
            return (month_num, current_year)
    
    # Pattern 4: "2025-11", "2025/11"
    pattern = r"(\d{4})[-/](\d{1,2})"
    match = re.search(pattern, q)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        if 1 <= month <= 12:
            return (month, year)
    
    return None

def extract_dates(query: str) -> List[str]:
    """
    Extract specific dates from query
    Returns: [start_date, end_date] or []
    """
    dates = []
    q = query.lower()
    
    # Priority 1: "last N days"
    last_days = re.search(r"last\s+(\d+)\s+days?", q)
    if last_days:
        days = int(last_days.group(1))
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        print(f"[DATE_PARSE] Last {days} days: {start_date} to {end_date}")
        return [str(start_date), str(end_date)]

    # Priority 1.5: "last N months"
    last_months = re.search(r"last\s+(\d+)\s+months?", q)
    if last_months:
        months = int(last_months.group(1))
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=months * 30)
        print(f"[DATE_PARSE] Last {months} months: {start_date} to {end_date}")
        return [str(start_date), str(end_date)]
    
    # Priority 2: explicit year with month/day, e.g. "25 dec 2025", "dec 25 2025"
    for month_name, month_num in MONTH_MAP.items():
        patterns = [
            rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+{month_name}\s+(\d{{4}})\b",
            rf"{month_name}\s+(\d{{1,2}})(?:st|nd|rd|th)?\s+(\d{{4}})\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, q)
            if match:
                if pattern.startswith(r"(\d"):
                    day = int(match.group(1))
                    year = int(match.group(2))
                else:
                    day = int(match.group(1))
                    year = int(match.group(2))
                try:
                    date_obj = datetime(year, month_num, day).date()
                    date_str = str(date_obj)
                    print(f" [DATE_PARSE] Explicit year date: {date_str}")
                    return [date_str, date_str]
                except ValueError:
                    continue

    # Priority 3: "dec 24", "24 dec", "29th december"
    for month_name, month_num in MONTH_MAP.items():
        # "dec 24", "december 24"
        pattern_a = rf"{month_name}\s+(\d{{1,2}})(?:st|nd|rd|th)?\b"
        match = re.search(pattern_a, q)
        if match:
            day = int(match.group(1))
            year = datetime.now().year
            try:
                date_obj = datetime(year, month_num, day).date()
                date_str = str(date_obj)
                print(f" [DATE_PARSE] Single date: {date_str}")
                return [date_str, date_str]
            except ValueError:
                continue
        
        # "24 dec", "24th december"
        pattern_b = rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+{month_name}\b"
        match = re.search(pattern_b, q)
        if match:
            day = int(match.group(1))
            year = datetime.now().year
            try:
                date_obj = datetime(year, month_num, day).date()
                date_str = str(date_obj)
                print(f" [DATE_PARSE] Single date: {date_str}")
                return [date_str, date_str]
            except ValueError:
                continue
    
    # Pattern 4: YYYY-MM-DD
    pattern1 = r"(\d{4}-\d{2}-\d{2})"
    matches = re.findall(pattern1, query)
    if matches:
        dates.extend(matches)
    
    # Pattern 5: DD-MM-YYYY
    pattern2 = r"(\d{2}-\d{2}-\d{4})"
    matches = re.findall(pattern2, query)
    if matches:
        dates.extend(matches)
    
    return dates

def detect_query_type(query: str, strict_entity: str = None) -> str:
    """Detect query type"""
    has_entity = strict_entity is not None
    has_date = bool(extract_dates(query))
    has_month = extract_month_year(query) is not None
    
    if has_entity and (has_date or has_month):
        return "structured"
    elif has_entity or has_date or has_month:
        return "structured"
    else:
        return "semantic"

def execute_structured_query(
    strict_entity: str = None, 
    entity_aliases: List[str] = None,
    dates: List[str] = None,
    month_year: Tuple[int, int] = None,
    limit: int = 10, 
    database: str = "all"
) -> List:
    """Execute structured SQL query"""
    if database == "all":
        combined = []
        for db_name in ["bse", "sebi", "rbi"]:
            combined.extend(
                execute_structured_query(
                    strict_entity=strict_entity,
                    entity_aliases=entity_aliases,
                    dates=dates,
                    month_year=month_year,
                    limit=limit,
                    database=db_name,
                )
            )
        return combined

    if database == "bse":
        session = get_db_session()
        try:
            q = session.query(DailyLog).filter(
                or_(
                    func.coalesce(DailyLog.Summary, "") != "NIL",
                    func.coalesce(DailyLog.Nature, "") != "NIL",
                )
            )

            if entity_aliases:
                alias_filters = [DailyLog.EntityName.ilike(f"%{alias}%") for alias in entity_aliases if alias]
                if alias_filters:
                    q = q.filter(or_(*alias_filters))
                    print(f" [SQL_FILTER] EntityName matched aliases: {entity_aliases}")
            elif strict_entity:
                q = q.filter(DailyLog.EntityName.ilike(f"%{strict_entity}%"))
                print(f" [SQL_FILTER] EntityName LIKE '%{strict_entity}%'")

            if month_year:
                month, year = month_year
                q = q.filter(extract("month", DailyLog.Date) == month)
                q = q.filter(extract("year", DailyLog.Date) == year)
                print(f" [SQL_FILTER] Filtering for EXACT Month={month}, Year={year}")

            if dates:
                parsed_dates = []
                for date_str in dates:
                    try:
                        if "-" in date_str and len(date_str.split("-")[0]) == 4:
                            parsed_dates.append(datetime.strptime(date_str, "%Y-%m-%d").date().isoformat())
                        elif "-" in date_str:
                            parsed_dates.append(datetime.strptime(date_str, "%d-%m-%Y").date().isoformat())
                    except ValueError:
                        continue

                if len(parsed_dates) == 2 and parsed_dates[0] != parsed_dates[1]:
                    start_date = datetime.strptime(parsed_dates[0], "%Y-%m-%d").date()
                    end_date = datetime.strptime(parsed_dates[1], "%Y-%m-%d").date()
                    q = q.filter(DailyLog.Date.between(start_date, end_date))
                    print(f" [SQL_FILTER] Date Range: {parsed_dates[0]} to {parsed_dates[1]}")
                elif parsed_dates:
                    single_date = datetime.strptime(parsed_dates[0], "%Y-%m-%d").date()
                    q = q.filter(DailyLog.Date == single_date)
                    print(f" [SQL_FILTER] Single Date: {parsed_dates[0]}")

            q = q.order_by(DailyLog.Date.desc())
            if limit:
                q = q.limit(limit)

            results = q.all()
            print(f" [SQL_QUERY] Returned {len(results)} results")
            return results
        finally:
            session.close()
    
    elif database == "sebi":
        session = get_sebi_session()
        try:
            q = session.query(SEBINotification)
            if entity_aliases:
                alias_filters = [SEBINotification.summary.ilike(f"%{alias}%") for alias in entity_aliases if alias]
                if alias_filters:
                    q = q.filter(or_(*alias_filters))
            elif strict_entity:
                q = q.filter(SEBINotification.summary.ilike(f"%{strict_entity}%"))
            if month_year:
                month, year = month_year
                results = q.order_by(SEBINotification.inserted_at.desc()).all()
                filtered = []
                for row in results:
                    try:
                        parsed = datetime.strptime(str(row.date_key), "%d-%m-%Y")
                        if parsed.month == month and parsed.year == year:
                            filtered.append(row)
                    except ValueError:
                        continue
                return filtered
            if dates:
                date_filters = [SEBINotification.date_key == d for d in dates]
                q = q.filter(or_(*date_filters))
            results = q.order_by(SEBINotification.inserted_at.desc()).limit(limit).all()
            return results
        finally:
            session.close()
    
    elif database == "rbi":
        session = get_rbi_session()
        try:
            q = session.query(RBINotification)
            if entity_aliases:
                alias_filters = [RBINotification.summary.ilike(f"%{alias}%") for alias in entity_aliases if alias]
                if alias_filters:
                    q = q.filter(or_(*alias_filters))
            elif strict_entity:
                q = q.filter(RBINotification.summary.ilike(f"%{strict_entity}%"))
            if month_year:
                month, year = month_year
                results = q.order_by(RBINotification.run_date.desc()).all()
                filtered = []
                for row in results:
                    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
                        try:
                            parsed = datetime.strptime(str(row.run_date), fmt)
                            if parsed.month == month and parsed.year == year:
                                filtered.append(row)
                            break
                        except ValueError:
                            continue
                return filtered
            if dates:
                parsed_dates = []
                for date_str in dates:
                    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
                        try:
                            parsed_dates.append(datetime.strptime(date_str, fmt).date())
                            break
                        except ValueError:
                            pass
                if parsed_dates:
                    q = q.filter(or_(*[RBINotification.run_date == d for d in parsed_dates]))
            results = q.order_by(RBINotification.run_date.desc()).limit(limit).all()
            return results
        finally:
            session.close()
    
    else:
        return execute_structured_query(strict_entity, entity_aliases, dates, month_year, limit, "bse")

def route_query(query: str, limit: int = 10, database: str = "all", strict_entity: str = None, entity_aliases: List[str] = None) -> Tuple[str, List]:
    """Main routing function"""
    print(f" [ROUTER] Query: '{query}'")
    print(f" [ROUTER] Entity Lock: {strict_entity}")
    
    # Extract dates FIRST (higher priority)
    dates = extract_dates(query)
    if dates:
        print(f" [ROUTER] Detected Dates: {dates}")
    
    # Extract month/year ONLY if no specific dates
    month_year = None
    if not dates:
        month_year = extract_month_year(query)
        if month_year:
            print(f" [ROUTER] Detected Month/Year: {month_year}")
    
    # Detect query type
    query_type = detect_query_type(query, strict_entity)
    print(f" [ROUTER] Type: {query_type}")
    
    if query_type == "structured":
        results = execute_structured_query(
            strict_entity=strict_entity,
            entity_aliases=entity_aliases,
            dates=dates,
            month_year=month_year,
            limit=limit,
            database=database
        )
        print(f" [ROUTER] Structured query returned {len(results)} results")
        return "structured", results
    
    else:
        print(f" [ROUTER] Using semantic retrieval")
        return "semantic", []
