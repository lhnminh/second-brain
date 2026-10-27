"""Persistent anonymous workspaces and separately expiring demo access."""

import hashlib
import hmac
import secrets
import time

COOKIE_NAME = "second_brain_session"
SESSION_SECONDS = 8 * 60 * 60
WORKSPACE_COOKIE_NAME = "second_brain_workspace"
WORKSPACE_SECONDS = 365 * 24 * 60 * 60


def workspace_cookie(value):
    # A 256-bit random capability, never the public owner ID. Do not accept IDs
    # from request bodies/headers or expose this capability in API snapshots.
    if value and len(value) == 64 and all(c in "0123456789abcdef" for c in value):
        return value
    return None


def workspace_owner(settings, workspace):
    digest = hashlib.sha256(f"{settings.mock_user_id}:{workspace}".encode()).hexdigest()
    return f"browser-{digest}"


def signature(settings, payload, workspace):
    return hmac.new(
        settings.mock_auth_token.get_secret_value().encode(),
        f"{workspace_owner(settings, workspace)}:{payload}".encode(),
        hashlib.sha256,
    ).hexdigest()


def create_session(settings, workspace):
    payload = f"{int(time.time()) + SESSION_SECONDS}.{secrets.token_hex(16)}"
    return f"{payload}.{signature(settings, payload, workspace)}"


def valid_session(settings, value, workspace):
    if not settings.mock_auth_token or not workspace or not value or len(value) > 256:
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
            digest.encode(),
            signature(settings, f"{expiry}.{nonce}", workspace).encode(),
        )
    )
