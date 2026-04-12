from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any

PBKDF2_SCHEME = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 310_000
PBKDF2_SALT_BYTES = 16
JWT_ALGORITHM = "HS256"


@dataclass(slots=True, frozen=True)
class TokenPayload:
    user_id: int
    issued_at: int
    expires_at: int


def _urlsafe_b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _urlsafe_b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(PBKDF2_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return (
        f"{PBKDF2_SCHEME}$"
        f"{PBKDF2_ITERATIONS}$"
        f"{_urlsafe_b64encode(salt)}$"
        f"{_urlsafe_b64encode(digest)}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash.startswith(f"{PBKDF2_SCHEME}$"):
        return False

    try:
        _, iterations_raw, salt_raw, digest_raw = password_hash.split("$", 3)
        iterations = int(iterations_raw)
        salt = _urlsafe_b64decode(salt_raw)
        expected_digest = _urlsafe_b64decode(digest_raw)
    except (TypeError, ValueError):
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(
    *,
    user_id: int,
    secret_key: str,
    expires_in_minutes: int,
) -> str:
    issued_at = int(time.time())
    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": issued_at + max(expires_in_minutes, 1) * 60,
    }
    header_segment = _urlsafe_b64encode(
        json.dumps(
            {"alg": JWT_ALGORITHM, "typ": "JWT"},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    payload_segment = _urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    signature_segment = _urlsafe_b64encode(
        hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    )
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def verify_access_token(token: str, secret_key: str) -> TokenPayload | None:
    try:
        header_segment, payload_segment, signature_segment = token.split(".", 2)
        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        expected_signature = hmac.new(
            secret_key.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        provided_signature = _urlsafe_b64decode(signature_segment)
        if not hmac.compare_digest(provided_signature, expected_signature):
            return None

        header = json.loads(_urlsafe_b64decode(header_segment))
        if header.get("alg") != JWT_ALGORITHM:
            return None

        payload: dict[str, Any] = json.loads(_urlsafe_b64decode(payload_segment))
        user_id = int(payload["sub"])
        issued_at = int(payload["iat"])
        expires_at = int(payload["exp"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None

    if expires_at <= int(time.time()):
        return None

    return TokenPayload(
        user_id=user_id,
        issued_at=issued_at,
        expires_at=expires_at,
    )
