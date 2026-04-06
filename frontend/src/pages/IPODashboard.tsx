import { useState, useEffect } from 'react'
import {
  ipoService,
  IPORecord,
  IPOCreate,
  IPOUpdate,
  IPOAlert,
  IPOAlertCreate,
  IPOStatus,
} from '../services/ipoService'
import './IPODashboard.css'

const STATUS_LABELS: Record<string, string> = {
  upcoming: 'Upcoming',
  filing: 'Filing',
  allocated: 'Allocated',
  listed: 'Listed',
  withdrawn: 'Withdrawn',
}

const STATUS_COLORS: Record<string, string> = {
  upcoming: '#f59e0b',
  filing: '#3b82f6',
  allocated: '#8b5cf6',
  listed: '#10b981',
  withdrawn: '#ef4444',
}

const fmt = (n: number | null | undefined) =>
  n == null ? '—' : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)

const fmtDate = (d: string | null | undefined) => {
  if (!d) return '—'
  try { return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) }
  catch { return d }
}

const daysUntil = (d: string | null | undefined) => {
  if (!d) return null
  const diff = new Date(d).getTime() - Date.now()
  return Math.ceil(diff / 86400000)
}

export default function IPODashboard() {
  const [tab, setTab] = useState<'overview' | 'ipos' | 'calendar' | 'alerts'>('overview')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [ipos, setIpos] = useState<IPORecord[]>([])
  const [upcoming, setUpcoming] = useState<IPORecord[]>([])
  const [alerts, setAlerts] = useState<IPOAlert[]>([])
  const [deadlines, setDeadlines] = useState<{ company_name: string; deadline: string; days_left: number }[]>([])

  const [showIpoForm, setShowIpoForm] = useState(false)
  const [editingIpo, setEditingIpo] = useState<IPORecord | null>(null)
  const [saving, setSaving] = useState(false)

  const [showAlertForm, setShowAlertForm] = useState(false)
  const [alertForm, setAlertForm] = useState<IPOAlertCreate>({ ipo_id: '', alert_type: 'deadline' })
  const [savingAlert, setSavingAlert] = useState(false)

  useEffect(() => { loadAll() }, [])

  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const [iposData, upcomingData, alertsData, deadlinesData] = await Promise.all([
        ipoService.listIPOs().catch(() => []),
        ipoService.getUpcomingIPOs().catch(() => []),
        ipoService.listAlerts().catch(() => []),
        ipoService.getUpcomingDeadlines().catch(() => []),
      ])
      setIpos(iposData)
      setUpcoming(upcomingData)
      setAlerts(alertsData)
      setDeadlines(deadlinesData)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  // ─── IPO Form ────────────────────────────────────────────────────────────────
  const emptyIpo = (): IPOCreate => ({
    company_name: '',
    ticker: null,
    exchange: null,
    sector: null,
    industry: null,
    ipo_price_min: null,
    ipo_price_max: null,
    final_ipo_price: null,
    shares_offered: null,
    lot_size: null,
    oversubscription_ratio: null,
    application_deadline: null,
    listing_date: null,
    first_trading_date: null,
    underwriter: null,
    status: 'upcoming',
    estimated_market_cap: null,
    raising_amount: null,
    notes: null,
  })

  const [ipoForm, setIpoForm] = useState<IPOCreate>(emptyIpo())

  const handleSaveIpo = async () => {
    setSaving(true)
    try {
      if (editingIpo) {
        await ipoService.updateIPO(editingIpo.id, ipoForm as IPOUpdate)
      } else {
        await ipoService.createIPO(ipoForm)
      }
      const data = await ipoService.listIPOs()
      const upcomingData = await ipoService.getUpcomingIPOs()
      setIpos(data)
      setUpcoming(upcomingData)
      setShowIpoForm(false)
      setEditingIpo(null)
      setIpoForm(emptyIpo())
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const handleEditIpo = (ipo: IPORecord) => {
    setEditingIpo(ipo)
    setIpoForm({
      company_name: ipo.company_name,
      ticker: ipo.ticker,
      exchange: ipo.exchange,
      sector: ipo.sector,
      industry: ipo.industry,
      ipo_price_min: ipo.ipo_price_min,
      ipo_price_max: ipo.ipo_price_max,
      final_ipo_price: ipo.final_ipo_price,
      shares_offered: ipo.shares_offered,
      lot_size: ipo.lot_size,
      oversubscription_ratio: ipo.oversubscription_ratio,
      application_deadline: ipo.application_deadline ? ipo.application_deadline.split('T')[0] : null,
      listing_date: ipo.listing_date ? ipo.listing_date.split('T')[0] : null,
      first_trading_date: ipo.first_trading_date ? ipo.first_trading_date.split('T')[0] : null,
      underwriter: ipo.underwriter,
      status: ipo.status as IPOStatus,
      estimated_market_cap: ipo.estimated_market_cap,
      raising_amount: ipo.raising_amount,
      notes: ipo.notes,
    })
    setShowIpoForm(true)
  }

  const handleDeleteIpo = async (id: string) => {
    if (!confirm('Delete this IPO record?')) return
    await ipoService.deleteIPO(id)
    setIpos(prev => prev.filter(i => i.id !== id))
    setUpcoming(prev => prev.filter(i => i.id !== id))
  }

  // ─── Alert Form ──────────────────────────────────────────────────────────────
  const handleSaveAlert = async () => {
    if (!alertForm.ipo_id) {
      alert('Please select an IPO first')
      return
    }
    setSavingAlert(true)
    try {
      await ipoService.createAlert(alertForm)
      const data = await ipoService.listAlerts()
      setAlerts(data)
      setShowAlertForm(false)
      setAlertForm({ ipo_id: '', alert_type: 'deadline' })
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to create alert')
    } finally {
      setSavingAlert(false)
    }
  }

  const handleDeleteAlert = async (id: string) => {
    if (!confirm('Delete this alert?')) return
    await ipoService.deleteAlert(id)
    setAlerts(prev => prev.filter(a => a.id !== id))
  }

  // ─── Computed ─────────────────────────────────────────────────────────────────
  const listedCount = ipos.filter(i => i.status === 'listed').length
  const upcomingCount = ipos.filter(i => i.status === 'upcoming' || i.status === 'filing').length
  const totalRaised = ipos.reduce((s, i) => s + (i.raising_amount || 0), 0)

  if (loading && ipos.length === 0) {
    return <div className="ipo-dashboard"><div className="loading">Loading IPO data...</div></div>
  }

  return (
    <div className="ipo-dashboard">
      <div className="dashboard-header">
        <h2>🏛️ IPO Tracker</h2>
        <div className="header-actions">
          <button onClick={loadAll} className="btn-secondary" disabled={loading}>Refresh</button>
          <button onClick={() => { setTab('ipos'); setShowIpoForm(false); setEditingIpo(null); setIpoForm(emptyIpo()) }} className="btn-primary">+ IPO</button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="tab-bar">
        <button className={tab === 'overview' ? 'active' : ''} onClick={() => setTab('overview')}>Overview</button>
        <button className={tab === 'ipos' ? 'active' : ''} onClick={() => setTab('ipos')}>IPOs ({ipos.length})</button>
        <button className={tab === 'calendar' ? 'active' : ''} onClick={() => setTab('calendar')}>Calendar</button>
        <button className={tab === 'alerts' ? 'active' : ''} onClick={() => setTab('alerts')}>Alerts ({alerts.length})</button>
      </div>

      {/* ── Overview ── */}
      {tab === 'overview' && (
        <div className="overview-grid">
          <div className="summary-card">
            <h3>IPO Summary</h3>
            <div className="stat-row"><span>Total Tracked</span><span>{ipos.length}</span></div>
            <div className="stat-row"><span>Upcoming / Filing</span><span>{upcomingCount}</span></div>
            <div className="stat-row"><span>Listed</span><span>{listedCount}</span></div>
            <div className="stat-row"><span>Total Raised</span><span>{fmt(totalRaised)}</span></div>
          </div>

          {upcoming.length > 0 && (
            <div className="summary-card">
              <h3>Upcoming IPOs</h3>
              {upcoming.slice(0, 5).map(ipo => (
                <div key={ipo.id} className="ipo-upcoming-row">
                  <div className="ipo-name">
                    <span className="status-dot" style={{ background: STATUS_COLORS[ipo.status] || '#888' }} />
                    {ipo.company_name}
                  </div>
                  <div className="ipo-meta">
                    {ipo.ticker && <span className="ticker-badge">{ipo.ticker}</span>}
                    {ipo.listing_date && <span className="countdown">{daysUntil(ipo.listing_date)}d</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {deadlines.length > 0 && (
            <div className="summary-card alert-card">
              <h3>⚠️ Upcoming Deadlines</h3>
              {deadlines.map((d, i) => (
                <div key={i} className="alert-row">
                  <span>{d.company_name}</span>
                  <span className="days-badge">{d.days_left}d left</span>
                </div>
              ))}
            </div>
          )}

          {alerts.length > 0 && (
            <div className="summary-card">
              <h3>Active Alerts</h3>
              {alerts.slice(0, 5).map(a => (
                <div key={a.id} className="alert-row">
                  <span>{a.message || `Alert for IPO`}</span>
                  <span className="alert-type-badge">{a.alert_type}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── IPOs ── */}
      {tab === 'ipos' && (
        <div>
          {showIpoForm && (
            <div className="form-card">
              <h3>{editingIpo ? 'Edit IPO' : 'New IPO'}</h3>
              <div className="form-grid">
                <label>Company Name<input value={ipoForm.company_name} onChange={e => setIpoForm(p => ({ ...p, company_name: e.target.value }))} /></label>
                <label>Ticker<input value={ipoForm.ticker || ''} onChange={e => setIpoForm(p => ({ ...p, ticker: e.target.value || null }))} placeholder="e.g. AION" /></label>
                <label>Exchange<input value={ipoForm.exchange || ''} onChange={e => setIpoForm(p => ({ ...p, exchange: e.target.value || null }))} placeholder="NYSE, NASDAQ..." /></label>
                <label>Sector<input value={ipoForm.sector || ''} onChange={e => setIpoForm(p => ({ ...p, sector: e.target.value || null }))} /></label>
                <label>Industry<input value={ipoForm.industry || ''} onChange={e => setIpoForm(p => ({ ...p, industry: e.target.value || null }))} /></label>
                <label>Status<select value={ipoForm.status} onChange={e => setIpoForm(p => ({ ...p, status: e.target.value as IPOStatus }))}>
                  {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select></label>
                <label>IPO Price Min<input type="number" min="0" value={ipoForm.ipo_price_min ?? ''} onChange={e => setIpoForm(p => ({ ...p, ipo_price_min: e.target.value ? +e.target.value : null }))} /></label>
                <label>IPO Price Max<input type="number" min="0" value={ipoForm.ipo_price_max ?? ''} onChange={e => setIpoForm(p => ({ ...p, ipo_price_max: e.target.value ? +e.target.value : null }))} /></label>
                <label>Final Price<input type="number" min="0" value={ipoForm.final_ipo_price ?? ''} onChange={e => setIpoForm(p => ({ ...p, final_ipo_price: e.target.value ? +e.target.value : null }))} /></label>
                <label>Shares Offered<input type="number" min="0" value={ipoForm.shares_offered ?? ''} onChange={e => setIpoForm(p => ({ ...p, shares_offered: e.target.value ? +e.target.value : null }))} /></label>
                <label>Lot Size<input type="number" min="0" value={ipoForm.lot_size ?? ''} onChange={e => setIpoForm(p => ({ ...p, lot_size: e.target.value ? +e.target.value : null }))} /></label>
                <label>Oversubscribe Ratio<input type="number" min="0" step="0.1" value={ipoForm.oversubscription_ratio ?? ''} onChange={e => setIpoForm(p => ({ ...p, oversubscription_ratio: e.target.value ? +e.target.value : null }))} /></label>
                <label>Application Deadline<input type="date" value={ipoForm.application_deadline || ''} onChange={e => setIpoForm(p => ({ ...p, application_deadline: e.target.value || null }))} /></label>
                <label>Listing Date<input type="date" value={ipoForm.listing_date || ''} onChange={e => setIpoForm(p => ({ ...p, listing_date: e.target.value || null }))} /></label>
                <label>First Trading Date<input type="date" value={ipoForm.first_trading_date || ''} onChange={e => setIpoForm(p => ({ ...p, first_trading_date: e.target.value || null }))} /></label>
                <label>Underwriter<input value={ipoForm.underwriter || ''} onChange={e => setIpoForm(p => ({ ...p, underwriter: e.target.value || null }))} /></label>
                <label>Est. Market Cap<input type="number" min="0" value={ipoForm.estimated_market_cap ?? ''} onChange={e => setIpoForm(p => ({ ...p, estimated_market_cap: e.target.value ? +e.target.value : null }))} /></label>
                <label>Raising Amount<input type="number" min="0" value={ipoForm.raising_amount ?? ''} onChange={e => setIpoForm(p => ({ ...p, raising_amount: e.target.value ? +e.target.value : null }))} /></label>
                <label className="full-width">Notes<textarea value={ipoForm.notes || ''} onChange={e => setIpoForm(p => ({ ...p, notes: e.target.value || null }))} /></label>
              </div>
              <div className="form-actions">
                <button onClick={handleSaveIpo} className="btn-primary" disabled={saving || !ipoForm.company_name}>{saving ? 'Saving...' : 'Save'}</button>
                <button onClick={() => { setShowIpoForm(false); setEditingIpo(null); setIpoForm(emptyIpo()) }} className="btn-secondary">Cancel</button>
              </div>
            </div>
          )}

          {ipos.length === 0 ? (
            <div className="empty-state">No IPO records yet. Add one to get started.</div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Company</th><th>Ticker</th><th>Status</th><th>Price Range</th>
                  <th>Raising</th><th>Deadline</th><th>Listing Date</th><th>Underwriter</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {ipos.map(ipo => (
                  <tr key={ipo.id}>
                    <td className="company-name-cell">{ipo.company_name}</td>
                    <td>{ipo.ticker || '—'}</td>
                    <td>
                      <span className="status-badge" style={{ background: STATUS_COLORS[ipo.status] || '#888' }}>
                        {STATUS_LABELS[ipo.status] || ipo.status}
                      </span>
                    </td>
                    <td>
                      {ipo.ipo_price_min && ipo.ipo_price_max
                        ? `${fmt(ipo.ipo_price_min)} – ${fmt(ipo.ipo_price_max)}`
                        : ipo.final_ipo_price ? fmt(ipo.final_ipo_price) : '—'}
                    </td>
                    <td>{fmt(ipo.raising_amount)}</td>
                    <td>{fmtDate(ipo.application_deadline)}</td>
                    <td>{fmtDate(ipo.listing_date)}</td>
                    <td>{ipo.underwriter || '—'}</td>
                    <td>
                      <button onClick={() => handleEditIpo(ipo)} className="btn-icon">✏️</button>
                      <button onClick={() => handleDeleteIpo(ipo.id)} className="btn-icon">🗑️</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ── Calendar ── */}
      {tab === 'calendar' && (
        <div>
          {upcoming.length === 0 ? (
            <div className="empty-state">No upcoming IPOs in your calendar.</div>
          ) : (
            <div className="calendar-grid">
              {upcoming.map(ipo => (
                <div key={ipo.id} className="calendar-card">
                  <div className="calendar-header">
                    <span className="status-badge" style={{ background: STATUS_COLORS[ipo.status] || '#888' }}>
                      {STATUS_LABELS[ipo.status] || ipo.status}
                    </span>
                    {ipo.ticker && <span className="ticker-badge">{ipo.ticker}</span>}
                  </div>
                  <h4>{ipo.company_name}</h4>
                  <div className="calendar-dates">
                    {ipo.application_deadline && (
                      <div><span className="date-label">Deadline:</span> {fmtDate(ipo.application_deadline)}</div>
                    )}
                    {ipo.listing_date && (
                      <div><span className="date-label">Listing:</span> {fmtDate(ipo.listing_date)} <span className="countdown-badge">{daysUntil(ipo.listing_date)}d</span></div>
                    )}
                    {ipo.first_trading_date && (
                      <div><span className="date-label">First Trade:</span> {fmtDate(ipo.first_trading_date)}</div>
                    )}
                  </div>
                  <div className="calendar-pricing">
                    {ipo.ipo_price_min && ipo.ipo_price_max && (
                      <div>{fmt(ipo.ipo_price_min)} – {fmt(ipo.ipo_price_max)}</div>
                    )}
                    {ipo.raising_amount && (
                      <div className="raising">Raising: {fmt(ipo.raising_amount)}</div>
                    )}
                  </div>
                  {ipo.underwriter && <div className="underwriter">🏦 {ipo.underwriter}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Alerts ── */}
      {tab === 'alerts' && (
        <div>
          <div className="section-actions">
            <button onClick={() => { setShowAlertForm(true); setAlertForm({ ipo_id: '', alert_type: 'deadline' }) }} className="btn-primary">+ Create Alert</button>
          </div>

          {showAlertForm && (
            <div className="form-card">
              <h3>New IPO Alert</h3>
              <div className="form-grid">
                <label>IPO<select value={alertForm.ipo_id} onChange={e => setAlertForm(f => ({ ...f, ipo_id: e.target.value }))}>
                  <option value="">Select IPO...</option>
                  {ipos.map(ipo => <option key={ipo.id} value={ipo.id}>{ipo.company_name} {ipo.ticker ? `(${ipo.ticker})` : ''}</option>)}
                </select></label>
                <label>Type<select value={alertForm.alert_type} onChange={e => setAlertForm(f => ({ ...f, alert_type: e.target.value as 'deadline' | 'allocation' | 'performance' }))}>
                  <option value="deadline">Deadline</option>
                  <option value="allocation">Allocation</option>
                  <option value="performance">Performance</option>
                </select></label>
                <label>Message<input value={alertForm.message || ''} onChange={e => setAlertForm(f => ({ ...f, message: e.target.value || null }))} placeholder="Optional custom message..." /></label>
              </div>
              <div className="form-actions">
                <button onClick={handleSaveAlert} className="btn-primary" disabled={savingAlert}>{savingAlert ? 'Saving...' : 'Save'}</button>
                <button onClick={() => setShowAlertForm(false)} className="btn-secondary">Cancel</button>
              </div>
            </div>
          )}

          {alerts.length === 0 ? (
            <div className="empty-state">No alerts configured. Create one to track IPO events.</div>
          ) : (
            <table className="data-table">
              <thead><tr><th>IPO</th><th>Type</th><th>Message</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead>
              <tbody>
                {alerts.map(a => {
                  const relatedIpo = ipos.find(i => i.id === a.ipo_id)
                  return (
                    <tr key={a.id}>
                      <td>{relatedIpo?.company_name || a.ipo_id}</td>
                      <td><span className="alert-type-badge">{a.alert_type}</span></td>
                      <td>{a.message || '—'}</td>
                      <td>{a.is_active ? <span className="active-badge">Active</span> : <span className="inactive-badge">Inactive</span>}</td>
                      <td>{fmtDate(a.created_at)}</td>
                      <td><button onClick={() => handleDeleteAlert(a.id)} className="btn-icon">🗑️</button></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}
