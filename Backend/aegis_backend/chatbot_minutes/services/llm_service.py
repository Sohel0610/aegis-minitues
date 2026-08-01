"""Provider-neutral LLM client used by planning, answering, and verification.

No provider credentials are logged.  The selected providers are controlled only
through environment variables so a local demo cannot accidentally call Azure.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import groq
from openai import AzureOpenAI

from ..config import settings

logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    pass


@dataclass
class LLMResult:
    content: str
    provider: str
    model: str


class LLMService:
    """Safe ordered provider selection with one optional fallback."""

    def __init__(self) -> None:
        self._groq_client: Optional[groq.Groq] = None
        self._azure_openai_client: Optional[AzureOpenAI] = None
        self._foundry_client: Optional[AzureOpenAI] = None

    def _provider_order(self) -> List[str]:
        primary = settings.CHATBOT_LLM_PROVIDER.strip().lower()
        fallback = settings.CHATBOT_FALLBACK_LLM_PROVIDER.strip().lower()
        providers = [provider for provider in (primary, fallback) if provider]
        if not providers or providers == ["auto"]:
            providers = ["groq"] if settings.GROQ_API_KEY else ["azure_openai"]
        return list(dict.fromkeys(providers))

    def _model_for(self, provider: str) -> str:
        if provider == "groq":
            return settings.CHATBOT_LLM_MODEL or settings.GROQ_MODEL
        if provider == "azure_openai":
            return settings.CHATBOT_LLM_MODEL or settings.AZURE_OPENAI_DEPLOYMENT_NAME
        if provider in {"azure_foundry", "foundry"}:
            return settings.CHATBOT_LLM_MODEL or settings.AZURE_FOUNDRY_DEPLOYMENT
        return settings.CHATBOT_LLM_MODEL

    def generate(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> LLMResult:
        failures: List[str] = []
        for provider in self._provider_order():
            try:
                return self._generate_with_provider(
                    provider,
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens or settings.CHATBOT_MAX_OUTPUT_TOKENS,
                )
            except Exception as exc:
                # Errors are useful operationally, but never log endpoints/keys.
                logger.warning("Chatbot LLM provider '%s' failed: %s", provider, type(exc).__name__)
                failures.append(f"{provider}: {type(exc).__name__}")
        raise LLMUnavailableError("No configured language-model provider is available (" + ", ".join(failures) + ").")

    def _generate_with_provider(
        self,
        provider: str,
        messages: List[Dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
    ) -> LLMResult:
        provider = provider.lower()
        model = self._model_for(provider)
        if provider == "groq":
            if not settings.GROQ_API_KEY:
                raise LLMUnavailableError("GROQ_API_KEY is missing")
            if self._groq_client is None:
                self._groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
            response = self._groq_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return LLMResult((response.choices[0].message.content or "").strip(), provider, model)

        if provider == "azure_openai":
            if not all([settings.AZURE_OPENAI_ENDPOINT, settings.AZURE_OPENAI_API_KEY, model]):
                raise LLMUnavailableError("Azure OpenAI settings are incomplete")
            if self._azure_openai_client is None:
                self._azure_openai_client = AzureOpenAI(
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                )
            response = self._azure_openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return LLMResult((response.choices[0].message.content or "").strip(), provider, model)

        if provider in {"azure_foundry", "foundry"}:
            if not all([settings.AZURE_FOUNDRY_ENDPOINT, settings.AZURE_FOUNDRY_API_KEY, model]):
                raise LLMUnavailableError("Azure Foundry settings are incomplete")
            if self._foundry_client is None:
                # Foundry's legacy /models URL is an inference discovery route.
                # AzureOpenAI consumes the resource base and builds the stable
                # /openai/deployments/<deployment>/chat/completions request.
                endpoint = settings.AZURE_FOUNDRY_ENDPOINT.rstrip("/")
                if endpoint.endswith("/models"):
                    endpoint = endpoint[: -len("/models")]
                self._foundry_client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=settings.AZURE_FOUNDRY_API_KEY,
                    api_version=settings.AZURE_FOUNDRY_API_VERSION,
                )
            response = self._foundry_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return LLMResult((response.choices[0].message.content or "").strip(), "azure_foundry", model)

        raise LLMUnavailableError(f"Unsupported LLM provider: {provider}")

    def generate_json(
        self,
        messages: List[Dict[str, str]],
        *,
        max_tokens: int = 900,
    ) -> tuple[Dict[str, Any], LLMResult]:
        request = list(messages) + [{
            "role": "system",
            "content": "Return one valid JSON object only. Do not wrap it in Markdown or add commentary.",
        }]
        result = self.generate(request, temperature=0, max_tokens=max_tokens)
        text = result.content.strip()
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("Model did not return a JSON object")
        value = json.loads(text[start : end + 1])
        if not isinstance(value, dict):
            raise ValueError("Model JSON response is not an object")
        return value, result
