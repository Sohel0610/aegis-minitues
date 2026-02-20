"""
Local Chatbot Service with Groq LLM

Modified version for local testing with Groq API instead of Azure OpenAI.
"""

from groq import Groq
from sqlalchemy.orm import Session
from minutes_chatbot.services.embedding_service import EmbeddingService
from minutes_chatbot.services.chat_history_service import ChatHistoryService
from minutes_chatbot.config.settings import settings
from minutes_chatbot.config.logging_config import logger
from typing import Dict, List
import os


class LocalChatbotService:
    """Service for RAG-based chatbot using Groq LLM"""
    
    def __init__(self):
        """Initialize Groq client and embedding service"""
        # Initialize Groq client
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=groq_api_key)
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.embedding_service = EmbeddingService()
        self.chat_history_service = ChatHistoryService()
    
    def process_query(
        self,
        db: Session,
        user_id: int,
        query: str,
        session_id: str
    ) -> Dict:
        """
        Process user query using RAG with Groq LLM.
        
        Args:
            db: Database session
            user_id: User ID
            query: User's question
            session_id: Chat session ID
        
        Returns:
            Dict with answer and sources
        """
        logger.info(f"Processing query for user {user_id}: {query[:50]}...")
        
        # Save user message to history
        self.chat_history_service.save_message(
            db=db,
            user_id=user_id,
            session_id=session_id,
            role="user",
            message=query
        )
        
        # Search for relevant document chunks
        similar_chunks = self.embedding_service.search_similar_chunks(
            db=db,
            query=query,
            user_id=user_id,
            top_k=5
        )
        
        if not similar_chunks:
            answer = "I don't have any documents to answer your question. Please upload relevant documents first."
            sources = []
        else:
            # Build context from similar chunks
            context = self._build_context(similar_chunks)
            
            # Generate answer using Groq LLM
            answer = self._generate_answer(query, context)
            
            # Extract sources
            sources = [
                {
                    "document": chunk[1],
                    "chunk": chunk[0][:200] + "..." if len(chunk[0]) > 200 else chunk[0],
                    "similarity": round(chunk[2], 3)
                }
                for chunk in similar_chunks[:3]  # Top 3 sources
            ]
        
        # Save assistant message to history
        self.chat_history_service.save_message(
            db=db,
            user_id=user_id,
            session_id=session_id,
            role="assistant",
            message=answer
        )
        
        logger.info(f"Query processed successfully for user {user_id}")
        
        return {
            "answer": answer,
            "sources": sources
        }
    
    def _build_context(self, similar_chunks: List[tuple]) -> str:
        """Build context string from similar chunks"""
        context_parts = []
        for idx, (chunk_text, filename, similarity) in enumerate(similar_chunks, 1):
            context_parts.append(f"[Source {idx} from {filename}]:\n{chunk_text}\n")
        
        return "\n".join(context_parts)
    
    def _generate_answer(self, query: str, context: str) -> str:
        """
        Generate answer using Groq LLM.
        
        Args:
            query: User's question
            context: Retrieved context from documents
        
        Returns:
            Generated answer
        """
        system_prompt = """You are a helpful assistant for answering questions about meeting minutes and documents.
Use the provided context to answer the user's question accurately and comprehensively.
IMPORTANT: Include ALL specific details from the context such as:
- Numbers, percentages, and statistics
- Committee compositions (e.g., "50% independent directors", "100% independent directors")
- Specific names, dates, and figures
- Exact terminology and technical details

CRITICAL: Provide clean, direct answers WITHOUT mentioning sources in your response.
Do NOT include phrases like:
- "According to the context"
- "Source 1 mentions"
- "(Source 2)"
- "from Management Presentation.pdf"
- "the provided context"

Just state the facts directly and naturally as if you know them.
If the context doesn't contain enough information to answer the question, say so clearly."""
        
        user_prompt = f"""Context from documents:
{context}

Question: {query}

Provide a clear, detailed answer with ALL specific details, numbers, and percentages. 
Answer directly without mentioning sources or context - just state the facts naturally."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            logger.debug(f"Generated answer (length: {len(answer)})")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer with Groq: {str(e)}")
            return "I apologize, but I encountered an error while generating the answer. Please try again."
