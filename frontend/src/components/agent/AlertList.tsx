import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { agentService, getErrorMessage } from '../../services/api'
import type { Alert } from '../../types/agent'
import './AlertList.css'

type FilterType = 'all' | 'unacknowledged'

function AlertList() {
  const { t } = useTranslation()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notification, setNotification] = useState<string | null>(null)
  const [filter, setFilter] = useState<FilterType>('unacknowledged')

  useEffect(() => {
    loadAlerts()
  }, [])

  const loadAlerts = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await agentService.getAlerts()
      setAlerts(data)
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

  const handleAcknowledge = async (alertId: string) => {
    try {
      const updated = await agentService.acknowledgeAlert(alertId)
      setAlerts(alerts.map(a => a.id === alertId ? updated : a))
      showNotification('Alert acknowledged')
    } catch (err) {
      showNotification(getErrorMessage(err))
    }
  }

  const getSeverityClass = (severity: Alert['severity']) => {
    switch (severity) {
      case 'CRITICAL': return 'severity-critical'
      case 'WARNING': return 'severity-warning'
      default: return 'severity-info'
    }
  }

  const getTypeLabel = (type: Alert['alert_type']) => {
    switch (type) {
      case 'PRICE': return t('agent.alert.typePrice', 'Price')
      case 'ALLOCATION': return t('agent.alert.typeAllocation', 'Allocation')
      case 'DIVERSIFICATION': return t('agent.alert.typeDiversification', 'Diversification')
      case 'REBALANCE': return t('agent.alert.typeRebalance', 'Rebalance')
      case 'TAX_LOSS': return t('agent.alert.typeTaxLoss', 'Tax Loss')
      default: return type
    }
  }

  const getTimeAgo = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)
    if (diffMins < 1) return t('agent.alert.justNow', 'just now')
    if (diffMins < 60) return t('agent.alert.minsAgo', '{{n}}m ago', { n: diffMins })
    if (diffHours < 24) return t('agent.alert.hoursAgo', '{{n}}h ago', { n: diffHours })
    return t('agent.alert.daysAgo', '{{n}}d ago', { n: diffDays })
  }

  const filteredAlerts = filter === 'unacknowledged'
    ? alerts.filter(a => !a.acknowledged)
    : alerts

  if (loading) {
    return <div className="alert-list-loading">Loading alerts...</div>
  }

  return (
    <div className="alert-list">
      <div className="alert-list-header">
        <h3>{t('agent.alerts.title', 'AI Agent Alerts')}</h3>
        <div className="alert-filter-tabs">
          <button
            className={`filter-tab ${filter === 'unacknowledged' ? 'active' : ''}`}
            onClick={() => setFilter('unacknowledged')}
          >
            {t('agent.alerts.unacknowledged', 'Unacknowledged')} ({alerts.filter(a => !a.acknowledged).length})
          </button>
          <button
            className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            {t('agent.alerts.all', 'All')} ({alerts.length})
          </button>
        </div>
      </div>

      {notification && <div className="notification">{notification}</div>}
      {error && <div className="error">{error}</div>}

      <div className="alerts-table-container">
        {filteredAlerts.length === 0 ? (
          <div className="no-alerts">{t('agent.alerts.empty', 'No alerts')}</div>
        ) : (
          <table className="alerts-table">
            <thead>
              <tr>
                <th>{t('agent.alert.severity', 'Severity')}</th>
                <th>{t('agent.alert.type', 'Type')}</th>
                <th>{t('agent.alert.message', 'Message')}</th>
                <th>{t('agent.alert.time', 'Time')}</th>
                <th>{t('agent.alert.actions', 'Actions')}</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.map(alert => (
                <tr key={alert.id} className={alert.acknowledged ? 'acknowledged' : ''}>
                  <td>
                    <span className={`severity-badge ${getSeverityClass(alert.severity)}`}>
                      {alert.severity}
                    </span>
                  </td>
                  <td>
                    <span className="type-label">{getTypeLabel(alert.alert_type)}</span>
                  </td>
                  <td className="message-cell">{alert.message}</td>
                  <td className="time-cell">{getTimeAgo(alert.created_at)}</td>
                  <td>
                    {!alert.acknowledged && (
                      <button
                        className="btn-acknowledge"
                        onClick={() => handleAcknowledge(alert.id)}
                      >
                        {t('agent.alert.acknowledge', 'Acknowledge')}
                      </button>
                    )}
                    {alert.acknowledged && (
                      <span className="acknowledged-label">{t('agent.alert.acknowledged', 'Acknowledged')}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export default AlertList
