import { useState, useEffect } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000/api";

function App() {
  const [posts, setPosts] = useState([]);
  const [stats, setStats] = useState(null);
  const [trendingBooks, setTrendingBooks] = useState([]);
  const [platform, setPlatform] = useState("");
  const [sortBy, setSortBy] = useState("collected_at");
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("trending");

  useEffect(() => {
    fetchData();
  }, [platform]);

  async function fetchData() {
    setLoading(true);
    try {
      const query = platform ? `?platform=${platform}&limit=200` : "?limit=200";
      const [postsRes, statsRes, trendingRes] = await Promise.all([
        fetch(`${API_BASE}/collect/raw-posts${query}`),
        fetch(`${API_BASE}/collect/stats`),
        fetch(`${API_BASE}/trending/top-books?limit=15`),
      ]);
      setPosts(await postsRes.json());
      setStats(await statsRes.json());
      setTrendingBooks(await trendingRes.json());
    } catch (err) {
      console.error("Failed to fetch:", err);
    }
    setLoading(false);
  }

  function sortedPosts() {
    return [...posts].sort((a, b) => {
      if (sortBy === "like_count" || sortBy === "view_count" || sortBy === "comment_count") {
        return (b[sortBy] || 0) - (a[sortBy] || 0);
      }
      return (b[sortBy] || "").localeCompare(a[sortBy] || "");
    });
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
        <h1>BookTok Dashboard</h1>
        <p className="subtitle">AI-powered trend monitoring from social media</p>
      </header>

      {stats && (
        <div className="stats-bar">
          <div className="stat">
            <span className="stat-number">{stats.total}</span>
            <span className="stat-label">Total Posts</span>
          </div>
          <div className="stat tiktok">
            <span className="stat-number">{stats.by_platform.tiktok}</span>
            <span className="stat-label">TikTok</span>
          </div>
          <div className="stat reddit">
            <span className="stat-number">{stats.by_platform.reddit}</span>
            <span className="stat-label">Reddit</span>
          </div>
          <div className="stat youtube">
            <span className="stat-number">{stats.by_platform.youtube}</span>
            <span className="stat-label">YouTube</span>
          </div>
          <div className="stat">
            <span className="stat-number">{trendingBooks.length}</span>
            <span className="stat-label">Books Found</span>
          </div>
        </div>
      )}

      <div className="tabs">
        <button
          className={`tab ${tab === "trending" ? "active" : ""}`}
          onClick={() => setTab("trending")}
        >
          Trending Books
        </button>
        <button
          className={`tab ${tab === "posts" ? "active" : ""}`}
          onClick={() => setTab("posts")}
        >
          Raw Posts
        </button>
        <button className="refresh-btn" onClick={fetchData} disabled={loading}>
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {tab === "trending" && (
        <div className="trending-section">
          <h2>Top 15 Trending Books</h2>
          <div className="books-list">
            {trendingBooks.map((book, i) => (
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
                    <span>👁 {formatNumber(book.total_views)}</span>
                    <span>❤️ {formatNumber(book.total_likes)}</span>
                    <span>💬 {formatNumber(book.total_comments)}</span>
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
          {trendingBooks.length === 0 && !loading && (
            <p className="empty">No books extracted yet. Collect more posts first.</p>
          )}
        </div>
      )}

      {tab === "posts" && (
        <>
          <div className="controls">
            <div className="filter-group">
              <label>Platform:</label>
              <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
                <option value="">All</option>
                <option value="tiktok">TikTok</option>
                <option value="reddit">Reddit</option>
                <option value="youtube">YouTube</option>
              </select>
            </div>
            <div className="filter-group">
              <label>Sort by:</label>
              <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                <option value="collected_at">Newest</option>
                <option value="view_count">Most Views</option>
                <option value="like_count">Most Likes</option>
                <option value="comment_count">Most Comments</option>
              </select>
            </div>
          </div>

          <div className="posts-grid">
            {sortedPosts().map((post) => (
              <div key={post.id} className="post-card">
                <div className="post-header">
                  <span className={`platform-badge ${post.platform}`}>
                    {post.platform}
                  </span>
                  <span className="post-author">@{post.author}</span>
                </div>
                <p className="post-text">{post.text || "No description"}</p>
                <div className="post-stats">
                  <span title="Views">👁 {formatNumber(post.view_count)}</span>
                  <span title="Likes">❤️ {formatNumber(post.like_count)}</span>
                  <span title="Comments">💬 {formatNumber(post.comment_count)}</span>
                  <span title="Shares">🔗 {formatNumber(post.share_count)}</span>
                </div>
                <div className="post-footer">
                  <span className="post-date">
                    {post.posted_at ? new Date(post.posted_at).toLocaleDateString() : "Unknown date"}
                  </span>
                  {post.url && (
                    <a href={post.url} target="_blank" rel="noopener noreferrer" className="post-link">
                      View →
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>

          {posts.length === 0 && !loading && (
            <p className="empty">No posts collected yet. Run the collector first.</p>
          )}
        </>
      )}
    </div>
  );
}

export default App;
