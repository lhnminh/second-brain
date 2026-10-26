from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .db import accounts, context, events, messages, now, runs, tasks, uid
from .muse import MuseFailure
from .schemas import RANGES, Proposal


def rows(connection, table, user_id):
    return [
        dict(row)
        for row in connection.execute(
            select(table).where(table.c.user_id == user_id)
        ).mappings()
    ]


def owned(connection, table, record_id, user_id):
    record = (
        connection.execute(
            select(table).where(
                table.c.id == record_id,
                table.c.user_id == user_id,
            )
        )
        .mappings()
        .first()
    )
    if record is None:
        raise HTTPException(404, "Record not found")
    return dict(record)


def audit(connection, user_id, kind, entity_id, details):
    connection.execute(
        insert(events).values(
            id=uid(),
            user_id=user_id,
            kind=kind,
            entity_id=entity_id,
            details=details,
            created_at=now(),
        )
    )


def lock_account(connection, user_id):
    # A write serializes this user's mutations on both Postgres and SQLite.
    dialect_insert = sqlite_insert if connection.dialect.name == "sqlite" else pg_insert
    connection.execute(
        dialect_insert(accounts)
        .values(user_id=user_id, revision=0)
        .on_conflict_do_nothing(index_elements=["user_id"])
    )
    connection.execute(
        update(accounts)
        .where(accounts.c.user_id == user_id)
        .values(revision=accounts.c.revision)
    )
    return connection.scalar(
        select(accounts.c.revision).where(accounts.c.user_id == user_id)
    )


def bump(connection, user_id):
    connection.execute(
        update(accounts)
        .where(accounts.c.user_id == user_id)
        .values(revision=accounts.c.revision + 1)
    )


def check_score(proposal, task):
    if task["user_importance_level"]:
        low, high = RANGES[task["user_importance_level"]]
        if not low <= proposal.importance_score <= high:
            raise ValueError(
                "Proposed importance conflicts with the user's selected level"
            )


def task_values(user_id, data, position=0, score=None):
    return {
        "id": uid(),
        "user_id": user_id,
        "parent_task_id": data.get("parent_task_id"),
        "title": data["title"],
        "description": data.get("description", ""),
        "deadline": data.get("deadline"),
        "importance_score": score,
        "user_importance_level": data.get("user_importance_level"),
        "status": "pending",
        "position": position,
        "version": 1,
        "created_at": now(),
        "updated_at": now(),
    }


class Service:
    def __init__(self, engine, muse, user_id, model):
        self.engine, self.muse, self.user_id, self.model = engine, muse, user_id, model

    def dashboard(self):
        with self.engine.begin() as c:
            lock_account(c, self.user_id)
            # A terminated serverless invocation must not look permanently running.
            cutoff = (datetime.now(UTC) - timedelta(minutes=2)).isoformat()
            for run in rows(c, runs, self.user_id):
                if run["status"] == "running" and run["updated_at"] < cutoff:
                    self._finish(
                        c,
                        run["id"],
                        "failed",
                        error="Planning interrupted; retry with a new request_id",
                    )
            data = {"user_id": self.user_id}
            for key, table in (
                ("tasks", tasks),
                ("context", context),
                ("runs", runs),
                ("messages", messages),
                ("events", events),
            ):
                data[key] = sorted(
                    rows(c, table, self.user_id),
                    key=lambda r: (
                        r.get("created_at", r.get("updated_at", "")),
                        r["id"],
                    ),
                )
            return data

    def create_task(self, body):
        data = body.model_dump(mode="json")
        with self.engine.begin() as c:
            lock_account(c, self.user_id)
            if data["parent_task_id"]:
                owned(c, tasks, data["parent_task_id"], self.user_id)
            position = c.scalar(
                select(func.count())
                .select_from(tasks)
                .where(
                    tasks.c.user_id == self.user_id,
                    tasks.c.parent_task_id == data["parent_task_id"],
                )
            )
            record = task_values(self.user_id, data, position)
            c.execute(insert(tasks).values(**record))
            bump(c, self.user_id)
            audit(c, self.user_id, "task.created", record["id"], record)
            return record

    def edit_task(self, task_id, body):
        with self.engine.begin() as c:
            lock_account(c, self.user_id)
            task = owned(c, tasks, task_id, self.user_id)
            if task["version"] != body.expected_version:
                raise HTTPException(409, "Task changed; reload before editing")
            changes = body.model_dump(
                mode="json", exclude_unset=True, exclude={"expected_version"}
            )
            if (
                "user_importance_level" in changes
                and changes["user_importance_level"] is not None
                and task["importance_score"] is not None
            ):
                low, high = RANGES[changes["user_importance_level"]]
                changes["importance_score"] = min(
                    high, max(low, task["importance_score"])
                )
            changes.update(version=task["version"] + 1, updated_at=now())
            c.execute(
                update(tasks)
                .where(tasks.c.id == task_id, tasks.c.user_id == self.user_id)
                .values(**changes)
            )
            bump(c, self.user_id)
            audit(
                c,
                self.user_id,
                "task.edited",
                task_id,
                {"before": task, "changes": changes},
            )
            return owned(c, tasks, task_id, self.user_id)

    def save_context(self, context_id, body):
        with self.engine.begin() as c:
            lock_account(c, self.user_id)
            previous = (
                c.execute(
                    select(context).where(
                        context.c.id == context_id,
                        context.c.user_id == self.user_id,
                    )
                )
                .mappings()
                .first()
            )
            version = previous["version"] if previous else 0
            if version != body.expected_version:
                raise HTTPException(409, "Context changed; reload before editing")
            record = body.model_dump(exclude={"expected_version"})
            record.update(
                id=context_id,
                user_id=self.user_id,
                version=version + 1,
                source="direct_user_edit",
                updated_at=now(),
            )
            if previous:
                c.execute(
                    update(context)
                    .where(
                        context.c.id == context_id, context.c.user_id == self.user_id
                    )
                    .values(**record)
                )
            else:
                c.execute(insert(context).values(**record))
            bump(c, self.user_id)
            audit(
                c,
                self.user_id,
                "context.saved",
                context_id,
                {"before": dict(previous) if previous else None, "after": record},
            )
            return record

    def _finish(self, c, run_id, status, **changes):
        c.execute(
            update(runs)
            .where(runs.c.id == run_id, runs.c.user_id == self.user_id)
            .values(status=status, updated_at=now(), **changes)
        )
        audit(c, self.user_id, f"planning.{status}", run_id, changes)

    def plan(self, task_id, body):
        with self.engine.begin() as c:
            revision = lock_account(c, self.user_id)
            task = owned(c, tasks, task_id, self.user_id)
            previous = (
                c.execute(
                    select(runs).where(
                        runs.c.user_id == self.user_id,
                        runs.c.request_id == str(body.request_id),
                    )
                )
                .mappings()
                .first()
            )
            if previous:
                if (
                    previous["task_id"] != task_id
                    or previous["message"] != body.message
                ):
                    raise HTTPException(
                        409, "request_id was already used for a different request"
                    )
                return dict(previous)
            run_id = uid()
            snapshot = {
                "task": task,
                "tasks": rows(c, tasks, self.user_id),
                "context": rows(c, context, self.user_id),
                "recent_messages": sorted(
                    rows(c, messages, self.user_id), key=lambda m: m["created_at"]
                )[-20:],
            }
            c.execute(
                insert(runs).values(
                    id=run_id,
                    user_id=self.user_id,
                    task_id=task_id,
                    request_id=str(body.request_id),
                    message=body.message,
                    snapshot_revision=revision,
                    status="running",
                    model=self.model,
                    created_at=now(),
                    updated_at=now(),
                )
            )
            c.execute(
                insert(messages).values(
                    id=uid(),
                    user_id=self.user_id,
                    run_id=run_id,
                    role="user",
                    content=body.message,
                    created_at=now(),
                )
            )
            audit(c, self.user_id, "planning.running", run_id, {"task_id": task_id})
        # Network work is outside the transaction. Running means an actual call was started.
        try:
            proposal = Proposal.model_validate(self.muse.plan(snapshot, body.message))
            check_score(proposal, task)
            error = None
        except MuseFailure, ValueError:
            proposal, error = (
                None,
                "Muse could not produce a valid proposal. Your tasks are unchanged.",
            )
        with self.engine.begin() as c:
            current_revision = lock_account(c, self.user_id)
            run = owned(c, runs, run_id, self.user_id)
            if run["status"] != "running":
                return run
            if error:
                self._finish(c, run_id, "failed", error=error)
            else:
                status = "awaiting_review" if current_revision == revision else "stale"
                self._finish(
                    c, run_id, status, proposal=proposal.model_dump(mode="json")
                )
                c.execute(
                    insert(messages).values(
                        id=uid(),
                        user_id=self.user_id,
                        run_id=run_id,
                        role="assistant",
                        content=proposal.reply,
                        created_at=now(),
                    )
                )
            return owned(c, runs, run_id, self.user_id)

    def review(self, run_id, approval=None, reject=False):
        with self.engine.begin() as c:
            revision = lock_account(c, self.user_id)
            run = owned(c, runs, run_id, self.user_id)
            if (reject and run["status"] == "rejected") or (
                not reject and run["status"] == "applied"
            ):
                return run
            if run["status"] != "awaiting_review":
                raise HTTPException(409, f"Run cannot be reviewed: {run['status']}")
            if reject:
                self._finish(c, run_id, "rejected")
                return owned(c, runs, run_id, self.user_id)
            if revision != run["snapshot_revision"]:
                # Persist stale status before returning a conflict to the caller.
                self._finish(c, run_id, "stale")
                result = None
            else:
                task = owned(c, tasks, run["task_id"], self.user_id)
                proposal = approval.proposal or Proposal.model_validate(run["proposal"])
                try:
                    check_score(proposal, task)
                except ValueError as exc:
                    raise HTTPException(422, str(exc)) from None
                position = c.scalar(
                    select(func.count())
                    .select_from(tasks)
                    .where(
                        tasks.c.user_id == self.user_id,
                        tasks.c.parent_task_id == task["id"],
                    )
                )
                child_ids = []
                for index, child in enumerate(proposal.subtasks):
                    values = task_values(
                        self.user_id,
                        {**child.model_dump(), "parent_task_id": task["id"]},
                        position + index,
                        child.importance_score,
                    )
                    c.execute(insert(tasks).values(**values))
                    audit(
                        c,
                        self.user_id,
                        "task.created",
                        values["id"],
                        {"run_id": run_id, "task": values},
                    )
                    child_ids.append(values["id"])
                c.execute(
                    update(tasks)
                    .where(tasks.c.id == task["id"], tasks.c.user_id == self.user_id)
                    .values(
                        importance_score=proposal.importance_score,
                        version=task["version"] + 1,
                        updated_at=now(),
                    )
                )
                bump(c, self.user_id)
                audit(
                    c,
                    self.user_id,
                    "task.scored",
                    task["id"],
                    {
                        "run_id": run_id,
                        "before": task["importance_score"],
                        "after": proposal.importance_score,
                    },
                )
                self._finish(
                    c, run_id, "applied", proposal=proposal.model_dump(mode="json")
                )
                audit(
                    c,
                    self.user_id,
                    "planning.approved",
                    run_id,
                    {"child_ids": child_ids},
                )
                result = owned(c, runs, run_id, self.user_id)
        if result is None:
            raise HTTPException(409, "Your state changed; request a fresh plan")
        return result
