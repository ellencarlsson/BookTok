"""Validate book titles against Open Library API."""
import logging

import httpx

logger = logging.getLogger(__name__)

_cache = {}


def validate_book(title, author):
    """Check if a book exists in Open Library. Returns (title, author) or None."""
    key = f"{title}|{author}".lower()
    if key in _cache:
        return _cache[key]

    result = _search_open_library(title, author)
    _cache[key] = result
    return result


def _search_open_library(title, author):
    """Search Open Library for a book match."""
    try:
        resp = httpx.get(
            "https://openlibrary.org/search.json",
            params={"title": title, "author": author, "limit": 3},
            timeout=5,
        )
        if resp.status_code != 200:
            return None

        docs = resp.json().get("docs", [])
        if not docs:
            return None

        for doc in docs:
            ol_title = doc.get("title", "")
            ol_authors = doc.get("author_name", [])
            if _titles_match(title, ol_title):
                ol_author = ol_authors[0] if ol_authors else author
                return {"title": ol_title, "author": ol_author}

    except Exception:
        logger.debug("Open Library lookup failed for '%s'", title)

    return None


def _titles_match(candidate, ol_title):
    """Check if candidate title matches Open Library title."""
    c = candidate.lower().strip()
    o = ol_title.lower().strip()
    # Exact match or candidate ends with the OL title (e.g. "storytelling of Say Nothing" contains "say nothing")
    return c == o or c.endswith(o) or o.endswith(c)
