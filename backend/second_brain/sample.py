"""Small, explicitly illustrative starter workspace; no model calls or fake replies."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import insert, update

from .attachments import validate_file
from .db import accounts, attachments, context, events, messages, now, runs, tasks, uid
from .schemas import Handoff

BRIEF = """EXAMPLE PRESENTATION BRIEF

Topic: How students can reduce food waste on campus.
Audience: A first-year university seminar.
Format: Five slides and a five-minute talk.

Include:
- One reliable statistic, with its source and publication date.
- Three practical actions students can take.
- One realistic proposal for the campus dining hall.

Keep the language clear and avoid unsupported environmental claims.
This is fictional sample content, not a real course assignment.
"""


def seed_workspace(connection, user_id, *, today=None):
    """Called inside the account lock, only for an untouched empty workspace.

    Everything commits together. Account revision prevents reseeding after edits
    or deletion; the caller is responsible for checking that the workspace is empty.
    """
    today = today or datetime.now(UTC).date()
    timestamp = now()
    saved = []

    def add(
        title,
        *,
        parent=None,
        horizon=None,
        due=None,
        level=None,
        score=50,
        handler="user",
        completed=False,
    ):
        assessment = Handoff(
            handler=handler,
            reason=(
                "Example assessment: Muse can research or draft this in task chat."
                if handler == "muse"
                else "Example assessment: this needs your personal action or practice."
            ),
            requirements=[],
            done_when=f"Finished: {title}.",
        ).model_dump()
        record = {
            "id": uid(),
            "user_id": user_id,
            "parent_task_id": parent,
            "title": title,
            "description": "",
            "deadline": (today + timedelta(days=due)).isoformat()
            if due is not None
            else None,
            "time_horizon": horizon,
            "importance_score": score,
            "user_importance_level": level,
            "status": "completed" if completed else "pending",
            "handoff": assessment,
            "handoff_source": "sample",
            "position": sum(t["parent_task_id"] == parent for t in saved),
            "version": 1,
            "created_at": timestamp,
            "updated_at": timestamp,
            "deleted_at": None,
        }
        # Insert parents before children to preserve owner/parent constraints.
        connection.execute(insert(tasks).values(**record))
        saved.append(record)
        return record["id"]

    presentation = add(
        "Prepare the climate presentation",
        horizon="short_term",
        due=1,
        level="very_high",
        score=90,
    )
    add("Choose the main argument", parent=presentation, completed=True)
    add(
        "Find three credible sources on campus food waste",
        parent=presentation,
        due=0,
        score=85,
        handler="muse",
    )
    add(
        "Draft a five-slide outline from the brief",
        parent=presentation,
        score=80,
        handler="muse",
    )
    add("Rehearse the five-minute talk", parent=presentation, score=75)

    internships = add(
        "Compare summer internship options",
        horizon="short_term",
        due=3,
        level="high",
        score=75,
        handler="muse",
    )
    add(
        "Research three internships for a first-year CS student",
        parent=internships,
        score=70,
        handler="muse",
    )
    add(
        "Compare eligibility, application dates and required skills",
        parent=internships,
        score=65,
        handler="muse",
    )

    add(
        "Book a dentist appointment",
        horizon="short_term",
        due=6,
        level="medium",
        score=50,
    )

    meals = add(
        "Plan next week's meals",
        horizon="short_term",
        due=10,
        level="low",
        score=30,
        handler="muse",
    )
    add(
        "Suggest three quick vegetarian dinners", parent=meals, score=35, handler="muse"
    )
    add(
        "Combine the ingredients into a shopping list",
        parent=meals,
        score=30,
        handler="muse",
    )

    portfolio = add(
        "Build a design portfolio", horizon="long_term", level="high", score=65
    )
    add("Choose two projects worth developing", parent=portfolio, score=60)
    add("Write a short case study for each", parent=portfolio, score=60, handler="muse")
    running = add("Run a comfortable 5K", horizon="long_term", level="medium", score=45)
    add("Build a consistent twice-weekly running habit", parent=running, score=45)

    add(
        "Submit the lab report",
        horizon="short_term",
        due=-2,
        level="medium",
        score=50,
        completed=True,
    )
    add(
        "Finish the Python basics course",
        horizon="long_term",
        level="low",
        score=30,
        completed=True,
    )

    file_id = uid()
    file = validate_file("presentation-brief.txt", BRIEF.encode("utf-8"))
    connection.execute(
        insert(attachments).values(
            **file,
            id=file_id,
            user_id=user_id,
            created_at=timestamp,
        )
    )

    def example_context(text, task_id=None, files=None):
        run_id = uid()
        connection.execute(
            insert(runs).values(
                id=run_id,
                user_id=user_id,
                task_id=None,
                request_id=uid(),
                message=text,
                input_payload={
                    "operation": "sample_context",
                    "chat_task_id": task_id,
                    "keep_chat_scope": True,
                    "attachment_ids": files or [],
                },
                snapshot_revision=1,
                status="sample",
                proposal=None,
                error=None,
                model="none (sample content)",
                created_at=timestamp,
                updated_at=timestamp,
            )
        )
        connection.execute(
            insert(messages).values(
                id=uid(),
                user_id=user_id,
                run_id=run_id,
                role="user",
                content=text,
                created_at=timestamp,
            )
        )

    example_context(
        "This is an example student day: a presentation coming up, internship "
        "research, a personal errand and meal planning, alongside two longer-term "
        "goals. These tasks and completed steps are illustrative. Edit them freely; "
        "Muse will respond to the messages you send."
    )
    example_context(
        "Sample context: the attached brief is for the climate presentation. "
        "The main argument is already chosen: small campus habits can reduce food "
        "waste. The sources and slide outline still need work. No research has "
        "been performed yet.",
        presentation,
        [file_id],
    )
    connection.execute(
        insert(context).values(
            id="sample-workspace",
            user_id=user_id,
            category="current_situation",
            content="Starter tasks, completed steps and example chat context are fictional "
            "sample data, not facts about the visitor. Sample handoff assessments "
            "are illustrative, not model results. Respect subsequent user changes.",
            provenance="sample",
            source="sample_workspace",
            version=1,
            updated_at=timestamp,
        )
    )
    connection.execute(
        insert(events).values(
            id=uid(),
            user_id=user_id,
            kind="workspace.sample_loaded",
            entity_id=user_id,
            details={
                "source": "sample_workspace",
                "task_ids": [t["id"] for t in saved],
                "note": "Illustrative content; no model requests or execution performed.",
            },
            created_at=timestamp,
        )
    )
    connection.execute(
        update(accounts).where(accounts.c.user_id == user_id).values(revision=1)
    )
