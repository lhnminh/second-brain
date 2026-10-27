"""Signed, expiring browser sessions for the existing single-account demo."""

import hashlib
import hmac
import secrets
import time

COOKIE_NAME = "second_brain_session"
SESSION_SECONDS = 8 * 60 * 60


def signature(settings, payload):
    return hmac.new(
        settings.mock_auth_token.get_secret_value().encode(),
        f"{settings.mock_user_id}:{payload}".encode(),
        hashlib.sha256,
    ).hexdigest()


def create_session(settings):
    payload = f"{int(time.time()) + SESSION_SECONDS}.{secrets.token_hex(16)}"
    return f"{payload}.{signature(settings, payload)}"


def valid_session(settings, value):
    if not settings.mock_auth_token or not value or len(value) > 256:
        return False
    try:
        expiry, nonce, digest = value.split(".")
        remaining = int(expiry) - time.time()
    except ValueError, TypeError:
        return False
    return (
        0 < remaining <= SESSION_SECONDS
        and len(nonce) == 32
        and hmac.compare_digest(
            digest.encode(), signature(settings, f"{expiry}.{nonce}").encode()
        )
    )
