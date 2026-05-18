from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    Date
)
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class DimSector(Base):
    __tablename__ = "dim_sector"

    sector_key: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True
    )

    sector_symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True
    )

    sector_name: Mapped[str] = mapped_column(
        String(100)
    )

    asset_class: Mapped[str] = mapped_column(
        String(50)
    )

    index_family: Mapped[str] = mapped_column(
        String(100)
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    effective_start_date: Mapped[Date] = mapped_column(
        Date
    )

    effective_end_date: Mapped[Date] = mapped_column(
        Date
    )