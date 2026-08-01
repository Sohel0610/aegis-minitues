"""Orchestrates planning, memory, retrieval, grounded generation, and verification."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..config import settings
from .chat_history_service import ChatHistoryService
from .embedding_service import EmbeddingService
from .grounding_service import GroundingService
from .llm_service import LLMService, LLMUnavailableError
from .query_planner import QueryPlanner
from .retrieval_service import HybridRetrievalService

logger = logging.getLogger(__name__)


class ChatbotService:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.retrieval_service = HybridRetrievalService(self.embedding_service)
        self.chat_history_service = ChatHistoryService()
        self.llm_service = LLMService()
        self.query_planner = QueryPlanner(self.llm_service)

    def process_query(
        self,
        db: Session,
        user_id: int,
        query: str,
        session_id: str,
        is_admin: bool = False,
        document_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        clean_query = query.strip()
        summary, recent_history = self.chat_history_service.get_memory_context(
            db, user_id, session_id, settings.HISTORY_RECENT_TURNS,
        )
        self.chat_history_service.save_message(db, user_id, session_id, "user", clean_query)
        plan = self.query_planner.build(clean_query, recent_history, summary)
        if not plan.entities:
            plan.entities = self.chat_history_service.extract_basic_entities(clean_query)
        self.chat_history_service.remember_entities(db, user_id, plan.entities)

        chunks = self._retrieve_for_plan(db, plan, user_id, is_admin, document_ids)
        tool_results = self.retrieval_service.run_tools(db, plan.tools, user_id, is_admin, document_ids)
        conflicts = self.retrieval_service.detect_potential_conflicts(chunks)
        context = self._build_context(chunks, tool_results, conflicts)
        answer, model_info = self._generate_answer(clean_query, plan, context, summary, recent_history, bool(chunks or tool_results))
        answer = self._remove_inline_citations(answer)
        assessment = GroundingService.assess(answer, chunks, tool_results, conflicts)
        assessment = self._optional_faithfulness_check(clean_query, answer, context, assessment)
        sources = [
            {
                "document_id": chunk["document_id"],
                "document": chunk["document"],
                "chunk_index": chunk["chunk_index"],
                "location": chunk["location"],
                "excerpt": chunk["excerpt"],
                "similarity": chunk["score"],
            }
            for chunk in chunks[:3]
        ]
        metadata = {
            "sources": sources,
            "retrieval_mode": plan.retrieval_mode,
            "confidence": assessment.as_dict(),
            "response_format": plan.response_format,
            "model": model_info,
            "document_ids": document_ids or [],
        }
        self.chat_history_service.save_message(
            db, user_id, session_id, "assistant", answer, response_metadata=metadata,
        )
        self._refresh_session_summary(db, user_id, session_id)
        return {
            "answer": answer,
            "sources": sources,
            "retrieval_mode": plan.retrieval_mode,
            "response_format": plan.response_format,
            "confidence": assessment.as_dict(),
            # Safe operational trace, deliberately not hidden chain-of-thought.
            "activity": self._activity(plan, chunks, tool_results, assessment),
            "session_id": session_id,
        }

    def _retrieve_for_plan(self, db: Session, plan, user_id: int, is_admin: bool, document_ids: Optional[List[int]]) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        seen = set()
        for search_query in [plan.rewritten_query] + plan.sub_questions[:2]:
            for chunk in self.retrieval_service.retrieve(
                db, search_query, user_id, is_admin, document_ids=document_ids, top_k=settings.RETRIEVAL_TOP_K,
            ):
                identity = (chunk["document_id"], chunk["chunk_index"])
                if identity not in seen:
                    merged.append(chunk)
                    seen.add(identity)
        return sorted(merged, key=lambda chunk: chunk["score"], reverse=True)[: settings.RETRIEVAL_TOP_K]

    def _build_context(self, chunks: List[Dict[str, Any]], tool_results: List[Dict[str, Any]], conflicts: List[str]) -> str:
        pieces: List[str] = []
        for index, chunk in enumerate(chunks, 1):
            pieces.append(
                f"[Evidence {index}: {chunk['document']} — {chunk['location']}]\n{chunk['expanded_text']}"
            )
        for result in tool_results:
            pieces.append(f"[Structured record: {result['tool']}]\n{result['text']}")
        if conflicts:
            pieces.append("[Evidence review]\n" + "\n".join(conflicts))
        context = "\n\n".join(pieces)
        return context[: settings.MAX_CONTEXT_CHARS]

    def _generate_answer(self, query: str, plan, context: str, summary: Optional[str], history: List[Any], has_evidence: bool) -> tuple[str, Dict[str, str]]:
        system_prompt = """You are Aegis Meeting Assistant for enterprise governance, finance, and corporate records.
Answer from supplied evidence and structured records only. Do not invent facts, figures, dates, legal conclusions, or actions.
Do not include source labels, page numbers, chunk numbers, or citations in the prose: the UI renders verified evidence separately.
If evidence is absent or insufficient, say what was searched, state that you cannot verify the answer, and give one focused next step.
When evidence may conflict, label it as a potential conflict and do not choose a side without support.
Do not claim to have sent email, changed records, accessed a database, or called an external system unless a tool result explicitly proves it.
Use concise business language. For comparison_table, use a Markdown table. For bullet_list, use bullets. For concise_answer, use 2–5 short paragraphs."""
        history_payload = "\n".join(f"{item.role}: {item.message}" for item in history[-settings.HISTORY_RECENT_TURNS * 2 :])
        user_payload = f"""REQUEST: {query}
RESPONSE FORMAT: {plan.response_format}
RETRIEVAL MODE: {plan.retrieval_mode}
SESSION SUMMARY: {summary or 'None'}
RECENT CONVERSATION: {history_payload or 'None'}
EVIDENCE AVAILABLE: {'yes' if has_evidence else 'no'}
EVIDENCE:
{context or 'No matching evidence was found in the selected documents.'}"""
        try:
            result = self.llm_service.generate(
                [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_payload}],
                temperature=0.2,
            )
            return result.content, {"provider": result.provider, "model": result.model}
        except LLMUnavailableError:
            if not has_evidence:
                return (
                    "I could not reach the configured language model, and no matching document evidence is available yet. "
                    "Upload a document or check the local Groq/Azure model configuration.",
                    {"provider": "unavailable", "model": ""},
                )
            return (
                "I found relevant evidence, but the configured language model is currently unavailable. "
                "Please retry after checking the model connection.",
                {"provider": "unavailable", "model": ""},
            )

    @staticmethod
    def _remove_inline_citations(answer: str) -> str:
        answer = re.sub(r"\s*\[\s*(?:source|evidence)\s*\d+\s*:[^\]]*\]", "", answer, flags=re.IGNORECASE)
        return re.sub(r"[ \t]+\n", "\n", answer).strip()

    def _optional_faithfulness_check(self, query: str, answer: str, context: str, assessment):
        if not settings.ENABLE_LLM_FAITHFULNESS_CHECK or not context:
            return assessment
        try:
            result, _ = self.llm_service.generate_json([
                {"role": "system", "content": "Judge whether an answer is supported only by evidence. Return JSON: {supported: boolean, reason: string}."},
                {"role": "user", "content": f"Question: {query}\nAnswer: {answer}\nEvidence: {context[:8000]}"},
            ], max_tokens=250)
            if result.get("supported") is False:
                assessment.confidence = "low"
                assessment.reason = "The answer needs review because evidence support could not be confirmed."
        except Exception:
            pass
        return assessment

    def _refresh_session_summary(self, db: Session, user_id: int, session_id: str) -> None:
        history = self.chat_history_service.get_session_history(db, user_id, session_id, limit=100)
        if len(history) <= settings.SESSION_SUMMARY_TURN_THRESHOLD:
            return
        existing_summary, _ = self.chat_history_service.get_memory_context(db, user_id, session_id, settings.HISTORY_RECENT_TURNS)
        try:
            result = self.llm_service.generate([
                {"role": "system", "content": "Summarise this enterprise chat in at most 5 neutral factual bullets. Preserve open questions, decisions, entities, dates, and document references. Do not invent facts."},
                {"role": "user", "content": "Previous summary:\n" + (existing_summary or "None") + "\n\nConversation:\n" + "\n".join(f"{item.role}: {item.message}" for item in history)},
            ], temperature=0, max_tokens=450)
            summary = result.content
        except Exception:
            summary = "Recent conversation topics: " + "; ".join(item.message[:160] for item in history[-6:])
        self.chat_history_service.upsert_session_summary(db, user_id, session_id, summary, history[-1].id)

    @staticmethod
    def _activity(plan, chunks: List[Dict[str, Any]], tool_results: List[Dict[str, Any]], assessment) -> List[str]:
        steps = ["Understanding your request", "Searching selected documents"]
        if plan.retrieval_mode == "agentic_rag":
            steps.append("Comparing retrieved evidence")
        if tool_results:
            steps.append("Checking structured records")
        steps.append("Verifying evidence" if assessment.evidence_found else "No matching evidence found")
        return steps
