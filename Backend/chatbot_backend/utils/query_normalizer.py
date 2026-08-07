from rapidfuzz import process, fuzz

# Words that must NEVER change
PROTECTED_TERMS = {
    "rbi", "sebi", "bse",
    "nbfc", "ipo", "fpi", "fii",
    "bank", "banks"
}

# Financial / regulatory vocabulary
DOMAIN_TERMS = [
    "notification", "notifications", "circular", "circulars",
    "energy", "bank", "banks", "finance",
    "penalty", "fine", "dividend", "buyback",
    "credit", "rating", "merger", "acquisition",
    "appointment", "resignation", "policy"
]

def normalize_query(query: str) -> str:
    """
    Fix common typos without damaging regulatory terms
    """
    words = query.split()
    normalized = []

    for word in words:
        lw = word.lower()

        # Skip protected terms
        if lw in PROTECTED_TERMS:
            normalized.append(word)
            continue

        # Find closest domain term
        match, score, _ = process.extractOne(
            lw, DOMAIN_TERMS, scorer=fuzz.ratio
        )

        if score >= 80:
            normalized.append(match)
        else:
            normalized.append(word)

    return " ".join(normalized)
