from .base import Base
from sqlalchemy import Column, Integer, String, Boolean, Date

class DimDate(Base):
    __tablename__ = "dim_date"

    date_key = Column(Integer, primary_key=True)
    full_date = Column(Date, nullable=False)

    calendar_year = Column(Integer, nullable=False)
    calendar_quarter = Column(Integer, nullable=False)
    calendar_month = Column(Integer, nullable=False)
    calendar_month_name = Column(String(20))

    day_of_month = Column(Integer, nullable=False)
    day_of_week = Column(Integer)
    day_name = Column(String(20))

    week_of_year = Column(Integer)

    is_month_end = Column(Boolean)
    is_quarter_end = Column(Boolean)
    is_year_end = Column(Boolean)