# BookTok

A community platform for book lovers — powered by AI that monitors TikTok, Reddit, Instagram and Pinterest to surface trending books, tropes, and reviews in real time.

## What is BookTok?

BookTok is the massive book community on TikTok with over 200 billion views. But the community has no home outside TikTok. This platform changes that.

## Features

- **Trending Books** — AI agents scan TikTok and Reddit daily to find which books are blowing up right now
- **Trope Search** — Find books by tropes (enemies to lovers, found family, slow burn) instead of traditional genres
- **Community Reviews** — Rate, review, and create reading lists
- **Book Pages** — Every book has a page with trending TikTok videos, tropes, sentiment score, and community reviews
- **AI-Powered Discovery** — "I liked Fourth Wing and The Love Hypothesis — what should I read next?"

## Tech Stack

- **Frontend:** React
- **Backend:** Python (FastAPI)
- **Database:** MariaDB (MySQL) on Plesk
- **AI Pipeline:** OpenAI/Claude API for book extraction, trope tagging, and sentiment analysis
- **Data Sources:** TikTok Research API, Reddit API
- **Scheduling:** Daily data collection via cron jobs

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Python (FastAPI) — Backend + AI Pipeline            │
│                                                      │
│  [Cron daily]                                        │
│    TikTok API  ──→  LLM Analysis  ──→  MariaDB      │
│    Reddit API  ──→  LLM Analysis  ──→  MariaDB      │
│                                                      │
│  [REST API]                                          │
│    /api/books, /api/tropes, /api/trending            │
│    /api/reviews, /api/lists, /api/search             │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
              React Frontend
```
