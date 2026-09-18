import base64
import binascii
import hashlib
import hmac
import json
import secrets
import time

from fastapi import Header, HTTPException, status

from .settings import get_settings


_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Passwords must contain at least 8 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${_encode(salt)}${_encode(digest)}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), _decode(salt), int(iterations)
        )
        return hmac.compare_digest(_encode(digest), expected)
    except (TypeError, ValueError):
        return False


def create_access_token(user_id: int, school_id: int, role: str) -> str:
    payload = {"sub": user_id, "school_id": school_id, "role": role, "exp": int(time.time()) + 8 * 3600}
    encoded = _encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(get_settings().secret_key.encode(), encoded.encode(), hashlib.sha256).digest()
    return f"{encoded}.{_encode(signature)}"


def decode_access_token(token: str) -> dict[str, int | str]:
    try:
        encoded, signature = token.split(".", 1)
        expected = hmac.new(get_settings().secret_key.encode(), encoded.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_decode(signature), expected):
            raise ValueError
        payload = json.loads(_decode(encoded))
        if int(payload["exp"]) < int(time.time()):
            raise ValueError
        return payload
    except (TypeError, ValueError, KeyError, json.JSONDecodeError, binascii.Error):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")


def require_token(authorization: str | None = Header(default=None)) -> dict[str, int | str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return decode_access_token(authorization.removeprefix("Bearer ").strip())


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
