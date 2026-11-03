from copy import deepcopy
from uuid import uuid4

from sqlalchemy import event
from test_direct_tasks import TASK, fixture, send


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
