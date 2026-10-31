from datetime import UTC, datetime, timedelta
from functools import cache

from fastapi import HTTPException
from sqlalchemy import func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .db import accounts, context, drafts, events, messages, now, runs, tasks, uid
from .muse import MuseFailure
from .schemas import RANGES, ConversationProposal, Proposal


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


def lock_account(connection, user_id, *, read_revision=True):
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
    if read_revision:
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


def task_values(user_id, data, position=0, score=None, handoff_source=None):
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
        "handoff": data.get("handoff"),
        "handoff_source": (
            (handoff_source or "user")
            if data.get("handoff") is not None or handoff_source == "user"
            else None
        ),
        "position": position,
        "version": 1,
        "created_at": now(),
        "updated_at": now(),
    }


def planning_tasks(saved_tasks):
    """Separate current work from history, including plans with no open steps.

    This is model context only: parent completion remains an explicit user edit.
    """
    by_id = {task["id"]: task for task in saved_tasks}
    children = {}
    for task in saved_tasks:
        children.setdefault(task["parent_task_id"], []).append(task["id"])

    @cache
    def leaves_completed(task_id):
        descendants = children.get(task_id, [])
        return (
            all(leaves_completed(child) for child in descendants)
            if descendants
            else by_id[task_id]["status"] == "completed"
        )

    finished = {
        task["id"]: (
            "completed" if task["status"] == "completed" else "all_steps_completed"
        )
        for task in saved_tasks
        if task["status"] == "completed"
        or (children.get(task["id"]) and leaves_completed(task["id"]))
    }
    active, history = [], []
    for task in saved_tasks:
        current = task
        while current is not None:
            if current["id"] in finished:
                history.append(
                    {
                        **task,
                        "completion_reason": finished[current["id"]]
                        if current["id"] == task["id"]
                        else "completed_parent",
                    }
                )
                break
            current = by_id.get(current["parent_task_id"])
        else:
            active.append(task)
    return active, history


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
                        error="Agent request interrupted; retry with a new request_id",
                    )
            data = {"user_id": self.user_id}
            for key, table in (
                ("tasks", tasks),
                ("drafts", drafts),
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
            lock_account(c, self.user_id, read_revision=False)
            task = owned(c, tasks, task_id, self.user_id)
            if task["version"] != body.expected_version:
                raise HTTPException(409, "Task changed; reload before editing")
            changes = body.model_dump(
                mode="json", exclude_unset=True, exclude={"expected_version"}
            )
            if "handoff" in changes:
                # Clearing an assessment is also an intentional user correction.
                changes["handoff_source"] = "user"
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
            # All changed values are explicit and the owner lock still serializes
            # edits. Return the saved row without another remote database read.
            return {**task, **changes}

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
        run = owned(c, runs, run_id, self.user_id)
        kind = (
            "draft"
            if (run["input_payload"] or {}).get("operation") == "draft"
            else "planning"
        )
        audit(c, self.user_id, f"{kind}.{status}", run_id, changes)

    def plan(self, task_id, body):
        with self.engine.begin() as c:
            revision = lock_account(c, self.user_id)
            task = owned(c, tasks, task_id, self.user_id) if task_id else None
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
                previous_input = previous["input_payload"]
                if task_id is None and previous_input is not None:
                    previous_input = {"apply_immediately": False, **previous_input}
                if (
                    previous["task_id"] != task_id
                    or previous["message"] != body.message
                    or (
                        previous_input is not None
                        and previous_input != body.model_dump(mode="json")
                    )
                ):
                    raise HTTPException(
                        409, "request_id was already used for a different request"
                    )
                return dict(previous)
            run_id = uid()
            recent_runs = rows(c, runs, self.user_id)
            recent_messages = rows(c, messages, self.user_id)
            if task_id is None:
                recent_runs = [
                    run
                    for run in recent_runs
                    if (run["input_payload"] or {}).get("operation") != "draft"
                ]
                run_ids = {run["id"] for run in recent_runs}
                recent_messages = [m for m in recent_messages if m["run_id"] in run_ids]
            if task_id is None and body.conversation_id is not None:
                # Saved tasks/context carry forward; chat belongs to this visit.
                recent_runs = [
                    run
                    for run in recent_runs
                    if (run["input_payload"] or {}).get("conversation_id")
                    == str(body.conversation_id)
                ]
                run_ids = {run["id"] for run in recent_runs}
                recent_messages = [
                    message
                    for message in recent_messages
                    if message["run_id"] in run_ids
                ]
            saved_tasks = rows(c, tasks, self.user_id)
            active_tasks, completed_tasks = planning_tasks(saved_tasks)
            snapshot = {
                "apply_immediately": task_id is None
                and getattr(body, "apply_immediately", False),
                "reference_date_utc": datetime.now(UTC).date().isoformat(),
                "recent_runs": sorted(recent_runs, key=lambda r: r["created_at"])[-10:],
                "task": task,
                "tasks": active_tasks,
                "completed_tasks": completed_tasks,
                "context": rows(c, context, self.user_id),
                "recent_messages": sorted(
                    recent_messages, key=lambda m: m["created_at"]
                )[-20:],
            }
            if task_id is None and body.review_draft is not None:
                try:
                    self._check_conversation(body.review_draft, saved_tasks)
                except ValueError as exc:
                    raise HTTPException(422, str(exc)) from None
                snapshot["review_draft"] = body.review_draft.model_dump(mode="json")
            c.execute(
                insert(runs).values(
                    id=run_id,
                    user_id=self.user_id,
                    task_id=task_id,
                    request_id=str(body.request_id),
                    message=body.message,
                    input_payload=body.model_dump(mode="json"),
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
            if task_id:
                proposal = Proposal.model_validate(
                    self.muse.plan(snapshot, body.message)
                )
                check_score(proposal, task)
            else:
                proposal = ConversationProposal.model_validate(
                    self.muse.converse(snapshot, body.message)
                )
                if body.apply_immediately and any(
                    (item.task_id is None and item.handoff is None)
                    or any(child.handoff is None for child in item.subtasks)
                    for item in proposal.tasks
                ):
                    raise ValueError("New tasks must include handoff classifications")
                self._check_conversation(
                    proposal, saved_tasks, protect_handoff=True, protect_history=True
                )
            error = None
        except MuseFailure, ValueError:
            proposal, error = (
                None,
                "Muse could not produce valid task updates. Your tasks are unchanged.",
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
                if task_id is None and any(
                    other["task_id"] is None and other["created_at"] > run["created_at"]
                    for other in rows(c, runs, self.user_id)
                ):
                    # An older reply must not replace a newer conversation correction.
                    status = "stale"
                if task_id is None and status == "awaiting_review":
                    if not proposal.tasks:
                        status = "answered"
                    else:
                        # A successful revision replaces earlier conversation drafts.
                        for old in rows(c, runs, self.user_id):
                            if (
                                old["task_id"] is None
                                and old["status"] == "awaiting_review"
                            ):
                                self._finish(c, old["id"], "superseded")
                        if body.apply_immediately:
                            # The input, validated updates, audit records, and final
                            # run state commit together. No intermediate review step.
                            self._apply_conversation(c, run_id, proposal, proposal)
                            bump(c, self.user_id)
                            status = "applied"
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

    def review(self, run_id, approval=None, reject=False, conversation=False):
        with self.engine.begin() as c:
            revision = lock_account(c, self.user_id)
            run = owned(c, runs, run_id, self.user_id)
            if not reject and (run["task_id"] is None) != conversation:
                raise HTTPException(409, "Use the matching proposal review endpoint")
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
            elif run["task_id"] is None:
                proposal = approval.proposal or ConversationProposal.model_validate(
                    run["proposal"]
                )
                try:
                    self._check_conversation(proposal, rows(c, tasks, self.user_id))
                except ValueError as exc:
                    raise HTTPException(422, str(exc)) from None
                self._apply_conversation(
                    c,
                    run_id,
                    proposal,
                    ConversationProposal.model_validate(run["proposal"]),
                )
                bump(c, self.user_id)
                self._finish(
                    c, run_id, "applied", proposal=proposal.model_dump(mode="json")
                )
                result = owned(c, runs, run_id, self.user_id)
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
                original = Proposal.model_validate(run["proposal"])
                for index, child in enumerate(proposal.subtasks):
                    values = task_values(
                        self.user_id,
                        {**child.model_dump(), "parent_task_id": task["id"]},
                        position + index,
                        child.importance_score,
                        handoff_source=(
                            "model"
                            if index < len(original.subtasks)
                            and child.handoff == original.subtasks[index].handoff
                            else "user"
                        ),
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

    def _check_conversation(
        self, proposal, saved_tasks, protect_handoff=False, protect_history=False
    ):
        saved = {t["id"]: t for t in saved_tasks}
        historical_ids = (
            {t["id"] for t in planning_tasks(saved_tasks)[1]}
            if protect_history
            else set()
        )
        seen = set()
        for item in proposal.tasks:
            if item.task_id is not None:
                task_id = str(item.task_id)
                if task_id not in saved or task_id in seen:
                    raise ValueError(
                        "Proposal references an unavailable or repeated task"
                    )
                seen.add(task_id)
                check_score(item, saved[task_id])
                if task_id in historical_ids and item.subtasks:
                    raise ValueError("Create new work separately from a finished plan")
                if protect_handoff and saved[task_id].get("handoff_source") == "user":
                    value = item.handoff.model_dump() if item.handoff else None
                    if value != saved[task_id].get("handoff"):
                        raise ValueError("Preserve the user's handoff classification")

    def _apply_conversation(self, c, run_id, proposal, original):
        for index, item in enumerate(proposal.tasks):
            data = item.model_dump(mode="json", exclude={"task_id", "subtasks"})
            baseline = original.tasks[index] if index < len(original.tasks) else None
            source = (
                "model" if baseline and item.handoff == baseline.handoff else "user"
            )
            if item.task_id:
                task = owned(c, tasks, str(item.task_id), self.user_id)
                # Old pending proposals cannot erase newer classification data.
                if item.handoff is None and (
                    baseline is None or baseline.handoff is None
                ):
                    data.pop("handoff", None)
                elif item.handoff is None:
                    data["handoff_source"] = "user"
                else:
                    data["handoff_source"] = (
                        task["handoff_source"]
                        if data["handoff"] == task["handoff"]
                        else source
                    )
                changes = {**data, "version": task["version"] + 1, "updated_at": now()}
                c.execute(
                    update(tasks)
                    .where(tasks.c.id == task["id"], tasks.c.user_id == self.user_id)
                    .values(**changes)
                )
                audit(
                    c,
                    self.user_id,
                    "task.edited",
                    task["id"],
                    {"run_id": run_id, "before": task, "changes": changes},
                )
            else:
                task = self._insert_conversation_task(
                    c, data, run_id, item.importance_score, source
                )
            for child_index, child in enumerate(item.subtasks):
                self._insert_conversation_task(
                    c,
                    {**child.model_dump(mode="json"), "parent_task_id": task["id"]},
                    run_id,
                    child.importance_score,
                    "model"
                    if baseline
                    and child_index < len(baseline.subtasks)
                    and child.handoff == baseline.subtasks[child_index].handoff
                    else "user",
                )

    def _insert_conversation_task(self, c, data, run_id, score, handoff_source="model"):
        position = c.scalar(
            select(func.count())
            .select_from(tasks)
            .where(
                tasks.c.user_id == self.user_id,
                tasks.c.parent_task_id == data.get("parent_task_id"),
            )
        )
        record = task_values(self.user_id, data, position, score, handoff_source)
        c.execute(insert(tasks).values(**record))
        audit(
            c,
            self.user_id,
            "task.created",
            record["id"],
            {"run_id": run_id, "task": record},
        )
        return record
