"""TikTok data collector using unofficial TikTokApi."""
import asyncio
import logging
from datetime import datetime

from TikTokApi import TikTokApi

from core.config import TIKTOK_MS_TOKEN
from core.database import SessionLocal
from models.raw_post import RawPost

logger = logging.getLogger(__name__)

BOOKTOK_HASHTAGS = [
    "BookTok",
    "bookreccomendations",
    "bookrecs",
    "romancebooks",
    "fantasybooktok",
    "bookreviews",
    "mustreadbooks",
]

VIDEOS_PER_HASHTAG = 20


async def collect_tiktok_data():
    """Fetch recent BookTok videos and store as raw posts."""
    db = SessionLocal()
    total_saved = 0

    try:
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[TIKTOK_MS_TOKEN],
                num_sessions=1,
                sleep_after=3,
            )

            for tag_name in BOOKTOK_HASHTAGS:
                logger.info("Collecting videos for #%s", tag_name)
                saved = await _collect_hashtag(api, db, tag_name)
                total_saved += saved

    except Exception:
        logger.exception("TikTok collection failed")
    finally:
        db.close()

    logger.info("TikTok collection done: %d new posts saved", total_saved)
    return total_saved


async def _collect_hashtag(api, db, tag_name):
    """Collect videos for a single hashtag."""
    saved = 0
    try:
        hashtag = api.hashtag(name=tag_name)

        async for video in hashtag.videos(count=VIDEOS_PER_HASHTAG):
            data = video.as_dict
            video_id = str(data.get("id", ""))

            existing = (
                db.query(RawPost)
                .filter_by(platform="tiktok", platform_id=video_id)
                .first()
            )
            if existing:
                continue

            stats = data.get("stats", {})
            author_info = data.get("author", {})
            hashtags = [h.get("hashtagName", "") for h in data.get("challenges", [])]
            desc = data.get("desc", "")
            create_time = data.get("createTime")

            posted_at = None
            if create_time:
                posted_at = datetime.fromtimestamp(int(create_time))

            raw_post = RawPost(
                platform="tiktok",
                platform_id=video_id,
                author=author_info.get("uniqueId", ""),
                text=desc,
                hashtags=hashtags,
                view_count=stats.get("playCount", 0),
                like_count=stats.get("diggCount", 0),
                comment_count=stats.get("commentCount", 0),
                share_count=stats.get("shareCount", 0),
                url=f"https://www.tiktok.com/@{author_info.get('uniqueId', '')}/video/{video_id}",
                posted_at=posted_at,
            )
            db.add(raw_post)
            saved += 1

        db.commit()
        logger.info("#%s: saved %d new videos", tag_name, saved)

    except Exception:
        db.rollback()
        logger.exception("Failed to collect #%s", tag_name)

    return saved


def run_tiktok_collector():
    """Sync entry point for running the TikTok collector."""
    return asyncio.run(collect_tiktok_data())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = run_tiktok_collector()
    print(f"Collected {count} new TikTok posts")
