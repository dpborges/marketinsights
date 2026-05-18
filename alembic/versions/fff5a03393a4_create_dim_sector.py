"""create dim sector

Revision ID: fff5a03393a4
Revises: c2b39704ef6f
Create Date: 2026-05-17 19:26:27.436304

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fff5a03393a4'
down_revision: Union[str, Sequence[str], None] = 'c2b39704ef6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dim_sector",
        sa.Column("sector_key", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("sector_symbol", sa.String(length=20), nullable=False),
        sa.Column("sector_name", sa.String(length=100), nullable=True),
        sa.Column("asset_class", sa.String(length=50), nullable=True),
        sa.Column("index_family", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("effective_start_date", sa.Date(), nullable=True),
        sa.Column("effective_end_date", sa.Date(), nullable=True),
    )

    op.create_unique_constraint(
        "uq_dim_sector_sector_symbol",
        "dim_sector",
        ["sector_symbol"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_dim_sector_sector_symbol",
        "dim_sector",
        type_="unique",
    )
    op.drop_table("dim_sector")