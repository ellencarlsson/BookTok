"""Reddit data collector using public JSON API."""
import logging
import time
from datetime import datetime

import httpx

from core.database import SessionLocal
from models.raw_post import RawPost

logger = logging.getLogger(__name__)

SUBREDDITS = ["Booktokreddit"]
POSTS_PER_PAGE = 100
MIN_UPVOTES = 5
USER_AGENT = "BookTok/1.0 (book discovery platform)"
REQUEST_DELAY = 2


def collect_reddit_data():
    """Fetch recent posts and comments from book subreddits."""
    db = SessionLocal()
    total_saved = 0
    total_comments = 0
    total_skipped = {"low_score": 0, "no_text": 0, "duplicate": 0}

    try:
        for subreddit in SUBREDDITS:
            saved, comments, skipped = _collect_subreddit(db, subreddit)
            total_saved += saved
            total_comments += comments
            for key in total_skipped:
                total_skipped[key] += skipped.get(key, 0)
    except Exception:
        logger.exception("Reddit collection failed")
    finally:
        db.close()

    logger.info(
        "Reddit done: %d posts, %d comments saved, skipped: %s",
        total_saved, total_comments, total_skipped,
    )
    return total_saved + total_comments


def _collect_subreddit(db, subreddit):
    """Collect posts and their comments from a subreddit."""
    saved = 0
    comments_saved = 0
    skipped = {"low_score": 0, "no_text": 0, "duplicate": 0}

    for sort in ["hot", "new", "top"]:
        try:
            params = {"limit": POSTS_PER_PAGE}
            if sort == "top":
                params["t"] = "month"

            url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
            resp = httpx.get(
                url,
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
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                score = post.get("score", 0)
                num_comments = post.get("num_comments", 0)
                permalink = post.get("permalink", "")

                text = f"{title}\n\n{selftext}".strip()

                if len(text) < 15:
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
                    url=f"https://www.reddit.com{permalink}",
                    posted_at=posted_at,
                )
                db.add(raw_post)
                saved += 1

                # Fetch comments for this post
                if num_comments > 0:
                    time.sleep(REQUEST_DELAY)
                    c = _collect_comments(db, subreddit, post_id, permalink)
                    comments_saved += c

            db.commit()
            time.sleep(REQUEST_DELAY)

        except Exception:
            db.rollback()
            logger.exception("Failed r/%s/%s", subreddit, sort)

    logger.info("r/%s: %d posts, %d comments", subreddit, saved, comments_saved)
    return saved, comments_saved, skipped


def _collect_comments(db, subreddit, post_id, permalink):
    """Fetch top-level comments for a post."""
    saved = 0
    try:
        url = f"https://www.reddit.com{permalink}.json"
        resp = httpx.get(
            url,
            params={"limit": 50, "sort": "top"},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
            follow_redirects=True,
        )

        if resp.status_code != 200:
            return 0

        data = resp.json()
        if len(data) < 2:
            return 0

        comments = data[1].get("data", {}).get("children", [])

        for item in comments:
            if item.get("kind") != "t1":
                continue

            comment = item.get("data", {})
            comment_id = comment.get("id", "")
            body = comment.get("body", "")
            score = comment.get("score", 0)

            if len(body) < 10 or score < 2:
                continue

            existing = (
                db.query(RawPost)
                .filter_by(platform="reddit", platform_id=f"c_{comment_id}")
                .first()
            )
            if existing:
                continue

            created_utc = comment.get("created_utc")
            posted_at = datetime.fromtimestamp(created_utc) if created_utc else None

            raw_post = RawPost(
                platform="reddit",
                platform_id=f"c_{comment_id}",
                author=comment.get("author", ""),
                text=body,
                hashtags=[subreddit],
                view_count=0,
                like_count=score,
                comment_count=0,
                share_count=0,
                url=f"https://www.reddit.com{permalink}{comment_id}/",
                posted_at=posted_at,
            )
            db.add(raw_post)
            saved += 1

        db.commit()

    except Exception:
        db.rollback()
        logger.exception("Failed comments for %s", post_id)

    return saved


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = collect_reddit_data()
    print(f"Collected {count} new Reddit posts/comments")
