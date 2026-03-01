"""RawPost model for storing scraped social media data before AI processing."""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, JSON
from sqlalchemy.sql import func

from core.database import Base


class RawPost(Base):
    __tablename__ = "raw_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False)
    platform_id = Column(String(200), nullable=False, unique=True)
    author = Column(String(200))
    text = Column(Text)
    hashtags = Column(JSON)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    url = Column(String(1000))
    posted_at = Column(TIMESTAMP)
    collected_at = Column(TIMESTAMP, server_default=func.now())
    processed = Column(Integer, default=0)
