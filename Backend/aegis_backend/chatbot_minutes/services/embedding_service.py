"""Embedding and source-aware chunking for local and Azure VM modes."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Tuple

import numpy as np
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Document, Embedding

logger = logging.getLogger(__name__)


class EmbeddingService:
    _local_models: Dict[str, Any] = {}
    _cohere_client: Any = None

    def __init__(self) -> None:
        self.provider = settings.EMBEDDING_PROVIDER.strip().lower()
        if self.provider in {"sentence_transformer", "sentence-transformer", "local"}:
            self._load_local_model()
        elif self.provider not in {"cohere", "cohere_azure", "azure_cohere"}:
            raise ValueError(f"Unsupported embedding provider: {settings.EMBEDDING_PROVIDER}")

    def _load_local_model(self) -> None:
        model_path = settings.EMBEDDING_MODEL_PATH or "sentence-transformers/all-MiniLM-L6-v2"
        if model_path not in self._local_models:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading local embedding model: %s", model_path)
            self._local_models[model_path] = SentenceTransformer(model_path)
        self.model = self._local_models[model_path]

    def _get_cohere_client(self):
        if self._cohere_client is not None:
            return self._cohere_client
        if not all([settings.COHERE_API_KEY, settings.COHERE_AZURE_ENDPOINT]):
            raise ValueError("COHERE_API_KEY and COHERE_AZURE_ENDPOINT are required for Azure Cohere embeddings")
        try:
            import cohere
        except ImportError as exc:
            raise ValueError("Install the 'cohere' package to use Azure Cohere embeddings") from exc
        self.__class__._cohere_client = cohere.ClientV2(
            api_key=settings.COHERE_API_KEY,
            base_url=settings.COHERE_AZURE_ENDPOINT,
        )
        return self._cohere_client

    def generate_embedding(self, text: str, *, input_type: str = "search_document") -> List[float]:
        cleaned = text.strip()
        if not cleaned:
            return []
        if self.provider in {"sentence_transformer", "sentence-transformer", "local"}:
            return self.model.encode(cleaned, convert_to_numpy=True, normalize_embeddings=True).tolist()
        client = self._get_cohere_client()
        response = client.embed(
            model=settings.COHERE_EMBED_MODEL,
            texts=[cleaned],
            input_type=input_type,
            embedding_types=["float"],
            output_dimension=settings.COHERE_EMBED_DIMENSIONS,
        )
        vectors = getattr(getattr(response, "embeddings", None), "float", None)
        if not vectors:
            raise ValueError("Azure Cohere returned no float embedding")
        return list(vectors[0])

    @staticmethod
    def chunk_text_with_metadata(text: str, chunk_size: int = 1400, overlap: int = 180) -> List[Tuple[str, Dict[str, Any]]]:
        """Keep page/slide/sheet boundaries intact before splitting long sections."""
        if not text or not text.strip():
            return []
        marker = re.compile(r"(?=^(?:--- Page \d+.*---|=== Slide \d+ ===|=== Sheet: .* ===|=== Word document ===|=== Image OCR ===))", re.MULTILINE)
        sections = [section.strip() for section in marker.split(text) if section.strip()]
        if not sections:
            sections = [text.strip()]
        chunks: List[Tuple[str, Dict[str, Any]]] = []
        for section in sections:
            metadata = EmbeddingService._source_metadata(section)
            if len(section) <= chunk_size:
                chunks.append((section, metadata))
                continue
            chunks.extend((piece, {**metadata, "continued": True}) for piece in EmbeddingService._split_long_text(section, chunk_size, overlap))
        return chunks

    @staticmethod
    def _split_long_text(text: str, chunk_size: int, overlap: int) -> List[str]:
        words = text.split()
        pieces, current, current_length = [], [], 0
        for word in words:
            length = len(word) + 1
            if current and current_length + length > chunk_size:
                pieces.append(" ".join(current))
                overlap_words, overlap_length = [], 0
                for previous in reversed(current):
                    overlap_length += len(previous) + 1
                    if overlap_length > overlap:
                        break
                    overlap_words.append(previous)
                current = list(reversed(overlap_words))
                current_length = sum(len(item) + 1 for item in current)
            current.append(word)
            current_length += length
        if current:
            pieces.append(" ".join(current))
        return pieces

    @staticmethod
    def _source_metadata(text: str) -> Dict[str, Any]:
        first_line = text.splitlines()[0] if text.splitlines() else ""
        page = re.search(r"--- Page (\d+)", first_line)
        slide = re.search(r"=== Slide (\d+) ===", first_line)
        sheet = re.search(r"=== Sheet: (.*) ===", first_line)
        if page:
            return {"location_type": "page", "location": f"Page {page.group(1)}", "page": int(page.group(1))}
        if slide:
            return {"location_type": "slide", "location": f"Slide {slide.group(1)}", "slide": int(slide.group(1))}
        if sheet:
            return {"location_type": "sheet", "location": f"Sheet: {sheet.group(1)}", "sheet": sheet.group(1)}
        return {"location_type": "document", "location": "Document"}

    def create_document_embeddings(self, db: Session, document: Document) -> int:
        if not document.extracted_text:
            return 0
        db.query(Embedding).filter(Embedding.document_id == document.id).delete(synchronize_session=False)
        chunks = self.chunk_text_with_metadata(document.extracted_text)
        created = 0
        for index, (chunk, metadata) in enumerate(chunks):
            try:
                db.add(Embedding(
                    document_id=document.id,
                    chunk_text=chunk,
                    embedding_vector=self.generate_embedding(chunk, input_type="search_document"),
                    chunk_index=index,
                    chunk_metadata=metadata,
                ))
                created += 1
            except Exception as exc:
                logger.error("Embedding failed for document %s chunk %s: %s", document.id, index, type(exc).__name__)
                raise
        db.commit()
        return created

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        left, right = np.array(vec1), np.array(vec2)
        denominator = np.linalg.norm(left) * np.linalg.norm(right)
        return float(np.dot(left, right) / denominator) if denominator else 0.0
