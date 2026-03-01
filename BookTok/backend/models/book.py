"""Book and BookTrope models."""
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    author = Column(String(300), nullable=False)
    cover_image = Column(String(1000))
    description = Column(Text)
    isbn = Column(String(13))
    google_books_id = Column(String(50))
    average_rating = Column(Numeric(3, 2), default=0.00)
    total_reviews = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    tropes = relationship("Trope", secondary="book_tropes", back_populates="books")
    reviews = relationship("Review", back_populates="book")
    trending_data = relationship("TrendingData", back_populates="book")


class BookTrope(Base):
    __tablename__ = "book_tropes"

    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
    trope_id = Column(Integer, ForeignKey("tropes.id", ondelete="CASCADE"), primary_key=True)
