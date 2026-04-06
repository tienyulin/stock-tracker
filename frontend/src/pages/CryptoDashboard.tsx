import { useState, useEffect } from 'react'
import { cryptoService, CryptoWallet, DefiPosition, CryptoSummary } from '../services/cryptoService'
import './CryptoDashboard.css'

const BLOCKCHAIN_LABELS: Record<string, string> = {
  ethereum: 'Ethereum',
  bsc: 'BNB Chain',
  polygon: 'Polygon',
  solana: 'Solana',
}

const POSITION_TYPE_LABELS: Record<string, string> = {
  lp: 'Liquidity Pool',
  staking: 'Staking',
  lending: 'Lending',
}

function CryptoDashboardPage() {
  const [summary, setSummary] = useState<CryptoSummary | null>(null)
  const [wallets, setWallets] = useState<CryptoWallet[]>([])
  const [defiPositions, setDefiPositions] = useState<DefiPosition[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'wallets' | 'defi'>('overview')

  // Add wallet modal
  const [showAddWallet, setShowAddWallet] = useState(false)
  const [newWalletName, setNewWalletName] = useState('')
  const [newBlockchain, setNewBlockchain] = useState<string>('ethereum')
  const [newAddress, setNewAddress] = useState('')
  const [newBalance, setNewBalance] = useState('')
  const [addingWallet, setAddingWallet] = useState(false)

  // Add DeFi position modal
  const [showAddDefi, setShowAddDefi] = useState(false)
  const [newProtocol, setNewProtocol] = useState('')
  const [newPosType, setNewPosType] = useState<string>('staking')
  const [newToken, setNewToken] = useState('')
  const [newQty, setNewQty] = useState('')
  const [newEntry, setNewEntry] = useState('')
  const [newApy, setNewApy] = useState('')
  const [addingDefi, setAddingDefi] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [sum, w, d] = await Promise.all([
        cryptoService.getSummary(),
        cryptoService.getWallets(),
        cryptoService.getDefiPositions(),
      ])
      setSummary(sum)
      setWallets(w)
      setDefiPositions(d)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleAddWallet = async () => {
    if (!newWalletName || !newAddress) return
    try {
      setAddingWallet(true)
      await cryptoService.createWallet({
        name: newWalletName,
        blockchain: newBlockchain,
        address: newAddress,
        balance: parseFloat(newBalance) || 0,
      })
      setShowAddWallet(false)
      setNewWalletName('')
      setNewAddress('')
      setNewBalance('')
      await loadData()
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to add wallet')
    } finally {
      setAddingWallet(false)
    }
  }

  const handleDeleteWallet = async (id: string) => {
    if (!confirm('Delete this wallet?')) return
    try {
      await cryptoService.deleteWallet(id)
      await loadData()
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to delete wallet')
    }
  }

  const handleAddDefi = async () => {
    if (!newProtocol || !newToken || !newQty || !newEntry) return
    try {
      setAddingDefi(true)
      await cryptoService.createDefiPosition({
        protocol_name: newProtocol,
        position_type: newPosType,
        token_symbol: newToken,
        quantity: parseFloat(newQty),
        entry_price: parseFloat(newEntry),
        apy: parseFloat(newApy) || undefined,
      })
      setShowAddDefi(false)
      setNewProtocol('')
      setNewToken('')
      setNewQty('')
      setNewEntry('')
      setNewApy('')
      await loadData()
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to add DeFi position')
    } finally {
      setAddingDefi(false)
    }
  }

  const handleDeleteDefi = async (id: string) => {
    if (!confirm('Delete this DeFi position?')) return
    try {
      await cryptoService.deleteDefiPosition(id)
      await loadData()
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Failed to delete position')
    }
  }

  const totalPnL = defiPositions.reduce((sum, p) => sum + (p.pnl || 0), 0)

  if (loading) return <div className="crypto-loading">Loading crypto portfolio...</div>
  if (error) return <div className="crypto-error">Error: {error}</div>

  return (
    <div className="crypto-dashboard">
      <div className="crypto-header">
        <h1>🦿 Crypto & DeFi Portfolio</h1>
        <div className="crypto-total">
          <span className="crypto-total-label">Total Value</span>
          <span className="crypto-total-value">
            ${summary?.total_crypto_value.toLocaleString('en-US', { minimumFractionDigits: 2 }) ?? '0.00'}
          </span>
        </div>
      </div>

      <div className="crypto-tabs">
        {(['overview', 'wallets', 'defi'] as const).map((tab) => (
          <button
            key={tab}
            className={`crypto-tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'overview' ? 'Overview' : tab === 'wallets' ? 'Wallets' : 'DeFi Positions'}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="crypto-overview">
          <div className="crypto-stat-cards">
            <div className="crypto-stat-card">
              <div className="stat-label">Total Value</div>
              <div className="stat-value">
                ${summary?.total_crypto_value.toLocaleString('en-US', { minimumFractionDigits: 2 }) ?? '0.00'}
              </div>
            </div>
            <div className="crypto-stat-card">
              <div className="stat-label">Wallets</div>
              <div className="stat-value">{summary?.wallet_count ?? 0}</div>
            </div>
            <div className="crypto-stat-card">
              <div className="stat-label">DeFi Positions</div>
              <div className="stat-value">{summary?.defi_position_count ?? 0}</div>
            </div>
            <div className="crypto-stat-card">
              <div className="stat-label">Unrealized P&L</div>
              <div className={`stat-value ${totalPnL >= 0 ? 'positive' : 'negative'}`}>
                {totalPnL >= 0 ? '+' : ''}{totalPnL.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'wallets' && (
        <div className="crypto-wallets">
          <div className="section-actions">
            <button className="btn-primary" onClick={() => setShowAddWallet(true)}>
              + Add Wallet
            </button>
          </div>
          {wallets.length === 0 ? (
            <div className="empty-state">No wallets added yet.</div>
          ) : (
            <table className="crypto-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Blockchain</th>
                  <th>Address</th>
                  <th>Balance</th>
                  <th>USD Value</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {wallets.map((w) => (
                  <tr key={w.id}>
                    <td>{w.name}</td>
                    <td>{BLOCKCHAIN_LABELS[w.blockchain] ?? w.blockchain}</td>
                    <td className="mono">{w.address.slice(0, 10)}...</td>
                    <td>{w.balance.toLocaleString('en-US', { maximumFractionDigits: 6 })}</td>
                    <td>${w.usd_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td>
                      <button className="btn-danger-sm" onClick={() => handleDeleteWallet(w.id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'defi' && (
        <div className="crypto-defi">
          <div className="section-actions">
            <button className="btn-primary" onClick={() => setShowAddDefi(true)}>
              + Add DeFi Position
            </button>
          </div>
          {defiPositions.length === 0 ? (
            <div className="empty-state">No DeFi positions yet.</div>
          ) : (
            <table className="crypto-table">
              <thead>
                <tr>
                  <th>Protocol</th>
                  <th>Type</th>
                  <th>Token</th>
                  <th>Qty</th>
                  <th>Entry</th>
                  <th>Current</th>
                  <th>Value</th>
                  <th>P&L</th>
                  <th>APY</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {defiPositions.map((p) => (
                  <tr key={p.id}>
                    <td>{p.protocol_name}</td>
                    <td>{POSITION_TYPE_LABELS[p.position_type] ?? p.position_type}</td>
                    <td>{p.token_symbol}</td>
                    <td>{p.quantity.toLocaleString('en-US', { maximumFractionDigits: 4 })}</td>
                    <td>${p.entry_price.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td>${p.current_price.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td>${p.current_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td className={p.pnl >= 0 ? 'positive' : 'negative'}>
                      {p.pnl >= 0 ? '+' : ''}{p.pnl.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      <br />
                      <span className="small">
                        {p.pnl_percentage >= 0 ? '+' : ''}{p.pnl_percentage.toFixed(2)}%
                      </span>
                    </td>
                    <td>{p.apy ? `${p.apy.toFixed(1)}%` : '-'}</td>
                    <td>
                      <button className="btn-danger-sm" onClick={() => handleDeleteDefi(p.id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Add Wallet Modal */}
      {showAddWallet && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Add Crypto Wallet</h2>
            <div className="form-group">
              <label>Wallet Name</label>
              <input value={newWalletName} onChange={(e) => setNewWalletName(e.target.value)} placeholder="My ETH Wallet" />
            </div>
            <div className="form-group">
              <label>Blockchain</label>
              <select value={newBlockchain} onChange={(e) => setNewBlockchain(e.target.value)}>
                <option value="ethereum">Ethereum</option>
                <option value="bsc">BNB Chain</option>
                <option value="polygon">Polygon</option>
                <option value="solana">Solana</option>
              </select>
            </div>
            <div className="form-group">
              <label>Address</label>
              <input value={newAddress} onChange={(e) => setNewAddress(e.target.value)} placeholder="0x..." />
            </div>
            <div className="form-group">
              <label>Balance (optional)</label>
              <input type="number" value={newBalance} onChange={(e) => setNewBalance(e.target.value)} placeholder="0.0" />
            </div>
            <div className="modal-actions">
              <button onClick={() => setShowAddWallet(false)}>Cancel</button>
              <button className="btn-primary" onClick={handleAddWallet} disabled={addingWallet}>
                {addingWallet ? 'Adding...' : 'Add Wallet'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add DeFi Position Modal */}
      {showAddDefi && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Add DeFi Position</h2>
            <div className="form-group">
              <label>Protocol</label>
              <input value={newProtocol} onChange={(e) => setNewProtocol(e.target.value)} placeholder="Uniswap, Aave, etc." />
            </div>
            <div className="form-group">
              <label>Position Type</label>
              <select value={newPosType} onChange={(e) => setNewPosType(e.target.value)}>
                <option value="staking">Staking</option>
                <option value="lp">Liquidity Pool</option>
                <option value="lending">Lending</option>
              </select>
            </div>
            <div className="form-group">
              <label>Token Symbol</label>
              <input value={newToken} onChange={(e) => setNewToken(e.target.value)} placeholder="ETH, USDC, etc." />
            </div>
            <div className="form-group">
              <label>Quantity</label>
              <input type="number" value={newQty} onChange={(e) => setNewQty(e.target.value)} placeholder="0.0" />
            </div>
            <div className="form-group">
              <label>Entry Price (USD)</label>
              <input type="number" value={newEntry} onChange={(e) => setNewEntry(e.target.value)} placeholder="0.00" />
            </div>
            <div className="form-group">
              <label>APY % (optional)</label>
              <input type="number" value={newApy} onChange={(e) => setNewApy(e.target.value)} placeholder="5.0" />
            </div>
            <div className="modal-actions">
              <button onClick={() => setShowAddDefi(false)}>Cancel</button>
              <button className="btn-primary" onClick={handleAddDefi} disabled={addingDefi}>
                {addingDefi ? 'Adding...' : 'Add Position'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CryptoDashboardPage
