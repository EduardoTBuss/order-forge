"""add_async_request_table

Revision ID: c016e7975ec3
Revises: 2dd77c3e0c00
Create Date: 2024-03-21 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c016e7975ec3"
down_revision: Union[str, None] = "2dd77c3e0c00"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create async_request table
    op.create_table(
        "async_request",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "completed",
                "pending",
                "processing",
                "failed",
                name="request_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("response", JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("async_request")
