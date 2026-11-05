"""Starter content must preserve ownership, user corrections and honest model state."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select

from second_brain.db import accounts, tasks
from second_brain.sample import BRIEF
from second_brain.service import handoff_available


def test_sample_workspace_persists_and_is_illustrative(setup):
    clients, muse, _ = setup
    client = clients(sample=True)
    state = client.get("/api/dashboard").json()
    roots = [t for t in state["tasks"] if not t["parent_task_id"]]
    assert len(roots) == 8
    assert len([t for t in roots if t["status"] != "completed"]) == 6
    assert {t["time_horizon"] for t in roots} == {"short_term", "long_term"}
    assert all(t["handoff_source"] == "sample" for t in state["tasks"])
    assert all(r["status"] == "sample" and r["proposal"] is None for r in state["runs"])
    assert all(m["role"] == "user" for m in state["messages"])
    assert muse.calls == 0
    assert client.get("/api/dashboard").json() == state
    eligible = next(
        t for t in roots if t["title"] == "Compare summer internship options"
    )
    mixed = next(t for t in roots if t["title"] == "Prepare the climate presentation")
    assert handoff_available(eligible, state["tasks"])
    assert not handoff_available(mixed, state["tasks"])

    changed = client.patch(
        "/api/tasks/" + eligible["id"],
        json={
            "title": "My corrected internship plan",
            "expected_version": eligible["version"],
        },
    )
    assert changed.status_code == 200
    returning = clients(sample=True, cookies=client.cookies)
    assert (
        next(
            t
            for t in returning.get("/api/dashboard").json()["tasks"]
            if t["id"] == eligible["id"]
        )["title"]
        == "My corrected internship plan"
    )


def test_sample_files_and_tasks_are_private_to_each_browser(setup):
    clients, _, _ = setup
    first, second = clients(sample=True), clients(sample=True)
    a = first.get("/api/dashboard").json()
    b = second.get("/api/dashboard").json()
    assert not {t["id"] for t in a["tasks"]} & {t["id"] for t in b["tasks"]}
    message = next(m for m in a["messages"] if m["attachments"])
    file = message["attachments"][0]
    path = "/api/attachments/" + file["id"]
    assert first.get(path).content.decode() == BRIEF
    assert second.get(path).status_code == 404
    assert "data" not in file
    run = next(r for r in a["runs"] if r["id"] == message["run_id"])
    assert run["chat_scope_id"] == next(
        t["id"] for t in a["tasks"] if t["title"] == "Prepare the climate presentation"
    )


def test_samples_never_refill_deleted_work_or_mix_with_existing_tasks(setup):
    clients, _, _ = setup
    client = clients(sample=True)
    state = client.get("/api/dashboard").json()
    from uuid import uuid4

    for task in [t for t in state["tasks"] if not t["parent_task_id"]]:
        assert (
            client.request(
                "DELETE",
                "/api/tasks/" + task["id"],
                json={
                    "request_id": str(uuid4()),
                    "expected_version": task["version"],
                },
            ).status_code
            == 200
        )
    assert client.get("/api/dashboard").json()["tasks"] == []
    existing = clients()
    saved = existing.post("/api/tasks", json={"title": "Keep my real work"}).json()
    enabled = clients(sample=True, cookies=existing.cookies)
    assert enabled.get("/api/dashboard").json()["tasks"] == [saved]


def test_parallel_first_loads_seed_once(setup):
    clients, _, _ = setup
    first = clients(sample=True)
    first.get("/")  # Establish the cookie before parallel dashboard requests.
    second = clients(sample=True, cookies=first.cookies)
    barrier = Barrier(2)

    def load(client):
        barrier.wait()
        return client.get("/api/dashboard").json()

    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = list(pool.map(load, [first, second]))
    assert a == b
    assert len([e for e in a["events"] if e["kind"] == "workspace.sample_loaded"]) == 1


def test_partial_seed_rolls_back_and_can_retry(setup, monkeypatch):
    from second_brain import service

    clients, _, engine = setup
    original = service.seed_workspace

    def fail_after_writes(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("Interrupted initialization")

    monkeypatch.setattr(service, "seed_workspace", fail_after_writes)
    client = clients(sample=True)
    with pytest.raises(RuntimeError, match="Interrupted initialization"):
        client.get("/api/dashboard")
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(tasks)) == 0
        assert connection.scalar(select(func.count()).select_from(accounts)) == 0
    monkeypatch.setattr(service, "seed_workspace", original)
    assert len(client.get("/api/dashboard").json()["tasks"]) > 0
