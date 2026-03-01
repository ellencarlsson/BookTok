"""Trope model."""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class Trope(Base):
    __tablename__ = "tropes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    books = relationship("Book", secondary="book_tropes", back_populates="tropes")
