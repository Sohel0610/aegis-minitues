"""
Entity Resolver - ENHANCED with Fuzzy Matching
Integrates advanced NLU fuzzy matcher for typo tolerance
"""
 
from chatbot_backend.utils.entity_registry import ENTITY_REGISTRY
from rapidfuzz import process, fuzz
import re

# Import fuzzy matcher if available
try:
    from chatbot_backend.nlu_engine.fuzzy_matcher import get_fuzzy_matcher
    FUZZY_MATCHER_AVAILABLE = True
except ImportError:
    FUZZY_MATCHER_AVAILABLE = False
    print("Warning: Fuzzy matcher not available, using basic matching only")
 
AMBIGUOUS_ALIASES = {
    "idea",
}

UNSAFE_SQL_ALIASES = {
    "green energy",
}


def _alias_in_query(alias: str, query: str) -> bool:
    alias = alias.lower().strip()
    query = query.lower()

    if not alias:
        return False

    # Avoid accidental substring matches like "vi" inside "civil".
    pattern = r"\b" + re.escape(alias) + r"\b"
    if not re.search(pattern, query):
        return False

    # Avoid overly generic aliases causing false entity locks.
    if alias in AMBIGUOUS_ALIASES:
        return False

    return True


def get_searchable_aliases(entity_aliases):
    """
    Return aliases that are safe to use in SQL LIKE filters and strict matching.
    Avoid generic phrases that can pull unrelated companies.
    """
    safe_aliases = []
    for alias in entity_aliases or []:
        alias_lower = alias.lower().strip()
        if not alias_lower:
            continue
        if alias_lower in AMBIGUOUS_ALIASES or alias_lower in UNSAFE_SQL_ALIASES:
            continue
        safe_aliases.append(alias)
    return safe_aliases


def resolve_entity(query: str):
    """
    Resolve entity from query with fuzzy matching support
    
    Args:
        query: User query string
        
    Returns:
        Dict with canonical name and aliases, or None if not found
    """
    q = query.lower()
    
    # Step 1: Exact substring match (fastest)
    for canonical, aliases in ENTITY_REGISTRY.items():
        for alias in aliases:
            if _alias_in_query(alias, q):
                return {"canonical": canonical, "aliases": aliases}
    
    # Step 2: Use advanced fuzzy matcher if available
    if FUZZY_MATCHER_AVAILABLE:
        try:
            fuzzy_matcher = get_fuzzy_matcher()
            result = fuzzy_matcher.match_entity(query, ENTITY_REGISTRY, threshold=0.75)
            
            if result and result.confidence >= 0.75:
                # Get aliases for matched entity
                aliases = ENTITY_REGISTRY.get(result.matched_text, [result.matched_text])
                print(f"[FUZZY_MATCH] '{query}' → '{result.matched_text}' (confidence: {result.confidence:.2f}, type: {result.match_type})")
                return {"canonical": result.matched_text, "aliases": aliases}
        except Exception as e:
            print(f"[FUZZY_MATCH_ERROR] {e}")
            # Fall through to basic fuzzy matching
    
    # Step 3: Basic rapidfuzz matching (fallback)
    all_aliases = []
    alias_to_canonical = {}
    
    for canonical, aliases in ENTITY_REGISTRY.items():
        for alias in aliases:
            all_aliases.append(alias.lower())
            alias_to_canonical[alias.lower()] = canonical
    
    words = q.split()
    
    # Try multi-word phrases first
    for length in [4, 3, 2]:
        for i in range(len(words) - length + 1):
            phrase = " ".join(words[i:i+length])
            match = process.extractOne(phrase, all_aliases, scorer=fuzz.ratio, score_cutoff=85)
            
            if match:
                matched_alias = match[0]
                canonical = alias_to_canonical[matched_alias]
                print(f"[BASIC_FUZZY] '{phrase}' → '{canonical}' (score: {match[1]})")
                return {"canonical": canonical, "aliases": ENTITY_REGISTRY[canonical]}
    
    return None
 
 
def _entity_match(notification, entity_aliases):
    """
    FIXED matching function
    Checks if notification matches any of the entity aliases
    """
    company = None
    
    if hasattr(notification, "EntityName"):
        company = notification.EntityName
    elif hasattr(notification, "entity_name"):
        company = notification.entity_name
    elif isinstance(notification, dict):
        company = notification.get("company") or notification.get("EntityName") or notification.get("entity_name")
    
    if not company:
        return False
    
    company_lower = company.lower().strip()
    
    for alias in get_searchable_aliases(entity_aliases):
        alias_lower = alias.lower().strip()
        
        pattern = r"\b" + re.escape(alias_lower) + r"\b"
        if re.search(pattern, company_lower):
            return True

        if company_lower == alias_lower:
            return True
    
    return False
