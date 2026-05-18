from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FactSectorPerformanceSnapshot(Base):
    __tablename__ = "fact_sector_performance_snapshot"

    sector_performance_key: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    date_key: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("dim_date.date_key", name="fk_sector_perf_date"),
        nullable=False,
    )

    sector_key: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("dim_sector.sector_key", name="fk_sector_perf_sector"),
        nullable=False,
    )

    percent_gain: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 4),
        nullable=True,
    )

    relative_strength: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 4),
        nullable=True,
    )

    source_system: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    load_datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        UniqueConstraint(
            "date_key",
            "sector_key",
            name="uq_sector_perf_snapshot",
        ),
    )