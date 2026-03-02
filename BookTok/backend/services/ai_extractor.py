"""AI-powered book extraction using Google Gemini REST API."""
import json
import logging
import time

import httpx

from core.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"

EXTRACTION_PROMPT = """You are analyzing a Reddit post about books.
Extract ALL book mentions from the text below.

For each book found, return:
- title: The full book title
- author: The author's name (if identifiable, otherwise "Unknown")
- tropes: List of book tropes mentioned or implied (e.g. "enemies to lovers", "slow burn", "dark romance", "fantasy", "spicy")
- sentiment: "positive", "negative", or "neutral" based on how the poster feels about the book

Important rules:
- Recognize abbreviations: ACOTAR = A Court of Thorns and Roses, ACOSF = A Court of Silver Flames, FW = Fourth Wing, TSOA = The Song of Achilles
- Recognize series references and list the specific book if clear, or the first book in the series
- Only extract actual books, not subreddit names or general topics
- If no books are found, return an empty list

Return ONLY valid JSON in this exact format, no other text:
{"books": [{"title": "...", "author": "...", "tropes": ["..."], "sentiment": "..."}]}

Reddit post:
"""

DELAY_BETWEEN_REQUESTS = 4.5  # ~13 req/min, under 15 req/min free tier limit


def extract_books_with_ai(text):
    """Send post text to Gemini and extract book information."""
    if not text or len(text.strip()) < 10:
        return []

    try:
        payload = {
            "contents": [{"parts": [{"text": EXTRACTION_PROMPT + text[:3000]}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1024,
            },
        }

        resp = httpx.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=30,
        )

        if resp.status_code == 429:
            logger.warning("Rate limited, waiting 60s...")
            time.sleep(60)
            return None

        if resp.status_code != 200:
            logger.warning("Gemini API error %d: %s", resp.status_code, resp.text[:200])
            return None

        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return []

        # Gemini 2.5 may include thinking parts — find the text part
        parts = candidates[0].get("content", {}).get("parts", [])
        raw = ""
        for part in parts:
            if "text" in part:
                raw = part["text"].strip()

        if not raw:
            return []

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            raw = raw.rsplit("```", 1)[0]

        result = json.loads(raw)
        return result.get("books", [])

    except json.JSONDecodeError:
        logger.warning("Failed to parse Gemini response for text: %.80s", text)
        return None
    except Exception:
        logger.exception("Gemini extraction failed for text: %.80s", text)
        return None


def process_unprocessed_posts(db):
    """Process all raw posts that haven't been analyzed by AI yet."""
    from models.raw_post import RawPost

    unprocessed = db.query(RawPost).filter_by(processed=0).all()
    logger.info("Found %d unprocessed posts", len(unprocessed))

    results = {"processed": 0, "books_found": 0, "errors": 0}

    for i, post in enumerate(unprocessed):
        books = extract_books_with_ai(post.text)

        if books is not None:
            post.extracted_books = json.dumps(books)
            post.processed = 1
            results["processed"] += 1
            results["books_found"] += len(books)
        else:
            results["errors"] += 1

        if (i + 1) % 10 == 0:
            db.commit()
            logger.info("Progress: %d/%d processed", i + 1, len(unprocessed))

        time.sleep(DELAY_BETWEEN_REQUESTS)

    db.commit()
    logger.info(
        "AI processing done: %d processed, %d books found, %d errors",
        results["processed"], results["books_found"], results["errors"],
    )
    return results
