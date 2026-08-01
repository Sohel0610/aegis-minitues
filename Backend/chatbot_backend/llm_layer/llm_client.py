"""Provider-safe LLM client for Azure OpenAI with Groq fallback.

The module deliberately has no subprocess/curl dependency: SDK clients support
timeouts, structured tool calls and streaming consistently on every platform.
"""
from typing import Any, Dict, Iterable, List, Optional, Union
import os

from dotenv import load_dotenv
from groq import Groq
from openai import AzureOpenAI

from config.llm_config import LLMConfig

load_dotenv()
_azure_client = None
_groq_client = None


def _ignore_missing_ssl_cert_file() -> None:
    path = os.environ.get("SSL_CERT_FILE")
    if path and not os.path.exists(path):
        os.environ.pop("SSL_CERT_FILE", None)


def _get_azure_client() -> AzureOpenAI:
    global _azure_client
    if _azure_client is None:
        if not (LLMConfig.AZURE_ENDPOINT and LLMConfig.AZURE_API_KEY and LLMConfig.AZURE_DEPLOYMENT):
            raise RuntimeError("Azure OpenAI endpoint, API key, or deployment is not configured")
        _azure_client = AzureOpenAI(
            azure_endpoint=LLMConfig.AZURE_ENDPOINT,
            api_key=LLMConfig.AZURE_API_KEY,
            api_version=LLMConfig.AZURE_API_VERSION,
            timeout=45.0,
            max_retries=2,
        )
    return _azure_client


def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        if not LLMConfig.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured")
        _ignore_missing_ssl_cert_file()
        _groq_client = Groq(api_key=LLMConfig.GROQ_API_KEY, timeout=45.0)
    return _groq_client


def embed_text(text: str) -> List[float]:
    """Compatibility hook; retrieval embeddings are supplied by embedding_utils."""
    from chatbot_backend.utils.embedding_utils import get_embedding_model
    return get_embedding_model().encode(text)[0].tolist()


def _messages(system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def _stream_text(stream: Iterable[Any]) -> Iterable[str]:
    for event in stream:
        delta = event.choices[0].delta.content if event.choices else None
        if delta:
            yield delta


def chat_completion(system_prompt: str, user_prompt: str, model: Optional[str] = None,
                    stream: bool = False) -> Union[str, Iterable[str]]:
    """Return text, or a token iterator when ``stream=True``.

    Azure is primary whenever configured. Groq is used as a resilient fallback
    if Azure errors and a Groq key is available.
    """
    messages = _messages(system_prompt, user_prompt)
    providers = ["azure", "groq"] if LLMConfig.is_azure_enabled() else ["groq", "azure"]
    errors = []
    for provider in providers:
        try:
            if provider == "azure" and LLMConfig.AZURE_ENDPOINT and LLMConfig.AZURE_API_KEY:
                response = _get_azure_client().chat.completions.create(
                    model=model or LLMConfig.AZURE_DEPLOYMENT, messages=messages,
                    temperature=0.2, max_tokens=1536, top_p=0.9, stream=stream,
                )
                return _stream_text(response) if stream else (response.choices[0].message.content or "").strip()
            if provider == "groq" and LLMConfig.GROQ_API_KEY:
                response = _get_groq_client().chat.completions.create(
                    model=model or LLMConfig.GROQ_MODEL, messages=messages,
                    temperature=0.2, max_tokens=1536, stream=stream,
                )
                return _stream_text(response) if stream else (response.choices[0].message.content or "").strip()
        except Exception as exc:
            errors.append(f"{provider}: {exc}")
    raise RuntimeError("LLM completion failed: " + "; ".join(errors or ["no provider configured"]))


def chat_completion_with_tools(messages: List[Dict[str, Any]], tools: List[Dict[str, Any]],
                               model: Optional[str] = None) -> Any:
    """Create a non-streaming tool-call completion for the agentic router."""
    if LLMConfig.AZURE_ENDPOINT and LLMConfig.AZURE_API_KEY:
        return _get_azure_client().chat.completions.create(
            model=model or LLMConfig.AZURE_DEPLOYMENT, messages=messages, tools=tools,
            tool_choice="auto", temperature=0.1, max_tokens=1024,
        )
    return _get_groq_client().chat.completions.create(
        model=model or LLMConfig.GROQ_MODEL, messages=messages, tools=tools,
        tool_choice="auto", temperature=0.1, max_tokens=1024,
    )


def generate_system_prompt() -> str:
    return """You answer strictly using the provided notifications.
Do not invent information or add external context. Return concise results focused
on company, date, and nature. If data is insufficient, say \"Insufficient data\"."""


def format_notifications_for_llm(notifications: List) -> str:
    if not notifications:
        return "No relevant notifications found."
    rows = []
    for i, item in enumerate(notifications, 1):
        get = (lambda *keys, default="": next((item.get(k) for k in keys if item.get(k) is not None), default)) if isinstance(item, dict) else (lambda *keys, default="": next((getattr(item, k, None) for k in keys if getattr(item, k, None) is not None), default))
        rows.append(f"[{i}] Entity: {get('entity_name', 'EntityName')}\nDate: {get('notice_date', 'Date', 'date_key', 'run_date')}\nNature: {get('notice_type', 'Nature', 'title')}\nSummary: {get('summary', 'Summary', 'full_text')}\nLink: {get('link', 'Link', 'pdf_link')}")
    return "\n\n".join(rows)
