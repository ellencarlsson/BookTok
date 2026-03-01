# BookTok — Project Plan

## Problem

BookTok is the biggest book community in the world (200B+ views on TikTok). But:
- There is no dedicated platform for the community outside TikTok
- Goodreads is outdated and not BookTok-focused
- StoryGraph is better but has no TikTok integration
- Trope Trove has trope search but no community or trends
- No platform shows what's trending on BookTok RIGHT NOW

## Solution

An international community platform that combines:
1. AI-powered trend monitoring from social media
2. Trope-based book discovery
3. Community features (reviews, lists, discussions)

## AI Pipeline

### Data Collection (runs daily)

#### TikTok (primary source)
- Apply for TikTok Research API access
- Query videos by hashtags: #booktok, #bookish, #romancebooks, #fantasybooktok, #bookrecommendations, #bookclub
- Collect: video description, hashtags, likes, shares, comments, date

#### Reddit
- Use Reddit API (free, open)
- Subreddits: r/booktok, r/romancebooks, r/Fantasy, r/books, r/suggestmeabook
- Collect: post title, body, comments, upvotes

#### Instagram & Pinterest (future)
- Add as data sources once core pipeline works

### AI Processing

For each collected post/video, an LLM analyzes:

1. **Book extraction** — Which book(s) are mentioned? Match against book database (Google Books API / Open Library API)
2. **Trope tagging** — What tropes are mentioned or implied? (enemies to lovers, slow burn, found family, forced proximity, etc.)
3. **Sentiment analysis** — Is this a positive or negative mention?
4. **Engagement scoring** — Likes, shares, comments → weighted score

### Aggregation

Per book, per day:
- Total mentions across platforms
- Trending score (mentions this week vs last week)
- Top tropes
- Sentiment percentage
- Links to source videos/posts

## Database Schema (initial)

### Books
- id, title, author, cover_image, description
- isbn, google_books_id
- average_rating, total_reviews

### Tropes
- id, name, slug, description
- Example: "enemies-to-lovers", "forced-proximity", "slow-burn"

### BookTropes
- book_id, trope_id

### TrendingData
- book_id, date, mention_count, sentiment_score, trending_score, platform

### Reviews (community)
- id, user_id, book_id, rating, text, created_at

### Users
- id, username, email, avatar, created_at

### ReadingLists
- id, user_id, name, description
- books (many-to-many)

## Pages / Routes

### Home
- Trending books this week
- Rising fast (biggest increase in mentions)
- Browse by trope

### Book Page
- Cover, title, author, description
- Tropes (clickable tags)
- Trending graph (mentions over time)
- TikTok videos about this book (embedded links)
- Community reviews
- "Similar books" (same tropes)

### Trope Page
- Description of the trope
- All books tagged with this trope
- Sorted by trending score

### Search
- Search by title, author, or trope
- AI-powered: "Books like Fourth Wing but with slow burn"

### User Profile
- Reading lists
- Reviews
- Favorite tropes

## Milestones

### Phase 1 — Data Pipeline
- [ ] Set up Python project with FastAPI
- [ ] Apply for TikTok Research API access
- [ ] Set up Reddit API connection
- [ ] Build LLM processing pipeline (book extraction + trope tagging)
- [ ] Set up PostgreSQL database with initial schema
- [ ] Create daily cron job for data collection
- [ ] Seed database with initial book data from Google Books API

### Phase 2 — Backend API
- [ ] REST API endpoints: /books, /books/:id, /tropes, /trending
- [ ] Search endpoint with filters (trope, rating, trending)
- [ ] User authentication (sign up, login)
- [ ] Review endpoints (create, read, update, delete)
- [ ] Reading list endpoints

### Phase 3 — Frontend
- [ ] React project setup
- [ ] Home page with trending books
- [ ] Book page with all details
- [ ] Trope browsing page
- [ ] Search with filters
- [ ] User registration and login
- [ ] Review form
- [ ] Reading list creation

### Phase 4 — AI Recommendations
- [ ] "Books like X" based on trope similarity
- [ ] Natural language search: "dark fantasy with enemies to lovers"
- [ ] Personalized recommendations based on user's reviews and lists

### Phase 5 — Polish & Launch
- [ ] Responsive design (mobile first — BookTok audience is on phones)
- [ ] SEO optimization
- [ ] Social sharing (share book pages to TikTok/Instagram)
- [ ] Deploy to production
- [ ] Custom domain
