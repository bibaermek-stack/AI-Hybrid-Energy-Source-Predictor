"""
API-key guard for endpoints that write or expose Solarman credentials.

The FastAPI process is reachable from the public internet through the Railway TCP
proxy (see mobile/config.py DEFAULT_API_BASE), so credential-touching routes must
not stay anonymous.
"""

from __future__ import annotations

import hmac
import logging
import os

from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)

API_KEY_ENV = "ECOPREDICT_API_KEY"


def configured_api_key() -> str:
    return os.getenv(API_KEY_ENV, "").strip()


def require_api_key(x_api_key: str = Header(default="", alias="X-API-Key")) -> None:
    """
    Fail-closed guard.

    An unset ECOPREDICT_API_KEY disables the route instead of leaving it open —
    "no key configured" must never mean "anyone may call this".
    """
    expected = configured_api_key()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Endpoint disabled: {API_KEY_ENV} is not configured on the server. "
                "Set it in the environment to enable this route."
            ),
        )

    supplied = (x_api_key or "").strip()
    if not supplied or not hmac.compare_digest(supplied, expected):
        logger.warning("Rejected credential request: missing or invalid X-API-Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
