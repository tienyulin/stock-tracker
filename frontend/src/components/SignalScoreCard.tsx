import { useEffect, useState } from 'react'
import { stockService, type SignalScore } from '../services/api'
import './SignalScoreCard.css'

interface SignalScoreCardProps {
  symbol: string
  period?: string
  interval?: string
}

function SignalScoreCard({ symbol, period = '3mo', interval = '1d' }: SignalScoreCardProps) {
  const [score, setScore] = useState<SignalScore | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!symbol) return

    const fetchScore = async () => {
      setLoading(true)
      setError(null)
      try {
        const result = await stockService.getSignalScore(symbol, period, interval)
        if (result) {
          setScore(result)
        } else {
          setError('無法取得評分')
        }
      } catch (err) {
        setError('無法取得評分')
      } finally {
        setLoading(false)
      }
    }

    fetchScore()
  }, [symbol, period, interval])

  if (loading) {
    return <div className="signal-score-loading">AI 分析中...</div>
  }

  if (error || !score) {
    return <div className="signal-score-error">{error || '無法取得評分'}</div>
  }

  const getScoreColor = (scoreValue: number): string => {
    if (scoreValue >= 70) return '#10b981' // Buy - green
    if (scoreValue >= 50) return '#34d399' // Hold - light green
    if (scoreValue >= 30) return '#fbbf24' // Hold - yellow
    if (scoreValue >= 15) return '#f97316' // Sell - orange
    return '#ef4444' // Strong Sell - red
  }

  const getVerdictColor = (verdict: string): string => {
    switch (verdict) {
      case 'Buy':
        return '#10b981'
      case 'Sell':
        return '#ef4444'
      default:
        return '#fbbf24'
    }
  }

  const getGaugeWidth = (): string => {
    return `${score.score}%`
  }

  return (
    <div className="signal-score-card">
      <div className="signal-score-header">
        <h3>🎯 AI 買賣評分</h3>
        <span className="symbol-badge">{score.symbol}</span>
      </div>

      <div className="signal-score-main">
        <div className="score-display">
          <div className="score-number" style={{ color: getScoreColor(score.score) }}>
            {score.score}
          </div>
          <div className="score-label">/ 100</div>
        </div>

        <div className="score-gauge">
          <div
            className="score-gauge-fill"
            style={{
              width: getGaugeWidth(),
              backgroundColor: getScoreColor(score.score),
            }}
          />
          <div className="score-gauge-labels">
            <span>Sell</span>
            <span>Hold</span>
            <span>Buy</span>
          </div>
        </div>

        <div className="verdict-badge" style={{ backgroundColor: getVerdictColor(score.verdict) }}>
          {score.verdict}
        </div>

        <div className="confidence-badge">
          信心度: {score.confidence}
        </div>
      </div>

      {score.key_drivers.length > 0 && (
        <div className="key-drivers">
          <h4>📊 關鍵驅動因素</h4>
          <ul>
            {score.key_drivers.map((driver, i) => (
              <li key={i}>{driver}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="indicator-scores">
        <h4>📈 指標評分</h4>
        <div className="indicator-grid">
          {Object.entries(score.indicator_scores).map(([key, value]) => (
            <div key={key} className="indicator-score-item">
              <span className="indicator-key">{key}</span>
              <div className="indicator-bar-container">
                <div
                  className="indicator-bar"
                  style={{
                    width: `${value}%`,
                    backgroundColor: getScoreColor(value),
                  }}
                />
              </div>
              <span className="indicator-value">{value.toFixed(0)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="signal-score-footer">
        <small>分析區間: {score.period} | 間隔: {score.interval}</small>
      </div>
    </div>
  )
}

export default SignalScoreCard
