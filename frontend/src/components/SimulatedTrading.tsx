import { useState } from 'react'
import axios from 'axios'
import './SimulatedTrading.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

interface SimulationResult {
  initial_capital: number
  final_capital: number
  total_return: number
  total_return_percent: number
  num_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  trades: Array<{
    id: string
    timestamp: string
    symbol: string
    action: string
    shares: number
    price: number
    total: number
    reason: string
  }>
}

interface EvaluateResult {
  symbol: string
  should_buy: boolean
  signal: string
  confidence: number
  reason: string
  max_position_percent: number
  bullish_factors: string[]
  bearish_factors: string[]
}

function SimulatedTrading() {
  const [initialCapital, setInitialCapital] = useState(5000)
  const [duration, setDuration] = useState(30)
  const [riskProfile, setRiskProfile] = useState<'conservative' | 'moderate' | 'aggressive'>('moderate')
  const [symbols, setSymbols] = useState('AAPL,GOOGL,MSFT,TSLA')
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [evaluations, setEvaluations] = useState<EvaluateResult[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleEvaluate = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    const symbolList = symbols.split(',').map(s => s.trim()).filter(Boolean)

    try {
      const response = await axios.post(`${API_BASE_URL}/stocks/simulation/evaluate`, {
        symbols: symbolList,
        initial_capital: initialCapital,
        risk_profile: riskProfile,
      })
      setEvaluations(response.data.symbols)
    } catch (err) {
      setError('評估失敗，請稍後再試')
    } finally {
      setLoading(false)
    }
  }

  const handleRunSimulation = async () => {
    setLoading(true)
    setError(null)
    setEvaluations(null)

    const symbolList = symbols.split(',').map(s => s.trim()).filter(Boolean)

    try {
      const response = await axios.post(`${API_BASE_URL}/stocks/simulation/run`, {
        symbols: symbolList,
        initial_capital: initialCapital,
        duration_days: duration,
        risk_profile: riskProfile,
      })
      setResult(response.data)
    } catch (err) {
      setError('模擬失敗，請稍後再試')
    } finally {
      setLoading(false)
    }
  }

  const getReturnClass = (value: number) => {
    if (value > 0) return 'return-positive'
    if (value < 0) return 'return-negative'
    return ''
  }

  const getSignalBadgeClass = (shouldBuy: boolean) => {
    return shouldBuy ? 'badge-buy' : 'badge-sell'
  }

  return (
    <div className="simulated-trading">
      <div className="trading-header">
        <h3>🎮 AI 模擬交易</h3>
        <p className="trading-subtitle">用歷史數據測試我們的推薦系統是否有效</p>
      </div>

      <div className="trading-config">
        <div className="config-row">
          <label>
            起始本金 ($)
            <input
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
              min={1000}
              max={100000}
              step={1000}
            />
          </label>

          <label>
            模擬天數
            <select value={duration} onChange={(e) => setDuration(Number(e.target.value))}>
              <option value={30}>30 天</option>
              <option value={90}>90 天</option>
              <option value={365}>365 天</option>
            </select>
          </label>

          <label>
            風險偏好
            <select value={riskProfile} onChange={(e) => setRiskProfile(e.target.value as any)}>
              <option value="conservative">保守</option>
              <option value="moderate">穩健</option>
              <option value="aggressive">積極</option>
            </select>
          </label>
        </div>

        <div className="config-row">
          <label className="full-width">
            股票符號（用逗號分隔）
            <input
              type="text"
              value={symbols}
              onChange={(e) => setSymbols(e.target.value)}
              placeholder="AAPL, GOOGL, MSFT, TSLA"
            />
          </label>
        </div>

        <div className="config-actions">
          <button onClick={handleEvaluate} disabled={loading} className="btn-evaluate">
            📊 評估
          </button>
          <button onClick={handleRunSimulation} disabled={loading} className="btn-run">
            ▶️ 開始模擬
          </button>
        </div>
      </div>

      {error && <div className="trading-error">{error}</div>}

      {loading && <div className="trading-loading">處理中...</div>}

      {evaluations && (
        <div className="evaluations-section">
          <h4>📊 股票評估結果</h4>
          <div className="evaluations-list">
            {evaluations.map((eval_item) => (
              <div key={eval_item.symbol} className="evaluation-card">
                <div className="eval-header">
                  <span className="eval-symbol">{eval_item.symbol}</span>
                  <span className={`eval-badge ${getSignalBadgeClass(eval_item.should_buy)}`}>
                    {eval_item.should_buy ? '✅ 建議買入' : '❌ 不建議'}
                  </span>
                </div>
                <div className="eval-details">
                  <div className="eval-row">
                    <span>信號:</span>
                    <span>{eval_item.signal}</span>
                  </div>
                  <div className="eval-row">
                    <span>信心度:</span>
                    <span>{eval_item.confidence}%</span>
                  </div>
                  <div className="eval-row">
                    <span>原因:</span>
                    <span>{eval_item.reason}</span>
                  </div>
                  <div className="eval-row">
                    <span>最大投入:</span>
                    <span>{eval_item.max_position_percent}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {result && (
        <div className="simulation-result">
          <h4>📈 模擬結果</h4>

          <div className="result-summary">
            <div className="result-card large">
              <div className="result-label">總資產</div>
              <div className="result-value">${result.final_capital.toLocaleString()}</div>
              <div className={`result-return ${getReturnClass(result.total_return)}`}>
                {result.total_return >= 0 ? '+' : ''}{result.total_return.toLocaleString()}
                ({result.total_return_percent >= 0 ? '+' : ''}{result.total_return_percent.toFixed(2)}%)
              </div>
            </div>

            <div className="result-card">
              <div className="result-label">初始本金</div>
              <div className="result-value">${result.initial_capital.toLocaleString()}</div>
            </div>

            <div className="result-card">
              <div className="result-label">交易次數</div>
              <div className="result-value">{result.num_trades}</div>
            </div>

            <div className="result-card">
              <div className="result-label">勝率</div>
              <div className="result-value">{result.win_rate}%</div>
            </div>

            <div className="result-card">
              <div className="result-label">獲勝</div>
              <div className="result-value win">{result.winning_trades}</div>
            </div>

            <div className="result-card">
              <div className="result-label">虧損</div>
              <div className="result-value loss">{result.losing_trades}</div>
            </div>
          </div>

          {result.trades.length > 0 && (
            <div className="trades-section">
              <h5>📜 交易歷史</h5>
              <div className="trades-list">
                {result.trades.map((trade) => (
                  <div key={trade.id} className={`trade-item ${trade.action.toLowerCase()}`}>
                    <div className="trade-action">
                      <span className={`trade-badge ${trade.action.toLowerCase()}`}>
                        {trade.action}
                      </span>
                      <span className="trade-symbol">{trade.symbol}</span>
                    </div>
                    <div className="trade-details">
                      <span>{trade.shares} 股 @ ${trade.price.toFixed(2)}</span>
                      <span className="trade-total">${trade.total.toFixed(2)}</span>
                    </div>
                    <div className="trade-reason">{trade.reason}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SimulatedTrading
