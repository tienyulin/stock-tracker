import { useState, useEffect } from 'react'
import { stockService } from '../services/api'
import type { StockInfo } from '../types'
import './Dashboard.css'

function Dashboard() {
  const [stocks, setStocks] = useState<StockInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadWatchlistStocks()
  }, [])

  const loadWatchlistStocks = async () => {
    try {
      setLoading(true)
      setError(null)
      // For demo, show some default stocks
      const demoSymbols = ['AAPL', 'GOOGL', 'MSFT']
      const stockInfos = await Promise.all(
        demoSymbols.map(symbol => stockService.getStockInfo(symbol))
      )
      setStocks(stockInfos.filter((s): s is StockInfo => s !== null))
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
      <div className="stock-grid">
        {stocks.map(stock => (
          <div key={stock.symbol} className="stock-card">
            <div className="stock-header">
              <span className="stock-symbol">{stock.symbol}</span>
              <span className="stock-exchange">{stock.exchange}</span>
            </div>
            <div className="stock-name">{stock.name}</div>
            <div className="stock-info">
              <span className="stock-currency">{stock.currency}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Dashboard
