import { useState, useEffect } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000/api";
const PLATFORMS = ["all", "reddit", "instagram", "tiktok"];

function App() {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("this-month");
  const [platform, setPlatform] = useState("all");

  useEffect(() => {
    fetchBooks();
  }, [tab, platform]);

  async function fetchBooks() {
    setLoading(true);
    try {
      const platformParam = platform !== "all" ? `&platform=${platform}` : "";
      const res = await fetch(`${API_BASE}/trending/${tab}?limit=15${platformParam}`);
      setBooks(await res.json());
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
      </div>

      <div className="platform-filters">
        {PLATFORMS.map((p) => (
          <button
            key={p}
            className={`platform-filter ${platform === p ? "active" : ""} ${p}`}
            onClick={() => setPlatform(p)}
          >
            {p === "all" ? "All Platforms" : p}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="empty">Loading...</p>
      ) : books.length === 0 ? (
        <p className="empty">No books found for this filter.</p>
      ) : (
        <div className="books-list">
          {books.map((book, i) => (
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
      )}
    </div>
  );
}

export default App;
