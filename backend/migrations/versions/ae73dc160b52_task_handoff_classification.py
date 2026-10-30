"""Store reviewed handoff recommendations separately from execution status."""

import sqlalchemy as sa
from alembic import op

revision = "ae73dc160b52"
down_revision = "753bc02ac941"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tasks", sa.Column("handoff", sa.JSON(), nullable=True))
    op.add_column("tasks", sa.Column("handoff_source", sa.String(20), nullable=True))


def downgrade():
    with op.batch_alter_table("tasks") as batch:
        batch.drop_column("handoff_source")
        batch.drop_column("handoff")
