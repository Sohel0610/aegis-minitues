"""
Suggestion Engine - Intelligent query suggestions
Provides autocomplete and alternative suggestions
"""

from typing import List, Dict, Any, Optional
from chatbot_backend.utils.entity_registry import ENTITY_REGISTRY


class SuggestionEngine:
    """
    Generates intelligent suggestions for user queries
    Provides autocomplete and alternatives
    """
    
    def __init__(self):
        # Common query templates
        self.query_templates = [
            "Show me notifications for {entity}",
            "What's the latest update on {entity}?",
            "Show me {entity} notifications in December",
            "Compare {entity} vs {entity}",
            "Show trend for {entity} over last 30 days",
            "How many notifications for {entity}?",
        ]
    
    def get_entity_suggestions(
        self,
        partial_query: str,
        limit: int = 5
    ) -> List[str]:
        """
        Get entity name suggestions based on partial query
        
        Args:
            partial_query: Partial user input
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested entity names
        """
        partial_lower = partial_query.lower()
        
        suggestions = []
        
        # Search in entity registry
        for canonical, aliases in ENTITY_REGISTRY.items():
            # Check canonical name
            if partial_lower in canonical.lower():
                suggestions.append(canonical)
            
            # Check aliases
            for alias in aliases:
                if partial_lower in alias.lower() and alias not in suggestions:
                    suggestions.append(alias)
        
        return suggestions[:limit]
    
    def get_query_suggestions(
        self,
        partial_query: str,
        limit: int = 5
    ) -> List[str]:
        """
        Get complete query suggestions
        
        Args:
            partial_query: Partial user input
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested complete queries
        """
        suggestions = []
        
        # If query is very short, suggest templates
        if len(partial_query.split()) <= 2:
            # Get entity suggestions
            entities = self.get_entity_suggestions(partial_query, limit=3)
            
            # Generate template-based suggestions
            for entity in entities:
                suggestions.append(f"Show me notifications for {entity}")
                if len(suggestions) >= limit:
                    break
        
        return suggestions
    
    def suggest_alternatives(
        self,
        failed_query: str,
        available_entities: List[str]
    ) -> str:
        """
        Suggest alternatives when query fails
        
        Args:
            failed_query: Query that returned no results
            available_entities: List of available entities
            
        Returns:
            Suggestion message
        """
        if not available_entities:
            return "No data available. Please try a different query."
        
        # Show top 5 available entities
        top_entities = available_entities[:5]
        entities_str = ", ".join(top_entities)
        
        return f"No data found for your query. Available entities include: {entities_str}"


# Global instance
_suggestion_engine = None

def get_suggestion_engine() -> SuggestionEngine:
    """Get singleton instance of SuggestionEngine"""
    global _suggestion_engine
    if _suggestion_engine is None:
        _suggestion_engine = SuggestionEngine()
    return _suggestion_engine
