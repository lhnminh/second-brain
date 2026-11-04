"""Opt-in, single-process local browser execution with owned persistent results."""

import base64
import importlib.util
import json
import logging
import threading
import time
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import insert, select, update

from .browser_driver import (
    BrowserActionError,
    BrowserDriver,
    describe_action,
    public_url,
)
from .browser_model import BrowserMuse
from .db import browser_runs, now, tasks, uid
from .service import audit, handoff_available, lock_account, owned

ACTIVE = {"queued", "running", "pausing", "paused", "needs_input", "stopping"}


class RunStopped(Exception):
    pass


class TaskChanged(Exception):
    pass


def image_input(png):
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


class BrowserWorker:
    def __init__(self, engine, settings, *, model=None, driver_factory=None):
        self.engine, self.settings = engine, settings
        self.model = model or BrowserMuse(settings)
        self.driver_factory = driver_factory or BrowserDriver
        self.directory = Path(settings.browser_data_dir)
        self.lock = threading.RLock()
        self.live = {}
        self.enabled = settings.browser_worker_enabled and not settings.vercel
        self.available = self.enabled and (
            driver_factory is not None
            or importlib.util.find_spec("playwright") is not None
        )
        if self.enabled:
            # A browser cannot survive its worker process. Never resume old actions blindly.
            with engine.begin() as c:
                c.execute(
                    update(browser_runs)
                    .where(browser_runs.c.status.in_(ACTIVE))
                    .values(
                        status="interrupted",
                        summary="The local worker restarted. Start a new handoff to continue.",
                        updated_at=now(),
                    )
                )

    def readiness(self):
        if not self.enabled:
            reason = "Start the local app with uv run --extra browser second-brain-browser to connect a dedicated browser. Hosted laptop connections are not available yet."
        elif not self.available:
            reason = "Install the browser extra and Chromium: uv sync --extra browser; uv run playwright install chromium."
        elif not self.settings.meta_api_key:
            reason = (
                "Add META_API_KEY to the local .env and restart the browser worker."
            )
        else:
            reason = "A separate browser will open on this laptop. Its page screenshots are sent to Meta during the run."
        return {
            "connected": bool(self.available and self.settings.meta_api_key),
            "mode": "local_browser",
            "reason": reason,
        }

    def listing(self, owner):
        with self.engine.connect() as c:
            records = [
                dict(r)
                for r in c.execute(
                    select(browser_runs)
                    .where(browser_runs.c.user_id == owner)
                    .order_by(browser_runs.c.created_at.desc())
                    .limit(30)
                ).mappings()
            ]
        return {**self.readiness(), "runs": [self.public(r) for r in records]}

    @staticmethod
    def public(record):
        result = {
            key: record[key]
            for key in (
                "id",
                "task_id",
                "request_id",
                "start_url",
                "status",
                "summary",
                "steps",
                "downloads",
                "frame",
                "created_at",
                "updated_at",
            )
        }
        goal = record["goal"]
        goal = json.loads(goal) if isinstance(goal, str) else goal
        result["task_title"] = goal["subtask"]["title"]
        return result

    def get(self, owner, run_id):
        with self.engine.connect() as c:
            return self.public(owned(c, browser_runs, run_id, owner))

    def start(self, owner, body):
        if not self.readiness()["connected"]:
            raise HTTPException(503, self.readiness()["reason"])
        payload = body.model_dump(mode="json")
        with self.lock, self.engine.begin() as c:
            lock_account(c, owner)
            previous = (
                c.execute(
                    select(browser_runs).where(
                        browser_runs.c.user_id == owner,
                        browser_runs.c.request_id == str(body.request_id),
                    )
                )
                .mappings()
                .first()
            )
            if previous:
                previous = dict(previous)
                saved_goal = previous["goal"]
                if isinstance(saved_goal, str):
                    saved_goal = json.loads(saved_goal)
                saved_request = saved_goal["request"]
                if saved_request != payload:
                    raise HTTPException(
                        409, "request_id was used for a different handoff"
                    )
                return self.public(previous)
            task = owned(c, tasks, str(body.task_id), owner)
            if task["version"] != body.expected_version:
                raise HTTPException(
                    409, "The subtask changed; refresh before handing it off"
                )
            if task["status"] == "completed" or (
                task["parent_task_id"]
                and (task["handoff"] is None or task["handoff"]["handler"] != "muse")
            ):
                raise HTTPException(
                    409, "This subtask is not available for Muse handoff"
                )
            saved = [
                dict(t)
                for t in c.execute(
                    select(tasks).where(
                        tasks.c.user_id == owner, tasks.c.deleted_at.is_(None)
                    )
                ).mappings()
            ]
            if not handoff_available(task, saved):
                raise HTTPException(
                    409,
                    "Handoff requires short-term work with all subtasks suitable for Muse",
                )
            scope_ids = {task["id"]}
            while True:
                children = {t["id"] for t in saved if t["parent_task_id"] in scope_ids}
                if children <= scope_ids:
                    break
                scope_ids |= children
            descendants = [
                t for t in saved if t["id"] in scope_ids and t["id"] != task["id"]
            ]
            ancestors, current = [], task
            while current["parent_task_id"]:
                current = owned(c, tasks, current["parent_task_id"], owner)
                if current["status"] == "completed":
                    raise HTTPException(
                        409, "Reopen the parent task before handing off work"
                    )
                ancestors.append(current)
            if self.live:
                raise HTTPException(
                    409,
                    "The dedicated browser is already in use. Finish or stop its current run first.",
                )
            try:
                public_url(body.start_url, resolve=False)
            except ValueError as exc:
                raise HTTPException(422, str(exc)) from None
            goal = {
                "request": payload,
                "subtask": {
                    key: task[key] for key in ("title", "description", "handoff")
                },
                "parent_task": ancestors[0]["title"] if ancestors else None,
                "subtasks": [
                    {key: t[key] for key in ("id", "title", "status", "handoff")}
                    for t in descendants
                ],
                "instructions": body.instructions,
            }
            stamp, run_id = now(), uid()
            record = {
                "id": run_id,
                "user_id": owner,
                "task_id": task["id"],
                "request_id": str(body.request_id),
                "task_version": task["version"],
                "goal": goal,
                "start_url": body.start_url,
                "status": "queued",
                "summary": "Waiting for the dedicated browser to open.",
                "steps": [],
                "downloads": [],
                "frame": 0,
                "created_at": stamp,
                "updated_at": stamp,
            }
            c.execute(insert(browser_runs).values(**record))
            audit(c, owner, "browser.queued", run_id, {"task_id": task["id"]})
            control = {
                "stop": threading.Event(),
                "pause": threading.Event(),
                "thread": None,
            }
            self.live[run_id] = control
        thread = threading.Thread(
            target=self._run,
            args=(
                record,
                control,
                [(t["id"], t["version"]) for t in [task, *ancestors, *descendants]],
            ),
            daemon=True,
            name="muse-browser",
        )
        control["thread"] = thread
        try:
            thread.start()
        except RuntimeError:
            with self.lock:
                self.live.pop(run_id, None)
            self._save(
                run_id,
                status="failed",
                summary="The local browser worker could not start. Retry with a new handoff.",
            )
            raise HTTPException(503, "The browser worker could not start") from None
        return self.public(record)

    def _save(self, run_id, **changes):
        with self.lock, self.engine.begin() as c:
            c.execute(
                update(browser_runs)
                .where(browser_runs.c.id == run_id)
                .values(**changes, updated_at=now())
            )

    def control(self, owner, run_id, action):
        with self.lock:
            record = self.get(owner, run_id)
            live = self.live.get(run_id)
            if record["status"] not in ACTIVE or not live:
                raise HTTPException(409, "This browser run has ended")
            if action == "stop":
                live["stop"].set()
                self._save(
                    run_id,
                    status="stopping",
                    summary="Stopping; any in-flight model request will be discarded before further actions.",
                )
            elif action == "pause":
                live["pause"].set()
                self._save(
                    run_id,
                    status="pausing",
                    summary="Pausing before the next browser action. Wait for Paused before taking over.",
                )
            elif action == "resume":
                if record["status"] not in {"paused", "needs_input"}:
                    raise HTTPException(
                        409, "Wait until the browser is paused before resuming"
                    )
                live["pause"].clear()
                self._save(
                    run_id,
                    status="running",
                    summary="Resuming from a fresh screenshot.",
                )
            return self.get(owner, run_id)

    def _check_tasks(self, owner, versions):
        with self.engine.connect() as c:
            try:
                if any(
                    owned(c, tasks, task_id, owner)["version"] != version
                    for task_id, version in versions
                ):
                    raise TaskChanged
            except HTTPException:
                raise TaskChanged from None
            # Appending new steps also changes the delegated scope, even if its title is unchanged.
            saved = c.execute(
                select(tasks.c.id, tasks.c.parent_task_id).where(
                    tasks.c.user_id == owner, tasks.c.deleted_at.is_(None)
                )
            ).all()
            ids = {versions[0][0]}
            while True:
                children = {t.id for t in saved if t.parent_task_id in ids}
                if children <= ids:
                    break
                ids |= children
            if not ids <= {task_id for task_id, _ in versions}:
                raise TaskChanged

    def _checkpoint(self, run_id, control):
        if control["stop"].is_set():
            raise RunStopped
        resumed = control["pause"].is_set()
        if resumed:
            with self.lock:
                status = self.get_status(run_id)
                if status != "needs_input":
                    self._save(
                        run_id,
                        status="paused",
                        summary="Paused. You can use the dedicated browser now; Resume observes the page again.",
                    )
            while control["pause"].is_set():
                if control["stop"].wait(0.2):
                    raise RunStopped
        if control["stop"].is_set():
            raise RunStopped
        return resumed

    def get_status(self, run_id):
        with self.engine.connect() as c:
            return c.scalar(
                select(browser_runs.c.status).where(browser_runs.c.id == run_id)
            )

    def _capture(self, record, driver, steps):
        png = driver.screenshot()
        record["frame"] += 1
        path = self.directory / record["id"] / f"frame-{record['frame']}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(png)
        self._save(
            record["id"],
            frame=record["frame"],
            steps=steps[-100:],
            downloads=driver.downloads,
        )
        return png

    def _history(self, record, png, note=""):
        goal = record["goal"]
        goal = json.loads(goal) if isinstance(goal, str) else dict(goal)
        goal.pop("request")
        return [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": json.dumps(goal) + "\n" + note},
                    {"type": "input_image", "image_url": image_input(png)},
                ],
            }
        ]

    def _run(self, record, control, versions):
        run_id, owner, steps = record["id"], record["user_id"], []
        deadline = time.monotonic() + 600
        try:
            self._checkpoint(run_id, control)
            self._check_tasks(owner, versions)
            with self.driver_factory(self.directory / run_id) as driver:
                self._save(
                    run_id, status="running", summary="Dedicated browser opened."
                )
                self._checkpoint(run_id, control)
                driver.open_url(record["start_url"])
                history = self._history(record, self._capture(record, driver, steps))
                for turn in range(20):
                    resumed = self._checkpoint(run_id, control)
                    self._check_tasks(owner, versions)
                    if time.monotonic() > deadline:
                        raise TimeoutError
                    if resumed:
                        history = self._history(
                            record,
                            self._capture(record, driver, steps),
                            "The user took over and resumed. Re-evaluate the current page; do not repeat earlier actions blindly.",
                        )
                    self._save(
                        run_id,
                        summary=f"Muse is looking at the page (step {turn + 1} of 20).",
                    )
                    result = self.model.turn(history)
                    if self._checkpoint(run_id, control):
                        history = self._history(
                            record,
                            self._capture(record, driver, steps),
                            "The user paused during thinking. Re-evaluate this new screenshot.",
                        )
                        continue
                    self._check_tasks(owner, versions)
                    call = result["call"]
                    if not call:
                        self._capture(record, driver, steps)
                        self._save(
                            run_id,
                            status="finished",
                            summary=result["text"]
                            or "The run ended. Review the browser result before completing the subtask.",
                        )
                        return
                    if call["checks"]:
                        control["pause"].set()
                        self._save(
                            run_id,
                            status="needs_input",
                            summary="Muse needs your help. Use the dedicated browser to provide what is missing, then Resume. No requested human action has run automatically.\n"
                            + "\n".join(c["message"] for c in call["checks"])[:2000],
                        )
                        self._checkpoint(run_id, control)
                        history = self._history(
                            record,
                            self._capture(record, driver, steps),
                            "The agent requested human input. The user took over and resumed; observe the current state. Do not assume permission for sensitive actions.",
                        )
                        continue
                    history.extend(result["output"])
                    interrupted = False
                    action_error = None
                    try:
                        if "url" in call:
                            driver.open_url(call["url"])
                            steps.append({"text": "Opened a website", "at": now()})
                        else:
                            for action in call["actions"]:
                                if self._checkpoint(run_id, control):
                                    interrupted = True
                                    break
                                self._check_tasks(owner, versions)
                                driver.perform(action)
                                steps.append(
                                    {"text": describe_action(action), "at": now()}
                                )
                                if driver.blocked:
                                    interrupted = True
                                    break
                    except BrowserActionError as exc:
                        action_error = str(exc)
                        steps.append(
                            {"text": "Blocked action: " + action_error, "at": now()}
                        )
                    png = self._capture(record, driver, steps)
                    if driver.blocked:
                        control["pause"].set()
                        self._save(
                            run_id,
                            status="needs_input",
                            summary=driver.blocked
                            + " Take over in the dedicated browser, then Resume.",
                        )
                        driver.blocked = None
                        self._checkpoint(run_id, control)
                        interrupted = True
                    if interrupted:
                        history = self._history(
                            record,
                            self._capture(record, driver, steps),
                            "The user took over; observe the current page again.",
                        )
                    else:
                        history.extend(
                            [
                                {
                                    "type": "function_call_output",
                                    "call_id": call["item"]["call_id"],
                                    "output": (
                                        "Action was blocked without execution: "
                                        + action_error
                                        + ". Choose a supported action using the fresh screenshot."
                                        if action_error
                                        else "Browser action finished. Inspect the fresh screenshot before continuing."
                                    ),
                                },
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_image",
                                            "image_url": image_input(png),
                                        }
                                    ],
                                },
                            ]
                        )
                self._save(
                    run_id,
                    status="finished",
                    summary="The 20-step limit was reached. Review the saved screen and downloads; the subtask has not been marked complete.",
                )
        except RunStopped:
            self._save(
                run_id,
                status="stopped",
                summary="Stopped by you. Saved screenshots and downloads remain available; the subtask is unchanged.",
            )
        except BrowserActionError as exc:
            self._save(
                run_id,
                status="failed",
                summary="The browser stopped: "
                + str(exc)
                + ". Saved results and task state are preserved.",
            )
        except TaskChanged:
            self._save(
                run_id,
                status="interrupted",
                summary="The task or its parent changed during execution. The browser stopped to preserve your correction. Start a new handoff using its current state.",
            )
        except Exception as exc:  # noqa: BLE001 -- isolate browser/provider failures from saved tasks
            logging.getLogger(__name__).error(
                "Local browser run %s failed (%s)", run_id, type(exc).__name__
            )
            self._save(
                run_id,
                status="failed",
                summary="The browser run could not continue. Check the browser installation, website and Meta model access, then try a new handoff. Saved tasks and any captured results are preserved.",
            )
        finally:
            with self.lock:
                self.live.pop(run_id, None)

    def artifact(self, owner, run_id, kind, value):
        record = self.get(owner, run_id)
        if kind == "frame":
            if not isinstance(value, int) or not 1 <= value <= record["frame"]:
                raise HTTPException(404, "Screenshot not found")
            return self.directory / run_id / f"frame-{value}.png", "image/png", None
        item = next((d for d in record["downloads"] if d["id"] == value), None)
        if not item:
            raise HTTPException(404, "Download not found")
        return (
            self.directory / run_id / item["id"],
            "application/octet-stream",
            item["name"],
        )

    def shutdown(self):
        with self.lock:
            running = list(self.live.values())
            for control in running:
                control["stop"].set()
        for control in running:
            if control["thread"]:
                control["thread"].join(timeout=2)


def main():
    """One loopback app process owns the worker and browser lifecycle."""
    import uvicorn

    from .api import create_app
    from .config import Settings

    settings = Settings(browser_worker_enabled=True)
    if settings.vercel:
        raise SystemExit("The laptop browser worker must run locally.")
    uvicorn.run(create_app(settings), host="127.0.0.1", port=8000)
