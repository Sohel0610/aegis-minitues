"""
Ambiguity Resolver - Intelligent disambiguation
Resolves ambiguous queries with intelligent prompts
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class AmbiguityResult:
    """Result of ambiguity detection"""
    is_ambiguous: bool
    ambiguity_type: str  # 'database', 'entity', 'timeframe', 'none'
    options: List[str]
    suggestion: str


class AmbiguityResolver:
    """
    Resolves ambiguous queries
    Provides intelligent selection prompts
    """
    
    def __init__(self):
        # Database keywords
        self.database_keywords = {
            'bse': ['bse', 'bombay stock exchange', 'stock', 'equity', 'share'],
            'sebi': ['sebi', 'securities', 'regulatory', 'regulation'],
            'rbi': ['rbi', 'reserve bank', 'monetary', 'banking', 'interest rate']
        }
    
    def detect_ambiguity(
        self,
        query: str,
        has_entity: bool = False,
        has_timeframe: bool = False
    ) -> AmbiguityResult:
        """
        Detect if query is ambiguous
        
        Args:
            query: User query
            has_entity: Whether entity is specified
            has_timeframe: Whether timeframe is specified
            
        Returns:
            AmbiguityResult with ambiguity details
        """
        query_lower = query.lower()
        
        # Check for database ambiguity
        database_matches = []
        for db, keywords in self.database_keywords.items():
            if any(kw in query_lower for kw in keywords):
                database_matches.append(db)
        
        # Ambiguous if multiple databases match or none match
        if len(database_matches) > 1:
            return AmbiguityResult(
                is_ambiguous=True,
                ambiguity_type='database',
                options=database_matches,
                suggestion=self._generate_database_prompt(database_matches)
            )
        
        if len(database_matches) == 0 and not has_entity:
            # No clear database and no entity - could be any database
            return AmbiguityResult(
                is_ambiguous=True,
                ambiguity_type='database',
                options=['bse', 'sebi', 'rbi'],
                suggestion="I can search in BSE, SEBI, or RBI data. Which would you like to explore?"
            )
        
        # Check for entity ambiguity (very generic query)
        if not has_entity and len(query.split()) <= 3:
            return AmbiguityResult(
                is_ambiguous=True,
                ambiguity_type='entity',
                options=[],
                suggestion="Which company or entity are you interested in?"
            )
        
        # No ambiguity detected
        return AmbiguityResult(
            is_ambiguous=False,
            ambiguity_type='none',
            options=[],
            suggestion=""
        )
    
    def _generate_database_prompt(self, databases: List[str]) -> str:
        """Generate prompt for database selection"""
        db_names = {
            'bse': 'BSE (Stock Exchange)',
            'sebi': 'SEBI (Securities Regulator)',
            'rbi': 'RBI (Reserve Bank)'
        }
        
        options_str = " and ".join([db_names.get(db, db.upper()) for db in databases])
        
        return f"I found relevant data in {options_str}. Which would you like to explore?"


# Global instance
_ambiguity_resolver = None

def get_ambiguity_resolver() -> AmbiguityResolver:
    """Get singleton instance of AmbiguityResolver"""
    global _ambiguity_resolver
    if _ambiguity_resolver is None:
        _ambiguity_resolver = AmbiguityResolver()
    return _ambiguity_resolver
