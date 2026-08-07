"""Issue and verify short-lived signed session tokens.

The Azure SSO callback used to redirect with a random `secrets.token_urlsafe`
that was never stored or verified. Routes that needed to know the caller's
identity (e.g. the minutes chatbot) trusted a client-supplied `X-User-Email`
header instead, which made impersonation trivial.

This module replaces that random token with a signed JWT so downstream
endpoints can verify identity without a server-side session store.
"""
import logging
import os
import time
from typing import Optional

import jwt

logger = logging.getLogger(__name__)

# Algorithm is fixed; only the secret is configurable.
_ALGORITHM = "HS256"
# 24h matches the previous "token in URL" lifetime expectations of the SPA.
_DEFAULT_TTL_SECONDS = 60 * 60 * 24

# Loud dev-only fallback. Production deployments MUST set AEGIS_SESSION_SECRET
# — otherwise tokens issued by one process can be forged by anyone reading
# this source file.
_DEV_FALLBACK_SECRET = "aegis-dev-only-do-not-use-in-prod"


def _get_secret() -> str:
    # SESSION_SECRET was used by earlier Aegis deployments.  Accept it during
    # migration so enabling SSO does not silently invalidate every session;
    # new deployments should use the explicitly named AEGIS_SESSION_SECRET.
    secret = os.getenv("AEGIS_SESSION_SECRET") or os.getenv("SESSION_SECRET")
    if not secret:
        logger.warning(
            "AEGIS_SESSION_SECRET is not set; using insecure dev fallback. "
            "Session tokens are NOT secure in this configuration."
        )
        return _DEV_FALLBACK_SECRET
    return secret


def issue_session_token(email: str, name: Optional[str] = None, ttl_seconds: int = _DEFAULT_TTL_SECONDS) -> str:
    """Sign a session JWT carrying the caller's email + display name."""
    if not email:
        raise ValueError("email is required to issue a session token")
    now = int(time.time())
    payload = {
        "sub": email.lower(),
        "name": name or "",
        "iat": now,
        "exp": now + ttl_seconds,
        "iss": "aegis-backend",
    }
    return jwt.encode(payload, _get_secret(), algorithm=_ALGORITHM)


def verify_session_token(token: str) -> dict:
    """Verify a session JWT. Returns the decoded payload.

    Raises jwt.InvalidTokenError (or a subclass) on any failure — caller is
    responsible for turning that into a 401.
    """
    if not token:
        raise jwt.InvalidTokenError("empty token")
    return jwt.decode(
        token,
        _get_secret(),
        algorithms=[_ALGORITHM],
        issuer="aegis-backend",
        options={"require": ["exp", "sub", "iat"]},
    )
