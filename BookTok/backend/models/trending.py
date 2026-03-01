"""TrendingData model."""
from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class TrendingData(Base):
    __tablename__ = "trending_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    mention_count = Column(Integer, default=0)
    sentiment_score = Column(Numeric(3, 2), default=0.00)
    trending_score = Column(Numeric(8, 2), default=0.00)
    platform = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    book = relationship("Book", back_populates="trending_data")
