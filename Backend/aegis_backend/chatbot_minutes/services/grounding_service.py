"""Deterministic grounding, numerical checks, and confidence explanation."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class GroundingAssessment:
    confidence: str
    reason: str
    evidence_found: bool
    numerical_claims_verified: bool
    potential_conflicts: List[str]

    def as_dict(self) -> Dict[str, object]:
        return {
            "confidence": self.confidence,
            "reason": self.reason,
            "evidence_found": self.evidence_found,
            "numerical_claims_verified": self.numerical_claims_verified,
            "potential_conflicts": self.potential_conflicts,
        }


class GroundingService:
    @staticmethod
    def assess(answer: str, chunks: List[Dict], tool_results: List[Dict], conflicts: List[str]) -> GroundingAssessment:
        evidence = "\n".join(
            [chunk.get("expanded_text", chunk.get("text", "")) for chunk in chunks]
            + [result.get("text", "") for result in tool_results]
        )
        if not evidence.strip():
            return GroundingAssessment("low", "No matching document or structured-record evidence was found.", False, True, conflicts)
        answer_numbers = GroundingService._numbers(answer)
        evidence_numbers = GroundingService._numbers(evidence)
        numbers_verified = all(number in evidence_numbers for number in answer_numbers)
        top_score = max((chunk.get("score", 0) for chunk in chunks), default=0)
        if conflicts:
            confidence, reason = "medium", "Relevant evidence was found, but potentially conflicting wording needs review."
        elif not numbers_verified:
            confidence, reason = "medium", "Relevant evidence was found, but one or more numeric statements could not be directly verified."
        elif top_score >= 0.42 or tool_results:
            confidence, reason = "high", "The response is grounded in relevant retrieved evidence."
        else:
            confidence, reason = "medium", "The response is grounded in limited or broadly related evidence."
        return GroundingAssessment(confidence, reason, True, numbers_verified, conflicts)

    @staticmethod
    def _numbers(text: str) -> set[str]:
        raw = re.findall(r"(?<![A-Za-z])(?:₹|INR\s*)?\d[\d,]*(?:\.\d+)?%?", text, flags=re.IGNORECASE)
        return {value.lower().replace(",", "").replace("inr", "").strip() for value in raw}
