import { useState, useEffect } from 'react'
import { alertService } from '../services/api'
import type { Alert } from '../services/api'
import './Alerts.css'

const DEMO_USER_ID = '00000000-0000-0000-0000-000000000001'

function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadAlerts()
  }, [])

  const loadAlerts = async () => {
    try {
      setLoading(true)
      setError(null)
      const userAlerts = await alertService.getAlerts(DEMO_USER_ID)
      setAlerts(userAlerts)
    } catch (err) {
      setError('Failed to load alerts')
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = async (alertId: string, isActive: boolean) => {
    try {
      await alertService.updateAlert(DEMO_USER_ID, alertId, { is_active: !isActive })
      setAlerts(alerts.map(a =>
        a.id === alertId ? { ...a, is_active: !isActive } : a
      ))
    } catch (err) {
      console.error('Failed to toggle alert:', err)
    }
  }

  const handleDelete = async (alertId: string) => {
    try {
      await alertService.deleteAlert(DEMO_USER_ID, alertId)
      setAlerts(alerts.filter(a => a.id !== alertId))
    } catch (err) {
      console.error('Failed to delete alert:', err)
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

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="alerts">
      <h2>Price Alerts</h2>
      {alerts.length === 0 ? (
        <p className="empty-message">No alerts set. Create one from the search page.</p>
      ) : (
        <ul className="alert-list">
          {alerts.map(alert => (
            <li key={alert.id} className={`alert-item ${!alert.is_active ? 'disabled' : ''}`}>
              <div className="alert-info">
                <span className="symbol">{alert.symbol}</span>
                <span className="type">{getAlertTypeLabel(alert.condition_type)}</span>
                <span className="threshold">${alert.threshold.toFixed(2)}</span>
                {alert.triggered_at && (
                  <span className="triggered">Triggered: {new Date(alert.triggered_at).toLocaleDateString()}</span>
                )}
              </div>
              <div className="alert-actions">
                <button
                  className={`toggle-btn ${alert.is_active ? 'active' : ''}`}
                  onClick={() => handleToggle(alert.id, alert.is_active)}
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
