import { useEffect, useMemo, useState } from 'react';

const apiBase = 'http://localhost:8000/api';

type Verification = {
  id: number;
  title: string;
  content_type: string;
  status: string;
  risk_score: number;
  verdict: string;
  priority?: string;
  created_at?: string;
};

type DashboardSummary = {
  total_verifications: number;
  low_risk: number;
  flagged: number;
  requires_review: number;
  active_users: number;
};

function App() {
  const [isLogin, setIsLogin] = useState(true);
  const [token, setToken] = useState<string | null>(localStorage.getItem('verifyai-token'));
  const [authForm, setAuthForm] = useState({ name: 'Analyst', email: 'demo@verifyai.app', password: 'verifyai123' });
  const [dashboard, setDashboard] = useState<{ summary: DashboardSummary; recent_activity: any[] } | null>(null);
  const [verifications, setVerifications] = useState<Verification[]>([]);
  const [title, setTitle] = useState('Synthetic media alert');
  const [contentType, setContentType] = useState('video');
  const [contentText, setContentText] = useState('Short viral clip appears to depict a public figure making an unverified statement.');
  const [sourceName, setSourceName] = useState('NewsPulse');
  const [sourceUrl, setSourceUrl] = useState('https://example.com/viral-clip');
  const [verification, setVerification] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const authHeaders = useMemo(
    () => ({
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }),
    [token],
  );

  const loadDashboard = async () => {
    if (!token) return;
    const res = await fetch(`${apiBase}/dashboard`, { headers: { Authorization: `Bearer ${token}` } });
    const data = await res.json();
    setDashboard(data);
  };

  const loadVerifications = async () => {
    if (!token) return;
    const res = await fetch(`${apiBase}/verifications`, { headers: { Authorization: `Bearer ${token}` } });
    const data = await res.json();
    setVerifications(Array.isArray(data) ? data : []);
  };

  useEffect(() => {
    if (token) {
      loadDashboard();
      loadVerifications();
    }
  }, [token]);

  const handleAuth = async () => {
    const endpoint = isLogin ? '/login' : '/register';
    const body = isLogin
      ? { email: authForm.email, password: authForm.password }
      : { email: authForm.email, password: authForm.password, name: authForm.name, role: 'analyst' };

    const res = await fetch(`${apiBase}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    if (!res.ok) {
      alert(data.detail || 'Authentication failed');
      return;
    }

    localStorage.setItem('verifyai-token', data.access_token);
    setToken(data.access_token);
  };

  const submitVerification = async () => {
    if (!token) {
      alert('Please log in first.');
      return;
    }

    setLoading(true);
    const res = await fetch(`${apiBase}/verifications`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({
        title,
        content_type: contentType,
        content_text: contentText,
        source_name: sourceName,
        source_url: sourceUrl,
        priority: 'high',
      }),
    });

    const data = await res.json();
    setVerification(data);
    setLoading(false);
    loadDashboard();
    loadVerifications();
  };

  const logout = () => {
    localStorage.removeItem('verifyai-token');
    setToken(null);
    setVerification(null);
  };

  if (!token) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <div className="auth-header">
            <span className="eyebrow">AI trust infrastructure</span>
            <h1>VerifyAI</h1>
          </div>

          <div className="toggle-row">
            <button className={isLogin ? 'toggle active' : 'toggle'} onClick={() => setIsLogin(true)}>Login</button>
            <button className={!isLogin ? 'toggle active' : 'toggle'} onClick={() => setIsLogin(false)}>Register</button>
          </div>

          {!isLogin && (
            <label>
              Name
              <input value={authForm.name} onChange={(e) => setAuthForm({ ...authForm, name: e.target.value })} />
            </label>
          )}

          <label>
            Email
            <input value={authForm.email} onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })} />
          </label>

          <label>
            Password
            <input type="password" value={authForm.password} onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })} />
          </label>

          <button className="primary-btn wide" onClick={handleAuth}>{isLogin ? 'Sign in' : 'Create account'}</button>
        </div>
      </div>
    );
  }

  const verdictColor =
    verification?.verdict === 'likely_malicious'
      ? '#f87171'
      : verification?.verdict === 'requires_review'
        ? '#fbbf24'
        : '#34d399';

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <span className="eyebrow">Trust operations center</span>
          <h1>VerifyAI</h1>
        </div>
        <div className="header-actions">
          <button className="secondary-btn">Live monitoring</button>
          <button className="ghost-btn" onClick={logout}>Log out</button>
        </div>
      </header>

      <section className="stats-grid">
        <div className="stat-card">
          <span>Total verifications</span>
          <strong>{dashboard?.summary?.total_verifications ?? 0}</strong>
        </div>
        <div className="stat-card warning">
          <span>Flagged</span>
          <strong>{dashboard?.summary?.flagged ?? 0}</strong>
        </div>
        <div className="stat-card review">
          <span>Needs review</span>
          <strong>{dashboard?.summary?.requires_review ?? 0}</strong>
        </div>
        <div className="stat-card success">
          <span>Low risk</span>
          <strong>{dashboard?.summary?.low_risk ?? 0}</strong>
        </div>
      </section>

      <main className="content-grid">
        <div className="panel">
          <h2>New verification</h2>

          <label>
            Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>

          <label>
            Content type
            <select value={contentType} onChange={(e) => setContentType(e.target.value)}>
              <option value="text">Text</option>
              <option value="image">Image</option>
              <option value="audio">Audio</option>
              <option value="video">Video</option>
            </select>
          </label>

          <label>
            Source name
            <input value={sourceName} onChange={(e) => setSourceName(e.target.value)} />
          </label>

          <label>
            Source URL
            <input value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} />
          </label>

          <label>
            Content summary
            <textarea value={contentText} onChange={(e) => setContentText(e.target.value)} rows={6} />
          </label>

          <button className="primary-btn wide" onClick={submitVerification} disabled={loading}>
            {loading ? 'Analyzing...' : 'Run verification'}
          </button>
        </div>

        <div className="panel result-panel">
          <h2>Verification result</h2>
          {verification ? (
            <>
              <div className="result-header">
                <span className="tag" style={{ background: verdictColor }}>
                  {verification.verdict}
                </span>
                <span>{verification.risk_score * 100}% risk</span>
              </div>

              <div className="score-row">
                <div>
                  <small>AI likelihood</small>
                  <strong>{verification.ai_likelihood * 100}%</strong>
                </div>
                <div>
                  <small>Source credibility</small>
                  <strong>{verification.source_credibility * 100}%</strong>
                </div>
                <div>
                  <small>Confidence</small>
                  <strong>{verification.confidence * 100}%</strong>
                </div>
              </div>

              <p className="summary">{verification.analysis_summary}</p>

              <div className="info-block">
                <h3>Manipulation signals</h3>
                <ul>
                  {verification.manipulation_signals.map((signal: string) => (
                    <li key={signal}>{signal}</li>
                  ))}
                </ul>
              </div>

              <div className="info-block">
                <h3>Recommendations</h3>
                <ul>
                  {verification.recommendations.map((recommendation: string) => (
                    <li key={recommendation}>{recommendation}</li>
                  ))}
                </ul>
              </div>
            </>
          ) : (
            <p className="placeholder">No verification run yet.</p>
          )}
        </div>
      </main>

      <section className="history-panel panel">
        <div className="panel-head">
          <h2>Verification history</h2>
          <span>{verifications.length} records</span>
        </div>

        <div className="history-list">
          {verifications.map((item) => (
            <div className="history-item" key={item.id}>
              <div>
                <strong>{item.title}</strong>
                <small>{item.content_type} • {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'new'}</small>
              </div>
              <div className="meta">
                <span className={`status-pill ${item.verdict}`}>{item.verdict}</span>
                <span>{item.risk_score * 100}% risk</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default App;
