"""
MS Teams Bot Service — Graph API Integration
Handles OAuth authentication, bot join/leave meeting via Microsoft Graph API.
"""
import os
import re
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class TeamsAuthService:
    """Manages OAuth 2.0 client credentials flow for MS Graph API."""

    def __init__(self):
        self.tenant_id = os.getenv('MS_TEAMS_TENANT_ID', '')
        self.client_id = os.getenv('MS_TEAMS_CLIENT_ID', '')
        self.client_secret = os.getenv('MS_TEAMS_CLIENT_SECRET', '')
        self.bot_app_id = os.getenv('MS_TEAMS_BOT_APP_ID', '')
        self._token_cache: Optional[Dict[str, Any]] = None

    def _is_configured(self) -> bool:
        """Check if all required credentials are present."""
        return all([
            self.tenant_id and 'PLACEHOLDER' not in self.tenant_id,
            self.client_id and 'PLACEHOLDER' not in self.client_id,
            self.client_secret and 'PLACEHOLDER' not in self.client_secret,
        ])

    def get_access_token(self) -> Optional[str]:
        """Acquire an access token using client credentials flow via MSAL."""
        if not self._is_configured():
            logger.warning("MS Teams Graph API credentials not configured. Using placeholder mode.")
            return None

        try:
            import msal

            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=authority,
            )

            # Try to get token from cache first
            scopes = ["https://graph.microsoft.com/.default"]
            result = app.acquire_token_silent(scopes, account=None)

            if not result:
                result = app.acquire_token_for_client(scopes=scopes)

            if "access_token" in result:
                logger.info("Successfully acquired MS Graph access token")
                return result["access_token"]
            else:
                logger.error(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
                return None

        except ImportError:
            logger.error("msal package not installed. Run: pip install msal")
            return None
        except Exception as e:
            logger.error(f"Error acquiring access token: {e}")
            return None


class TeamsBotService:
    """Handles bot join/leave meeting operations via MS Graph API."""

    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self):
        self.auth = TeamsAuthService()

    @staticmethod
    def parse_teams_meeting_url(meeting_url: str) -> Dict[str, str]:
        """Extract meeting info from a Teams meeting URL.

        Teams URLs typically look like:
        https://teams.microsoft.com/l/meetup-join/19%3ameeting_xxx/0?context=...
        """
        parsed = {"raw_url": meeting_url, "join_url": meeting_url}

        # Try to extract thread ID from the URL
        thread_match = re.search(r'19%3a(meeting_[^/]+)', meeting_url)
        if thread_match:
            parsed["thread_id"] = f"19:{thread_match.group(1)}"

        # Try to extract context (organizer, tenant) from URL query
        context_match = re.search(r'context=([^&]+)', meeting_url)
        if context_match:
            try:
                import urllib.parse
                context_str = urllib.parse.unquote(context_match.group(1))
                context = json.loads(context_str)
                parsed["organizer_id"] = context.get("Oid", "")
                parsed["tenant_id"] = context.get("Tid", "")
            except (json.JSONDecodeError, Exception):
                pass

        return parsed

    async def join_meeting(self, meeting_url: str, meeting_db_id: str) -> Dict[str, Any]:
        """Join a Teams meeting as a bot participant.

        Uses POST /communications/calls to create a call and join the meeting.
        """
        token = self.auth.get_access_token()
        if not token:
            return {
                "success": False,
                "error": "Graph API not configured. Please set MS_TEAMS_* environment variables.",
                "placeholder_mode": True
            }

        try:
            import httpx

            meeting_info = self.parse_teams_meeting_url(meeting_url)

            # Build the call request payload
            call_payload = {
                "@odata.type": "#microsoft.graph.call",
                "callbackUri": f"https://your-callback-url.com/api/teams/callback",
                "requestedModalities": ["audio"],
                "mediaConfig": {
                    "@odata.type": "#microsoft.graph.serviceHostedMediaConfig",
                },
                "chatInfo": {
                    "@odata.type": "#microsoft.graph.chatInfo",
                    "threadId": meeting_info.get("thread_id", ""),
                    "messageId": "0",
                },
                "meetingInfo": {
                    "@odata.type": "#microsoft.graph.organizerMeetingInfo",
                    "organizer": {
                        "@odata.type": "#microsoft.graph.identitySet",
                        "user": {
                            "@odata.type": "#microsoft.graph.identity",
                            "id": meeting_info.get("organizer_id", ""),
                            "tenantId": meeting_info.get("tenant_id", self.auth.tenant_id),
                        }
                    }
                },
                "tenantId": self.auth.tenant_id,
            }

            # If we can use JoinMeetingIdMeetingInfo (simpler approach with join URL)
            if meeting_url.startswith("https://teams.microsoft.com"):
                call_payload["meetingInfo"] = {
                    "@odata.type": "#microsoft.graph.joinMeetingIdMeetingInfo",
                    "joinUrl": meeting_url,
                }
                # Remove chatInfo when using joinUrl directly
                call_payload.pop("chatInfo", None)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.GRAPH_BASE_URL}/communications/calls",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=call_payload,
                    timeout=30.0,
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    call_id = data.get("id", "")
                    logger.info(f"Bot joined meeting successfully. Call ID: {call_id}")
                    return {
                        "success": True,
                        "call_id": call_id,
                        "status": data.get("state", "establishing"),
                    }
                else:
                    error_text = response.text
                    logger.error(f"Failed to join meeting: {response.status_code} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Graph API error ({response.status_code}): {error_text}",
                    }

        except ImportError:
            logger.error("httpx package not installed. Run: pip install httpx")
            return {"success": False, "error": "httpx package not installed"}
        except Exception as e:
            logger.error(f"Error joining meeting: {e}")
            return {"success": False, "error": str(e)}

    async def leave_meeting(self, call_id: str) -> Dict[str, Any]:
        """Leave a Teams meeting (hang up the call)."""
        token = self.auth.get_access_token()
        if not token:
            return {"success": False, "error": "Graph API not configured"}

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.GRAPH_BASE_URL}/communications/calls/{call_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )

                if response.status_code in (200, 204):
                    logger.info(f"Bot left meeting. Call ID: {call_id}")
                    return {"success": True}
                else:
                    return {
                        "success": False,
                        "error": f"Graph API error ({response.status_code}): {response.text}",
                    }

        except Exception as e:
            logger.error(f"Error leaving meeting: {e}")
            return {"success": False, "error": str(e)}

    async def get_online_meeting_id(self, meeting_url: str) -> Optional[str]:
        """Resolve a Teams meeting URL to an onlineMeeting ID for transcript retrieval."""
        token = self.auth.get_access_token()
        if not token:
            return None

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                # Use the join URL to find the meeting
                response = await client.get(
                    f"{self.GRAPH_BASE_URL}/communications/onlineMeetings",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"$filter": f"joinWebUrl eq '{meeting_url}'"},
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    meetings = data.get("value", [])
                    if meetings:
                        return meetings[0].get("id")
                    logger.warning("No online meeting found for the given URL")
                    return None
                else:
                    logger.error(f"Failed to resolve meeting: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error resolving meeting ID: {e}")
            return None
