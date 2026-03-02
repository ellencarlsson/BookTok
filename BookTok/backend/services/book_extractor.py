"""Extract trending books from processed raw posts."""
import json
from collections import defaultdict


def extract_trending_books(posts, limit=15):
    """Analyze posts and return top trending books using AI-extracted data."""
    book_stats = defaultdict(lambda: {
        "title": "",
        "author": "",
        "mentions": 0,
        "total_views": 0,
        "total_likes": 0,
        "total_comments": 0,
        "platforms": set(),
        "tropes": set(),
    })

    for post in posts:
        books = _get_books_from_post(post)

        for book in books:
            title = book.get("title", "").strip()
            author = book.get("author", "Unknown").strip()
            if not title:
                continue

            key = title.lower()
            stats = book_stats[key]
            stats["title"] = title
            stats["author"] = author
            stats["mentions"] += 1

            for trope in book.get("tropes", []):
                stats["tropes"].add(trope)

            if isinstance(post, dict):
                stats["total_views"] += post.get("view_count", 0) or 0
                stats["total_likes"] += post.get("like_count", 0) or 0
                stats["total_comments"] += post.get("comment_count", 0) or 0
                stats["platforms"].add(post.get("platform", ""))
            else:
                stats["total_views"] += post.view_count or 0
                stats["total_likes"] += post.like_count or 0
                stats["total_comments"] += post.comment_count or 0
                stats["platforms"].add(post.platform or "")

    ranked = []
    for stats in book_stats.values():
        score = (
            stats["mentions"] * 1000
            + stats["total_likes"] * 0.1
            + stats["total_comments"] * 0.5
        )
        ranked.append({
            "title": stats["title"],
            "author": stats["author"],
            "mentions": stats["mentions"],
            "total_views": stats["total_views"],
            "total_likes": stats["total_likes"],
            "total_comments": stats["total_comments"],
            "platforms": sorted(stats["platforms"]),
            "tropes": sorted(stats["tropes"]),
            "score": round(score, 2),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:limit]


def _get_books_from_post(post):
    """Get AI-extracted books from a post."""
    if isinstance(post, dict):
        raw = post.get("extracted_books")
    else:
        raw = post.extracted_books

    if not raw:
        return []

    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []
    return raw
