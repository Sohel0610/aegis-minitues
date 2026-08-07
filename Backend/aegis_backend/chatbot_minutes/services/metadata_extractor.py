"""Extract structured meeting metadata from document text at upload time.

Uses the configured LLM to pull meeting identity fields (title, date, type,
participants, topics, decisions, summary) from the first portion of a document.
Falls back to regex-based heuristic extraction if the LLM is unavailable.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from .llm_service import LLMService, LLMUnavailableError

logger = logging.getLogger(__name__)

# Maximum characters sent to the LLM for metadata extraction.  Most MOM
# headers, agendas, and participant lists appear in the first 6 000 characters.
_MAX_EXTRACTION_CHARS = 6000

# Known meeting-type keywords mapped to canonical labels.
_MEETING_TYPE_PATTERNS: List[tuple[str, str]] = [
    (r"\bboard\s+(?:of\s+directors?\s+)?meeting\b", "board_meeting"),
    (r"\baudit\s+committee\b", "audit_committee"),
    (r"\bnomination\s+(?:and\s+)?remuneration\s+committee\b", "nomination_remuneration_committee"),
    (r"\bstakeholders?\s+relationship\s+committee\b", "stakeholder_relationship_committee"),
    (r"\brisk\s+management\s+committee\b", "risk_management_committee"),
    (r"\bcsr\s+committee\b", "csr_committee"),
    (r"\bannual\s+general\s+meeting\b|\bagm\b", "AGM"),
    (r"\bextraordinary\s+general\s+meeting\b|\begm\b", "EGM"),
    (r"\bvendor\s+review\b", "vendor_review"),
    (r"\bproject\s+review\b", "project_review"),
    (r"\binternal\s+review\b", "internal_review"),
    (r"\bcommittee\s+meeting\b", "committee_meeting"),
    (r"\bteam\s+meeting\b", "team_meeting"),
    (r"\bstandup\b|\bstand-up\b", "standup"),
    (r"\bretrospective\b", "retrospective"),
    (r"\btownhall\b|\btown\s+hall\b", "townhall"),
]

# Date patterns for heuristic extraction.
_DATE_PATTERNS = [
    # "12 March 2026", "March 12, 2026"
    (r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b", "dmy"),
    (r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b", "mdy"),
    # "12/03/2026", "2026-03-12"
    (r"\b(\d{4})-(\d{2})-(\d{2})\b", "iso"),
    (r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", "slash"),
]

_MONTH_MAP = {
    month.lower(): index
    for index, month in enumerate(
        ["January", "February", "March", "April", "May", "June",
         "July", "August", "September", "October", "November", "December"],
        1,
    )
}


class MeetingMetadataExtractor:
    """Extracts structured meeting metadata from document text."""

    def __init__(self, llm_service: Optional[LLMService] = None) -> None:
        self._llm = llm_service or LLMService()

    def extract(self, text: str, filename: str) -> Dict[str, Any]:
        """Return a dict of meeting metadata fields.

        Tries the LLM first for high-quality extraction, then falls back to a
        deterministic regex-based heuristic.
        """
        if not text or not text.strip():
            return self._empty_result()
        try:
            result = self._llm_extract(text[:_MAX_EXTRACTION_CHARS], filename)
            result = self._validate_and_clean(result)
            logger.info("LLM metadata extraction succeeded for '%s'", filename)
            return result
        except Exception as exc:
            logger.warning(
                "LLM metadata extraction failed for '%s' (%s), using heuristic fallback",
                filename, type(exc).__name__,
            )
            result = self._heuristic_extract(text[:_MAX_EXTRACTION_CHARS], filename)
            return self._validate_and_clean(result)

    # ------------------------------------------------------------------
    # LLM-based extraction
    # ------------------------------------------------------------------

    def _llm_extract(self, text: str, filename: str) -> Dict[str, Any]:
        system_prompt = """You are a document metadata extractor for enterprise meeting documents.
Analyse the supplied document text and extract structured meeting metadata.
Return one valid JSON object with exactly these fields (use null for unknown values):
{
  "meeting_title": "string — concise meeting title",
  "meeting_date": "YYYY-MM-DD or null",
  "meeting_type": "one of: board_meeting, audit_committee, nomination_remuneration_committee, stakeholder_relationship_committee, risk_management_committee, csr_committee, AGM, EGM, vendor_review, project_review, internal_review, committee_meeting, team_meeting, standup, retrospective, townhall, other",
  "company_name": "string — the company or organisation name, or null",
  "project_name": "string — the project/initiative being discussed, or null",
  "participants": [{"name": "Full Name", "role": "Role/Designation"}],
  "chairperson": "string or null",
  "agenda_summary": "string — 1-3 sentence summary of the agenda",
  "key_topics": ["topic1", "topic2"],
  "key_decisions": ["decision1", "decision2"],
  "action_items_summary": [{"task": "...", "owner": "...", "deadline": "..."}],
  "meeting_summary": "string — 3-5 sentence summary of the entire meeting/document"
}
Do not invent participants or decisions that are not mentioned in the text.
If the document is not a meeting document, still extract as much as possible and set meeting_type to 'other'."""

        user_content = f"FILENAME: {filename}\n\nDOCUMENT TEXT:\n{text}"

        result, _ = self._llm.generate_json(
            [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}],
            max_tokens=1200,
        )
        return result

    # ------------------------------------------------------------------
    # Heuristic fallback
    # ------------------------------------------------------------------

    def _heuristic_extract(self, text: str, filename: str) -> Dict[str, Any]:
        """Regex-based fallback when LLM is unavailable."""
        result = self._empty_result()

        # Meeting type
        lower = text.lower()
        for pattern, label in _MEETING_TYPE_PATTERNS:
            if re.search(pattern, lower):
                result["meeting_type"] = label
                break

        # Meeting date
        result["meeting_date"] = self._extract_date_heuristic(text)

        # Meeting title — try common header patterns
        title_match = re.search(
            r"(?:minutes\s+of\s+(?:the\s+)?|meeting\s+title\s*[:\-]\s*)(.+?)(?:\n|$)",
            text, re.IGNORECASE,
        )
        if title_match:
            result["meeting_title"] = title_match.group(1).strip()[:500]
        elif result["meeting_type"] and result["meeting_type"] != "other":
            result["meeting_title"] = result["meeting_type"].replace("_", " ").title()

        # Company name — look for common patterns
        company_match = re.search(
            r"(?:company\s*[:\-]\s*|of\s+(?:the\s+)?)((?:[A-Z][A-Za-z]+\s+){1,4}(?:Limited|Ltd|Inc|Corp|Pvt|Private|Group|Enterprises|Infrastructure|Power|Energy|Green|Ports))",
            text,
        )
        if company_match:
            result["company_name"] = company_match.group(1).strip()

        # Participants — look for "Present:", "Attendees:", "Members Present:" sections
        participants_section = re.search(
            r"(?:present|attendees?|members\s+present|participants?)\s*[:\-]\s*\n?((?:.*\n?){1,20}?)(?:\n\s*\n|\bAbsent|\bAgenda|\bItem|\bSr\.?\s*No)",
            text, re.IGNORECASE,
        )
        if participants_section:
            lines = participants_section.group(1).strip().splitlines()
            participants = []
            for line in lines[:15]:
                name = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
                name = re.sub(r"\s*[-–]\s*$", "", name).strip()
                if name and len(name) > 2 and len(name) < 200:
                    participants.append({"name": name, "role": ""})
            result["participants"] = participants

        # Chairperson
        chair_match = re.search(r"(?:chair(?:man|person|ed by)?)\s*[:\-]\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if chair_match:
            result["chairperson"] = chair_match.group(1).strip()[:255]

        # Key topics — extract from agenda items or numbered items
        topics = []
        for match in re.finditer(r"(?:^|\n)\s*(?:\d+[\.\)]\s*|Item\s+\d+\s*[:\-]\s*)(.+?)(?:\n|$)", text):
            topic = match.group(1).strip()
            if topic and len(topic) > 3 and len(topic) < 300:
                topics.append(topic[:200])
        result["key_topics"] = topics[:10]

        # Generate a minimal summary from the filename
        result["meeting_summary"] = f"Document '{filename}' uploaded for meeting analysis."

        result["extraction_confidence"] = "heuristic"
        return result

    @staticmethod
    def _extract_date_heuristic(text: str) -> Optional[str]:
        """Try multiple date formats, prefer the earliest date found in the header area."""
        header = text[:2000]  # Dates are typically near the top
        candidates: List[date] = []

        for pattern, fmt in _DATE_PATTERNS:
            for match in re.finditer(pattern, header, re.IGNORECASE):
                try:
                    if fmt == "dmy":
                        day, month_str, year = match.group(1), match.group(2), match.group(3)
                        candidates.append(date(int(year), _MONTH_MAP[month_str.lower()], int(day)))
                    elif fmt == "mdy":
                        month_str, day, year = match.group(1), match.group(2), match.group(3)
                        candidates.append(date(int(year), _MONTH_MAP[month_str.lower()], int(day)))
                    elif fmt == "iso":
                        year, month, day = match.group(1), match.group(2), match.group(3)
                        candidates.append(date(int(year), int(month), int(day)))
                    elif fmt == "slash":
                        part1, part2, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                        # Ambiguous: try DD/MM/YYYY first (common in Indian business docs)
                        if part1 <= 31 and part2 <= 12:
                            candidates.append(date(year, part2, part1))
                        elif part1 <= 12 and part2 <= 31:
                            candidates.append(date(year, part1, part2))
                except (ValueError, KeyError):
                    continue

        if not candidates:
            return None
        # Return the first valid date (closest to the document header)
        return candidates[0].isoformat()

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _empty_result() -> Dict[str, Any]:
        return {
            "meeting_title": None,
            "meeting_date": None,
            "meeting_type": None,
            "company_name": None,
            "project_name": None,
            "participants": [],
            "chairperson": None,
            "agenda_summary": None,
            "key_topics": [],
            "key_decisions": [],
            "action_items_summary": [],
            "meeting_summary": None,
            "extraction_confidence": "auto",
        }

    @staticmethod
    def _validate_and_clean(result: Dict[str, Any]) -> Dict[str, Any]:
        """Normalise types and truncate fields to model column limits."""
        clean = MeetingMetadataExtractor._empty_result()

        for key in ("meeting_title", "company_name", "project_name", "chairperson"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                clean[key] = value.strip()[:500 if key == "meeting_title" else 255]

        for key in ("agenda_summary", "meeting_summary"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                clean[key] = value.strip()

        # Meeting type
        meeting_type = result.get("meeting_type")
        if isinstance(meeting_type, str) and meeting_type.strip():
            clean["meeting_type"] = meeting_type.strip().lower().replace(" ", "_")[:100]

        # Meeting date
        raw_date = result.get("meeting_date")
        if isinstance(raw_date, str) and raw_date.strip():
            try:
                parsed = datetime.strptime(raw_date.strip()[:10], "%Y-%m-%d").date()
                clean["meeting_date"] = parsed.isoformat()
            except ValueError:
                pass

        # Lists
        for key in ("key_topics", "key_decisions"):
            value = result.get(key)
            if isinstance(value, list):
                clean[key] = [str(item)[:300] for item in value if item][:15]

        # Participants
        participants = result.get("participants")
        if isinstance(participants, list):
            clean["participants"] = [
                {"name": str(p.get("name", ""))[:255], "role": str(p.get("role", ""))[:255]}
                for p in participants
                if isinstance(p, dict) and p.get("name")
            ][:30]

        # Action items
        action_items = result.get("action_items_summary")
        if isinstance(action_items, list):
            clean["action_items_summary"] = [
                {
                    "task": str(item.get("task", ""))[:500],
                    "owner": str(item.get("owner", ""))[:255],
                    "deadline": str(item.get("deadline", ""))[:100],
                }
                for item in action_items
                if isinstance(item, dict) and item.get("task")
            ][:20]

        clean["extraction_confidence"] = result.get("extraction_confidence", "auto")
        return clean
