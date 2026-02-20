"""
Chatbot Service

RAG-based chatbot for answering questions from uploaded documents.
"""

from openai import AzureOpenAI
from sqlalchemy.orm import Session
from minutes_chatbot.services.embedding_service import EmbeddingService
from minutes_chatbot.services.chat_history_service import ChatHistoryService
from minutes_chatbot.config import settings, logger
from typing import Dict, List


class ChatbotService:
    """Service for RAG-based chatbot"""
    
    def __init__(self):
        """Initialize Azure OpenAI client and embedding service"""
        self.client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
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
        Process user query using RAG.
        
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
            
            # Generate answer using LLM
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
        Generate answer using Azure OpenAI LLM.
        
        Args:
            query: User's question
            context: Retrieved context from documents
        
        Returns:
            Generated answer
        """
        system_prompt = """You are a helpful assistant for answering questions about meeting minutes and documents.
Use the provided context to answer the user's question accurately.
If the context doesn't contain enough information to answer the question, say so clearly.
Always cite which source you're using when answering."""
        
        user_prompt = f"""Context from documents:
{context}

Question: {query}

Please provide a clear and concise answer based on the context above."""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            logger.debug(f"Generated answer (length: {len(answer)})")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return "I apologize, but I encountered an error while generating the answer. Please try again."
