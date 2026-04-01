import { useState, useEffect } from 'react'
import { alertService } from '../services/api'
import type { Alert } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import './Alerts.css'

type FilterType = 'all' | 'active' | 'triggered'

function Alerts() {
  const { user } = useAuth()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<FilterType>('active')
  const [notification, setNotification] = useState<string | null>(null)

  useEffect(() => {
    if (user?.id) {
      loadAlerts()
    }
  }, [user?.id])

  const userId = user?.id || ''

  const loadAlerts = async () => {
    try {
      setLoading(true)
      setError(null)
      const userAlerts = await alertService.getAlerts(userId)
      setAlerts(userAlerts)
    } catch (err) {
      setError('Failed to load alerts')
    } finally {
      setLoading(false)
    }
  }

  const showNotification = (message: string) => {
    setNotification(message)
    setTimeout(() => setNotification(null), 3000)
  }

  const handleToggle = async (alertId: string, isActive: boolean) => {
    try {
      await alertService.updateAlert(userId, alertId, { is_active: !isActive })
      setAlerts(alerts.map(a =>
        a.id === alertId ? { ...a, is_active: !isActive } : a
      ))
      showNotification(isActive ? 'Alert disabled' : 'Alert enabled')
    } catch (err) {
      showNotification('Failed to update alert')
    }
  }

  const handleDelete = async (alertId: string) => {
    try {
      await alertService.deleteAlert(userId, alertId)
      setAlerts(alerts.filter(a => a.id !== alertId))
      showNotification('Alert deleted')
    } catch (err) {
      showNotification('Failed to delete alert')
    }
  }

  const handleResetAlert = async (alertId: string) => {
    try {
      const updated = await alertService.updateAlert(userId, alertId, { triggered_at: undefined })
      setAlerts(alerts.map(a => a.id === alertId ? updated : a))
      showNotification('Alert reset successfully')
    } catch (err) {
      showNotification('Failed to reset alert')
    }
  }

  const getAlertTypeLabel = (type: string) => {
    switch (type) {
      case 'above': return 'Price Above'
      case 'below': return 'Price Below'
      case 'change_pct': return 'Change %'
      default: return type
    }
  }

  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'active') return alert.is_active && !alert.triggered_at
    if (filter === 'triggered') return !!alert.triggered_at
    return true
  })

  const counts = {
    all: alerts.length,
    active: alerts.filter(a => a.is_active && !a.triggered_at).length,
    triggered: alerts.filter(a => !!a.triggered_at).length,
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="alerts">
      <h2>Price Alerts</h2>

      {/* Notification toast */}
      {notification && <div className="notification">{notification}</div>}

      {/* Filter tabs */}
      <div className="filter-tabs">
        {(['active', 'triggered', 'all'] as FilterType[]).map(f => (
          <button
            key={f}
            className={`filter-tab ${filter === f ? 'active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
            <span className="count">{counts[f]}</span>
          </button>
        ))}
      </div>

      {/* Refresh button */}
      <button className="refresh-btn" onClick={loadAlerts}>
        ↻ Refresh
      </button>

      {filteredAlerts.length === 0 ? (
        <p className="empty-message">
          {filter === 'active' && 'No active alerts. Create one from the search page.'}
          {filter === 'triggered' && 'No triggered alerts yet.'}
          {filter === 'all' && 'No alerts set. Create one from the search page.'}
        </p>
      ) : (
        <ul className="alert-list">
          {filteredAlerts.map(alert => (
            <li key={alert.id} className={`alert-item ${!alert.is_active ? 'disabled' : ''} ${alert.triggered_at ? 'triggered' : ''}`}>
              <div className="alert-info">
                <span className="symbol">{alert.symbol}</span>
                <span className="type">{getAlertTypeLabel(alert.condition_type)}</span>
                <span className="threshold">${alert.threshold.toFixed(2)}</span>
                {alert.triggered_at && (
                  <span className="triggered-badge">
                    Triggered {new Date(alert.triggered_at).toLocaleDateString()}
                  </span>
                )}
              </div>
              <div className="alert-actions">
                {alert.triggered_at && (
                  <button
                    className="reset-btn"
                    onClick={() => handleResetAlert(alert.id)}
                    title="Reset alert"
                  >
                    Reset
                  </button>
                )}
                <button
                  className={`toggle-btn ${alert.is_active ? 'active' : ''}`}
                  onClick={() => handleToggle(alert.id, alert.is_active)}
                  disabled={!!alert.triggered_at}
                >
                  {alert.is_active ? 'ON' : 'OFF'}
                </button>
                <button
                  className="delete-btn"
                  onClick={() => handleDelete(alert.id)}
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default Alerts
