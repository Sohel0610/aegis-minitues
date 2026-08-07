"""Context-aware query preparation before intent routing and retrieval."""
from dataclasses import dataclass
from functools import lru_cache
import re
from typing import List, Optional


@dataclass
class PreparedQuery:
    original: str
    resolved: str
    retrieval_query: str
    sub_queries: List[str]


class QueryPreprocessor:
    def __init__(self, context_manager=None):
        self.context_manager = context_manager

    def resolve_coreferences(self, query: str, session_id: Optional[str] = None) -> str:
        if not self.context_manager or not session_id:
            return query
        # ContextManager owns the session lookup and does word-safe substitutions.
        return self.context_manager.resolve_pronouns(query, session_id)

    @staticmethod
    @lru_cache(maxsize=512)
    def _rewrite_cached(query: str) -> str:
        """Deterministic retrieval expansion; never makes network calls on the hot path."""
        result = re.sub(r"\bwhat happened with\b", "BSE notifications for", query, flags=re.I)
        result = re.sub(r"\brecently\b", "last 30 days", result, flags=re.I)
        result = re.sub(r"\bupdates?\b", "notifications", result, flags=re.I)
        return re.sub(r"\s+", " ", result).strip()

    def rewrite_for_retrieval(self, query: str) -> str:
        return self._rewrite_cached(query)

    def decompose(self, query: str) -> List[str]:
        """Split explicit multi-source requests without breaking company names."""
        if not re.search(r"\b(?:also|and also|cross-reference|combine)\b", query, re.I):
            return [query]
        chunks = re.split(r"\s+(?:and also|also|cross-reference|combine)\s+", query, flags=re.I)
        return [part.strip(" ,") for part in chunks if part.strip(" ,")] or [query]

    def prepare(self, query: str, session_id: Optional[str] = None) -> PreparedQuery:
        resolved = self.resolve_coreferences(query, session_id)
        rewritten = self.rewrite_for_retrieval(resolved)
        return PreparedQuery(query, resolved, rewritten, self.decompose(rewritten))
