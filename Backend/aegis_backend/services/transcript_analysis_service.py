"""
AI Transcript Analysis Service
Runs multiple AI analyses on meeting transcripts: sentiment, topics, risks, speaker stats, decisions.
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class TranscriptAnalysisService:
    """Run multiple AI-powered analyses on a meeting transcript."""

    MAX_CHUNK_CHARS = 12000

    def __init__(self):
        self._llm_client = None

    def _get_llm_client(self):
        """Get Azure OpenAI client."""
        if self._llm_client:
            return self._llm_client

        try:
            from openai import AzureOpenAI

            endpoint = os.environ.get('LLM_ENDPOINT') or os.environ.get('AZURE_OPENAI_ENDPOINT')
            api_key = os.environ.get('LLM_API_KEY') or os.environ.get('AZURE_OPENAI_API_KEY')
            api_version = os.environ.get('AZURE_API_VERSION') or os.environ.get('AZURE_OPENAI_API_VERSION', '2023-05-15')

            if endpoint and api_key:
                self._llm_client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=api_key,
                    api_version=api_version,
                )
                return self._llm_client
        except ImportError:
            pass
        return None

    def _get_deployment_name(self) -> str:
        return (
            os.environ.get('LLM_DEPLOYMENT')
            or os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME')
            or 'gpt-4'
        )

    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 3000) -> Optional[str]:
        """Make an LLM call with Groq fallback."""
        client = self._get_llm_client()
        if client:
            try:
                response = client.chat.completions.create(
                    model=self._get_deployment_name(),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                return content.strip() if content else None
            except Exception as e:
                logger.error(f"Azure OpenAI analysis call failed: {e}")

        # Fallback to Groq
        groq_key = os.environ.get('GROQ_API_KEY')
        if groq_key:
            try:
                from groq import Groq
                groq_client = Groq(api_key=groq_key)
                model = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
                completion = groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens,
                )
                content = completion.choices[0].message.content
                return content.strip() if content else None
            except Exception as e:
                logger.error(f"Groq analysis fallback failed: {e}")

        return None

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parse LLM response as JSON, handling markdown fences."""
        if not response:
            return None
        cleaned = response.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('\n', 1)[1] if '\n' in cleaned else cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        if cleaned.startswith('json'):
            cleaned = cleaned[4:].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Could not parse analysis JSON response")
            return None

    def run_all_analyses(
        self,
        transcript_text: str,
        structured_segments: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Run all analysis types and return combined results.

        Args:
            transcript_text: Full readable transcript text
            structured_segments: Optional parsed VTT segments

        Returns:
            Dict with results keyed by analysis type
        """
        truncated = transcript_text[:self.MAX_CHUNK_CHARS]
        results = {}

        # Run each analysis
        sentiment = self.analyze_sentiment(truncated)
        if sentiment:
            results["sentiment"] = sentiment

        decisions = self.extract_key_decisions(truncated)
        if decisions:
            results["key_decisions"] = decisions

        risks = self.analyze_risk_compliance(truncated)
        if risks:
            results["risk_compliance"] = risks

        topics = self.analyze_topic_distribution(truncated)
        if topics:
            results["topic_distribution"] = topics

        # Speaker stats from structured segments (no LLM needed)
        if structured_segments:
            results["speaker_stats"] = self.compute_speaker_stats(structured_segments)

        return {
            "success": True,
            "insights": results,
            "analysis_count": len(results),
            "analyzed_at": datetime.now().isoformat(),
        }

    def analyze_sentiment(self, transcript_text: str) -> Optional[Dict]:
        """Analyze per-speaker sentiment and overall meeting mood."""
        system_prompt = "You are a meeting sentiment analyzer. Respond only with valid JSON."
        user_prompt = f"""Analyze the sentiment of this meeting transcript. For each speaker, provide their overall sentiment and notable emotional moments.

TRANSCRIPT:
{transcript_text}

Return JSON:
{{
    "overall_sentiment": "positive/neutral/negative/mixed",
    "overall_score": 0.0 to 1.0 (0=very negative, 1=very positive),
    "meeting_mood": "brief description of overall meeting atmosphere",
    "speaker_sentiments": [
        {{
            "speaker": "Name",
            "sentiment": "positive/neutral/negative/mixed",
            "score": 0.0 to 1.0,
            "notable_moments": ["brief description of emotional moments"]
        }}
    ],
    "tension_points": ["any moments of disagreement or tension"]
}}"""

        result = self._call_llm(system_prompt, user_prompt)
        return self._parse_json_response(result)

    def extract_key_decisions(self, transcript_text: str) -> Optional[Dict]:
        """Extract key decisions made during the meeting."""
        system_prompt = "You are a corporate governance analyst extracting decisions from meeting transcripts. Respond only with valid JSON."
        user_prompt = f"""Extract all key decisions made in this meeting transcript.

TRANSCRIPT:
{transcript_text}

Return JSON:
{{
    "decisions": [
        {{
            "decision": "clear description of what was decided",
            "context": "brief context of why this decision was made",
            "proposed_by": "speaker who proposed (if identifiable)",
            "agreed_by": ["speakers who agreed"],
            "dissented_by": ["speakers who dissented, if any"],
            "impact": "high/medium/low",
            "category": "financial/operational/strategic/compliance/hr/other"
        }}
    ],
    "pending_decisions": ["items discussed but not yet decided"],
    "total_decisions": number
}}"""

        result = self._call_llm(system_prompt, user_prompt)
        return self._parse_json_response(result)

    def analyze_risk_compliance(self, transcript_text: str) -> Optional[Dict]:
        """Flag potential risk or compliance concerns from the discussion."""
        system_prompt = "You are a risk and compliance analyst for corporate governance. Respond only with valid JSON."
        user_prompt = f"""Analyze this meeting transcript for any risk or compliance concerns.

TRANSCRIPT:
{transcript_text}

Return JSON:
{{
    "risk_flags": [
        {{
            "flag": "description of the risk/compliance concern",
            "severity": "high/medium/low",
            "category": "regulatory/financial/operational/legal/reputational",
            "relevant_quote": "approximate quote from the transcript",
            "speaker": "who raised or is involved"
        }}
    ],
    "compliance_mentions": ["any regulatory bodies, laws, or standards mentioned"],
    "overall_risk_level": "high/medium/low/none",
    "recommendations": ["suggested follow-up actions"]
}}"""

        result = self._call_llm(system_prompt, user_prompt)
        return self._parse_json_response(result)

    def analyze_topic_distribution(self, transcript_text: str) -> Optional[Dict]:
        """Cluster topics discussed and estimate time distribution."""
        system_prompt = "You are a meeting analytics specialist. Respond only with valid JSON."
        user_prompt = f"""Analyze this meeting transcript to identify the main topics discussed and their relative coverage.

TRANSCRIPT:
{transcript_text}

Return JSON:
{{
    "topics": [
        {{
            "topic": "topic name",
            "description": "brief description of what was discussed",
            "coverage_percent": estimated percentage of meeting time,
            "key_speakers": ["speakers who contributed most to this topic"],
            "outcome": "resolved/ongoing/deferred"
        }}
    ],
    "off_topic_percentage": estimated percentage of off-topic discussion,
    "meeting_efficiency_score": 0 to 100 (how focused was the meeting)
}}"""

        result = self._call_llm(system_prompt, user_prompt)
        return self._parse_json_response(result)

    @staticmethod
    def compute_speaker_stats(segments: List[Dict]) -> Dict:
        """Compute speaker statistics from structured transcript segments (no LLM needed)."""
        speaker_data: Dict[str, Dict] = {}

        for seg in segments:
            speaker = seg.get("speaker", "Unknown")
            text = seg.get("text", "")
            word_count = len(text.split())

            if speaker not in speaker_data:
                speaker_data[speaker] = {
                    "speaker": speaker,
                    "segment_count": 0,
                    "total_words": 0,
                    "first_spoke": seg.get("start_time", ""),
                    "last_spoke": seg.get("end_time", ""),
                }

            speaker_data[speaker]["segment_count"] += 1
            speaker_data[speaker]["total_words"] += word_count
            speaker_data[speaker]["last_spoke"] = seg.get("end_time", "")

        # Calculate percentages
        total_words = sum(s["total_words"] for s in speaker_data.values())
        stats = []
        for s in speaker_data.values():
            s["talk_percentage"] = round((s["total_words"] / total_words * 100) if total_words > 0 else 0, 1)
            stats.append(s)

        # Sort by talk percentage descending
        stats.sort(key=lambda x: x["talk_percentage"], reverse=True)

        return {
            "speakers": stats,
            "total_speakers": len(stats),
            "total_segments": len(segments),
            "total_words": total_words,
        }
