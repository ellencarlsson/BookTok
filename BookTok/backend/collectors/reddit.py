"""Reddit data collector using public JSON API."""
import logging
from datetime import datetime

import httpx

from core.database import SessionLocal
from models.raw_post import RawPost

logger = logging.getLogger(__name__)

SUBREDDITS = [
    "BookTok",
    "RomanceBooks",
    "suggestmeabook",
    "Fantasy",
    "books",
]

POSTS_PER_SUBREDDIT = 50
MIN_UPVOTES = 10
USER_AGENT = "BookTok/1.0 (book discovery platform)"


def collect_reddit_data():
    """Fetch recent posts from book subreddits and store as raw posts."""
    db = SessionLocal()
    total_saved = 0
    total_skipped = {"low_score": 0, "no_text": 0, "duplicate": 0}

    try:
        for subreddit in SUBREDDITS:
            saved, skipped = _collect_subreddit(db, subreddit)
            total_saved += saved
            for key in total_skipped:
                total_skipped[key] += skipped.get(key, 0)
    except Exception:
        logger.exception("Reddit collection failed")
    finally:
        db.close()

    logger.info(
        "Reddit collection done: %d saved, skipped: %s",
        total_saved, total_skipped,
    )
    return total_saved


def _collect_subreddit(db, subreddit):
    """Collect posts from a single subreddit."""
    saved = 0
    skipped = {"low_score": 0, "no_text": 0, "duplicate": 0}

    for sort in ["hot", "new"]:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
            resp = httpx.get(
                url,
                params={"limit": POSTS_PER_SUBREDDIT},
                headers={"User-Agent": USER_AGENT},
                timeout=15,
                follow_redirects=True,
            )

            if resp.status_code != 200:
                logger.warning("Failed to fetch r/%s/%s: %d", subreddit, sort, resp.status_code)
                continue

            posts = resp.json().get("data", {}).get("children", [])

            for item in posts:
                post = item.get("data", {})
                post_id = post.get("id", "")
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                score = post.get("score", 0)
                num_comments = post.get("num_comments", 0)

                text = f"{title}\n\n{selftext}".strip()

                if len(text) < 20:
                    skipped["no_text"] += 1
                    continue

                if score < MIN_UPVOTES:
                    skipped["low_score"] += 1
                    continue

                existing = (
                    db.query(RawPost)
                    .filter_by(platform="reddit", platform_id=post_id)
                    .first()
                )
                if existing:
                    skipped["duplicate"] += 1
                    continue

                created_utc = post.get("created_utc")
                posted_at = datetime.fromtimestamp(created_utc) if created_utc else None

                raw_post = RawPost(
                    platform="reddit",
                    platform_id=post_id,
                    author=post.get("author", ""),
                    text=text,
                    hashtags=[subreddit],
                    view_count=0,
                    like_count=score,
                    comment_count=num_comments,
                    share_count=0,
                    url=f"https://www.reddit.com{post.get('permalink', '')}",
                    posted_at=posted_at,
                )
                db.add(raw_post)
                saved += 1

            db.commit()

        except Exception:
            db.rollback()
            logger.exception("Failed to collect r/%s/%s", subreddit, sort)

    logger.info("r/%s: saved %d, skipped %s", subreddit, saved, skipped)
    return saved, skipped


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = collect_reddit_data()
    print(f"Collected {count} new Reddit posts")
