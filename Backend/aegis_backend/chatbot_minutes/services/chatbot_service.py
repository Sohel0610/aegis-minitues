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
        
        # Initialize LLM clients
        self.groq_client = None
        self.azure_client = None
        
        if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your-groq-api-key":
            self.groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
            logger.info(f"Groq LLM initialized: {settings.GROQ_MODEL}")
            
        if settings.AZURE_OPENAI_API_KEY:
            self.azure_client = AzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION
            )
            logger.info("Azure OpenAI LLM initialized")
            
        if not self.groq_client and not self.azure_client:
            logger.warning("No LLM API key configured for ChatbotService")

    def process_query(
        self,
        db: Session,
        user_id: int,
        query: str,
        session_id: str,
        is_admin: bool = False
    ) -> Dict:
        # 1. Fetch conversation history for this session (ChatGPT style)
        history = self.chat_history_service.get_session_history(db, user_id, session_id, limit=6)
        
        # 2. Save current user message
        self.chat_history_service.save_message(
            db=db,
            user_id=user_id,
            session_id=session_id,
            role="user",
            message=query
        )
        
        # 3. Search for context (passing is_admin flag for RBAC)
        similar_chunks = self.embedding_service.search_similar_chunks(
            db=db,
            query=query,
            user_id=user_id,
            is_admin=is_admin,
            top_k=5
        )
        
        if not similar_chunks:
            context = "No specific document context found."
            sources = []
        else:
            context = self._build_context(similar_chunks)
            sources = [
                {
                    "document": chunk[1],
                    "chunk": chunk[0][:300] + "..." if len(chunk[0]) > 300 else chunk[0],
                    "similarity": round(chunk[2], 3)
                }
                for chunk in similar_chunks[:3]
            ]
        
        # 4. Generate answer using history + current context
        answer = self._generate_answer(query, context, history)
        
        # 5. Save assistant message
        self.chat_history_service.save_message(
            db=db,
            user_id=user_id,
            session_id=session_id,
            role="assistant",
            message=answer
        )
        
        return {
            "answer": answer,
            "sources": sources,
            "session_id": session_id
        }

    def _build_context(self, similar_chunks: List[tuple]) -> str:
        context_parts = []
        for idx, (chunk_text, filename, similarity) in enumerate(similar_chunks, 1):
            context_parts.append(f"[Document: {filename}]\n{chunk_text}\n")
        return "\n".join(context_parts)

    def _generate_answer(self, query: str, context: str, history: List) -> str:
        system_prompt = """You are 'Aegis Meeting Assistant', a professional AI designed to analyze meeting minutes, agendas, and corporate records.
You are in a conversation. Use the 'Document Context' to answer accurately. 
Review the 'Conversation History' to understand the thread.
If the context doesn't have the answer, use your knowledge but mention that the docs don't say.
Always cite source filenames."""
        
        # Build chat message history
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg.role, "content": msg.message})
            
        # Add current context and question
        user_payload = f"DOCUMENT CONTEXT:\n{context}\n\nUSER QUESTION: {query}"
        messages.append({"role": "user", "content": user_payload})

        try:
            # Logic: Try Azure first, fallback to Groq if Azure fails or is unavailable
            if self.azure_client:
                try:
                    response = self.azure_client.chat.completions.create(
                        model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                        messages=messages,
                        temperature=0.4,
                        max_tokens=2048
                    )
                    return response.choices[0].message.content
                except Exception as azure_err:
                    logger.warning(f"Azure OpenAI call failed: {azure_err}. Attempting Groq fallback...")
                    if self.groq_client:
                        response = self.groq_client.chat.completions.create(
                            model=settings.GROQ_MODEL,
                            messages=messages,
                            temperature=0.4,
                            max_tokens=2048
                        )
                        return response.choices[0].message.content
                    else:
                        raise azure_err
            elif self.groq_client:
                response = self.groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=messages,
                    temperature=0.4,
                    max_tokens=2048
                )
                return response.choices[0].message.content
            else:
                return "LLM service is not configured. Please check your API keys."
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return f"I apologize, but I encountered an error while generating the answer: {str(e)}"
