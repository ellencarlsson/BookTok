"""Trending books endpoint."""
import logging
from datetime import date, timedelta

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from models.book import Book
from models.trending import TrendingData

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/trending", tags=["trending"])

_cover_cache = {}


def _fetch_cover(title, author):
    """Fetch book cover URL from Open Library."""
    key = f"{title}|{author}".lower()
    if key in _cover_cache:
        return _cover_cache[key]

    try:
        resp = httpx.get(
            "https://openlibrary.org/search.json",
            params={"q": f"{title} {author}", "limit": 1},
            timeout=5,
        )
        docs = resp.json().get("docs", [])
        if docs and docs[0].get("cover_i"):
            cover_url = f"https://covers.openlibrary.org/b/id/{docs[0]['cover_i']}-M.jpg"
            _cover_cache[key] = cover_url
            return cover_url
    except Exception:
        logger.debug("Failed to fetch cover for %s", title)

    _cover_cache[key] = None
    return None


def _query_trending(db, limit, platform=None, platform_prefix=None, cutoff=None):
    """Query trending books from the database."""
    query = (
        db.query(
            Book.title,
            Book.author,
            func.sum(TrendingData.mention_count).label("mentions"),
            func.sum(TrendingData.trending_score).label("score"),
            func.group_concat(TrendingData.platform.distinct()).label("platforms"),
        )
        .join(TrendingData, Book.id == TrendingData.book_id)
    )

    if cutoff:
        query = query.filter(TrendingData.date >= cutoff)
    if platform:
        query = query.filter(TrendingData.platform == platform)
    elif platform_prefix:
        query = query.filter(TrendingData.platform.like(f"{platform_prefix}%"))

    rows = (
        query
        .group_by(Book.id)
        .order_by(func.sum(TrendingData.trending_score).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "title": row.title,
            "author": row.author,
            "mentions": int(row.mentions),
            "score": round(float(row.score), 2),
            "platforms": sorted(row.platforms.split(",")) if row.platforms else [],
            "cover_url": _fetch_cover(row.title, row.author),
        }
        for row in rows
    ]


@router.get("/this-month")
def this_month(
    limit: int = Query(15, le=50),
    platform: str = Query(None),
    db: Session = Depends(get_db),
):
    """Return popular books from the last 30 days."""
    cutoff = date.today() - timedelta(days=30)
    return _query_trending(db, limit, platform=platform, cutoff=cutoff)


@router.get("/websites")
def websites(
    limit: int = Query(15, le=50),
    source: str = Query(None),
    db: Session = Depends(get_db),
):
    """Return BookTok books from curated website sources."""
    if source:
        return _query_trending(db, limit, platform=f"websites:{source}")
    return _query_trending(db, limit, platform_prefix="websites:")


