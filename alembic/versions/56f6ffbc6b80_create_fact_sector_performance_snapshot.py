"""create fact sector performance snapshot

Revision ID: 56f6ffbc6b80
Revises: fff5a03393a4
Create Date: 2026-05-17 20:00:43.363371

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '56f6ffbc6b80'
down_revision: Union[str, Sequence[str], None] = 'fff5a03393a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fact_sector_performance_snapshot",
        sa.Column(
            "sector_performance_key",
            sa.BigInteger(),
            sa.Identity(always=True),
            primary_key=True,
        ),
        sa.Column("date_key", sa.Integer(), nullable=False),
        sa.Column("sector_key", sa.BigInteger(), nullable=False),
        sa.Column("percent_gain", sa.Numeric(9, 4), nullable=True),
        sa.Column("relative_strength", sa.Numeric(9, 4), nullable=True),
        sa.Column("source_system", sa.String(length=50), nullable=True),
        sa.Column(
            "load_datetime",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["date_key"],
            ["dim_date.date_key"],
            name="fk_sector_perf_date",
        ),
        sa.ForeignKeyConstraint(
            ["sector_key"],
            ["dim_sector.sector_key"],
            name="fk_sector_perf_sector",
        ),
        sa.UniqueConstraint(
            "date_key",
            "sector_key",
            name="uq_sector_perf_snapshot",
        ),
    )


def downgrade() -> None:
    op.drop_table("fact_sector_performance_snapshot")