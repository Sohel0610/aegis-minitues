"""
MS Teams Transcript Service — Retrieval & Parsing
Handles fetching transcripts from Graph API and parsing VTT format into structured JSON.
"""
import os
import re
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class TranscriptParser:
    """Parse WebVTT transcript format into structured JSON."""

    @staticmethod
    def parse_vtt(vtt_content: str) -> List[Dict[str, Any]]:
        """Parse VTT content into a list of transcript segments.

        VTT format example:
            WEBVTT

            00:00:01.000 --> 00:00:05.000
            <v John Doe>Hello everyone, welcome to the meeting.</v>

            00:00:06.000 --> 00:00:10.000
            <v Jane Smith>Thank you John, let's get started.</v>

        Returns:
            List of dicts: [{speaker, start_time, end_time, text}]
        """
        if not vtt_content or not vtt_content.strip():
            return []

        segments = []
        # Split by double newline to get cue blocks
        blocks = re.split(r'\n\s*\n', vtt_content.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if not lines:
                continue

            # Skip the WEBVTT header line
            if lines[0].startswith('WEBVTT'):
                continue

            # Skip numbered cue identifiers
            start_idx = 0
            if lines[0].strip().isdigit():
                start_idx = 1

            if start_idx >= len(lines):
                continue

            # Parse timestamp line: "00:00:01.000 --> 00:00:05.000"
            timestamp_line = lines[start_idx] if start_idx < len(lines) else ""
            timestamp_match = re.match(
                r'(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})',
                timestamp_line
            )
            if not timestamp_match:
                continue

            start_time = timestamp_match.group(1).replace(',', '.')
            end_time = timestamp_match.group(2).replace(',', '.')

            # Parse text lines (may contain speaker tags)
            text_lines = lines[start_idx + 1:]
            full_text = ' '.join(text_lines)

            # Extract speaker from <v Speaker Name>text</v> format
            speaker = "Unknown"
            text = full_text

            speaker_match = re.match(r'<v\s+([^>]+)>(.*?)(?:</v>)?$', full_text, re.DOTALL)
            if speaker_match:
                speaker = speaker_match.group(1).strip()
                text = speaker_match.group(2).strip()
            else:
                # Clean any remaining HTML-like tags
                text = re.sub(r'<[^>]+>', '', full_text).strip()

            if text:
                segments.append({
                    "speaker": speaker,
                    "start_time": start_time,
                    "end_time": end_time,
                    "text": text,
                })

        return segments

    @staticmethod
    def segments_to_full_text(segments: List[Dict[str, Any]]) -> str:
        """Convert structured segments into a readable full-text transcript."""
        lines = []
        current_speaker = None
        for seg in segments:
            if seg["speaker"] != current_speaker:
                current_speaker = seg["speaker"]
                lines.append(f"\n{current_speaker} [{seg['start_time']}]:")
            lines.append(f"  {seg['text']}")
        return '\n'.join(lines).strip()

    @staticmethod
    def get_participants(segments: List[Dict[str, Any]]) -> List[str]:
        """Extract unique participant names from segments."""
        speakers = set()
        for seg in segments:
            if seg.get("speaker") and seg["speaker"] != "Unknown":
                speakers.add(seg["speaker"])
        return sorted(list(speakers))

    @staticmethod
    def get_duration_minutes(segments: List[Dict[str, Any]]) -> int:
        """Estimate meeting duration from transcript timestamps."""
        if not segments:
            return 0
        try:
            last_time = segments[-1].get("end_time", "00:00:00.000")
            parts = last_time.replace('.', ':').split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            total_minutes = hours * 60 + minutes + (1 if seconds > 0 else 0)
            return max(total_minutes, 1)
        except (ValueError, IndexError):
            return 0


class TeamsTranscriptService:
    """Fetch and process meeting transcripts from Microsoft Graph API."""

    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self):
        from services.teams_bot_service import TeamsAuthService
        self.auth = TeamsAuthService()
        self.parser = TranscriptParser()

    async def fetch_transcript(self, meeting_url: str, organizer_user_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch transcript for a completed meeting from Graph API.

        Flow:
        1. Resolve meeting URL to onlineMeeting ID
        2. List available transcripts
        3. Download transcript content (VTT)
        4. Parse into structured format

        Args:
            meeting_url: The Teams meeting join URL
            organizer_user_id: Optional organizer's user ID for the API path

        Returns:
            Dict with raw_vtt, structured_json, participants, duration_minutes
        """
        token = self.auth.get_access_token()
        if not token:
            return {
                "success": False,
                "error": "Graph API not configured. Set MS_TEAMS_* env variables.",
                "placeholder_mode": True,
            }

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                # Step 1: Find the online meeting ID
                meeting_id = await self._resolve_meeting_id(client, token, meeting_url, organizer_user_id)
                if not meeting_id:
                    return {
                        "success": False,
                        "error": "Could not resolve meeting from URL. The meeting may not have transcription enabled.",
                    }

                # Step 2: List transcripts for the meeting
                transcripts = await self._list_transcripts(client, token, meeting_id, organizer_user_id)
                if not transcripts:
                    return {
                        "success": False,
                        "error": "No transcripts available. Ensure transcription was enabled during the meeting.",
                    }

                # Step 3: Download the most recent transcript content
                transcript_id = transcripts[0].get("id")
                vtt_content = await self._download_transcript(
                    client, token, meeting_id, transcript_id, organizer_user_id
                )
                if not vtt_content:
                    return {
                        "success": False,
                        "error": "Failed to download transcript content.",
                    }

                # Step 4: Parse VTT into structured format
                segments = self.parser.parse_vtt(vtt_content)
                participants = self.parser.get_participants(segments)
                duration = self.parser.get_duration_minutes(segments)
                full_text = self.parser.segments_to_full_text(segments)

                return {
                    "success": True,
                    "raw_vtt": vtt_content,
                    "structured_json": segments,
                    "full_text": full_text,
                    "participants": participants,
                    "participant_count": len(participants),
                    "duration_minutes": duration,
                    "segment_count": len(segments),
                }

        except ImportError:
            return {"success": False, "error": "httpx package not installed"}
        except Exception as e:
            logger.error(f"Error fetching transcript: {e}")
            return {"success": False, "error": str(e)}

    async def _resolve_meeting_id(
        self, client, token: str, meeting_url: str, user_id: Optional[str]
    ) -> Optional[str]:
        """Resolve a meeting URL to an online meeting ID."""
        try:
            # Approach 1: Use filter on onlineMeetings
            if user_id:
                url = f"{self.GRAPH_BASE_URL}/users/{user_id}/onlineMeetings"
            else:
                url = f"{self.GRAPH_BASE_URL}/communications/onlineMeetings"

            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                params={"$filter": f"joinWebUrl eq '{meeting_url}'"},
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                meetings = data.get("value", [])
                if meetings:
                    return meetings[0].get("id")

            logger.warning(f"Could not resolve meeting ID from URL filter (status={response.status_code})")
            return None

        except Exception as e:
            logger.error(f"Error resolving meeting ID: {e}")
            return None

    async def _list_transcripts(
        self, client, token: str, meeting_id: str, user_id: Optional[str]
    ) -> List[Dict]:
        """List available transcripts for a meeting."""
        try:
            if user_id:
                url = f"{self.GRAPH_BASE_URL}/users/{user_id}/onlineMeetings/{meeting_id}/transcripts"
            else:
                url = f"{self.GRAPH_BASE_URL}/communications/onlineMeetings/{meeting_id}/transcripts"

            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("value", [])
            else:
                logger.warning(f"Failed to list transcripts: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error listing transcripts: {e}")
            return []

    async def _download_transcript(
        self, client, token: str, meeting_id: str, transcript_id: str, user_id: Optional[str]
    ) -> Optional[str]:
        """Download transcript content as VTT."""
        try:
            if user_id:
                url = (
                    f"{self.GRAPH_BASE_URL}/users/{user_id}/onlineMeetings/{meeting_id}"
                    f"/transcripts/{transcript_id}/content"
                )
            else:
                url = (
                    f"{self.GRAPH_BASE_URL}/communications/onlineMeetings/{meeting_id}"
                    f"/transcripts/{transcript_id}/content"
                )

            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "text/vtt",
                },
                timeout=60.0,
            )

            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"Failed to download transcript: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error downloading transcript: {e}")
            return None

    def parse_uploaded_vtt(self, vtt_content: str) -> Dict[str, Any]:
        """Parse a manually uploaded VTT file (for testing without Graph API)."""
        segments = self.parser.parse_vtt(vtt_content)
        participants = self.parser.get_participants(segments)
        duration = self.parser.get_duration_minutes(segments)
        full_text = self.parser.segments_to_full_text(segments)

        return {
            "success": True,
            "raw_vtt": vtt_content,
            "structured_json": segments,
            "full_text": full_text,
            "participants": participants,
            "participant_count": len(participants),
            "duration_minutes": duration,
            "segment_count": len(segments),
        }
