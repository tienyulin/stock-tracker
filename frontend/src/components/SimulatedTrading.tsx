import { useState, useMemo } from 'react'
import axios from 'axios'
import './SimulatedTrading.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

interface Trade {
  id: string
  timestamp: string
  symbol: string
  action: 'BUY' | 'SELL'
  shares: number
  price: number
  total: number
  reason: string
}

interface SimulationResult {
  initial_capital: number
  final_capital: number
  total_return: number
  total_return_percent: number
  num_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  trades: Trade[]
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

type SortField = 'timestamp' | 'total' | 'symbol'
type SortDir = 'asc' | 'desc'

function SimulatedTrading() {
  const [initialCapital, setInitialCapital] = useState(5000)
  const [duration, setDuration] = useState(30)
  const [riskProfile, setRiskProfile] = useState<'conservative' | 'moderate' | 'aggressive'>('moderate')
  const [symbols, setSymbols] = useState('AAPL,GOOGL,MSFT,TSLA')
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [evaluations, setEvaluations] = useState<EvaluateResult[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Trade history detail state
  const [filterAction, setFilterAction] = useState<'ALL' | 'BUY' | 'SELL'>('ALL')
  const [filterSymbol, setFilterSymbol] = useState('')
  const [sortField, setSortField] = useState<SortField>('timestamp')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [expandedTradeId, setExpandedTradeId] = useState<string | null>(null)

  // Pair BUY and SELL trades to calculate P&L and holding period
  const pairedTrades = useMemo(() => {
    if (!result) return []
    const buyMap = new Map<string, Trade>()
    const pairs: Array<{
      buy: Trade
      sell: Trade
      holdingDays: number
      pnl: number
      pnlPercent: number
    }> = []

    for (const trade of result.trades) {
      if (trade.action === 'BUY') {
        buyMap.set(trade.symbol, trade)
      } else if (trade.action === 'SELL') {
        const buy = buyMap.get(trade.symbol)
        if (buy) {
          const buyDate = new Date(buy.timestamp)
          const sellDate = new Date(trade.timestamp)
          const holdingMs = sellDate.getTime() - buyDate.getTime()
          const holdingDays = Math.round(holdingMs / (1000 * 60 * 60 * 24))
          const pnl = trade.total - buy.total
          const pnlPercent = (pnl / buy.total) * 100
          pairs.push({ buy, sell: trade, holdingDays, pnl, pnlPercent })
          buyMap.delete(trade.symbol)
        }
      }
    }
    return pairs
  }, [result])

  // Build trade summary for display (interleaved with pairs)
  const displayTrades = useMemo(() => {
    if (!result) return []
    let trades = [...result.trades]

    // Filter
    if (filterAction !== 'ALL') {
      trades = trades.filter(t => t.action === filterAction)
    }
    if (filterSymbol.trim()) {
      trades = trades.filter(t => t.symbol.toLowerCase().includes(filterSymbol.toLowerCase()))
    }

    // Sort
    trades.sort((a, b) => {
      let cmp = 0
      if (sortField === 'timestamp') {
        cmp = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      } else if (sortField === 'total') {
        cmp = a.total - b.total
      } else if (sortField === 'symbol') {
        cmp = a.symbol.localeCompare(b.symbol)
      }
      return sortDir === 'asc' ? cmp : -cmp
    })

    return trades
  }, [result, filterAction, filterSymbol, sortField, sortDir])

  // Trade summary stats
  const tradeStats = useMemo(() => {
    if (!result) return null
    const buys = result.trades.filter(t => t.action === 'BUY').length
    const sells = result.trades.filter(t => t.action === 'SELL').length
    const avgHolding = pairedTrades.length > 0
      ? Math.round(pairedTrades.reduce((sum, p) => sum + p.holdingDays, 0) / pairedTrades.length)
      : 0
    const totalPnl = pairedTrades.reduce((sum, p) => sum + p.pnl, 0)
    return { buys, sells, avgHolding, totalPnl }
  }, [result, pairedTrades])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDir('desc')
    }
  }

  const exportCSV = () => {
    if (!result) return
    const headers = ['ID', 'Timestamp', 'Symbol', 'Action', 'Shares', 'Price', 'Total', 'Reason']
    const rows = result.trades.map(t => [
      t.id, t.timestamp, t.symbol, t.action, t.shares, t.price.toFixed(2), t.total.toFixed(2), t.reason
    ])
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `trades_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

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

  const formatDate = (ts: string) => {
    return new Date(ts).toLocaleString('zh-TW', {
      month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    })
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
              <div className="trades-section-header">
                <h5>📜 交易歷史</h5>
                {tradeStats && (
                  <div className="trade-stats">
                    <span>買入 {tradeStats.buys}</span>
                    <span>賣出 {tradeStats.sells}</span>
                    <span>平均持有 {tradeStats.avgHolding} 天</span>
                    <span className={tradeStats.totalPnl >= 0 ? 'pnl-positive' : 'pnl-negative'}>
                      總損益 ${tradeStats.totalPnl.toFixed(2)}
                    </span>
                  </div>
                )}
              </div>

              {/* Filter & Sort Controls */}
              <div className="trades-controls">
                <div className="trade-filters">
                  <label>
                    動作
                    <select value={filterAction} onChange={e => setFilterAction(e.target.value as any)}>
                      <option value="ALL">全部</option>
                      <option value="BUY">買入</option>
                      <option value="SELL">賣出</option>
                    </select>
                  </label>
                  <label>
                    股票
                    <input
                      type="text"
                      value={filterSymbol}
                      onChange={e => setFilterSymbol(e.target.value)}
                      placeholder="搜尋..."
                    />
                  </label>
                </div>
                <div className="trade-sorts">
                  <span>排序:</span>
                  <button
                    className={`sort-btn ${sortField === 'timestamp' ? 'active' : ''}`}
                    onClick={() => handleSort('timestamp')}
                  >
                    時間 {sortField === 'timestamp' && (sortDir === 'asc' ? '↑' : '↓')}
                  </button>
                  <button
                    className={`sort-btn ${sortField === 'total' ? 'active' : ''}`}
                    onClick={() => handleSort('total')}
                  >
                    金額 {sortField === 'total' && (sortDir === 'asc' ? '↑' : '↓')}
                  </button>
                  <button
                    className={`sort-btn ${sortField === 'symbol' ? 'active' : ''}`}
                    onClick={() => handleSort('symbol')}
                  >
                    股票 {sortField === 'symbol' && (sortDir === 'asc' ? '↑' : '↓')}
                  </button>
                  <button className="btn-export" onClick={exportCSV}>
                    📥 匯出 CSV
                  </button>
                </div>
              </div>

              <div className="trades-list">
                {displayTrades.length === 0 ? (
                  <div className="trades-empty">沒有符合條件的交易</div>
                ) : (
                  displayTrades.map((trade) => {
                    const isExpanded = expandedTradeId === trade.id
                    // Find paired trade info
                    const pair = pairedTrades.find(
                      p => (p.buy.id === trade.id || p.sell.id === trade.id)
                    )
                    const isBuy = trade.action === 'BUY'
                    const paired = isBuy ? pair?.sell : pair?.buy

                    return (
                      <div
                        key={trade.id}
                        className={`trade-item ${trade.action.toLowerCase()} ${isExpanded ? 'expanded' : ''}`}
                        onClick={() => setExpandedTradeId(isExpanded ? null : trade.id)}
                      >
                        <div className="trade-main">
                          <div className="trade-action">
                            <span className={`trade-badge ${trade.action.toLowerCase()}`}>
                              {trade.action}
                            </span>
                            <span className="trade-symbol">{trade.symbol}</span>
                            {isExpanded && <span className="trade-expand-hint">▲ 收合</span>}
                            {!isExpanded && <span className="trade-expand-hint">▼ 展開</span>}
                          </div>
                          <div className="trade-details">
                            <span>{trade.shares} 股 @ ${trade.price.toFixed(2)}</span>
                            <span className="trade-total">${trade.total.toFixed(2)}</span>
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="trade-expanded">
                            <div className="trade-expanded-row">
                              <span className="trade-expanded-label">時間</span>
                              <span>{formatDate(trade.timestamp)}</span>
                            </div>
                            <div className="trade-expanded-row">
                              <span className="trade-expanded-label">原因</span>
                              <span>{trade.reason}</span>
                            </div>
                            {pair && (
                              <>
                                <div className="trade-expanded-row">
                                  <span className="trade-expanded-label">配對{isBuy ? '賣出' : '買入'}</span>
                                  <span>
                                    {paired?.symbol} · {paired?.shares} 股 @ ${Number(paired?.price).toFixed(2)}
                                  </span>
                                </div>
                                <div className="trade-expanded-row">
                                  <span className="trade-expanded-label">持有期間</span>
                                  <span>{pair.holdingDays} 天</span>
                                </div>
                                <div className="trade-expanded-row">
                                  <span className="trade-expanded-label">該筆損益</span>
                                  <span className={pair.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}>
                                    ${pair.pnl.toFixed(2)} ({pair.pnlPercent >= 0 ? '+' : ''}{pair.pnlPercent.toFixed(2)}%)
                                  </span>
                                </div>
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SimulatedTrading
