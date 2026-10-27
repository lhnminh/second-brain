"""The conversation migration must preserve the existing task-planning slice."""

from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import insert

from second_brain.api import create_app
from second_brain.config import Settings
from second_brain.db import make_engine, now, runs, tasks
from second_brain.service import task_values


def test_upgrade_preserves_existing_tasks_and_reviewable_plans(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'legacy.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(cfg, "806c16449586")
    engine = make_engine(url)
    task = task_values("alice", {"title": "Saved before migration"})
    run_id = str(uuid4())
    with engine.begin() as c:
        c.execute(insert(tasks).values(**task))
        c.execute(
            insert(runs).values(
                id=run_id,
                user_id="alice",
                task_id=task["id"],
                request_id=str(uuid4()),
                message="Plan it",
                snapshot_revision=0,
                status="awaiting_review",
                proposal={"reply": "Review", "importance_score": 50, "subtasks": []},
                model="fixture",
                created_at=now(),
                updated_at=now(),
            )
        )
    command.upgrade(cfg, "head")
    client = TestClient(
        create_app(
            Settings(
                _env_file=None,
                database_url=url,
                mock_user_id="alice",
                mock_auth_token=None,
                vercel=None,
            ),
            engine,
        )
    )
    data = client.get("/api/dashboard").json()
    assert data["tasks"] == [task]
    assert data["runs"][0]["input_payload"] is None
    assert client.post(f"/api/runs/{run_id}/approve", json={}).status_code == 200
    assert client.get("/api/dashboard").json()["tasks"][0]["importance_score"] == 50
    engine.dispose()
