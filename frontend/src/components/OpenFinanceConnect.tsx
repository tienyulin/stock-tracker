import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { agentService, type OpenFinanceConnection } from '../services/agentApi'
import './OpenFinanceConnect.css'

interface OpenFinanceConnectProps {
  onConnectionChange?: (connections: OpenFinanceConnection[]) => void
}

interface Bank {
  code: string
  name: string
  logo?: string
  available: boolean
  description?: string
}

const PILOT_BANKS: Bank[] = [
  {
    code: 'ESUN',
    name: 'E.Sun Bank',
    available: true,
    description: 'Pilot partner - Full account aggregation support',
  },
  {
    code: 'FUBON',
    name: 'Fubon Bank',
    available: false,
    description: 'Coming soon',
  },
  {
    code: 'CTBC',
    name: 'CTBC Bank',
    available: false,
    description: 'Coming soon',
  },
  {
    code: 'CATHAY',
    name: 'Cathay Bank',
    available: false,
    description: 'Coming soon',
  },
]

export function OpenFinanceConnect({ onConnectionChange }: OpenFinanceConnectProps) {
  const { t } = useTranslation()
  const [connections, setConnections] = useState<OpenFinanceConnection[]>([])
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState<string | null>(null)
  const [showUpload, setShowUpload] = useState(false)

  useEffect(() => {
    loadConnections()
  }, [])

  const loadConnections = async () => {
    try {
      const result = await agentService.getOpenFinanceConnections()
      setConnections(result)
      onConnectionChange?.(result)
    } catch (err) {
      console.error('Failed to load open finance connections:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleConnect = async (bankCode: string) => {
    setConnecting(bankCode)
    try {
      // In a real implementation, this would redirect to the bank's OAuth flow
      const result = await agentService.connectOpenFinance(bankCode)
      if (result) {
        await loadConnections()
      }
    } catch (err) {
      console.error('Failed to connect bank:', err)
    } finally {
      setConnecting(null)
    }
  }

  const handleDisconnect = async (bankCode: string) => {
    if (!confirm(`Disconnect from ${bankCode}? This will stop fetching new transactions.`)) return

    try {
      await agentService.disconnectOpenFinance(bankCode)
      await loadConnections()
    } catch (err) {
      console.error('Failed to disconnect bank:', err)
    }
  }

  const getConnectionStatus = (bankCode: string): OpenFinanceConnection | undefined => {
    return connections.find((c) => c.bank_code === bankCode)
  }

  if (loading) {
    return (
      <div className="openfinance-panel openfinance-loading">
        <span>{t('common.loading', 'Loading...')}</span>
      </div>
    )
  }

  return (
    <div className="openfinance-panel">
      <div className="openfinance-header">
        <h3>{t('agent.openFinance.title', 'Open Finance Connections')}</h3>
        <button
          className="openfinance-upload-toggle"
          onClick={() => setShowUpload(!showUpload)}
        >
          {showUpload ? t('agent.openFinance.hideUpload', 'Hide Upload') : t('agent.openFinance.manualUpload', 'Manual Upload')}
        </button>
      </div>

      {showUpload && (
        <div className="openfinance-upload-section">
          <p className="openfinance-upload-desc">
            {t('agent.openFinance.uploadDesc', 'Upload bank statements manually if auto-import is not available.')}
          </p>
          <div className="openfinance-upload-dropzone">
            <input type="file" accept=".csv,.ofx,.qfx" id="bank-upload" className="openfinance-upload-input" />
            <label htmlFor="bank-upload" className="openfinance-upload-label">
              <span className="openfinance-upload-icon">📁</span>
              <span>{t('agent.openFinance.dropzone', 'Drop files here or click to upload')}</span>
              <span className="openfinance-upload-hint">CSV, OFX, QFX supported</span>
            </label>
          </div>
        </div>
      )}

      <div className="openfinance-banks">
        {PILOT_BANKS.map((bank) => {
          const connection = getConnectionStatus(bank.code)
          const isConnected = connection?.status === 'CONNECTED'

          return (
            <div key={bank.code} className={`openfinance-bank-card ${isConnected ? 'connected' : ''}`}>
              <div className="openfinance-bank-info">
                <div className="openfinance-bank-logo">
                  {bank.code === 'ESUN' && <span className="bank-icon">🏦</span>}
                  {bank.code !== 'ESUN' && <span className="bank-icon">🏛️</span>}
                </div>
                <div className="openfinance-bank-details">
                  <span className="openfinance-bank-name">{bank.name}</span>
                  <span className="openfinance-bank-desc">{bank.description}</span>
                </div>
              </div>

              <div className="openfinance-bank-status">
                {isConnected ? (
                  <>
                    <span className="openfinance-connected-badge">
                      ✓ {t('agent.openFinance.connected', 'Connected')}
                    </span>
                    <span className="openfinance-account-count">
                      {connection?.account_count || 0} {t('agent.openFinance.accounts', 'accounts')}
                    </span>
                  </>
                ) : bank.available ? (
                  <button
                    className="openfinance-connect-btn"
                    onClick={() => handleConnect(bank.code)}
                    disabled={connecting === bank.code}
                  >
                    {connecting === bank.code
                      ? t('common.loading', 'Connecting...')
                      : t('agent.openFinance.connect', 'Connect')}
                  </button>
                ) : (
                  <span className="openfinance-coming-soon">
                    {t('agent.openFinance.comingSoon', 'Coming Soon')}
                  </span>
                )}
              </div>

              {isConnected && (
                <button
                  className="openfinance-disconnect-btn"
                  onClick={() => handleDisconnect(bank.code)}
                >
                  {t('agent.openFinance.disconnect', 'Disconnect')}
                </button>
              )}
            </div>
          )
        })}
      </div>

      <div className="openfinance-footer">
        <p className="openfinance-security-note">
          🔒 {t('agent.openFinance.securityNote', 'Your credentials are securely stored and never shared.')}
        </p>
      </div>
    </div>
  )
}
