import logging
from typing import Dict, List
from openai import AzureOpenAI
import groq
from sqlalchemy.orm import Session
from .embedding_service import EmbeddingService
from .chat_history_service import ChatHistoryService
from ..config import settings

logger = logging.getLogger(__name__)

class ChatbotService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.chat_history_service = ChatHistoryService()
        
        # Initialize LLM client
        self.use_groq = settings.GROQ_API_KEY is not None
        if self.use_groq:
            self.groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
            logger.info(f"Using Groq LLM: {settings.GROQ_MODEL}")
        elif settings.AZURE_OPENAI_API_KEY:
            self.azure_client = AzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION
            )
            logger.info("Using Azure OpenAI LLM")
        else:
            logger.warning("No LLM API key configured for ChatbotService")

    def process_query(
        self,
        db: Session,
        user_id: int,
        query: str,
        session_id: str
    ) -> Dict:
        # Save user message
        self.chat_history_service.save_message(
            db=db,
            user_id=user_id,
            session_id=session_id,
            role="user",
            message=query
        )
        
        # Search for context
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
            context = self._build_context(similar_chunks)
            answer = self._generate_answer(query, context)
            sources = [
                {
                    "document": chunk[1],
                    "chunk": chunk[0][:200] + "..." if len(chunk[0]) > 200 else chunk[0],
                    "similarity": round(chunk[2], 3)
                }
                for chunk in similar_chunks[:3]
            ]
        
        # Save assistant message
        self.chat_history_service.save_message(
            db=db,
            user_id=user_id,
            session_id=session_id,
            role="assistant",
            message=answer
        )
        
        return {
            "answer": answer,
            "sources": sources
        }

    def _build_context(self, similar_chunks: List[tuple]) -> str:
        context_parts = []
        for idx, (chunk_text, filename, similarity) in enumerate(similar_chunks, 1):
            context_parts.append(f"[Source {idx} from {filename}]:\n{chunk_text}\n")
        return "\n".join(context_parts)

    def _generate_answer(self, query: str, context: str) -> str:
        system_prompt = """You are a helpful assistant for answering questions about meeting minutes and documents.
Use the provided context to answer the user's question accurately.
If the context doesn't contain enough information to answer the question, say so clearly.
Always cite which source you're using when answering."""
        
        user_prompt = f"""Context from documents:
{context}

Question: {query}

Please provide a clear and concise answer based on the context above."""

        try:
            if self.use_groq:
                response = self.groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1024
                )
                return response.choices[0].message.content
            elif hasattr(self, 'azure_client'):
                response = self.azure_client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1024
                )
                return response.choices[0].message.content
            else:
                return "LLM service is not configured."
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return "I apologize, but I encountered an error while generating the answer."
