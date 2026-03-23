from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
import logging
import json

# Existing router definition
router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)

# --- Pydantic Models for Existing Endpoints ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    database: Optional[str] = None
    limit: Optional[int] = None
    last_n_days: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    database_used: str
    structured: Optional[Any] = None

# --- Existing POST Endpoints with Dynamic Import Logic ---

@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.append(root_dir)
        sys.path.append(os.path.join(root_dir, "chatbot_backend"))
        import importlib.util, importlib
        orchestrator_path = os.path.join(root_dir, "chatbot_backend", "chat_orchestrator", "orchestrator.py")
        try:
            cb_pkg = importlib.import_module("chatbot_backend")
            sys.modules["data_layer"] = importlib.import_module("chatbot_backend.data_layer")
            sys.modules["indexing_layer"] = importlib.import_module("chatbot_backend.indexing_layer")
            sys.modules["chat_orchestrator"] = importlib.import_module("chatbot_backend.chat_orchestrator")
            sys.modules["llm_layer"] = importlib.import_module("chatbot_backend.llm_layer")
            sys.modules["utils"] = importlib.import_module("chatbot_backend.utils")
        except Exception as e:
            logger.warning(f"Module import warning for chat_message: {e}")
        spec = importlib.util.spec_from_file_location("cb_orchestrator", orchestrator_path)
        cb_module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(cb_module)
        process_user_query = cb_module.process_user_query
        database = request.database or "all"
        limit = request.limit if request.limit is not None else 10
        last_n_days = request.last_n_days
        
        # response_data can be str or dict (table/chart)
        response_data, _sources = process_user_query(request.message, database, limit=limit, last_n_days=last_n_days)

        structured = None
        response_text = ""

        # If orchestrator returned a dict (structured), pass it through as structured
        if isinstance(response_data, dict):
            structured = response_data
            try:
                response_text = json.dumps(response_data)
            except Exception:
                response_text = str(response_data)
        else:
            # response_data is likely a string. Try to parse JSON out of it (models often return JSON as text)
            response_text = response_data if response_data is not None else ""
            try:
                parsed = json.loads(response_text)
                structured = parsed
            except Exception:
                # Try to extract JSON substring if the model wrapped JSON in text
                try:
                    start_idx = None
                    for ch in ['[', '{']:
                        idx = response_text.find(ch)
                        if idx != -1:
                            start_idx = idx
                            break
                    if start_idx is not None:
                        end_idx = None
                        for ch in [']', '}']:
                            idx2 = response_text.rfind(ch)
                            if idx2 != -1 and idx2 > start_idx:
                                end_idx = idx2
                                break
                        if end_idx is not None:
                            json_sub = response_text[start_idx:end_idx+1]
                            parsed = json.loads(json_sub)
                            structured = parsed
                except Exception:
                    structured = None

        return ChatResponse(response=response_text, database_used=database, structured=structured)
    except Exception as e:
        try:
            msg_preview = (request.message[:200] + "...") if request and request.message and len(request.message) > 200 else (request.message or "")
        except Exception:
            msg_preview = ""
        logger.exception(
            f"chat_message error | session_id={getattr(request, 'session_id', None)} | database={getattr(request, 'database', None)} | limit={getattr(request, 'limit', None)} | last_n_days={getattr(request, 'last_n_days', None)} | message_preview={msg_preview}"
        )
        raise HTTPException(status_code=500, detail="Failed to process chat message")

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.append(root_dir)
        sys.path.append(os.path.join(root_dir, "chatbot_backend"))
        import importlib.util, importlib
        orchestrator_path = os.path.join(root_dir, "chatbot_backend", "chat_orchestrator", "orchestrator.py")
        try:
            cb_pkg = importlib.import_module("chatbot_backend")
            sys.modules["data_layer"] = importlib.import_module("chatbot_backend.data_layer")
            sys.modules["indexing_layer"] = importlib.import_module("chatbot_backend.indexing_layer")
            sys.modules["chat_orchestrator"] = importlib.import_module("chatbot_backend.chat_orchestrator")
            sys.modules["llm_layer"] = importlib.import_module("chatbot_backend.llm_layer")
            sys.modules["utils"] = importlib.import_module("chatbot_backend.utils")
        except Exception:
            pass
        spec = importlib.util.spec_from_file_location("cb_orchestrator", orchestrator_path)
        cb_module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(cb_module)
        process_user_query = cb_module.process_user_query
        database = request.database or "all"
        limit = request.limit if request.limit is not None else 10
        last_n_days = request.last_n_days

        def generate():
            # response_text can be str or dict (table/chart)
            response_data, _sources = process_user_query(request.message, database, limit=limit, last_n_days=last_n_days)
            
            # Streaming response typically only supports text/plain, so complex objects 
            # must be serialized or handled differently by the client. We serialize here.
            if isinstance(response_data, dict):
                 text = json.dumps(response_data)
            else:
                 text = response_data
            
            chunk_size = 256
            for i in range(0, len(text), chunk_size):
                yield text[i : i + chunk_size]

        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------------------
# --- NEW GET Endpoint for direct, structured chat response ---
# -------------------------------------------------------------------

# Using a new router instance for the new endpoint structure, as the old one has a prefix /api/chat.
# For simplicity, we define a second router here, but in a real app, you would typically 
# combine them or ensure consistent prefixing.

# We must dynamically import process_user_query or rely on a successful path configuration.
# Since the user requested simple imports, we'll try to stick to that, assuming the environment
# is set up correctly, but for this file's context, we wrap the import to minimize file changes.
try:
    # Attempt simple import (as requested in the new code snippet)
    from chatbot_backend.chat_orchestrator.orchestrator import process_user_query
except ImportError:
    # Fallback/note: In a real app, you must ensure the path is correct. 
    # For this exercise, we proceed assuming a successful import path.
    # We define a placeholder function to allow the code to run if the import fails
    def process_user_query(*args, **kwargs):
        return "Error: Orchestrator not imported (dependency issue).", []

# Let's attach this new GET endpoint to the main `router` instead of creating a second non-imported one.
@router.get("")
def chat_get(
    q: str = Query(..., description="User query"),
    database: str = Query("all", description="bse | sebi | rbi | all"),
    limit: int = Query(10, description="Max number of results"),
    last_n_days: Optional[int] = Query(None, description="Filter by recent days"),
) -> Dict[str, Any]:
    """
    Main chat endpoint (GET) supporting structured table/chart output.
    """
    response, sources = process_user_query(
        query=q,
        database=database,
        limit=limit,
        last_n_days=last_n_days
    )

    #  CASE 1: Structured chart response (JSON from analytics/LLM)
    if isinstance(response, dict) and response.get("response_type") == "chart":
        # 
        return {
            "type": "chart",
            "chart_type": response.get("chart_type", "bar"),
            "title": response.get("title", "Notification Count"),
            "x": response.get("x", []),
            "y": response.get("y", [])
        }

    #  CASE 2: Structured table response (JSON from LLM)
    if isinstance(response, dict) and response.get("response_type") == "table":
        # 
        return {
            "type": "table",
            "columns": response.get("columns", []),
            "rows": response.get("rows", [])
        }

    #  CASE 3: Normal text response
    return {
        "type": "text",
        "content": response
    }