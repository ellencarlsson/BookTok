"""Collection endpoints for triggering and viewing scraped data."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from models.raw_post import RawPost
from collectors.reddit import collect_reddit_data
from services.ai_extractor import process_unprocessed_posts

router = APIRouter(prefix="/api/collect", tags=["collect"])


@router.post("/reddit")
def run_reddit_collector():
    """Trigger Reddit data collection."""
    count = collect_reddit_data()
    return {"saved": count}


@router.post("/extract-books")
def extract_books(db: Session = Depends(get_db)):
    """Run AI extraction on all unprocessed posts."""
    return process_unprocessed_posts(db)


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
            "author": p.author,
            "text": p.text[:200],
            "like_count": p.like_count,
            "comment_count": p.comment_count,
            "url": p.url,
            "posted_at": str(p.posted_at) if p.posted_at else None,
            "processed": p.processed,
        }
        for p in posts
    ]


@router.get("/stats")
def collection_stats(db: Session = Depends(get_db)):
    """Get collection statistics."""
    total = db.query(RawPost).count()
    reddit = db.query(RawPost).filter_by(platform="reddit").count()
    processed = db.query(RawPost).filter_by(processed=1).count()
    unprocessed = db.query(RawPost).filter_by(processed=0).count()
    return {
        "total": total,
        "reddit": reddit,
        "processed": processed,
        "unprocessed": unprocessed,
    }
