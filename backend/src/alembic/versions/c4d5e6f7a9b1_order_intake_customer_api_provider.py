"""order_intake customer api provider (base_url + model)

Adds optional ``api_base_url`` and ``api_model`` to ``oi_customers`` so each
``llm_api`` customer can target a different OpenAI-compatible provider.

Revision ID: c4d5e6f7a9b1
Revises: b3c4d5e6f7a9
Create Date: 2026-06-26 15:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "c4d5e6f7a9b1"
down_revision: Union[str, None] = "b3c4d5e6f7a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "oi_customers", sa.Column("api_base_url", sa.String(), nullable=True)
    )
    op.add_column(
        "oi_customers", sa.Column("api_model", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("oi_customers", "api_model")
    op.drop_column("oi_customers", "api_base_url")
