import { useState, useEffect } from 'react'
import { alertService } from '../services/api'
import type { PriceAlert } from '../types'
import './Alerts.css'

function Alerts() {
  const [alerts, setAlerts] = useState<PriceAlert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAlerts()
  }, [])

  const loadAlerts = async () => {
    try {
      setLoading(true)
      const userAlerts = await alertService.getUserAlerts('demo-user')
      setAlerts(userAlerts)
    } catch (err) {
      console.error('Failed to load alerts:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = async (alertId: string, enabled: boolean) => {
    try {
      await alertService.toggleAlert('demo-user', alertId, enabled)
      setAlerts(alerts.map(a =>
        a.id === alertId ? { ...a, enabled } : a
      ))
    } catch (err) {
      console.error('Failed to toggle alert:', err)
    }
  }

  const handleDelete = async (alertId: string) => {
    try {
      await alertService.deleteAlert('demo-user', alertId)
      setAlerts(alerts.filter(a => a.id !== alertId))
    } catch (err) {
      console.error('Failed to delete alert:', err)
    }
  }

  const getAlertTypeLabel = (type: string) => {
    switch (type) {
      case 'PRICE_ABOVE': return 'Price Above'
      case 'PRICE_BELOW': return 'Price Below'
      case 'PRICE_CHANGE_PERCENT': return 'Change %'
      default: return type
    }
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="alerts">
      <h2>Price Alerts</h2>
      {alerts.length === 0 ? (
        <p className="empty-message">No alerts set. Create one from the search page.</p>
      ) : (
        <ul className="alert-list">
          {alerts.map(alert => (
            <li key={alert.id} className={`alert-item ${!alert.enabled ? 'disabled' : ''}`}>
              <div className="alert-info">
                <span className="symbol">{alert.symbol}</span>
                <span className="type">{getAlertTypeLabel(alert.alert_type)}</span>
                <span className="threshold">${alert.threshold}</span>
              </div>
              <div className="alert-actions">
                <button
                  className={`toggle-btn ${alert.enabled ? 'active' : ''}`}
                  onClick={() => handleToggle(alert.id, !alert.enabled)}
                >
                  {alert.enabled ? 'ON' : 'OFF'}
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
