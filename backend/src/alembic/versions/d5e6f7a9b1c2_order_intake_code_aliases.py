"""order_intake learned code aliases

Adds ``oi_code_aliases``: the learned ``(customer, their printed code) ->
internal AE code`` map. Each operator inline edit teaches one row, so repeated
codes from the same customer resolve deterministically next time (auto-improving
reconciliation, no LLM needed for known codes).

Revision ID: d5e6f7a9b1c2
Revises: c4d5e6f7a9b1
Create Date: 2026-06-26 17:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "d5e6f7a9b1c2"
down_revision: Union[str, None] = "c4d5e6f7a9b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "oi_code_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_code", sa.String(), nullable=False),
        sa.Column("customer_part_code", sa.String(), nullable=False),
        sa.Column("internal_code", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "customer_code", "customer_part_code", name="uq_oi_code_alias"
        ),
    )
    op.create_index(
        "ix_oi_code_aliases_customer_code",
        "oi_code_aliases",
        ["customer_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_oi_code_aliases_customer_code", table_name="oi_code_aliases"
    )
    op.drop_table("oi_code_aliases")
