import { useState, useEffect } from 'react'
import { dividendService, DividendPayment, DividendHolding, DividendDashboard, DividendCalendarEntry } from '../services/dividendService'
import { useAuth } from '../contexts/AuthContext'
import './DividendTracker.css'

function DividendTracker() {
  const { user } = useAuth()
  const [dashboard, setDashboard] = useState<DividendDashboard | null>(null)
  const [holdings, setHoldings] = useState<DividendHolding[]>([])
  const [payments, setPayments] = useState<DividendPayment[]>([])
  const [calendar, setCalendar] = useState<DividendCalendarEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'dashboard' | 'payments' | 'holdings' | 'calendar'>('dashboard')

  // Add payment form
  const [showAddForm, setShowAddForm] = useState(false)
  const [newSymbol, setNewSymbol] = useState('')
  const [newExDate, setNewExDate] = useState('')
  const [newPayDate, setNewPayDate] = useState('')
  const [newAmount, setNewAmount] = useState('')
  const [newShares, setNewShares] = useState('')
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    if (user?.id) {
      loadData()
    }
  }, [user?.id])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [dashboardData, holdingsData, paymentsData, calendarData] = await Promise.all([
        dividendService.getDashboard().catch(() => null),
        dividendService.getHoldings().catch(() => []),
        dividendService.getPayments({ limit: 20 }).catch(() => []),
        dividendService.getCalendar(60).catch(() => []),
      ])
      setDashboard(dashboardData)
      setHoldings(holdingsData)
      setPayments(paymentsData)
      setCalendar(calendarData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dividend data')
    } finally {
      setLoading(false)
    }
  }

  const handleAddPayment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSymbol || !newExDate || !newPayDate || !newAmount || !newShares) return

    try {
      setAdding(true)
      await dividendService.createPayment({
        symbol: newSymbol.toUpperCase(),
        ex_dividend_date: newExDate,
        payment_date: newPayDate,
        amount_per_share: parseFloat(newAmount),
        shares_owned: parseFloat(newShares),
      })
      setShowAddForm(false)
      setNewSymbol('')
      setNewExDate('')
      setNewPayDate('')
      setNewAmount('')
      setNewShares('')
      loadData()
    } catch (err) {
      alert('Failed to add dividend payment')
    } finally {
      setAdding(false)
    }
  }

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(amount)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString()
  }

  if (loading) {
    return <div className="dividend-loading">Loading dividend data...</div>
  }

  if (error) {
    return <div className="dividend-error">{error}</div>
  }

  return (
    <div className="dividend-tracker">
      <div className="dividend-header">
        <h1>Dividend Tracker</h1>
        <button className="btn-primary" onClick={() => setShowAddForm(true)}>
          + Add Dividend
        </button>
      </div>

      {showAddForm && (
        <div className="modal-overlay" onClick={() => setShowAddForm(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Record Dividend Payment</h2>
            <form onSubmit={handleAddPayment}>
              <div className="form-group">
                <label>Symbol</label>
                <input
                  type="text"
                  value={newSymbol}
                  onChange={e => setNewSymbol(e.target.value)}
                  placeholder="e.g. AAPL"
                  required
                />
              </div>
              <div className="form-group">
                <label>Ex-Dividend Date</label>
                <input
                  type="date"
                  value={newExDate}
                  onChange={e => setNewExDate(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Payment Date</label>
                <input
                  type="date"
                  value={newPayDate}
                  onChange={e => setNewPayDate(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Amount per Share ($)</label>
                <input
                  type="number"
                  step="0.01"
                  value={newAmount}
                  onChange={e => setNewAmount(e.target.value)}
                  placeholder="0.24"
                  required
                />
              </div>
              <div className="form-group">
                <label>Shares Owned</label>
                <input
                  type="number"
                  step="1"
                  value={newShares}
                  onChange={e => setNewShares(e.target.value)}
                  placeholder="100"
                  required
                />
              </div>
              <div className="form-actions">
                <button type="button" onClick={() => setShowAddForm(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={adding} className="btn-primary">
                  {adding ? 'Adding...' : 'Add Payment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="dividend-tabs">
        <button
          className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
        <button
          className={`tab ${activeTab === 'payments' ? 'active' : ''}`}
          onClick={() => setActiveTab('payments')}
        >
          Payments ({payments.length})
        </button>
        <button
          className={`tab ${activeTab === 'holdings' ? 'active' : ''}`}
          onClick={() => setActiveTab('holdings')}
        >
          Holdings ({holdings.length})
        </button>
        <button
          className={`tab ${activeTab === 'calendar' ? 'active' : ''}`}
          onClick={() => setActiveTab('calendar')}
        >
          Calendar ({calendar.length})
        </button>
      </div>

      {activeTab === 'dashboard' && dashboard && (
        <div className="dashboard-grid">
          <div className="stat-card">
            <h3>Total Received</h3>
            <p className="stat-value">{formatCurrency(dashboard.total_dividends_received)}</p>
          </div>
          <div className="stat-card">
            <h3>This Year</h3>
            <p className="stat-value">{formatCurrency(dashboard.dividends_this_year)}</p>
          </div>
          <div className="stat-card">
            <h3>Last Year</h3>
            <p className="stat-value">{formatCurrency(dashboard.dividends_last_year)}</p>
          </div>
          <div className="stat-card">
            <h3>YoY Growth</h3>
            <p className={`stat-value ${dashboard.year_over_year_growth >= 0 ? 'positive' : 'negative'}`}>
              {dashboard.year_over_year_growth >= 0 ? '+' : ''}{dashboard.year_over_year_growth.toFixed(2)}%
            </p>
          </div>
          <div className="stat-card">
            <h3>Portfolio Yield</h3>
            <p className="stat-value">{dashboard.portfolio_dividend_yield.toFixed(2)}%</p>
          </div>
          <div className="stat-card">
            <h3>Avg Yield on Cost</h3>
            <p className="stat-value">{dashboard.yield_on_cost.toFixed(2)}%</p>
          </div>
        </div>
      )}

      {activeTab === 'payments' && (
        <div className="payments-list">
          {payments.length === 0 ? (
            <p className="empty-state">No dividend payments recorded yet.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Ex-Date</th>
                  <th>Payment Date</th>
                  <th>Shares</th>
                  <th>Per Share</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {payments.map(payment => (
                  <tr key={payment.id}>
                    <td>{payment.symbol}</td>
                    <td>{formatDate(payment.ex_dividend_date)}</td>
                    <td>{formatDate(payment.payment_date)}</td>
                    <td>{payment.shares_owned}</td>
                    <td>{formatCurrency(payment.amount_per_share)}</td>
                    <td>{formatCurrency(payment.total_amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'holdings' && (
        <div className="holdings-list">
          {holdings.length === 0 ? (
            <p className="empty-state">No dividend holdings tracked yet.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Shares</th>
                  <th>Cost Basis</th>
                  <th>Annual Dividend</th>
                  <th>Yield on Cost</th>
                  <th>Growth Rate</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map(holding => (
                  <tr key={holding.symbol}>
                    <td>{holding.symbol}</td>
                    <td>{holding.shares_owned}</td>
                    <td>{formatCurrency(holding.cost_basis)}</td>
                    <td>{formatCurrency(holding.annual_dividend)}/yr</td>
                    <td>{holding.yield_on_cost.toFixed(2)}%</td>
                    <td>{holding.dividend_growth_rate.toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'calendar' && (
        <div className="calendar-list">
          {calendar.length === 0 ? (
            <p className="empty-state">No upcoming dividends in the next 60 days.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Ex-Dividend Date</th>
                  <th>Payment Date</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                {calendar.map((entry, idx) => (
                  <tr key={idx}>
                    <td>{entry.symbol}</td>
                    <td>{formatDate(entry.ex_dividend_date)}</td>
                    <td>{formatDate(entry.payment_date)}</td>
                    <td>{formatCurrency(entry.amount_per_share)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}

export default DividendTracker
