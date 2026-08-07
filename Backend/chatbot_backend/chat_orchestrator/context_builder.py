"""Bounded, relevant context construction for all LLM calls."""
from typing import Iterable, List, Optional
from chatbot_backend.llm_layer.llm_client import format_notifications_for_llm

class ContextBuilder:
    def __init__(self, max_context_tokens: int = 6000):
        self.max_context_tokens = max_context_tokens

    @staticmethod
    def count_tokens(text: str) -> int:
        try:
            import tiktoken
            return len(tiktoken.get_encoding("cl100k_base").encode(text))
        except Exception:
            return max(1, len(text) // 4)

    def notifications(self, records: Iterable, reserve_tokens: int = 1200) -> str:
        """Keep highest-ranked records that fit; never allow silent model truncation."""
        budget = max(512, self.max_context_tokens - reserve_tokens)
        kept: List = []
        for record in records:
            candidate = format_notifications_for_llm(kept + [record])
            if self.count_tokens(candidate) > budget:
                break
            kept.append(record)
        return format_notifications_for_llm(kept)

    def history(self, query: str, turns: Iterable, max_turns: int = 6) -> str:
        words = set(query.lower().split())
        ranked = sorted(turns, key=lambda turn: len(words.intersection(set(turn.user_query.lower().split()))), reverse=True)
        selected = ranked[:4]
        for turn in list(turns)[-2:]:
            if turn not in selected:
                selected.append(turn)
        return "\n".join(f"User: {turn.user_query}\nAssistant: {turn.bot_response[:500]}" for turn in selected[-max_turns:])

context_builder = ContextBuilder()
