import {
  useState,
  useRef,
} from 'react'
import { stockService, watchlistService, alertService } from '../services/api'
import type { StockQuote, StockHistory, AlertConditionType } from '../services/api'
import StockIndicators from '../components/StockIndicators'
import StockSignal from '../components/StockSignal'
import StockChart from '../components/StockChart'
import { useAuth } from '../contexts/AuthContext'
import './StockSearch.css'

// Popular US stocks for suggestions
const POPULAR_STOCKS = [
  { symbol: 'AAPL', name: 'Apple Inc.' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.' },
  { symbol: 'MSFT', name: 'Microsoft Corp.' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.' },
  { symbol: 'TSLA', name: 'Tesla Inc.' },
  { symbol: 'META', name: 'Meta Platforms' },
  { symbol: 'NVDA', name: 'NVIDIA Corp.' },
  { symbol: 'JPM', name: 'JPMorgan Chase' },
  { symbol: 'V', name: 'Visa Inc.' },
  { symbol: 'JNJ', name: 'Johnson & Johnson' },
]

type Period = '1W' | '1M' | '3M' | '6M'

const PERIOD_MAP: Record<Period, { period: string; interval: string }> = {
  '1W': { period: '5d', interval: '30m' },
  '1M': { period: '1mo', interval: '1d' },
  '3M': { period: '3mo', interval: '1d' },
  '6M': { period: '6mo', interval: '1d' },
}

function StockSearch() {
  const { user } = useAuth()
  const userId = user?.id || '00000000-0000-0000-0000-000000000001' // fallback for demo
  const [symbol, setSymbol] = useState('')
  const [quote, setQuote] = useState<StockQuote | null>(null)
  const [history, setHistory] = useState<StockHistory | null>(null)
  const [loading, setLoading] = useState(false)
  const [chartLoading, setChartLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [addedToWatchlist, setAddedToWatchlist] = useState(false)
  const [alertType, setAlertType] = useState<AlertConditionType>('above')
  const [alertThreshold, setAlertThreshold] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [period, setPeriod] = useState<Period>('1M')
  const inputRef = useRef<HTMLInputElement>(null)

  // Filter suggestions based on input
  const suggestions = symbol.length > 0
    ? POPULAR_STOCKS.filter(s =>
        s.symbol.toLowerCase().includes(symbol.toLowerCase()) ||
        s.name.toLowerCase().includes(symbol.toLowerCase())
      ).slice(0, 5)
    : POPULAR_STOCKS.slice(0, 8)

  const handleSelectSuggestion = (sym: string) => {
    setSymbol(sym)
    setShowSuggestions(false)
    inputRef.current?.blur()
    // Trigger search
    const form = document.querySelector('.search-form') as HTMLFormElement
    form?.requestSubmit()
  }

  const fetchHistory = async (sym: string, p: Period) => {
    const { period: pPeriod, interval: pInterval } = PERIOD_MAP[p]
    setChartLoading(true)
    try {
      const historyData = await stockService.getStockHistory(sym, pPeriod, pInterval)
      setHistory(historyData)
    } finally {
      setChartLoading(false)
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!symbol.trim()) return

    try {
      setLoading(true)
      setError(null)
      setAddedToWatchlist(false)
      setMessage(null)
      setShowSuggestions(false)
      const result = await stockService.getStockQuote(symbol.toUpperCase())
      if (result) {
        setQuote(result)
        setAlertThreshold(result.price.toString())
        await fetchHistory(symbol.toUpperCase(), period)
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

  const handlePeriodChange = async (p: Period) => {
    setPeriod(p)
    if (quote) {
      await fetchHistory(quote.symbol, p)
    }
  }

  const handleAddToWatchlist = async () => {
    if (!quote) return
    try {
      const watchlists = await watchlistService.getWatchlists(userId)
      let targetWatchlist = watchlists.find(wl => wl.is_default) || watchlists[0]

      if (!targetWatchlist) {
        targetWatchlist = await watchlistService.createWatchlist(userId, 'My Watchlist', true)
      }

      await watchlistService.addItemToWatchlist(userId, targetWatchlist.id, quote.symbol)
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
        userId,
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
      <div className="search-wrapper">
        <form onSubmit={handleSearch} className="search-form">
          <input
            ref={inputRef}
            type="text"
            value={symbol}
            onChange={(e) => {
              setSymbol(e.target.value)
              setShowSuggestions(true)
            }}
            onFocus={() => setShowSuggestions(true)}
            placeholder="Enter stock symbol (e.g., AAPL)"
            className="search-input"
            autoComplete="off"
          />
          <button type="submit" className="search-btn" disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>

        {/* Suggestions dropdown */}
        {showSuggestions && (
          <div className="suggestions-dropdown">
            {suggestions.length > 0 ? (
              suggestions.map(stock => (
                <button
                  key={stock.symbol}
                  className="suggestion-item"
                  onClick={() => handleSelectSuggestion(stock.symbol)}
                >
                  <span className="suggestion-symbol">{stock.symbol}</span>
                  <span className="suggestion-name">{stock.name}</span>
                </button>
              ))
            ) : (
              <div className="suggestion-empty">No matches</div>
            )}
          </div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}
      {message && <div className="success-message">{message}</div>}

      {quote && (
        <div className="stock-details">
          <div className="stock-header">
            <span className="symbol">{quote.symbol}</span>
            <span className="company-name">{quote.name || 'Unknown'}</span>
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

          <StockIndicators symbol={quote.symbol} />

          <StockSignal symbol={quote.symbol} />

          {history && (
            <div className="chart-section">
              <div className="chart-header">
                <h4>Price Chart</h4>
                <div className="period-selector">
                  {(['1W', '1M', '3M', '6M'] as Period[]).map(p => (
                    <button
                      key={p}
                      className={`period-btn ${period === p ? 'active' : ''}`}
                      onClick={() => handlePeriodChange(p)}
                      disabled={chartLoading}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
              {chartLoading ? (
                <div className="chart-loading">Loading chart...</div>
              ) : (
                <StockChart data={history} symbol={quote.symbol} />
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default StockSearch
