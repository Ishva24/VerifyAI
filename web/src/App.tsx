import { useEffect, useState } from 'react';

const apiBase = 'http://localhost:8000/api';

type Verification = {
  id: number;
  title: string;
  content_type: string;
  status: string;
  risk_score: number;
  confidence: number;
  verdict: string;
  analysis_summary: string;
  source_credibility: number;
  ai_likelihood: number;
  manipulation_signals: string[];
  recommendations: string[];
};

function App() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [title, setTitle] = useState('Deepfake video alert');
  const [contentType, setContentType] = useState('video');
  const [contentText, setContentText] = useState('A viral campaign clip appears to show a public figure making a fabrication.');
  const [sourceName, setSourceName] = useState('CampaignWire');
  const [sourceUrl, setSourceUrl] = useState('https://example.com/viral-clip');
  const [verification, setVerification] = useState<Verification | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${apiBase}/dashboard`)
      .then((res) => res.json())
      .then((data) => setDashboard(data))
      .catch(() => setDashboard({ summary: { total_verifications: 0 } }));
  }, []);

  const submitVerification = async () => {
    setLoading(true);
    const res = await fetch(`${apiBase}/verifications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        content_type: contentType,
        content_text: contentText,
        source_name: sourceName,
        source_url: sourceUrl,
      }),
    });

    const data = await res.json();
    setVerification(data);
    setLoading(false);
    const dashboardRes = await fetch(`${apiBase}/dashboard`);
    const dashboardData = await dashboardRes.json();
    setDashboard(dashboardData);
  };

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
          <span className="eyebrow">AI trust infrastructure</span>
          <h1>VerifyAI</h1>
        </div>
        <button className="primary-btn">Live Monitoring</button>
      </header>

      <section className="stats-grid">
        <div className="stat-card">
          <span>Total verifications</span>
          <strong>{dashboard?.summary?.total_verifications ?? 0}</strong>
        </div>
        <div className="stat-card">
          <span>Flagged</span>
          <strong>{dashboard?.summary?.flagged ?? 0}</strong>
        </div>
        <div className="stat-card">
          <span>Needs review</span>
          <strong>{dashboard?.summary?.requires_review ?? 0}</strong>
        </div>
        <div className="stat-card">
          <span>Active users</span>
          <strong>{dashboard?.summary?.active_users ?? 0}</strong>
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
                  {verification.manipulation_signals.map((signal) => (
                    <li key={signal}>{signal}</li>
                  ))}
                </ul>
              </div>

              <div className="info-block">
                <h3>Recommendations</h3>
                <ul>
                  {verification.recommendations.map((recommendation) => (
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
    </div>
  );
}

export default App;
