from copy import deepcopy
from uuid import uuid4

import pytest
from sqlalchemy import event, insert
from test_direct_tasks import TASK, fixture, send

from second_brain.db import messages, now, runs, uid


def test_task_chat_persists_across_clients_and_excludes_other_chats(setup):
    clients, muse, _ = setup
    client = clients()
    fixture(muse)
    creation = send(client).json()
    initial = client.get("/api/dashboard").json()
    task = next(t for t in initial["tasks"] if t["parent_task_id"] is None)
    assert task["id"] in initial["runs"][0]["related_task_ids"]
    other = client.post("/api/tasks", json={"title": "Another task"}).json()
    snapshots = []

    def reply(snapshot, message):
        snapshots.append(deepcopy(snapshot))
        return {"reply": "Saved conversation reply.", "tasks": []}

    muse.converse = reply
    assert (
        send(client, "Task A message", chat_task_id=task["id"]).json()["status"]
        == "answered"
    )
    assert snapshots[-1]["task"]["id"] == task["id"]
    assert snapshots[-1]["recent_runs"][0]["id"] == creation["id"]
    assert send(client, "Task B message", chat_task_id=other["id"]).status_code == 200
    assert snapshots[-1]["recent_messages"] == []
    returning = clients(cookies=client.cookies)
    assert (
        send(returning, "Return to task A", chat_task_id=task["id"]).status_code == 200
    )
    contents = [m["content"] for m in snapshots[-1]["recent_messages"]]
    assert "Task A message" in contents and "Task B message" not in contents
    assert send(returning, "General message").status_code == 200
    assert "Task A message" not in [
        m["content"] for m in snapshots[-1]["recent_messages"]
    ]
    # No accepted proposals/input payloads are duplicated in the model snapshot.
    assert all(
        "input_payload" not in r and "proposal" not in r
        for r in snapshots[-1]["recent_runs"]
    )
    data = returning.get("/api/dashboard").json()
    assert any(m["content"] == "Task A message" for m in data["messages"])


def test_task_chat_ownership_and_retry_scope(setup):
    clients, muse, _ = setup
    first, second = clients(), clients()
    task = first.post("/api/tasks", json={"title": "Private task"}).json()
    calls = []
    muse.converse = lambda snapshot, message: (
        calls.append(message) or {"reply": "Reply", "tasks": []}
    )
    assert send(second, chat_task_id=task["id"]).status_code == 404
    assert not calls
    assert second.get("/api/dashboard").json()["messages"] == []
    request = {
        "request_id": str(uuid4()),
        "message": "Remember this",
        "chat_task_id": task["id"],
        "apply_immediately": True,
    }
    run = first.post("/api/conversation", json=request).json()
    assert first.post("/api/conversation", json=request).json()["id"] == run["id"]
    assert (
        first.post(
            "/api/conversation", json={**request, "chat_task_id": None}
        ).status_code
        == 409
    )
    assert len(calls) == 1


def test_subtask_database_round_trips_do_not_grow_per_step(setup):
    clients, muse, engine = setup
    client = clients()
    statements = []

    def track(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    def create(count):
        fixture(
            muse,
            [
                {
                    **TASK,
                    "subtasks": [deepcopy(TASK["subtasks"][0]) for _ in range(count)],
                }
            ],
        )
        statements.clear()
        assert send(client).json()["status"] == "applied"
        return len(statements)

    event.listen(engine, "before_cursor_execute", track)
    try:
        one, eight = create(1), create(8)
    finally:
        event.remove(engine, "before_cursor_execute", track)
    assert eight == one
    data = client.get("/api/dashboard").json()
    root = next(t for t in reversed(data["tasks"]) if not t["parent_task_id"])
    children = [t for t in data["tasks"] if t["parent_task_id"] == root["id"]]
    assert len(children) == 8
    assert sorted(t["position"] for t in children) == list(range(8))
    assert len([e for e in data["events"] if e["kind"] == "task.created"]) == 11


def test_subtasks_share_root_context_and_legacy_messages_are_preserved(setup):
    clients, muse, engine = setup
    client = clients()
    root = client.post("/api/tasks", json={"title": "Parent"}).json()
    child = client.post(
        "/api/tasks", json={"title": "Step", "parent_task_id": root["id"]}
    ).json()
    sibling = client.post(
        "/api/tasks", json={"title": "Other step", "parent_task_id": root["id"]}
    ).json()
    user_id = client.get("/api/dashboard").json()["user_id"]
    with engine.begin() as c:
        run_id = uid()
        c.execute(
            insert(runs).values(
                id=run_id,
                user_id=user_id,
                task_id=None,
                request_id=uid(),
                message="Legacy step discussion",
                snapshot_revision=0,
                input_payload={"chat_task_id": child["id"]},
                status="answered",
                model="fixture",
                created_at=now(),
                updated_at=now(),
            )
        )
        c.execute(
            insert(messages).values(
                id=uid(),
                user_id=user_id,
                run_id=run_id,
                role="user",
                content="Legacy step discussion",
                created_at=now(),
            )
        )
    snapshots = []
    muse.converse = lambda snapshot, message: (
        snapshots.append(snapshot) or {"reply": "Reply", "tasks": []}
    )
    assert (
        send(client, "Sibling question", chat_task_id=sibling["id"]).json()["status"]
        == "answered"
    )
    assert snapshots[-1]["task"]["id"] == root["id"]
    assert snapshots[-1]["chat_task_id"] == root["id"]
    assert "Legacy step discussion" in [
        m["content"] for m in snapshots[-1]["recent_messages"]
    ]
    assert send(client, "Parent question", chat_task_id=root["id"]).status_code == 200
    assert "Sibling question" in [
        m["content"] for m in snapshots[-1]["recent_messages"]
    ]


def test_conversation_changes_focus_and_preserves_it_on_unrelated_edit(setup):
    clients, muse, _ = setup
    client = clients()
    root = client.post(
        "/api/tasks",
        json={
            "title": "Interview",
            "time_horizon": "short_term",
            "deadline": "2026-11-06",
        },
    ).json()
    update = {
        **TASK,
        "task_id": root["id"],
        "title": root["title"],
        "description": "",
        "deadline": root["deadline"],
        "subtasks": [],
        "time_horizon": "long_term",
    }
    fixture(muse, [update])
    assert send(client, "Move to long-term").json()["status"] == "applied"
    saved = client.get("/api/dashboard").json()["tasks"][0]
    assert saved["id"] == root["id"] and saved["time_horizon"] == "long_term"
    assert saved["deadline"] == root["deadline"]
    fixture(muse, [{**update, "time_horizon": None, "title": "Updated interview"}])
    assert send(client, "Rename").json()["status"] == "applied"
    assert (
        client.get("/api/dashboard").json()["tasks"][0]["time_horizon"] == "long_term"
    )


def test_answer_identifies_existing_task_and_keeps_question_in_its_history(setup):
    clients, muse, _ = setup
    client, other = clients(), clients()
    task = client.post("/api/tasks", json={"title": "Pottery"}).json()
    muse.converse = lambda snapshot, message: {
        "reply": "Brief answer",
        "tasks": [],
        "chat_task_id": task["id"],
    }
    assert (
        send(client, "About pottery").json()["proposal"]["chat_task_id"] == task["id"]
    )
    assert send(other, "Foreign ID must fail").json()["status"] == "failed"
    snapshots = []
    muse.converse = lambda snapshot, message: (
        snapshots.append(snapshot) or {"reply": "Reply", "tasks": []}
    )
    assert send(client, "Follow up", chat_task_id=task["id"]).status_code == 200
    assert "About pottery" in [m["content"] for m in snapshots[-1]["recent_messages"]]


@pytest.mark.parametrize("operation", ["answer", "edit", "create"])
def test_rerouted_exchange_has_one_chat_after_reload_and_in_model_context(
    setup, operation
):
    clients, muse, _ = setup
    client = clients()
    origin = client.post("/api/tasks", json={"title": "Origin task"}).json()
    target = client.post("/api/tasks", json={"title": "Destination task"}).json()
    request = {
        "request_id": str(uuid4()),
        "message": "Question for destination",
        "apply_immediately": True,
        "chat_task_id": origin["id"],
    }
    proposal = {
        "reply": "Destination answer",
        "tasks": [],
        "chat_task_id": target["id"],
    }
    if operation != "answer":
        proposal["tasks"] = [
            {
                **TASK,
                "task_id": None if operation == "create" else target["id"],
                "subtasks": [],
                "title": "New task" if operation == "create" else target["title"],
            }
        ]
        proposal["chat_task_id"] = None
    muse.converse = lambda snapshot, message: deepcopy(proposal)
    run = client.post("/api/conversation", json=request).json()
    assert run["status"] in {"applied", "answered"}
    returning = clients(cookies=client.cookies)
    data = returning.get("/api/dashboard").json()
    if operation == "create":
        target = next(t for t in data["tasks"] if t["title"] == "New task")
    saved_run = next(r for r in data["runs"] if r["id"] == run["id"])
    assert saved_run["chat_scope_id"] == target["id"]
    assert saved_run["input_payload"] == {
        "conversation_id": None,
        "review_draft": None,
        "keep_chat_scope": False,
        "web_enabled": False,
        "delegated_task_id": None,
        **request,
    }
    assert len([m for m in data["messages"] if m["run_id"] == run["id"]]) == 2
    # Retries retain the original request identity even though the visible chat moved.
    assert returning.post("/api/conversation", json=request).json()["id"] == run["id"]
    snapshots = []
    muse.converse = lambda snapshot, message: (
        snapshots.append(snapshot) or {"reply": "Reply", "tasks": []}
    )
    for scope in (origin["id"], None, target["id"]):
        assert send(returning, "Follow-up", chat_task_id=scope).status_code == 200
        contents = [m["content"] for m in snapshots[-1]["recent_messages"]]
        assert ("Question for destination" in contents) == (scope == target["id"])
        assert ("Destination answer" in contents) == (scope == target["id"])


def test_handoff_requires_short_term_and_every_subtask_eligible(setup):
    clients, muse, _ = setup
    client = clients()
    handoff = {
        "handler": "muse",
        "reason": "Research",
        "requirements": [],
        "done_when": "Notes",
    }
    root = client.post(
        "/api/tasks",
        json={
            "title": "Research",
            "time_horizon": "short_term",
            "subtasks": [{"title": "Read"}, {"title": "Compare"}],
        },
    ).json()
    children = root.pop("subtasks")
    calls = []
    muse.converse = lambda snapshot, message: (
        calls.append(snapshot) or {"reply": "Result", "tasks": []}
    )

    def delegate(task):
        return client.post(
            "/api/conversation",
            json={
                "request_id": str(uuid4()),
                "message": "Work on this",
                "chat_task_id": root["id"],
                "delegated_task_id": task["id"],
                "keep_chat_scope": True,
            },
        )

    assert delegate(root).status_code == 409
    for child in children:
        client.patch(
            "/api/tasks/" + child["id"],
            json={"expected_version": child["version"], "handoff": handoff},
        )
    assert delegate(root).status_code == 200 and len(calls) == 1
    client.patch(
        "/api/tasks/" + children[1]["id"],
        json={"expected_version": 2, "handoff": {**handoff, "handler": "user"}},
    )
    assert delegate(root).status_code == 409
    # Eligible individual steps still work even when the whole short-term plan cannot.
    assert delegate(children[0]).status_code == 200
    saved = client.patch(
        "/api/tasks/" + root["id"],
        json={"expected_version": root["version"], "time_horizon": "long_term"},
    )
    assert saved.status_code == 200
    assert delegate(root).status_code == 409
    assert delegate(children[0]).status_code == 409
    # Ordinary Ask Muse chat is still available for long-term work.
    assert send(client, "Help me plan", chat_task_id=root["id"]).status_code == 200
