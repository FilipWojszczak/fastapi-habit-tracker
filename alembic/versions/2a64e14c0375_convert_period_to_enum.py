"""convert_period_to_enum

Revision ID: 2a64e14c0375
Revises: 4279a8e05696
Create Date: 2026-01-18 20:52:10.912280

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2a64e14c0375"
down_revision: str | Sequence[str] | None = "4279a8e05696"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute(
        "UPDATE habit SET period = 'daily' WHERE period IS NULL OR period NOT IN "
        "('daily', 'weekly', 'monthly');"
    )

    bind = op.get_bind()
    sa.Enum("daily", "weekly", "monthly", name="habitperiod").create(bind)
    op.execute("ALTER TABLE habit RENAME COLUMN period TO habit_period")
    op.execute(
        "ALTER TABLE habit ALTER COLUMN habit_period TYPE habitperiod USING "
        "habit_period::habitperiod"
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("ALTER TABLE habit RENAME COLUMN habit_period TO period")
    op.execute("ALTER TABLE habit ALTER COLUMN period TYPE VARCHAR USING period::text")
    op.execute("DROP TYPE habitperiod")
