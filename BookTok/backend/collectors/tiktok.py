"""TikTok data collector using unofficial TikTokApi."""
import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta, date

from TikTokApi import TikTokApi

from core.config import TIKTOK_MS_TOKEN
from core.database import SessionLocal
from models.book import Book
from models.trending import TrendingData
from services.book_extractor import extract_books_from_text

logger = logging.getLogger(__name__)

MONTH_NAMES = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]

BOOKTOK_HASHTAGS = [
    "BookTok",
    "bookrecs",
    "bookreccomendations",
    "romancebooks",
    "fantasybooktok",
    "mustreadbooks",
    "spicybooktok",
    "darkromance",
    "booktoker",
    "bookreview",
    "CurrentlyReading",
    "BookTokChallenge",
    "enemiestolovers",
]

VIDEOS_PER_HASHTAG = 200
MIN_VIEWS = 2_000
MAX_AGE_DAYS = 30


def _get_monthly_hashtags():
    """Generate monthly TBR hashtags based on current month."""
    month = MONTH_NAMES[datetime.now().month - 1]
    return [f"{month}tbr", f"{month}bookhaul", f"{month}wrapup"]


async def collect_tiktok_data():
    """Fetch recent BookTok videos and aggregate book mentions."""
    book_agg = defaultdict(lambda: {
        "title": "",
        "author": "",
        "mentions": 0,
        "total_likes": 0,
        "total_comments": 0,
    })
    total_videos = 0
    seen_ids = set()

    try:
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[TIKTOK_MS_TOKEN],
                num_sessions=1,
                sleep_after=3,
            )

            all_hashtags = BOOKTOK_HASHTAGS + _get_monthly_hashtags()
            cutoff = datetime.now() - timedelta(days=MAX_AGE_DAYS)

            for tag_name in all_hashtags:
                logger.info("Scanning #%s", tag_name)
                count = await _scan_hashtag(
                    api, tag_name, cutoff, seen_ids, book_agg,
                )
                total_videos += count

    except Exception:
        logger.exception("TikTok collection failed")

    saved = _save_aggregated(book_agg)
    logger.info(
        "TikTok done: scanned %d videos, found %d books, saved %d",
        total_videos, len(book_agg), saved,
    )
    return saved


async def _scan_hashtag(api, tag_name, cutoff, seen_ids, book_agg):
    """Scan videos for a hashtag and aggregate book mentions."""
    count = 0
    try:
        hashtag = api.hashtag(name=tag_name)

        async for video in hashtag.videos(count=VIDEOS_PER_HASHTAG):
            data = video.as_dict
            video_id = str(data.get("id", ""))

            if video_id in seen_ids:
                continue
            seen_ids.add(video_id)

            desc = data.get("desc", "")
            if not desc or len(desc.strip()) < 10:
                continue

            create_time = data.get("createTime")
            if create_time:
                if datetime.fromtimestamp(int(create_time)) < cutoff:
                    continue

            stats = data.get("stats", {})
            if stats.get("playCount", 0) < MIN_VIEWS:
                continue

            count += 1
            hashtags = [h.get("hashtagName", "") for h in data.get("challenges", [])]
            hashtag_text = " ".join(f"#{h}" for h in hashtags if h)
            full_text = f"{desc}\n{hashtag_text}".strip()

            for book in extract_books_from_text(full_text):
                key = book["title"].lower()
                agg = book_agg[key]
                agg["title"] = book["title"]
                agg["author"] = book["author"]
                agg["mentions"] += 1
                agg["total_likes"] += stats.get("diggCount", 0)
                agg["total_comments"] += stats.get("commentCount", 0)

    except Exception:
        logger.exception("Failed to scan #%s", tag_name)

    return count


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
                .filter_by(book_id=book.id, date=today, platform="tiktok")
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
                    platform="tiktok",
                ))

            saved += 1

        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to save aggregated data")
    finally:
        db.close()

    return saved


def run_tiktok_collector():
    """Sync entry point for running the TikTok collector."""
    return asyncio.run(collect_tiktok_data())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = run_tiktok_collector()
    print(f"Saved {count} books from TikTok")
