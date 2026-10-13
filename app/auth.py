"""
Dashboard Authentication (JWT Cookie)
Ad-to-Sale Attribution System
Skills: fastapi, security-and-hardening.
Zero new deps: stdlib hashlib/hmac/secrets + PyJWT (installed).
"""

import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import jwt
from fastapi import Cookie, Depends, Request

from app.config import (
    ADMIN_PASSWORD_HASH,
    ADMIN_USERNAME,
    AUTH_ENABLED,
    AUTH_SECRET_KEY,
    TOKEN_EXPIRE_MINUTES,
)

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
COOKIE_NAME = "hc_session"
GENERIC_LOGIN_ERROR = "Invalid username or password"

_LOGIN_ATTEMPTS: dict[str, list[float]] = {}
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 5 * 60


def hash_password(password: str, iterations: int = 210_000) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iters, salt_hex, hash_hex = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"),
            bytes.fromhex(salt_hex), int(iters),
        )
        return hmac.compare_digest(dk, bytes.fromhex(hash_hex))
    except Exception:
        return False


def create_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, AUTH_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        return str(sub) if sub else None
    except jwt.InvalidTokenError:
        return None


def _token_from_request(request: Request, hc_session: Optional[str]) -> Optional[str]:
    if hc_session:
        return hc_session
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


async def get_current_user(
    request: Request,
    hc_session: Annotated[Optional[str], Cookie(alias=COOKIE_NAME)] = None,
) -> Optional[str]:
    if not AUTH_ENABLED:
        return ADMIN_USERNAME or "admin"
    token = _token_from_request(request, hc_session)
    if not token:
        return None
    username = decode_access_token(token)
    if username and username == ADMIN_USERNAME:
        return username
    return None


CurrentUser = Annotated[Optional[str], Depends(get_current_user)]


def _prune(key: str, now: float) -> list[float]:
    hits = [t for t in _LOGIN_ATTEMPTS.get(key, []) if now - t < WINDOW_SECONDS]
    _LOGIN_ATTEMPTS[key] = hits
    return hits


def is_rate_limited(key: str) -> bool:
    return len(_prune(key, time.time())) >= MAX_ATTEMPTS


def record_failed_login(key: str) -> None:
    now = time.time()
    hits = _prune(key, now)
    hits.append(now)
    _LOGIN_ATTEMPTS[key] = hits


def clear_login_attempts(key: str) -> None:
    _LOGIN_ATTEMPTS.pop(key, None)


def verify_credentials(username: str, password: str) -> bool:
    if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:
        logger.warning("Auth attempted with no admin credentials configured")
        return False
    user_ok = hmac.compare_digest(username, ADMIN_USERNAME)
    pass_ok = verify_password(password, ADMIN_PASSWORD_HASH)
    if not (user_ok and pass_ok):
        logger.warning("Failed login attempt for user=%r", username)
        return False
    return True


def cookie_kwargs() -> dict:
    import os
    public = os.environ.get("PUBLIC_URL", "")
    # Secure cookies are never sent over plain HTTP (browsers and httpx
    # alike), so default to False and only enable on positive evidence of
    # HTTPS: an https:// PUBLIC_URL, Railway env markers, or explicit flag.
    # Railway deployments always terminate TLS, so production stays Secure.
    secure = (
        public.startswith("https://")
        or os.environ.get("HTTPS_ENABLED", "").lower() in ("1", "true", "yes")
        or os.environ.get("RAILWAY_ENVIRONMENT", "") != ""
        or os.environ.get("RENDER", "") != ""
    )
    return {
        "httponly": True,
        "secure": secure,
        "samesite": "lax",
        "path": "/",
        "max_age": TOKEN_EXPIRE_MINUTES * 60,
    }
