import { useState, useEffect } from 'react'
import {
  fixedIncomeService,
  Bond,
  BondAnalytics,
  TermDeposit,
  MaturityAlert,
} from '../services/fixedIncomeService'
import './FixedIncomeDashboard.css'

const BOND_TYPE_LABELS: Record<string, string> = {
  government: 'Government Bond',
  corporate: 'Corporate Bond',
  municipal: 'Municipal Bond',
  treasury: 'Treasury',
  high_yield: 'High Yield',
}

const fmt = (n: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)
const fmtPct = (n: number) => `${(n * 100).toFixed(3)}%`

export default function FixedIncomeDashboard() {
  const [tab, setTab] = useState<'overview' | 'bonds' | 'deposits'>('overview')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Bond state
  const [bonds, setBonds] = useState<Bond[]>([])
  const [selectedBond, setSelectedBond] = useState<Bond | null>(null)
  const [analytics, setAnalytics] = useState<BondAnalytics | null>(null)
  const [showBondForm, setShowBondForm] = useState(false)
  const [saving, setSaving] = useState(false)

  // Term deposit state
  const [deposits, setDeposits] = useState<TermDeposit[]>([])
  const [alerts, setAlerts] = useState<MaturityAlert[]>([])
  const [showDepositForm, setShowDepositForm] = useState(false)

  useEffect(() => { loadAll() }, [])

  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const [b, d, a] = await Promise.all([
        fixedIncomeService.listBonds(),
        fixedIncomeService.listTermDeposits(),
        fixedIncomeService.getMaturityAlerts(90),
      ])
      setBonds(b)
      setDeposits(d)
      setAlerts(a)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const loadBondAnalytics = async (bond: Bond) => {
    setSelectedBond(bond)
    try {
      const a = await fixedIncomeService.getBondAnalytics(bond.id)
      setAnalytics(a)
    } catch {
      setAnalytics(null)
    }
  }

  // ─── Bond Form ───────────────────────────────────────────────────────────────
  const emptyBond = () => ({
    name: '', bond_type: 'corporate', face_value: 10000,
    coupon_rate: 0.03, purchase_price: 10000,
    purchase_date: new Date().toISOString().split('T')[0],
    maturity_date: new Date(Date.now() + 5 * 365 * 86400 * 1000).toISOString().split('T')[0],
    ticker: '', credit_rating: '', current_market_value: null as number | null,
    currency: 'USD', notes: null as string | null,
  })

  const [bondForm, setBondForm] = useState<ReturnType<typeof emptyBond>>(emptyBond())

  const submitBond = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await fixedIncomeService.createBond(bondForm)
      setShowBondForm(false)
      setBondForm(emptyBond())
      await loadAll()
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to save bond')
    } finally {
      setSaving(false)
    }
  }

  const deleteBond = async (id: string) => {
    if (!confirm('Delete this bond?')) return
    await fixedIncomeService.deleteBond(id)
    setSelectedBond(null)
    setAnalytics(null)
    await loadAll()
  }

  // ─── Term Deposit Form ───────────────────────────────────────────────────────
  const emptyDeposit = () => ({
    name: '', bank_name: '', principal: 10000,
    interest_rate: 0.015, term_months: 12,
    start_date: new Date().toISOString().split('T')[0],
    maturity_date: new Date(Date.now() + 365 * 86400 * 1000).toISOString().split('T')[0],
    compound_frequency: 'annually', auto_renew: false, notes: null as string | null,
  })

  const [depositForm, setDepositForm] = useState<ReturnType<typeof emptyDeposit>>(emptyDeposit())

  const submitDeposit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await fixedIncomeService.createTermDeposit(depositForm)
      setShowDepositForm(false)
      setDepositForm(emptyDeposit())
      await loadAll()
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to save term deposit')
    } finally {
      setSaving(false)
    }
  }

  const deleteDeposit = async (id: string) => {
    if (!confirm('Delete this term deposit?')) return
    await fixedIncomeService.deleteTermDeposit(id)
    await loadAll()
  }

  const totalBondValue = bonds.reduce((s, b) => s + (b.current_market_value ?? b.purchase_price), 0)
  const totalDepositPrincipal = deposits.reduce((s, d) => s + d.principal, 0)
  const totalDepositMaturity = deposits.reduce((s, d) => s + (d.maturity_value ?? 0), 0)

  if (loading) return <div className="fi-loading"><div className="spinner" />Loading...</div>
  if (error) return <div className="fi-error">{error} <button onClick={loadAll}>Retry</button></div>

  return (
    <div className="fixed-income-dashboard">
      <div className="fi-header">
        <h1>Fixed Income Dashboard</h1>
        <div className="fi-tabs">
          <button className={tab === 'overview' ? 'active' : ''} onClick={() => setTab('overview')}>Overview</button>
          <button className={tab === 'bonds' ? 'active' : ''} onClick={() => setTab('bonds')}>Bonds ({bonds.length})</button>
          <button className={tab === 'deposits' ? 'active' : ''} onClick={() => setTab('deposits')}>Term Deposits ({deposits.length})</button>
        </div>
      </div>

      {tab === 'overview' && (
        <div className="fi-overview">
          <div className="fi-cards">
            <div className="fi-card">
              <h3>Bonds</h3>
              <div className="fi-card-value">{fmt(totalBondValue)}</div>
              <div className="fi-card-sub">{bonds.length} positions</div>
            </div>
            <div className="fi-card">
              <h3>Term Deposits</h3>
              <div className="fi-card-value">{fmt(totalDepositMaturity)}</div>
              <div className="fi-card-sub">principal: {fmt(totalDepositPrincipal)}</div>
            </div>
            <div className="fi-card">
              <h3>Maturity Alerts</h3>
              <div className="fi-card-value">{alerts.length}</div>
              <div className="fi-card-sub">next 90 days</div>
            </div>
          </div>

          {alerts.length > 0 && (
            <div className="fi-section">
              <h2>Upcoming Maturities</h2>
              <div className="fi-alerts">
                {alerts.map(a => (
                  <div key={a.id} className="fi-alert">
                    <span className="fi-alert-name">{a.name}</span>
                    <span className="fi-alert-bank">{a.bank_name}</span>
                    <span className="fi-alert-date">{a.days_until_maturity}d</span>
                    <span className="fi-alert-value">{fmt(a.maturity_value)}</span>
                    {a.auto_renew && <span className="fi-badge">Auto-renew</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="fi-section">
            <h2>Bond Breakdown</h2>
            {bonds.length === 0 ? <p className="fi-empty">No bonds yet.</p> : (
              <div className="fi-list">
                {bonds.map(b => (
                  <div key={b.id} className="fi-item" onClick={() => { setTab('bonds'); loadBondAnalytics(b) }}>
                    <span className="fi-item-name">{b.name}</span>
                    <span className="fi-item-type">{BOND_TYPE_LABELS[b.bond_type] ?? b.bond_type}</span>
                    <span className="fi-item-value">{fmt(b.current_market_value ?? b.purchase_price)}</span>
                    <span className="fi-item-sub">YTM: {fmtPct(b.coupon_rate)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'bonds' && (
        <div className="fi-bonds">
          <div className="fi-toolbar">
            <button className="btn-primary" onClick={() => setShowBondForm(!showBondForm)}>
              + Add Bond
            </button>
          </div>

          {showBondForm && (
            <form className="fi-form" onSubmit={submitBond}>
              <h3>Add Bond</h3>
              <div className="fi-form-grid">
                <label>Name<input value={bondForm.name} onChange={e => setBondForm(f => ({ ...f, name: e.target.value }))} required /></label>
                <label>Type<select value={bondForm.bond_type} onChange={e => setBondForm(f => ({ ...f, bond_type: e.target.value }))}>
                  {Object.entries(BOND_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select></label>
                <label>Face Value<input type="number" step="0.01" value={bondForm.face_value} onChange={e => setBondForm(f => ({ ...f, face_value: +e.target.value }))} /></label>
                <label>Coupon Rate<input type="number" step="0.0001" value={bondForm.coupon_rate} onChange={e => setBondForm(f => ({ ...f, coupon_rate: +e.target.value }))} /></label>
                <label>Purchase Price<input type="number" step="0.01" value={bondForm.purchase_price} onChange={e => setBondForm(f => ({ ...f, purchase_price: +e.target.value }))} /></label>
                <label>Purchase Date<input type="date" value={bondForm.purchase_date} onChange={e => setBondForm(f => ({ ...f, purchase_date: e.target.value }))} /></label>
                <label>Maturity Date<input type="date" value={bondForm.maturity_date} onChange={e => setBondForm(f => ({ ...f, maturity_date: e.target.value }))} /></label>
                <label>Ticker<input value={bondForm.ticker ?? ''} onChange={e => setBondForm(f => ({ ...f, ticker: e.target.value }))} /></label>
                <label>Credit Rating<input value={bondForm.credit_rating ?? ''} onChange={e => setBondForm(f => ({ ...f, credit_rating: e.target.value }))} /></label>
                <label>Currency<input value={bondForm.currency} onChange={e => setBondForm(f => ({ ...f, currency: e.target.value }))} /></label>
                <label>Current Market Value<input type="number" step="0.01" value={bondForm.current_market_value ?? ''} onChange={e => setBondForm(f => ({ ...f, current_market_value: e.target.value ? +e.target.value : null }))} /></label>
              </div>
              <div className="fi-form-actions">
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                <button type="button" className="btn-secondary" onClick={() => setShowBondForm(false)}>Cancel</button>
              </div>
            </form>
          )}

          {selectedBond && analytics && (
            <div className="fi-analytics-panel">
              <div className="fi-analytics-header">
                <h3>{selectedBond.name} — Analytics</h3>
                <button onClick={() => { setSelectedBond(null); setAnalytics(null) }}>✕</button>
              </div>
              <div className="fi-analytics-grid">
                <div className="fi-analytics-item"><span>YTM</span><strong>{fmtPct(analytics.ytm)}</strong></div>
                <div className="fi-analytics-item"><span>Current Yield</span><strong>{fmtPct(analytics.current_yield)}</strong></div>
                <div className="fi-analytics-item"><span>Years to Maturity</span><strong>{analytics.years_to_maturity.toFixed(2)}y</strong></div>
                <div className="fi-analytics-item"><span>Macauley Duration</span><strong>{analytics.macauley_duration.toFixed(4)}</strong></div>
                <div className="fi-analytics-item"><span>Modified Duration</span><strong>{analytics.modified_duration.toFixed(4)}</strong></div>
                <div className="fi-analytics-item"><span>Price Δ +100bps</span><strong>{(analytics.price_change_100bps * 100).toFixed(2)}%</strong></div>
                <div className="fi-analytics-item"><span>Annual Coupon</span><strong>{fmt(analytics.annual_coupon)}</strong></div>
                <div className="fi-analytics-item">
                  <span>P&L</span>
                  <strong className={Number(selectedBond.unrealized_pnl) >= 0 ? 'positive' : 'negative'}>
                    {fmt(selectedBond.unrealized_pnl ?? 0)}
                  </strong>
                </div>
              </div>
              <button className="btn-danger" onClick={() => deleteBond(selectedBond.id)}>Delete Bond</button>
            </div>
          )}

          <div className="fi-list">
            {bonds.length === 0 ? <p className="fi-empty">No bonds yet. Click "Add Bond" to get started.</p> :
              bonds.map(b => (
                <div key={b.id} className={`fi-item ${selectedBond?.id === b.id ? 'selected' : ''}`} onClick={() => loadBondAnalytics(b)}>
                  <div className="fi-item-main">
                    <span className="fi-item-name">{b.name}</span>
                    <span className="fi-item-type">{BOND_TYPE_LABELS[b.bond_type] ?? b.bond_type}</span>
                  </div>
                  <div className="fi-item-details">
                    <span>Face: {fmt(b.face_value)}</span>
                    <span>Coupon: {fmtPct(b.coupon_rate)}</span>
                    <span>Matures: {b.maturity_date}</span>
                  </div>
                  <div className="fi-item-value">
                    {fmt(b.current_market_value ?? b.purchase_price)}
                    {b.unrealized_pnl !== null && (
                      <span className={`fi-pnl ${b.unrealized_pnl >= 0 ? 'positive' : 'negative'}`}>
                        {b.unrealized_pnl >= 0 ? '+' : ''}{fmt(b.unrealized_pnl)}
                      </span>
                    )}
                  </div>
                </div>
              ))
            }
          </div>
        </div>
      )}

      {tab === 'deposits' && (
        <div className="fi-deposits">
          <div className="fi-toolbar">
            <button className="btn-primary" onClick={() => setShowDepositForm(!showDepositForm)}>
              + Add Term Deposit
            </button>
          </div>

          {showDepositForm && (
            <form className="fi-form" onSubmit={submitDeposit}>
              <h3>Add Term Deposit</h3>
              <div className="fi-form-grid">
                <label>Name<input value={depositForm.name} onChange={e => setDepositForm(f => ({ ...f, name: e.target.value }))} required /></label>
                <label>Bank<input value={depositForm.bank_name} onChange={e => setDepositForm(f => ({ ...f, bank_name: e.target.value }))} required /></label>
                <label>Principal<input type="number" step="0.01" value={depositForm.principal} onChange={e => setDepositForm(f => ({ ...f, principal: +e.target.value }))} /></label>
                <label>Interest Rate<input type="number" step="0.0001" value={depositForm.interest_rate} onChange={e => setDepositForm(f => ({ ...f, interest_rate: +e.target.value }))} /></label>
                <label>Term (months)<input type="number" value={depositForm.term_months} onChange={e => setDepositForm(f => ({ ...f, term_months: +e.target.value }))} /></label>
                <label>Start Date<input type="date" value={depositForm.start_date} onChange={e => setDepositForm(f => ({ ...f, start_date: e.target.value }))} /></label>
                <label>Maturity Date<input type="date" value={depositForm.maturity_date} onChange={e => setDepositForm(f => ({ ...f, maturity_date: e.target.value }))} /></label>
                <label>Compound<select value={depositForm.compound_frequency} onChange={e => setDepositForm(f => ({ ...f, compound_frequency: e.target.value }))}>
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                  <option value="semi_annually">Semi-Annually</option>
                  <option value="annually">Annually</option>
                </select></label>
                <label>Auto Renew<input type="checkbox" checked={depositForm.auto_renew} onChange={e => setDepositForm(f => ({ ...f, auto_renew: e.target.checked }))} /></label>
              </div>
              <div className="fi-form-actions">
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                <button type="button" className="btn-secondary" onClick={() => setShowDepositForm(false)}>Cancel</button>
              </div>
            </form>
          )}

          <div className="fi-list">
            {deposits.length === 0 ? <p className="fi-empty">No term deposits yet.</p> :
              deposits.map(d => (
                <div key={d.id} className="fi-item">
                  <div className="fi-item-main">
                    <span className="fi-item-name">{d.name}</span>
                    <span className="fi-item-type">{d.bank_name}</span>
                  </div>
                  <div className="fi-item-details">
                    <span>Principal: {fmt(d.principal)}</span>
                    <span>Rate: {fmtPct(d.interest_rate)}</span>
                    <span>Term: {d.term_months}mo</span>
                    <span>Matures: {d.maturity_date}</span>
                  </div>
                  <div className="fi-item-value">
                    {fmt(d.maturity_value ?? d.principal)}
                    {d.accrued_interest !== null && (
                      <span className="fi-pnl positive">+{fmt(d.accrued_interest)} accrued</span>
                    )}
                  </div>
                  <button className="btn-icon" onClick={() => deleteDeposit(d.id)} title="Delete">🗑</button>
                </div>
              ))
            }
          </div>
        </div>
      )}
    </div>
  )
}
