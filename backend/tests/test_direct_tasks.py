"""The dashboard saves validated tasks in the same request as the conversation."""

from copy import deepcopy
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from second_brain.muse import MuseFailure
from second_brain.service import Service

HANDOFF = {
    "handler": "muse",
    "reason": "Produces a document on a computer.",
    "requirements": ["Meeting notes"],
    "done_when": "An agenda draft is ready.",
}
TASK = {
    "task_id": None,
    "title": "Prepare a meeting",
    "description": "Use project notes",
    "deadline": None,
    "importance_score": 60,
    "handoff": HANDOFF,
    "subtasks": [
        {
            "title": "Draft the agenda",
            "description": "Use the notes",
            "importance_score": 60,
            "handoff": HANDOFF,
        }
    ],
}


def fixture(muse, items=None):
    def respond(snapshot, message):
        muse.calls += 1
        muse.snapshot = deepcopy(snapshot)
        return {
            "reply": "Here is your meeting plan.",
            "tasks": deepcopy(items if items is not None else [TASK]),
        }

    muse.converse = respond


def send(client, message="Prepare my meeting", **changes):
    return client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": message,
            "apply_immediately": True,
            **changes,
        },
    )


def test_task_and_classified_steps_are_saved_before_reply_and_can_be_corrected(setup):
    clients, muse, _ = setup
    client = clients()
    fixture(muse)
    result = send(client)
    assert result.status_code == 200
    run = result.json()
    assert run["status"] == "applied" and muse.snapshot["apply_immediately"] is True
    data = client.get("/api/dashboard").json()
    assert len(data["tasks"]) == 2
    root = next(t for t in data["tasks"] if not t["parent_task_id"])
    child = next(t for t in data["tasks"] if t["parent_task_id"])
    assert child["parent_task_id"] == root["id"] and child["handoff"] == HANDOFF
    assert all(t["status"] == "pending" for t in data["tasks"])
    assert not any(r["status"] == "awaiting_review" for r in data["runs"])
    corrected = client.patch(
        "/api/tasks/" + child["id"],
        json={
            "expected_version": child["version"],
            "title": "Use only the supplied meeting notes",
        },
    ).json()
    returning = clients(cookies=client.cookies)
    assert corrected in returning.get("/api/dashboard").json()["tasks"]
    # An explicit follow-up updates the saved object, rather than another draft.
    fixture(
        muse,
        [
            {
                **TASK,
                "task_id": root["id"],
                "title": "Prepare Monday meeting",
                "subtasks": [],
            }
        ],
    )
    followup = send(client, "Rename it to Prepare Monday meeting").json()
    assert followup["status"] == "applied"
    assert corrected in muse.snapshot["tasks"]
    saved = client.get("/api/dashboard").json()["tasks"]
    assert len(saved) == 2 and corrected in saved
    assert (
        next(t for t in saved if t["id"] == root["id"])["title"]
        == "Prepare Monday meeting"
    )
    assert clients("bob").get("/api/dashboard").json()["tasks"] == []


def test_retries_cannot_duplicate_tasks_or_switch_save_modes(setup):
    clients, muse, _ = setup
    client = clients()
    fixture(muse)
    run = send(client).json()
    payload = run["input_payload"]
    assert client.post("/api/conversation", json=payload).json()["id"] == run["id"]
    assert muse.calls == 1
    assert len(client.get("/api/dashboard").json()["tasks"]) == 2
    for change in ({"message": "Different"}, {"apply_immediately": False}):
        assert (
            client.post("/api/conversation", json={**payload, **change}).status_code
            == 409
        )
    assert len(client.get("/api/dashboard").json()["tasks"]) == 2


def test_clarification_can_save_concrete_work_without_inventing_steps(setup):
    clients, muse, _ = setup
    client = clients()
    fixture(muse, [{**TASK, "subtasks": []}])
    assert (
        send(client, "Prepare a meeting; details are still unknown").json()["status"]
        == "applied"
    )
    saved = client.get("/api/dashboard").json()["tasks"]
    assert len(saved) == 1 and saved[0]["deadline"] is None
    fixture(muse, [])
    assert send(client, "What can you do?").json()["status"] == "answered"
    assert client.get("/api/dashboard").json()["tasks"] == saved


@pytest.mark.parametrize("kind", ["provider", "invalid", "unclassified", "foreign"])
def test_failure_never_creates_or_edits_tasks(setup, kind):
    clients, muse, _ = setup
    client = clients()
    existing = client.post("/api/tasks", json={"title": "Keep my work"}).json()
    value = deepcopy(TASK)
    if kind == "provider":

        def fail(*_):
            raise MuseFailure("Provider details")

        muse.converse = fail
    else:
        if kind == "invalid":
            value["subtasks"][0]["handoff"] = {**HANDOFF, "handler": "unknown"}
        elif kind == "unclassified":
            value["subtasks"][0].pop("handoff")
        else:
            value["task_id"] = (
                clients("bob")
                .post("/api/tasks", json={"title": "Private"})
                .json()["id"]
            )
        fixture(muse, [value])
    run = send(client).json()
    assert run["status"] == "failed"
    assert client.get("/api/dashboard").json()["tasks"] == [existing]


def test_edit_during_model_call_prevents_stale_automatic_save(setup):
    clients, muse, _ = setup
    client = clients()
    existing = client.post("/api/tasks", json={"title": "Original"}).json()

    def respond(*_):
        client.patch(
            "/api/tasks/" + existing["id"],
            json={"expected_version": existing["version"], "title": "My correction"},
        )
        return {"reply": "A plan", "tasks": [TASK]}

    muse.converse = respond
    assert send(client).json()["status"] == "stale"
    saved = client.get("/api/dashboard").json()["tasks"]
    assert len(saved) == 1 and saved[0]["title"] == "My correction"


def test_older_overlapping_reply_cannot_create_duplicate_work(setup):
    clients, muse, _ = setup
    client = clients()
    client.get("/")

    def respond(*_):
        fixture(muse, [{**TASK, "title": "Latest request"}])
        assert send(client, "My newer correction").json()["status"] == "applied"
        return {"reply": "Old plan", "tasks": [TASK]}

    muse.converse = respond
    assert send(client).json()["status"] == "stale"
    roots = [
        t
        for t in client.get("/api/dashboard").json()["tasks"]
        if not t["parent_task_id"]
    ]
    assert len(roots) == 1 and roots[0]["title"] == "Latest request"


def test_database_failure_rolls_back_all_task_changes(setup, monkeypatch):
    clients, muse, _ = setup
    client = clients()
    fixture(muse)
    original = Service._insert_conversation_task
    calls = 0

    def fail_second(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise SQLAlchemyError("Simulated transaction failure")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Service, "_insert_conversation_task", fail_second)
    assert send(client).status_code == 503
    data = client.get("/api/dashboard").json()
    assert data["tasks"] == []
    assert not any(event["kind"] == "task.created" for event in data["events"])
    assert not any(message["role"] == "assistant" for message in data["messages"])


def test_direct_save_protects_user_handoff_corrections(setup):
    clients, muse, _ = setup
    client = clients()
    manual = {**HANDOFF, "handler": "user", "reason": "I want to do this myself."}
    existing = client.post(
        "/api/tasks", json={"title": "My task", "handoff": manual}
    ).json()
    fixture(muse, [{**TASK, "task_id": existing["id"], "subtasks": []}])
    assert send(client).json()["status"] == "failed"
    assert client.get("/api/dashboard").json()["tasks"] == [existing]


def test_applied_conversation_supersedes_old_unsaved_plan(setup):
    clients, muse, _ = setup
    client = clients()
    fixture(muse)
    old = send(client, apply_immediately=False).json()
    assert old["status"] == "awaiting_review"
    assert send(client).json()["status"] == "applied"
    data = client.get("/api/dashboard").json()
    assert (
        next(r for r in data["runs"] if r["id"] == old["id"])["status"] == "superseded"
    )
    assert len(data["tasks"]) == 2


def test_title_correction_preserves_a_user_cleared_assessment(setup):
    clients, muse, _ = setup
    client = clients()
    task = client.post("/api/tasks", json={"title": "Original"}).json()
    cleared = client.patch(
        "/api/tasks/" + task["id"],
        json={"expected_version": task["version"], "handoff": None},
    ).json()
    fixture(
        muse,
        [
            {
                **TASK,
                "task_id": task["id"],
                "title": "Corrected title",
                "handoff": None,
                "subtasks": [],
            }
        ],
    )
    assert send(client, "Correct the title").json()["status"] == "applied"
    saved = client.get("/api/dashboard").json()["tasks"][0]
    assert saved["title"] == "Corrected title"
    assert (
        saved["handoff"] is None
        and saved["handoff_source"] == cleared["handoff_source"] == "user"
    )


def test_legacy_retry_payload_without_save_mode_remains_idempotent(setup):
    from sqlalchemy import update

    from second_brain.db import runs

    clients, muse, engine = setup
    client = clients()
    fixture(muse)
    run = send(client, apply_immediately=False).json()
    legacy_payload = run["input_payload"]
    legacy_payload.pop("apply_immediately")
    with engine.begin() as c:
        c.execute(
            update(runs)
            .where(runs.c.id == run["id"])
            .values(input_payload=legacy_payload)
        )
    retry = client.post("/api/conversation", json=legacy_payload)
    assert retry.status_code == 200 and retry.json()["id"] == run["id"]
    assert muse.calls == 1
    assert client.get("/api/dashboard").json()["tasks"] == []
