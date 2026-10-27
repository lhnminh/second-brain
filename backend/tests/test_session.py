"""Browser navigation, session lifetime, and existing bearer authentication."""

import pytest

from second_brain.session import COOKIE_NAME, SESSION_SECONDS


def connect(client, token="demo-secret"):
    return client.post("/api/session", json={"token": token})


def test_browser_session_survives_page_navigation_and_reload(setup):
    clients, _, _ = setup
    client = clients(token="demo-secret")
    assert client.get("/api/dashboard").status_code == 401
    response = connect(client)
    assert response.status_code == 200
    assert "demo-secret" not in response.text
    cookie = response.headers["set-cookie"]
    assert "demo-secret" not in cookie
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie
    assert "Path=/api" in cookie
    assert f"Max-Age={SESSION_SECONDS}" in cookie
    assert "Secure" not in cookie  # Local HTTP remains usable.
    created = client.post("/api/tasks", json={"title": "Navigation stays connected"})
    assert created.status_code == 201
    for path in ("/", "/dev", "/", "/"):
        assert client.get(path).status_code == 200
        assert (
            client.get("/api/dashboard").json()["tasks"][0]["id"]
            == created.json()["id"]
        )
    assert client.delete("/api/session").status_code == 200
    assert client.get("/api/dashboard").status_code == 401
    assert COOKIE_NAME not in client.cookies
    # Signing out does not delete saved work.
    assert connect(client).status_code == 200
    assert len(client.get("/api/dashboard").json()["tasks"]) == 1


def test_session_cookie_is_secure_over_https(setup):
    clients, _, _ = setup
    client = clients(token="demo-secret")
    client.base_url = "https://testserver"
    response = connect(client)
    assert "Secure" in response.headers["set-cookie"]
    assert client.get("/api/dashboard").status_code == 200


@pytest.mark.parametrize("token", ["wrong", "unexpected-🔑"])
def test_invalid_login_does_not_issue_session_or_echo_credentials(setup, token):
    clients, _, _ = setup
    client = clients(token="demo-secret")
    response = connect(client, token)
    assert response.status_code == 401
    assert "set-cookie" not in response.headers
    assert token not in response.text
    assert client.get("/api/dashboard").status_code == 401


def test_login_validation_omits_submitted_secret(setup):
    clients, _, _ = setup
    response = connect(clients(token="secret"), "sensitive-" * 500)
    assert response.status_code == 422
    assert "sensitive-" not in response.text


def test_session_expiry_tampering_rotation_and_owner_binding(setup, monkeypatch):
    clients, _, _ = setup
    clock = [1000]
    monkeypatch.setattr("second_brain.session.time.time", lambda: clock[0])
    client = clients(token="demo-secret")
    assert connect(client).status_code == 200
    cookie = client.cookies.get(COOKIE_NAME)
    assert client.get("/api/dashboard").status_code == 200
    # Cross-worker validation uses the same configured owner and signing secret.
    other = clients(token="demo-secret")
    other.cookies.set(COOKIE_NAME, cookie, path="/api")
    assert other.get("/api/dashboard").status_code == 200
    for foreign in (clients("bob", token="demo-secret"), clients(token="rotated")):
        foreign.cookies.set(COOKIE_NAME, cookie, path="/api")
        assert foreign.get("/api/dashboard").status_code == 401
    clock[0] += SESSION_SECONDS + 1
    assert client.get("/api/dashboard").status_code == 401
    clock[0] = 1000
    for bad in (cookie[:-1] + ("a" if cookie[-1] != "a" else "b"), "broken", "1.x.bad"):
        other.cookies.clear()
        other.cookies.set(COOKIE_NAME, bad, path="/api")
        assert other.get("/api/dashboard").status_code == 401


def test_cross_origin_session_writes_are_rejected(setup):
    clients, _, _ = setup
    client = clients(token="demo-secret")
    malicious = {"Origin": "https://unrelated.example"}
    assert (
        client.post(
            "/api/session", json={"token": "demo-secret"}, headers=malicious
        ).status_code
        == 403
    )
    assert connect(client).status_code == 200
    assert (
        client.post(
            "/api/tasks", json={"title": "Not authorized"}, headers=malicious
        ).status_code
        == 403
    )
    assert client.delete("/api/session", headers=malicious).status_code == 403
    assert (
        client.post(
            "/api/tasks",
            json={"title": "Same origin"},
            headers={"Origin": "http://testserver"},
        ).status_code
        == 201
    )
    assert client.get("/api/dashboard").status_code == 200


def test_explicit_invalid_bearer_does_not_fall_back_to_cookie(setup):
    clients, _, _ = setup
    client = clients(token="demo-secret")
    assert connect(client).status_code == 200
    assert (
        client.get(
            "/api/dashboard", headers={"Authorization": "Bearer wrong"}
        ).status_code
        == 401
    )
    assert (
        clients(token="demo-secret")
        .get("/api/dashboard", headers={"Authorization": "Bearer demo-secret"})
        .status_code
        == 200
    )


def test_auth_and_data_responses_are_not_cached(setup):
    clients, _, _ = setup
    client = clients(token="demo-secret")
    for response in (
        client.get("/api/dashboard"),
        connect(client),
        client.get("/api/dashboard"),
        client.delete("/api/session"),
    ):
        assert response.headers["cache-control"] == "no-store"
    assert client.get("/health").json()["demo_access_required"] is True
    assert clients().get("/health").json()["demo_access_required"] is False


def test_hosted_session_uses_public_https_origin_behind_proxy(setup):
    from fastapi.testclient import TestClient

    from second_brain.api import create_app
    from second_brain.config import Settings

    _, muse, engine = setup
    settings = Settings(
        _env_file=None,
        vercel="1",
        database_url="postgresql://unused/db",
        mock_auth_token="demo-secret",
        meta_api_key=None,
    )
    client = TestClient(create_app(settings, engine, muse))
    # The public HTTPS origin can differ from the internal ASGI scheme.
    response = client.post(
        "/api/session",
        json={"token": "demo-secret"},
        headers={"Origin": "https://testserver"},
    )
    assert response.status_code == 200
    assert "Secure" in response.headers["set-cookie"]
    assert (
        client.post(
            "/api/session",
            json={"token": "demo-secret"},
            headers={"Origin": "https://other.example"},
        ).status_code
        == 403
    )
