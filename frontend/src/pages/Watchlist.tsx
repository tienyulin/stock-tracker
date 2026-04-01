import { useState, useEffect } from 'react'
import { watchlistService, stockService } from '../services/api'
import type { Watchlist, StockQuote } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import './Watchlist.css'

type SortKey = 'symbol' | 'price'

function Watchlist() {
  const { user } = useAuth()
  const [watchlists, setWatchlists] = useState<Watchlist[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stockQuotes, setStockQuotes] = useState<Record<string, StockQuote>>({})
  const [sortKey, setSortKey] = useState<SortKey>('symbol')
  const [newListName, setNewListName] = useState('')
  const [creating, setCreating] = useState(false)
  const [notification, setNotification] = useState<string | null>(null)

  useEffect(() => {
    if (user?.id) {
      loadWatchlists()
    }
  }, [user?.id])

  const userId = user?.id || ''

  const showNotification = (message: string) => {
    setNotification(message)
    setTimeout(() => setNotification(null), 3000)
  }

  const loadWatchlists = async () => {
    try {
      setLoading(true)
      setError(null)
      const lists = await watchlistService.getWatchlists(userId)
      setWatchlists(lists)

      // Load quotes for all symbols in parallel
      const allSymbols = lists.flatMap(wl => wl.items.map(item => item.symbol))
      const uniqueSymbols = [...new Set(allSymbols)]

      if (uniqueSymbols.length > 0) {
        const quotesResults = await Promise.all(
          uniqueSymbols.map(symbol => stockService.getStockQuote(symbol))
        )
        const quotes: Record<string, StockQuote> = {}
        quotesResults.forEach((quote, i) => {
          if (quote) quotes[uniqueSymbols[i]] = quote
        })
        setStockQuotes(quotes)
      }
    } catch (err) {
      setError('Failed to load watchlists')
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveItem = async (watchlistId: string, itemId: string, symbol: string) => {
    try {
      await watchlistService.removeItemFromWatchlist(userId, watchlistId, itemId)
      showNotification(`${symbol} removed from watchlist`)
      await loadWatchlists()
    } catch (err) {
      showNotification('Failed to remove item')
    }
  }

  const handleCreateWatchlist = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newListName.trim()) return
    try {
      setCreating(true)
      await watchlistService.createWatchlist(userId, newListName.trim(), false)
      setNewListName('')
      showNotification('Watchlist created')
      await loadWatchlists()
    } catch (err) {
      showNotification('Failed to create watchlist')
    } finally {
      setCreating(false)
    }
  }

  const sortedItems = (items: Watchlist['items']) => {
    return [...items].sort((a, b) => {
      if (sortKey === 'symbol') {
        return a.symbol.localeCompare(b.symbol)
      }
      const priceA = stockQuotes[a.symbol]?.price ?? 0
      const priceB = stockQuotes[b.symbol]?.price ?? 0
      return priceB - priceA
    })
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="watchlist">
      <h2>My Watchlist</h2>

      {/* Notification toast */}
      {notification && <div className="notification">{notification}</div>}

      {/* Sort controls */}
      <div className="watchlist-controls">
        <div className="sort-controls">
          <span>Sort by:</span>
          <button
            className={`sort-btn ${sortKey === 'symbol' ? 'active' : ''}`}
            onClick={() => setSortKey('symbol')}
          >
            Symbol
          </button>
          <button
            className={`sort-btn ${sortKey === 'price' ? 'active' : ''}`}
            onClick={() => setSortKey('price')}
          >
            Price
          </button>
        </div>
        <button className="refresh-btn" onClick={loadWatchlists}>↻ Refresh</button>
      </div>

      {/* Create new watchlist */}
      <form className="create-watchlist-form" onSubmit={handleCreateWatchlist}>
        <input
          type="text"
          value={newListName}
          onChange={(e) => setNewListName(e.target.value)}
          placeholder="New watchlist name..."
          className="watchlist-name-input"
        />
        <button type="submit" className="create-btn" disabled={creating || !newListName.trim()}>
          {creating ? 'Creating...' : '+ Create'}
        </button>
      </form>

      {watchlists.length === 0 ? (
        <p className="empty-message">No watchlists yet. Create one above!</p>
      ) : (
        watchlists.map(watchlist => (
          <div key={watchlist.id} className="watchlist-section">
            <h3>{watchlist.name} ({watchlist.items.length})</h3>
            {watchlist.items.length === 0 ? (
              <p className="empty-message">No stocks. Add from search page.</p>
            ) : (
              <ul className="watchlist-items">
                {sortedItems(watchlist.items).map(item => {
                  const quote = stockQuotes[item.symbol]
                  return (
                    <li key={item.id} className="watchlist-item">
                      <span className="symbol">{item.symbol}</span>
                      {quote ? (
                        <>
                          <span className="price">${quote.price.toFixed(2)}</span>
                          <span className="volume">Vol: {quote.volume.toLocaleString()}</span>
                        </>
                      ) : (
                        <span className="loading-price">Loading...</span>
                      )}
                      <button
                        className="remove-btn"
                        onClick={() => handleRemoveItem(watchlist.id, item.id, item.symbol)}
                      >
                        Remove
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>
        ))
      )}
    </div>
  )
}

export default Watchlist
