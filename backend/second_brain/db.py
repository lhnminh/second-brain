from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.pool import NullPool

metadata = MetaData()


def now():
    return datetime.now(UTC).isoformat()


def uid():
    return str(uuid4())


accounts = Table(
    "accounts",
    metadata,
    Column("user_id", String(100), primary_key=True),
    Column("revision", Integer, nullable=False, server_default="0"),
)
tasks = Table(
    "tasks",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("user_id", String(100), nullable=False, index=True),
    Column("parent_task_id", String(36)),
    Column("title", String(300), nullable=False),
    Column("description", String(10000), nullable=False),
    Column("deadline", String(10)),
    Column("importance_score", Integer),
    Column("user_importance_level", String(20)),
    Column("status", String(20), nullable=False),
    Column("position", Integer, nullable=False),
    Column("version", Integer, nullable=False),
    Column("created_at", String(40), nullable=False),
    Column("updated_at", String(40), nullable=False),
    UniqueConstraint("user_id", "id", name="uq_tasks_owner_id"),
    ForeignKeyConstraint(["user_id", "parent_task_id"], ["tasks.user_id", "tasks.id"]),
    CheckConstraint(
        "parent_task_id IS NULL OR parent_task_id <> id", name="no_self_parent"
    ),
    CheckConstraint(
        "importance_score IS NULL OR importance_score BETWEEN 0 AND 100",
        name="score_bounds",
    ),
    CheckConstraint(
        "status IN ('pending', 'in_progress', 'completed')", name="task_status"
    ),
    CheckConstraint(
        "user_importance_level IS NULL OR user_importance_level IN ('very_low','low','medium','high','very_high')",
        name="importance_level",
    ),
    CheckConstraint(
        "importance_score IS NULL OR user_importance_level IS NULL OR "
        "(user_importance_level='very_low' AND importance_score BETWEEN 0 AND 19) OR "
        "(user_importance_level='low' AND importance_score BETWEEN 20 AND 39) OR "
        "(user_importance_level='medium' AND importance_score BETWEEN 40 AND 59) OR "
        "(user_importance_level='high' AND importance_score BETWEEN 60 AND 79) OR "
        "(user_importance_level='very_high' AND importance_score BETWEEN 80 AND 100)",
        name="user_score_range",
    ),
)
context = Table(
    "context",
    metadata,
    Column("id", String(100), primary_key=True),
    Column("user_id", String(100), primary_key=True),
    Column("category", String(40), nullable=False),
    Column("content", String(10000), nullable=False),
    Column("provenance", String(30), nullable=False),
    Column("source", String(50), nullable=False),
    Column("version", Integer, nullable=False),
    Column("updated_at", String(40), nullable=False),
)
runs = Table(
    "runs",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("user_id", String(100), nullable=False, index=True),
    Column("task_id", String(36)),
    Column("request_id", String(36), nullable=False),
    Column("message", String(10000), nullable=False),
    Column("input_payload", JSON),
    Column("snapshot_revision", Integer, nullable=False),
    Column("status", String(30), nullable=False),
    Column("proposal", JSON),
    Column("error", String(300)),
    Column("model", String(100), nullable=False),
    Column("created_at", String(40), nullable=False),
    Column("updated_at", String(40), nullable=False),
    UniqueConstraint("user_id", "request_id", name="uq_run_request"),
    ForeignKeyConstraint(["user_id", "task_id"], ["tasks.user_id", "tasks.id"]),
)
messages = Table(
    "messages",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("user_id", String(100), nullable=False, index=True),
    Column("run_id", String(36), nullable=False),
    Column("role", String(20), nullable=False),
    Column("content", String(10000), nullable=False),
    Column("created_at", String(40), nullable=False),
)
events = Table(
    "events",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("user_id", String(100), nullable=False, index=True),
    Column("kind", String(50), nullable=False),
    Column("entity_id", String(100), nullable=False),
    Column("details", JSON, nullable=False),
    Column("created_at", String(40), nullable=False),
)


def make_engine(url):
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    options = (
        {"connect_args": {"check_same_thread": False, "timeout": 10}}
        if url.startswith("sqlite")
        else {"poolclass": NullPool}
    )
    engine = create_engine(url, **options)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def foreign_keys(dbapi_connection, _):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

    return engine
