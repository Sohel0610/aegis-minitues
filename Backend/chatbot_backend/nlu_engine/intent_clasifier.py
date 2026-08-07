"""
Intent Classifier - Multi-layer intent classification system
Classifies user queries into specific intents with confidence scoring
"""

from enum import Enum
from typing import Dict, List, Tuple, Any
import re
import json
from dataclasses import dataclass


class QueryIntent(Enum):
    """Query intent types"""
    # Explicit intents
    EXPLICIT_DATA_REQUEST = "explicit_data_request"  # "Show me notifications for Adani"
    EXPLICIT_COUNT = "explicit_count"  # "How many notifications for Adani?"
    
    # Implicit intents
    IMPLICIT_ANALYSIS = "implicit_analysis"  # "What's happening with Adani?"
    IMPLICIT_SUMMARY = "implicit_summary"  # "Tell me about Adani"
    
    # Comparative intents
    COMPARATIVE_ANALYSIS = "comparative_analysis"  # "Compare Adani vs Reliance"
    COMPARATIVE_TREND = "comparative_trend"  # "Which company has more notifications?"
    
    # Temporal intents
    TEMPORAL_TREND = "temporal_trend"  # "Show trend over last 30 days"
    TEMPORAL_SPECIFIC = "temporal_specific"  # "Show December data"
    
    # Entity-specific intents
    ENTITY_DISCOVERY = "entity_discovery"  # "What companies are available?"
    ENTITY_DETAILS = "entity_details"  # "Tell me about this company"
    
    # Analytics intents
    ANALYTICS_CHART = "analytics_chart"  # "Show me a chart"
    ANALYTICS_STATISTICS = "analytics_statistics"  # "Give me statistics"
    
    # Ambiguous/Unknown
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    """Intent classification result"""
    intent: QueryIntent
    confidence: float
    sub_intents: List[QueryIntent]
    reasoning: str
    entities: List[str] = None
    date_range: List[str] = None
    regulation_types: List[str] = None


class IntentClassifier:
    """
    Multi-layer intent classification system
    Uses pattern matching and keyword analysis for intent detection
    """
    
    def __init__(self):
        # Intent patterns (regex patterns mapped to intents)
        self.intent_patterns = {
            QueryIntent.EXPLICIT_DATA_REQUEST: [
                r'\b(show|display|get|fetch|retrieve|list)\b.*\b(notification|data|information|details)\b',
                r'\b(show|give|get)\s+me\b',
                r'\bnotifications?\s+for\b',
            ],
            QueryIntent.EXPLICIT_COUNT: [
                r'\bhow\s+many\b',
                r'\bcount\s+of\b',
                r'\bnumber\s+of\b',
                r'\btotal\s+(notifications?|records?)\b',
                r'\b(?:give|show|provide)\s+(?:me\s+)?(?:a\s+)?count\b',
            ],
            QueryIntent.IMPLICIT_ANALYSIS: [
                r'\bwhat\'?s\s+happening\b',
                r'\bwhat\s+is\s+going\s+on\b',
                r'\bany\s+updates?\b',
                r'\blatest\s+news\b',
            ],
            QueryIntent.IMPLICIT_SUMMARY: [
                r'\btell\s+me\s+about\b',
                r'\bsummar(y|ize)\b',
                r'\boverview\s+of\b',
                r'\bwhat\s+do\s+you\s+know\s+about\b',
            ],
            QueryIntent.COMPARATIVE_ANALYSIS: [
                r'\bcompare\b',
                r'\bvs\b',
                r'\bversus\b',
                r'\bdifference\s+between\b',
            ],
            QueryIntent.COMPARATIVE_TREND: [
                r'\bwhich\s+(company|entity)\b.*\b(more|most|highest|lowest)\b',
                r'\btop\s+\d+\b',
                r'\branking\b',
            ],
            QueryIntent.TEMPORAL_TREND: [
                r'\btrend\b',
                r'\bover\s+(time|last|past)\b',
                r'\b(last|past)\s+\d+\s+(days?|weeks?|months?|years?)\b',
                r'\bhistorical\b',
            ],
            QueryIntent.TEMPORAL_SPECIFIC: [
                r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
                r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
                r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
                r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',  # DD-MM-YYYY or MM-DD-YYYY
            ],
            QueryIntent.ENTITY_DISCOVERY: [
                r'\bwhat\s+(companies|entities)\b',
                r'\blist\s+(all\s+)?(companies|entities)\b',
                r'\bavailable\s+(companies|entities)\b',
                r'\bshow\s+me\s+(all\s+)?(companies|entities)\b',
            ],
            QueryIntent.ENTITY_DETAILS: [
                r'\babout\s+(this|that|the)\s+(company|entity)\b',
                r'\bdetails\s+of\b',
                r'\binformation\s+on\b',
            ],
            QueryIntent.ANALYTICS_CHART: [
                r'\b(chart|graph|plot|visualization)\b',
                r'\bshow\s+me\s+a\s+(chart|graph)\b',
                r'\bvisualize\b',
            ],
            QueryIntent.ANALYTICS_STATISTICS: [
                r'\bstatistics?\b',
                r'\bstats?\b',
                r'\bmetrics?\b',
                r'\banalysis\b',
            ],
        }
        
        # Keywords for intent boosting
        self.intent_keywords = {
            QueryIntent.EXPLICIT_DATA_REQUEST: ['show', 'display', 'get', 'fetch', 'list', 'notifications'],
            QueryIntent.EXPLICIT_COUNT: ['how many', 'count', 'number', 'total'],
            QueryIntent.IMPLICIT_ANALYSIS: ['happening', 'updates', 'latest', 'news'],
            QueryIntent.IMPLICIT_SUMMARY: ['summary', 'overview', 'tell me about'],
            QueryIntent.COMPARATIVE_ANALYSIS: ['compare', 'vs', 'versus', 'difference'],
            QueryIntent.TEMPORAL_TREND: ['trend', 'over time', 'historical', 'last'],
            QueryIntent.ANALYTICS_CHART: ['chart', 'graph', 'plot', 'visualize'],
        }
    
    def classify(self, query: str) -> IntentResult:
        """
        Classify query intent with confidence scoring
        
        Args:
            query: User query string
            
        Returns:
            IntentResult with primary intent, confidence, and sub-intents
        """
        query_lower = query.lower()
        
        # Score each intent
        intent_scores: Dict[QueryIntent, float] = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            
            # Pattern matching (high weight)
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 0.5
            
            # Keyword matching (medium weight)
            if intent in self.intent_keywords:
                keywords = self.intent_keywords[intent]
                for keyword in keywords:
                    if keyword in query_lower:
                        score += 0.2
            
            if score > 0:
                intent_scores[intent] = min(score, 1.0)  # Cap at 1.0
        
        # No matches - check for ambiguous or unknown
        if not intent_scores:
            # Very short query or no clear intent
            if len(query.split()) <= 2:
                return IntentResult(
                    intent=QueryIntent.AMBIGUOUS,
                    confidence=0.8,
                    sub_intents=[],
                    reasoning="Query too short or unclear", **self._extract_entities(query)
                )
            else:
                return self._llm_fallback(query, QueryIntent.UNKNOWN, 0.6, "No matching intent patterns")
        
        # Sort by score
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        
        primary_intent, primary_score = sorted_intents[0]
        sub_intents = [intent for intent, score in sorted_intents[1:] if score >= 0.3]
        
        # Determine reasoning
        reasoning = self._generate_reasoning(primary_intent, query_lower)
        
        result = IntentResult(
            intent=primary_intent,
            confidence=primary_score,
            sub_intents=sub_intents,
            reasoning=reasoning, **self._extract_entities(query)
        )
        return self._llm_fallback(query, result.intent, result.confidence, result.reasoning) if result.confidence < 0.6 else result

    def _llm_fallback(self, query: str, default: QueryIntent, confidence: float, reasoning: str) -> IntentResult:
        """Use the LLM only for ambiguous pattern matches; graceful offline fallback."""
        try:
            from chatbot_backend.llm_layer.llm_client import chat_completion
            choices = ", ".join(intent.value for intent in QueryIntent)
            raw = chat_completion("Return strict JSON only.", f"Classify this regulatory query into one intent: {choices}. Query: {query}. Return {{\"intent\":...,\"confidence\":0..1,\"reasoning\":...}}")
            parsed = json.loads(raw)
            return IntentResult(QueryIntent(parsed["intent"]), float(parsed.get("confidence", confidence)), [], parsed.get("reasoning", reasoning), **self._extract_entities(query))
        except Exception:
            return IntentResult(default, confidence, [], reasoning, **self._extract_entities(query))

    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Cheap shared extraction so the API does not re-parse a request."""
        from chatbot_backend.utils.entity_resolver import resolve_entity
        from chatbot_backend.chat_orchestrator.router_logic import extract_dates
        entity = resolve_entity(query)
        regulation_types = re.findall(r'\b(?:bse|sebi|rbi|circulars?|disclosures?|filings?)\b', query, re.I)
        return {
            "entities": [entity["canonical"]] if entity else [],
            "date_range": extract_dates(query),
            "regulation_types": sorted(set(item.lower() for item in regulation_types)),
        }
    
    def _generate_reasoning(self, intent: QueryIntent, query: str) -> str:
        """Generate human-readable reasoning for intent classification"""
        if intent == QueryIntent.EXPLICIT_DATA_REQUEST:
            return "User explicitly requesting data/notifications"
        elif intent == QueryIntent.EXPLICIT_COUNT:
            return "User asking for count/number of items"
        elif intent == QueryIntent.IMPLICIT_ANALYSIS:
            return "User seeking analysis or updates"
        elif intent == QueryIntent.IMPLICIT_SUMMARY:
            return "User requesting summary or overview"
        elif intent == QueryIntent.COMPARATIVE_ANALYSIS:
            return "User comparing multiple entities"
        elif intent == QueryIntent.TEMPORAL_TREND:
            return "User interested in trends over time"
        elif intent == QueryIntent.TEMPORAL_SPECIFIC:
            return "User requesting data for specific time period"
        elif intent == QueryIntent.ANALYTICS_CHART:
            return "User wants visual chart/graph"
        elif intent == QueryIntent.ANALYTICS_STATISTICS:
            return "User requesting statistical analysis"
        else:
            return f"Classified as {intent.value}"
    
    def is_table_preferred(self, intent_result: IntentResult) -> bool:
        """Determine if table format is preferred for this intent"""
        table_intents = {
            QueryIntent.EXPLICIT_DATA_REQUEST,
            QueryIntent.COMPARATIVE_ANALYSIS,
            QueryIntent.ENTITY_DISCOVERY,
        }
        return intent_result.intent in table_intents
    
    def is_chart_preferred(self, intent_result: IntentResult) -> bool:
        """Determine if chart format is preferred for this intent"""
        chart_intents = {
            QueryIntent.ANALYTICS_CHART,
            QueryIntent.TEMPORAL_TREND,
            QueryIntent.COMPARATIVE_TREND,
            QueryIntent.ANALYTICS_STATISTICS,
        }
        return intent_result.intent in chart_intents


# Global instance
_intent_classifier = None

def get_intent_classifier() -> IntentClassifier:
    """Get singleton instance of IntentClassifier"""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
