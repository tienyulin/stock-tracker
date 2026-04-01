import { useEffect, useState } from 'react'
import { stockService, type StockSignal } from '../services/api'
import { addToSignalHistory } from '../services/signalHistory'
import { IndicatorExplainPanel } from './IndicatorExplain'
import './StockSignal.css'

interface StockSignalProps {
  symbol: string
  period?: string
  interval?: string
}

function StockSignal({ symbol, period = '3mo', interval = '1d' }: StockSignalProps) {
  const [signal, setSignal] = useState<StockSignal | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showExplain, setShowExplain] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

  useEffect(() => {
    if (!symbol) return

    const fetchSignal = async () => {
      setLoading(true)
      setError(null)
      try {
        const result = await stockService.getStockSignal(symbol, period, interval)
        if (result) {
          setSignal(result)
          addToSignalHistory(symbol, result)
        } else {
          setError('Failed to load signal')
        }
      } catch (err) {
        setError('Failed to load signal')
      } finally {
        setLoading(false)
      }
    }

    fetchSignal()
  }, [symbol, period, interval])

  if (loading) {
    return <div className="signal-loading">分析中...</div>
  }

  if (error || !signal) {
    return <div className="signal-error">{error || '無法取得信號'}</div>
  }

  const getSignalClass = (signalType: string) => {
    switch (signalType) {
      case 'STRONG_BUY':
        return 'signal-strong-buy'
      case 'BUY':
        return 'signal-buy'
      case 'HOLD':
        return 'signal-hold'
      case 'SELL':
        return 'signal-sell'
      case 'STRONG_SELL':
        return 'signal-strong-sell'
      default:
        return ''
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return '#10b981'
    if (confidence >= 60) return '#34d399'
    if (confidence >= 40) return '#fbbf24'
    if (confidence >= 20) return '#f97316'
    return '#ef4444'
  }

  return (
    <div className={`signal-container ${getSignalClass(signal.signal)}`}>
      <div className="signal-header">
        <h3>📈 股票評估</h3>
        <div className="signal-badge">
          <span className={`signal-type ${getSignalClass(signal.signal)}`}>
            {signal.signal_label}
          </span>
          <span
            className="confidence"
            style={{ color: getConfidenceColor(signal.confidence) }}
          >
            信心度: {signal.confidence}%
          </span>
        </div>
      </div>

      <div className="signal-summary">
        <p>{signal.summary}</p>
      </div>

      <div className="signal-details">
        {signal.bullish_factors.length > 0 && (
          <div className="signal-factors bullish">
            <h4>🟢 看漲因素</h4>
            <ul>
              {signal.bullish_factors.map((factor, i) => (
                <li key={i}>{factor}</li>
              ))}
            </ul>
          </div>
        )}

        {signal.bearish_factors.length > 0 && (
          <div className="signal-factors bearish">
            <h4>🔴 看跌因素</h4>
            <ul>
              {signal.bearish_factors.map((factor, i) => (
                <li key={i}>{factor}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="indicator-signals">
        <div className="signals-header">
          <h4>📊 指標分析</h4>
          <div className="signal-toggles">
            <button
              className={`toggle-btn ${showExplain ? 'active' : ''}`}
              onClick={() => setShowExplain(!showExplain)}
            >
              📚 看說明
            </button>
            <button
              className={`toggle-btn ${showAdvanced ? 'active' : ''}`}
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              ⚙️ 進階
            </button>
          </div>
        </div>
        <div className="indicator-list">
          {signal.indicators.map((ind, i) => (
            <div key={i} className={`indicator-item ${getSignalClass(ind.signal)}`}>
              <span className="indicator-name">{ind.indicator}</span>
              {showAdvanced ? (
                <span className="indicator-value">
                  {typeof ind.value === 'number' ? ind.value.toFixed(4) : ind.value}
                </span>
              ) : (
                <span className="indicator-value">
                  {typeof ind.value === 'number' ? ind.value.toFixed(2) : ind.value}
                </span>
              )}
              <span className="indicator-signal">{ind.signal}</span>
            </div>
          ))}
        </div>
      </div>

      {showExplain && (
        <IndicatorExplainPanel indicators={signal.indicators} />
      )}

      <div className="signal-footer">
        <small>分析區間: {signal.period} | 間隔: {signal.interval}</small>
      </div>
    </div>
  )
}

export default StockSignal
