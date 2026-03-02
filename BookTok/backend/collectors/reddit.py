"""Reddit data collector using public JSON API."""
import logging
import time
from collections import defaultdict
from datetime import date, datetime

import httpx

from core.database import SessionLocal
from models.book import Book
from models.trending import TrendingData
from services.book_extractor import extract_books_from_text

logger = logging.getLogger(__name__)

SUBREDDITS = ["Booktokreddit"]
POSTS_PER_PAGE = 100
MIN_UPVOTES = 5
MIN_COMMENT_SCORE = 2
USER_AGENT = "BookTok/1.0 (book discovery platform)"
REQUEST_DELAY = 2


def collect_reddit_data():
    """Fetch recent posts and comments, aggregate book mentions."""
    book_agg = defaultdict(lambda: {
        "title": "",
        "author": "",
        "mentions": 0,
        "total_likes": 0,
        "total_comments": 0,
    })
    seen_ids = set()

    for subreddit in SUBREDDITS:
        try:
            _scan_subreddit(subreddit, seen_ids, book_agg)
        except Exception:
            logger.exception("Reddit collection failed for r/%s", subreddit)

    saved = _save_aggregated(book_agg)
    logger.info("Reddit done: found %d books, saved %d", len(book_agg), saved)
    return saved


def _scan_subreddit(subreddit, seen_ids, book_agg):
    """Scan posts and comments from a subreddit."""
    for sort in ["hot", "new", "top"]:
        try:
            params = {"limit": POSTS_PER_PAGE}
            if sort == "top":
                params["t"] = "month"

            resp = httpx.get(
                f"https://www.reddit.com/r/{subreddit}/{sort}.json",
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=15,
                follow_redirects=True,
            )

            if resp.status_code != 200:
                logger.warning("Failed r/%s/%s: %d", subreddit, sort, resp.status_code)
                continue

            posts = resp.json().get("data", {}).get("children", [])

            for item in posts:
                post = item.get("data", {})
                post_id = post.get("id", "")

                if post_id in seen_ids:
                    continue
                seen_ids.add(post_id)

                title = post.get("title", "")
                selftext = post.get("selftext", "")
                score = post.get("score", 0)
                permalink = post.get("permalink", "")

                text = f"{title}\n\n{selftext}".strip()
                if len(text) < 15 or score < MIN_UPVOTES:
                    continue

                _extract_to_agg(text, score, post.get("num_comments", 0), book_agg)

                # Scan comments
                if post.get("num_comments", 0) > 0:
                    time.sleep(REQUEST_DELAY)
                    _scan_comments(permalink, seen_ids, book_agg)

            time.sleep(REQUEST_DELAY)

        except Exception:
            logger.exception("Failed r/%s/%s", subreddit, sort)


def _scan_comments(permalink, seen_ids, book_agg):
    """Scan top-level comments for book mentions."""
    try:
        resp = httpx.get(
            f"https://www.reddit.com{permalink}.json",
            params={"limit": 50, "sort": "top"},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
            follow_redirects=True,
        )

        if resp.status_code != 200:
            return

        data = resp.json()
        if len(data) < 2:
            return

        for item in data[1].get("data", {}).get("children", []):
            if item.get("kind") != "t1":
                continue

            comment = item.get("data", {})
            comment_id = comment.get("id", "")

            if comment_id in seen_ids:
                continue
            seen_ids.add(comment_id)

            body = comment.get("body", "")
            score = comment.get("score", 0)

            if len(body) < 10 or score < MIN_COMMENT_SCORE:
                continue

            _extract_to_agg(body, score, 0, book_agg)

    except Exception:
        logger.exception("Failed comments for %s", permalink)


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
                .filter_by(book_id=book.id, date=today, platform="reddit")
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
                    platform="reddit",
                ))

            saved += 1

        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to save aggregated data")
    finally:
        db.close()

    return saved


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = collect_reddit_data()
    print(f"Saved {count} books from Reddit")
