from decimal import Decimal
from datetime import date

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class VwSectorPerformanceSnapshot(Base):
    __tablename__ = "vw_sector_performance_snapshot"

    # Views don't usually have natural PKs, but SQLAlchemy expects one
    as_of_date: Mapped[date] = mapped_column(Date, primary_key=True)
    sector: Mapped[str] = mapped_column(String(20), primary_key=True)

    percent_gain: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 4)
    )

    relative_strength: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 4)
    )