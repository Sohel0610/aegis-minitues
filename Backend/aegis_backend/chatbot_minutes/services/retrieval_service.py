"""Hybrid retrieval, relevance filtering, source expansion, and read-only tools."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional
from datetime import date as date_type

from sqlalchemy.orm import Session
from sqlalchemy import extract as sql_extract, func as sql_func

from ..config import settings
from ..models import ActionItem, Agenda, Decision, Document, Embedding, MeetingMetadata
from .embedding_service import EmbeddingService


class HybridRetrievalService:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    @staticmethod
    def _tokens(text: str) -> List[str]:
        return re.findall(r"[a-z0-9][a-z0-9._%-]*", text.lower())

    def _scope(self, db: Session, user_id: int, is_admin: bool, document_ids: Optional[List[int]] = None):
        query = db.query(Embedding).join(Document)
        if not is_admin:
            query = query.filter(Document.user_id == user_id)
        if document_ids:
            query = query.filter(Embedding.document_id.in_(document_ids))
        return query

    def retrieve(
        self,
        db: Session,
        query: str,
        user_id: int,
        is_admin: bool,
        *,
        document_ids: Optional[List[int]] = None,
        top_k: Optional[int] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Get broad hybrid candidates, then retain only genuinely relevant chunks."""
        if settings.RETRIEVAL_BACKEND.lower() == "azure_ai_search":
            return self._retrieve_from_azure_ai_search(query, user_id, is_admin, document_ids, top_k)

        # Apply metadata pre-filter: narrow candidate documents before semantic search.
        filtered_doc_ids = document_ids
        if metadata_filters:
            meta_doc_ids = self._apply_metadata_prefilter(db, user_id, metadata_filters)
            if meta_doc_ids is not None:
                if filtered_doc_ids:
                    filtered_doc_ids = list(set(filtered_doc_ids) & set(meta_doc_ids))
                else:
                    filtered_doc_ids = meta_doc_ids

        rows = self._scope(db, user_id, is_admin, filtered_doc_ids).order_by(Embedding.id).limit(5000).all()
        if not rows:
            return []
        query_embedding = self.embedding_service.generate_embedding(query, input_type="search_query")
        q_tokens = self._tokens(query)
        candidates = self._hybrid_rank(rows, query_embedding, q_tokens)

        # Apply metadata topic-boost: increase relevance of chunks whose meeting topics match.
        if metadata_filters and metadata_filters.get("topic"):
            candidates = self._apply_metadata_boost(candidates, metadata_filters["topic"])

        filtered = [candidate for candidate in candidates[: settings.RETRIEVAL_CANDIDATES] if candidate["relevance"] >= settings.RETRIEVAL_MIN_RELEVANCE]
        # Do not turn a sparse exact-value question into a refusal solely because
        # its semantic score is low: keep one top lexical candidate when present.
        if not filtered and candidates and candidates[0]["lexical_score"] > 0:
            filtered = candidates[:1]
        results = []
        for candidate in filtered[: (top_k or settings.RETRIEVAL_TOP_K)]:
            row = candidate.pop("_row")
            metadata = row.chunk_metadata or {}
            expanded = self._expand_with_siblings(db, row)
            results.append({
                "text": row.chunk_text,
                "expanded_text": expanded,
                "document": row.document.filename,
                "document_id": row.document_id,
                "chunk_index": row.chunk_index,
                "location": metadata.get("location", "Document"),
                "location_type": metadata.get("location_type", "document"),
                "score": round(candidate["relevance"], 3),
                "semantic_score": round(candidate["semantic_score"], 3),
                "lexical_score": round(candidate["lexical_score"], 3),
                "excerpt": self._excerpt(row.chunk_text),
            })
        return results

    def _apply_metadata_prefilter(
        self, db: Session, user_id: int, filters: Dict[str, Any],
    ) -> Optional[List[int]]:
        """Return document IDs matching the metadata filters, or None if no filter applies."""
        query = db.query(MeetingMetadata.document_id).filter(MeetingMetadata.user_id == user_id)
        applied = False

        if filters.get("meeting_type"):
            query = query.filter(MeetingMetadata.meeting_type == filters["meeting_type"])
            applied = True

        if filters.get("month"):
            query = query.filter(sql_extract("month", MeetingMetadata.meeting_date) == int(filters["month"]))
            applied = True

        if filters.get("participant"):
            # JSON field search: look for the participant name in the JSON array.
            participant = filters["participant"].lower()
            query = query.filter(
                sql_func.lower(sql_func.cast(MeetingMetadata.participants, db.bind.dialect.name == 'postgresql' and 'TEXT' or 'VARCHAR'))
                .contains(participant)
            )
            applied = True

        if not applied:
            return None

        result = query.all()
        return [row[0] for row in result] if result else []

    @staticmethod
    def _apply_metadata_boost(
        candidates: List[Dict[str, Any]], topic: str,
    ) -> List[Dict[str, Any]]:
        """Soft-boost candidates whose chunk metadata key_topics overlap with the query topic."""
        topic_lower = topic.lower()
        topic_tokens = set(re.findall(r"[a-z0-9]+", topic_lower))
        for candidate in candidates:
            row = candidate.get("_row")
            if row:
                meta = row.chunk_metadata or {}
                chunk_topics = meta.get("key_topics", [])
                if isinstance(chunk_topics, list):
                    for ct in chunk_topics:
                        ct_tokens = set(re.findall(r"[a-z0-9]+", ct.lower()))
                        overlap = len(topic_tokens & ct_tokens) / max(len(topic_tokens), 1)
                        if overlap > 0.4:
                            candidate["relevance"] = min(1.0, candidate["relevance"] + 0.1)
                            break
        return sorted(candidates, key=lambda c: c["relevance"], reverse=True)

    def _retrieve_from_azure_ai_search(
        self,
        query: str,
        user_id: int,
        is_admin: bool,
        document_ids: Optional[List[int]],
        top_k: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Production hybrid retrieval against the documented Minutes index contract.

        The Azure index must filter by the authenticated owner field. This method
        deliberately fails closed if the index/client is not configured.
        """
        if not all([settings.AZURE_SEARCH_ENDPOINT, settings.AZURE_SEARCH_API_KEY, settings.AZURE_SEARCH_INDEX]):
            raise ValueError("Azure AI Search is selected but endpoint, key, or index is missing")
        try:
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents import SearchClient
            from azure.search.documents.models import VectorizedQuery
        except ImportError as exc:
            raise ValueError("Install azure-search-documents to use Azure AI Search retrieval") from exc
        vector = self.embedding_service.generate_embedding(query, input_type="search_query")
        vector_query = VectorizedQuery(vector=vector, k_nearest_neighbors=settings.RETRIEVAL_CANDIDATES, fields=settings.AZURE_SEARCH_VECTOR_FIELD)
        filters = []
        if not is_admin:
            filters.append(f"{settings.AZURE_SEARCH_OWNER_FIELD} eq '{int(user_id)}'")
        if document_ids:
            filters.append("(" + " or ".join(f"document_id eq {int(document_id)}" for document_id in document_ids) + ")")
        client = SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name=settings.AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(settings.AZURE_SEARCH_API_KEY),
        )
        select = ["document_id", "filename", "chunk_index", "location", settings.AZURE_SEARCH_CONTENT_FIELD]
        response = client.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=" and ".join(filters) or None,
            select=select,
            top=top_k or settings.RETRIEVAL_TOP_K,
        )
        results = []
        for item in response:
            content = item.get(settings.AZURE_SEARCH_CONTENT_FIELD, "")
            score = float(item.get("@search.reranker_score") or item.get("@search.score") or 0)
            results.append({
                "text": content,
                "expanded_text": content,
                "document": item.get("filename", "Document"),
                "document_id": int(item.get("document_id", 0)),
                "chunk_index": int(item.get("chunk_index", 0)),
                "location": item.get("location", "Document"),
                "location_type": "indexed",
                "score": round(score, 3),
                "semantic_score": round(score, 3),
                "lexical_score": 0,
                "excerpt": self._excerpt(content),
            })
        return results

    def _hybrid_rank(self, rows: List[Embedding], query_embedding: List[float], q_tokens: List[str]) -> List[Dict[str, Any]]:
        tokenized = [self._tokens(row.chunk_text) for row in rows]
        document_frequency = Counter(token for tokens in tokenized for token in set(tokens))
        average_length = max(sum(len(tokens) for tokens in tokenized) / len(rows), 1)
        semantic, lexical = [], []
        for index, (row, tokens) in enumerate(zip(rows, tokenized)):
            semantic_score = self.embedding_service._cosine_similarity(query_embedding, row.embedding_vector or [])
            counts = Counter(tokens)
            bm25 = 0.0
            for token in q_tokens:
                if not counts[token]:
                    continue
                idf = math.log(1 + (len(rows) - document_frequency[token] + 0.5) / (document_frequency[token] + 0.5))
                bm25 += idf * counts[token] * 2.0 / (counts[token] + 1.2 * (1 - 0.75 + 0.75 * len(tokens) / average_length))
            semantic.append((index, semantic_score))
            lexical.append((index, bm25))
        semantic_rank = sorted(semantic, key=lambda item: item[1], reverse=True)
        lexical_rank = sorted(lexical, key=lambda item: item[1], reverse=True)
        reciprocal = Counter()
        for ranking in (semantic_rank, lexical_rank):
            for rank, (index, _) in enumerate(ranking[: settings.RETRIEVAL_CANDIDATES * 2], 1):
                reciprocal[index] += 1 / (60 + rank)
        max_bm25 = max((score for _, score in lexical), default=1.0) or 1.0
        output = []
        for index, row in enumerate(rows):
            semantic_score = semantic[index][1]
            lexical_score = lexical[index][1]
            coverage = sum(1 for token in set(q_tokens) if token in set(tokenized[index])) / max(len(set(q_tokens)), 1)
            # Reranker: semantic relevance + exact term coverage + keyword score.
            relevance = max(0.0, 0.55 * max(semantic_score, 0) + 0.3 * coverage + 0.15 * min(lexical_score / max_bm25, 1))
            output.append({
                "_row": row,
                "relevance": relevance,
                "semantic_score": semantic_score,
                "lexical_score": lexical_score,
                "rrf_score": reciprocal[index],
            })
        return sorted(output, key=lambda item: (item["relevance"], item["rrf_score"]), reverse=True)

    @staticmethod
    def _excerpt(text: str, limit: int = 360) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        return compact if len(compact) <= limit else compact[: limit - 1].rstrip() + "…"

    @staticmethod
    def _expand_with_siblings(db: Session, row: Embedding) -> str:
        siblings = db.query(Embedding).filter(
            Embedding.document_id == row.document_id,
            Embedding.chunk_index >= max((row.chunk_index or 0) - 1, 0),
            Embedding.chunk_index <= (row.chunk_index or 0) + 1,
        ).order_by(Embedding.chunk_index.asc()).all()
        return "\n\n".join(item.chunk_text for item in siblings) if siblings else row.chunk_text

    def run_tools(
        self,
        db: Session,
        requested_tools: Iterable[str],
        user_id: int,
        is_admin: bool,
        document_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        scope = {} if is_admin else {"user_id": user_id}
        tools = set(requested_tools)
        results: List[Dict[str, Any]] = []
        if "list_action_items" in tools:
            for row in db.query(ActionItem).filter_by(**scope).order_by(ActionItem.created_at.desc()).limit(20):
                results.append({"tool": "list_action_items", "text": f"{row.task_description} (owner: {row.assignee or 'unassigned'}, status: {row.status})"})
        if "list_decisions" in tools:
            for row in db.query(Decision).filter_by(**scope).order_by(Decision.created_at.desc()).limit(20):
                results.append({"tool": "list_decisions", "text": row.decision_text})
        if "list_agendas" in tools:
            for row in db.query(Agenda).filter_by(**scope).order_by(Agenda.created_at.desc()).limit(20):
                results.append({"tool": "list_agendas", "text": f"{row.agenda_title}: {row.agenda_content or ''}"})
        if "document_catalog" in tools:
            document_query = db.query(Document)
            if not is_admin:
                document_query = document_query.filter(Document.user_id == user_id)
            if document_ids:
                document_query = document_query.filter(Document.id.in_(document_ids))
            for row in document_query.order_by(Document.upload_date.desc()).limit(50):
                results.append({"tool": "document_catalog", "text": f"{row.filename} ({row.file_type}, {row.processing_status or 'unknown'})"})
        if "meeting_context_search" in tools:
            meta_query = db.query(MeetingMetadata).filter(MeetingMetadata.user_id == user_id)
            if document_ids:
                meta_query = meta_query.filter(MeetingMetadata.document_id.in_(document_ids))
            for row in meta_query.order_by(MeetingMetadata.meeting_date.desc().nullslast()).limit(30):
                parts = []
                if row.meeting_title:
                    parts.append(f"Title: {row.meeting_title}")
                if row.meeting_date:
                    parts.append(f"Date: {row.meeting_date.isoformat()}")
                if row.meeting_type:
                    parts.append(f"Type: {row.meeting_type.replace('_', ' ').title()}")
                if row.company_name:
                    parts.append(f"Company: {row.company_name}")
                if row.chairperson:
                    parts.append(f"Chair: {row.chairperson}")
                if row.participants:
                    names = [p.get("name", "") for p in (row.participants or [])[:5] if p.get("name")]
                    if names:
                        parts.append(f"Participants: {', '.join(names)}")
                if row.key_topics:
                    parts.append(f"Topics: {', '.join(row.key_topics[:5])}")
                if row.meeting_summary:
                    parts.append(f"Summary: {row.meeting_summary[:300]}")
                if parts:
                    results.append({"tool": "meeting_context_search", "text": " | ".join(parts)})
        return results

    @staticmethod
    def detect_potential_conflicts(chunks: List[Dict[str, Any]]) -> List[str]:
        """Conservative indicator only; the answer must label it as a potential conflict."""
        conflicts = []
        corpus = " ".join(chunk.get("text", "").lower() for chunk in chunks)
        pairs = (("unmodified", "modified"), ("approved", "not approved"), ("completed", "not completed"))
        for left, right in pairs:
            if left in corpus and right in corpus:
                conflicts.append(f"Potentially conflicting language found: '{left}' and '{right}'.")
        return conflicts
