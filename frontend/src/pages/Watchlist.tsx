import { useState, useEffect } from 'react'
import { watchlistService, stockService } from '../services/api'
import type { Watchlist, WatchlistItem, StockQuote } from '../services/api'
import './Watchlist.css'

const DEMO_USER_ID = '00000000-0000-0000-0000-000000000001'

function Watchlist() {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stockQuotes, setStockQuotes] = useState<Record<string, StockQuote>>({})

  useEffect(() => {
    loadWatchlists()
  }, [])

  const loadWatchlists = async () => {
    try {
      setLoading(true)
      setError(null)
      const lists = await watchlistService.getWatchlists(DEMO_USER_ID)
      setWatchlists(lists)
      
      // Load quotes for all symbols
      const allSymbols = lists.flatMap(wl => wl.items.map(item => item.symbol))
      const uniqueSymbols = [...new Set(allSymbols)]
      
      const quotes: Record<string, StockQuote> = {}
      for (const symbol of uniqueSymbols) {
        const quote = await stockService.getStockQuote(symbol)
        if (quote) {
          quotes[symbol] = quote
        }
      }
      setStockQuotes(quotes)
    } catch (err) {
      setError('Failed to load watchlists')
    } finally {
      setLoading(false)
    }
  }

  const handleAddSymbol = async (symbol: string) => {
    try {
      if (watchlists.length === 0) {
        // Create a default watchlist
        const newWl = await watchlistService.createWatchlist(DEMO_USER_ID, 'My Watchlist', true)
        setWatchlists([newWl])
        await watchlistService.addItemToWatchlist(DEMO_USER_ID, newWl.id, symbol)
      } else {
        const defaultWl = watchlists.find(wl => wl.is_default) || watchlists[0]
        await watchlistService.addItemToWatchlist(DEMO_USER_ID, defaultWl.id, symbol)
      }
      await loadWatchlists()
    } catch (err) {
      console.error('Failed to add symbol:', err)
    }
  }

  const handleRemoveItem = async (watchlistId: string, itemId: string) => {
    try {
      await watchlistService.removeItemFromWatchlist(DEMO_USER_ID, watchlistId, itemId)
      await loadWatchlists()
    } catch (err) {
      console.error('Failed to remove item:', err)
    }
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
      {watchlists.length === 0 ? (
        <p className="empty-message">Your watchlist is empty. Add stocks from the search page.</p>
      ) : (
        watchlists.map(watchlist => (
          <div key={watchlist.id} className="watchlist-section">
            <h3>{watchlist.name}</h3>
            {watchlist.items.length === 0 ? (
              <p className="empty-message">No stocks in this watchlist.</p>
            ) : (
              <ul className="watchlist-items">
                {watchlist.items.map(item => {
                  const quote = stockQuotes[item.symbol]
                  return (
                    <li key={item.id} className="watchlist-item">
                      <span className="symbol">{item.symbol}</span>
                      {quote && (
                        <>
                          <span className="price">${quote.price.toFixed(2)}</span>
                          <span className="volume">Vol: {quote.volume.toLocaleString()}</span>
                        </>
                      )}
                      <button
                        className="remove-btn"
                        onClick={() => handleRemoveItem(watchlist.id, item.id)}
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
