import { useState, useEffect } from 'react'
import { portfolioService, getErrorMessage, PortfolioSignalsResponse } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import './PortfolioSignals.css'

const SIGNAL_COLORS: Record<string, string> = {
  STRONG_BUY: '#10b981',
  BUY: '#34d399',
  HOLD: '#fbbf24',
  SELL: '#fb923c',
  STRONG_SELL: '#ef4444',
}

const SIGNAL_ORDER: Record<string, number> = {
  STRONG_SELL: 0,
  SELL: 1,
  HOLD: 2,
  BUY: 3,
  STRONG_BUY: 4,
}

function PortfolioSignals() {
  const { user } = useAuth()
  const [data, setData] = useState<PortfolioSignalsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<'confidence' | 'signal' | 'gain_loss'>('confidence')
  const [expandedSymbol, setExpandedSymbol] = useState<string | null>(null)
  const [filterSignal, setFilterSignal] = useState<string>('ALL')

  useEffect(() => {
    if (user?.id) {
      loadSignals()
    }
  }, [user?.id])

  const loadSignals = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await portfolioService.getPortfolioSignals()
      setData(result)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '—'
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)
  }

  const formatPercent = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '—'
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(2)}%`
  }

  const getSignalBadgeStyle = (signal: string): React.CSSProperties => {
    const color = SIGNAL_COLORS[signal] || '#6b7280'
    return {
      backgroundColor: color,
      color: 'white',
      padding: '4px 10px',
      borderRadius: '12px',
      fontSize: '12px',
      fontWeight: 600,
      display: 'inline-block',
    }
  }

  const sortedHoldings = data?.holdings ? [...data.holdings].sort((a, b) => {
    switch (sortBy) {
      case 'confidence':
        return b.signal.confidence - a.signal.confidence
      case 'signal':
        return SIGNAL_ORDER[a.signal.signal] - SIGNAL_ORDER[b.signal.signal]
      case 'gain_loss':
        return (b.holding.gain_loss || 0) - (a.holding.gain_loss || 0)
      default:
        return 0
    }
  }) : []

  const filteredHoldings = filterSignal === 'ALL'
    ? sortedHoldings
    : sortedHoldings.filter(h => h.signal.signal === filterSignal)

  const conflictCount = data?.total_conflicts || 0
  const strongBuyCount = filteredHoldings.filter(h => h.signal.signal === 'STRONG_BUY').length
  const strongSellCount = filteredHoldings.filter(h => h.signal.signal === 'STRONG_SELL').length

  if (!user) {
    return <div className="portfolio-signals-page"><div className="error">Please log in to view portfolio signals</div></div>
  }

  return (
    <div className="portfolio-signals-page">
      <div className="page-header">
        <h1>Portfolio Signals</h1>
        <p className="subtitle">AI-powered analysis of your holdings</p>
      </div>

      {error && <div className="error">{error}</div>}

      {data && (
        <>
          <div className="signals-summary">
            <div className="summary-item">
              <span className="summary-value">{data.total_holdings}</span>
              <span className="summary-label">Holdings Analyzed</span>
            </div>
            <div className="summary-item conflict">
              <span className="summary-value">{conflictCount}</span>
              <span className="summary-label">Conflicts</span>
            </div>
            <div className="summary-item positive">
              <span className="summary-value">{strongBuyCount}</span>
              <span className="summary-label">Strong Buy</span>
            </div>
            <div className="summary-item negative">
              <span className="summary-value">{strongSellCount}</span>
              <span className="summary-label">Strong Sell</span>
            </div>
          </div>

          {conflictCount > 0 && (
            <div className="conflict-alert">
              <span className="conflict-icon">⚠️</span>
              <span>
                You have <strong>{conflictCount} position{conflictCount > 1 ? 's' : ''}</strong> with bearish signals.
                Review your holdings below.
              </span>
            </div>
          )}

          <div className="signals-controls">
            <div className="filter-group">
              <label>Signal Filter:</label>
              <select value={filterSignal} onChange={(e) => setFilterSignal(e.target.value)}>
                <option value="ALL">All Signals</option>
                <option value="STRONG_BUY">Strong Buy</option>
                <option value="BUY">Buy</option>
                <option value="HOLD">Hold</option>
                <option value="SELL">Sell</option>
                <option value="STRONG_SELL">Strong Sell</option>
              </select>
            </div>
            <div className="sort-group">
              <label>Sort by:</label>
              <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}>
                <option value="confidence">Confidence</option>
                <option value="signal">Signal</option>
                <option value="gain_loss">Gain/Loss</option>
              </select>
            </div>
          </div>

          {loading ? (
            <div className="loading">Analyzing your portfolio...</div>
          ) : filteredHoldings.length === 0 ? (
            <div className="empty-state">
              <p>No holdings found. Add stocks to your portfolio first.</p>
            </div>
          ) : (
            <div className="signals-table-container">
              <table className="signals-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Signal</th>
                    <th>Confidence</th>
                    <th>Shares</th>
                    <th>Value</th>
                    <th>Gain/Loss</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredHoldings.map((item) => (
                    <tr key={item.holding.id} className={item.is_conflict ? 'conflict-row' : ''}>
                      <td className="symbol">
                        {item.holding.symbol}
                        {item.is_conflict && <span className="conflict-badge">⚠️</span>}
                      </td>
                      <td>
                        <span style={getSignalBadgeStyle(item.signal.signal)}>
                          {item.signal.signal_label}
                        </span>
                      </td>
                      <td>
                        <div className="confidence-cell">
                          <span className="confidence-value">{item.signal.confidence}%</span>
                          <div className="confidence-bar">
                            <div
                              className="confidence-fill"
                              style={{
                                width: `${item.signal.confidence}%`,
                                backgroundColor: SIGNAL_COLORS[item.signal.signal],
                              }}
                            />
                          </div>
                        </div>
                      </td>
                      <td>{item.holding.quantity}</td>
                      <td>{formatCurrency(item.holding.current_value)}</td>
                      <td className={(item.holding.gain_loss || 0) >= 0 ? 'positive' : 'negative'}>
                        {formatCurrency(item.holding.gain_loss)}<br />
                        <span className="gain-pct">{formatPercent(item.holding.gain_loss_pct)}</span>
                      </td>
                      <td>
                        <button
                          className="btn-small"
                          onClick={() => setExpandedSymbol(
                            expandedSymbol === item.holding.symbol ? null : item.holding.symbol
                          )}
                        >
                          {expandedSymbol === item.holding.symbol ? 'Hide' : 'Details'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {expandedSymbol && (
                <div className="signal-details-panel">
                  {filteredHoldings
                    .filter(h => h.holding.symbol === expandedSymbol)
                    .map(item => (
                      <div key={item.holding.id} className="detail-content">
                        <h3>{item.holding.symbol} - Signal Details</h3>
                        
                        {item.signal.bullish_factors.length > 0 && (
                          <div className="factor-group bullish">
                            <h4>🟢 Bullish Factors</h4>
                            <ul>
                              {item.signal.bullish_factors.map((factor, i) => (
                                <li key={i}>{factor}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {item.signal.bearish_factors.length > 0 && (
                          <div className="factor-group bearish">
                            <h4>🔴 Bearish Factors</h4>
                            <ul>
                              {item.signal.bearish_factors.map((factor, i) => (
                                <li key={i}>{factor}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <div className="indicators-section">
                          <h4>📊 Technical Indicators</h4>
                          <div className="indicators-grid">
                            {item.signal.indicators.map((ind, i) => (
                              <div key={i} className="indicator-card">
                                <div className="indicator-header">
                                  <span className="indicator-name">{ind.indicator}</span>
                                  <span
                                    className="indicator-signal"
                                    style={{ color: SIGNAL_COLORS[ind.signal] }}
                                  >
                                    {ind.signal}
                                  </span>
                                </div>
                                <div className="indicator-value">Value: {typeof ind.value === 'number' ? ind.value.toFixed(2) : ind.value}</div>
                                <div className="indicator-reasoning">{ind.reasoning}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default PortfolioSignals
