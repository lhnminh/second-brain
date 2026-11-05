"""Public judging access keeps ownership and existing browser workspaces."""

import pytest
from fastapi.testclient import TestClient

from second_brain.api import create_app
from second_brain.config import Settings


def public_client(engine, muse, cookies=None):
    client = TestClient(
        create_app(
            Settings(
                _env_file=None,
                database_url="postgresql://unused/db",
                mock_user_id="alice",
                mock_auth_token="existing-private-demo-code",
                public_demo=True,
                sample_workspace=False,
                vercel="1",
            ),
            engine=engine,
            muse=muse,
        ),
        base_url="https://testserver",
    )
    if cookies:
        client.cookies.update(cookies)
    return client


def test_public_access_preserves_workspace_isolation(setup):
    _, muse, engine = setup
    first, second = public_client(engine, muse), public_client(engine, muse)
    assert first.get("/health").json()["demo_access_required"] is False
    assert first.get("/api/dashboard").status_code == 200
    saved = first.post("/api/tasks", json={"title": "Private to this browser"}).json()
    assert second.get("/api/dashboard").json()["tasks"] == []
    assert (
        second.patch(
            "/api/tasks/" + saved["id"],
            json={"title": "Changed", "expected_version": 1},
        ).status_code
        == 404
    )
    returning = public_client(engine, muse, first.cookies)
    assert returning.get("/api/dashboard").json()["tasks"][0]["id"] == saved["id"]
    assert "existing-private-demo-code" not in first.get("/").text


def test_enabling_public_demo_keeps_previously_saved_work(setup):
    clients, muse, engine = setup
    private = clients(token="existing-private-demo-code")
    private.post("/api/session", json={"token": "existing-private-demo-code"})
    saved = private.post("/api/tasks", json={"title": "Keep existing work"}).json()
    public = public_client(engine, muse, private.cookies)
    assert public.get("/api/dashboard").json()["tasks"][0]["id"] == saved["id"]


def test_public_writes_still_require_the_app_origin(setup):
    _, muse, engine = setup
    client = public_client(engine, muse)
    response = client.post(
        "/api/tasks",
        json={"title": "Unwanted cross-site task"},
        headers={"Origin": "https://other.example", "Authorization": "Bearer ignored"},
    )
    assert response.status_code == 403
    assert client.get("/api/dashboard").json()["tasks"] == []


def test_public_hosting_requires_explicit_opt_in_and_postgres():
    Settings(
        _env_file=None,
        vercel="1",
        database_url="postgresql://unused/db",
        mock_auth_token=None,
        public_demo=True,
    ).validate_hosted()
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            vercel="1",
            database_url="postgresql://unused/db",
            mock_auth_token=None,
            public_demo=False,
        ).validate_hosted()
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            vercel="1",
            database_url="sqlite:///test.db",
            mock_auth_token=None,
            public_demo=True,
        ).validate_hosted()
