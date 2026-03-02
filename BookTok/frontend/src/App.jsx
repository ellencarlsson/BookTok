import { useState, useEffect } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000/api";
const TABS = ["social", "websites"];
const PLATFORMS = ["all", "reddit", "instagram", "tiktok", "youtube"];
const SOURCES = [
  { id: "all", label: "All Sources" },
  { id: "goodreads-booktok", label: "Goodreads BookTok" },
  { id: "hudson-booksellers", label: "Hudson Booksellers" },
];

function App() {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("social");
  const [platform, setPlatform] = useState("all");
  const [source, setSource] = useState("all");

  useEffect(() => {
    fetchBooks();
  }, [tab, platform, source]);

  async function fetchBooks() {
    setLoading(true);
    try {
      let url;
      if (tab === "websites") {
        const sourceParam = source !== "all" ? `&source=${source}` : "";
        url = `${API_BASE}/trending/websites?limit=15${sourceParam}`;
      } else {
        const platformParam = platform !== "all" ? `&platform=${platform}` : "";
        url = `${API_BASE}/trending/this-month?limit=15${platformParam}`;
      }
      const res = await fetch(url);
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

      <div className="tab-filters">
        {TABS.map((t) => (
          <button
            key={t}
            className={`tab-filter ${tab === t ? "active" : ""}`}
            onClick={() => setTab(t)}
          >
            {t === "social" ? "Social Media" : "Websites"}
          </button>
        ))}
      </div>

      {tab === "social" && (
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
      )}

      {tab === "websites" && (
        <div className="platform-filters">
          {SOURCES.map((s) => (
            <button
              key={s.id}
              className={`platform-filter ${source === s.id ? "active" : ""} ${s.id}`}
              onClick={() => setSource(s.id)}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}

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
                  <span className="book-mentions">
                    {tab === "websites"
                      ? `${book.mentions} sources`
                      : `${book.mentions} mentions`}
                  </span>
                </div>
                <div className="book-platforms">
                  {book.platforms.map((p) => (
                    <span key={p} className={`platform-badge ${p}`}>
                      {p.replace("websites:", "")}
                    </span>
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
