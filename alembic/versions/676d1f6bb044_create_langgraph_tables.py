"""create_langgraph_tables

Revision ID: 676d1f6bb044
Revises: 17d1fb45f3a8
Create Date: 2026-02-12 12:42:41.583732

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import BYTEA, JSONB

# revision identifiers, used by Alembic.
revision: str = "676d1f6bb044"
down_revision: str | Sequence[str] | None = "17d1fb45f3a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "checkpoints",
        sa.Column("thread_id", sa.TEXT, primary_key=True),
        sa.Column("checkpoint_ns", sa.TEXT, primary_key=True, server_default=""),
        sa.Column("checkpoint_id", sa.TEXT, primary_key=True),
        sa.Column("parent_checkpoint_id", sa.TEXT, nullable=True),
        sa.Column("type", sa.TEXT, nullable=True),
        sa.Column("checkpoint", JSONB, nullable=False),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
    )

    op.create_table(
        "checkpoint_blobs",
        sa.Column("thread_id", sa.TEXT, primary_key=True),
        sa.Column("checkpoint_ns", sa.TEXT, primary_key=True, server_default=""),
        sa.Column("channel", sa.TEXT, primary_key=True),
        sa.Column("version", sa.TEXT, primary_key=True),
        sa.Column("type", sa.TEXT, nullable=True),
        sa.Column("blob", BYTEA, nullable=True),
    )

    op.create_table(
        "checkpoint_writes",
        sa.Column("thread_id", sa.TEXT, primary_key=True),
        sa.Column("checkpoint_ns", sa.TEXT, primary_key=True, server_default=""),
        sa.Column("checkpoint_id", sa.TEXT, primary_key=True),
        sa.Column("task_id", sa.TEXT, primary_key=True),
        sa.Column("idx", sa.INTEGER, primary_key=True),
        sa.Column("channel", sa.TEXT, nullable=False),
        sa.Column("type", sa.TEXT, nullable=True),
        sa.Column("blob", BYTEA, nullable=True),
        sa.Column("value", JSONB, nullable=True),
        sa.Column("task_path", sa.TEXT, nullable=False, server_default=""),
    )

    op.create_table(
        "checkpoint_migrations",
        sa.Column("v", sa.INTEGER, primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("checkpoint_migrations")
    op.drop_table("checkpoint_writes")
    op.drop_table("checkpoint_blobs")
    op.drop_table("checkpoints")
