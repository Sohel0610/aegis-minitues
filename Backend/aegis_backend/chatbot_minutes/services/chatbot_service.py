import logging
import os
import json
import subprocess
import tempfile
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
            try:
                self.groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
                logger.info(f"Groq LLM initialized: {settings.GROQ_MODEL}")
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")
            
        if settings.AZURE_OPENAI_API_KEY:
            try:
                self.azure_client = AzureOpenAI(
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    api_version=settings.AZURE_OPENAI_API_VERSION
                )
                logger.info("Azure OpenAI LLM initialized")
            except Exception as e:
                logger.warning(f"Could not initialize AzureOpenAI Python client: {e}. Subprocess curl will be used.")
                self.azure_client = None
            
        if not self.groq_client and not settings.AZURE_OPENAI_API_KEY:
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
            if settings.AZURE_OPENAI_API_KEY:
                try:
                    # Prepare payload
                    prompt_data = {
                        "messages": messages,
                        "temperature": 0.4,
                        "max_tokens": 2048
                    }
                    
                    # Write payload to a temporary file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', encoding='utf-8', delete=False) as f:
                        json.dump(prompt_data, f, indent=2, ensure_ascii=False)
                        prompt_file = f.name
                        
                    endpoint = settings.AZURE_OPENAI_ENDPOINT
                    deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME
                    api_key = settings.AZURE_OPENAI_API_KEY
                    api_version = settings.AZURE_OPENAI_API_VERSION
                    
                    api_url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
                    
                    if os.name == 'nt':
                        # Windows - quote file path properly and use shell execution
                        curl_command = f'curl -s -k -X POST "{api_url}" -H "Content-Type: application/json" -H "api-key: {api_key}" -d "@{prompt_file}"'
                        result = subprocess.run(curl_command, capture_output=True, encoding='utf-8', errors='replace', shell=True, timeout=45)
                    else:
                        # Unix/Linux/Mac
                        curl_command = [
                            'curl', '-s', '-k', '-X', 'POST', api_url,
                            '-H', 'Content-Type: application/json',
                            '-H', f'api-key: {api_key}',
                            '-d', f'@{prompt_file}'
                        ]
                        result = subprocess.run(curl_command, capture_output=True, encoding='utf-8', errors='replace', timeout=45)
                        
                    # Clean up file
                    if os.path.exists(prompt_file):
                        os.unlink(prompt_file)
                        
                    if result.returncode != 0:
                        error_msg = result.stderr if result.stderr else "Unknown error"
                        raise Exception(f"Curl command failed with return code {result.returncode}: {error_msg}")
                        
                    if not result.stdout:
                        raise Exception("No response from Azure OpenAI via curl")
                        
                    response_data = json.loads(result.stdout)
                    
                    if "error" in response_data:
                        error_message = response_data["error"]
                        if isinstance(error_message, dict) and "message" in error_message:
                            raise Exception(f"Azure API error: {error_message['message']}")
                        else:
                            raise Exception(f"Azure API error: {error_message}")
                            
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        if "message" in response_data["choices"][0] and "content" in response_data["choices"][0]["message"]:
                            return response_data["choices"][0]["message"]["content"].strip()
                    
                    raise Exception("Invalid API response format from curl")
                    
                except Exception as azure_err:
                    logger.warning(f"Azure OpenAI curl call failed: {azure_err}. Attempting Groq fallback...")
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
