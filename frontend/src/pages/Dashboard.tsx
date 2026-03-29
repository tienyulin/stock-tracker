import { useState, useEffect } from 'react'
import { stockService } from '../services/api'
import type { StockQuote } from '../services/api'
import './Dashboard.css'

function Dashboard() {
  const [quotes, setQuotes] = useState<StockQuote[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadWatchlistStocks()
  }, [])

  const loadWatchlistStocks = async () => {
    try {
      setLoading(true)
      setError(null)
      // Demo stocks - in production would come from user's watchlist
      const demoSymbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
      
      const results = await Promise.all(
        demoSymbols.map(async (symbol) => {
          const quote = await stockService.getStockQuote(symbol)
          return quote
        })
      )
      
      setQuotes(results.filter((q): q is StockQuote => q !== null))
    } catch (err) {
      setError('Failed to load stocks')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      {quotes.length === 0 ? (
        <p className="empty-state">No stocks to display. Add stocks to your watchlist.</p>
      ) : (
        <div className="stock-grid">
          {quotes.map(quote => (
            <div key={quote.symbol} className="stock-card">
              <div className="stock-header">
                <span className="stock-symbol">{quote.symbol}</span>
                <span className="stock-market-state">{quote.market_state || 'Unknown'}</span>
              </div>
              <div className="stock-price">${quote.price.toFixed(2)}</div>
              <div className="stock-volume">Vol: {quote.volume.toLocaleString()}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Dashboard
