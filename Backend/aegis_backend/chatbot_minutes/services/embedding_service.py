from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from ..models import Embedding, Document
from ..config import settings
from typing import List
import numpy as np
import logging
import re

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        try:
            model_path = settings.EMBEDDING_MODEL_PATH
            if not model_path or model_path == "None":
                model_path = "sentence-transformers/all-MiniLM-L6-v2"
                logger.info(f"No local model path set, using model name: {model_path}")
            else:
                logger.info(f"Loading embedding model from: {model_path}")
            
            self.model = SentenceTransformer(model_path)
            logger.info(f"Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        if not text:
            return []
        if len(text) <= chunk_size:
            return [text.strip()]
        
        # Section-aware chunking
        section_markers = ["\nAttendees:", "\nAgenda:", "\nDecisions:", "\nAction Items:",
                          "\n--- Page", "\n=== Slide", "\n=== Sheet", "\n## ", "\n# "]
        
        has_sections = any(marker in text for marker in section_markers)
        if has_sections:
            pattern = r'(?=\n(?:Attendees:|Agenda:|Decisions:|Action Items:|--- Page|=== Slide|=== Sheet|## |# ))'
            sections = re.split(pattern, text)
            chunks = []
            current_chunk = ""
            for section in sections:
                if len(current_chunk) + len(section) <= chunk_size:
                    current_chunk += section
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = section
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            return chunks

        # Fallback: character-based chunking
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start += (chunk_size - overlap)
        return chunks

    def create_document_embeddings(self, db: Session, document: Document):
        if not document.extracted_text:
            return
        
        chunks = self.chunk_text(document.extracted_text)
        for idx, chunk in enumerate(chunks):
            try:
                embedding = self.generate_embedding(chunk)
                doc_embedding = Embedding(
                    document_id=document.id,
                    chunk_text=chunk,
                    embedding_vector=embedding,
                    chunk_index=idx
                )
                db.add(doc_embedding)
            except Exception as e:
                logger.error(f"Error creating embedding for chunk {idx}: {str(e)}")
                continue
        db.commit()

    def search_similar_chunks(
        self,
        db: Session,
        query: str,
        user_id: int,
        top_k: int = 5
    ) -> List[tuple]:
        query_embedding = self.generate_embedding(query)
        
        embeddings = db.query(Embedding).join(Document).filter(
            Document.user_id == user_id
        ).all()
        
        if not embeddings:
            return []
        
        results = []
        for emb in embeddings:
            if emb.embedding_vector:
                similarity = self._cosine_similarity(query_embedding, emb.embedding_vector)
                results.append((emb.chunk_text, emb.document.filename, similarity))
        
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
