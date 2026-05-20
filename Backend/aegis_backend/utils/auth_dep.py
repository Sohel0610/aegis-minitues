"""FastAPI dependency for session-token auth.

Use `Depends(require_session)` on any endpoint that must run as a known caller.
When SSO is disabled (dev), it falls back to a deterministic guest identity so
local development keeps working. When SSO is enabled, it requires a valid
`Authorization: Bearer <jwt>` header and returns the decoded claims.
"""
import logging
import os

from fastapi import HTTPException, Request

import jwt as _pyjwt

from utils.session_token import verify_session_token

logger = logging.getLogger(__name__)


def _sso_enabled() -> bool:
    return os.getenv("SSO_ENABLED", "false").lower() == "true"


async def require_session(request: Request) -> dict:
    """Return the authenticated caller's claims, or raise 401.

    Returned dict shape: {"email": str, "name": str}.
    """
    if not _sso_enabled():
        return {"email": "guest@aegis.local", "name": "Guest User"}

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    token = auth_header.split(" ", 1)[1].strip()
    try:
        claims = verify_session_token(token)
    except _pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except _pyjwt.InvalidTokenError as e:
        logger.warning(f"Rejected request with invalid session token: {e}")
        raise HTTPException(status_code=401, detail="Invalid session token")
    email = claims.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Session token missing subject")
    return {"email": email, "name": claims.get("name") or email.split("@")[0]}
