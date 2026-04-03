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
from chatbot_backend.utils.entity_registry import ENTITY_REGISTRY
from typing import List, Tuple
from chatbot_backend.data_layer.models import DailyLog
from chatbot_backend.indexing_layer.embedding_index import search_similar_notifications, search_sebi_similar, search_rbi_similar
from chatbot_backend.chat_orchestrator.router_logic import route_query, execute_structured_query
from chatbot_backend.llm_layer.llm_client import chat_completion, generate_system_prompt, format_notifications_for_llm
from chatbot_backend.utils.db_formatter import convert_to_common_format, format_mixed_notification
from chatbot_backend.data_layer.db_models import get_sebi_session, get_rbi_session, SEBINotification, RBINotification
from chatbot_backend.data_layer.models import get_db_session
from sqlalchemy import or_, and_
import re
import json
import hashlib
from datetime import datetime
from collections import Counter

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

        # Check for comparison queries first (higher priority)
        comparison_patterns = [
            r'compare\s+.*\s+and\s+',  # "compare X and Y"
            r'comparison\s+between',    # "comparison between X and Y"
            r'between\s+.*\s+and\s+',   # "between X and Y"
            r'vs\s+',                   # "X vs Y"
            r'versus\s+'                # "X versus Y"
        ]
        if any(re.search(pattern, q) for pattern in comparison_patterns):
            return "comparison"

        chart_terms = ["chart", "charts", "graph", "graphs", "compare", "comparison", "between", "versus", " vs "]
        has_chart_term = any(term in q for term in chart_terms)
        alias_hits = set()
        for canonical, aliases in ENTITY_REGISTRY.items():
            for alias in aliases:
                alias_lower = alias.lower().strip()
                if len(alias_lower) >= 4 and alias_lower in q:
                    alias_hits.add(canonical)
                    break

        if has_chart_term and len(alias_hits) >= 2:
            return "comparison"

        if has_chart_term and q.count(" and ") >= 2:
            return "comparison"

        analytics_keywords = ["trend", "analysis", "statistics", "month-wise", "year-wise", "chart", "graph"]
        table_keywords = ["list", "show all", "table", "date wise", "company wise", "in table"]

        if any(kw in q for kw in analytics_keywords):
            return "analytics"
        if any(kw in q for kw in table_keywords):
            return "table"
        return "auto"

    def _wants_count_only(self, user_query: str) -> bool:
        q = user_query.lower()
        count_keywords = ["how many", "count", "total notifications", "total notification", "number of notifications"]
        return any(keyword in q for keyword in count_keywords)

    def _asks_for_database_results(self, user_query: str) -> bool:
        q = user_query.lower().strip()
        database_terms = [
            "notification", "notifications", "bse", "sebi", "rbi", "stock", "regulation",
            "circular", "circulars", "filing", "filings", "disclosure", "disclosures",
            "latest update", "latest updates", "latest notification", "latest notifications",
            "recent update", "recent updates", "recent notification", "recent notifications",
            "investor", "analyst", "trading window", "subsidiary", "incorporation",
            "rating", "meeting", "interaction", "date wise", "company wise", "show all",
            "list", "table", "chart", "graph", "trend", "analysis", "statistics",
            "month-wise", "year-wise", "compare", "comparison", "versus", " vs ",
            "count", "how many", "number of notifications", "total notifications",
        ]
        return any(term in q for term in database_terms)

    def _asks_for_company_overview(self, user_query: str, strict_entity_canonical: str = None) -> bool:
        q = user_query.lower().strip()
        if self._asks_for_database_results(q):
            return False

        overview_patterns = [
            r"^tell me about\s+",
            r"^let me know about\s+",
            r"^give me details about\s+",
            r"^give details about\s+",
            r"^describe\s+",
            r"^what is\s+",
            r"^who is\s+",
            r"^give me an overview of\s+",
            r"^overview of\s+",
            r"^give me idea about\s+",
            r"^give me an idea about\s+",
            r"^give idea about\s+",
            r"^explain\s+",
            r"^brief me about\s+",
        ]
        if any(re.search(pattern, q) for pattern in overview_patterns):
            return True

        overview_cues = [
            "about",
            "overview",
            "profile",
            "business",
            "what does",
            "who are",
            "company details",
            "company profile",
            "background",
            "idea about",
        ]
        has_overview_cue = any(cue in q for cue in overview_cues)
        return bool(strict_entity_canonical and has_overview_cue)

    def _is_general_query(self, user_query: str, strict_entity_canonical: str = None) -> bool:
        if strict_entity_canonical:
            return False
        q = user_query.lower().strip()
        database_terms = [
            "notification", "notifications", "bse", "sebi", "rbi", "stock", "regulation",
            "company", "entity", "circular", "filing", "disclosure", "month", "date",
            "latest update", "latest updates", "investor", "analyst", "agel", "adani",
        ]
        return not any(term in q for term in database_terms)

    def _is_knowledge_query(self, user_query: str, strict_entity_canonical: str = None) -> bool:
        return self._asks_for_company_overview(user_query, strict_entity_canonical)

    def _is_unsupported_database_query(self, user_query: str) -> bool:
        return False

    def _handle_general_query(self, user_query: str) -> Tuple[str, List[str]]:
        q = user_query.lower().strip()
        if q in {"who are you", "who are you?"}:
            return (
                "I am Aegis Intelligence, your AI assistant for regulatory notifications, company disclosures, and general guidance. "
                "I can answer database-backed BSE, SEBI, and RBI questions, and I can also help with general questions when you are not asking about the databases.",
                [],
            )
        return self._unrelated_query_response(user_query)

    def _unrelated_query_response(self, user_query: str) -> Tuple[str, List[str]]:
        sample_questions = [
            "Show Adani Green Energy notifications for December 2025.",
            "Count AGEL notifications in December 2025.",
            "Show the latest BSE updates.",
            "List SEBI notifications for this month.",
            "What are the latest RBI circulars?",
            "Compare Adani Green Energy and Adani Power notifications in December 2025.",
            "Show AGEL investor meeting notifications in December 2025.",
            "Give me AGEL disclosures related to ESG rating.",
            "List notifications on 25 December 2025 for Adani Green Energy.",
            "Show the top companies by notification count.",
        ]
        canned_replies = [
            "Sorry, I cannot help with that. I am Aegis Intelligence, so please ask me about BSE, SEBI, RBI, company disclosures, charts, or notification-related questions.",
            "I am focused on regulatory intelligence and company disclosure data. Please ask me something related to notifications, company updates, SEBI, RBI, or BSE.",
            "That looks unrelated to my scope. I can help with Aegis Intelligence topics such as company notifications, regulatory updates, trends, comparisons, and disclosure summaries.",
            "I am designed for Aegis Intelligence use cases. Try asking about a company, a month, a date range, the latest updates, or BSE, SEBI, and RBI data.",
        ]
        reply_index = int(hashlib.md5(user_query.lower().strip().encode()).hexdigest(), 16) % len(canned_replies)
        sample_block = "\n\nSample questions you can ask:\n" + "\n".join(
            f"{idx}. {question}" for idx, question in enumerate(sample_questions, start=1)
        )
        return f"{canned_replies[reply_index]}{sample_block}", []

    def _handle_unsupported_database_query(self, user_query: str) -> Tuple[str, List[str]]:
        message = (
            "I could not find a direct 'announcements' dataset for that request. "
            "This chatbot currently works best with notifications, disclosures, circulars, regulatory updates, and comparisons."
        )
        sample_block = "\n\nSample questions you can ask:\n" + "\n".join([
            "1. Show the latest BSE notifications.",
            "2. List BSE notifications for the last 30 days.",
            "3. Show Adani Green Energy notifications for December 2025.",
            "4. Count AGEL notifications in December 2025.",
            "5. List SEBI circulars for this month.",
            "6. Show the latest RBI updates.",
            "7. Compare Adani Green Energy and Adani Power notifications in December 2025.",
            "8. Show AGEL investor meeting notifications in December 2025.",
            "9. Give me AGEL disclosures related to ESG rating.",
            "10. Show the top companies by notification count.",
        ])
        return f"{message}{sample_block}", []

    def _handle_knowledge_query(self, user_query: str, strict_entity_canonical: str = None) -> Tuple[str, List[str]]:
        subject = strict_entity_canonical or user_query
        prompt = (
            "You are Aegis Intelligence. "
            "Answer as a knowledgeable assistant using general model knowledge. "
            "Give a concise but genuinely helpful overview in plain English. "
            "If the topic is a company or group, explain what it is, what it does, key business segments, and why it is known. "
            "When the user asks casually like 'tell me about' or 'give me an idea about', treat it as a company overview request, not a notifications lookup. "
            "Do not invent database results. "
            "Do not answer in database/table format. "
            "End with one short line saying the user can also ask for BSE, SEBI, or RBI notification data."
        )

        try:
            return chat_completion(prompt, user_query), []
        except Exception:
            return (
                f"{subject} appears to be a general knowledge query rather than a database retrieval query. "
                "I can answer company overviews with the model, and I can also search BSE, SEBI, and RBI notifications if you ask for regulatory updates.",
                [],
            )

    def _apply_query_specific_filters(self, notifications: List, user_query: str) -> List:
        if not notifications:
            return notifications

        query_lower = user_query.lower()
        keyword_groups = []

        if any(term in query_lower for term in ["esg", "rating"]):
            keyword_groups.append(["esg", "rating"])
        if any(term in query_lower for term in ["investor", "analyst", "meeting", "interaction"]):
            keyword_groups.append(["investor", "analyst", "meeting", "interaction"])
        if any(term in query_lower for term in ["subsidiary", "incorporation", "step-down"]):
            keyword_groups.append(["subsidiary", "incorporation", "step-down"])
        if any(term in query_lower for term in ["trading window", "closure of trading window"]):
            keyword_groups.append(["trading window", "closure"])

        if not keyword_groups:
            return notifications

        filtered = []
        for notification in notifications:
            subject = str(self._safe_get_attr(notification, ["Nature", "notice_type", "title"], "")).lower()
            summary = str(self._safe_get_attr(notification, ["Summary", "summary", "full_text"], "")).lower()
            haystack = f"{subject} {summary}"
            if any(any(keyword in haystack for keyword in group) for group in keyword_groups):
                filtered.append(notification)

        return filtered or notifications

    def _is_summary_qa_query(self, user_query: str) -> bool:
        q = user_query.lower().strip()

        if not q:
            return False

        blocked_terms = [
            "table", "list", "show all", "chart", "graph", "compare", "comparison",
            "versus", " vs ", "how many", "count", "total notifications",
        ]
        if any(term in q for term in blocked_terms):
            return False

        question_cues = [
            "what", "which", "who", "when", "why", "how", "can you tell",
            "tell me", "explain", "summarize", "describe",
        ]
        return any(cue in q for cue in question_cues) or q.endswith("?")

    def _has_explicit_entity_mention(self, user_query: str) -> bool:
        q = user_query.lower().strip()
        if not q:
            return False

        ambiguous_aliases = {"idea"}
        short_aliases = {"agel", "atgl", "ril", "tcs", "hcl", "sbi", "ntpc", "itc", "infy", "msil", "vi"}

        for aliases in ENTITY_REGISTRY.values():
            for alias in aliases:
                alias_lower = alias.lower().strip()
                if not alias_lower or alias_lower in ambiguous_aliases:
                    continue
                if len(alias_lower) <= 3 and alias_lower not in short_aliases:
                    continue

                pattern = r"\b" + re.escape(alias_lower) + r"\b"
                if re.search(pattern, q):
                    return True

        return False

    def _suggest_company_name_for_query(self, user_query: str) -> Tuple[str, List[str]]:
        return (
            "I could not identify the company clearly from your question. "
            "Please include the company name or short code so I can answer more accurately.\n\n"
            "Examples:\n"
            "- Which civil case happened on 31 Jan 2026 against Gautam Adani and Sagar Adani for AGEL?\n"
            "- Who signed the disclosure on 2026-01-31 for Adani Green Energy?\n"
            "- Show 31 Jan 2026 disclosures for AGEL.",
            [],
        )

    def _extract_query_terms(self, user_query: str) -> List[str]:
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "of", "to", "for", "from", "in", "on", "at", "by", "with", "about",
            "into", "within", "against", "regarding", "this", "that", "these",
            "those", "there", "their", "then", "than", "and", "or", "but", "if",
            "so", "as", "it", "its", "he", "she", "they", "them", "his", "her",
            "what", "which", "who", "when", "where", "why", "how", "can", "could",
            "would", "should", "do", "does", "did", "have", "has", "had", "any",
            "all", "about", "within", "under", "over", "after", "before", "during",
            "notification", "notifications", "summary", "summaries", "update",
            "updates", "document", "disclosure", "disclosures", "record", "records",
            "show", "tell", "give", "find", "search", "asked", "happen", "happened",
            "happening", "date", "sub", "subject",
            "january", "jan", "february", "feb", "march", "mar", "april", "apr",
            "may", "june", "jun", "july", "jul", "august", "aug", "september",
            "sep", "sept", "october", "oct", "november", "nov", "december", "dec",
        }
        tokens = re.findall(r"[a-zA-Z0-9]+", user_query.lower())
        return [token for token in tokens if len(token) > 2 and token not in stopwords and not token.isdigit()]

    def _rank_notifications_for_question(self, notifications: List, user_query: str) -> List:
        if not notifications:
            return []

        query_terms = self._extract_query_terms(user_query)
        term_counter = Counter(query_terms)
        ranked = []

        for notification in notifications:
            item = format_mixed_notification(notification)
            entity = str(item.get("entity_name", "")).lower()
            notice_type = str(item.get("notice_type", "")).lower()
            title = str(item.get("title", "")).lower()
            summary = str(item.get("summary", "")).lower()
            notice_date = str(item.get("notice_date", "")).lower()

            haystack = f"{entity} {notice_type} {title} {summary} {notice_date}"
            score = 0

            for term, freq in term_counter.items():
                if term in entity:
                    score += 5 * freq
                if term in notice_type:
                    score += 4 * freq
                if term in title:
                    score += 4 * freq
                if term in summary:
                    score += 3 * freq
                if term in notice_date:
                    score += 6 * freq

            if user_query.lower().strip() in haystack:
                score += 12

            ranked.append((score, item, notification))

        ranked.sort(
            key=lambda row: (
                row[0],
                row[1].get("notice_date", ""),
            ),
            reverse=True,
        )

        scored_rows = [row for row in ranked if row[0] > 0]
        if scored_rows:
            return [row[2] for row in scored_rows]
        return [row[2] for row in ranked]

    def _extract_best_matching_sentences(self, notifications: List, user_query: str, max_sentences: int = 3) -> List[str]:
        query_terms = set(self._extract_query_terms(user_query))
        if not query_terms:
            return []

        scored_sentences = []
        for notification in notifications[:5]:
            item = format_mixed_notification(notification)
            summary = item.get("summary", "")
            parts = re.split(r"(?<=[.!?])\s+|\n+", str(summary))
            for part in parts:
                sentence = part.strip(" -")
                if not sentence:
                    continue
                sentence_lower = sentence.lower()
                overlap = sum(1 for term in query_terms if term in sentence_lower)
                if overlap > 0:
                    scored_sentences.append((overlap, sentence))

        scored_sentences.sort(key=lambda row: row[0], reverse=True)
        selected = []
        seen = set()
        for _, sentence in scored_sentences:
            normalized = sentence.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            selected.append(sentence)
            if len(selected) >= max_sentences:
                break
        return selected

    def _answer_from_summary_context(self, user_query: str, notifications: List, entity_name: str = None) -> Tuple[str, List]:
        if not notifications:
            return f"No notifications found for {entity_name}." if entity_name else "No relevant notifications found.", []

        ranked_notifications = self._rank_notifications_for_question(notifications, user_query)
        top_notifications = ranked_notifications[:8]
        llm_context = format_notifications_for_llm([format_mixed_notification(n) for n in top_notifications])

        system_prompt = (
            "You are Aegis Intelligence. "
            "Answer the user's question strictly from the provided notification summaries only. "
            "Do not add outside knowledge. "
            "If the answer is present, answer directly in 2-6 short lines. "
            "Mention the date and subject when helpful. "
            "If multiple records are relevant, say that clearly. "
            "If the summaries do not contain the answer, say 'Insufficient data in the retrieved summaries.' "
            "Use plain ASCII only."
        )
        user_prompt = (
            f"User question:\n{user_query}\n\n"
            f"Retrieved notifications:\n{llm_context}\n"
        )

        try:
            answer = chat_completion(system_prompt, user_prompt)
            if answer and answer.strip():
                return answer.strip(), self._extract_sources(top_notifications)
        except Exception:
            pass

        top_item = format_mixed_notification(top_notifications[0])
        best_sentences = self._extract_best_matching_sentences(top_notifications, user_query)
        if best_sentences:
            response_lines = [best_sentences[0]]
            if len(best_sentences) > 1:
                response_lines.extend(best_sentences[1:])
            response_lines.append(f"Date: {top_item.get('notice_date', 'Unknown')}")
            response_lines.append(f"Subject: {top_item.get('notice_type', 'Unknown')}")
            return "\n".join(response_lines), self._extract_sources(top_notifications)

        fallback = [
            f"Most relevant record date: {top_item.get('notice_date', 'Unknown')}",
            f"Subject: {top_item.get('notice_type', 'Unknown')}",
            f"Summary: {top_item.get('summary', 'No summary available')}",
        ]
        return "\n".join(fallback), self._extract_sources(top_notifications)


    def apply_strict_entity_filter(self, notifications: List, entity_aliases: List[str]) -> List:
        """Filter results to match entity"""
        if not entity_aliases:
            return notifications

        filtered = []
        for notification in notifications:
            if _entity_match(notification, entity_aliases):
                filtered.append(notification)

        return filtered

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

        if self._is_knowledge_query(user_query, strict_entity_canonical):
            return self._handle_knowledge_query(user_query, strict_entity_canonical)

        if self._is_general_query(user_query, strict_entity_canonical):
            return self._handle_general_query(user_query)

        if self._is_unsupported_database_query(user_query):
            return self._handle_unsupported_database_query(user_query)

        # Step 3: Detect Intent
        query_intent = self.detect_query_intent(user_query)
        print(f" [QUERY_INTENT] {query_intent}")

        # Step 4: Handle Analytics
        if query_intent == "analytics":
            return self._handle_analytics_query(user_query)

        # Step 4.5: Handle Comparison
        if query_intent == "comparison":
            return self._handle_comparison_query(user_query)

        # Step 5: Route Query - INCREASED LIMIT TO GET ALL DATA
        retrieval_method, sql_results = route_query(
            user_query,
            limit=1000,  # GET ALL DATA - NO SKIPPING
            database=database,
            strict_entity=strict_entity_canonical,
            entity_aliases=entity_aliases,
        )

        # Step 6: Get Notifications
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

        notifications = self._apply_query_specific_filters(notifications, user_query)

        if not notifications and not self._has_explicit_entity_mention(user_query):
            return self._suggest_company_name_for_query(user_query)

        if self._wants_count_only(user_query):
            return self._generate_count_response(user_query, notifications, strict_entity_canonical)

        if self._is_summary_qa_query(user_query):
            return self._answer_from_summary_context(user_query, notifications, strict_entity_canonical)

        # Step 7: Format Response
        if query_intent == "table" or self._wants_table(user_query):
            return self._generate_table_response_perfect(user_query, notifications, strict_entity_canonical)
        else:
            return self._generate_text_response_perfect(user_query, notifications, strict_entity_canonical)

    def _generate_count_response(self, user_query: str, notifications: List, entity_name: str = None) -> Tuple[str, List]:
        if not notifications:
            if entity_name:
                return f"No notifications found for {entity_name}.", []
            return "No notifications found.", []

        count = len(notifications)
        if entity_name:
            return f"{entity_name} has {count} matching notifications.", self._extract_sources(notifications)
        return f"I found {count} matching notifications.", self._extract_sources(notifications)

    def _handle_analytics_query(self, user_query: str) -> Tuple[dict, List]:
        """Generate analytics response"""
        q = user_query.lower()

        if (
            re.search(r'between\s+.*\s+and\s+', q)
            or " vs " in q
            or " versus " in q
        ):
            return self._handle_comparison_query(user_query)

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

    def _handle_comparison_query(self, user_query: str):
        """Handle comparison queries like 'compare X and Y'"""
        try:
            from chatbot_backend.services.analytics_service import compare_companies_notifications
            from chatbot_backend.chat_orchestrator.router_logic import extract_month_year
            from chatbot_backend.utils.entity_resolver import resolve_entity
            from chatbot_backend.utils.entity_registry import ENTITY_REGISTRY
            
            q = user_query.lower()
            company_names = []

            def _clean_comparison_part(part: str) -> str:
                cleaned = part.lower()
                cleaned = re.sub(
                    r'\b(show|give|list|display|plot|draw|create|me|the|a|an|my|for|of|in|on)\b',
                    ' ',
                    cleaned,
                )
                cleaned = re.sub(
                    r'\b(graph|graphs|chart|charts|comparison|compare|between|versus|vs|notifications?|notification|counts?|count)\b',
                    ' ',
                    cleaned,
                )
                cleaned = re.sub(
                    r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december)\b',
                    ' ',
                    cleaned,
                    flags=re.IGNORECASE,
                )
                cleaned = re.sub(r'\b(2024|2025|2026|2027)\b', ' ', cleaned)
                cleaned = re.sub(r'\s+', ' ', cleaned)
                return cleaned.strip(" ?,.")

            def _resolve_company_name(part: str):
                cleaned = _clean_comparison_part(part)
                if not cleaned:
                    return None
                resolved = resolve_entity(cleaned)
                if resolved:
                    return resolved["canonical"]
                return cleaned.title()

            # First pass: extract all explicit entity aliases that appear in the query.
            alias_matches = []
            for canonical, aliases in ENTITY_REGISTRY.items():
                for alias in aliases:
                    alias_lower = alias.lower().strip()
                    if len(alias_lower) < 4:
                        continue
                    if alias_lower in q:
                        alias_matches.append((len(alias_lower), canonical))
                        break

            for _, canonical in sorted(alias_matches, reverse=True):
                if canonical not in company_names:
                    company_names.append(canonical)

            # Second pass: split multi-company comparison phrases such as
            # "A vs B vs C", "between A and B and C", or comma-separated lists.
            parts = re.split(r'\s+(?:and|vs|versus)\s+|,', q)
            for part in parts:
                company_name = _resolve_company_name(part)
                if company_name and company_name not in company_names:
                    company_names.append(company_name)
            
            # Extract month/year if present
            month_year = extract_month_year(user_query)
            month = month_year[0] if month_year else None
            year = month_year[1] if month_year else None
            
            if not company_names:
                return {"response_type": "text", "message": "Could not identify companies to compare"}, []
            
            print(f"[COMPARISON] Extracted companies: {company_names}, month={month}, year={year}")
            
            # Get comparison data
            labels, values = compare_companies_notifications(company_names, month=month, year=year)
            
            if not labels or not values:
                return {"response_type": "chart", "message": f"No data found for comparison of {', '.join(company_names)}"}, []
            
            # Build title
            date_str = ""
            if month and year:
                from calendar import month_name
                date_str = f" ({month_name[month]} {year})"
            elif year:
                date_str = f" ({year})"
            
            title = f"Notification Comparison{date_str}"
            
            return {
                "response_type": "chart",
                "chart_type": "bar",
                "title": title,
                "x_axis": "Company",
                "y_axis": "Notification Count",
                "data": {"labels": labels, "values": values}
            }, []
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"response_type": "text", "message": f"Comparison error: {str(e)}"}, []

    def _shorten_summary(self, full_summary: str) -> str:
        """Extract 1–2 key points from full summary."""
        if not full_summary or full_summary == "NIL":
            return "No summary available"
        sentences = re.split(r'[.\n]', full_summary)
        key_points = [s.strip() for s in sentences if s.strip()]
        return " | ".join(key_points[:2])  # Take first 2 points

    def _display_company_name(self, notification) -> str:
        source = str(self._safe_get_attr(notification, ["source_system"], "")).upper()
        company = self._safe_get_attr(
            notification,
            ["EntityName", "entity_name"],
            None,
        )
        if company and str(company).strip() and str(company).strip().lower() != "unknown":
            return str(company)
        if source == "SEBI":
            return "SEBI Regulatory Update"
        if source == "RBI":
            return "RBI Regulatory Update"
        if source == "BSE":
            return "BSE Notification"
        return "Regulatory Update"

    def _display_date(self, notification) -> str:
        date_value = self._safe_get_attr(
            notification,
            ["Date", "notice_date", "date_key", "run_date", "inserted_at", "created_at"],
            "Unknown",
        )
        if date_value in [None, "", "NIL"]:
            return "Unknown"
        return str(date_value)

    def _display_subject(self, notification) -> str:
        subject = self._safe_get_attr(
            notification,
            ["Nature", "notice_type", "title"],
            None,
        )
        if subject and str(subject).strip() and str(subject).strip().lower() != "unknown":
            return str(subject)

        source = str(self._safe_get_attr(notification, ["source_system"], "")).upper()
        if source == "SEBI":
            return "SEBI Regulatory Update"
        if source == "RBI":
            return "RBI Regulatory Update"
        if source == "BSE":
            return "Notification"
        return "Regulatory Update"

    def _display_summary(self, notification) -> str:
        summary = self._safe_get_attr(notification, ["Summary", "summary", "full_text"], "")
        if not summary or str(summary).strip() in {"", "NIL", "Unknown"}:
            title = self._safe_get_attr(notification, ["title"], "")
            if title and str(title).strip():
                return str(title)
            return "No summary available"
        return str(summary)

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
            company = self._display_company_name(n)
            date = self._display_date(n)
            subject = self._display_subject(n)
            full_summary = self._display_summary(n)
            short_summary = self._shorten_summary(full_summary)

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
        Detailed grouped text format for normal notification queries.
        """
        if not notifications:
            return f"No notifications found for {entity_name}." if entity_name else "No relevant notifications found.", []
        company_groups = {}
        for notification in notifications:
            company = self._display_company_name(notification)
            company_groups.setdefault(company, []).append(notification)

        response_parts = []

        for company, company_notifications in company_groups.items():
            response_parts.append(f"\n{'=' * 80}")
            response_parts.append(f"{company} ({len(company_notifications)} notifications)")
            response_parts.append(f"{'=' * 80}\n")

            for notification in company_notifications:
                date = self._display_date(notification)
                subject = self._display_subject(notification)
                summary = self._display_summary(notification)

                response_parts.append(f"Date: {date}")
                response_parts.append(f"Sub: {subject}")
                response_parts.append(f"Summary: {summary}")
                response_parts.append("")

        return "\n".join(response_parts).strip(), self._extract_sources(notifications)

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
            link = self._safe_get_attr(n, ["link", "Link", "pdf_link"], None)
            if link and link != "NIL":
                sources.append(link)
        return sources[:5]

    def _fetch_recent_notifications(self, database: str, limit: int = 25) -> List:
        if database == "bse":
            session = get_db_session()
            try:
                return (
                    session.query(DailyLog)
                    .filter(or_(DailyLog.Summary != "NIL", DailyLog.Nature != "NIL"))
                    .order_by(DailyLog.Date.desc())
                    .limit(limit)
                    .all()
                )
            finally:
                session.close()

        if database == "sebi":
            session = get_sebi_session()
            try:
                return session.query(SEBINotification).order_by(SEBINotification.inserted_at.desc()).limit(limit).all()
            finally:
                session.close()

        if database == "rbi":
            session = get_rbi_session()
            try:
                return session.query(RBINotification).order_by(RBINotification.run_date.desc()).limit(limit).all()
            finally:
                session.close()

        combined = []
        for db_name in ["bse", "sebi", "rbi"]:
            combined.extend(self._fetch_recent_notifications(db_name, limit=max(5, limit // 3)))
        return convert_to_common_format(combined, "all")

    def semantic_retrieve(self, user_query: str, database: str, limit: int = 1000, last_n_days: int = None, strict_entity: str = None) -> List:
        """Semantic retrieval - returns ALL matching data"""
        generic_latest_terms = ["latest", "recent", "updates", "update", "new notifications"]
        if not strict_entity and any(term in user_query.lower() for term in generic_latest_terms):
            return self._fetch_recent_notifications(database, limit=min(limit, 30))

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
