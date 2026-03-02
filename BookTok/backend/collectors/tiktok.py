"""TikTok data collector using unofficial TikTokApi."""
import asyncio
import logging
from datetime import datetime

from TikTokApi import TikTokApi

from core.config import TIKTOK_MS_TOKEN
from core.database import SessionLocal
from models.raw_post import RawPost

logger = logging.getLogger(__name__)

# --- Collection rules ---

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


def _get_monthly_hashtags():
    """Generate monthly TBR hashtags based on current month."""
    month = MONTH_NAMES[datetime.now().month - 1]
    return [f"{month}tbr", f"{month}bookhaul", f"{month}wrapup"]

VIDEOS_PER_HASHTAG = 50
MIN_VIEWS = 2_000


async def collect_tiktok_data():
    """Fetch recent BookTok videos and store as raw posts."""
    db = SessionLocal()
    total_saved = 0
    total_skipped = {"low_views": 0, "no_text": 0, "duplicate": 0}

    try:
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[TIKTOK_MS_TOKEN],
                num_sessions=1,
                sleep_after=3,
            )

            all_hashtags = BOOKTOK_HASHTAGS + _get_monthly_hashtags()
            for tag_name in all_hashtags:
                logger.info("Collecting videos for #%s", tag_name)
                saved, skipped = await _collect_hashtag(api, db, tag_name)
                total_saved += saved
                for key in total_skipped:
                    total_skipped[key] += skipped.get(key, 0)

    except Exception:
        logger.exception("TikTok collection failed")
    finally:
        db.close()

    logger.info(
        "TikTok collection done: %d saved, skipped: %s",
        total_saved,
        total_skipped,
    )
    return total_saved


async def _collect_hashtag(api, db, tag_name):
    """Collect videos for a single hashtag with filtering."""
    saved = 0
    skipped = {"low_views": 0, "no_text": 0, "duplicate": 0}

    try:
        hashtag = api.hashtag(name=tag_name)

        async for video in hashtag.videos(count=VIDEOS_PER_HASHTAG):
            data = video.as_dict
            video_id = str(data.get("id", ""))
            stats = data.get("stats", {})
            desc = data.get("desc", "")
            create_time = data.get("createTime")

            # Filter: skip videos with no text
            if not desc or len(desc.strip()) < 10:
                skipped["no_text"] += 1
                continue

            posted_at = None
            if create_time:
                posted_at = datetime.fromtimestamp(int(create_time))

            # Filter: skip low engagement
            view_count = stats.get("playCount", 0)
            if view_count < MIN_VIEWS:
                skipped["low_views"] += 1
                continue

            # Filter: skip duplicates
            existing = (
                db.query(RawPost)
                .filter_by(platform="tiktok", platform_id=video_id)
                .first()
            )
            if existing:
                skipped["duplicate"] += 1
                continue

            author_info = data.get("author", {})
            hashtags = [h.get("hashtagName", "") for h in data.get("challenges", [])]

            # Combine description + hashtags for better text matching
            hashtag_text = " ".join(f"#{h}" for h in hashtags if h)
            full_text = f"{desc}\n{hashtag_text}".strip()

            raw_post = RawPost(
                platform="tiktok",
                platform_id=video_id,
                author=author_info.get("uniqueId", ""),
                text=full_text,
                hashtags=hashtags,
                view_count=view_count,
                like_count=stats.get("diggCount", 0),
                comment_count=stats.get("commentCount", 0),
                share_count=stats.get("shareCount", 0),
                url=f"https://www.tiktok.com/@{author_info.get('uniqueId', '')}/video/{video_id}",
                posted_at=posted_at,
            )
            db.add(raw_post)
            saved += 1

        db.commit()
        logger.info(
            "#%s: saved %d, skipped %s",
            tag_name, saved, skipped,
        )

    except Exception:
        db.rollback()
        logger.exception("Failed to collect #%s", tag_name)

    return saved, skipped


def run_tiktok_collector():
    """Sync entry point for running the TikTok collector."""
    return asyncio.run(collect_tiktok_data())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = run_tiktok_collector()
    print(f"Collected {count} new TikTok posts")
