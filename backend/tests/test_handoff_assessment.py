from copy import deepcopy
from uuid import uuid4

import pytest

from second_brain.muse import MuseFailure


def make_steps(client):
    root = client.post(
        "/api/tasks",
        json={
            "title": "Prepare the workshop",
            "time_horizon": "short_term",
            "subtasks": [{"title": "Draft an agenda"}, {"title": "Arrange the chairs"}],
        },
    ).json()
    return root, root.pop("subtasks")


def assessment(snapshot):
    return {
        "tasks": [
            {
                "task_id": task["id"],
                "handoff": {
                    "handler": "user" if "chairs" in task["title"] else "muse",
                    "reason": "Physical action"
                    if "chairs" in task["title"]
                    else "Computer document work",
                    "requirements": [],
                    "done_when": task["title"],
                },
            }
            for task in snapshot["tasks"]
        ]
    }


def request(steps):
    return {"request_id": str(uuid4()), "task_ids": [task["id"] for task in steps]}


def test_saved_steps_get_model_assessments_without_chat_or_execution_and_retry_is_safe(
    setup,
):
    clients, muse, _ = setup
    client = clients()
    root, steps = make_steps(client)
    calls = []
    muse.assess_handoff = lambda snapshot: (
        calls.append(deepcopy(snapshot)) or assessment(snapshot)
    )
    body = request(steps)
    result = client.post("/api/handoff/assess", json=body).json()
    assert result["status"] == "answered"
    assert [task["handoff"]["handler"] for task in result["tasks"]] == ["muse", "user"]
    assert all(
        task["handoff_source"] == "model" and task["status"] == "pending"
        for task in result["tasks"]
    )
    assert [task["title"] for task in result["tasks"]] == [
        task["title"] for task in steps
    ]
    assert calls[0]["parent"]["id"] == root["id"]
    assert client.post("/api/handoff/assess", json=body).json()["id"] == result["id"]
    assert len(calls) == 1
    data = client.get("/api/dashboard").json()
    assert data["messages"] == []
    assert data["runs"][0]["input_payload"]["operation"] == "handoff_assessment"
    assert data["runs"][0]["task_id"] == root["id"]
    assert len(data["tasks"]) == 3 and all(
        task["status"] == "pending" for task in data["tasks"]
    )
    assert (
        client.post(
            "/api/handoff/assess", json={**body, "task_ids": [steps[0]["id"]]}
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    "mode",
    [
        "provider_failure",
        "wrong_ids",
        "duplicate_ids",
        "missing_assessment",
        "stale_child",
        "stale_parent",
    ],
)
def test_failed_or_stale_assessment_preserves_saved_work(setup, mode):
    clients, muse, _ = setup
    client = clients()
    root, steps = make_steps(client)

    def respond(snapshot):
        if mode == "provider_failure":
            raise MuseFailure("Fixture provider failure")
        value = assessment(snapshot)
        if mode == "wrong_ids":
            value["tasks"][0]["task_id"] = str(uuid4())
        if mode == "duplicate_ids":
            value["tasks"][1]["task_id"] = value["tasks"][0]["task_id"]
        if mode == "missing_assessment":
            value["tasks"][0]["handoff"] = None
        if mode.startswith("stale_"):
            target = root if mode == "stale_parent" else steps[0]
            assert (
                client.patch(
                    "/api/tasks/" + target["id"],
                    json={
                        "expected_version": target["version"],
                        "title": "My correction",
                    },
                ).status_code
                == 200
            )
        return value

    muse.assess_handoff = respond
    result = client.post("/api/handoff/assess", json=request(steps)).json()
    assert result["status"] == ("stale" if mode.startswith("stale_") else "failed")
    data = client.get("/api/dashboard").json()
    assert len(data["tasks"]) == 3 and data["messages"] == []
    assert all(task["handoff"] is None for task in data["tasks"])
    if mode.startswith("stale_"):
        assert any(task["title"] == "My correction" for task in data["tasks"])


def test_assessment_rejects_foreign_roots_duplicate_requests_and_user_overrides(setup):
    clients, muse, _ = setup
    first, second = clients(), clients()
    root, steps = make_steps(first)
    muse.assess_handoff = lambda snapshot: pytest.fail(
        "Invalid assessment must not call Muse"
    )
    assert second.post("/api/handoff/assess", json=request(steps)).status_code == 404
    assert first.post("/api/handoff/assess", json=request([root])).status_code == 422
    assert (
        first.post(
            "/api/handoff/assess", json=request([steps[0], steps[0]])
        ).status_code
        == 422
    )
    assert (
        first.patch(
            "/api/tasks/" + steps[0]["id"],
            json={
                "expected_version": steps[0]["version"],
                "handoff": assessment({"tasks": [steps[0]]})["tasks"][0]["handoff"],
            },
        ).status_code
        == 200
    )
    assert first.post("/api/handoff/assess", json=request(steps)).status_code == 409
