import './IndicatorExplain.css'

interface IndicatorExplainProps {
  indicator: string
  value: number
  signal: string
}

const INDICATOR_INFO: Record<string, { name: string; description: string; interpretation: string }> = {
  RSI: {
    name: 'RSI (相對強度指數)',
    description: '衡量股價變動的速度和幅度，範圍 0-100',
    interpretation: 'RSI > 70 表示超買（可能過高），RSI < 30 表示超賣（可能過低）',
  },
  MACD: {
    name: 'MACD (移動平均收斂發散)',
    description: '比較短期和長期指數移動平均線的差異',
    interpretation: 'MACD > 0 表示多頭趨勢，MACD < 0 表示空頭趨勢',
  },
  SMA20: {
    name: 'SMA20 (20日簡單移動平均)',
    description: '過去20個交易日的平均價格',
    interpretation: '價格高於SMA20表示短期趨勢向上，低於則向下',
  },
  SMA50: {
    name: 'SMA50 (50日簡單移動平均)',
    description: '過去50個交易日的平均價格',
    interpretation: '價格高於SMA50表示中期趨勢向上，低於則向下',
  },
  EMA12: {
    name: 'EMA12 (12日指數移動平均)',
    description: '給予近期價格更高權重的移動平均',
    interpretation: '價格高於EMA12表示短期動能向上，低於則向下',
  },
}

function IndicatorExplain({ indicator, value, signal }: IndicatorExplainProps) {
  const info = INDICATOR_INFO[indicator]

  if (!info) {
    return null
  }

  const getSignalEmoji = (sig: string) => {
    switch (sig) {
      case 'STRONG_BUY':
        return '🟢🟢'
      case 'BUY':
        return '🟢'
      case 'HOLD':
        return '🟡'
      case 'SELL':
        return '🔴'
      case 'STRONG_SELL':
        return '🔴🔴'
      default:
        return '⚪'
    }
  }

  return (
    <div className="indicator-explain">
      <div className="indicator-header">
        <h4>{info.name}</h4>
        <span className="indicator-signal-badge">
          {getSignalEmoji(signal)} {signal}
        </span>
      </div>
      <div className="indicator-value-display">
        <span className="current-value">目前數值：{typeof value === 'number' ? value.toFixed(2) : value}</span>
      </div>
      <div className="indicator-description">
        <p><strong>📖 這是什麼？</strong><br />{info.description}</p>
        <p><strong>💡 怎麼解讀？</strong><br />{info.interpretation}</p>
      </div>
    </div>
  )
}

export function IndicatorExplainPanel({ indicators }: { indicators: Array<{ indicator: string; value: number; signal: string }> }) {
  return (
    <div className="indicator-explain-panel">
      <h3>📚 指標說明</h3>
      <p className="panel-intro">
        了解每個技術指標背後的意義，幫助你做出更好的投資決策
      </p>
      <div className="indicators-list">
        {indicators.map((ind, i) => (
          <IndicatorExplain
            key={i}
            indicator={ind.indicator}
            value={ind.value}
            signal={ind.signal}
          />
        ))}
      </div>
    </div>
  )
}

export default IndicatorExplain
