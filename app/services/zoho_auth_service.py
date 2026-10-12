"""
Zoho Books OAuth2 Token Service
Ad-to-Sale Attribution System

Mints and caches Zoho Books access tokens from a refresh token. Zoho access
tokens expire after 60 minutes, so this service keeps one cached token per
brand and transparently refreshes it before expiry.

Every Zoho Books call in this system should obtain its Authorization header
from here rather than reading a token from the environment directly.
"""

import threading
import time
from typing import Dict, Any, Optional

import requests

from app.config import (
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_ACCOUNTS_URL,
    ZOHO_TOKEN_REFRESH_MARGIN,
    get_brand_config,
)

_lock = threading.Lock()

# refresh_token -> {"token": str, "expires_at": float}
_token_cache: Dict[str, Dict[str, Any]] = {}


class ZohoAuthError(Exception):
    """Raised when a Zoho Books access token cannot be obtained."""


def _request_token(refresh_token: str) -> Dict[str, Any]:
    """Exchange a Zoho refresh token for a fresh access token."""
    payload = {
        "refresh_token": refresh_token,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token",
    }
    try:
        r = requests.post(ZOHO_ACCOUNTS_URL, data=payload, timeout=20)
    except Exception as e:
        raise ZohoAuthError(f"Zoho token request failed: {e}")

    if r.status_code != 200:
        raise ZohoAuthError(
            f"Zoho token request rejected: {r.status_code} - {r.text[:300]}"
        )

    data = r.json()
    if "error" in data or not data.get("access_token"):
        raise ZohoAuthError(f"Zoho token response invalid: {data}")

    return data


def get_access_token(brand: str = "Home Cartel", force_refresh: bool = False) -> str:
    """
    Return a valid Zoho Books access token for the given brand.

    Cached per refresh token so brands sharing a Zoho account reuse one token.
    Thread-safe: the poller daemon and FastAPI background tasks may both call
    this concurrently.
    """
    brand_cfg = get_brand_config(brand)
    refresh_token = brand_cfg.get("zoho_refresh_token") or ""

    if not refresh_token:
        raise ZohoAuthError(
            f"No Zoho refresh token configured for brand '{brand}'. "
            "Set the brand's ZOHO_REFRESH_TOKEN to enable Zoho Books integration."
        )

    with _lock:
        cached = _token_cache.get(refresh_token)
        now = time.time()

        if cached and not force_refresh and now < cached["expires_at"]:
            return cached["token"]

        data = _request_token(refresh_token)
        token = data["access_token"]
        # Zoho returns expires_in in seconds (normally 3600).
        expires_in = int(data.get("expires_in", 3600))
        _token_cache[refresh_token] = {
            "token": token,
            "expires_at": now + max(0, expires_in - ZOHO_TOKEN_REFRESH_MARGIN),
            "api_domain": data.get("api_domain"),
        }
        return token


def get_auth_headers(brand: str = "Home Cartel") -> Dict[str, str]:
    """Build Zoho Books REST headers, fetching a token if needed."""
    return {
        "Authorization": f"Zoho-oauthtoken {get_access_token(brand)}",
        "Content-Type": "application/json",
    }


def resolve_org_id(brand: str = "Home Cartel") -> str:
    """Return the Zoho Books organization ID for a brand."""
    brand_cfg = get_brand_config(brand)
    org_id = brand_cfg.get("zoho_org_id") or ""
    if not org_id:
        raise ZohoAuthError(
            f"No Zoho organization ID configured for brand '{brand}'."
        )
    return org_id


def is_configured(brand: str = "Home Cartel") -> bool:
    """True when the brand has enough Zoho credentials to make API calls."""
    brand_cfg = get_brand_config(brand)
    return bool(
        brand_cfg.get("zoho_refresh_token")
        and brand_cfg.get("zoho_org_id")
        and ZOHO_CLIENT_ID
        and ZOHO_CLIENT_SECRET
    )


def clear_cache() -> None:
    """Drop all cached tokens. Used by tests and credential rotation."""
    with _lock:
        _token_cache.clear()
