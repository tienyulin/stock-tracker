import { useState, useEffect } from 'react'
import { portfolioService, getErrorMessage, Holding, PortfolioSummary } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import './Portfolio.css'

function Portfolio() {
  const { user } = useAuth()
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [summary, setSummary] = useState<PortfolioSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notification, setNotification] = useState<string | null>(null)

  // Add holding form
  const [showAddForm, setShowAddForm] = useState(false)
  const [newSymbol, setNewSymbol] = useState('')
  const [newQuantity, setNewQuantity] = useState('')
  const [newAvgCost, setNewAvgCost] = useState('')
  const [adding, setAdding] = useState(false)

  // Edit holding
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editQuantity, setEditQuantity] = useState('')
  const [editAvgCost, setEditAvgCost] = useState('')

  useEffect(() => {
    if (user?.id) {
      loadPortfolio()
    }
  }, [user?.id])

  const showNotification = (message: string) => {
    setNotification(message)
    setTimeout(() => setNotification(null), 3000)
  }

  const loadPortfolio = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await portfolioService.getPortfolio()
      setHoldings(data.holdings)
      setSummary(data.summary)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const handleAddHolding = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSymbol || !newQuantity || !newAvgCost) return

    try {
      setAdding(true)
      await portfolioService.addHolding(newSymbol.toUpperCase(), parseFloat(newQuantity), parseFloat(newAvgCost))
      showNotification(`${newSymbol.toUpperCase()} added to portfolio`)
      setNewSymbol('')
      setNewQuantity('')
      setNewAvgCost('')
      setShowAddForm(false)
      await loadPortfolio()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setAdding(false)
    }
  }

  const handleUpdateHolding = async (id: string) => {
    try {
      const data: { quantity?: number; avg_cost?: number } = {}
      if (editQuantity) data.quantity = parseFloat(editQuantity)
      if (editAvgCost) data.avg_cost = parseFloat(editAvgCost)
      
      await portfolioService.updateHolding(id, data)
      showNotification('Holding updated')
      setEditingId(null)
      setEditQuantity('')
      setEditAvgCost('')
      await loadPortfolio()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const handleDeleteHolding = async (id: string, symbol: string) => {
    if (!confirm(`Delete ${symbol} from portfolio?`)) return

    try {
      await portfolioService.deleteHolding(id)
      showNotification(`${symbol} removed from portfolio`)
      await loadPortfolio()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const startEdit = (holding: Holding) => {
    setEditingId(holding.id)
    setEditQuantity(holding.quantity.toString())
    setEditAvgCost(holding.avg_cost.toString())
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditQuantity('')
    setEditAvgCost('')
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

  if (!user) {
    return <div className="portfolio-page"><div className="error">Please log in to view portfolio</div></div>
  }

  return (
    <div className="portfolio-page">
      <div className="page-header">
        <h1>Portfolio Overview</h1>
        <button className="btn-primary" onClick={() => setShowAddForm(!showAddForm)}>
          {showAddForm ? 'Cancel' : '+ Add Holding'}
        </button>
      </div>

      {notification && <div className="notification">{notification}</div>}
      {error && <div className="error">{error}</div>}

      {showAddForm && (
        <div className="add-holding-form">
          <h3>Add New Holding</h3>
          <form onSubmit={handleAddHolding}>
            <div className="form-row">
              <div className="form-group">
                <label>Symbol</label>
                <input
                  type="text"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                  placeholder="e.g. AAPL"
                  required
                />
              </div>
              <div className="form-group">
                <label>Quantity</label>
                <input
                  type="number"
                  step="any"
                  value={newQuantity}
                  onChange={(e) => setNewQuantity(e.target.value)}
                  placeholder="Number of shares"
                  required
                />
              </div>
              <div className="form-group">
                <label>Avg Cost (USD)</label>
                <input
                  type="number"
                  step="0.01"
                  value={newAvgCost}
                  onChange={(e) => setNewAvgCost(e.target.value)}
                  placeholder="Cost per share"
                  required
                />
              </div>
            </div>
            <button type="submit" className="btn-primary" disabled={adding}>
              {adding ? 'Adding...' : 'Add Holding'}
            </button>
          </form>
        </div>
      )}

      {summary && (
        <div className="portfolio-summary">
          <div className="summary-card">
            <div className="summary-label">Total Cost</div>
            <div className="summary-value">{formatCurrency(summary.total_cost)}</div>
          </div>
          <div className="summary-card">
            <div className="summary-label">Current Value</div>
            <div className="summary-value">{formatCurrency(summary.total_current_value)}</div>
          </div>
          <div className="summary-card">
            <div className="summary-label">Total Gain/Loss</div>
            <div className={`summary-value ${(summary.total_gain_loss || 0) >= 0 ? 'positive' : 'negative'}`}>
              {formatCurrency(summary.total_gain_loss)}
            </div>
          </div>
          <div className="summary-card">
            <div className="summary-label">Return</div>
            <div className={`summary-value ${(summary.total_gain_loss_pct || 0) >= 0 ? 'positive' : 'negative'}`}>
              {formatPercent(summary.total_gain_loss_pct)}
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading portfolio...</div>
      ) : holdings.length === 0 ? (
        <div className="empty-state">
          <p>No holdings yet. Add your first holding to track your portfolio.</p>
        </div>
      ) : (
        <div className="holdings-table-container">
          <table className="holdings-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Shares</th>
                <th>Avg Cost</th>
                <th>Current Price</th>
                <th>Current Value</th>
                <th>Gain/Loss</th>
                <th>Return</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((holding) => (
                <tr key={holding.id}>
                  <td className="symbol">{holding.symbol}</td>
                  <td>
                    {editingId === holding.id ? (
                      <input
                        type="number"
                        step="any"
                        value={editQuantity}
                        onChange={(e) => setEditQuantity(e.target.value)}
                        className="edit-input"
                      />
                    ) : (
                      holding.quantity
                    )}
                  </td>
                  <td>
                    {editingId === holding.id ? (
                      <input
                        type="number"
                        step="0.01"
                        value={editAvgCost}
                        onChange={(e) => setEditAvgCost(e.target.value)}
                        className="edit-input"
                      />
                    ) : (
                      formatCurrency(holding.avg_cost)
                    )}
                  </td>
                  <td>{formatCurrency(holding.current_price)}</td>
                  <td>{formatCurrency(holding.current_value)}</td>
                  <td className={((holding.gain_loss || 0) >= 0) ? 'positive' : 'negative'}>
                    {formatCurrency(holding.gain_loss)}
                  </td>
                  <td className={((holding.gain_loss_pct || 0) >= 0) ? 'positive' : 'negative'}>
                    {formatPercent(holding.gain_loss_pct)}
                  </td>
                  <td className="actions">
                    {editingId === holding.id ? (
                      <>
                        <button className="btn-small btn-primary" onClick={() => handleUpdateHolding(holding.id)}>
                          Save
                        </button>
                        <button className="btn-small" onClick={cancelEdit}>
                          Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        <button className="btn-small" onClick={() => startEdit(holding)}>
                          Edit
                        </button>
                        <button className="btn-small btn-danger" onClick={() => handleDeleteHolding(holding.id, holding.symbol)}>
                          Delete
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default Portfolio
