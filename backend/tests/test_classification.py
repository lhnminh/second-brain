"""Reviewable handoff recommendations are independent of execution state."""

from copy import deepcopy
from uuid import uuid4

import pytest

MUSE = {
    "handler": "muse",
    "reason": "Can produce a reviewable document on a computer.",
    "requirements": ["Project notes", "Document editor access"],
    "done_when": "An agenda draft with the requested topics is ready for review.",
}
USER = {
    "handler": "user",
    "reason": "Requires your personal choice.",
    "requirements": ["The agenda draft"],
    "done_when": "You have selected the topics to include.",
}


def proposal(task_id=None, handoff=USER):
    return {
        "reply": "Review the plan and suggested handlers.",
        "tasks": [
            {
                "task_id": task_id,
                "title": "Prepare the meeting",
                "description": "Use project notes",
                "deadline": None,
                "importance_score": 60,
                "handoff": deepcopy(handoff),
                "subtasks": [
                    {
                        "title": "Draft the agenda",
                        "description": "Use the supplied notes",
                        "importance_score": 60,
                        "handoff": deepcopy(MUSE),
                    },
                    {
                        "title": "Choose the discussion topics",
                        "description": "Make the final choice",
                        "importance_score": 60,
                        "handoff": deepcopy(USER),
                    },
                ],
            }
        ],
    }


def send(client, message="Plan the meeting"):
    return client.post(
        "/api/conversation", json={"request_id": str(uuid4()), "message": message}
    )


def test_classify_review_correct_save_and_reload(setup):
    clients, muse, _ = setup
    client = clients()
    muse.converse = lambda *_: proposal()
    run = send(client).json()
    assert run["status"] == "awaiting_review"
    assert run["proposal"]["tasks"][0]["subtasks"][0]["handoff"] == MUSE
    assert client.get("/api/dashboard").json()["tasks"] == []
    # A user changes the recommended owner before approving the plan.
    reviewed = run["proposal"]
    reviewed["tasks"][0]["subtasks"][1]["handoff"] = deepcopy(MUSE)
    approved = client.post(
        "/api/conversation/" + run["id"] + "/approve", json={"proposal": reviewed}
    )
    assert approved.status_code == 200
    saved = clients(cookies=client.cookies).get("/api/dashboard").json()
    parent = next(t for t in saved["tasks"] if not t["parent_task_id"])
    children = sorted(
        (t for t in saved["tasks"] if t["parent_task_id"]), key=lambda t: t["position"]
    )
    assert parent["handoff"] == USER
    assert children[0]["handoff"] == MUSE and children[0]["handoff_source"] == "model"
    assert children[1]["handoff"] == MUSE and children[1]["handoff_source"] == "user"
    assert all(t["status"] == "pending" for t in saved["tasks"])
    assert not any(event["kind"].startswith("execution.") for event in saved["events"])
    # Direct corrections persist and are passed to subsequent model requests.
    corrected = client.patch(
        "/api/tasks/" + children[0]["id"],
        json={
            "expected_version": children[0]["version"],
            "handoff": USER,
        },
    ).json()
    assert corrected["handoff"] == USER and corrected["handoff_source"] == "user"
    captured = {}

    def respond(snapshot, message):
        captured.update(snapshot)
        return {"reply": "Your choices are preserved.", "tasks": []}

    muse.converse = respond
    assert send(client).json()["status"] == "answered"
    assert (
        next(t for t in captured["tasks"] if t["id"] == corrected["id"])["handoff"]
        == USER
    )
    assert (
        clients("bob")
        .patch(
            "/api/tasks/" + corrected["id"],
            json={"expected_version": corrected["version"], "handoff": MUSE},
        )
        .status_code
        == 404
    )


def test_model_cannot_overwrite_direct_classification_correction(setup):
    clients, muse, _ = setup
    client = clients()
    task = client.post(
        "/api/tasks", json={"title": "Decide agenda topics", "handoff": USER}
    ).json()

    def response(*_):
        result = proposal(task["id"], MUSE)
        result["tasks"][0]["subtasks"] = []
        return result

    muse.converse = response
    assert send(client).json()["status"] == "failed"
    assert client.get("/api/dashboard").json()["tasks"][0] == task
    # Even clearing an assessment is an intentional choice.
    cleared = client.patch(
        "/api/tasks/" + task["id"],
        json={"expected_version": task["version"], "handoff": None},
    ).json()
    assert cleared["handoff"] is None and cleared["handoff_source"] == "user"
    assert send(client).json()["status"] == "failed"


def test_task_specific_breakdown_saves_classification(setup):
    clients, muse, _ = setup
    client = clients()
    task = client.post("/api/tasks", json={"title": "Prepare a meeting"}).json()
    muse.callback = lambda *_: {
        "reply": "Review",
        "importance_score": 60,
        "subtasks": proposal()["tasks"][0]["subtasks"],
    }
    run = client.post(
        "/api/tasks/" + task["id"] + "/plans",
        json={"request_id": str(uuid4()), "message": "Break it down"},
    ).json()
    assert run["status"] == "awaiting_review"
    assert (
        client.post("/api/runs/" + run["id"] + "/approve", json={}).status_code == 200
    )
    saved = client.get("/api/dashboard").json()["tasks"]
    assert next(t for t in saved if t["title"] == "Draft the agenda")["handoff"] == MUSE
    assert (
        next(t for t in saved if t["title"] == "Choose the discussion topics")[
            "handoff"
        ]
        == USER
    )
    assert next(t for t in saved if t["id"] == task["id"])["handoff"] is None


@pytest.mark.parametrize(
    "invalid",
    [
        {**MUSE, "handler": "either"},
        {**MUSE, "done_when": " "},
        {**MUSE, "requirements": [""]},
        {**MUSE, "requirements": ["x" * 501]},
        {**MUSE, "requirements": ["need"] * 11},
        {**MUSE, "reason": "x" * 1001},
        {**MUSE, "authorized": True},
    ],
)
def test_invalid_model_classification_preserves_tasks(setup, invalid):
    clients, muse, _ = setup
    client = clients()
    task = client.post("/api/tasks", json={"title": "Existing work"}).json()
    value = proposal()
    value["tasks"][0]["subtasks"][0]["handoff"] = invalid
    muse.converse = lambda *_: value
    assert send(client).json()["status"] == "failed"
    assert client.get("/api/dashboard").json()["tasks"] == [task]
    assert (
        client.patch(
            "/api/tasks/" + task["id"],
            json={"expected_version": task["version"], "handoff": invalid},
        ).status_code
        == 422
    )


def test_old_reviewable_proposals_and_unassessed_tasks_remain_compatible(setup):
    clients, muse, _ = setup
    client = clients()
    value = proposal()
    for item in (value["tasks"][0], *value["tasks"][0]["subtasks"]):
        item.pop("handoff")
    muse.converse = lambda *_: value
    run = send(client).json()
    assert (
        client.post("/api/conversation/" + run["id"] + "/approve", json={}).status_code
        == 200
    )
    assert all(
        t["handoff"] is None for t in client.get("/api/dashboard").json()["tasks"]
    )


def test_clearing_a_recommendation_during_review_is_a_user_choice(setup):
    clients, muse, _ = setup
    client = clients()
    muse.converse = lambda *_: proposal()
    run = send(client).json()
    reviewed = run["proposal"]
    reviewed["tasks"][0]["subtasks"][0]["handoff"] = None
    assert (
        client.post(
            "/api/conversation/" + run["id"] + "/approve", json={"proposal": reviewed}
        ).status_code
        == 200
    )
    task = next(
        t
        for t in client.get("/api/dashboard").json()["tasks"]
        if t["title"] == "Draft the agenda"
    )
    assert task["handoff"] is None and task["handoff_source"] == "user"
    # Review can also intentionally clear a saved recommendation.
    current = client.post("/api/tasks", json={"title": "Another task"}).json()

    def response(*_):
        result = proposal(current["id"], MUSE)
        result["tasks"][0]["subtasks"] = []
        return result

    muse.converse = response
    next_run = send(client).json()
    next_review = next_run["proposal"]
    next_review["tasks"][0]["handoff"] = None
    assert (
        client.post(
            "/api/conversation/" + next_run["id"] + "/approve",
            json={"proposal": next_review},
        ).status_code
        == 200
    )
    saved = next(
        t
        for t in client.get("/api/dashboard").json()["tasks"]
        if t["id"] == current["id"]
    )
    assert saved["handoff"] is None and saved["handoff_source"] == "user"
