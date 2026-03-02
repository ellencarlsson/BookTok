"""YouTube Shorts BookTok data collector using YouTube Data API v3."""
import logging
import time
from collections import defaultdict
from datetime import date, datetime, timedelta

import httpx

from core.config import YOUTUBE_API_KEY
from core.database import SessionLocal
from models.book import Book
from models.trending import TrendingData
from services.book_extractor import extract_books_from_text

logger = logging.getLogger(__name__)

API_BASE = "https://www.googleapis.com/youtube/v3"
SEARCH_QUERIES = [
    "booktok book recommendations",
    "booktok must read|booktok books",
]
MIN_VIEW_COUNT = 1_000
MIN_LIKE_COUNT = 10
MAX_COMMENT_PAGES = 10
REQUEST_DELAY = 0.5
MAX_AGE_DAYS = 30


def collect_youtube_data():
    """Fetch recent BookTok Shorts and comments, aggregate book mentions."""
    if not YOUTUBE_API_KEY:
        logger.warning("YOUTUBE_API_KEY not set, skipping YouTube collection")
        return 0

    book_agg = defaultdict(lambda: {
        "title": "",
        "author": "",
        "mentions": 0,
        "total_likes": 0,
        "total_comments": 0,
    })
    seen_ids = set()

    for query in SEARCH_QUERIES:
        try:
            video_ids = _search_shorts(query, seen_ids)
            if not video_ids:
                continue

            videos = _get_video_details(video_ids)
            for video in videos:
                _process_video(video, book_agg)

        except Exception:
            logger.exception("YouTube collection failed for query: %s", query)

        time.sleep(REQUEST_DELAY)

    saved = _save_aggregated(book_agg)
    logger.info("YouTube done: found %d books, saved %d", len(book_agg), saved)
    return saved


def _search_shorts(query, seen_ids):
    """Search for BookTok Shorts and return new video IDs."""
    published_after = (datetime.utcnow() - timedelta(days=MAX_AGE_DAYS)).isoformat() + "Z"

    resp = httpx.get(
        f"{API_BASE}/search",
        params={
            "part": "id",
            "q": query,
            "type": "video",
            "videoDuration": "short",
            "maxResults": 50,
            "order": "relevance",
            "publishedAfter": published_after,
            "key": YOUTUBE_API_KEY,
        },
        timeout=15,
    )

    if resp.status_code != 200:
        logger.warning("YouTube search failed (%d): %s", resp.status_code, resp.text[:200])
        return []

    video_ids = []
    for item in resp.json().get("items", []):
        vid = item.get("id", {}).get("videoId")
        if vid and vid not in seen_ids:
            seen_ids.add(vid)
            video_ids.append(vid)

    return video_ids


def _get_video_details(video_ids):
    """Fetch video details in batches of 50."""
    videos = []

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        resp = httpx.get(
            f"{API_BASE}/videos",
            params={
                "part": "snippet,statistics",
                "id": ",".join(batch),
                "key": YOUTUBE_API_KEY,
            },
            timeout=15,
        )

        if resp.status_code != 200:
            logger.warning("YouTube videos.list failed (%d)", resp.status_code)
            continue

        for item in resp.json().get("items", []):
            stats = item.get("statistics", {})
            views = int(stats.get("viewCount", "0"))
            likes = int(stats.get("likeCount", "0"))

            if views < MIN_VIEW_COUNT or likes < MIN_LIKE_COUNT:
                continue

            videos.append({
                "id": item["id"],
                "title": item["snippet"]["title"],
                "description": item["snippet"].get("description", ""),
                "likes": likes,
                "comments": int(stats.get("commentCount", "0")),
            })

        time.sleep(REQUEST_DELAY)

    return videos


def _process_video(video, book_agg):
    """Extract books from video title, description, and comments."""
    text = f"{video['title']}\n\n{video['description']}".strip()
    _extract_to_agg(text, video["likes"], video["comments"], book_agg)

    if video["comments"] > 0:
        _fetch_all_comments(video["id"], book_agg)


def _fetch_all_comments(video_id, book_agg):
    """Paginate through all comment threads for a video."""
    page_token = None

    for _ in range(MAX_COMMENT_PAGES):
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,
            "order": "relevance",
            "textFormat": "plainText",
            "key": YOUTUBE_API_KEY,
        }
        if page_token:
            params["pageToken"] = page_token

        try:
            resp = httpx.get(
                f"{API_BASE}/commentThreads",
                params=params,
                timeout=15,
            )
        except Exception:
            logger.exception("Comment fetch error for %s", video_id)
            break

        if resp.status_code == 403:
            logger.debug("Comments disabled for %s", video_id)
            break
        if resp.status_code != 200:
            logger.warning("CommentThreads failed (%d) for %s", resp.status_code, video_id)
            break

        data = resp.json()
        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            body = snippet.get("textDisplay", "")
            likes = int(snippet.get("likeCount", 0))

            if len(body) >= 10:
                _extract_to_agg(body, likes, 0, book_agg)

        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(REQUEST_DELAY)


def _extract_to_agg(text, likes, comments, book_agg):
    """Extract books from text and add to aggregation."""
    for book in extract_books_from_text(text):
        key = book["title"].lower()
        agg = book_agg[key]
        agg["title"] = book["title"]
        agg["author"] = book["author"]
        agg["mentions"] += 1
        agg["total_likes"] += likes
        agg["total_comments"] += comments


def _save_aggregated(book_agg):
    """Save aggregated book data to books + trending_data tables."""
    if not book_agg:
        return 0

    db = SessionLocal()
    saved = 0
    today = date.today()

    try:
        for stats in book_agg.values():
            book = (
                db.query(Book)
                .filter_by(title=stats["title"], author=stats["author"])
                .first()
            )
            if not book:
                book = Book(title=stats["title"], author=stats["author"])
                db.add(book)
                db.flush()

            score = (
                stats["mentions"] * 1000
                + stats["total_likes"] * 0.1
                + stats["total_comments"] * 0.5
            )

            existing = (
                db.query(TrendingData)
                .filter_by(book_id=book.id, date=today, platform="youtube")
                .first()
            )
            if existing:
                existing.mention_count = stats["mentions"]
                existing.trending_score = score
            else:
                db.add(TrendingData(
                    book_id=book.id,
                    date=today,
                    mention_count=stats["mentions"],
                    trending_score=score,
                    platform="youtube",
                ))

            saved += 1

        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to save YouTube aggregated data")
    finally:
        db.close()

    return saved


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = collect_youtube_data()
    print(f"Saved {count} books from YouTube")
