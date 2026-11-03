"""Preserve an explicit focus section without changing existing task grouping."""

import sqlalchemy as sa
from alembic import op

revision = "c42b193d7e61"
down_revision = "ae73dc160b52"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "tasks",
        sa.Column(
            "time_horizon",
            sa.String(20),
            sa.CheckConstraint(
                "time_horizon IS NULL OR time_horizon IN ('short_term', 'long_term')",
                name="task_time_horizon",
            ),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("tasks", "time_horizon")
