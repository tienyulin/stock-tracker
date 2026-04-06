import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { agentService, type RebalanceResult, type DriftHolding } from '../services/agentApi'
import './RebalanceActionCard.css'

const ACTION_COLORS = {
  BUY: '#22c55e',
  SELL: '#ef4444',
  HOLD: '#6b7280',
}

interface RebalanceActionCardProps {
  onRebalanceComplete?: (result: RebalanceResult) => void
}

export function RebalanceActionCard({ onRebalanceComplete }: RebalanceActionCardProps) {
  const { t } = useTranslation()
  const [preview, setPreview] = useState<RebalanceResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [rebalancing, setRebalancing] = useState(false)
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    loadPreview()
  }, [])

  const loadPreview = async () => {
    try {
      const result = await agentService.getRebalancePreview()
      setPreview(result)
    } catch (err) {
      console.error('Failed to load rebalance preview:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRebalance = async () => {
    setRebalancing(true)
    try {
      const result = await agentService.triggerRebalance()
      if (result) {
        setPreview(result)
        onRebalanceComplete?.(result)
      }
    } catch (err) {
      console.error('Failed to trigger rebalance:', err)
    } finally {
      setRebalancing(false)
    }
  }

  if (loading) {
    return (
      <div className="rebalance-card rebalance-loading">
        <span>{t('common.loading', 'Loading...')}</span>
      </div>
    )
  }

  if (!preview) {
    return (
      <div className="rebalance-card rebalance-empty">
        <span>{t('agent.rebalance.notAvailable', 'Rebalance preview not available')}</span>
      </div>
    )
  }

  const { holdings, summary } = preview
  const hasDrift = summary.total_drift > 0

  return (
    <div className="rebalance-card">
      <div className="rebalance-header">
        <h3>{t('agent.rebalance.title', 'Portfolio Rebalance')}</h3>
        <button
          className="rebalance-details-toggle"
          onClick={() => setShowDetails(!showDetails)}
        >
          {showDetails ? t('agent.rebalance.hideDetails', 'Hide Details') : t('agent.rebalance.showDetails', 'Show Details')}
        </button>
      </div>

      <div className="rebalance-summary">
        <div className="rebalance-summary-item">
          <span className="rebalance-summary-label">{t('agent.rebalance.totalDrift', 'Total Drift')}</span>
          <span className="rebalance-summary-value">{summary.total_drift.toFixed(2)}%</span>
        </div>
        <div className="rebalance-summary-item">
          <span className="rebalance-summary-label">{t('agent.rebalance.buy', 'Buy')}</span>
          <span className="rebalance-summary-value" style={{ color: ACTION_COLORS.BUY }}>
            {summary.buy_count}
          </span>
        </div>
        <div className="rebalance-summary-item">
          <span className="rebalance-summary-label">{t('agent.rebalance.sell', 'Sell')}</span>
          <span className="rebalance-summary-value" style={{ color: ACTION_COLORS.SELL }}>
            {summary.sell_count}
          </span>
        </div>
        <div className="rebalance-summary-item">
          <span className="rebalance-summary-label">{t('agent.rebalance.hold', 'Hold')}</span>
          <span className="rebalance-summary-value" style={{ color: ACTION_COLORS.HOLD }}>
            {summary.hold_count}
          </span>
        </div>
      </div>

      {showDetails && holdings.length > 0 && (
        <div className="rebalance-holdings">
          <div className="rebalance-holdings-header">
            <span>{t('agent.rebalance.holding', 'Holding')}</span>
            <span>{t('agent.rebalance.current', 'Current')}</span>
            <span>{t('agent.rebalance.target', 'Target')}</span>
            <span>{t('agent.rebalance.drift', 'Drift')}</span>
            <span>{t('agent.rebalance.action', 'Action')}</span>
          </div>

          {holdings.map((holding) => (
            <DriftRow key={holding.symbol} holding={holding} />
          ))}
        </div>
      )}

      {showDetails && holdings.length === 0 && (
        <div className="rebalance-empty-message">
          {t('agent.rebalance.noDrift', 'Your portfolio is well balanced. No rebalancing needed.')}
        </div>
      )}

      <div className="rebalance-actions">
        {hasDrift && (
          <p className="rebalance-recommendation">
            {t('agent.rebalance.recommendation', 'Based on your target allocation, rebalancing is recommended.')}
          </p>
        )}
        <button
          className="rebalance-btn"
          onClick={handleRebalance}
          disabled={rebalancing || holdings.length === 0}
        >
          {rebalancing
            ? t('agent.rebalancing', 'Rebalancing...')
            : t('agent.rebalance.execute', 'Execute Rebalance')}
        </button>
      </div>
    </div>
  )
}

function DriftRow({ holding }: { holding: DriftHolding }) {
  const { t } = useTranslation()

  const driftAbs = Math.abs(holding.drift_pct)
  const driftClass = driftAbs > 5 ? 'high' : driftAbs > 2 ? 'medium' : 'low'

  return (
    <div className="drift-row">
      <div className="drift-symbol">
        <span className="drift-symbol-text">{holding.symbol}</span>
        <span className="drift-name">{holding.name}</span>
      </div>
      <span className="drift-current">{(holding.current_weight * 100).toFixed(1)}%</span>
      <span className="drift-target">{(holding.target_weight * 100).toFixed(1)}%</span>
      <span className={`drift-pct drift-${driftClass}`}>
        {holding.drift_pct > 0 ? '+' : ''}{(holding.drift_pct * 100).toFixed(1)}%
      </span>
      <span
        className="drift-action"
        style={{ color: ACTION_COLORS[holding.action] }}
      >
        {t(`agent.rebalance.actions.${holding.action}`, holding.action)}
        {holding.suggested_amount && (
          <span className="drift-amount">
            {holding.action === 'BUY' ? '+' : '-'}${Math.abs(holding.suggested_amount).toFixed(0)}
          </span>
        )}
      </span>
    </div>
  )
}
