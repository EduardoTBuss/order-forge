"""Create disabled_tables clean

Revision ID: 78094a9cbb21
Revises: c016e7975ec3
Create Date: 2025-08-21 16:07:06.990369

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "78094a9cbb21"
down_revision: Union[str, None] = "c016e7975ec3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "disabled_tables",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("table_name", sa.String(), nullable=False, unique=True),
        sa.Column(
            "disabled_columns",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "is_fully_disabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
