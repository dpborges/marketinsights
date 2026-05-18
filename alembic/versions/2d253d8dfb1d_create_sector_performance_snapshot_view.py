"""create sector performance snapshot view

Revision ID: 2d253d8dfb1d
Revises: 56f6ffbc6b80
Create Date: 2026-05-17 20:26:42.373949

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d253d8dfb1d'
down_revision: Union[str, Sequence[str], None] = '56f6ffbc6b80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE VIEW vw_sector_performance_snapshot AS
        SELECT
            d.full_date AS as_of_date,
            s.sector_symbol AS sector,
            f.percent_gain,
            f.relative_strength
        FROM fact_sector_performance_snapshot f
        JOIN dim_date d
            ON f.date_key = d.date_key
        JOIN dim_sector s
            ON f.sector_key = s.sector_key
    """)


def downgrade() -> None:
    op.execute("""
        DROP VIEW IF EXISTS vw_sector_performance_snapshot
    """)
