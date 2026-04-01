import { useState, useEffect } from 'react'
import { stockService } from '../services/api'
import type { StockQuote } from '../services/api'
import { StockCardSkeleton } from '../components/Skeleton'
import './Dashboard.css'

// Major market indices
const MARKET_INDICES = [
  { symbol: '^GSPC', name: 'S&P 500' },
  { symbol: '^IXIC', name: 'Nasdaq' },
  { symbol: '^DJI', name: 'Dow Jones' },
  { symbol: '^TNX', name: '10Y Treasury' },
]

function getMarketStatus(indices: StockQuote[]) {
  if (indices.length === 0) return null
  const states = indices.map(q => q.market_state?.toLowerCase())
  if (states.every(s => s === 'regular')) return 'open'
  if (states.some(s => s === 'pre')) return 'pre'
  if (states.some(s => s === 'post')) return 'after'
  return 'closed'
}

function formatChange(change: number | undefined, percent: number | undefined) {
  if (change === undefined || change === null) return null
  const sign = change >= 0 ? '+' : ''
  const pctStr = percent !== undefined ? ` (${sign}${percent.toFixed(2)}%)` : ''
  return `${sign}${change.toFixed(2)}${pctStr}`
}

function Dashboard() {
  const [quotes, setQuotes] = useState<StockQuote[]>([])
  const [indices, setIndices] = useState<StockQuote[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadAll()
  }, [])

  const loadAll = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load watchlist stocks
      const demoSymbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
      const [watchlistResults, indexResults] = await Promise.all([
        Promise.all(demoSymbols.map(s => stockService.getStockQuote(s))),
        Promise.all(MARKET_INDICES.map(i => stockService.getStockQuote(i.symbol))),
      ])

      const validQuotes = watchlistResults.filter((q): q is StockQuote => q !== null)
      const validIndices = indexResults.filter((q): q is StockQuote => q !== null)

      // Debug: log results
      console.log('Watchlist results:', watchlistResults)
      console.log('Index results:', indexResults)

      setQuotes(validQuotes)
      setIndices(validIndices)

      // If we got no data at all, show an error
      if (validQuotes.length === 0 && validIndices.length === 0) {
        setError('Failed to load data - please check your connection')
      }
    } catch (err) {
      console.error('Dashboard loadAll error:', err)
      setError('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="dashboard">
        <h2>Dashboard</h2>
        <section className="market-section">
          <h3>Market Overview</h3>
          <div className="stock-grid indices-grid">
            {[1, 2, 3, 4].map(i => <StockCardSkeleton key={i} />)}
          </div>
        </section>
        <section className="watchlist-section">
          <h3>My Watchlist</h3>
          <div className="stock-grid">
            {[1, 2, 3, 4].map(i => <StockCardSkeleton key={i} />)}
          </div>
        </section>
      </div>
    )
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>

      {/* Market status banner */}
      {indices.length > 0 && (() => {
        const status = getMarketStatus(indices)
        const statusConfig = {
          open: { label: 'Market Open', class: 'market-open' },
          pre: { label: 'Pre-Market', class: 'market-pre' },
          after: { label: 'After Hours', class: 'market-after' },
          closed: { label: 'Market Closed', class: 'market-closed' },
        }[status ?? 'closed']
        return (
          <div className={`market-status-banner ${statusConfig.class}`}>
            <span className="market-status-dot" />
            {statusConfig.label} — Prices may be delayed
          </div>
        )
      })()}

      {/* Market Overview */}
      {indices.length > 0 && (
        <section className="market-section">
          <h3>Market Overview</h3>
          <div className="stock-grid indices-grid">
            {indices.map((quote, i) => {
              const changeStr = formatChange(quote.change, quote.change_percent)
              const isUp = (quote.change ?? 0) >= 0
              return (
                <div key={quote.symbol} className="stock-card index-card">
                  <div className="stock-header">
                    <span className="stock-symbol">{MARKET_INDICES[i]?.name || quote.symbol}</span>
                    {quote.market_state && (
                      <span className={`market-badge ${quote.market_state.toLowerCase()}`}>
                        {quote.market_state}
                      </span>
                    )}
                  </div>
                  <div className="stock-price">
                    {quote.price != null && quote.price > 0
                      ? `$${quote.price.toFixed(2)}`
                      : 'N/A'}
                  </div>
                  {changeStr && (
                    <div className={`stock-change ${isUp ? 'up' : 'down'}`}>
                      {changeStr}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* Watchlist */}
      {quotes.length === 0 ? (
        <p className="empty-state">No stocks to display. Add stocks to your watchlist.</p>
      ) : (
        <section className="watchlist-section">
          <h3>My Watchlist</h3>
          <div className="stock-grid">
            {quotes.map(quote => {
              const changeStr = formatChange(quote.change, quote.change_percent)
              const isUp = (quote.change ?? 0) >= 0
              return (
                <div key={quote.symbol} className="stock-card">
                  <div className="stock-header">
                    <span className="stock-symbol">{quote.name || quote.symbol}</span>
                    {quote.market_state && (
                      <span className="stock-market-state">{quote.market_state}</span>
                    )}
                  </div>
                  <div className="stock-price">
                    {quote.price != null && quote.price > 0
                      ? `$${quote.price.toFixed(2)}`
                      : 'N/A'}
                  </div>
                  {changeStr && (
                    <div className={`stock-change ${isUp ? 'up' : 'down'}`}>
                      {changeStr}
                    </div>
                  )}
                  <div className="stock-volume">Vol: {quote.volume.toLocaleString()}</div>
                </div>
              )
            })}
          </div>
        </section>
      )}
    </div>
  )
}

export default Dashboard
