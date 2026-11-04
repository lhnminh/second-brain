"""Owned execution state, cancellation and corrections, using explicit fake drivers."""

import base64
import json
import threading
import time
from typing import ClassVar
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from second_brain.api import create_app
from second_brain.browser_driver import BrowserActionError, BrowserDriver
from second_brain.browser_worker import BrowserWorker
from second_brain.config import Settings
from second_brain.db import browser_runs

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jC1kAAAAASUVORK5CYII="
)
HANDOFF = {
    "handler": "muse",
    "reason": "Browser research",
    "requirements": [],
    "done_when": "The result is visible",
}


class FakeDriver:
    instances: ClassVar[list] = []

    def __init__(self, directory):
        self.directory, self.downloads, self.blocked, self.actions = (
            directory,
            [],
            None,
            [],
        )
        self.closed = False
        self.instances.append(self)

    def __enter__(self):
        return self

    def open_url(self, url):
        self.url = url

    def screenshot(self):
        return PNG

    def perform(self, action):
        self.actions.append(action)

    def __exit__(self, *_):
        self.closed = True


class FakeModel:
    def __init__(self, *, hold=False, needs_input=False, fail=False):
        self.calls, self.history = 0, []
        self.entered, self.release = threading.Event(), threading.Event()
        self.hold, self.needs_input, self.fail = hold, needs_input, fail

    def turn(self, history):
        self.calls += 1
        self.history.append(history.copy())
        if self.calls == 1:
            self.entered.set()
            if self.hold:
                assert self.release.wait(5), "test did not release model"
            if self.fail:
                raise ValueError("simulated provider error; must not reach client")
            call = {
                "item": {"call_id": "one"},
                "actions": [{"type": "click", "x": 20, "y": 30, "button": "left"}],
                "checks": [{"message": "Please log in yourself"}]
                if self.needs_input
                else [],
            }
            return {
                "call": call,
                "output": [
                    {
                        "type": "function_call",
                        "call_id": "one",
                        "name": "browser_action",
                        "arguments": "{}",
                    }
                ],
                "text": "",
            }
        return {
            "call": None,
            "output": [],
            "text": "Observed the requested result. Review the screen.",
        }


def wait_for(client, run_id, statuses):
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        record = client.get("/api/browser/runs/" + run_id).json()
        if record.get("status") in statuses:
            return record
        time.sleep(0.01)
    raise AssertionError(record)


@pytest.fixture
def browser_app(setup, tmp_path):
    _, muse, engine = setup
    workers, models = [], []

    def build(model=None, enabled=True):
        model = model or FakeModel()
        settings = Settings(
            _env_file=None,
            database_url=str(engine.url),
            mock_auth_token=None,
            mock_user_id="browser-tests",
            meta_api_key="fake-test-key",
            browser_worker_enabled=enabled,
            browser_data_dir=tmp_path / "browser-data",
            vercel=None,
        )
        worker = BrowserWorker(engine, settings, model=model, driver_factory=FakeDriver)
        workers.append(worker)
        models.append(model)
        client = TestClient(
            create_app(settings, engine, muse, browser_worker=worker),
            base_url="http://127.0.0.1:8000",
            client=("127.0.0.1", 50100),
        )
        root = client.post(
            "/api/tasks", json={"title": "Research", "time_horizon": "short_term"}
        ).json()
        step = client.post(
            "/api/tasks",
            json={
                "title": "Read the example page",
                "parent_task_id": root["id"],
                "handoff": HANDOFF,
            },
        ).json()
        payload = {
            "request_id": str(uuid4()),
            "task_id": step["id"],
            "expected_version": step["version"],
            "start_url": "https://example.com/",
        }
        return client, worker, root, step, payload

    yield build
    for model in models:
        model.release.set()
    for worker in workers:
        worker.shutdown()


def test_browser_handoff_saves_real_states_without_completing_or_chatting(browser_app):
    client, worker, _, step, payload = browser_app()
    before = client.get("/api/dashboard").json()
    created = client.post("/api/browser/runs", json=payload)
    assert created.status_code == 202
    run_id = created.json()["id"]
    final = wait_for(client, run_id, {"finished"})
    assert final["frame"] >= 2 and final["steps"][0]["text"] == "Clicked on the page"
    assert FakeDriver.instances[-1].closed
    assert final["task_title"] == step["title"]
    assert (
        client.get(f"/api/browser/runs/{run_id}/frames/{final['frame']}").content == PNG
    )
    assert client.get(f"/api/browser/runs/{run_id}/frames/999").status_code == 404
    again = client.post("/api/browser/runs", json=payload).json()
    assert again["id"] == run_id and worker.model.calls == 2
    assert (
        client.post(
            "/api/browser/runs", json={**payload, "instructions": "different"}
        ).status_code
        == 409
    )
    after = client.get("/api/dashboard").json()
    assert after["messages"] == before["messages"]
    assert (
        next(t for t in after["tasks"] if t["id"] == step["id"])["status"] == "pending"
    )
    assert (
        client.post(
            f"/api/browser/runs/{run_id}/control", json={"action": "resume"}
        ).status_code
        == 409
    )
    assert client.get("/api/browser").json()["runs"][0]["id"] == run_id


@pytest.mark.parametrize("action", ["stop", "pause", "edit", "trash"])
def test_inflight_model_result_cannot_act_after_stop_pause_or_edit(browser_app, action):
    model = FakeModel(hold=True)
    client, _, _, step, payload = browser_app(model)
    run_id = client.post("/api/browser/runs", json=payload).json()["id"]
    assert model.entered.wait(3)
    if action == "trash":
        assert (
            client.request(
                "DELETE",
                "/api/tasks/" + step["id"],
                json={"request_id": str(uuid4()), "expected_version": step["version"]},
            ).status_code
            == 200
        )
    elif action == "edit":
        assert (
            client.patch(
                "/api/tasks/" + step["id"],
                json={"expected_version": 1, "title": "My corrected goal"},
            ).status_code
            == 200
        )
    else:
        assert (
            client.post(
                f"/api/browser/runs/{run_id}/control", json={"action": action}
            ).status_code
            == 200
        )
    model.release.set()
    status = {
        "stop": "stopped",
        "pause": "paused",
        "edit": "interrupted",
        "trash": "interrupted",
    }[action]
    wait_for(client, run_id, {status})
    assert FakeDriver.instances[-1].actions == []
    if action == "pause":
        assert (
            client.post(
                f"/api/browser/runs/{run_id}/control", json={"action": "resume"}
            ).status_code
            == 200
        )
        wait_for(client, run_id, {"finished"})
        assert len(model.history[1]) == 1  # fresh screen, no stale action replay


def test_human_input_pauses_without_running_the_action(browser_app):
    client, _, _, _, payload = browser_app(FakeModel(needs_input=True))
    run_id = client.post("/api/browser/runs", json=payload).json()["id"]
    result = wait_for(client, run_id, {"needs_input"})
    assert "log in" in result["summary"]
    assert FakeDriver.instances[-1].actions == []
    assert (
        client.post(
            f"/api/browser/runs/{run_id}/control", json={"action": "resume"}
        ).status_code
        == 200
    )
    wait_for(client, run_id, {"finished"})


def test_provider_failure_and_restart_preserve_tasks(browser_app):
    client, worker, _, _, payload = browser_app(FakeModel(fail=True))
    run_id = client.post("/api/browser/runs", json=payload).json()["id"]
    final = wait_for(client, run_id, {"failed"})
    assert (
        "simulated provider" not in final["summary"] and FakeDriver.instances[-1].closed
    )
    with worker.engine.begin() as c:
        c.execute(
            update(browser_runs)
            .where(browser_runs.c.id == run_id)
            .values(status="running")
        )
    BrowserWorker(
        worker.engine, worker.settings, model=FakeModel(), driver_factory=FakeDriver
    )
    assert client.get("/api/browser/runs/" + run_id).json()["status"] == "interrupted"


def test_ownership_capacity_version_and_laptop_gates(browser_app):
    model = FakeModel(hold=True)
    client, worker, _root, _step, payload = browser_app(model)
    for changes, status in [
        ({"expected_version": 99}, 409),
        ({"start_url": "file:///private"}, 422),
        ({"start_url": "http://127.0.0.1/"}, 422),
    ]:
        assert (
            client.post("/api/browser/runs", json={**payload, **changes}).status_code
            == status
        )
    assert (
        client.post(
            "/api/browser/runs",
            json=payload,
            headers={"Origin": "https://evil.example"},
        ).status_code
        == 403
    )
    run_id = client.post("/api/browser/runs", json=payload).json()["id"]
    assert model.entered.wait(3)
    assert (
        client.post(
            "/api/browser/runs", json={**payload, "request_id": str(uuid4())}
        ).status_code
        == 409
    )
    other = TestClient(
        client.app, base_url="http://127.0.0.1:8000", client=("127.0.0.1", 50101)
    )
    assert other.get("/api/browser").json()["runs"] == []
    for suffix in ["", "/frames/1", "/downloads/" + str(uuid4())]:
        assert other.get("/api/browser/runs/" + run_id + suffix).status_code == 404
    assert (
        other.post(
            f"/api/browser/runs/{run_id}/control", json={"action": "stop"}
        ).status_code
        == 404
    )
    assert other.post("/api/browser/runs", json=payload).status_code == 404
    remote = TestClient(
        client.app, base_url="http://192.168.1.1:8000", client=("192.168.1.2", 50100)
    )
    assert remote.get("/api/browser").status_code == 403
    assert remote.post("/api/browser/runs", json=payload).status_code == 403
    model.release.set()
    wait_for(client, run_id, {"finished"})
    with worker.engine.connect() as c:
        assert len(c.execute(select(browser_runs)).all()) == 1


def test_disabled_worker_does_not_start_work(browser_app):
    client, worker, _, _, payload = browser_app(enabled=False)
    assert client.get("/api/browser").json()["connected"] is False
    assert client.post("/api/browser/runs", json=payload).status_code == 503
    assert worker.model.calls == 0


def test_whole_task_browser_is_explicit_and_watches_its_subtasks(browser_app):
    model = FakeModel(hold=True)
    client, _worker, root, step, payload = browser_app(model)
    payload.update(task_id=root["id"], expected_version=root["version"])
    response = client.post("/api/browser/runs", json=payload)
    assert response.status_code == 202
    run_id = response.json()["id"]
    assert model.entered.wait(3)
    goal = json.loads(model.history[0][0]["content"][0]["text"].split("\n")[0])
    assert goal["subtasks"][0]["id"] == step["id"]
    assert (
        client.post(
            "/api/tasks",
            json={"title": "New requirement", "parent_task_id": root["id"]},
        ).status_code
        == 201
    )
    model.release.set()
    wait_for(client, run_id, {"interrupted"})
    assert FakeDriver.instances[-1].actions == []


def test_downloads_are_saved_under_opaque_owned_paths(browser_app):
    class Download:
        suggested_filename = "../../result.txt"

        def save_as(self, path):
            path.write_text("Synthetic download result", encoding="utf-8")

    class DownloadDriver(FakeDriver):
        def perform(self, action):
            self.directory.mkdir(parents=True, exist_ok=True)
            BrowserDriver._download(self, Download())
            super().perform(action)

    client, worker, _, _, payload = browser_app()
    worker.driver_factory = DownloadDriver
    run_id = client.post("/api/browser/runs", json=payload).json()["id"]
    run = wait_for(client, run_id, {"finished"})
    download = run["downloads"][0]
    assert download["name"] == "result.txt" and download["id"] != download["name"]
    response = client.get(f"/api/browser/runs/{run_id}/downloads/{download['id']}")
    assert response.text == "Synthetic download result"
    assert "attachment" in response.headers["content-disposition"]
    assert response.headers["cache-control"] == "no-store"


def test_safe_action_rejection_returns_feedback_without_executing(browser_app):
    class GuardedDriver(FakeDriver):
        def perform(self, action):
            raise BrowserActionError(
                "This keyboard shortcut is unavailable in the dedicated browser"
            )

    client, worker, _, _, payload = browser_app()
    worker.driver_factory = GuardedDriver
    run_id = client.post("/api/browser/runs", json=payload).json()["id"]
    run = wait_for(client, run_id, {"finished"})
    assert run["steps"][0]["text"].startswith("Blocked action:")
    assert FakeDriver.instances[-1].actions == []
    outputs = [
        item
        for item in worker.model.history[1]
        if item.get("type") == "function_call_output"
    ]
    assert "blocked without execution" in outputs[-1]["output"]


@pytest.mark.parametrize("change", ["human", "completed", "completed-parent"])
def test_unsuitable_or_finished_work_cannot_start(browser_app, change):
    client, worker, root, step, payload = browser_app()
    target = root if change == "completed-parent" else step
    edits = (
        {"handoff": {**HANDOFF, "handler": "user"}}
        if change == "human"
        else {"status": "completed"}
    )
    saved = client.patch(
        "/api/tasks/" + target["id"],
        json={"expected_version": target["version"], **edits},
    ).json()
    if target == step:
        payload["expected_version"] = saved["version"]
    assert client.post("/api/browser/runs", json=payload).status_code == 409
    assert worker.model.calls == 0


@pytest.mark.parametrize("change", ["long-term", "mixed-whole"])
def test_new_browser_runs_obey_focus_and_whole_task_eligibility(browser_app, change):
    client, worker, root, _step, payload = browser_app()
    if change == "long-term":
        client.patch(
            "/api/tasks/" + root["id"],
            json={"expected_version": root["version"], "time_horizon": "long_term"},
        )
    else:
        client.post(
            "/api/tasks",
            json={
                "title": "Physical step",
                "parent_task_id": root["id"],
                "handoff": {**HANDOFF, "handler": "user"},
            },
        )
        payload.update(task_id=root["id"], expected_version=root["version"])
    assert client.post("/api/browser/runs", json=payload).status_code == 409
    assert worker.model.calls == 0
