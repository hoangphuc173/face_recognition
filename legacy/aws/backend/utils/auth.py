"""Authentication helpers for REST and WebSocket endpoints."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict, List, Mapping, Optional

import requests
from fastapi import Depends, HTTPException, status
from jwt import InvalidTokenError, PyJWKClient, decode as jwt_decode

from .config import settings

LOGGER = logging.getLogger(__name__)


def _issuer() -> str:
    return f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/{settings.cognito_user_pool_id}"


@lru_cache(maxsize=1)
def _jwk_client() -> Optional[PyJWKClient]:
    if not settings.cognito_enabled or not settings.cognito_user_pool_id:
        return None
    jwks_url = f"{_issuer()}/.well-known/jwks.json"
    return PyJWKClient(jwks_url)


def _verify_cognito_token(token: str) -> Dict[str, Any]:
    client = _jwk_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Cognito disabled"
        )
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        claims = jwt_decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.cognito_app_client_id,
            issuer=_issuer(),
        )
        # Add groups to the claims for easier access
        claims["groups"] = claims.get("cognito:groups", [])
        return claims
    except InvalidTokenError as err:
        LOGGER.warning("Invalid Cognito token: %s", err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from err


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def authenticate_request(
    authorization: Optional[str] = Depends(lambda: None),
    headers: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Authenticate request via Cognito JWT or API key, returning claims with groups."""
    # This function is designed to be a dependency in FastAPI
    # It's a bit complex to handle both headers from HTTP and None from WebSocket
    final_headers = headers or (authorization.get("headers") if hasattr(authorization, 'get') else {})
    auth_header = final_headers.get("authorization") or (authorization if isinstance(authorization, str) else None)

    token = _extract_bearer_token(auth_header)
    if token:
        # Allow dev bypass token for development
        if token == "dev_token_bypass":
            return {"auth": "dev_bypass", "groups": ["admin"], "sub": "dev_user"}
        return _verify_cognito_token(token)

    api_key_header = settings.api_key_header.lower()
    provided_api_key = final_headers.get(api_key_header, "")

    if settings.api_key_enabled and provided_api_key == settings.api_key_value:
        # API key provides admin-level access for automation
        return {"auth": "api_key", "groups": ["admin"]}

    if settings.cognito_enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required",
        )
    if settings.api_key_enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    # For local dev without auth enabled
    return {"auth": "anonymous", "groups": []}


def require_admin(auth_claims: Dict[str, Any] = Depends(authenticate_request)) -> None:
    """FastAPI dependency that requires the user to be in the 'admin' group."""
    if "admin" not in auth_claims.get("groups", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )


def fetch_cognito_jwks() -> Dict[str, Any]:
    """Utility used by WebSocket handler packaging to warm JWKS cache."""
    if not settings.cognito_enabled:
        return {}
    response = requests.get(f"{_issuer()}/.well-known/jwks.json", timeout=5)
    response.raise_for_status()
    return response.json()
