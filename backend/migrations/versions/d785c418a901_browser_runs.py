"""Persist dedicated local-browser handoffs separately from planning runs."""

import sqlalchemy as sa
from alembic import op

revision = "d785c418a901"
down_revision = "c42b193d7e61"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "browser_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("task_id", sa.String(36), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("task_version", sa.Integer, nullable=False),
        sa.Column("goal", sa.JSON, nullable=False),
        sa.Column("start_url", sa.String(2000), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("summary", sa.String(10000), nullable=False),
        sa.Column("steps", sa.JSON, nullable=False),
        sa.Column("downloads", sa.JSON, nullable=False),
        sa.Column("frame", sa.Integer, nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.Column("updated_at", sa.String(40), nullable=False),
        sa.UniqueConstraint("user_id", "request_id", name="uq_browser_request"),
        sa.ForeignKeyConstraint(["user_id", "task_id"], ["tasks.user_id", "tasks.id"]),
    )
    op.create_index("ix_browser_runs_user_id", "browser_runs", ["user_id"])


def downgrade():
    op.drop_table("browser_runs")
