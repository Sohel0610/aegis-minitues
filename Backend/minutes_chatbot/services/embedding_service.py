"""
Embedding Service

Generates vector embeddings using local sentence-transformers model.
Uses all-MiniLM-L6-v2 (384 dimensions) loaded from local path.
"""

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from minutes_chatbot.database.models import Embedding, Document
from minutes_chatbot.config import settings, logger
from typing import List
import numpy as np


class EmbeddingService:
    """Service for generating and managing embeddings using local model"""
    
    def __init__(self):
        """Initialize local sentence-transformers model from local path"""
        try:
            # Use model name if path is None or doesn't exist
            model_path = settings.EMBEDDING_MODEL_PATH
            if not model_path or model_path == "None":
                model_path = "sentence-transformers/all-MiniLM-L6-v2"
                logger.info(f"No local model path set, downloading model: {model_path}")
            else:
                logger.info(f"Loading embedding model from: {model_path}")
            
            self.model = SentenceTransformer(model_path)
            logger.info(f"✅ Embedding model loaded successfully (dimension: {self.model.get_sentence_embedding_dimension()})")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using local sentence-transformers.
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector (list of floats)
        """
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Convert to list
            embedding_list = embedding.tolist()
            
            logger.debug(f"Generated embedding for text (length: {len(text)})")
            return embedding_list
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Split text into overlapping chunks, preserving logical sections.
        
        Args:
            text: Input text
            chunk_size: Size of each chunk (in characters)
            overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        # If text is small enough, return as single chunk
        if len(text) <= chunk_size:
            if text.strip():
                return [text.strip()]
            return []
        
        # Try to split on section boundaries first (for structured text like JSON)
        section_markers = ["\nAttendees:", "\nAgenda:", "\nDecisions:", "\nAction Items:",
                          "\n--- Page", "\n=== Slide", "\n=== Sheet", "\n## ", "\n# "]
        
        # Check if text has section markers
        has_sections = any(marker in text for marker in section_markers)
        
        if has_sections:
            # Section-aware chunking: split on section boundaries
            chunks = []
            # Split text into sections
            import re
            pattern = r'(?=\n(?:Attendees:|Agenda:|Decisions:|Action Items:|--- Page|=== Slide|=== Sheet|## |# ))'
            sections = re.split(pattern, text)
            
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
            
            if chunks:
                logger.info(f"Split text into {len(chunks)} section-aware chunks")
                return chunks
        
        # Fallback: standard character-based chunking with overlap
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start += (chunk_size - overlap)
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def create_document_embeddings(self, db: Session, document: Document):
        """
        Create embeddings for a document.
        
        Args:
            db: Database session
            document: Document object
        """
        if not document.extracted_text:
            logger.warning(f"No extracted text for document {document.id}")
            return
        
        # Split text into chunks
        chunks = self.chunk_text(document.extracted_text)
        
        # Generate embeddings for each chunk
        for idx, chunk in enumerate(chunks):
            try:
                embedding = self.generate_embedding(chunk)
                
                # Save to database
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
        logger.info(f"Created {len(chunks)} embeddings for document {document.id}")
    
    def search_similar_chunks(
        self,
        db: Session,
        query: str,
        user_id: int,
        top_k: int = 5
    ) -> List[tuple]:
        """
        Search for similar document chunks using semantic search.
        
        Args:
            db: Database session
            query: Search query
            user_id: User ID (to filter documents)
            top_k: Number of results to return
        
        Returns:
            List of tuples (chunk_text, document_filename, similarity_score)
        """
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Get all embeddings for user's documents
        embeddings = db.query(Embedding).join(Document).filter(
            Document.user_id == user_id
        ).all()
        
        if not embeddings:
            logger.warning(f"No embeddings found for user {user_id}")
            return []
        
        # Calculate cosine similarity
        results = []
        for emb in embeddings:
            if emb.embedding_vector:
                similarity = self._cosine_similarity(query_embedding, emb.embedding_vector)
                results.append((emb.chunk_text, emb.document.filename, similarity))
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x[2], reverse=True)
        top_results = results[:top_k]
        
        logger.info(f"Found {len(top_results)} similar chunks for query: {query[:50]}...")
        return top_results
    
    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
