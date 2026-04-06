import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { agentService, getErrorMessage } from '../../services/api'
import type { OpenFinanceConnection } from '../../types/agent'
import './OpenFinanceConnect.css'

const BANKS = [
  { code: 'ESUN', name: '玉山銀行 (E.Sun Bank)', pilot: true },
  { code: 'FUBON', name: '富邦銀行 (Fubon Bank)', pilot: false },
  { code: 'CTBC', name: '中信銀行 (CTBC Bank)', pilot: false },
]

function OpenFinanceConnect() {
  const { t } = useTranslation()
  const [connections, setConnections] = useState<OpenFinanceConnection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notification, setNotification] = useState<string | null>(null)
  const [syncingId, setSyncingId] = useState<string | null>(null)
  const [connectingBank, setConnectingBank] = useState<string | null>(null)

  useEffect(() => {
    loadConnections()
  }, [])

  const loadConnections = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await agentService.getOpenFinanceConnections()
      setConnections(data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const showNotification = (message: string) => {
    setNotification(message)
    setTimeout(() => setNotification(null), 3000)
  }

  const handleConnect = async (bankCode: string) => {
    try {
      setConnectingBank(bankCode)
      const result = await agentService.connectOpenFinanceBank(bankCode)
      // If backend returns auth_url, open in new tab (OAuth flow)
      if (result.auth_url) {
        window.open(result.auth_url, '_blank')
      }
      // Reload connections after OAuth redirect
      setTimeout(loadConnections, 2000)
    } catch (err) {
      showNotification(getErrorMessage(err))
    } finally {
      setConnectingBank(null)
    }
  }

  const handleDisconnect = async (connectionId: string) => {
    try {
      await agentService.disconnectOpenFinanceBank(connectionId)
      setConnections(connections.filter(c => c.id !== connectionId))
      showNotification('Bank account disconnected')
    } catch (err) {
      showNotification(getErrorMessage(err))
    }
  }

  const handleSync = async (connectionId: string) => {
    try {
      setSyncingId(connectionId)
      await agentService.syncOpenFinanceAccount(connectionId)
      showNotification('Account synced successfully')
      loadConnections()
    } catch (err) {
      showNotification(getErrorMessage(err))
    } finally {
      setSyncingId(null)
    }
  }

  const getStatusClass = (status: OpenFinanceConnection['status']) => {
    switch (status) {
      case 'CONNECTED': return 'status-connected'
      case 'PENDING': return 'status-pending'
      case 'ERROR': return 'status-error'
      default: return 'status-disconnected'
    }
  }

  const connectedBanks = connections.filter(c => c.status === 'CONNECTED' || c.status === 'PENDING')
  const pilotBanks = BANKS.filter(b => b.pilot)

  if (loading) {
    return <div className="open-finance-loading">Loading connections...</div>
  }

  return (
    <div className="open-finance-connect">
      <div className="ofc-header">
        <h3>{t('agent.openFinance.title', 'Open Finance Connect')}</h3>
        <button className="btn-refresh" onClick={loadConnections}>↻ {t('common.refresh', 'Refresh')}</button>
      </div>

      {notification && <div className="notification">{notification}</div>}
      {error && <div className="error">{error}</div>}

      <div className="pilot-banks-section">
        <div className="section-label">
          {t('agent.openFinance.pilotBanks', 'Pilot Banks')}
        </div>
        <div className="pilot-banks-list">
          {pilotBanks.map(bank => {
            const connected = connections.find(c => c.bank_code === bank.code)
            return (
              <div key={bank.code} className="bank-card">
                <div className="bank-info">
                  <div className="bank-name">{bank.name}</div>
                  {bank.pilot && <span className="pilot-badge">Pilot</span>}
                  {connected && (
                    <span className={`connection-status ${getStatusClass(connected.status)}`}>
                      {connected.status}
                    </span>
                  )}
                </div>
                <div className="bank-actions">
                  {connected ? (
                    <>
                      <button
                        className="btn-sync"
                        onClick={() => handleSync(connected.id)}
                        disabled={syncingId === connected.id || connected.status === 'PENDING'}
                      >
                        {syncingId === connected.id ? '...' : t('agent.openFinance.syncNow', 'Sync Now')}
                      </button>
                      <button
                        className="btn-disconnect"
                        onClick={() => handleDisconnect(connected.id)}
                      >
                        {t('agent.openFinance.disconnect', 'Disconnect')}
                      </button>
                    </>
                  ) : (
                    <button
                      className="btn-connect"
                      onClick={() => handleConnect(bank.code)}
                      disabled={connectingBank === bank.code}
                    >
                      {connectingBank === bank.code ? '...' : t('agent.openFinance.connect', 'Connect')}
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {connectedBanks.length > 0 && (
        <div className="connected-accounts-section">
          <div className="section-label">{t('agent.openFinance.connectedAccounts', 'Connected Accounts')}</div>
          <div className="accounts-list">
            {connectedBanks.map(conn => {
              const bank = BANKS.find(b => b.code === conn.bank_code)
              return (
                <div key={conn.id} className="account-card">
                  <div className="account-bank">{bank?.name || conn.bank_code}</div>
                  <div className="account-last-sync">
                    {conn.last_sync_at
                      ? t('agent.openFinance.lastSync', 'Last sync') + ': ' + new Date(conn.last_sync_at).toLocaleString()
                      : t('agent.openFinance.notSynced', 'Not synced yet')}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export default OpenFinanceConnect
