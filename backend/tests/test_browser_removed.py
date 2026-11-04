"""Retired computer control cannot be started through the app."""

from uuid import uuid4


def test_browser_control_routes_are_removed(setup):
    clients, _, _ = setup
    client = clients()
    assert client.get("/api/browser").status_code == 404
    assert (
        client.post("/api/browser/runs", json={"request_id": str(uuid4())}).status_code
        == 404
    )
    schema = client.get("/openapi.json").json()
    assert not any(path.startswith("/api/browser") for path in schema["paths"])
    page = client.get("/").text
    assert "use-task-browser" not in page and "handoff-dialog" not in page
