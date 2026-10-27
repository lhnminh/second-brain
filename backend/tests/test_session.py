"""Browser navigation, session lifetime, and existing bearer authentication."""

import pytest

from second_brain.session import (
    COOKIE_NAME,
    SESSION_SECONDS,
    WORKSPACE_COOKIE_NAME,
    WORKSPACE_SECONDS,
)


def connect(client, token="demo-secret"):
    return client.post("/api/session", json={"token": token})


def test_browser_session_survives_page_navigation_and_reload(setup):
    clients, _, _ = setup
    client = clients(token="demo-secret")
    assert client.get("/api/dashboard").status_code == 401
    response = connect(client)
    assert response.status_code == 200
    assert "demo-secret" not in response.text
    cookie = next(
        c
        for c in response.headers.get_list("set-cookie")
        if c.startswith(COOKIE_NAME + "=")
    )
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
    other.cookies.update(client.cookies)
    assert other.get("/api/dashboard").status_code == 200
    for foreign in (clients("bob", token="demo-secret"), clients(token="rotated")):
        foreign.cookies.update(client.cookies)
        assert foreign.get("/api/dashboard").status_code == 401
    clock[0] += SESSION_SECONDS + 1
    assert client.get("/api/dashboard").status_code == 401
    clock[0] = 1000
    for bad in (cookie[:-1] + ("a" if cookie[-1] != "a" else "b"), "broken", "1.x.bad"):
        other.cookies.clear()
        other.cookies.update(client.cookies)
        other.cookies.delete(COOKIE_NAME)
        other.cookies.set(COOKIE_NAME, bad, path="/api")
        assert other.get("/api/dashboard").status_code == 401


@pytest.mark.parametrize("token", [None, "demo-secret"])
def test_browser_workspaces_isolate_full_journey_and_survive_restart(setup, token):
    from uuid import uuid4

    clients, muse, engine = setup
    alice, bob = clients(token=token), clients(token=token)
    for browser in (alice, bob):
        page = browser.get("/")
        assert f"Max-Age={WORKSPACE_SECONDS}" in page.headers["set-cookie"]
        assert "HttpOnly" in page.headers["set-cookie"]
        assert "SameSite=lax" in page.headers["set-cookie"]
        assert "Path=/;" in page.headers["set-cookie"]
        if token:
            assert connect(browser).status_code == 200
    capability = alice.cookies.get(WORKSPACE_COOKIE_NAME)
    assert capability != bob.cookies.get(WORKSPACE_COOKIE_NAME)
    parent = alice.post("/api/tasks", json={"title": "My homework"}).json()
    assert (
        alice.put(
            "/api/context/studies",
            json={
                "expected_version": 0,
                "category": "current_situation",
                "content": "Math",
            },
        ).status_code
        == 200
    )
    request = {"request_id": str(uuid4()), "message": "Plan my homework"}
    run = alice.post(f"/api/tasks/{parent['id']}/plans", json=request).json()
    assert run["status"] == "awaiting_review"
    empty = bob.get("/api/dashboard").json()
    for key in ("tasks", "context", "runs", "messages", "events"):
        assert empty[key] == []
    assert empty["user_id"] != parent["user_id"]
    assert capability not in str(alice.get("/api/dashboard").json())
    assert (
        bob.patch(
            f"/api/tasks/{parent['id']}",
            json={"expected_version": 1, "title": "Stolen"},
        ).status_code
        == 404
    )
    assert (
        bob.post(
            "/api/tasks",
            json={"title": "Foreign child", "parent_task_id": parent["id"]},
        ).status_code
        == 404
    )
    assert bob.post(f"/api/runs/{run['id']}/approve", json={}).status_code == 404
    assert bob.post(f"/api/runs/{run['id']}/reject").status_code == 404
    # The same request key in a different browser is a separate planning request.
    other_task = bob.post("/api/tasks", json={"title": "Other homework"}).json()
    assert (
        bob.post(f"/api/tasks/{other_task['id']}/plans", json=request).status_code
        == 200
    )
    assert muse.snapshot["context"] == []
    assert all(t["id"] != parent["id"] for t in muse.snapshot["tasks"])
    assert alice.post(f"/api/runs/{run['id']}/approve", json={}).status_code == 200
    saved = alice.get("/api/dashboard").json()
    # A fresh app instance and DB connection represent a restart/another worker.
    engine.dispose()
    returning = clients(token=token, cookies=alice.cookies)
    for path in ("/dev", "/"):
        assert returning.get(path).status_code == 200
        assert returning.get("/api/dashboard").json() == saved
        assert returning.cookies.get(WORKSPACE_COOKIE_NAME) == capability


def test_workspace_persists_after_access_expiry_and_token_rotation(setup, monkeypatch):
    clients, _, _ = setup
    clock = [1000]
    monkeypatch.setattr("second_brain.session.time.time", lambda: clock[0])
    client = clients(token="demo-secret")
    connect(client)
    parent = client.post("/api/tasks", json={"title": "Keep my work"}).json()
    clock[0] += SESSION_SECONDS + 1
    assert client.get("/api/dashboard").status_code == 401
    connect(client)
    assert client.get("/api/dashboard").json()["tasks"] == [parent]
    rotated = clients(token="rotated", cookies=client.cookies)
    assert rotated.get("/api/dashboard").status_code == 401
    assert connect(rotated, "rotated").status_code == 200
    assert rotated.get("/api/dashboard").json()["tasks"] == [parent]


def test_session_requires_its_workspace_and_clearing_cookies_starts_empty(setup):
    clients, _, _ = setup
    alice, bob = clients(token="demo-secret"), clients(token="demo-secret")
    connect(alice)
    connect(bob)
    alice.post("/api/tasks", json={"title": "Original workspace"})
    # A session alone, or combined with a different workspace, grants no access.
    session_only = clients(token="demo-secret")
    session_only.cookies.set(COOKIE_NAME, alice.cookies.get(COOKIE_NAME), path="/api")
    assert session_only.get("/api/dashboard").status_code == 401
    session_only.cookies.set(
        WORKSPACE_COOKIE_NAME, bob.cookies.get(WORKSPACE_COOKIE_NAME), path="/"
    )
    assert session_only.get("/api/dashboard").status_code == 401
    alice.cookies.clear()
    assert connect(alice).status_code == 200
    assert alice.get("/api/dashboard").json()["tasks"] == []


def test_public_owner_id_cannot_be_used_as_workspace_capability(setup):
    clients, _, _ = setup
    alice, bob = clients(), clients()
    parent = alice.post("/api/tasks", json={"title": "Private"}).json()
    bob.cookies.set(WORKSPACE_COOKIE_NAME, parent["user_id"], path="/")
    data = bob.get("/api/dashboard").json()
    assert data["tasks"] == [] and data["user_id"] != parent["user_id"]


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
