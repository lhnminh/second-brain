"""Persist reviewed, editable task drafts without changing task status."""

import sqlalchemy as sa
from alembic import op

revision = "753bc02ac941"
down_revision = "22c90aa438bc"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "task_drafts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.String(20000), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.Column("updated_at", sa.String(40), nullable=False),
        sa.ForeignKeyConstraint(["user_id", "id"], ["tasks.user_id", "tasks.id"]),
    )
    op.create_index("ix_task_drafts_user_id", "task_drafts", ["user_id"])


def downgrade():
    op.drop_index("ix_task_drafts_user_id", table_name="task_drafts")
    op.drop_table("task_drafts")
