import { useState, useEffect } from 'react'
import {
  passiveIncomeService,
  PassiveIncomeDashboard,
  PassiveIncomeSource,
  FireProgress,
} from '../services/passiveIncomeService'
import { useAuth } from '../contexts/AuthContext'
import './PassiveIncomeDashboard.css'

const SOURCE_TYPE_LABELS: Record<string, string> = {
  dividend: 'Dividend',
  rental: 'Rental',
  interest: 'Interest',
  royalty: 'Royalty',
  pension: 'Pension',
  social_security: 'Social Security',
  p2p: 'P2P Lending',
  other: 'Other',
}

function PassiveIncomeDashboardPage() {
  const { user } = useAuth()
  const [dashboard, setDashboard] = useState<PassiveIncomeDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'sources' | 'fire'>('overview')

  // Add source modal
  const [showAddSource, setShowAddSource] = useState(false)
  const [newSourceName, setNewSourceName] = useState('')
  const [newSourceType, setNewSourceType] = useState<PassiveIncomeSource['source_type']>('dividend')
  const [newMonthly, setNewMonthly] = useState('')
  const [newAnnual, setNewAnnual] = useState('')
  const [newCurrency, setNewCurrency] = useState('USD')
  const [adding, setAdding] = useState(false)

  // Add record modal
  const [showAddRecord, setShowAddRecord] = useState(false)
  const [recordSourceId, setRecordSourceId] = useState('')
  const [recordAmount, setRecordAmount] = useState('')
  const [recordDate, setRecordDate] = useState('')
  const [recordType, setRecordType] = useState<'received' | 'expected' | 'missed'>('received')
  const [addingRecord, setAddingRecord] = useState(false)

  // FIRE goal
  const [showFireForm, setShowFireForm] = useState(false)
  const [fireTarget, setFireTarget] = useState('')
  const [fireExpenses, setFireExpenses] = useState('')
  const [fireDate, setFireDate] = useState('')
  const [savingFire, setSavingFire] = useState(false)

  useEffect(() => {
    if (user?.id) loadData()
  }, [user?.id])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await passiveIncomeService.getDashboard()
      setDashboard(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load passive income data')
    } finally {
      setLoading(false)
    }
  }

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSourceName || !newSourceType) return
    try {
      setAdding(true)
      await passiveIncomeService.createSource({
        name: newSourceName,
        source_type: newSourceType,
        expected_monthly_income: parseFloat(newMonthly) || 0,
        expected_annual_income: parseFloat(newAnnual) || 0,
        currency: newCurrency,
      })
      setShowAddSource(false)
      setNewSourceName('')
      setNewSourceType('dividend')
      setNewMonthly('')
      setNewAnnual('')
      loadData()
    } catch {
      alert('Failed to add income source')
    } finally {
      setAdding(false)
    }
  }

  const handleAddRecord = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!recordSourceId || !recordAmount || !recordDate) return
    try {
      setAddingRecord(true)
      await passiveIncomeService.addRecord({
        source_id: recordSourceId,
        amount: parseFloat(recordAmount),
        record_date: recordDate,
        record_type: recordType,
      })
      setShowAddRecord(false)
      setRecordSourceId('')
      setRecordAmount('')
      setRecordDate('')
      loadData()
    } catch {
      alert('Failed to add record')
    } finally {
      setAddingRecord(false)
    }
  }

  const handleSaveFireGoal = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!fireTarget || !fireExpenses) return
    try {
      setSavingFire(true)
      await passiveIncomeService.upsertFireGoal({
        target_annual_income: parseFloat(fireTarget),
        monthly_expenses: parseFloat(fireExpenses),
        target_date: fireDate || undefined,
      })
      setShowFireForm(false)
      loadData()
    } catch {
      alert('Failed to save FIRE goal')
    } finally {
      setSavingFire(false)
    }
  }

  const handleDeleteSource = async (id: string) => {
    if (!confirm('Delete this income source? Records will also be deleted.')) return
    try {
      await passiveIncomeService.deleteSource(id)
      loadData()
    } catch {
      alert('Failed to delete source')
    }
  }

  const formatCurrency = (amount: number, currency = 'USD') =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount)

  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const maxMonthly = dashboard?.annual_summary.monthly
    ? Math.max(...dashboard.annual_summary.monthly, 1)
    : 1

  if (loading) return <div className="pi-loading">Loading passive income data...</div>
  if (error) return <div className="pi-error">{error}</div>

  return (
    <div className="passive-income-page">
      <div className="pi-header">
        <h1>Passive Income Tracker</h1>
        <div className="header-actions">
          <button className="btn-secondary" onClick={() => setShowAddRecord(true)}>
            + Record Payment
          </button>
          <button className="btn-primary" onClick={() => setShowAddSource(true)}>
            + Add Source
          </button>
        </div>
      </div>

      {/* Add Source Modal */}
      {showAddSource && (
        <div className="modal-overlay" onClick={() => setShowAddSource(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Add Income Source</h2>
            <form onSubmit={handleAddSource}>
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={newSourceName}
                  onChange={e => setNewSourceName(e.target.value)}
                  placeholder="e.g. Rental Property, AAPL Dividends"
                  required
                />
              </div>
              <div className="form-group">
                <label>Type</label>
                <select
                  value={newSourceType}
                  onChange={e => setNewSourceType(e.target.value as PassiveIncomeSource['source_type'])}
                >
                  {Object.entries(SOURCE_TYPE_LABELS).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Expected Monthly Income</label>
                <input
                  type="number"
                  step="0.01"
                  value={newMonthly}
                  onChange={e => setNewMonthly(e.target.value)}
                  placeholder="0.00"
                />
              </div>
              <div className="form-group">
                <label>Expected Annual Income</label>
                <input
                  type="number"
                  step="0.01"
                  value={newAnnual}
                  onChange={e => setNewAnnual(e.target.value)}
                  placeholder="0.00"
                />
              </div>
              <div className="form-group">
                <label>Currency</label>
                <select value={newCurrency} onChange={e => setNewCurrency(e.target.value)}>
                  <option value="USD">USD</option>
                  <option value="TWD">TWD</option>
                  <option value="HKD">HKD</option>
                  <option value="JPY">JPY</option>
                  <option value="EUR">EUR</option>
                </select>
              </div>
              <div className="form-actions">
                <button type="button" onClick={() => setShowAddSource(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={adding} className="btn-primary">
                  {adding ? 'Adding...' : 'Add Source'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Record Modal */}
      {showAddRecord && (
        <div className="modal-overlay" onClick={() => setShowAddRecord(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Record Payment</h2>
            <form onSubmit={handleAddRecord}>
              <div className="form-group">
                <label>Source</label>
                <select
                  value={recordSourceId}
                  onChange={e => setRecordSourceId(e.target.value)}
                  required
                >
                  <option value="">Select source...</option>
                  {dashboard?.sources.map(s => (
                    <option key={s.id} value={s.id}>{s.name} ({SOURCE_TYPE_LABELS[s.source_type]})</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Amount</label>
                <input
                  type="number"
                  step="0.01"
                  value={recordAmount}
                  onChange={e => setRecordAmount(e.target.value)}
                  placeholder="0.00"
                  required
                />
              </div>
              <div className="form-group">
                <label>Date</label>
                <input
                  type="date"
                  value={recordDate}
                  onChange={e => setRecordDate(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Type</label>
                <select
                  value={recordType}
                  onChange={e => setRecordType(e.target.value as typeof recordType)}
                >
                  <option value="received">Received</option>
                  <option value="expected">Expected</option>
                  <option value="missed">Missed</option>
                </select>
              </div>
              <div className="form-actions">
                <button type="button" onClick={() => setShowAddRecord(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={addingRecord} className="btn-primary">
                  {addingRecord ? 'Adding...' : 'Add Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* FIRE Form Modal */}
      {showFireForm && (
        <div className="modal-overlay" onClick={() => setShowFireForm(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Set FIRE Goal</h2>
            <form onSubmit={handleSaveFireGoal}>
              <div className="form-group">
                <label>Target Annual Passive Income ($)</label>
                <input
                  type="number"
                  step="100"
                  value={fireTarget}
                  onChange={e => setFireTarget(e.target.value)}
                  placeholder="e.g. 60000"
                  required
                />
              </div>
              <div className="form-group">
                <label>Monthly Expenses ($)</label>
                <input
                  type="number"
                  step="100"
                  value={fireExpenses}
                  onChange={e => setFireExpenses(e.target.value)}
                  placeholder="e.g. 4000"
                  required
                />
              </div>
              <div className="form-group">
                <label>Target Date (optional)</label>
                <input
                  type="date"
                  value={fireDate}
                  onChange={e => setFireDate(e.target.value)}
                />
              </div>
              <div className="form-actions">
                <button type="button" onClick={() => setShowFireForm(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={savingFire} className="btn-primary">
                  {savingFire ? 'Saving...' : 'Save Goal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="pi-tabs">
        <button className={`tab ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>
          Overview
        </button>
        <button className={`tab ${activeTab === 'sources' ? 'active' : ''}`} onClick={() => setActiveTab('sources')}>
          Income Sources ({dashboard?.sources.length ?? 0})
        </button>
        <button className={`tab ${activeTab === 'fire' ? 'active' : ''}`} onClick={() => setActiveTab('fire')}>
          FIRE Progress
        </button>
      </div>

      {dashboard && activeTab === 'overview' && (
        <>
          {/* Stats Grid */}
          <div className="pi-stats-grid">
            <div className="pi-stat-card">
              <h3>Annual Total</h3>
              <p className="pi-stat-value">{formatCurrency(dashboard.annual_summary.total)}</p>
            </div>
            <div className="pi-stat-card">
              <h3>Monthly Average</h3>
              <p className="pi-stat-value">
                {formatCurrency(dashboard.annual_summary.total / 12)}
              </p>
            </div>
            <div className="pi-stat-card">
              <h3>Income Sources</h3>
              <p className="pi-stat-value">{dashboard.sources.length}</p>
            </div>
            <div className="pi-stat-card">
              <h3>FIRE Progress</h3>
              <p className="pi-stat-value">
                {dashboard.fire_progress
                  ? `${dashboard.fire_progress.progress_percentage.toFixed(1)}%`
                  : '—'}
              </p>
            </div>
          </div>

          {/* Annual Trend Chart (ASCII-style bar chart) */}
          <div className="pi-section">
            <h2>{dashboard.annual_summary.year} Annual Trend</h2>
            <div className="pi-bar-chart">
              {dashboard.annual_summary.monthly.map((amount, i) => (
                <div key={i} className="pi-bar-col">
                  <div
                    className="pi-bar"
                    style={{ height: `${(amount / maxMonthly) * 100}%` }}
                    title={formatCurrency(amount)}
                  />
                  <span className="pi-bar-label">{months[i]}</span>
                  <span className="pi-bar-amount">{formatCurrency(amount)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Source Breakdown */}
          {Object.keys(dashboard.monthly_summary.by_type).length > 0 && (
            <div className="pi-section">
              <h2>This Month — by Type</h2>
              <div className="pi-type-breakdown">
                {Object.entries(dashboard.monthly_summary.by_type).map(([type, amount]) => (
                  <div key={type} className="pi-type-item">
                    <span className="pi-type-label">{SOURCE_TYPE_LABELS[type] || type}</span>
                    <span className="pi-type-amount">{formatCurrency(amount)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {dashboard && activeTab === 'sources' && (
        <>
          {dashboard.sources.length === 0 ? (
            <div className="pi-empty">
              <p>No income sources yet.</p>
              <button className="btn-primary" onClick={() => setShowAddSource(true)}>
                + Add Your First Source
              </button>
            </div>
          ) : (
            <div className="pi-sources-list">
              {dashboard.sources.map(source => (
                <div key={source.id} className="pi-source-card">
                  <div className="pi-source-header">
                    <div>
                      <h3>{source.name}</h3>
                      <span className="pi-source-type">
                        {SOURCE_TYPE_LABELS[source.source_type] || source.source_type}
                      </span>
                    </div>
                    <button
                      className="btn-danger-sm"
                      onClick={() => handleDeleteSource(source.id)}
                    >
                      Delete
                    </button>
                  </div>
                  <div className="pi-source-stats">
                    <div className="pi-source-stat">
                      <span>Monthly</span>
                      <strong>{formatCurrency(source.expected_monthly_income, source.currency)}</strong>
                    </div>
                    <div className="pi-source-stat">
                      <span>Annual</span>
                      <strong>{formatCurrency(source.expected_annual_income, source.currency)}</strong>
                    </div>
                    {source.yield_on_cost != null && (
                      <div className="pi-source-stat">
                        <span>YOC</span>
                        <strong>{source.yield_on_cost.toFixed(2)}%</strong>
                      </div>
                    )}
                  </div>
                  {source.description && (
                    <p className="pi-source-desc">{source.description}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {dashboard && activeTab === 'fire' && (
        <>
          {!dashboard.fire_progress ? (
            <div className="pi-empty">
              <p>No FIRE goal set yet.</p>
              <button className="btn-primary" onClick={() => setShowFireForm(true)}>
                Set FIRE Goal
              </button>
            </div>
          ) : (
            <>
              <div className="pi-fire-header">
                <div>
                  <h2>FIRE Progress</h2>
                  <p>Financial Independence, Retire Early</p>
                </div>
                <button className="btn-secondary" onClick={() => setShowFireForm(true)}>
                  Edit Goal
                </button>
              </div>

              {/* Progress Bar */}
              <div className="pi-fire-progress-bar">
                <div
                  className="pi-fire-progress-fill"
                  style={{ width: `${Math.min(dashboard.fire_progress.progress_percentage, 100)}%` }}
                />
              </div>
              <p className="pi-fire-progress-label">
                {dashboard.fire_progress.progress_percentage.toFixed(1)}% of way to FIRE
              </p>

              <div className="pi-stats-grid">
                <div className="pi-stat-card">
                  <h3>Current Passive Income</h3>
                  <p className="pi-stat-value">
                    {formatCurrency(dashboard.fire_progress.current_passive_income, dashboard.fire_progress.currency)}
                  </p>
                </div>
                <div className="pi-stat-card">
                  <h3>Target Annual Income</h3>
                  <p className="pi-stat-value">
                    {formatCurrency(dashboard.fire_progress.target_annual_income, dashboard.fire_progress.currency)}
                  </p>
                </div>
                <div className="pi-stat-card">
                  <h3>Monthly Expenses</h3>
                  <p className="pi-stat-value">
                    {formatCurrency(dashboard.fire_progress.monthly_expenses, dashboard.fire_progress.currency)}
                  </p>
                </div>
                <div className="pi-stat-card">
                  <h3>Monthly Target</h3>
                  <p className="pi-stat-value">
                    {formatCurrency(dashboard.fire_progress.monthly_target, dashboard.fire_progress.currency)}
                  </p>
                </div>
                {dashboard.fire_progress.months_to_target > 0 && (
                  <div className="pi-stat-card">
                    <h3>Est. Months to FIRE</h3>
                    <p className="pi-stat-value">
                      {Math.round(dashboard.fire_progress.months_to_target / 12)} years
                    </p>
                  </div>
                )}
                {dashboard.fire_progress.target_date && (
                  <div className="pi-stat-card">
                    <h3>Target Date</h3>
                    <p className="pi-stat-value">
                      {new Date(dashboard.fire_progress.target_date).toLocaleDateString()}
                    </p>
                  </div>
                )}
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}

export default PassiveIncomeDashboardPage
