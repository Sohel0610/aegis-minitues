"""
Chat Orchestrator - FINAL PERFECT VERSION
✅ Returns ALL data (no skipping)
✅ Full summaries for text mode
✅ Short summaries for table mode (1–2 key points)
✅ Exact date filtering (no hallucination)
✅ Notification count in heading
✅ Perfect formatting: Company Name | Date | Subject | Short Summary
"""

from chatbot_backend.utils.query_normalizer import normalize_query
from chatbot_backend.utils.entity_resolver import resolve_entity, _entity_match
from typing import List, Tuple
from chatbot_backend.data_layer.models import DailyLog
from chatbot_backend.indexing_layer.embedding_index import search_similar_notifications, search_sebi_similar, search_rbi_similar
from chatbot_backend.chat_orchestrator.router_logic import route_query, execute_structured_query
from chatbot_backend.llm_layer.llm_client import chat_completion, generate_system_prompt, format_notifications_for_llm
from chatbot_backend.utils.db_formatter import convert_to_common_format
from chatbot_backend.data_layer.db_models import get_sebi_session, get_rbi_session, SEBINotification, RBINotification
from chatbot_backend.data_layer.models import get_db_session
from sqlalchemy import or_, and_
import re
import json
from datetime import datetime

# Analytics service
from chatbot_backend.services.analytics_service import month_wise_notification_count


class ChatOrchestrator:
    """
    FINAL PERFECT VERSION - No Skipping, No Truncation, No Hallucination
    """

    def __init__(self):
        self.system_prompt = generate_system_prompt()

    def detect_query_intent(self, user_query: str) -> str:
        """Detect query intent"""
        q = user_query.lower()

        analytics_keywords = ["trend", "analysis", "how many", "count", "statistics", "month-wise", "year-wise", "chart", "graph"]
        table_keywords = ["list", "show all", "table", "compare", "date wise", "company wise", "in table"]

        if any(kw in q for kw in analytics_keywords):
            return "analytics"
        if any(kw in q for kw in table_keywords):
            return "table"
        return "auto"

    def apply_strict_entity_filter(self, notifications: List, entity_aliases: List[str]) -> List:
        """Filter results to match entity"""
        if not entity_aliases:
            return notifications

        filtered = []
        for notification in notifications:
            if _entity_match(notification, entity_aliases):
                filtered.append(notification)

        return filtered

    def detect_domain(self, query: str) -> str:
        """Detect domain from query"""
        q = query.lower()
        if any(w in q for w in ["bse", "stock", "shares", "scrip", "price", "market"]):
             return "bse"
        if any(w in q for w in ["sebi", "circular", "regulator", "regulation", "adjudication"]):
             return "sebi"
        if any(w in q for w in ["rbi", "bank", "monetary", "repo", "rate", "lending"]):
             return "rbi"
        return None

    def process_query(self, user_query: str, database: str = "all", limit: int = 10, last_n_days: int = None) -> Tuple[object, List[str]]:
        """
        MAIN QUERY PROCESSOR
        """
        # Step 1: Normalize Query
        normalized_query = normalize_query(user_query)
        if normalized_query != user_query:
            print(f"[NORMALIZED] {user_query} → {normalized_query}")
        user_query = normalized_query

        # Step 2: Resolve Entity
        resolved = resolve_entity(user_query)
        strict_entity_canonical = None
        entity_aliases = None

        if resolved:
            strict_entity_canonical = resolved["canonical"]
            entity_aliases = resolved["aliases"]
            print(f" [ENTITY_LOCK] {strict_entity_canonical}")

        # Step 3: Detect Domain if generic (AUTO-ROUTING)
        if database == "all" or database is None:
            detected = self.detect_domain(user_query)
            if detected:
                database = detected
                print(f" [AUTO_ROUTING] Detected domain: {database}")
            else:
                # Handle greetings specifically
                if user_query.lower().strip() in ["hi", "hello", "hey", "help"]:
                    return "Hello! I am your AEGIS Assistant. I can help you with data from BSE, SEBI, and RBI. Which one would you like to explore?", []
                
                # Check for explicit clarification intent or if query is too generic
                # Return structured request for clarification
                return {
                    "response_type": "clarification_needed", 
                    "message": "I can search across BSE, SEBI, and RBI. Which domain are you referring to?",
                    "options": ["BSE", "SEBI", "RBI"]
                }, []

        # Step 4: Detect Intent
        query_intent = self.detect_query_intent(user_query)
        print(f" [QUERY_INTENT] {query_intent}")

        # Step 5: Handle Analytics
        if query_intent == "analytics":
            return self._handle_analytics_query(user_query)

        # Step 6: Route Query - INCREASED LIMIT TO GET ALL DATA
        retrieval_method, sql_results = route_query(
            user_query,
            limit=1000,  # GET ALL DATA - NO SKIPPING
            database=database,
            strict_entity=strict_entity_canonical
        )

        # Step 7: Get Notifications
        if retrieval_method in ["structured", "date_only"]:
            notifications = convert_to_common_format(sql_results, database)
            print(f" Retrieved {len(notifications)} via SQL from {database}")

        else:
            notifications = self.semantic_retrieve(
                user_query,
                database,
                limit=1000,  # GET ALL DATA
                last_n_days=last_n_days,
                strict_entity=strict_entity_canonical
            )
            print(f" Retrieved {len(notifications)} via semantic from {database}")

            if entity_aliases:
                before_count = len(notifications)
                notifications = self.apply_strict_entity_filter(notifications, entity_aliases)
                after_count = len(notifications)
                print(f" [ENTITY_FILTER] {before_count} → {after_count}")

        # Step 8: Format Response
        if query_intent == "table" or self._wants_table(user_query):
            return self._generate_table_response_perfect(user_query, notifications, strict_entity_canonical)
        else:
            return self._generate_text_response_perfect(user_query, notifications, strict_entity_canonical)

    def _handle_analytics_query(self, user_query: str) -> Tuple[dict, List]:
        """Generate analytics response"""
        q = user_query.lower()

        try:
            from chatbot_backend.services.analytics_service import (
                month_wise_notification_count,
                get_notification_trends,
                get_company_wise_counts
            )

            if "company" in q or "entity" in q or "top" in q:
                labels, values = get_company_wise_counts(limit=10)
                title = "Top 10 Companies by Notification Count"
                x_axis = "Company"
            elif "month" in q or "this month" in q:
                now = datetime.utcnow()
                labels, values = month_wise_notification_count(now.month, now.year)
                title = f"Notifications in {now.strftime('%B %Y')}"
                x_axis = "Day"
            else:
                labels, values = get_notification_trends(database="all", days=30)
                title = "Notification Trends (Last 30 Days)"
                x_axis = "Date"

            if not labels or not values:
                return {"response_type": "chart", "message": "No data available"}, []

            return {
                "response_type": "chart",
                "chart_type": "bar",
                "title": title,
                "x_axis": x_axis,
                "y_axis": "Count",
                "data": {"labels": labels, "values": values}
            }, []

        except Exception as e:
            return {"response_type": "text", "message": f"Analytics error: {str(e)}"}, []

    def _shorten_summary(self, full_summary: str) -> str:
        """Extract 1–2 key points from full summary."""
        if not full_summary or full_summary == "NIL":
            return "No summary available"
        sentences = re.split(r'[.\n]', full_summary)
        key_points = [s.strip() for s in sentences if s.strip()]
        return " | ".join(key_points[:2])  # Take first 2 points

    def _generate_table_response_perfect(self, user_query: str, notifications: List, entity_name: str = None) -> Tuple[dict, List]:
        """Generate table response with short summaries"""
        if not notifications:
            return {
                "response_type": "table",
                "title": f"Notifications for {entity_name}" if entity_name else "Search Results",
                "columns": ["Company Name", "Date", "Subject", "Short Summary"],
                "rows": [],
                "message": f"No notifications found"
            }, []

        rows = []
        for n in notifications:
            company = self._safe_get_attr(n, ["EntityName", "entity_name"], "Unknown")
            date = self._safe_get_attr(n, ["Date", "notice_date"], "Unknown")
            subject = self._safe_get_attr(n, ["Nature", "notice_type"], "Unknown")
            full_summary = self._safe_get_attr(n, ["Summary", "summary"], "")
            short_summary = self._shorten_summary(full_summary)

            if date != "Unknown":
                date = str(date)

            rows.append([company, date, subject, short_summary])

        return {
            "response_type": "table",
            "title": f"Notifications for {entity_name}" if entity_name else "Search Results",
            "columns": ["Company Name", "Date", "Subject", "Short Summary"],
            "rows": rows,
            "total_count": len(rows)
        }, self._extract_sources(notifications)

    def _generate_text_response_perfect(self, user_query: str, notifications: List, entity_name: str = None) -> Tuple[str, List]:
        """
        PERFECT TEXT FORMAT with notification count
        Company Name (count)
        Date-[date]
        Sub-[subject]
        Summary-[FULL summary, no truncation]
        """
        if not notifications:
            return f"No notifications found for {entity_name}." if entity_name else "No relevant notifications found.", []

        # Group by company
        company_groups = {}
        for n in notifications:
            company = self._safe_get_attr(n, ["EntityName", "entity_name"], "Unknown")

            if company not in company_groups:
                company_groups[company] = []

            company_groups[company].append(n)

        # Format response
        response_parts = []

        for company, notifs in company_groups.items():
            #  SHOW NOTIFICATION COUNT
            notification_count = len(notifs)
            response_parts.append(f"\n{'='*80}")
            response_parts.append(f" {company} ({notification_count} notifications)")
            response_parts.append(f"{'='*80}\n")

            # All notifications for this company
            for n in notifs:
                date = self._safe_get_attr(n, ["Date", "notice_date"], "Unknown")
                subject = self._safe_get_attr(n, ["Nature", "notice_type"], "Unknown")
                summary = self._safe_get_attr(n, ["Summary", "summary"], "")

                if date != "Unknown":
                    date = str(date)

                if subject == "NIL":
                    subject = "Notification"
                if summary == "NIL":
                    summary = "No summary available"

                response_parts.append(f"Date: {date}")
                response_parts.append(f"Sub: {subject}")
                response_parts.append(f"Summary: {summary}")  # FULL SUMMARY
                response_parts.append("")  # Blank line

        final_response = "\n".join(response_parts)
        sources = self._extract_sources(notifications)

        return final_response, sources

    def _safe_get_attr(self, obj, attr_names: List[str], default):
        """Safely get attribute from object or dict"""
        for attr in attr_names:
            if hasattr(obj, attr):
                val = getattr(obj, attr)
                if val is not None:
                    return val
            elif isinstance(obj, dict):
                val = obj.get(attr)
                if val is not None:
                    return val
        return default

    def _wants_table(self, user_query: str) -> bool:
        """Check if table wanted"""
        keywords = ["list", "show all", "table", "compare", "in table"]
        return any(k in user_query.lower() for k in keywords)

    def _extract_sources(self, notifications: List) -> List[str]:
        """Extract source links"""
        sources = []
        for n in notifications:
            link = self._safe_get_attr(n, ["link", "Link"], None)
            if link and link != "NIL":
                sources.append(link)
        return sources[:5]

    def semantic_retrieve(self, user_query: str, database: str, limit: int = 1000, last_n_days: int = None, strict_entity: str = None) -> List:
        """Semantic retrieval - returns ALL matching data"""
        if database == "bse":
            session = get_db_session()
            try:
                q = session.query(DailyLog)

                if strict_entity:
                    q = q.filter(DailyLog.EntityName.ilike(f"%{strict_entity}%"))

                tokens = [t for t in re.findall(r"[a-zA-Z0-9]+", user_query.lower()) if len(t) > 2]
                if tokens:
                    conditions = []
                    for t in tokens:
                        conditions.append(DailyLog.Summary.ilike(f"%{t}%"))
                        conditions.append(DailyLog.Nature.ilike(f"%{t}%"))
                    q = q.filter(or_(*conditions))

                q = q.filter(
                    or_(
                        DailyLog.Summary != "NIL",
                        DailyLog.Nature != "NIL"
                    )
                )

                results = q.order_by(DailyLog.Date.desc()).limit(limit).all()
                if results:
                    return results

                semantic_results = search_similar_notifications(user_query, top_k=limit)
                ranked = self.re_rank_results(semantic_results, last_n_days)
                return [r["notification"] for r in ranked]
            finally:
                session.close()

        elif database == "sebi":
            session = get_sebi_session()
            try:
                q = session.query(SEBINotification)
                if strict_entity:
                    q = q.filter(SEBINotification.summary.ilike(f"%{strict_entity}%"))
                results = q.order_by(SEBINotification.inserted_at.desc()).limit(limit).all()
                if results:
                    return convert_to_common_format(results, "sebi")
                sebi_sim = search_sebi_similar(user_query, top_k=limit)
                ranked = self.re_rank_results(sebi_sim, last_n_days)
                return [r["notification"] for r in ranked]
            finally:
                session.close()

        elif database == "rbi":
            session = get_rbi_session()
            try:
                q = session.query(RBINotification)
                if strict_entity:
                    q = q.filter(RBINotification.summary.ilike(f"%{strict_entity}%"))
                results = q.order_by(RBINotification.run_date.desc()).limit(limit).all()
                if results:
                    return convert_to_common_format(results, "rbi")
                rbi_sim = search_rbi_similar(user_query, top_k=limit)
                ranked = self.re_rank_results(rbi_sim, last_n_days)
                return [r["notification"] for r in ranked]
            finally:
                session.close()

        bse_sim = search_similar_notifications(user_query, top_k=limit)
        sebi_sim = search_sebi_similar(user_query, top_k=limit)
        rbi_sim = search_rbi_similar(user_query, top_k=limit)
        combined = bse_sim + sebi_sim + rbi_sim
        ranked = self.re_rank_results(combined, last_n_days)
        return [r["notification"] for r in ranked]

    def re_rank_results(self, results: List[dict], last_n_days: int) -> List[dict]:
        """Re-rank by relevance + recency"""
        if not results:
            return []

        import datetime
        now = datetime.datetime.utcnow().date()
        horizon = last_n_days if last_n_days else 90

        scored = []
        for r in results:
            n = r.get("notification")
            sim = r.get("similarity", 0.0)
            d = None
            if hasattr(n, "Date"):
                d = n.Date
            age = (now - d).days if d else horizon
            recency_score = max(0.0, 1.0 - min(age, horizon) / float(horizon))
            total_score = sim + 0.3 * recency_score
            scored.append({"notification": n, "score": total_score})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored


# Global instance
chat_orchestrator = ChatOrchestrator()

def process_user_query(query: str, database: str = "all", limit: int = 10, last_n_days: int = None) -> Tuple[object, List[str]]:
    """Process query"""
    return chat_orchestrator.process_query(query, database, limit=limit, last_n_days=last_n_days)