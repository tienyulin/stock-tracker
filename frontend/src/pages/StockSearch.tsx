import { useState } from 'react'
import { stockService, watchlistService, alertService } from '../services/api'
import type { StockInfo, PriceAlert } from '../types'
import './StockSearch.css'

function StockSearch() {
  const [symbol, setSymbol] = useState('')
  const [stock, setStock] = useState<StockInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [addedToWatchlist, setAddedToWatchlist] = useState(false)
  const [alertType, setAlertType] = useState('PRICE_ABOVE')
  const [alertThreshold, setAlertThreshold] = useState('')

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!symbol.trim()) return

    try {
      setLoading(true)
      setError(null)
      setAddedToWatchlist(false)
      const result = await stockService.getStockInfo(symbol.toUpperCase())
      if (result) {
        setStock(result)
        setAlertThreshold('')
      } else {
        setError('Stock not found')
        setStock(null)
      }
    } catch (err) {
      setError('Failed to search stock')
      setStock(null)
    } finally {
      setLoading(false)
    }
  }

  const handleAddToWatchlist = async () => {
    if (!stock) return
    try {
      await watchlistService.addStock('demo-user', stock.symbol, stock.name)
      setAddedToWatchlist(true)
    } catch (err) {
      console.error('Failed to add to watchlist:', err)
    }
  }

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!stock || !alertThreshold) return
    try {
      await alertService.createAlert('demo-user', stock.symbol, alertType, parseFloat(alertThreshold))
      alert('Alert created successfully!')
      setAlertThreshold('')
    } catch (err) {
      console.error('Failed to create alert:', err)
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

      {stock && (
        <div className="stock-details">
          <div className="stock-header">
            <span className="symbol">{stock.symbol}</span>
            <span className="exchange">{stock.exchange}</span>
          </div>
          <div className="stock-name">{stock.name}</div>
          <div className="stock-currency">Currency: {stock.currency}</div>

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
                onChange={(e) => setAlertType(e.target.value)}
                className="alert-select"
              >
                <option value="PRICE_ABOVE">Price Above</option>
                <option value="PRICE_BELOW">Price Below</option>
                <option value="PRICE_CHANGE_PERCENT">Change %</option>
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
