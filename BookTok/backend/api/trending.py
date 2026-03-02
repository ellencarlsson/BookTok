"""Trending books endpoint."""
import logging
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from models.raw_post import RawPost
from services.book_extractor import extract_trending_books

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/trending", tags=["trending"])

_cover_cache = {}


def _fetch_cover(title, author):
    """Fetch book cover URL from Open Library."""
    key = f"{title}|{author}".lower()
    if key in _cover_cache:
        return _cover_cache[key]

    try:
        query = f"{title} {author}"
        resp = httpx.get(
            "https://openlibrary.org/search.json",
            params={"q": query, "limit": 1},
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


def _add_covers(books):
    for book in books:
        book["cover_url"] = _fetch_cover(book["title"], book["author"])
    return books


@router.get("/this-month")
def this_month(
    limit: int = Query(15, le=50),
    db: Session = Depends(get_db),
):
    """Return popular books from the last 30 days."""
    cutoff = datetime.now() - timedelta(days=30)
    posts = (
        db.query(RawPost)
        .filter(RawPost.posted_at >= cutoff, RawPost.processed == 1)
        .all()
    )
    return _add_covers(extract_trending_books(posts, limit=limit))


@router.get("/all-time")
def all_time(
    limit: int = Query(15, le=50),
    db: Session = Depends(get_db),
):
    """Return all-time popular BookTok books."""
    posts = db.query(RawPost).filter(RawPost.processed == 1).all()
    return _add_covers(extract_trending_books(posts, limit=limit))
