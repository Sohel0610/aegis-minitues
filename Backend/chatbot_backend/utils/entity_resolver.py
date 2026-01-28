"""

Entity Resolver - REQUIREMENT 4 COMPLIANT

"""
 
from chatbot_backend.utils.entity_registry import ENTITY_REGISTRY

from rapidfuzz import process, fuzz
 
def resolve_entity(query: str):

    q = query.lower()

    for canonical, aliases in ENTITY_REGISTRY.items():

        for alias in aliases:

            if alias.lower() in q:

                return {"canonical": canonical, "aliases": aliases}

    all_aliases = []

    alias_to_canonical = {}

    for canonical, aliases in ENTITY_REGISTRY.items():

        for alias in aliases:

            all_aliases.append(alias.lower())

            alias_to_canonical[alias.lower()] = canonical

    words = q.split()

    for length in [4, 3, 2]:

        for i in range(len(words) - length + 1):

            phrase = " ".join(words[i:i+length])

            match = process.extractOne(phrase, all_aliases, scorer=fuzz.ratio, score_cutoff=85)

            if match:

                matched_alias = match[0]

                canonical = alias_to_canonical[matched_alias]

                return {"canonical": canonical, "aliases": ENTITY_REGISTRY[canonical]}

    return None
 
 
def _entity_match(notification, entity_aliases):

    """FIXED matching function"""

    company = None

    if hasattr(notification, "EntityName"):

        company = notification.EntityName

    elif hasattr(notification, "entity_name"):

        company = notification.entity_name

    elif isinstance(notification, dict):

        company = notification.get("company") or notification.get("EntityName")

    if not company:

        return False

    company_lower = company.lower().strip()

    for alias in entity_aliases:

        alias_lower = alias.lower().strip()

        if alias_lower in company_lower or company_lower in alias_lower:

            return True

    return False
 