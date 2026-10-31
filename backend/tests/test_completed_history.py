"""A completed commitment must not suppress new work with a similar title."""

from copy import deepcopy
from uuid import uuid4

import pytest

from second_brain.service import planning_tasks

HANDOFF = {
    "handler": "user",
    "reason": "The user owns this assessment.",
    "requirements": ["Current assessment brief"],
    "done_when": "The current assessment requirements have been completed.",
}


def send(client, message, chat=None):
    return client.post(
        "/api/conversation",
        json={
            "request_id": str(uuid4()),
            "message": message,
            "conversation_id": chat,
            "apply_immediately": True,
        },
    )


def new_assessment():
    return {
        "reply": "Here is your new assessment task. What is the exact due date?",
        "tasks": [
            {
                "task_id": None,
                "title": "Duolingo Takehome assessment",
                "description": "Current assessment due next week; exact date and brief needed.",
                "deadline": None,
                "importance_score": 70,
                "handoff": deepcopy(HANDOFF),
                "subtasks": [],
            }
        ],
    }


def seed_finished(client, finish_parent):
    parent = client.post(
        "/api/tasks",
        json={
            "title": "Duolingo Takehome assessment",
            "description": "Earlier assessment, already finished.",
            "deadline": "2026-10-01",
        },
    ).json()
    child = client.post(
        "/api/tasks",
        json={"title": "Complete the old brief", "parent_task_id": parent["id"]},
    ).json()
    record = parent if finish_parent else child
    saved = client.patch(
        "/api/tasks/" + record["id"],
        json={"expected_version": record["version"], "status": "completed"},
    ).json()
    return (saved, child) if finish_parent else (parent, saved)


@pytest.mark.parametrize("finish_parent", [True, False])
def test_finished_assessment_is_history_and_new_assessment_is_saved(
    setup, finish_parent
):
    clients, muse, _ = setup
    client = clients()
    old_parent, old_child = seed_finished(client, finish_parent)

    def respond(snapshot, message):
        assert snapshot["tasks"] == []
        history = {task["id"]: task for task in snapshot["completed_tasks"]}
        assert set(history) == {old_parent["id"], old_child["id"]}
        assert history[old_parent["id"]]["completion_reason"] == (
            "completed" if finish_parent else "all_steps_completed"
        )
        return new_assessment()

    muse.converse = respond
    run = send(
        client, "I have a Duolingo Takehome assessment need to be done by next week."
    ).json()
    assert run["status"] == "applied"
    saved = client.get("/api/dashboard").json()["tasks"]
    assert old_parent in saved and old_child in saved
    new = next(
        task for task in saved if task["id"] not in {old_parent["id"], old_child["id"]}
    )
    assert new["status"] == "pending" and new["parent_task_id"] is None
    assert new["title"] == old_parent["title"] and new["deadline"] is None
    assert new["description"] != old_parent["description"]
    returned = clients(cookies=client.cookies).get("/api/dashboard").json()["tasks"]
    assert new in returned and old_parent in returned

    # Later corrections use the new active task, rather than the old matching title.
    def correct(snapshot, message):
        assert [task["id"] for task in snapshot["tasks"]] == [new["id"]]
        result = new_assessment()
        result["tasks"][0].update(task_id=new["id"], title="New Duolingo assessment")
        return result

    muse.converse = correct
    assert (
        send(client, "Call the new one New Duolingo assessment").json()["status"]
        == "applied"
    )
    saved = client.get("/api/dashboard").json()["tasks"]
    assert len(saved) == 3 and old_parent in saved
    assert (
        next(task for task in saved if task["id"] == new["id"])["title"]
        == "New Duolingo assessment"
    )


def test_completed_steps_do_not_hide_a_plan_with_unfinished_work():
    tasks = [
        {"id": "plan", "parent_task_id": None, "status": "pending"},
        {"id": "done", "parent_task_id": "plan", "status": "completed"},
        {"id": "todo", "parent_task_id": "plan", "status": "pending"},
        {"id": "other", "parent_task_id": None, "status": "in_progress"},
    ]
    original = deepcopy(tasks)
    active, history = planning_tasks(tasks)
    assert {task["id"] for task in active} == {"plan", "todo", "other"}
    assert [task["id"] for task in history] == ["done"]
    assert tasks == original


def test_nested_finished_leaves_and_completed_parent_are_history():
    tasks = [
        {"id": "plan", "parent_task_id": None, "status": "pending"},
        {"id": "step", "parent_task_id": "plan", "status": "pending"},
        {"id": "leaf", "parent_task_id": "step", "status": "completed"},
        {"id": "closed", "parent_task_id": None, "status": "completed"},
        {"id": "leftover", "parent_task_id": "closed", "status": "pending"},
    ]
    active, history = planning_tasks(tasks)
    assert active == [] and len(history) == 5
    assert (
        next(task for task in history if task["id"] == "leftover")["completion_reason"]
        == "completed_parent"
    )
    assert tasks[0]["status"] == "pending"


def test_old_chat_creation_reply_is_not_current_work(setup):
    clients, muse, _ = setup
    client = clients()
    chat = str(uuid4())
    muse.converse = lambda *_: new_assessment()
    assert send(client, "Create an assessment task", chat).json()["status"] == "applied"
    old = client.get("/api/dashboard").json()["tasks"][0]
    client.patch(
        "/api/tasks/" + old["id"],
        json={"expected_version": old["version"], "status": "completed"},
    )

    def respond(snapshot, message):
        assert snapshot["tasks"] == []
        assert snapshot["completed_tasks"][0]["id"] == old["id"]
        assert snapshot["recent_messages"] and snapshot["recent_runs"]
        return new_assessment()

    muse.converse = respond
    assert (
        send(client, "I have another assessment to do next week", chat).json()["status"]
        == "applied"
    )
    assert len(client.get("/api/dashboard").json()["tasks"]) == 2


def test_model_cannot_add_invisible_steps_to_finished_history(setup):
    clients, muse, _ = setup
    client = clients()
    old, _ = seed_finished(client, False)

    def respond(*_):
        result = new_assessment()
        result["tasks"][0].update(
            task_id=old["id"],
            subtasks=[
                {
                    "title": "New assessment step",
                    "description": "This belongs to new work",
                    "importance_score": 60,
                    "handoff": HANDOFF,
                }
            ],
        )
        return result

    muse.converse = respond
    before = client.get("/api/dashboard").json()["tasks"]
    assert send(client, "I have a new assessment").json()["status"] == "failed"
    assert client.get("/api/dashboard").json()["tasks"] == before


def test_history_remains_addressable_for_explicit_corrections(setup):
    clients, muse, _ = setup
    client = clients()
    old, child = seed_finished(client, True)

    def respond(snapshot, message):
        assert snapshot["tasks"] == []
        result = new_assessment()
        result["tasks"][0].update(
            task_id=old["id"], title="Archived assessment from October"
        )
        return result

    muse.converse = respond
    assert (
        send(
            client,
            "Rename the finished historical record to Archived assessment from October",
        ).json()["status"]
        == "applied"
    )
    saved = client.get("/api/dashboard").json()["tasks"]
    assert len(saved) == 2 and child in saved
    assert (
        next(task for task in saved if task["id"] == old["id"])["status"] == "completed"
    )
