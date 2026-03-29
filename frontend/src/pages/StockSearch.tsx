import { useState } from 'react'
import { stockService, watchlistService, alertService } from '../services/api'
import type { StockQuote, AlertConditionType } from '../services/api'
import './StockSearch.css'

const DEMO_USER_ID = '00000000-0000-0000-0000-000000000001'

function StockSearch() {
  const [symbol, setSymbol] = useState('')
  const [quote, setQuote] = useState<StockQuote | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [addedToWatchlist, setAddedToWatchlist] = useState(false)
  const [alertType, setAlertType] = useState<AlertConditionType>('above')
  const [alertThreshold, setAlertThreshold] = useState('')
  const [message, setMessage] = useState<string | null>(null)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!symbol.trim()) return

    try {
      setLoading(true)
      setError(null)
      setAddedToWatchlist(false)
      setMessage(null)
      const result = await stockService.getStockQuote(symbol.toUpperCase())
      if (result) {
        setQuote(result)
        setAlertThreshold(result.price.toString())
      } else {
        setError('Stock not found')
        setQuote(null)
      }
    } catch (err) {
      setError('Failed to search stock')
      setQuote(null)
    } finally {
      setLoading(false)
    }
  }

  const handleAddToWatchlist = async () => {
    if (!quote) return
    try {
      // Get or create default watchlist
      const watchlists = await watchlistService.getWatchlists(DEMO_USER_ID)
      let targetWatchlist = watchlists.find(wl => wl.is_default) || watchlists[0]
      
      if (!targetWatchlist) {
        targetWatchlist = await watchlistService.createWatchlist(DEMO_USER_ID, 'My Watchlist', true)
      }
      
      await watchlistService.addItemToWatchlist(DEMO_USER_ID, targetWatchlist.id, quote.symbol)
      setAddedToWatchlist(true)
      setMessage('Added to watchlist!')
    } catch (err) {
      console.error('Failed to add to watchlist:', err)
      setMessage('Failed to add to watchlist')
    }
  }

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!quote || !alertThreshold) return
    try {
      await alertService.createAlert(
        DEMO_USER_ID,
        quote.symbol,
        alertType,
        parseFloat(alertThreshold)
      )
      setMessage('Alert created successfully!')
    } catch (err) {
      console.error('Failed to create alert:', err)
      setMessage('Failed to create alert')
    }
  }

  return (
    <div className="stock-search">
      <h2>Search Stocks</h2>
      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="Enter stock symbol (e.g., AAPL)"
          className="search-input"
        />
        <button type="submit" className="search-btn" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <div className="error-message">{error}</div>}
      {message && <div className="success-message">{message}</div>}

      {quote && (
        <div className="stock-details">
          <div className="stock-header">
            <span className="symbol">{quote.symbol}</span>
            <span className="market-state">{quote.market_state || 'Unknown'}</span>
          </div>
          <div className="stock-price">${quote.price.toFixed(2)}</div>
          <div className="stock-volume">Volume: {quote.volume.toLocaleString()}</div>

          <div className="stock-actions">
            <button
              className="action-btn watchlist-btn"
              onClick={handleAddToWatchlist}
              disabled={addedToWatchlist}
            >
              {addedToWatchlist ? 'Added to Watchlist' : 'Add to Watchlist'}
            </button>
          </div>

          <form onSubmit={handleCreateAlert} className="alert-form">
            <h3>Create Price Alert</h3>
            <div className="alert-inputs">
              <select
                value={alertType}
                onChange={(e) => setAlertType(e.target.value as AlertConditionType)}
                className="alert-select"
              >
                <option value="above">Price Above</option>
                <option value="below">Price Below</option>
                <option value="change_pct">Change %</option>
              </select>
              <input
                type="number"
                value={alertThreshold}
                onChange={(e) => setAlertThreshold(e.target.value)}
                placeholder="Threshold value"
                className="threshold-input"
                step="0.01"
              />
              <button type="submit" className="create-alert-btn">
                Create Alert
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}

export default StockSearch
