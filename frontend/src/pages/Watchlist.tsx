import { useState, useEffect } from 'react'
import { watchlistService } from '../services/api'
import type { WatchlistItem } from '../types'
import './Watchlist.css'

function Watchlist() {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadWatchlist()
  }, [])

  const loadWatchlist = async () => {
    try {
      setLoading(true)
      const items = await watchlistService.getWatchlist('demo-user')
      setWatchlist(items)
    } catch (err) {
      console.error('Failed to load watchlist:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRemove = async (symbol: string) => {
    try {
      await watchlistService.removeStock('demo-user', symbol)
      setWatchlist(watchlist.filter(item => item.symbol !== symbol))
    } catch (err) {
      console.error('Failed to remove stock:', err)
    }
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="watchlist">
      <h2>My Watchlist</h2>
      {watchlist.length === 0 ? (
        <p className="empty-message">Your watchlist is empty. Add stocks from the search page.</p>
      ) : (
        <ul className="watchlist-items">
          {watchlist.map(item => (
            <li key={item.id} className="watchlist-item">
              <span className="symbol">{item.symbol}</span>
              <span className="name">{item.name}</span>
              <button
                className="remove-btn"
                onClick={() => handleRemove(item.symbol)}
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default Watchlist
