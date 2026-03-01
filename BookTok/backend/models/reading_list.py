"""ReadingList and ReadingListBook models."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class ReadingList(Base):
    __tablename__ = "reading_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="reading_lists")
    books = relationship("Book", secondary="reading_list_books")


class ReadingListBook(Base):
    __tablename__ = "reading_list_books"

    reading_list_id = Column(Integer, ForeignKey("reading_lists.id", ondelete="CASCADE"), primary_key=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(TIMESTAMP, server_default=func.now())
