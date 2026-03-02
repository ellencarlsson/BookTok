import { useState, useEffect } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000/api";

function App() {
  const [thisMonth, setThisMonth] = useState([]);
  const [allTime, setAllTime] = useState([]);
  const [redditPosts, setRedditPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("this-month");

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const [monthRes, allTimeRes, redditRes] = await Promise.all([
        fetch(`${API_BASE}/trending/this-month?limit=15`),
        fetch(`${API_BASE}/trending/all-time?limit=15`),
        fetch(`${API_BASE}/collect/raw-posts?platform=reddit&limit=30`),
      ]);
      setThisMonth(await monthRes.json());
      setAllTime(await allTimeRes.json());
      setRedditPosts(await redditRes.json());
    } catch (err) {
      console.error("Failed to fetch:", err);
    }
    setLoading(false);
  }

  function formatNumber(n) {
    if (!n) return "0";
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
    if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
    return n.toString();
  }

  const books = tab === "this-month" ? thisMonth : tab === "all-time" ? allTime : null;

  return (
    <div className="app">
      <header>
        <h1>BookTok</h1>
        <p className="subtitle">Popular books on social media right now</p>
      </header>

      <div className="tabs">
        <button
          className={`tab ${tab === "this-month" ? "active" : ""}`}
          onClick={() => setTab("this-month")}
        >
          This Month
        </button>
        <button
          className={`tab ${tab === "all-time" ? "active" : ""}`}
          onClick={() => setTab("all-time")}
        >
          All Time
        </button>
        <button
          className={`tab ${tab === "reddit" ? "active" : ""}`}
          onClick={() => setTab("reddit")}
        >
          Reddit
        </button>
        <button className="refresh-btn" onClick={fetchData} disabled={loading}>
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {tab === "reddit" ? (
        <div className="reddit-posts">
          {redditPosts.map((post) => (
            <div key={post.id} className="reddit-card">
              <div className="reddit-meta">
                <span className="reddit-author">u/{post.author}</span>
                <span className="reddit-score">{formatNumber(post.like_count)} upvotes</span>
                <span>{post.comment_count} comments</span>
              </div>
              <p className="reddit-text">{post.text}</p>
              <a className="reddit-link" href={post.url} target="_blank" rel="noreferrer">
                View on Reddit
              </a>
            </div>
          ))}
          {redditPosts.length === 0 && !loading && (
            <p className="empty">No Reddit posts collected yet.</p>
          )}
        </div>
      ) : (
        <>
          <div className="books-list">
            {books && books.map((book, i) => (
              <div key={book.title} className="book-card">
                <div className="book-rank">#{i + 1}</div>
                {book.cover_url ? (
                  <img className="book-cover" src={book.cover_url} alt={book.title} />
                ) : (
                  <div className="book-cover-placeholder">No Cover</div>
                )}
                <div className="book-info">
                  <h3 className="book-title">{book.title}</h3>
                  <p className="book-author">by {book.author}</p>
                  <div className="book-stats">
                    <span className="book-mentions">{book.mentions} mentions</span>
                    <span>{formatNumber(book.total_likes)} upvotes</span>
                    <span>{formatNumber(book.total_comments)} comments</span>
                  </div>
                  <div className="book-platforms">
                    {book.platforms.map((p) => (
                      <span key={p} className={`platform-badge ${p}`}>{p}</span>
                    ))}
                  </div>
                </div>
                <div className="book-score">
                  <span className="score-number">{formatNumber(book.score)}</span>
                  <span className="score-label">score</span>
                </div>
              </div>
            ))}
          </div>

          {books && books.length === 0 && !loading && (
            <p className="empty">No books found yet. Collect more posts first.</p>
          )}
        </>
      )}
    </div>
  );
}

export default App;
