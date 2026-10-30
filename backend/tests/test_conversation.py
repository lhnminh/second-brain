"""Conversation fixtures exercise persistence and safety, not live model quality."""

from copy import deepcopy
from uuid import uuid4

import pytest

from second_brain.muse import MuseFailure

TASK = {
    "task_id": None,
    "title": "Homework",
    "description": "Chapter 3 questions",
    "deadline": "2026-11-01",
    "importance_score": 70,
    "subtasks": [
        {"title": "Read chapter 3", "description": "Take notes", "importance_score": 60}
    ],
}


def converse(client, message="Plan my homework", request_id=None):
    return client.post(
        "/api/conversation",
        json={"request_id": request_id or str(uuid4()), "message": message},
    )


def fixture(muse, tasks=None):
    def respond(snapshot, message):
        muse.calls += 1
        muse.snapshot = snapshot
        return {
            "reply": "Review this plan.",
            "tasks": deepcopy(tasks if tasks is not None else [TASK]),
        }

    muse.converse = respond


def approve(client, run, **body):
    return client.post(f"/api/conversation/{run['id']}/approve", json=body)


def test_conversation_review_correction_and_saved_reload(setup):
    clients, muse, _ = setup
    fixture(muse)
    client = clients()
    run = converse(client).json()
    assert run["task_id"] is None
    assert run["status"] == "awaiting_review"
    assert client.get("/api/dashboard").json()["tasks"] == []
    run["proposal"]["tasks"][0]["subtasks"][0]["title"] = "Read only assigned pages"
    assert approve(client, run, proposal=run["proposal"]).status_code == 200
    assert approve(client, run).status_code == 200
    data = clients(cookies=client.cookies).get("/api/dashboard").json()
    assert len(data["tasks"]) == 2
    parent = next(t for t in data["tasks"] if t["parent_task_id"] is None)
    child = next(t for t in data["tasks"] if t["parent_task_id"])
    assert child["parent_task_id"] == parent["id"]
    assert child["title"] == "Read only assigned pages"
    assert parent["deadline"] == "2026-11-01"
    assert child["deadline"] is None
    assert len(data["messages"]) == 2
    assert clients("bob").get("/api/dashboard").json()["tasks"] == []
    assert approve(clients("bob"), run).status_code == 404


def test_take_home_cards_survive_review_correction_and_return(setup, monkeypatch):
    """Mock provider output verifies the real adapter and saved dashboard journey."""
    import json

    import httpx

    from second_brain.config import Settings
    from second_brain.muse import Muse

    clients, muse, _ = setup
    proposal = {
        "reply": "Review the proposed take-home card and steps before saving.",
        "tasks": [
            {
                "task_id": None,
                "title": "Complete Duolingo take-home",
                "description": "Read the supplied brief and prepare the submission.",
                "deadline": None,
                "importance_score": 70,
                "subtasks": [
                    {
                        "title": "Read the assignment brief",
                        "description": "List its required deliverables and constraints.",
                        "importance_score": 70,
                    },
                    {
                        "title": "Prepare the required submission",
                        "description": "Follow the deliverables listed in the brief.",
                        "importance_score": 70,
                    },
                ],
            }
        ],
    }
    for item in proposal["tasks"]:
        for step in (item, *item["subtasks"]):
            step["handoff"] = {
                "handler": "user",
                "reason": "The user will prepare and review this submission.",
                "requirements": ["Assignment brief"],
                "done_when": "The required work has been prepared and checked.",
            }

    def handler(request):
        body = json.loads(request.content)
        state = json.loads(body["messages"][1]["content"])["state"]
        assert state["tasks"] == []
        assert body["response_format"]["json_schema"]["name"] == "conversation_plan"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": json.dumps(proposal)},
                    }
                ]
            },
        )

    original_client = httpx.Client
    monkeypatch.setattr(
        "second_brain.muse.httpx.Client",
        lambda **kw: original_client(transport=httpx.MockTransport(handler), **kw),
    )
    muse.converse = Muse(
        Settings(_env_file=None, meta_api_key="test-secret", vercel=None)
    ).converse
    client = clients()
    run = converse(
        client,
        "Break my Duolingo take-home into bite-size steps: read the supplied brief "
        "and prepare the required submission.",
    ).json()
    assert run["status"] == "awaiting_review"
    assert run["proposal"] == proposal
    assert client.get("/api/dashboard").json()["tasks"] == []
    run["proposal"]["tasks"][0]["subtasks"][0]["title"] = "Read the brief I received"
    assert approve(client, run, proposal=run["proposal"]).status_code == 200
    saved = clients(cookies=client.cookies).get("/api/dashboard").json()
    parent = next(t for t in saved["tasks"] if t["parent_task_id"] is None)
    steps = sorted(
        (t for t in saved["tasks"] if t["parent_task_id"] == parent["id"]),
        key=lambda t: t["position"],
    )
    assert parent["title"] == "Complete Duolingo take-home"
    assert [t["title"] for t in steps] == [
        "Read the brief I received",
        "Prepare the required submission",
    ]
    assert all(t["deadline"] is None for t in saved["tasks"])
    assert all(t["status"] == "pending" for t in saved["tasks"])


def test_follow_up_replaces_pending_proposal_but_failure_preserves_it(setup):
    clients, muse, _ = setup
    fixture(muse)
    client = clients()
    first = converse(client).json()
    fixture(muse, [{**TASK, "title": "Math homework"}])
    second = converse(client, "It is math homework").json()
    assert muse.snapshot["recent_runs"][-1]["id"] == first["id"]
    assert muse.snapshot["recent_messages"][-1]["role"] == "assistant"
    assert approve(client, first).status_code == 409

    def fail(*_):
        raise MuseFailure("Unavailable")

    muse.converse = fail
    assert converse(client, "Make it shorter").json()["status"] == "failed"
    assert approve(client, second).status_code == 200


def test_clarifying_reply_creates_no_work(setup):
    clients, muse, _ = setup
    fixture(muse, [])
    client = clients()
    run = converse(client, "What can you do?").json()
    assert run["status"] == "answered"
    assert approve(client, run).status_code == 409
    assert client.get("/api/dashboard").json()["tasks"] == []


def test_conversation_retry_and_authentication(setup):
    clients, muse, _ = setup
    fixture(muse)
    client = clients()
    request_id = str(uuid4())
    first = converse(client, request_id=request_id).json()
    assert converse(client, request_id=request_id).json()["id"] == first["id"]
    assert muse.calls == 1
    assert converse(client, "Different", request_id).status_code == 409
    assert converse(clients(token="secret")).status_code == 401


def test_saved_correction_invalidates_pending_conversation(setup):
    clients, muse, _ = setup
    fixture(muse)
    client = clients()
    run = converse(client).json()
    client.post("/api/tasks", json={"title": "A correction"})
    assert approve(client, run).status_code == 409
    assert [t["title"] for t in client.get("/api/dashboard").json()["tasks"]] == [
        "A correction"
    ]


@pytest.mark.parametrize(
    "invalid", ["foreign_id", "duplicate_id", "user_score", "boolean_score", "bad_date"]
)
def test_invalid_conversation_never_mutates_work(setup, invalid):
    clients, muse, _ = setup
    client = clients()
    parent = client.post(
        "/api/tasks", json={"title": "Mine", "user_importance_level": "low"}
    ).json()
    foreign = clients("bob").post("/api/tasks", json={"title": "Private"}).json()
    item = {**TASK, "task_id": parent["id"], "importance_score": 30}
    if invalid == "foreign_id":
        item["task_id"] = foreign["id"]
    elif invalid == "user_score":
        item["importance_score"] = 70
    elif invalid == "boolean_score":
        item["importance_score"] = True
    elif invalid == "bad_date":
        item["deadline"] = "tomorrow"
    fixture(muse, [item, item] if invalid == "duplicate_id" else [item])
    assert converse(client).json()["status"] == "failed"
    assert client.get("/api/dashboard").json()["tasks"] == [parent]


def test_conversation_updates_saved_object_without_replacing_children(setup):
    clients, muse, _ = setup
    client = clients()
    parent = client.post(
        "/api/tasks", json={"title": "Homework", "user_importance_level": "high"}
    ).json()
    child = client.post(
        "/api/tasks", json={"title": "My step", "parent_task_id": parent["id"]}
    ).json()
    fixture(
        muse,
        [{**TASK, "task_id": parent["id"], "title": "Math homework", "subtasks": []}],
    )
    run = converse(client, "Rename homework to Math homework").json()
    assert approve(client, run).status_code == 200
    data = client.get("/api/dashboard").json()
    saved = next(t for t in data["tasks"] if t["id"] == parent["id"])
    assert saved["title"] == "Math homework"
    assert saved["user_importance_level"] == "high"
    assert saved["version"] == 2
    assert next(t for t in data["tasks"] if t["id"] == child["id"]) == child
    assert client.post(f"/api/runs/{run['id']}/approve", json={}).status_code == 409


def test_review_payload_cannot_bypass_ownership_validation(setup):
    clients, muse, _ = setup
    fixture(muse)
    client = clients()
    run = converse(client).json()
    foreign = clients("bob").post("/api/tasks", json={"title": "Private"}).json()
    run["proposal"]["tasks"][0]["task_id"] = foreign["id"]
    assert approve(client, run, proposal=run["proposal"]).status_code == 422
    assert client.get("/api/dashboard").json()["tasks"] == []


def test_unsaved_review_edits_are_shared_with_muse_and_bound_to_retry(setup):
    clients, muse, _ = setup
    fixture(muse)
    client = clients()
    first = converse(client).json()
    draft = first["proposal"]
    draft["tasks"][0]["title"] = "My corrected title"
    body = {
        "request_id": str(uuid4()),
        "message": "Make it shorter",
        "review_draft": draft,
    }
    assert client.post("/api/conversation", json=body).status_code == 200
    assert muse.snapshot["review_draft"]["tasks"][0]["title"] == "My corrected title"
    body["review_draft"]["tasks"][0]["title"] = "Another title"
    assert client.post("/api/conversation", json=body).status_code == 409


def test_older_response_cannot_supersede_a_newer_conversation_correction(setup):
    clients, muse, _ = setup
    client = clients()
    client.get("/")  # Establish the browser workspace before overlapping requests.
    newer = {}

    def old_response(snapshot, message):
        fixture(muse, [{**TASK, "title": "New correction"}])
        newer.update(converse(client, "My correction").json())
        return {"reply": "Old reply", "tasks": [TASK]}

    muse.converse = old_response
    old = converse(client).json()
    assert old["status"] == "stale"
    assert approve(client, old).status_code == 409
    assert approve(client, newer).status_code == 200
    roots = [
        t
        for t in client.get("/api/dashboard").json()["tasks"]
        if not t["parent_task_id"]
    ]
    assert [t["title"] for t in roots] == ["New correction"]
