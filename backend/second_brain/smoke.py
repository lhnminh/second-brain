"""Opt-in live Muse → validated review → disposable saved task smoke check."""

import tempfile
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from pydantic import ValidationError

from .config import Settings
from .db import make_engine
from .muse import Muse
from .schemas import Approval, PlanRequest, TaskCreate, TaskEdit
from .service import Service


def main():
    settings = Settings()
    # Override migration configuration locally, without modifying .env or Neon.
    with tempfile.TemporaryDirectory(prefix="second-brain-live-") as folder:
        import os

        original = os.environ.get("DATABASE_URL")
        url = f"sqlite:///{folder}/smoke.db"
        os.environ["DATABASE_URL"] = url
        try:
            command.upgrade(
                Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head"
            )
        finally:
            if original is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = original
        engine = make_engine(url)
        try:
            service = Service(engine, Muse(settings), "live-smoke", settings.meta_model)
            task = service.create_task(
                TaskCreate(
                    title="Finish homework",
                    description="Synthetic test assignment: read chapter 3 and answer questions 1–5.",
                    deadline="2026-11-01",
                    user_importance_level="high",
                )
            )
            run = service.plan(
                task["id"],
                PlanRequest(
                    request_id=uuid4(),
                    message=(
                        "Help break down this synthetic homework assignment into concrete subtasks. "
                        "Use only the assignment details in the task description."
                    ),
                ),
            )
            print(f"Live Muse run: {run['status']}")
            if run["status"] != "awaiting_review":
                raise SystemExit(1)
            if not run["proposal"]["subtasks"]:
                raise SystemExit(
                    "Live response had no subtasks; breakdown check incomplete"
                )
            service.review(run["id"], Approval())
            service.edit_task(
                task["id"],
                TaskEdit(
                    expected_version=2,
                    description="User correction: I can start on Saturday",
                ),
            )
            # Reconnect to verify persistence beyond the original service instance.
            engine.dispose()
            saved = service.dashboard()
            assert saved["runs"][0]["status"] == "applied"
            assert any(
                t["description"] == "User correction: I can start on Saturday"
                for t in saved["tasks"]
            )
            print(
                f"Saved task count: {len(saved['tasks'])}; review and correction persisted"
            )
        finally:
            engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except ValidationError:
        raise SystemExit("Invalid configuration; check local settings") from None
