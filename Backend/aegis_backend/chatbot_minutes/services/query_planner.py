"""Query understanding, lightweight planning, and safe heuristic fallback."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .llm_service import LLMService
from ..config import settings


@dataclass
class QueryPlan:
    intent: str = "document_question"
    retrieval_mode: str = "hybrid_rag"
    rewritten_query: str = ""
    sub_questions: List[str] = field(default_factory=list)
    entities: List[Dict[str, str]] = field(default_factory=list)
    date_scope: Optional[str] = None
    response_format: str = "concise_answer"
    tools: List[str] = field(default_factory=list)
    requires_comparison: bool = False
    has_coreference: bool = False
    planner_used: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


class QueryPlanner:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def build(self, query: str, history: List[Any], session_summary: Optional[str] = None) -> QueryPlan:
        fallback = self._heuristic_plan(query, history)
        if not settings.ENABLE_LLM_QUERY_PLANNER:
            return fallback
        prompt = self._planner_prompt(query, history, session_summary)
        try:
            payload, _ = self.llm_service.generate_json(prompt, max_tokens=800)
            return self._normalise(payload, query, fallback)
        except Exception:
            return fallback

    @staticmethod
    def _heuristic_plan(query: str, history: List[Any]) -> QueryPlan:
        q = query.lower().strip()
        comparison = any(term in q for term in ("compare", "difference", "versus", "vs", "trend", "risk", "impact", "contradict"))
        structured_terms = {
            "list_action_items": ("action item", "actions", "owner", "assignee"),
            "list_decisions": ("decision", "decided", "resolution"),
            "list_agendas": ("agenda", "agenda item"),
        }
        tools = [name for name, terms in structured_terms.items() if any(term in q for term in terms)]
        mode = "agentic_rag" if comparison or len(tools) > 1 else ("structured_plus_rag" if tools else "hybrid_rag")
        response_format = "comparison_table" if comparison else ("bullet_list" if tools or q.startswith(("list", "show all")) else "concise_answer")
        coreference = bool(re.search(r"\b(it|they|that|this|those|the last one)\b", q))
        rewritten = query
        if coreference and history:
            previous_user = next((getattr(item, "message", "") for item in reversed(history) if getattr(item, "role", "") == "user"), "")
            if previous_user:
                rewritten = f"{query} Context from the preceding user request: {previous_user}"
        entities = []
        for value in re.findall(r"\b(?:SEBI|RBI|BSE|MCA|DIN|Adani(?:\s+[A-Z][A-Za-z]+){0,3})\b", query):
            entities.append({"type": "organisation", "value": value})
        date_match = re.search(r"\b(?:last\s+(?:week|month|quarter|year)|FY\s?\d{2,4}(?:-\d{2,4})?|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", query, re.I)
        return QueryPlan(
            intent="comparison" if comparison else ("structured_lookup" if tools else "document_question"),
            retrieval_mode=mode,
            rewritten_query=rewritten,
            sub_questions=[query],
            entities=entities,
            date_scope=date_match.group(0) if date_match else None,
            response_format=response_format,
            tools=tools,
            requires_comparison=comparison,
            has_coreference=coreference,
        )

    @staticmethod
    def _planner_prompt(query: str, history: List[Any], session_summary: Optional[str]) -> List[Dict[str, str]]:
        recent = [{"role": getattr(item, "role", "user"), "message": getattr(item, "message", "")[:1000]} for item in history[-6:]]
        system = """You are the query planner for an enterprise document assistant. Plan retrieval only; do not answer the user.
Return JSON with exactly: intent, retrieval_mode, rewritten_query, sub_questions, entities, date_scope, response_format, tools, requires_comparison, has_coreference.
retrieval_mode must be hybrid_rag, agentic_rag, or structured_plus_rag.
tools may only contain list_action_items, list_decisions, list_agendas, document_catalog.
Use a comparison_table response format for comparisons, bullet_list for lists, concise_answer otherwise.
Resolve pronouns only using the supplied conversation. Never create facts or entities not present in the request/history."""
        payload = {"query": query, "session_summary": session_summary or "", "recent_history": recent}
        return [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]

    @staticmethod
    def _normalise(payload: Dict[str, Any], query: str, fallback: QueryPlan) -> QueryPlan:
        valid_modes = {"hybrid_rag", "agentic_rag", "structured_plus_rag"}
        valid_tools = {"list_action_items", "list_decisions", "list_agendas", "document_catalog"}
        mode = payload.get("retrieval_mode") if payload.get("retrieval_mode") in valid_modes else fallback.retrieval_mode
        tools = [tool for tool in payload.get("tools", []) if tool in valid_tools] if isinstance(payload.get("tools"), list) else fallback.tools
        entities = [entity for entity in payload.get("entities", []) if isinstance(entity, dict) and entity.get("value")][:12]
        sub_questions = [str(item)[:500] for item in payload.get("sub_questions", []) if str(item).strip()][:5] or [query]
        response_format = payload.get("response_format") if payload.get("response_format") in {"comparison_table", "bullet_list", "concise_answer", "analysis"} else fallback.response_format
        return QueryPlan(
            intent=str(payload.get("intent") or fallback.intent)[:100],
            retrieval_mode=mode,
            rewritten_query=str(payload.get("rewritten_query") or query)[:2000],
            sub_questions=sub_questions,
            entities=entities or fallback.entities,
            date_scope=str(payload.get("date_scope") or fallback.date_scope or "")[:200] or None,
            response_format=response_format,
            tools=tools,
            requires_comparison=bool(payload.get("requires_comparison", fallback.requires_comparison)),
            has_coreference=bool(payload.get("has_coreference", fallback.has_coreference)),
            planner_used=True,
        )
