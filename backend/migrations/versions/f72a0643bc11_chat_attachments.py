"""Workspace-owned chat files; existing conversations remain untouched."""

import sqlalchemy as sa
from alembic import op

revision = "f72a0643bc11"
down_revision = "e490ac621fb8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "attachments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("media_type", sa.String(100), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(100000)),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
    )
    op.create_index("ix_attachments_user_id", "attachments", ["user_id"])


def downgrade():
    op.drop_table("attachments")
