import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { agentService, getErrorMessage } from '../../services/api'
import type { TaxImpactSummary } from '../../types/agent'
import './TaxImpact.css'

function TaxImpact() {
  const { t } = useTranslation()
  const [taxImpact, setTaxImpact] = useState<TaxImpactSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTaxImpact()
  }, [])

  const loadTaxImpact = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await agentService.getTaxImpact()
      setTaxImpact(data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const chartData = taxImpact ? [
    {
      name: t('agent.tax.savings', 'Est. Tax Savings'),
      value: taxImpact.estimated_savings,
      fill: '#2e7d32',
    },
    {
      name: t('agent.tax.harvestedLosses', 'Harvested Losses'),
      value: taxImpact.harvested_losses,
      fill: '#c62828',
    },
  ] : []

  if (loading) {
    return <div className="tax-impact-loading">Loading tax impact...</div>
  }

  return (
    <div className="tax-impact">
      <div className="tax-impact-header">
        <h3>{t('agent.tax.title', 'Tax Impact Visualizer')}</h3>
        <button className="btn-refresh" onClick={loadTaxImpact}>↻ {t('common.refresh', 'Refresh')}</button>
      </div>

      {error && <div className="error">{error}</div>}

      {taxImpact && (
        <>
          <div className="tax-summary-cards">
            <div className="summary-card savings">
              <div className="card-label">{t('agent.tax.estimatedSavings', 'Estimated Tax Savings')}</div>
              <div className="card-value">
                ${taxImpact.estimated_savings.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
            <div className="summary-card losses">
              <div className="card-label">{t('agent.tax.harvestedLossesLabel', 'Harvested Losses')}</div>
              <div className="card-value">
                ${taxImpact.harvested_losses.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
            <div className={`summary-card wash-sale ${taxImpact.wash_sale_risk ? 'at-risk' : ''}`}>
              <div className="card-label">{t('agent.tax.washSaleRisk', 'Wash Sale Risk')}</div>
              <div className="card-value">
                {taxImpact.wash_sale_risk ? t('common.yes', 'Yes') : t('common.no', 'No')}
              </div>
            </div>
          </div>

          <div className="tax-chart-container">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} tickFormatter={v => `$${v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}`} />
                <Tooltip
                  formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
                  contentStyle={{ borderRadius: 8, border: '1px solid #e0e0e0', fontSize: 13 }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="tax-footer">
            <span className="tax-timestamp">
              {t('agent.tax.calculatedAt', 'Calculated at')}: {new Date(taxImpact.calculated_at).toLocaleString()}
            </span>
          </div>
        </>
      )}
    </div>
  )
}

export default TaxImpact
