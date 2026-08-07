"""Grounding checks applied to final chatbot responses."""
from dataclasses import dataclass
from typing import Any, Iterable, List
import re
from chatbot_backend.indexing_layer.reranker import _value, reranker

@dataclass
class PostProcessResult:
    response: str
    confidence: str
    warnings: List[str]

class ResponsePostProcessor:
    def process(self, response: str, records: Iterable[Any]) -> PostProcessResult:
        records = list(records)
        source_dates = {_value(r, "notice_date", "Date", "date_key", "run_date") for r in records}
        mentioned_dates = set(re.findall(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b", response))
        warnings = [f"Date {date} in the answer was not found in retrieved source data." for date in mentioned_dates if date not in source_dates]
        warnings.extend(reranker.contradictions(records))
        if warnings:
            response = response.rstrip() + "\n\nNote: " + " ".join(warnings)
        # A compact source citation is guaranteed for grounded text responses.
        if records and "[Source:" not in response:
            citations = []
            for record in records[:5]:
                entity = _value(record, "entity_name", "EntityName") or "Regulatory record"
                date = _value(record, "notice_date", "Date", "date_key", "run_date") or "Unknown date"
                citations.append(f"[Source: {entity}, {date}]")
            response = response.rstrip() + "\n\n" + " ".join(citations)
        confidence = "CONFLICTING_DATA" if any("Conflicting" in w for w in warnings) else ("ANSWERED_FROM_DATA" if records else "INSUFFICIENT_DATA")
        return PostProcessResult(response=response, confidence=confidence, warnings=warnings)

post_processor = ResponsePostProcessor()
