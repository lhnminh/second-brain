from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import insert, select, update

from second_brain.db import runs, tasks, uid
from second_brain.muse import MuseFailure


def task(client, **overrides):
    response = client.post(
        "/api/tasks",
        json={
            "title": "Homework",
            "deadline": "2026-11-01",
            "user_importance_level": "high",
            **overrides,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def plan(client, record, request_id=None, message="Help me plan my homework"):
    response = client.post(
        f"/api/tasks/{record['id']}/plans",
        json={
            "request_id": request_id or str(uuid4()),
            "message": message,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_homework_review_edit_and_return(setup):
    clients, muse, _ = setup
    client = clients()
    ctx = client.put(
        "/api/context/studies",
        json={
            "expected_version": 0,
            "category": "current_situation",
            "content": "I study part time",
        },
    )
    assert ctx.status_code == 200
    parent = task(client)
    run = plan(client, parent)
    assert run["status"] == "awaiting_review"
    assert len(client.get("/api/dashboard").json()["tasks"]) == 1
    assert muse.snapshot["context"][0]["content"] == "I study part time"
    reviewed = run["proposal"]
    reviewed["subtasks"][0]["title"] = "Read the math assignment"
    assert (
        client.post(
            f"/api/runs/{run['id']}/approve", json={"proposal": reviewed}
        ).json()["status"]
        == "applied"
    )
    # Repeated approval is safe and cannot create duplicate subtasks.
    assert client.post(f"/api/runs/{run['id']}/approve", json={}).status_code == 200
    data = clients(cookies=client.cookies).get("/api/dashboard").json()
    assert len(data["tasks"]) == 3
    children = [t for t in data["tasks"] if t["parent_task_id"]]
    assert {t["title"] for t in children} == {
        "Read the math assignment",
        "Work through the questions",
    }
    assert all(t["deadline"] is None and t["status"] == "pending" for t in children)
    saved_parent = next(t for t in data["tasks"] if t["id"] == parent["id"])
    assert (
        saved_parent["status"] == "pending" and saved_parent["deadline"] == "2026-11-01"
    )
    edited = client.patch(
        f"/api/tasks/{children[0]['id']}",
        json={
            "expected_version": 1,
            "title": "My corrected step",
            "status": "completed",
        },
    )
    assert edited.status_code == 200
    assert any(
        t["title"] == "My corrected step" and t["status"] == "completed"
        for t in clients(cookies=client.cookies).get("/api/dashboard").json()["tasks"]
    )
    assert len(data["messages"]) == 2 and data["events"]


def test_isolation_and_cross_user_parent(setup):
    clients, muse, _ = setup
    alice, bob = clients(), clients("bob")
    parent = task(alice)
    run = plan(alice, parent)
    assert bob.get("/api/dashboard").json()["tasks"] == []
    assert bob.get("/api/dashboard").json()["runs"] == []
    assert (
        bob.post(
            "/api/tasks", json={"title": "Child", "parent_task_id": parent["id"]}
        ).status_code
        == 404
    )
    assert (
        bob.patch(
            f"/api/tasks/{parent['id']}",
            json={"expected_version": 1, "title": "Stolen"},
        ).status_code
        == 404
    )
    assert bob.post(f"/api/runs/{run['id']}/approve", json={}).status_code == 404
    assert bob.post(f"/api/runs/{run['id']}/reject").status_code == 404
    response = bob.post(
        f"/api/tasks/{parent['id']}/plans",
        json={"request_id": str(uuid4()), "message": "plan"},
    )
    assert response.status_code == 404
    assert muse.calls == 1


def test_idempotency_and_rejection(setup):
    clients, muse, _ = setup
    client = clients()
    parent = task(client)
    key = str(uuid4())
    run = plan(client, parent, key)
    assert plan(client, parent, key)["id"] == run["id"]
    assert muse.calls == 1
    assert (
        client.post(
            f"/api/tasks/{parent['id']}/plans",
            json={"request_id": key, "message": "different"},
        ).status_code
        == 409
    )
    assert client.post(f"/api/runs/{run['id']}/reject").json()["status"] == "rejected"
    assert client.post(f"/api/runs/{run['id']}/approve", json={}).status_code == 409
    assert len(client.get("/api/dashboard").json()["tasks"]) == 1


@pytest.mark.parametrize("change_context", [False, True])
def test_edits_invalidate_approval(setup, change_context):
    clients, _, _ = setup
    client = clients()
    parent = task(client)
    run = plan(client, parent)
    if change_context:
        client.put(
            "/api/context/studies",
            json={
                "expected_version": 0,
                "category": "current_situation",
                "content": "Homework is math",
            },
        )
    else:
        client.patch(
            f"/api/tasks/{parent['id']}",
            json={"expected_version": 1, "title": "Corrected homework"},
        )
    assert client.post(f"/api/runs/{run['id']}/approve", json={}).status_code == 409
    data = client.get("/api/dashboard").json()
    assert data["runs"][0]["status"] == "stale"
    assert len(data["tasks"]) == 1


def test_edit_during_provider_call(setup):
    clients, muse, _ = setup
    client = clients()
    parent = task(client)

    def edit(snapshot, message):
        client.patch(
            f"/api/tasks/{parent['id']}",
            json={"expected_version": 1, "description": "User correction"},
        )
        return {"reply": "Review", "importance_score": 70, "subtasks": []}

    muse.callback = edit
    assert plan(client, parent)["status"] == "stale"


@pytest.mark.parametrize(
    "invalid", ["failure", "bounds", "user_range", "invented_deadline", "boolean_score"]
)
def test_invalid_output_preserves_work(setup, invalid):
    clients, muse, _ = setup
    client = clients()
    parent = task(client)

    def fail(snapshot, message):
        if invalid == "failure":
            raise MuseFailure("do not expose provider details")
        score = {"bounds": 101, "user_range": 10, "boolean_score": True}.get(
            invalid, 70
        )
        child = {"title": "Read", "description": "Read it", "importance_score": 70}
        if invalid == "invented_deadline":
            child["deadline"] = "2026-10-30"
        return {"reply": "Review", "importance_score": score, "subtasks": [child]}

    muse.callback = fail
    run = plan(client, parent)
    assert run["status"] == "failed"
    assert run["proposal"] is None
    assert client.get("/api/dashboard").json()["tasks"] == [parent]


def test_stale_edit_and_importance_constraints(setup):
    clients, _, _ = setup
    client = clients()
    parent = task(client)
    run = plan(client, parent)
    client.post(f"/api/runs/{run['id']}/approve", json={})
    response = client.patch(
        f"/api/tasks/{parent['id']}",
        json={"expected_version": 2, "user_importance_level": "low"},
    )
    assert response.json()["importance_score"] == 39
    assert (
        client.patch(
            f"/api/tasks/{parent['id']}", json={"expected_version": 1, "title": "stale"}
        ).status_code
        == 409
    )
    assert (
        client.patch(
            f"/api/tasks/{parent['id']}",
            json={"expected_version": 3, "parent_task_id": parent["id"]},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/tasks/{parent['id']}", json={"expected_version": 3, "title": None}
        ).status_code
        == 422
    )


def test_context_correction_and_versions(setup):
    clients, muse, _ = setup
    client = clients()
    body = {
        "expected_version": 0,
        "category": "current_situation",
        "content": "Physics homework",
    }
    assert client.put("/api/context/homework", json=body).status_code == 200
    assert client.put("/api/context/homework", json=body).status_code == 409
    body.update(
        expected_version=1,
        content="Actually math homework",
        provenance="user_confirmed",
    )
    assert client.put("/api/context/homework", json=body).status_code == 200
    plan(client, task(client))
    assert muse.snapshot["context"][0]["content"] == "Actually math homework"
    assert muse.snapshot["context"][0]["provenance"] == "user_confirmed"


def test_authentication_and_no_caller_selected_identity(setup):
    clients, _, _ = setup
    client = clients(token="test-token")
    assert client.get("/api/dashboard").status_code == 401
    assert (
        client.get(
            "/api/dashboard", headers={"Authorization": "Bearer wrong"}
        ).status_code
        == 401
    )
    response = client.get(
        "/api/dashboard",
        headers={"Authorization": "Bearer test-token", "X-User-Id": "bob"},
    )
    assert response.json()["user_id"].startswith("browser-")
    assert response.json()["user_id"] != "bob"


def test_interrupted_run_recovery(setup):
    clients, _, engine = setup
    client = clients()
    parent = task(client)
    with engine.begin() as c:
        c.execute(
            insert(runs).values(
                id=uid(),
                user_id=parent["user_id"],
                task_id=parent["id"],
                request_id=str(uuid4()),
                message="plan",
                snapshot_revision=1,
                status="running",
                model="fixture",
                created_at="2020-01-01T00:00:00+00:00",
                updated_at="2020-01-01T00:00:00+00:00",
            )
        )
    data = client.get("/api/dashboard").json()
    assert data["runs"][0]["status"] == "failed"
    assert len(data["tasks"]) == 1


def test_concurrent_approval_has_one_effect(setup):
    clients, _, _ = setup
    client = clients()
    parent = task(client)
    run = plan(client, parent)
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(
                lambda _: clients(cookies=client.cookies).post(
                    f"/api/runs/{run['id']}/approve", json={}
                ),
                range(2),
            )
        )
    assert all(r.status_code == 200 for r in responses)
    assert len(client.get("/api/dashboard").json()["tasks"]) == 3


def test_bad_review_is_atomic(setup):
    clients, _, _ = setup
    client = clients()
    parent = task(client)
    run = plan(client, parent)
    proposal = run["proposal"]
    proposal["importance_score"] = 10
    assert (
        client.post(
            f"/api/runs/{run['id']}/approve", json={"proposal": proposal}
        ).status_code
        == 422
    )
    data = client.get("/api/dashboard").json()
    assert data["tasks"] == [parent]
    assert data["runs"][0]["status"] == "awaiting_review"


def test_database_enforces_cross_user_parent(setup):
    from sqlalchemy.exc import IntegrityError

    clients, _, engine = setup
    parent = task(clients())
    other = task(clients("bob"))
    with pytest.raises(IntegrityError), engine.begin() as c:
        c.execute(
            update(tasks)
            .where(tasks.c.id == other["id"])
            .values(parent_task_id=parent["id"])
        )
    with engine.connect() as c:
        assert (
            c.scalar(select(tasks.c.parent_task_id).where(tasks.c.id == other["id"]))
            is None
        )
