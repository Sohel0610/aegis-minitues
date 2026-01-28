
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
from sqlalchemy import or_, and_

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

def extract_month_year(query: str) -> Optional[Tuple[int, int]]:
    """
    Extract month and year from query
     FIX: Detects "december month", "dec month", "december 2025"
    
    Returns: (month, year) or None
    """
    q = query.lower()
    current_year = datetime.now().year
    
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
    
    # Priority 2: Natural language month/day with optional year
    # e.g., "dec 24", "24 dec", "29th december", "dec 24 2025", "24th december 2025", "december 24, 2025"
    for month_name, month_num in MONTH_MAP.items():
        # A) "dec 24" or "dec 24 2025" or "december 24, 2025"
        pattern_a = rf"\b{month_name}\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,)?(?:\s+(\d{{4}}))?\b"
        match_a = re.search(pattern_a, q)
        if match_a:
            day = int(match_a.group(1))
            year = int(match_a.group(2)) if match_a.group(2) else datetime.now().year
            try:
                date_obj = datetime(year, month_num, day).date()
                date_str = str(date_obj)
                print(f" [DATE_PARSE] Single date (month first): {date_str}")
                return [date_str, date_str]
            except ValueError:
                # Invalid day/month combo; continue trying
                pass
        
        # B) "24 dec" or "24th december 2025"
        pattern_b = rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{month_name}(?:,)?(?:\s+(\d{{4}}))?\b"
        match_b = re.search(pattern_b, q)
        if match_b:
            day = int(match_b.group(1))
            year = int(match_b.group(2)) if match_b.group(2) else datetime.now().year
            try:
                date_obj = datetime(year, month_num, day).date()
                date_str = str(date_obj)
                print(f" [DATE_PARSE] Single date (day first): {date_str}")
                return [date_str, date_str]
            except ValueError:
                # Invalid day/month combo; continue trying
                pass
    
    # Pattern 3: YYYY-MM-DD
    pattern1 = r"(\d{4}-\d{2}-\d{2})"
    matches = re.findall(pattern1, query)
    if matches:
        dates.extend(matches)
    
    # Pattern 4: DD-MM-YYYY
    pattern2 = r"(\d{2}-\d{2}-\d{4})"
    matches = re.findall(pattern2, query)
    if matches:
        dates.extend(matches)

    # Pattern 5: DD/MM/YYYY
    pattern3 = r"(\d{2}/\d{2}/\d{4})"
    matches = re.findall(pattern3, query)
    if matches:
        # Normalize to YYYY-MM-DD
        for d in matches:
            try:
                parsed = datetime.strptime(d, "%d/%m/%Y").date()
                dates.append(parsed.strftime("%Y-%m-%d"))
            except ValueError:
                pass

    # Pattern 6: YYYY/MM/DD
    pattern4 = r"(\d{4}/\d{2}/\d{2})"
    matches = re.findall(pattern4, query)
    if matches:
        # Normalize to YYYY-MM-DD
        for d in matches:
            try:
                parsed = datetime.strptime(d, "%Y/%m/%d").date()
                dates.append(parsed.strftime("%Y-%m-%d"))
            except ValueError:
                pass
    
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
    dates: List[str] = None,
    month_year: Tuple[int, int] = None,
    limit: int = 10, 
    database: str = "all"
) -> List:
    """Execute structured SQL query"""
    if database == "bse":
        session = get_db_session()
        try:
            q = session.query(DailyLog)
            
            # Filter out NIL entries
            q = q.filter(
                or_(
                    DailyLog.Summary != "NIL",
                    DailyLog.Nature != "NIL"
                )
            )
            
            # Entity filter
            if strict_entity:
                q = q.filter(DailyLog.EntityName.ilike(f"%{strict_entity}%"))
                print(f" [SQL_FILTER] EntityName LIKE '%{strict_entity}%'")
            
            #  Month/Year filter - STRICT FILTERING
            if month_year:
                month, year = month_year
                print(f" [SQL_FILTER] Filtering for EXACT Month={month}, Year={year}")
                
                # --- NEW: DB-side range filter for target month ---
                # Compute first/last day of the month
                first_day = datetime(year, month, 1).date()
                if month == 12:
                    last_day = datetime(year, 12, 31).date()
                else:
                    next_month_first = datetime(year, month + 1, 1).date()
                    last_day = (next_month_first - timedelta(days=1))
                
                # Apply DB-side filter (preferred; avoids format inconsistencies)
                q_month = q.filter(
                    and_(
                        DailyLog.Date >= first_day,
                        DailyLog.Date <= last_day
                    )
                )
                results = q_month.order_by(DailyLog.Date.desc()).all()
                print(f" [DEBUG] DB-side month filter results: {len(results)}")
                if results:
                    return results
                # --- END NEW ---

                # Fallback: Python-side filter with robust parsing
                results = q.order_by(DailyLog.Date.desc()).all()
                print(f" [DEBUG] Total results before month filter: {len(results)}")
                
                # Robust date extraction
                def _parse_date_any(dval):
                    """Return a date object from various possible formats/attrs."""
                    if dval is None:
                        return None
                    # Already a date/datetime
                    if hasattr(dval, "year") and hasattr(dval, "month"):
                        try:
                            return dval.date() if hasattr(dval, "date") else dval
                        except Exception:
                            pass
                    # String formats
                    if isinstance(dval, str):
                        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
                            try:
                                return datetime.strptime(dval.strip(), fmt).date()
                            except ValueError:
                                continue
                    return None

                filtered = []
                for r in results:
                    # Try primary date field
                    d = getattr(r, "Date", None)
                    # Fallback: some rows store date in notice_date
                    if d is None:
                        d = getattr(r, "notice_date", None)

                    d_obj = _parse_date_any(d)
                    if d_obj and d_obj.month == month and d_obj.year == year:
                        filtered.append(r)
                
                print(f" [SQL_FILTER] Found {len(filtered)} notifications in month {month}/{year}")
                if filtered:
                    print(f" [SQL_FILTER] Date range: {filtered[-1].Date} to {filtered[0].Date}")
                return filtered
            
            # Specific date filter
            if dates:
                parsed_dates = []
                for date_str in dates:
                    try:
                        if "-" in date_str and len(date_str.split("-")[0]) == 4:
                            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        elif "-" in date_str:
                           d_date = datetime.strptime(date_str, "%d-%m-%Y").date()
                        else:
                            continue
                        parsed_dates.append(parsed_date)
                    except ValueError:
                        continue
                
                if len(parsed_dates) == 2 and parsed_dates[0] != parsed_dates[1]:
                    # Date range
                    print(f" [SQL_FILTER] Date Range: {parsed_dates[0]} to {parsed_dates[1]}")
                    q = q.filter(
                        and_(
                            DailyLog.Date >= parsed_dates[0],
                            DailyLog.Date <= parsed_dates[1]
                        )
                    )
                elif len(parsed_dates) >= 1:
                    # Single date
                    single_date = parsed_dates[0]
                    print(f" [SQL_FILTER] Single Date: {single_date}")
                    q = q.filter(DailyLog.Date == single_date)
            
            results = q.order_by(DailyLog.Date.desc()).limit(limit).all()
            print(f" [SQL_QUERY] Returned {len(results)} results")
            return results
        finally:
            session.close()
    
    elif database == "sebi":
        session = get_sebi_session()
        try:
            q = session.query(SEBINotification)
            if strict_entity:
                q = q.filter(SEBINotification.summary.ilike(f"%{strict_entity}%"))
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
            if strict_entity:
                q = q.filter(RBINotification.summary.ilike(f"%{strict_entity}%"))
            if dates:
                date_filters = [RBINotification.run_date == d for d in dates]
                q = q.filter(or_(*date_filters))
            results = q.order_by(RBINotification.run_date.desc()).limit(limit).all()
            return results
        finally:
            session.close()
    
    else:
        return execute_structured_query(strict_entity, dates, month_year, limit, "bse")

def route_query(query: str, limit: int = 10, database: str = "all", strict_entity: str = None) -> Tuple[str, List]:
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
