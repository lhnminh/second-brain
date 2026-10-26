from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from second_brain.api import create_app
from second_brain.config import Settings
from second_brain.db import make_engine
from second_brain.schemas import Proposal


class FixtureMuse:
    """Explicit test fixture; never selected by application configuration."""

    calls = 0
    callback = None

    def plan(self, snapshot, message):
        self.calls += 1
        self.snapshot = snapshot
        if self.callback:
            return self.callback(snapshot, message)
        return Proposal(
            reply="Review these steps before saving.",
            importance_score=70,
            subtasks=[
                {
                    "title": "Read the assignment",
                    "description": "Identify the requirements",
                    "importance_score": 65,
                },
                {
                    "title": "Work through the questions",
                    "description": "Use the assignment instructions",
                    "importance_score": 70,
                },
            ],
        )


@pytest.fixture
def setup(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(cfg, "head")
    engine = make_engine(url)
    muse = FixtureMuse()

    def client(user="alice", token=None):
        settings = Settings(
            _env_file=None,
            database_url=url,
            mock_user_id=user,
            mock_auth_token=token,
            meta_api_key=None,
            vercel=None,
        )
        return TestClient(create_app(settings, engine, muse))

    yield client, muse, engine
    engine.dispose()
