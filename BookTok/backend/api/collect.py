"""Collection endpoints for triggering and viewing scraped data."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from models.raw_post import RawPost

router = APIRouter(prefix="/api/collect", tags=["collect"])


@router.get("/raw-posts")
def list_raw_posts(
    platform: str = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """List collected raw posts, optionally filtered by platform."""
    query = db.query(RawPost).order_by(RawPost.collected_at.desc())
    if platform:
        query = query.filter(RawPost.platform == platform)
    posts = query.offset(offset).limit(limit).all()
    return [
        {
            "id": p.id,
            "platform": p.platform,
            "platform_id": p.platform_id,
            "author": p.author,
            "text": p.text,
            "hashtags": p.hashtags,
            "view_count": p.view_count,
            "like_count": p.like_count,
            "comment_count": p.comment_count,
            "share_count": p.share_count,
            "url": p.url,
            "posted_at": str(p.posted_at) if p.posted_at else None,
            "collected_at": str(p.collected_at) if p.collected_at else None,
            "processed": p.processed,
        }
        for p in posts
    ]


@router.get("/stats")
def collection_stats(db: Session = Depends(get_db)):
    """Get collection statistics per platform."""
    total = db.query(RawPost).count()
    tiktok = db.query(RawPost).filter_by(platform="tiktok").count()
    reddit = db.query(RawPost).filter_by(platform="reddit").count()
    youtube = db.query(RawPost).filter_by(platform="youtube").count()
    unprocessed = db.query(RawPost).filter_by(processed=0).count()
    return {
        "total": total,
        "by_platform": {"tiktok": tiktok, "reddit": reddit, "youtube": youtube},
        "unprocessed": unprocessed,
    }
