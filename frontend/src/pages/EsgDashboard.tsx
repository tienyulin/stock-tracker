import { useState, useEffect } from 'react'
import {
  esgService,
  EsgScore,
  PortfolioEsgSummary,
  ControversyAlert,
  ExclusionListEntry,
  PortfolioCarbon,
  PortfolioScreen,
} from '../services/esgService'
import './EsgDashboard.css'

const ESG_RATING_COLORS: Record<string, string> = {
  AAA: '#00c853',
  AA: '#64dd17',
  A: '#cddc39',
  BBB: '#ffeb3b',
  BB: '#ffc107',
  B: '#ff9800',
  CCC: '#f44336',
}

function EsgDashboardPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'scores' | 'alerts' | 'screen'>('overview')

  const [summary, setSummary] = useState<PortfolioEsgSummary | null>(null)
  const [carbon, setCarbon] = useState<PortfolioCarbon | null>(null)
  const [scores] = useState<EsgScore[]>([])
  const [alerts, setAlerts] = useState<ControversyAlert[]>([])
  const [exclusions, setExclusions] = useState<ExclusionListEntry[]>([])
  const [screenResult, setScreenResult] = useState<PortfolioScreen | null>(null)

  // Add score form
  const [showAddScore, setShowAddScore] = useState(false)
  const [addTicker, setAddTicker] = useState('')
  const [addCompany, setAddCompany] = useState('')
  const [addEsg, setAddEsg] = useState('')
  const [addEnv, setAddEnv] = useState('')
  const [addSocial, setAddSocial] = useState('')
  const [addGov, setAddGov] = useState('')
  const [addCarbon, setAddCarbon] = useState('')
  const [addingScore, setAddingScore] = useState(false)

  // Add exclusion form
  const [showAddExclusion, setShowAddExclusion] = useState(false)
  const [exclType, setExclType] = useState<'negative_screening' | 'ethical_exclusion'>('negative_screening')
  const [exclTicker, setExclTicker] = useState('')
  const [exclSector, setExclSector] = useState('')
  const [exclReason, setExclReason] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [sum, carb, als, excl, screen] = await Promise.all([
        esgService.getPortfolioSummary().catch(() => null),
        esgService.getPortfolioCarbon().catch(() => null),
        esgService.getActiveAlerts().catch(() => []),
        esgService.getExclusions().catch(() => []),
        esgService.screenPortfolio().catch(() => null),
      ])
      setSummary(sum)
      setCarbon(carb)
      setAlerts(als)
      setExclusions(excl)
      setScreenResult(screen)
    } catch (e) {
      setError('Failed to load ESG data')
    } finally {
      setLoading(false)
    }
  }

  const handleAddScore = async () => {
    if (!addTicker || !addCompany || !addEsg) return
    try {
      setAddingScore(true)
      await esgService.createEsgScore({
        ticker: addTicker,
        company_name: addCompany,
        esg_total_score: parseFloat(addEsg),
        environmental_score: parseFloat(addEnv || addEsg),
        social_score: parseFloat(addSocial || addEsg),
        governance_score: parseFloat(addGov || addEsg),
        carbon_footprint_tons: addCarbon ? parseFloat(addCarbon) : null,
        rating_date: new Date().toISOString().split('T')[0],
      })
      setShowAddScore(false)
      setAddTicker('')
      setAddCompany('')
      setAddEsg('')
      setAddEnv('')
      setAddSocial('')
      setAddGov('')
      setAddCarbon('')
      loadData()
    } catch (e) {
      alert('Failed to add ESG score')
    } finally {
      setAddingScore(false)
    }
  }

  const handleAddExclusion = async () => {
    if (!exclTicker && !exclSector) return
    try {
      await esgService.createExclusion({
        list_type: exclType,
        ticker: exclTicker || undefined,
        sector: exclSector || undefined,
        reason: exclReason || undefined,
      })
      setShowAddExclusion(false)
      setExclTicker('')
      setExclSector('')
      setExclReason('')
      loadData()
    } catch (e) {
      alert('Failed to add exclusion')
    }
  }

  const handleDismissAlert = async (alertId: string) => {
    try {
      await esgService.dismissAlert(alertId)
      loadData()
    } catch (e) {
      alert('Failed to dismiss alert')
    }
  }

  const handleDeleteExclusion = async (id: string) => {
    try {
      await esgService.deleteExclusion(id)
      loadData()
    } catch (e) {
      alert('Failed to delete exclusion')
    }
  }

  const getRatingColor = (score: number) => {
    if (score >= 85) return ESG_RATING_COLORS.AAA
    if (score >= 75) return ESG_RATING_COLORS.AA
    if (score >= 65) return ESG_RATING_COLORS.A
    if (score >= 55) return ESG_RATING_COLORS.BBB
    if (score >= 45) return ESG_RATING_COLORS.BB
    if (score >= 35) return ESG_RATING_COLORS.B
    return ESG_RATING_COLORS.CCC
  }

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      low: '#4caf50',
      medium: '#ff9800',
      high: '#f44336',
      critical: '#9c27b0',
    }
    return colors[severity] || '#999'
  }

  if (loading) {
    return <div className="esg-loading">🌱 Loading ESG Dashboard...</div>
  }

  if (error) {
    return <div className="esg-error">{error}</div>
  }

  return (
    <div className="esg-dashboard">
      <div className="esg-header">
        <h1>🌿 ESG Dashboard</h1>
        <p>Sustainable Investing & Ethical Screening</p>
      </div>

      {/* Tab Navigation */}
      <div className="esg-tabs">
        {(['overview', 'scores', 'alerts', 'screen'] as const).map((tab) => (
          <button
            key={tab}
            className={`esg-tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'overview' && '📊 Overview'}
            {tab === 'scores' && '📈 ESG Scores'}
            {tab === 'alerts' && `⚠️ Alerts${alerts.length > 0 ? ` (${alerts.length})` : ''}`}
            {tab === 'screen' && '🔍 Screening'}
          </button>
        ))}
      </div>

      {/* ─── Overview Tab ─────────────────────────────────────────────── */}
      {activeTab === 'overview' && (
        <div className="esg-overview">
          {/* Portfolio Score Cards */}
          <div className="esg-score-cards">
            <div className="esg-score-card main">
              <div className="card-label">Portfolio ESG Score</div>
              <div
                className="card-value"
                style={{ color: getRatingColor(summary?.portfolio_esg_score || 0) }}
              >
                {summary?.portfolio_esg_score?.toFixed(1) || '—'}
              </div>
              <div className="card-sub">
                {summary?.holdings_count || 0} holdings tracked
              </div>
            </div>
            <div className="esg-score-card">
              <div className="card-label">🌿 Environmental</div>
              <div className="card-value env">
                {summary?.portfolio_env_score?.toFixed(1) || '—'}
              </div>
            </div>
            <div className="esg-score-card">
              <div className="card-label">👥 Social</div>
              <div className="card-value social">
                {summary?.portfolio_social_score?.toFixed(1) || '—'}
              </div>
            </div>
            <div className="esg-score-card">
              <div className="card-label">⚖️ Governance</div>
              <div className="card-value gov">
                {summary?.portfolio_gov_score?.toFixed(1) || '—'}
              </div>
            </div>
          </div>

          {/* Carbon Footprint */}
          {carbon && (
            <div className="esg-carbon-card">
              <h3>🌍 Carbon Footprint</h3>
              <div className="carbon-stats">
                <div className="carbon-stat">
                  <span className="stat-label">Total</span>
                  <span className="stat-value">{carbon.total_carbon_tons.toFixed(2)} tons CO₂/yr</span>
                </div>
                <div className="carbon-stat">
                  <span className="stat-label">Benchmark Avg</span>
                  <span className="stat-value">{carbon.benchmark_average_tons.toFixed(2)} tons</span>
                </div>
                <div className="carbon-stat">
                  <span className="stat-label">vs Benchmark</span>
                  <span
                    className="stat-value"
                    style={{ color: carbon.vs_benchmark_pct > 0 ? '#f44336' : '#4caf50' }}
                  >
                    {carbon.vs_benchmark_pct > 0 ? '+' : ''}{carbon.vs_benchmark_pct.toFixed(1)}%
                  </span>
                </div>
                {carbon.highest_carbon_ticker && (
                  <div className="carbon-stat">
                    <span className="stat-label">Highest Carbon</span>
                    <span className="stat-value warn">{carbon.highest_carbon_ticker}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ESG Rating Distribution */}
          {summary?.esg_rating_distribution && Object.keys(summary.esg_rating_distribution).length > 0 && (
            <div className="esg-distribution-card">
              <h3>📊 ESG Rating Distribution</h3>
              <div className="rating-bars">
                {Object.entries(summary.esg_rating_distribution).map(([rating, count]) => (
                  <div key={rating} className="rating-bar-row">
                    <span className="rating-badge" style={{ backgroundColor: ESG_RATING_COLORS[rating] }}>
                      {rating}
                    </span>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{
                          width: `${(count / summary.holdings_count) * 100}%`,
                          backgroundColor: ESG_RATING_COLORS[rating],
                        }}
                      />
                    </div>
                    <span className="bar-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ─── Scores Tab ───────────────────────────────────────────────── */}
      {activeTab === 'scores' && (
        <div className="esg-scores-tab">
          <div className="esg-section-header">
            <h3>ESG Scores</h3>
            <button className="btn-primary" onClick={() => setShowAddScore(true)}>
              + Add Score
            </button>
          </div>

          {/* Add Score Modal */}
          {showAddScore && (
            <div className="modal-overlay">
              <div className="modal">
                <h3>Add ESG Score</h3>
                <div className="form-grid">
                  <label>
                    Ticker
                    <input value={addTicker} onChange={(e) => setAddTicker(e.target.value)} placeholder="AAPL" />
                  </label>
                  <label>
                    Company Name
                    <input value={addCompany} onChange={(e) => setAddCompany(e.target.value)} placeholder="Apple Inc." />
                  </label>
                  <label>
                    ESG Total (0-100)
                    <input type="number" value={addEsg} onChange={(e) => setAddEsg(e.target.value)} placeholder="75" />
                  </label>
                  <label>
                    Environmental
                    <input type="number" value={addEnv} onChange={(e) => setAddEnv(e.target.value)} placeholder="Same as total" />
                  </label>
                  <label>
                    Social
                    <input type="number" value={addSocial} onChange={(e) => setAddSocial(e.target.value)} placeholder="Same as total" />
                  </label>
                  <label>
                    Governance
                    <input type="number" value={addGov} onChange={(e) => setAddGov(e.target.value)} placeholder="Same as total" />
                  </label>
                  <label>
                    Carbon (tons CO₂/yr)
                    <input type="number" value={addCarbon} onChange={(e) => setAddCarbon(e.target.value)} placeholder="Optional" />
                  </label>
                </div>
                <div className="modal-actions">
                  <button onClick={() => setShowAddScore(false)}>Cancel</button>
                  <button className="btn-primary" onClick={handleAddScore} disabled={addingScore}>
                    {addingScore ? 'Adding...' : 'Add Score'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {scores.length === 0 && (
            <div className="esg-empty">
              <p>No ESG scores tracked yet. Add your first score above.</p>
            </div>
          )}
        </div>
      )}

      {/* ─── Alerts Tab ──────────────────────────────────────────────── */}
      {activeTab === 'alerts' && (
        <div className="esg-alerts-tab">
          <div className="esg-section-header">
            <h3>⚠️ Controversy Alerts</h3>
            <button className="btn-primary" onClick={() => setShowAddExclusion(true)}>
              + Add Exclusion
            </button>
          </div>

          {/* Add Exclusion Modal */}
          {showAddExclusion && (
            <div className="modal-overlay">
              <div className="modal">
                <h3>Add to Exclusion List</h3>
                <div className="form-grid">
                  <label>
                    List Type
                    <select value={exclType} onChange={(e) => setExclType(e.target.value as any)}>
                      <option value="negative_screening">Negative Screening</option>
                      <option value="ethical_exclusion">Ethical Exclusion</option>
                    </select>
                  </label>
                  <label>
                    Ticker
                    <input value={exclTicker} onChange={(e) => setExclTicker(e.target.value)} placeholder="BA or leave empty" />
                  </label>
                  <label>
                    Sector
                    <input value={exclSector} onChange={(e) => setExclSector(e.target.value)} placeholder="Weapons" />
                  </label>
                  <label>
                    Reason
                    <input value={exclReason} onChange={(e) => setExclReason(e.target.value)} placeholder="Defense contractor" />
                  </label>
                </div>
                <div className="modal-actions">
                  <button onClick={() => setShowAddExclusion(false)}>Cancel</button>
                  <button className="btn-primary" onClick={handleAddExclusion}>Add Exclusion</button>
                </div>
              </div>
            </div>
          )}

          {/* Active Alerts */}
          {alerts.length > 0 && (
            <div className="alerts-section">
              <h4>Active Alerts ({alerts.length})</h4>
              <div className="alerts-list">
                {alerts.map((alert) => (
                  <div key={alert.id} className="alert-card" style={{ borderLeftColor: getSeverityColor(alert.severity) }}>
                    <div className="alert-header">
                      <span className="alert-ticker">{alert.ticker}</span>
                      <span
                        className="alert-severity"
                        style={{ backgroundColor: getSeverityColor(alert.severity) }}
                      >
                        {alert.severity.toUpperCase()}
                      </span>
                    </div>
                    <div className="alert-headline">{alert.headline}</div>
                    {alert.description && <div className="alert-desc">{alert.description}</div>}
                    <div className="alert-footer">
                      <span className="alert-date">{alert.alert_date}</span>
                      <button
                        className="btn-dismiss"
                        onClick={() => handleDismissAlert(alert.id)}
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {alerts.length === 0 && (
            <div className="esg-empty">
              <p>✅ No active controversy alerts. Your portfolio is clean!</p>
            </div>
          )}

          {/* Exclusion List */}
          {exclusions.length > 0 && (
            <div className="exclusion-section">
              <h4>Exclusion List ({exclusions.length})</h4>
              <table className="esg-table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Ticker</th>
                    <th>Sector</th>
                    <th>Reason</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {exclusions.map((ex) => (
                    <tr key={ex.id}>
                      <td>
                        <span className={`excl-type-badge ${ex.list_type}`}>
                          {ex.list_type.replace('_', ' ')}
                        </span>
                      </td>
                      <td>{ex.ticker || '—'}</td>
                      <td>{ex.sector || '—'}</td>
                      <td>{ex.reason || '—'}</td>
                      <td>
                        <button className="btn-danger-sm" onClick={() => handleDeleteExclusion(ex.id)}>
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ─── Screening Tab ─────────────────────────────────────────────── */}
      {activeTab === 'screen' && (
        <div className="esg-screen-tab">
          <div className="esg-section-header">
            <h3>🔍 Portfolio Screening</h3>
            <button className="btn-primary" onClick={loadData}>↻ Refresh</button>
          </div>

          {screenResult && (
            <div className="screen-results">
              <div className="compliance-card">
                <div className="card-label">Compliance Score</div>
                <div
                  className="card-value"
                  style={{ color: screenResult.compliance_score >= 80 ? '#4caf50' : screenResult.compliance_score >= 50 ? '#ff9800' : '#f44336' }}
                >
                  {screenResult.compliance_score.toFixed(0)}%
                </div>
                <div className="card-sub">
                  {screenResult.total_holdings} total holdings
                </div>
              </div>

              {screenResult.flagged_holdings.length > 0 && (
                <div className="flagged-section">
                  <h4>🚫 Flagged Holdings ({screenResult.flagged_holdings.length})</h4>
                  <div className="flagged-list">
                    {screenResult.flagged_holdings.map((h, i) => (
                      <div key={i} className="flagged-item">
                        <span className="flagged-ticker">{h.ticker}</span>
                        <span className="flagged-name">{h.company_name}</span>
                        <span className="flagged-reason">{h.reason}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {screenResult.screened_holdings.length > 0 && (
                <div className="screened-section">
                  <h4>✅ Screened Holdings ({screenResult.screened_holdings.length})</h4>
                  <table className="esg-table">
                    <thead>
                      <tr>
                        <th>Ticker</th>
                        <th>Company</th>
                        <th>ESG Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {screenResult.screened_holdings.map((h, i) => (
                        <tr key={i}>
                          <td>{h.ticker}</td>
                          <td>{h.company_name}</td>
                          <td>
                            <span style={{ color: getRatingColor(h.esg_score), fontWeight: 600 }}>
                              {h.esg_score.toFixed(1)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {!screenResult && (
            <div className="esg-empty">
              <p>Add ESG scores to run portfolio screening.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default EsgDashboardPage
