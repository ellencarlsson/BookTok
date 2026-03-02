"""Website data collector — scrapes BookTok book lists from curated sources."""
import logging
import re
import time
from collections import defaultdict
from datetime import date

import httpx
from bs4 import BeautifulSoup

from core.database import SessionLocal
from models.book import Book
from models.trending import TrendingData

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_DELAY = 2
GOODREADS_PAGES = 3


def _clean_title(raw):
    """Remove series info and subtitle noise from a title."""
    cleaned = re.sub(r"\s*\([^)]*#\d+[^)]*\)", "", raw)
    cleaned = re.sub(r":\s+A\s+(Novel|Memoir|Story)\b.*$", "", cleaned)
    cleaned = re.sub(r":\s+\d+\w*\s+Anniversary.*$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _get(url, timeout=15):
    """Fetch a URL and return BeautifulSoup."""
    resp = httpx.get(
        url, headers=HEADERS, timeout=timeout, follow_redirects=True,
    )
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def scrape_goodreads_booktok():
    """Scrape Goodreads BookTok shelf — community-ranked by booktok tag count."""
    books = []
    seen = set()

    for page in range(1, GOODREADS_PAGES + 1):
        try:
            url = f"https://www.goodreads.com/shelf/show/booktok?page={page}"
            soup = _get(url)

            for item in soup.select(".leftAlignedImage"):
                title_el = item.select_one("a.bookTitle")
                author_el = item.select_one("a.authorName")
                if not title_el or not author_el:
                    continue

                title = _clean_title(title_el.get_text(strip=True))
                author = author_el.get_text(strip=True)
                if not title or title.lower() in seen:
                    continue

                seen.add(title.lower())
                books.append({"title": title, "author": author})

            time.sleep(REQUEST_DELAY)
        except Exception:
            logger.exception("Failed Goodreads BookTok page %d", page)

    return books


def scrape_hudson_booktok():
    """Scrape Hudson Booksellers BookTok page via img alt texts."""
    books = []
    seen = set()

    try:
        soup = _get("https://hudsonbooksellers.com/booktok")

        for img in soup.select("img[alt]"):
            alt = img.get("alt", "").strip()
            if not alt or len(alt) < 3:
                continue
            if any(skip in alt.lower() for skip in ["logo", "hudson", "banner", "icon"]):
                continue

            title = _clean_title(alt)
            if title.lower() in seen:
                continue
            seen.add(title.lower())
            books.append({"title": title, "author": "Unknown"})
    except Exception:
        logger.exception("Failed Hudson BookTok")

    return books


def collect_website_data():
    """Scrape all BookTok sources and aggregate book appearances."""
    book_sources = defaultdict(lambda: {
        "title": "",
        "author": "",
        "sources": set(),
    })

    scrapers = [
        ("Goodreads BookTok", scrape_goodreads_booktok),
        ("Hudson Booksellers", scrape_hudson_booktok),
    ]

    for name, scraper in scrapers:
        try:
            logger.info("Scraping %s", name)
            books = scraper()
            logger.info("%s: found %d books", name, len(books))
            for book in books:
                key = book["title"].lower()
                agg = book_sources[key]
                agg["title"] = book["title"]
                if book["author"] != "Unknown" or not agg["author"]:
                    agg["author"] = book["author"]
                agg["sources"].add(name)
        except Exception:
            logger.exception("Failed to scrape %s", name)
        time.sleep(REQUEST_DELAY)

    saved = _save_aggregated(book_sources)
    logger.info(
        "Websites done: found %d unique books, saved %d",
        len(book_sources), saved,
    )
    return saved


def _save_aggregated(book_sources):
    """Save aggregated book data — score = number of sources."""
    if not book_sources:
        return 0

    db = SessionLocal()
    saved = 0
    today = date.today()

    try:
        for stats in book_sources.values():
            book = (
                db.query(Book)
                .filter_by(title=stats["title"], author=stats["author"])
                .first()
            )
            if not book:
                book = Book(title=stats["title"], author=stats["author"])
                db.add(book)
                db.flush()

            score = len(stats["sources"])

            existing = (
                db.query(TrendingData)
                .filter_by(book_id=book.id, date=today, platform="websites")
                .first()
            )
            if existing:
                existing.mention_count = score
                existing.trending_score = score
            else:
                db.add(TrendingData(
                    book_id=book.id,
                    date=today,
                    mention_count=score,
                    trending_score=score,
                    platform="websites",
                ))

            saved += 1

        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to save website data")
    finally:
        db.close()

    return saved


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = collect_website_data()
    print(f"Saved {count} books from websites")
