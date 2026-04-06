import { useState, useEffect } from 'react'
import {
  commodityService,
  futuresService,
  preciousMetalsService,
  CommodityPosition,
  FuturesContract,
  ExpirationAlert,
  PreciousMetalsPrices,
  InflationHedgeMetrics,
} from '../services/commodityService'
import './CommodityDashboard.css'

const COMMODITY_TYPE_LABELS: Record<string, string> = {
  gold: 'Gold',
  silver: 'Silver',
  platinum: 'Platinum',
  oil: 'Crude Oil',
  natural_gas: 'Natural Gas',
  agricultural: 'Agricultural',
  other: 'Other',
}

const METAL_ICONS: Record<string, string> = {
  gold: '🥇',
  silver: '🥈',
  platinum: '🪙',
  oil: '🛢️',
  natural_gas: '🔥',
  agricultural: '🌾',
}

const fmt = (n: number | null | undefined) =>
  n == null ? '—' : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)

const fmtPct = (n: number | null | undefined) =>
  n == null ? '—' : `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`

export default function CommodityDashboard() {
  const [tab, setTab] = useState<'overview' | 'positions' | 'futures'>('overview')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Data state
  const [positions, setPositions] = useState<CommodityPosition[]>([])
  const [contracts, setContracts] = useState<FuturesContract[]>([])
  const [alerts, setAlerts] = useState<ExpirationAlert[]>([])
  const [metalPrices, setMetalPrices] = useState<PreciousMetalsPrices | null>(null)
  const [metrics, setMetrics] = useState<InflationHedgeMetrics | null>(null)

  // Position form state
  const [showPositionForm, setShowPositionForm] = useState(false)
  const [editingPosition, setEditingPosition] = useState<CommodityPosition | null>(null)
  const [saving, setSaving] = useState(false)

  // Futures form state
  const [showFuturesForm, setShowFuturesForm] = useState(false)
  const [editingContract, setEditingContract] = useState<FuturesContract | null>(null)

  useEffect(() => { loadAll() }, [])

  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const [pos, con, exp, prices, met] = await Promise.all([
        commodityService.listPositions().catch(() => []),
        futuresService.listContracts().catch(() => []),
        futuresService.getExpirationAlerts().catch(() => []),
        preciousMetalsService.getPrices().catch(() => null),
        preciousMetalsService.getInflationHedgeMetrics().catch(() => null),
      ])
      setPositions(pos)
      setContracts(con)
      setAlerts(exp)
      setMetalPrices(prices)
      setMetrics(met)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  // ─── Position Form Helpers ────────────────────────────────────────────────────
  const emptyPosition = () => ({
    name: '',
    commodity_type: 'gold',
    ticker: null as string | null,
    quantity: 1,
    unit: 'shares',
    purchase_price: 0,
    current_price: null as number | null,
    purchase_date: new Date().toISOString().split('T')[0],
    currency: 'USD',
    notes: null as string | null,
  })

  const [positionForm, setPositionForm] = useState<ReturnType<typeof emptyPosition>>(emptyPosition())

  const handleSavePosition = async () => {
    setSaving(true)
    try {
      if (editingPosition) {
        await commodityService.updatePosition(editingPosition.id, positionForm)
      } else {
        await commodityService.createPosition(positionForm)
      }
      const pos = await commodityService.listPositions()
      setPositions(pos)
      setShowPositionForm(false)
      setEditingPosition(null)
      setPositionForm(emptyPosition())
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const handleEditPosition = (p: CommodityPosition) => {
    setEditingPosition(p)
    setPositionForm({
      name: p.name,
      commodity_type: p.commodity_type,
      ticker: p.ticker,
      quantity: p.quantity,
      unit: p.unit,
      purchase_price: p.purchase_price,
      current_price: p.current_price,
      purchase_date: p.purchase_date.split('T')[0],
      currency: p.currency,
      notes: p.notes,
    })
    setShowPositionForm(true)
  }

  const handleDeletePosition = async (id: string) => {
    if (!confirm('Delete this position?')) return
    await commodityService.deletePosition(id)
    setPositions(prev => prev.filter(p => p.id !== id))
  }

  const handleSyncPrices = async () => {
    setLoading(true)
    try {
      const result = await commodityService.syncPrices()
      if (result.updated.length > 0) {
        const pos = await commodityService.listPositions()
        setPositions(pos)
      }
    } catch {
      // silent fail
    } finally {
      setLoading(false)
    }
  }

  // ─── Futures Form Helpers ────────────────────────────────────────────────────
  const emptyContract = () => ({
    name: '',
    commodity_type: 'gold',
    ticker: null as string | null,
    contract_size: 100,
    contract_month: new Date().toISOString().slice(0, 7),
    expiration_date: new Date(Date.now() + 90 * 86400 * 1000).toISOString().split('T')[0],
    entry_price: 0,
    position_type: 'long',
    notes: null as string | null,
  })

  const [contractForm, setContractForm] = useState<ReturnType<typeof emptyContract>>(emptyContract())

  const handleSaveContract = async () => {
    setSaving(true)
    try {
      if (editingContract) {
        await futuresService.updateContract(editingContract.id, contractForm)
      } else {
        await futuresService.createContract(contractForm)
      }
      const con = await futuresService.listContracts()
      setContracts(con)
      setShowFuturesForm(false)
      setEditingContract(null)
      setContractForm(emptyContract())
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const handleEditContract = (c: FuturesContract) => {
    setEditingContract(c)
    setContractForm({
      name: c.name,
      commodity_type: c.commodity_type,
      ticker: c.ticker,
      contract_size: c.contract_size,
      contract_month: c.contract_month,
      expiration_date: c.expiration_date.split('T')[0],
      entry_price: c.entry_price,
      position_type: c.position_type,
      notes: c.notes,
    })
    setShowFuturesForm(true)
  }

  const handleDeleteContract = async (id: string) => {
    if (!confirm('Delete this contract?')) return
    await futuresService.deleteContract(id)
    setContracts(prev => prev.filter(c => c.id !== id))
  }

  // ─── Computed ─────────────────────────────────────────────────────────────────
  const totalPositionValue = positions.reduce((s, p) => s + (p.market_value || 0), 0)
  const totalPositionPnl = positions.reduce((s, p) => s + (p.unrealized_pnl || 0), 0)
  const totalFuturesValue = contracts.reduce((s, c) => s + (c.market_value || 0), 0)
  const totalFuturesPnl = contracts.reduce((s, c) => s + (c.unrealized_pnl || 0), 0)

  if (loading && positions.length === 0 && contracts.length === 0) {
    return <div className="commodity-dashboard"><div className="loading">Loading commodities...</div></div>
  }

  return (
    <div className="commodity-dashboard">
      <div className="dashboard-header">
        <h2>🦍 Commodities & Precious Metals</h2>
        <div className="header-actions">
          <button onClick={handleSyncPrices} className="btn-secondary" disabled={loading}>Sync Prices</button>
          <button onClick={() => { setTab('positions'); setShowPositionForm(false); setEditingPosition(null); setPositionForm(emptyPosition()) }} className="btn-primary">+ Position</button>
          <button onClick={() => { setTab('futures'); setShowFuturesForm(false); setEditingContract(null); setContractForm(emptyContract()) }} className="btn-primary">+ Futures</button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="tab-bar">
        <button className={tab === 'overview' ? 'active' : ''} onClick={() => setTab('overview')}>Overview</button>
        <button className={tab === 'positions' ? 'active' : ''} onClick={() => setTab('positions')}>
          Positions ({positions.length})
        </button>
        <button className={tab === 'futures' ? 'active' : ''} onClick={() => setTab('futures')}>
          Futures ({contracts.length})
        </button>
      </div>

      {/* ── Overview ── */}
      {tab === 'overview' && (
        <div className="overview-grid">
          <div className="summary-card">
            <h3>Position Summary</h3>
            <div className="stat-row"><span>Total Value</span><span>{fmt(totalPositionValue)}</span></div>
            <div className="stat-row"><span>Unrealized P&L</span><span className={totalPositionPnl >= 0 ? 'positive' : 'negative'}>{fmt(totalPositionPnl)}</span></div>
            <div className="stat-row"><span>Holdings</span><span>{positions.length}</span></div>
          </div>

          <div className="summary-card">
            <h3>Futures Summary</h3>
            <div className="stat-row"><span>Total Value</span><span>{fmt(totalFuturesValue)}</span></div>
            <div className="stat-row"><span>Unrealized P&L</span><span className={totalFuturesPnl >= 0 ? 'positive' : 'negative'}>{fmt(totalFuturesPnl)}</span></div>
            <div className="stat-row"><span>Contracts</span><span>{contracts.length}</span></div>
          </div>

          <div className="summary-card">
            <h3>Precious Metals Prices</h3>
            {metalPrices ? (
              <>
                <div className="metal-row"><span>🥇 Gold (GC=F)</span><span>{fmt(metalPrices.gold)}/oz</span></div>
                <div className="metal-row"><span>🥈 Silver (SI=F)</span><span>{fmt(metalPrices.silver)}/oz</span></div>
                <div className="metal-row"><span>🪙 Platinum (PL=F)</span><span>{fmt(metalPrices.platinum)}/oz</span></div>
              </>
            ) : <div className="empty">No price data</div>}
          </div>

          {metrics && (
            <div className="summary-card">
              <h3>Inflation Hedge Metrics</h3>
              <div className="stat-row"><span>Gold 1M Change</span><span>{fmtPct(metrics.gold_change_1m_pct)}</span></div>
              <div className="stat-row"><span>Gold 1Y Change</span><span>{fmtPct(metrics.gold_change_1y_pct)}</span></div>
              <div className="stat-row"><span>DXY Index</span><span>{fmt(metrics.dxy_index)}</span></div>
              <div className="stat-row"><span>Signal</span><span className="badge">{metrics.inflation_hedge_signal}</span></div>
            </div>
          )}

          {alerts.length > 0 && (
            <div className="summary-card alert-card">
              <h3>⚠️ Expiration Alerts</h3>
              {alerts.map(a => (
                <div key={a.id} className="alert-row">
                  <span>{METAL_ICONS[a.commodity_type] || '📦'} {a.name}</span>
                  <span>Expires in {a.days_until_expiration}d</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Positions ── */}
      {tab === 'positions' && (
        <div>
          {showPositionForm && (
            <div className="form-card">
              <h3>{editingPosition ? 'Edit Position' : 'New Position'}</h3>
              <div className="form-grid">
                <label>Name<input value={positionForm.name} onChange={e => setPositionForm(p => ({ ...p, name: e.target.value }))} /></label>
                <label>Type<select value={positionForm.commodity_type} onChange={e => setPositionForm(p => ({ ...p, commodity_type: e.target.value }))}>
                  {Object.entries(COMMODITY_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select></label>
                <label>Ticker<input value={positionForm.ticker || ''} onChange={e => setPositionForm(p => ({ ...p, ticker: e.target.value || null }))} placeholder="GLD, SLV..." /></label>
                <label>Quantity<input type="number" min="0" value={positionForm.quantity} onChange={e => setPositionForm(p => ({ ...p, quantity: +e.target.value }))} /></label>
                <label>Unit<select value={positionForm.unit} onChange={e => setPositionForm(p => ({ ...p, unit: e.target.value }))}>
                  <option value="shares">Shares</option><option value="oz">Troy Ounce</option><option value="g">Grams</option><option value="barrel">Barrel</option><option value="bushel">Bushel</option>
                </select></label>
                <label>Purchase Price<input type="number" min="0" value={positionForm.purchase_price} onChange={e => setPositionForm(p => ({ ...p, purchase_price: +e.target.value }))} /></label>
                <label>Current Price<input type="number" min="0" value={positionForm.current_price || ''} onChange={e => setPositionForm(p => ({ ...p, current_price: e.target.value ? +e.target.value : null }))} /></label>
                <label>Purchase Date<input type="date" value={positionForm.purchase_date} onChange={e => setPositionForm(p => ({ ...p, purchase_date: e.target.value }))} /></label>
                <label>Notes<textarea value={positionForm.notes || ''} onChange={e => setPositionForm(p => ({ ...p, notes: e.target.value || null }))} /></label>
              </div>
              <div className="form-actions">
                <button onClick={handleSavePosition} className="btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                <button onClick={() => { setShowPositionForm(false); setEditingPosition(null); setPositionForm(emptyPosition()) }} className="btn-secondary">Cancel</button>
              </div>
            </div>
          )}

          {positions.length === 0 ? (
            <div className="empty-state">No commodity positions yet. Add one to get started.</div>
          ) : (
            <table className="data-table">
              <thead><tr><th>Name</th><th>Type</th><th>Ticker</th><th>Qty</th><th>Avg Cost</th><th>Current</th><th>Market Value</th><th>P&L</th><th>Actions</th></tr></thead>
              <tbody>
                {positions.map(p => (
                  <tr key={p.id}>
                    <td>{METAL_ICONS[p.commodity_type] || '📦'} {p.name}</td>
                    <td>{COMMODITY_TYPE_LABELS[p.commodity_type] || p.commodity_type}</td>
                    <td>{p.ticker || '—'}</td>
                    <td>{p.quantity} {p.unit}</td>
                    <td>{fmt(p.purchase_price)}</td>
                    <td>{fmt(p.current_price)}</td>
                    <td>{fmt(p.market_value)}</td>
                    <td className={((p.unrealized_pnl || 0) >= 0) ? 'positive' : 'negative'}>{fmt(p.unrealized_pnl)}</td>
                    <td>
                      <button onClick={() => handleEditPosition(p)} className="btn-icon">✏️</button>
                      <button onClick={() => handleDeletePosition(p.id)} className="btn-icon">🗑️</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ── Futures ── */}
      {tab === 'futures' && (
        <div>
          {showFuturesForm && (
            <div className="form-card">
              <h3>{editingContract ? 'Edit Contract' : 'New Futures Contract'}</h3>
              <div className="form-grid">
                <label>Name<input value={contractForm.name} onChange={e => setContractForm(c => ({ ...c, name: e.target.value }))} /></label>
                <label>Type<select value={contractForm.commodity_type} onChange={e => setContractForm(c => ({ ...c, commodity_type: e.target.value }))}>
                  {Object.entries(COMMODITY_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select></label>
                <label>Ticker<input value={contractForm.ticker || ''} onChange={e => setContractForm(c => ({ ...c, ticker: e.target.value || null }))} /></label>
                <label>Contract Size<input type="number" min="0" value={contractForm.contract_size} onChange={e => setContractForm(c => ({ ...c, contract_size: +e.target.value }))} /></label>
                <label>Contract Month<input type="month" value={contractForm.contract_month} onChange={e => setContractForm(c => ({ ...c, contract_month: e.target.value }))} /></label>
                <label>Expiration Date<input type="date" value={contractForm.expiration_date} onChange={e => setContractForm(c => ({ ...c, expiration_date: e.target.value }))} /></label>
                <label>Entry Price<input type="number" min="0" value={contractForm.entry_price} onChange={e => setContractForm(c => ({ ...c, entry_price: +e.target.value }))} /></label>
                <label>Position<select value={contractForm.position_type} onChange={e => setContractForm(c => ({ ...c, position_type: e.target.value }))}>
                  <option value="long">Long</option><option value="short">Short</option>
                </select></label>
                <label>Notes<textarea value={contractForm.notes || ''} onChange={e => setContractForm(c => ({ ...c, notes: e.target.value || null }))} /></label>
              </div>
              <div className="form-actions">
                <button onClick={handleSaveContract} className="btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                <button onClick={() => { setShowFuturesForm(false); setEditingContract(null); setContractForm(emptyContract()) }} className="btn-secondary">Cancel</button>
              </div>
            </div>
          )}

          {contracts.length === 0 ? (
            <div className="empty-state">No futures contracts yet.</div>
          ) : (
            <table className="data-table">
              <thead><tr><th>Name</th><th>Type</th><th>Month</th><th>Expiry</th><th>Position</th><th>Entry</th><th>Current</th><th>Market Value</th><th>P&L</th><th>Margin</th><th>Actions</th></tr></thead>
              <tbody>
                {contracts.map(c => (
                  <tr key={c.id}>
                    <td>{METAL_ICONS[c.commodity_type] || '📦'} {c.name}</td>
                    <td>{COMMODITY_TYPE_LABELS[c.commodity_type] || c.commodity_type}</td>
                    <td>{c.contract_month}</td>
                    <td>{c.expiration_date}</td>
                    <td className={c.position_type === 'long' ? 'positive' : 'negative'}>{c.position_type.toUpperCase()}</td>
                    <td>{fmt(c.entry_price)}</td>
                    <td>{fmt(c.current_price)}</td>
                    <td>{fmt(c.market_value)}</td>
                    <td className={((c.unrealized_pnl || 0) >= 0) ? 'positive' : 'negative'}>{fmt(c.unrealized_pnl)}</td>
                    <td>{fmt(c.margin_required)}</td>
                    <td>
                      <button onClick={() => handleEditContract(c)} className="btn-icon">✏️</button>
                      <button onClick={() => handleDeleteContract(c.id)} className="btn-icon">🗑️</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}
