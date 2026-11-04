"""Reversible task removal preserves chats, execution results and relationships."""

import sqlalchemy as sa
from alembic import op

revision = "e490ac621fb8"
down_revision = "d785c418a901"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tasks", sa.Column("deleted_at", sa.String(40), nullable=True))


def downgrade():
    op.drop_column("tasks", "deleted_at")
