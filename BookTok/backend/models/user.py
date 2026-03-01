"""User model."""
from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(String(1000))
    created_at = Column(TIMESTAMP, server_default=func.now())

    reviews = relationship("Review", back_populates="user")
    reading_lists = relationship("ReadingList", back_populates="user")
