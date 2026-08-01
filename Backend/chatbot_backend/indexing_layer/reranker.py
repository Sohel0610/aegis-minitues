"""CPU re-ranking and source-conflict detection for retrieved notifications."""
from typing import Any, Dict, Iterable, List, Tuple
import re


def _value(item: Any, *names: str) -> str:
    if isinstance(item, dict):
        return str(next((item.get(n) for n in names if item.get(n) is not None), ""))
    return str(next((getattr(item, n, None) for n in names if getattr(item, n, None) is not None), ""))


class ReRanker:
    def __init__(self) -> None:
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", local_files_only=True)
            except Exception:
                self._model = False
        return self._model

    def rank(self, query: str, rows: List[Any], minimum_score: float = 0.4, limit: int = 40) -> List[Any]:
        rows = rows[:limit]
        model = self._get_model()
        if not rows or not model:
            return rows
        texts = [f"{_value(row, 'entity_name', 'EntityName')} {_value(row, 'Nature', 'notice_type', 'title')} {_value(row, 'Summary', 'summary', 'full_text')}" for row in rows]
        scores = model.predict([(query, text) for text in texts])
        # Cross-encoder scores are unbounded; sigmoid yields a stable 0..1 cutoff.
        ranked = sorted(zip(rows, scores), key=lambda pair: pair[1], reverse=True)
        return [row for row, score in ranked if 1 / (1 + __import__('math').exp(-float(score))) >= minimum_score]

    def contradictions(self, rows: Iterable[Any]) -> List[str]:
        groups: Dict[Tuple[str, str], List[str]] = {}
        for row in rows:
            key = (_value(row, "entity_name", "EntityName").lower(), _value(row, "notice_date", "Date", "date_key", "run_date"))
            groups.setdefault(key, []).append(_value(row, "summary", "Summary", "full_text").lower())
        conflicts = []
        for (entity, date), summaries in groups.items():
            joined = " ".join(summaries)
            if len(summaries) > 1 and re.search(r"\b(?:approved|accepted)\b", joined) and re.search(r"\b(?:deferred|rejected|cancelled)\b", joined):
                conflicts.append(f"Conflicting source records for {entity or 'unknown entity'} on {date}.")
        return conflicts


reranker = ReRanker()
