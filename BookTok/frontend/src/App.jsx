import { useState, useEffect } from "react";
import "./App.css";

const API_URL = "http://localhost:8000/api/collect";

function App() {
  const [posts, setPosts] = useState([]);
  const [stats, setStats] = useState(null);
  const [platform, setPlatform] = useState("");
  const [sortBy, setSortBy] = useState("collected_at");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [platform]);

  async function fetchData() {
    setLoading(true);
    try {
      const query = platform ? `?platform=${platform}&limit=200` : "?limit=200";
      const [postsRes, statsRes] = await Promise.all([
        fetch(`${API_URL}/raw-posts${query}`),
        fetch(`${API_URL}/stats`),
      ]);
      setPosts(await postsRes.json());
      setStats(await statsRes.json());
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
            <span className="stat-number">{stats.unprocessed}</span>
            <span className="stat-label">Unprocessed</span>
          </div>
        </div>
      )}

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
        <button className="refresh-btn" onClick={fetchData} disabled={loading}>
          {loading ? "Loading..." : "Refresh"}
        </button>
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
    </div>
  );
}

export default App;
