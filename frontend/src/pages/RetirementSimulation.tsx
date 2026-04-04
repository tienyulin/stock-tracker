import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  simulationService,
  RetirementSimulationRequest,
  RetirementSimulationResponse,
} from '../services/simulationService'
import './RetirementSimulation.css'

type RiskProfile = 'conservative' | 'moderate' | 'aggressive'

const RISK_PROFILES: Record<RiskProfile, Record<string, number>> = {
  conservative: { stocks: 0.3, bonds: 0.5, cash: 0.1, real_estate: 0.1 },
  moderate: { stocks: 0.6, bonds: 0.3, cash: 0.05, real_estate: 0.05 },
  aggressive: { stocks: 0.8, bonds: 0.1, cash: 0.0, real_estate: 0.1 },
}

export default function RetirementSimulation() {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<RetirementSimulationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [riskProfile, setRiskProfile] = useState<RiskProfile>('moderate')

  const [form, setForm] = useState<RetirementSimulationRequest>({
    current_age: 30,
    retirement_age: 65,
    current_savings: 50000,
    monthly_contribution: 1000,
    desired_monthly_income: 5000,
    portfolio_allocation: { ...RISK_PROFILES.moderate },
    num_simulations: 1000,
  })

  const handleRiskProfileChange = (profile: RiskProfile) => {
    setRiskProfile(profile)
    setForm((f) => ({ ...f, portfolio_allocation: { ...RISK_PROFILES[profile] } }))
  }

  const handleAllocationChange = (asset: string, value: string) => {
    const num = parseFloat(value) / 100
    setForm((f) => ({
      ...f,
      portfolio_allocation: { ...f.portfolio_allocation, [asset]: isNaN(num) ? 0 : num },
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await simulationService.runRetirementSimulation(form)
      setResult(res)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Simulation failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const fmt = (n: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)

  const successClass =
    result
      ? result.success_probability >= 0.8
        ? 'high'
        : result.success_probability >= 0.5
        ? 'medium'
        : 'low'
      : ''

  return (
    <div className="retirement-page">
      <h2>🎲 {t('retirement.title', 'Monte Carlo Retirement Simulator')}</h2>

      <div className="retirement-layout">
        {/* --- Form --- */}
        <div className="retirement-form-card">
          <h3>{t('retirement.formTitle', 'Simulation Parameters')}</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>{t('retirement.currentAge', 'Current Age')}</label>
              <input
                type="number"
                min={18}
                max={80}
                value={form.current_age}
                onChange={(e) => setForm((f) => ({ ...f, current_age: Number(e.target.value) }))}
              />
            </div>

            <div className="form-group">
              <label>{t('retirement.retirementAge', 'Target Retirement Age')}</label>
              <input
                type="number"
                min={19}
                max={90}
                value={form.retirement_age}
                onChange={(e) => setForm((f) => ({ ...f, retirement_age: Number(e.target.value) }))}
              />
            </div>

            <div className="form-group">
              <label>{t('retirement.currentSavings', 'Current Portfolio Value ($)')}</label>
              <input
                type="number"
                min={0}
                step={1000}
                value={form.current_savings}
                onChange={(e) => setForm((f) => ({ ...f, current_savings: Number(e.target.value) }))}
              />
            </div>

            <div className="form-group">
              <label>{t('retirement.monthlyContribution', 'Monthly Contribution ($)')}</label>
              <input
                type="number"
                min={0}
                step={100}
                value={form.monthly_contribution}
                onChange={(e) => setForm((f) => ({ ...f, monthly_contribution: Number(e.target.value) }))}
              />
            </div>

            <div className="form-group">
              <label>{t('retirement.desiredIncome', 'Desired Monthly Retirement Income ($)')}</label>
              <input
                type="number"
                min={0}
                step={500}
                value={form.desired_monthly_income}
                onChange={(e) => setForm((f) => ({ ...f, desired_monthly_income: Number(e.target.value) }))}
              />
            </div>

            <div className="form-group">
              <label>{t('retirement.riskProfile', 'Risk Profile')}</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {(['conservative', 'moderate', 'aggressive'] as RiskProfile[]).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => handleRiskProfileChange(p)}
                    style={{
                      flex: 1,
                      padding: '0.4rem',
                      borderRadius: '6px',
                      border: '1px solid',
                      borderColor: riskProfile === p ? 'var(--accent-color, #4f46e5)' : 'var(--border-color)',
                      background: riskProfile === p ? 'var(--accent-color, #4f46e5)' : 'transparent',
                      color: riskProfile === p ? '#fff' : 'var(--text-primary)',
                      cursor: 'pointer',
                      fontSize: '0.8rem',
                      textTransform: 'capitalize',
                    }}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>{t('retirement.portfolioAllocation', 'Portfolio Allocation (%)')}</label>
              <div className="allocation-grid">
                {Object.entries(form.portfolio_allocation).map(([asset, weight]) => (
                  <div key={asset} className="form-group">
                    <label style={{ fontSize: '0.75rem', textTransform: 'capitalize' }}>{asset}</label>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={Math.round(weight * 100)}
                      onChange={(e) => handleAllocationChange(asset, e.target.value)}
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>{t('retirement.numSimulations', 'Number of Simulations')}</label>
              <select
                value={form.num_simulations}
                onChange={(e) => setForm((f) => ({ ...f, num_simulations: Number(e.target.value) }))}
              >
                <option value={500}>500 (Fast)</option>
                <option value={1000}>1,000 (Balanced)</option>
                <option value={5000}>5,000 (Accurate)</option>
                <option value={10000}>10,000 (Thorough)</option>
              </select>
            </div>

            {error && (
              <p style={{ color: '#ef4444', fontSize: '0.875rem', marginTop: '0.5rem' }}>{error}</p>
            )}

            <button type="submit" className="btn-run-simulation" disabled={loading}>
              {loading ? 'Running...' : '▶ Run Simulation'}
            </button>
          </form>
        </div>

        {/* --- Results --- */}
        <div className="retirement-results-card">
          <h3>{t('retirement.resultsTitle', 'Simulation Results')}</h3>

          {!result ? (
            <div className="placeholder-results">
              <div style={{ fontSize: '3rem' }}>🎯</div>
              <p>Configure parameters and run the simulation to see your retirement outlook.</p>
            </div>
          ) : (
            <>
              {/* Success probability */}
              <div className="success-meter">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600 }}>Success Probability</span>
                  <span className={`stat-value ${successClass}`} style={{ fontSize: '1.5rem' }}>
                    {(result.success_probability * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="success-bar-bg">
                  <div
                    className={`success-bar-fill ${successClass}`}
                    style={{ width: `${result.success_probability * 100}%` }}
                  />
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Based on {result.total_simulations.toLocaleString()} simulations · 4% safe withdrawal rate
                </p>
              </div>

              {/* Percentile range */}
              <div className="percentile-range">
                <p style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                  Portfolio Value Range (at retirement)
                </p>
                <div className="range-labels">
                  <span>{fmt(result.percentile_10)} (10th)</span>
                  <span>{fmt(result.percentile_90)} (90th)</span>
                </div>
                <div className="range-bar-bg">
                  <div
                    className="range-bar-fill"
                    style={{
                      left: '0%',
                      width: '100%',
                      background: 'linear-gradient(90deg, #ef4444 0%, #f59e0b 40%, #22c55e 100%)',
                    }}
                  />
                  <div
                    style={{
                      position: 'absolute',
                      left: '50%',
                      top: '-4px',
                      width: '3px',
                      height: '16px',
                      background: 'white',
                      borderRadius: '2px',
                      transform: 'translateX(-50%)',
                    }}
                  />
                </div>
                <div className="range-labels" style={{ marginTop: '0.25rem' }}>
                  <span>Worst case</span>
                  <span style={{ color: '#22c55e', fontWeight: 600 }}>Median: {fmt(result.median_outcome)}</span>
                  <span>Best case</span>
                </div>
              </div>

              {/* Stats grid */}
              <div className="stats-grid" style={{ marginTop: '1rem' }}>
                <div className="stat-item">
                  <div className="stat-label">Median Outcome</div>
                  <div className="stat-value">{fmt(result.median_outcome)}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">Average Outcome</div>
                  <div className="stat-value">{fmt(result.average_outcome)}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">10th Percentile</div>
                  <div className="stat-value danger">{fmt(result.percentile_10)}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">90th Percentile</div>
                  <div className="stat-value success">{fmt(result.percentile_90)}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">Worst Outcome</div>
                  <div className="stat-value danger">{fmt(result.worst_outcome)}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">Best Outcome</div>
                  <div className="stat-value success">{fmt(result.best_outcome)}</div>
                </div>
              </div>

              {/* Assumptions */}
              <div className="assumptions-box">
                <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>📊 Model Assumptions</p>
                <p>Expected return: {(result.assumptions.portfolio_mean * 100).toFixed(1)}% / year</p>
                <p>Volatility: {(result.assumptions.portfolio_std * 100).toFixed(1)}% / year</p>
                <p>Inflation rate: {(result.assumptions.inflation_rate * 100).toFixed(1)}% / year</p>
                <p>Withdrawal period: {result.assumptions.withdrawal_years} years</p>
                <p style={{ marginTop: '0.5rem', fontStyle: 'italic' }}>
                  Years to retirement: {result.years_until_retirement}
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
