"""initial_semaphore_tables

Revision ID: 2dd77c3e0c00
Revises:
Create Date: 2024-03-21 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "2dd77c3e0c00"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False),
        sa.Column("cost", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usages_timestamp", "usages", ["timestamp"], unique=False)
    op.create_index("ix_usages_path", "usages", ["path"], unique=False)
    op.create_index(
        "ix_usages_path_timestamp", "usages", ["path", "timestamp"], unique=False
    )

    op.create_table(
        "consumption_limits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=True),
        sa.Column("max_cost", sa.Float(), nullable=True),
        sa.Column("max_tokens", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("period", "path", name="uq_consumption_limit_period_path"),
    )


def downgrade() -> None:
    op.drop_table("consumption_limits")
    op.drop_index("ix_usages_path_timestamp", table_name="usages")
    op.drop_index("ix_usages_path", table_name="usages")
    op.drop_index("ix_usages_timestamp", table_name="usages")
    op.drop_table("usages")
