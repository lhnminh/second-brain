"""Allow conversation runs before a task exists."""

import sqlalchemy as sa
from alembic import op

revision = "22c90aa438bc"
down_revision = "806c16449586"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("runs") as batch:
        batch.alter_column("task_id", existing_type=sa.String(36), nullable=True)
        batch.add_column(sa.Column("input_payload", sa.JSON(), nullable=True))


def downgrade():
    # Conversation history cannot be represented in the old non-null schema.
    connection = op.get_bind()
    if connection.scalar(sa.text("SELECT count(*) FROM runs WHERE task_id IS NULL")):
        raise RuntimeError("Conversation runs exist; export them before downgrading")
    with op.batch_alter_table("runs") as batch:
        batch.drop_column("input_payload")
        batch.alter_column("task_id", existing_type=sa.String(36), nullable=False)
