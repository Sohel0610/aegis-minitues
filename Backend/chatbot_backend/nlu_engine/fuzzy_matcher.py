"""
Fuzzy Matcher - Typo tolerance and semantic matching
Handles misspellings, phonetic matching, and semantic similarity
"""

from typing import List, Optional, Tuple, Dict
import re
from dataclasses import dataclass

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    print("Warning: rapidfuzz not available, fuzzy matching will be limited")

try:
    import jellyfish
    JELLYFISH_AVAILABLE = True
except ImportError:
    JELLYFISH_AVAILABLE = False
    print("Warning: jellyfish not available, phonetic matching disabled")


@dataclass
class FuzzyMatchResult:
    """Result of fuzzy matching"""
    matched_text: str
    original_text: str
    confidence: float
    match_type: str  # 'exact', 'fuzzy', 'phonetic', 'semantic'


class FuzzyMatcher:
    """
    Advanced fuzzy matching for entity names and regulatory bodies
    Handles typos, phonetic similarities, and common misspellings
    """
    
    def __init__(self):
        # Common misspellings and corrections
        self.known_corrections = {
            # Regulatory bodies
            'seby': 'sebi',
            'sebbi': 'sebi',
            'sebii': 'sebi',
            'rbbi': 'rbi',
            'rbii': 'rbi',
            
            # Common company misspellings
            'adnai': 'adani',
            'adanni': 'adani',
            'relince': 'reliance',
            'relianse': 'reliance',
            'tata': 'tata',
            'infosys': 'infosys',
            'wipro': 'wipro',
        }
        
        # Phonetic cache for performance
        self._phonetic_cache: Dict[str, str] = {}
    
    def match_entity(
        self,
        query_text: str,
        entity_registry: Dict[str, List[str]],
        threshold: float = 0.75
    ) -> Optional[FuzzyMatchResult]:
        """
        Match query text against entity registry with fuzzy matching
        
        Args:
            query_text: Text to match
            entity_registry: Dict of canonical names to aliases
            threshold: Minimum confidence threshold (0.0 to 1.0)
            
        Returns:
            FuzzyMatchResult if match found, None otherwise
        """
        query_lower = query_text.lower().strip()
        
        # Step 1: Check known corrections first
        for typo, correction in self.known_corrections.items():
            if typo in query_lower:
                # Check if correction exists in registry
                for canonical, aliases in entity_registry.items():
                    if correction in canonical.lower() or any(correction in alias.lower() for alias in aliases):
                        return FuzzyMatchResult(
                            matched_text=canonical,
                            original_text=query_text,
                            confidence=0.95,
                            match_type='known_correction'
                        )
        
        # Step 2: Exact match (case-insensitive)
        for canonical, aliases in entity_registry.items():
            all_names = [canonical] + aliases
            for name in all_names:
                if query_lower == name.lower():
                    return FuzzyMatchResult(
                        matched_text=canonical,
                        original_text=query_text,
                        confidence=1.0,
                        match_type='exact'
                    )
        
        # Step 3: Substring match
        for canonical, aliases in entity_registry.items():
            all_names = [canonical] + aliases
            for name in all_names:
                if query_lower in name.lower() or name.lower() in query_lower:
                    return FuzzyMatchResult(
                        matched_text=canonical,
                        original_text=query_text,
                        confidence=0.9,
                        match_type='substring'
                    )
        
        # Step 4: Fuzzy string matching (Levenshtein-based)
        if RAPIDFUZZ_AVAILABLE:
            best_match = self._fuzzy_string_match(query_lower, entity_registry, threshold)
            if best_match:
                return best_match
        
        # Step 5: Phonetic matching (Soundex/Metaphone)
        if JELLYFISH_AVAILABLE:
            phonetic_match = self._phonetic_match(query_lower, entity_registry, threshold)
            if phonetic_match:
                return phonetic_match
        
        return None
    
    def _fuzzy_string_match(
        self,
        query: str,
        entity_registry: Dict[str, List[str]],
        threshold: float
    ) -> Optional[FuzzyMatchResult]:
        """Fuzzy string matching using Levenshtein distance"""
        if not RAPIDFUZZ_AVAILABLE:
            return None
        
        # Build list of all possible names
        all_names = []
        name_to_canonical = {}
        
        for canonical, aliases in entity_registry.items():
            for name in [canonical] + aliases:
                name_lower = name.lower()
                all_names.append(name_lower)
                name_to_canonical[name_lower] = canonical
        
        # Find best match
        result = process.extractOne(
            query,
            all_names,
            scorer=fuzz.ratio,
            score_cutoff=threshold * 100  # rapidfuzz uses 0-100 scale
        )
        
        if result:
            matched_name, score, _ = result
            canonical = name_to_canonical[matched_name]
            confidence = score / 100.0  # Convert to 0-1 scale
            
            return FuzzyMatchResult(
                matched_text=canonical,
                original_text=query,
                confidence=confidence,
                match_type='fuzzy'
            )
        
        return None
    
    def _phonetic_match(
        self,
        query: str,
        entity_registry: Dict[str, List[str]],
        threshold: float
    ) -> Optional[FuzzyMatchResult]:
        """Phonetic matching using Soundex and Metaphone"""
        if not JELLYFISH_AVAILABLE:
            return None
        
        # Get phonetic representation of query
        query_soundex = self._get_soundex(query)
        query_metaphone = self._get_metaphone(query)
        
        best_match = None
        best_score = 0.0
        
        for canonical, aliases in entity_registry.items():
            for name in [canonical] + aliases:
                name_lower = name.lower()
                
                # Compare phonetic representations
                name_soundex = self._get_soundex(name_lower)
                name_metaphone = self._get_metaphone(name_lower)
                
                # Soundex match
                if query_soundex and name_soundex and query_soundex == name_soundex:
                    score = 0.85  # High confidence for soundex match
                    if score > best_score:
                        best_score = score
                        best_match = canonical
                
                # Metaphone match
                if query_metaphone and name_metaphone and query_metaphone == name_metaphone:
                    score = 0.85  # High confidence for metaphone match
                    if score > best_score:
                        best_score = score
                        best_match = canonical
        
        if best_match and best_score >= threshold:
            return FuzzyMatchResult(
                matched_text=best_match,
                original_text=query,
                confidence=best_score,
                match_type='phonetic'
            )
        
        return None
    
    def _get_soundex(self, text: str) -> Optional[str]:
        """Get Soundex phonetic representation with caching"""
        if text in self._phonetic_cache:
            return self._phonetic_cache.get(f"soundex_{text}")
        
        try:
            # Extract first word for phonetic matching
            first_word = text.split()[0] if text else ""
            if first_word:
                soundex = jellyfish.soundex(first_word)
                self._phonetic_cache[f"soundex_{text}"] = soundex
                return soundex
        except:
            pass
        
        return None
    
    def _get_metaphone(self, text: str) -> Optional[str]:
        """Get Metaphone phonetic representation with caching"""
        if text in self._phonetic_cache:
            return self._phonetic_cache.get(f"metaphone_{text}")
        
        try:
            # Extract first word for phonetic matching
            first_word = text.split()[0] if text else ""
            if first_word:
                metaphone = jellyfish.metaphone(first_word)
                self._phonetic_cache[f"metaphone_{text}"] = metaphone
                return metaphone
        except:
            pass
        
        return None
    
    def correct_regulatory_body(self, text: str) -> str:
        """
        Correct common misspellings of regulatory bodies
        
        Args:
            text: Text potentially containing regulatory body names
            
        Returns:
            Corrected text
        """
        text_lower = text.lower()
        
        # Check for regulatory body misspellings
        regulatory_corrections = {
            r'\bseby\b': 'SEBI',
            r'\bsebbi\b': 'SEBI',
            r'\bsebii\b': 'SEBI',
            r'\brbbi\b': 'RBI',
            r'\brbii\b': 'RBI',
        }
        
        corrected = text
        for pattern, replacement in regulatory_corrections.items():
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        
        return corrected


# Global instance
_fuzzy_matcher = None

def get_fuzzy_matcher() -> FuzzyMatcher:
    """Get singleton instance of FuzzyMatcher"""
    global _fuzzy_matcher
    if _fuzzy_matcher is None:
        _fuzzy_matcher = FuzzyMatcher()
    return _fuzzy_matcher
