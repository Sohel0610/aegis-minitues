"""
AI MOM (Minutes of Meeting) Generator Service
Converts meeting transcripts into structured Minutes of Meeting using Azure OpenAI / Groq.
Reuses the LLM patterns established in llm_utils.py.
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class MOMGeneratorService:
    """Generate structured Minutes of Meeting from transcript text using LLM."""

    # Maximum tokens to send per chunk to avoid context window limits
    MAX_CHUNK_CHARS = 12000

    def __init__(self):
        self._llm_client = None

    def _get_llm_client(self):
        """Get Azure OpenAI client (same pattern as llm_utils.py)."""
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
        """Get the LLM deployment name."""
        return (
            os.environ.get('LLM_DEPLOYMENT')
            or os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME')
            or 'gpt-4'
        )

    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> Optional[str]:
        """Make an LLM call with fallback to Groq."""
        # Try Azure OpenAI first
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
                logger.error(f"Azure OpenAI call failed: {e}")

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
                logger.error(f"Groq fallback failed: {e}")

        logger.error("No LLM available for MOM generation")
        return None

    def generate_mom(
        self,
        transcript_text: str,
        meeting_title: Optional[str] = None,
        meeting_date: Optional[str] = None,
        participants: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate a structured MOM from transcript text.

        Args:
            transcript_text: Full meeting transcript text
            meeting_title: Optional meeting title
            meeting_date: Optional meeting date
            participants: Optional list of participant names

        Returns:
            Dict containing the structured MOM or error
        """
        if not transcript_text or not transcript_text.strip():
            return {"success": False, "error": "Empty transcript provided"}

        # If transcript is too long, use chunked approach
        if len(transcript_text) > self.MAX_CHUNK_CHARS:
            return self._generate_mom_chunked(transcript_text, meeting_title, meeting_date, participants)

        return self._generate_mom_single(transcript_text, meeting_title, meeting_date, participants)

    def _generate_mom_single(
        self,
        transcript_text: str,
        meeting_title: Optional[str],
        meeting_date: Optional[str],
        participants: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Generate MOM from a single transcript chunk."""
        system_prompt = """You are an expert corporate secretary specializing in generating professional 
Minutes of Meeting (MOM) documents. You produce structured, clear, and actionable minutes.
Always respond with valid JSON only. No markdown, no explanations outside the JSON."""

        context_info = ""
        if meeting_title:
            context_info += f"Meeting Title: {meeting_title}\n"
        if meeting_date:
            context_info += f"Meeting Date: {meeting_date}\n"
        if participants:
            context_info += f"Known Participants: {', '.join(participants)}\n"

        user_prompt = f"""Analyze the following meeting transcript and generate a structured Minutes of Meeting (MOM).

{context_info}

TRANSCRIPT:
{transcript_text[:self.MAX_CHUNK_CHARS]}

Generate a JSON response with this exact structure:
{{
    "meeting_title": "string - inferred or provided meeting title",
    "meeting_date": "string - date of the meeting",
    "meeting_duration": "string - estimated duration",
    "attendees": ["list of participant names identified from transcript"],
    "absentees": ["list if mentioned"],
    "agenda_items": [
        {{
            "topic": "string - agenda topic",
            "discussion_summary": "string - key points discussed",
            "decisions": ["list of decisions made"],
            "action_items": [
                {{
                    "task": "string - what needs to be done",
                    "assignee": "string - who is responsible",
                    "deadline": "string - deadline if mentioned, else 'TBD'"
                }}
            ]
        }}
    ],
    "key_highlights": ["list of important points or announcements"],
    "next_steps": ["list of agreed next steps"],
    "next_meeting": "string - next meeting date/time if discussed, else 'To be scheduled'",
    "additional_notes": "string - any other relevant observations"
}}

Important:
- Extract ACTUAL content from the transcript, do not make up information
- Identify speakers and attribute action items correctly
- Group related discussions into logical agenda items
- Be concise but comprehensive"""

        result = self._call_llm(system_prompt, user_prompt, max_tokens=4000)
        if not result:
            return {"success": False, "error": "LLM call failed. Check LLM configuration."}

        try:
            # Clean potential markdown code fences
            cleaned = result.strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.split('\n', 1)[1] if '\n' in cleaned else cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            if cleaned.startswith('json'):
                cleaned = cleaned[4:].strip()

            mom_data = json.loads(cleaned)
            return {
                "success": True,
                "mom": mom_data,
                "generated_at": datetime.now().isoformat(),
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MOM JSON: {e}")
            # Return raw text as fallback
            return {
                "success": True,
                "mom": {"raw_text": result},
                "generated_at": datetime.now().isoformat(),
                "parse_warning": "Could not parse structured JSON, returning raw text",
            }

    def _generate_mom_chunked(
        self,
        transcript_text: str,
        meeting_title: Optional[str],
        meeting_date: Optional[str],
        participants: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Handle long transcripts by summarizing in chunks then merging."""
        # Split transcript into chunks
        chunks = []
        words = transcript_text.split()
        current_chunk = []
        current_len = 0

        for word in words:
            current_chunk.append(word)
            current_len += len(word) + 1
            if current_len >= self.MAX_CHUNK_CHARS:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_len = 0

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        # Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            system_prompt = "You are a meeting transcript summarizer. Provide a detailed summary of this transcript segment."
            user_prompt = f"""Summarize this transcript segment ({i + 1} of {len(chunks)}). 
Extract: key topics discussed, decisions made, action items, and speakers involved.

TRANSCRIPT SEGMENT:
{chunk}

Provide a detailed text summary (not JSON)."""

            summary = self._call_llm(system_prompt, user_prompt, max_tokens=2000)
            if summary:
                chunk_summaries.append(f"--- Segment {i + 1} ---\n{summary}")

        # Merge summaries and generate final MOM
        merged_summary = '\n\n'.join(chunk_summaries)
        return self._generate_mom_single(merged_summary, meeting_title, meeting_date, participants)

    def generate_mom_html(self, mom_data: Dict[str, Any]) -> str:
        """Convert structured MOM JSON into a formatted HTML document."""
        if not mom_data:
            return "<p>No MOM data available.</p>"

        html_parts = [
            '<div class="mom-document">',
            f'<h1>{mom_data.get("meeting_title", "Meeting Minutes")}</h1>',
            f'<p><strong>Date:</strong> {mom_data.get("meeting_date", "N/A")}</p>',
            f'<p><strong>Duration:</strong> {mom_data.get("meeting_duration", "N/A")}</p>',
        ]

        # Attendees
        attendees = mom_data.get("attendees", [])
        if attendees:
            html_parts.append('<h2>Attendees</h2><ul>')
            for a in attendees:
                html_parts.append(f'<li>{a}</li>')
            html_parts.append('</ul>')

        # Agenda Items
        agenda = mom_data.get("agenda_items", [])
        if agenda:
            html_parts.append('<h2>Agenda & Discussion</h2>')
            for i, item in enumerate(agenda, 1):
                html_parts.append(f'<h3>{i}. {item.get("topic", "Untitled")}</h3>')
                html_parts.append(f'<p>{item.get("discussion_summary", "")}</p>')

                decisions = item.get("decisions", [])
                if decisions:
                    html_parts.append('<p><strong>Decisions:</strong></p><ul>')
                    for d in decisions:
                        html_parts.append(f'<li>{d}</li>')
                    html_parts.append('</ul>')

                actions = item.get("action_items", [])
                if actions:
                    html_parts.append('<p><strong>Action Items:</strong></p>')
                    html_parts.append('<table border="1" cellpadding="6"><tr><th>Task</th><th>Assignee</th><th>Deadline</th></tr>')
                    for a in actions:
                        html_parts.append(
                            f'<tr><td>{a.get("task", "")}</td>'
                            f'<td>{a.get("assignee", "")}</td>'
                            f'<td>{a.get("deadline", "TBD")}</td></tr>'
                        )
                    html_parts.append('</table>')

        # Key Highlights
        highlights = mom_data.get("key_highlights", [])
        if highlights:
            html_parts.append('<h2>Key Highlights</h2><ul>')
            for h in highlights:
                html_parts.append(f'<li>{h}</li>')
            html_parts.append('</ul>')

        # Next Steps
        next_steps = mom_data.get("next_steps", [])
        if next_steps:
            html_parts.append('<h2>Next Steps</h2><ul>')
            for n in next_steps:
                html_parts.append(f'<li>{n}</li>')
            html_parts.append('</ul>')

        # Next Meeting
        next_meeting = mom_data.get("next_meeting")
        if next_meeting:
            html_parts.append(f'<p><strong>Next Meeting:</strong> {next_meeting}</p>')

        html_parts.append('</div>')
        return '\n'.join(html_parts)
