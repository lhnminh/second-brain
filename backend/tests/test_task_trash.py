"""Reversible removal, ownership and preserved chat identities."""

from uuid import uuid4

from sqlalchemy import func, select

from second_brain.db import messages, tasks


def remove(client, task, request_id=None):
    return client.request(
        "DELETE",
        "/api/tasks/" + task["id"],
        json={
            "request_id": request_id or str(uuid4()),
            "expected_version": task["version"],
        },
    )


def test_trash_hides_a_tree_preserves_history_and_undo_restores_ids(setup):
    clients, muse, engine = setup
    client = clients()
    root = client.post(
        "/api/tasks",
        json={
            "title": "Short work",
            "time_horizon": "short_term",
            "subtasks": [{"title": "A step"}],
        },
    ).json()
    child = root["subtasks"][0]
    long = client.post(
        "/api/tasks", json={"title": "Long work", "time_horizon": "long_term"}
    ).json()
    muse.converse = lambda snapshot, message: {"reply": "Saved chat reply", "tasks": []}
    run = client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": "Task private context",
            "chat_task_id": root["id"],
            "keep_chat_scope": True,
        },
    ).json()
    deletion = remove(client, root).json()
    assert set(deletion["task_ids"]) == {root["id"], child["id"]}
    data = client.get("/api/dashboard").json()
    assert [t["id"] for t in data["tasks"]] == [long["id"]]
    hidden = next(r for r in data["runs"] if r["id"] == run["id"])
    assert hidden["chat_hidden"] is True and hidden["chat_scope_id"] == root["id"]
    with engine.connect() as c:
        assert c.scalar(select(func.count()).select_from(tasks)) == 3
        assert c.scalar(select(func.count()).select_from(messages)) == 2
    assert (
        client.patch(
            "/api/tasks/" + child["id"],
            json={"expected_version": child["version"], "title": "Must not revive"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/tasks", json={"title": "No child", "parent_task_id": root["id"]}
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/tasks/" + root["id"] + "/restore",
            json={"deletion_id": deletion["deletion_id"]},
        ).status_code
        == 200
    )
    restored = client.get("/api/dashboard").json()
    assert {t["id"] for t in restored["tasks"]} == {root["id"], child["id"], long["id"]}
    assert (
        next(r for r in restored["runs"] if r["id"] == run["id"])["chat_hidden"]
        is False
    )
    assert (
        client.post(
            "/api/tasks/" + root["id"] + "/restore",
            json={"deletion_id": deletion["deletion_id"]},
        ).status_code
        == 200
    )


def test_trash_retry_ownership_versions_and_independently_deleted_children(setup):
    clients, _, _ = setup
    first, other = clients(), clients()
    root = first.post(
        "/api/tasks",
        json={"title": "Root", "subtasks": [{"title": "One"}, {"title": "Two"}]},
    ).json()
    child = root["subtasks"][0]
    assert remove(other, root).status_code == 404
    assert remove(first, {**root, "version": 99}).status_code == 409
    child_delete = remove(first, child).json()
    request_id = str(uuid4())
    deletion = remove(first, root, request_id).json()
    assert child["id"] not in deletion["task_ids"]
    assert remove(first, root, request_id).json() == deletion
    assert remove(first, {**root, "version": 99}, request_id).status_code == 409
    assert (
        other.post(
            "/api/tasks/" + root["id"] + "/restore",
            json={"deletion_id": deletion["deletion_id"]},
        ).status_code
        == 404
    )
    assert (
        first.post(
            "/api/tasks/" + child["id"] + "/restore",
            json={"deletion_id": child_delete["deletion_id"]},
        ).status_code
        == 404
    )
    assert (
        first.post(
            "/api/tasks/" + root["id"] + "/restore",
            json={"deletion_id": deletion["deletion_id"]},
        ).status_code
        == 200
    )
    assert child["id"] not in {
        t["id"] for t in first.get("/api/dashboard").json()["tasks"]
    }
    assert (
        first.post(
            "/api/tasks/" + child["id"] + "/restore",
            json={"deletion_id": child_delete["deletion_id"]},
        ).status_code
        == 200
    )


def test_new_surface_keeps_general_and_task_handoffs_in_their_chosen_chats(setup):
    clients, muse, engine = setup
    client = clients()
    root = client.post(
        "/api/tasks",
        json={"title": "Research", "subtasks": [{"title": "Compare sources"}]},
    ).json()
    child = root["subtasks"][0]
    client.patch(
        "/api/tasks/" + child["id"],
        json={
            "expected_version": child["version"],
            "handoff": {
                "handler": "muse",
                "reason": "Research",
                "requirements": [],
                "done_when": "Comparison",
            },
        },
    )
    seen = []
    muse.converse = lambda snapshot, message: (
        seen.append(snapshot)
        or {"reply": "Answer", "tasks": [], "chat_task_id": root["id"]}
    )
    general = client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": "Question about Research",
            "keep_chat_scope": True,
            "web_enabled": True,
        },
    ).json()
    handoff = client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": "Work on the comparison",
            "chat_task_id": root["id"],
            "delegated_task_id": child["id"],
            "keep_chat_scope": True,
            "web_enabled": True,
        },
    ).json()
    assert (
        handoff["status"] == "answered"
        and seen[-1]["delegated_task"]["id"] == child["id"]
    )
    assert seen[-1]["task"]["id"] == root["id"] and seen[-1]["recent_messages"] == []
    runs = client.get("/api/dashboard").json()["runs"]
    assert next(r for r in runs if r["id"] == general["id"])["chat_scope_id"] is None
    assert (
        next(r for r in runs if r["id"] == handoff["id"])["chat_scope_id"] == root["id"]
    )
    from second_brain.db import browser_runs

    with engine.connect() as c:
        assert c.scalar(select(func.count()).select_from(browser_runs)) == 0
    another = client.post("/api/tasks", json={"title": "Other task"}).json()
    assert (
        client.post(
            "/api/conversation",
            json={
                "request_id": str(uuid4()),
                "message": "Wrong scope",
                "chat_task_id": another["id"],
                "delegated_task_id": child["id"],
            },
        ).status_code
        == 422
    )


def test_deleted_task_chat_does_not_leak_into_general_model_context(setup):
    clients, muse, _ = setup
    client = clients()
    root = client.post("/api/tasks", json={"title": "Private work"}).json()
    seen = []
    muse.converse = lambda snapshot, message: (
        seen.append(snapshot) or {"reply": "Answer", "tasks": []}
    )
    client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": "Only in this task",
            "chat_task_id": root["id"],
            "keep_chat_scope": True,
        },
    )
    remove(client, root)
    client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": "General follow-up",
            "keep_chat_scope": True,
        },
    )
    assert seen[-1]["recent_messages"] == [] and seen[-1]["tasks"] == []


def test_task_handoff_retains_relevant_general_context_without_copying_history(setup):
    clients, muse, _ = setup
    client = clients()
    handoff = {
        "handler": "muse",
        "reason": "Research",
        "requirements": [],
        "done_when": "A sourced summary",
    }
    muse.converse = lambda snapshot, message: {
        "reply": "Created",
        "tasks": [
            {
                "task_id": None,
                "title": "Prepare report",
                "description": "",
                "deadline": None,
                "importance_score": 50,
                "subtasks": [],
                "handoff": handoff,
                "time_horizon": "short_term",
            }
        ],
    }
    creation = client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": "Prepare a report comparing IANA and ICANN using official sources.",
            "keep_chat_scope": True,
            "apply_immediately": True,
        },
    ).json()
    root = client.get("/api/dashboard").json()["tasks"][0]
    seen = []
    muse.converse = lambda snapshot, message: (
        seen.append(snapshot) or {"reply": "Answer", "tasks": []}
    )
    client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": "Unrelated general discussion",
            "keep_chat_scope": True,
        },
    )
    result = client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": "Work on this report",
            "chat_task_id": root["id"],
            "delegated_task_id": root["id"],
            "keep_chat_scope": True,
        },
    ).json()
    assert result["status"] == "answered"
    assert seen[-1]["task_user_context"][0]["message"] == creation["message"]
    assert len(seen[-1]["task_user_context"]) == 1 and seen[-1]["recent_messages"] == []
    saved = client.get("/api/dashboard").json()
    assert (
        next(r for r in saved["runs"] if r["id"] == creation["id"])["chat_scope_id"]
        is None
    )
    assert len([m for m in saved["messages"] if m["run_id"] == creation["id"]]) == 2
