"""order_intake customer api_key

Adds an optional ``api_key`` column to ``oi_customers`` for the ``llm_api``
extraction strategy (external LLM with the customer's own key).

Revision ID: b3c4d5e6f7a9
Revises: a2b3c4d5e6f8
Create Date: 2026-06-26 14:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "b3c4d5e6f7a9"
down_revision: Union[str, None] = "a2b3c4d5e6f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "oi_customers", sa.Column("api_key", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("oi_customers", "api_key")
