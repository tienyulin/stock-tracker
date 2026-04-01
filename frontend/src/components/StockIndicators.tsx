import { useEffect, useState } from 'react'
import { stockService, type StockIndicators } from '../services/api'
import './StockIndicators.css'

interface StockIndicatorsProps {
  symbol: string
  period?: string
  interval?: string
}

function StockIndicators({ symbol, period = '3mo', interval = '1d' }: StockIndicatorsProps) {
  const [indicators, setIndicators] = useState<StockIndicators | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!symbol) return

    const fetchIndicators = async () => {
      setLoading(true)
      setError(null)
      try {
        const result = await stockService.getStockIndicators(symbol, period, interval)
        console.log('getStockIndicators result:', result)
        if (result) {
          setIndicators(result)
        } else {
          setError('Failed to load indicators')
        }
      } catch (err) {
        console.error('fetchIndicators error:', err)
        setError('Failed to load indicators')
      } finally {
        setLoading(false)
      }
    }

    fetchIndicators()
  }, [symbol, period, interval])

  if (loading) {
    return <div className="indicators-loading">Loading indicators...</div>
  }

  if (error || !indicators) {
    return <div className="indicators-error">{error || 'No data'}</div>
  }

  const getRsiColor = (rsi: number | null | undefined) => {
    if (rsi == null) return ''
    if (rsi >= 70) return 'overbought'
    if (rsi <= 30) return 'oversold'
    return ''
  }

  const getRsiLabel = (rsi: number | null | undefined) => {
    if (rsi == null) return 'N/A'
    if (rsi >= 70) return 'Overbought'
    if (rsi <= 30) return 'Oversold'
    return 'Neutral'
  }

  return (
    <div className="indicators-container">
      <h3>📊 Technical Indicators</h3>
      
      <div className="indicators-grid">
        {/* RSI */}
        <div className={`indicator-card ${getRsiColor(indicators.rsi)}`}>
          <div className="indicator-label">RSI (14)</div>
          <div className="indicator-value">
            {indicators.rsi != null ? indicators.rsi.toFixed(2) : 'N/A'}
          </div>
          <div className="indicator-status">
            {getRsiLabel(indicators.rsi)}
          </div>
        </div>

        {/* MACD */}
        {indicators.macd && (
          <div className="indicator-card">
            <div className="indicator-label">MACD (12/26/9)</div>
            <div className="indicator-value">
              {indicators.macd.macd_line != null ? indicators.macd.macd_line.toFixed(4) : 'N/A'}
            </div>
            <div className="indicator-detail">
              Signal: {indicators.macd.signal_line != null ? indicators.macd.signal_line.toFixed(4) : 'N/A'}
            </div>
            <div className={`indicator-histogram ${indicators.macd.histogram >= 0 ? 'positive' : 'negative'}`}>
              Histogram: {indicators.macd.histogram != null ? indicators.macd.histogram.toFixed(4) : 'N/A'}
            </div>
          </div>
        )}

        {/* SMA */}
        <div className="indicator-card">
          <div className="indicator-label">SMA</div>
          <div className="indicator-values">
            {Object.entries(indicators.sma || {}).map(([key, value]) => (
              <div key={key} className="indicator-row">
                <span className="indicator-key">{key}:</span>
                <span className="indicator-val">{value != null ? value.toFixed(2) : 'N/A'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* EMA */}
        <div className="indicator-card">
          <div className="indicator-label">EMA</div>
          <div className="indicator-values">
            {Object.entries(indicators.ema || {}).map(([key, value]) => (
              <div key={key} className="indicator-row">
                <span className="indicator-key">{key}:</span>
                <span className="indicator-val">{value != null ? value.toFixed(2) : 'N/A'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default StockIndicators
