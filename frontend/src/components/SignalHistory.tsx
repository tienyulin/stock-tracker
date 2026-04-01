import { useEffect, useState } from 'react'
import { getSignalHistory, clearSignalHistory, type SignalHistoryItem } from '../services/signalHistory'
import './SignalHistory.css'

function SignalHistory() {
  const [history, setHistory] = useState<SignalHistoryItem[]>([])
  const [filter, setFilter] = useState<string>('')

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = () => {
    setHistory(getSignalHistory())
  }

  const handleClear = () => {
    clearSignalHistory()
    setHistory([])
  }

  const filteredHistory = filter
    ? history.filter(item => item.symbol.toLowerCase().includes(filter.toLowerCase()))
    : history

  const getSignalBadgeClass = (signal: string) => {
    switch (signal) {
      case 'STRONG_BUY':
        return 'badge-strong-buy'
      case 'BUY':
        return 'badge-buy'
      case 'HOLD':
        return 'badge-hold'
      case 'SELL':
        return 'badge-sell'
      case 'STRONG_SELL':
        return 'badge-strong-sell'
      default:
        return ''
    }
  }

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp)
    return date.toLocaleString('zh-TW', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="signal-history">
      <div className="history-header">
        <h3>📜 信號歷史</h3>
        <div className="history-controls">
          <input
            type="text"
            placeholder="篩選股票..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="filter-input"
          />
          {history.length > 0 && (
            <button onClick={handleClear} className="clear-btn">
              清除
            </button>
          )}
        </div>
      </div>

      {filteredHistory.length === 0 ? (
        <div className="history-empty">
          <p>尚無信號歷史</p>
          <small>搜尋股票後產生的評估會自動記錄在這裡</small>
        </div>
      ) : (
        <div className="history-list">
          {filteredHistory.map((item) => (
            <div key={item.id} className="history-item">
              <div className="history-item-header">
                <span className="history-symbol">{item.symbol}</span>
                <span className={`history-badge ${getSignalBadgeClass(item.signal.signal)}`}>
                  {item.signal.signal_label}
                </span>
                <span className="history-confidence">
                  {item.signal.confidence}%
                </span>
              </div>
              <div className="history-item-details">
                <span className="history-date">{formatDate(item.timestamp)}</span>
                <span className="history-period">{item.signal.period}</span>
              </div>
              <div className="history-summary">
                {item.signal.bullish_factors.length > 0 && (
                  <span className="bullish">🟢 {item.signal.bullish_factors.length}</span>
                )}
                {item.signal.bearish_factors.length > 0 && (
                  <span className="bearish">🔴 {item.signal.bearish_factors.length}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default SignalHistory
