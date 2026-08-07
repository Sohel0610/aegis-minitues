"""
Enhanced Chat Router with NLU Integration
Integrates intent classification, fuzzy matching, context management, and intelligent responses
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
import logging
import json
import re

router = APIRouter(prefix="/api/chat", tags=["Chat Enhanced"])
logger = logging.getLogger(__name__)


def _upgrade_legacy_notification_text(response_text: str) -> str:
    """
    Convert old compact bullet text into the detailed Date/Sub/Summary layout.
    """
    if not isinstance(response_text, str):
        return response_text

    if "include:" not in response_text or "(Ref" not in response_text:
        return response_text

    lines = [line.strip() for line in response_text.splitlines() if line.strip()]
    if not lines:
        return response_text

    header = lines[0]
    match = re.match(r"^(?P<company>.+?) notifications(?: for .+?)? include:$", header, flags=re.IGNORECASE)
    if not match:
        return response_text

    company = match.group("company").strip()
    bullet_lines = [line for line in lines[1:] if line.startswith("- ")]
    if not bullet_lines:
        return response_text

    detailed_lines = [
        "=" * 80,
        f"{company} ({len(bullet_lines)} notifications)",
        "=" * 80,
        "",
    ]

    for bullet in bullet_lines:
        cleaned = re.sub(r"\s*\(Ref\s*\[?\d+\]?(?:,\s*\[?\d+\]?)*\)\s*$", "", bullet).strip()
        cleaned = cleaned[2:] if cleaned.startswith("- ") else cleaned

        date_part = "Unknown"
        summary_part = cleaned

        if ":" in cleaned:
            left, right = cleaned.split(":", 1)
            date_part = left.strip()
            summary_part = right.strip()

        detailed_lines.append(f"Date: {date_part}")
        detailed_lines.append("Sub: Notification")
        detailed_lines.append(f"Summary: {summary_part}")
        detailed_lines.append("")

    return "\n".join(detailed_lines).strip()


def _format_notifications_detailed(chat_orchestrator, notifications) -> str:
    if not notifications:
        return "No relevant notifications found."

    company_groups = {}
    for notification in notifications:
        company = chat_orchestrator._display_company_name(notification)
        company_groups.setdefault(company, []).append(notification)

    response_parts = []
    for company, company_notifications in company_groups.items():
        response_parts.append(f"{'=' * 80}")
        response_parts.append(f"{company} ({len(company_notifications)} notifications)")
        response_parts.append(f"{'=' * 80}")
        response_parts.append("")

        for notification in company_notifications:
            date = chat_orchestrator._display_date(notification)
            subject = chat_orchestrator._display_subject(notification)
            summary = chat_orchestrator._display_summary(notification)

            response_parts.append(f"Date: {date}")
            response_parts.append(f"Sub: {subject}")
            response_parts.append(f"Summary: {summary}")
            response_parts.append("")

    return "\n".join(response_parts).strip()


def _rebuild_detailed_response(cb_module, resolved_query: str, database_to_use: str, last_n_days: Optional[int]) -> Optional[str]:
    try:
        resolved = cb_module.resolve_entity(resolved_query)
        strict_entity = resolved["canonical"] if resolved else None
        entity_aliases = resolved["aliases"] if resolved else None

        retrieval_method, sql_results = cb_module.route_query(
            resolved_query,
            limit=1000,
            database=database_to_use,
            strict_entity=strict_entity,
            entity_aliases=entity_aliases,
        )

        if retrieval_method in ["structured", "date_only"]:
            notifications = cb_module.convert_to_common_format(sql_results, database_to_use)
            if entity_aliases:
                notifications = cb_module.chat_orchestrator.apply_strict_entity_filter(notifications, entity_aliases)
        else:
            notifications = cb_module.chat_orchestrator.semantic_retrieve(
                resolved_query,
                database_to_use,
                limit=1000,
                last_n_days=last_n_days,
                strict_entity=strict_entity,
            )
            if entity_aliases:
                notifications = cb_module.chat_orchestrator.apply_strict_entity_filter(notifications, entity_aliases)

        notifications = cb_module.chat_orchestrator._apply_query_specific_filters(notifications, resolved_query)
        return _format_notifications_detailed(cb_module.chat_orchestrator, notifications)
    except Exception as rebuild_error:
        logger.warning("Failed to rebuild detailed response: %s", rebuild_error)
        return None


def _should_force_detailed_rebuild(response_text: str, resolved_query: str, intent_value: Optional[str]) -> bool:
    if not isinstance(response_text, str):
        return False

    if "Date:" in response_text and "Sub:" in response_text and "Summary:" in response_text:
        return False

    query_lower = (resolved_query or "").lower()
    explicit_data_request = intent_value == "explicit_data_request"
    retrieval_cues = ["show", "list", "notification", "notifications", "announcement", "announcements", "summary", "summaries", "summeries"]

    return explicit_data_request and any(cue in query_lower for cue in retrieval_cues)

# Pydantic Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_session"
    database: Optional[str] = None  # Optional - will be auto-detected
    limit: Optional[int] = 10
    last_n_days: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    database_detected: Optional[str] = None
    response_type: str = "text"  # text | table | chart | executive
    structured: Optional[Any] = None
    chart_config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/message", response_model=ChatResponse)
async def chat_message_enhanced(request: ChatRequest):
    """
    Enhanced chat endpoint with NLU integration
    - Automatic database detection
    - Intent classification
    - Fuzzy entity matching
    - Multi-format responses (text/table/chart)
    - Context-aware conversations
    """
    try:
        # 🔹 QUICK GREETING SHORTCUT
        # If the user just says "hi", "hello", etc., return a simple greeting
        raw_message = (request.message or "").strip()
        normalized = raw_message.lower()

        greeting_patterns = {
            "hi",
            "hello",
            "hey",
            "hi there",
            "hello there",
            "hii",
            "hiii",
            "hey there",
        }

        if normalized in greeting_patterns:
            db_detected = request.database or "all"
            return ChatResponse(
                response="Hello! How Can I Help You?",
                database_detected=db_detected,
                response_type="text",
                structured=None,
                chart_config=None,
                metadata={
                    "nlu_enabled": False,
                    "is_greeting": True,
                },
            )

        # Add chatbot_backend to path
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, root_dir)
        sys.path.insert(0, os.path.join(root_dir, "chatbot_backend"))
        
        # Import NLU components
        try:
            from chatbot_backend.nlu_engine import (
                get_intent_classifier,
                get_context_manager,
                get_fuzzy_matcher
            )
            from chatbot_backend.nlu_engine.query_preprocessor import QueryPreprocessor
            from chatbot_backend.response_layer import (
                get_response_formatter,
                get_chart_generator
            )
            from chatbot_backend.guidance_layer import get_ambiguity_resolver
            from chatbot_backend.performance_layer import get_query_cache
            
            nlu_available = True
        except ImportError as e:
            logger.warning(f"NLU components not available: {e}")
            nlu_available = False
        
        # Import orchestrator
        import importlib.util
        orchestrator_path = os.path.join(root_dir, "chatbot_backend", "chat_orchestrator", "orchestrator.py")
        spec = importlib.util.spec_from_file_location("cb_orchestrator", orchestrator_path)
        cb_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cb_module)
        process_user_query = cb_module.process_user_query
        
        # Initialize components if available
        if nlu_available:
            intent_classifier = get_intent_classifier()
            context_manager = get_context_manager()
            response_formatter = get_response_formatter()
            chart_generator = get_chart_generator()
            ambiguity_resolver = get_ambiguity_resolver()
            query_cache = get_query_cache()
            
            cached_response = query_cache.get(request.message, request.database or "all", request.session_id or "anonymous")
            if cached_response and isinstance(cached_response, dict) and cached_response.get("response"):
                return ChatResponse(**cached_response)
            
            # Step 2: Resolve pronouns using context
            effective_session_id = (
                request.session_id
                if request.session_id and request.session_id != "default_session"
                else None
            )
            prepared_query = QueryPreprocessor(context_manager).prepare(request.message, effective_session_id)
            resolved_query = prepared_query.retrieval_query
            logger.info(f"Resolved query: {resolved_query}")
            
            # Step 3: Classify intent
            intent_result = intent_classifier.classify(resolved_query)
            logger.info(f"Intent: {intent_result.intent.value} (confidence: {intent_result.confidence:.2f})")
            
            # Step 4: Detect database if not specified
            database_to_use = request.database
            if not database_to_use or database_to_use == "auto":
                # Use ambiguity resolver to detect database
                ambiguity = ambiguity_resolver.detect_ambiguity(resolved_query, has_entity=True)
                
                # Simple keyword-based detection
                query_lower = resolved_query.lower()
                if any(kw in query_lower for kw in ["bse", "stock", "equity", "share"]):
                    database_to_use = "bse"
                elif any(kw in query_lower for kw in ["sebi", "securities", "regulatory"]):
                    database_to_use = "sebi"
                elif any(kw in query_lower for kw in ["rbi", "reserve bank", "monetary", "banking"]):
                    database_to_use = "rbi"
                else:
                    database_to_use = "all"
            
            logger.info(f"Database detected: {database_to_use}")
        else:
            # Fallback without NLU
            resolved_query = request.message
            database_to_use = request.database or "all"
            intent_result = None
        
        # Step 5: Query orchestrator
        limit = request.limit if request.limit is not None else 10
        last_n_days = request.last_n_days
        
        response_data, sources = process_user_query(
            resolved_query, 
            database_to_use, 
            limit=limit, 
            last_n_days=last_n_days
        )
        logger.info(
            "Orchestrator returned type=%s preview=%s",
            type(response_data).__name__,
            str(response_data)[:200].replace("\n", "\\n")
        )
        
        # Step 6: Format response based on intent
        structured = None
        chart_config = None
        response_type = "text"
        response_text = ""
        
        if nlu_available and intent_result:
            # If backend already returned final text, preserve it exactly.
            if isinstance(response_data, str):
                response_type = "text"
                if _should_force_detailed_rebuild(response_data, resolved_query, intent_result.intent.value):
                    rebuilt = _rebuild_detailed_response(cb_module, resolved_query, database_to_use, last_n_days)
                    response_text = rebuilt or _upgrade_legacy_notification_text(response_data)
                else:
                    response_text = response_data

            # Respect backend-native structured responses first
            elif isinstance(response_data, dict) and response_data.get("response_type") == "chart":
                response_type = "chart"
                chart_config = {
                    "chart_type": response_data.get("chart_type", "bar"),
                    "title": response_data.get("title", "Chart"),
                    "x_axis": response_data.get("x_axis"),
                    "y_axis": response_data.get("y_axis"),
                    "data": response_data.get("data", {"labels": [], "values": []}),
                    "metadata": response_data.get("metadata", {}),
                }
                response_text = response_data.get("message") or response_data.get("title") or ""

            elif isinstance(response_data, dict) and response_data.get("response_type") == "table":
                response_type = "table"
                structured = response_data
                response_text = response_data.get("title") or response_data.get("message") or "Table results"

            # Determine response format based on intent
            elif intent_classifier.is_chart_preferred(intent_result):
                if isinstance(response_data, list):
                    response_type = "chart"
                    chart_cfg = chart_generator.generate_chart(
                        response_data,
                        intent_result.intent.value,
                        entity_name=None
                    )
                    chart_config = {
                        "chart_type": chart_cfg.chart_type.value,
                        "title": chart_cfg.title,
                        "x_axis": chart_cfg.x_axis,
                        "y_axis": chart_cfg.y_axis,
                        "data": chart_cfg.data,
                        "metadata": chart_cfg.metadata
                    }
                    response_text = f"Generated {chart_cfg.chart_type.value} chart: {chart_cfg.title}"
                else:
                    response_type = "text"
                    response_text = str(response_data) if response_data is not None else ""

            elif intent_classifier.is_table_preferred(intent_result):
                response_type = "table"
                if isinstance(response_data, list):
                    structured = response_data
                    response_text = f"Found {len(response_data)} results"
                elif isinstance(response_data, dict):
                    structured = response_data
                    response_text = response_data.get("title") or response_data.get("message") or "Table results"
                else:
                    response_text = str(response_data)

            else:
                # Conversational format
                response_type = "text"
                if isinstance(response_data, str):
                    if _should_force_detailed_rebuild(response_data, resolved_query, intent_result.intent.value):
                        rebuilt = _rebuild_detailed_response(cb_module, resolved_query, database_to_use, last_n_days)
                        response_text = rebuilt or _upgrade_legacy_notification_text(response_data)
                    else:
                        response_text = response_data
                elif isinstance(response_data, list):
                    # Format as conversational text
                    formatted = response_formatter.format_conversational(response_data, None)
                    response_text = formatted.content
                else:
                    response_text = str(response_data)
            
            # Step 7: Save to context
            if effective_session_id:
                context_manager.add_turn(
                    session_id=effective_session_id,
                    user_query=request.message,
                    bot_response=response_text[:2000],
                    intent=intent_result.intent.value,
                    entities=intent_result.entities or [],
                    metadata={"database": database_to_use, "rewritten_query": resolved_query},
                )
            
            # Step 8: Cache disabled for now to avoid stale response formats.
        
        else:
            # Fallback without NLU - use existing logic
            if isinstance(response_data, dict):
                structured = response_data
                response_text = json.dumps(response_data)
                response_type = "table"
            elif isinstance(response_data, list):
                structured = response_data
                response_text = f"Found {len(response_data)} results"
                response_type = "table"
            else:
                response_text = str(response_data) if response_data else ""
                response_type = "text"
        
        confidence = None
        if nlu_available and isinstance(response_text, str):
            from chatbot_backend.response_layer.post_processor import post_processor
            # Structured/table responses are already source data; text is checked.
            source_records = response_data if isinstance(response_data, list) else []
            checked = post_processor.process(response_text, source_records)
            response_text, confidence = checked.response, checked.confidence
        response = ChatResponse(
            response=response_text,
            database_detected=database_to_use,
            response_type=response_type,
            structured=structured,
            chart_config=chart_config,
            metadata={"nlu_enabled": nlu_available, "confidence": confidence}
        )
        if nlu_available:
            query_cache.set(request.message, response.dict(), database_to_use, user_id=request.session_id or "anonymous")
        return response
        
    except Exception as e:
        logger.exception(f"Error in enhanced chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat message: {str(e)}")


@router.post("/stream")
async def chat_message_stream(request: ChatRequest):
    """SSE delivery for browser chat clients.

    Retrieval runs before generation; chunks are then delivered as SSE `token`
    events so the UI can render progressively and handle `done`/`error` events.
    """
    async def events():
        try:
            response = await chat_message_enhanced(request)
            for token in re.findall(r"\S+\s*", response.response):
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
                await asyncio.sleep(0)
            yield f"event: metadata\ndata: {json.dumps(response.metadata or {})}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception:
            yield "event: error\ndata: {\"message\": \"Chat request failed\"}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
