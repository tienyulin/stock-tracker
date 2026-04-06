import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { agentService, getErrorMessage } from '../../services/api'
import type { RebalanceAction } from '../../types/agent'
import './RebalanceAction.css'

function RebalanceAction() {
  const { t } = useTranslation()
  const [actions, setActions] = useState<RebalanceAction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notification, setNotification] = useState<string | null>(null)

  useEffect(() => {
    loadActions()
  }, [])

  const loadActions = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await agentService.getRebalanceActions()
      setActions(data)
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

  const handleApprove = async (actionId: string) => {
    try {
      const updated = await agentService.approveRebalanceAction(actionId)
      setActions(actions.map(a => a.id === actionId ? updated : a))
      showNotification('Rebalance action approved')
    } catch (err) {
      showNotification(getErrorMessage(err))
    }
  }

  const handleReject = async (actionId: string) => {
    try {
      const updated = await agentService.rejectRebalanceAction(actionId)
      setActions(actions.map(a => a.id === actionId ? updated : a))
      showNotification('Rebalance action rejected')
    } catch (err) {
      showNotification(getErrorMessage(err))
    }
  }

  const getActionIcon = (actionType: RebalanceAction['action_type']) => {
    switch (actionType) {
      case 'BUY': return '↑'
      case 'SELL': return '↓'
      case 'SWAP': return '⇄'
    }
  }

  const getActionClass = (actionType: RebalanceAction['action_type']) => {
    switch (actionType) {
      case 'BUY': return 'action-buy'
      case 'SELL': return 'action-sell'
      case 'SWAP': return 'action-swap'
    }
  }

  const getStatusClass = (status: RebalanceAction['status']) => {
    switch (status) {
      case 'APPROVED': return 'status-approved'
      case 'REJECTED': return 'status-rejected'
      default: return 'status-proposed'
    }
  }

  const proposedActions = actions.filter(a => a.status === 'PROPOSED')
  const processedActions = actions.filter(a => a.status !== 'PROPOSED')

  if (loading) {
    return <div className="rebalance-loading">Loading rebalance actions...</div>
  }

  return (
    <div className="rebalance-action">
      <div className="rebalance-header">
        <h3>{t('agent.rebalance.title', 'Rebalancing Actions')}</h3>
        <button className="btn-refresh" onClick={loadActions}>↻ {t('common.refresh', 'Refresh')}</button>
      </div>

      {notification && <div className="notification">{notification}</div>}
      {error && <div className="error">{error}</div>}

      <div className="proposed-section">
        <h4>{t('agent.rebalance.proposed', 'Proposed Trades')}</h4>
        {proposedActions.length === 0 ? (
          <div className="no-actions">{t('agent.rebalance.noProposed', 'No proposed trades pending review')}</div>
        ) : (
          <div className="actions-list">
            {proposedActions.map(action => (
              <div key={action.id} className="action-card">
                <div className={`action-icon ${getActionClass(action.action_type)}`}>
                  {getActionIcon(action.action_type)}
                </div>
                <div className="action-details">
                  <div className="action-symbol">
                    <span className={`type-badge ${getActionClass(action.action_type)}`}>{action.action_type}</span>
                    <strong>{action.symbol}</strong>
                  </div>
                  <div className="action-values">
                    {action.quantity != null && (
                      <span>{t('agent.rebalance.quantity', 'Qty')}: {action.quantity}</span>
                    )}
                    {action.amount != null && (
                      <span>${action.amount.toLocaleString()}</span>
                    )}
                  </div>
                  <div className="action-reason">{action.reason}</div>
                  <div className="action-time">
                    {new Date(action.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="action-buttons">
                  <button
                    className="btn-approve"
                    onClick={() => handleApprove(action.id)}
                  >
                    ✓ {t('agent.rebalance.approve', 'Approve')}
                  </button>
                  <button
                    className="btn-reject"
                    onClick={() => handleReject(action.id)}
                  >
                    ✗ {t('agent.rebalance.reject', 'Reject')}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {processedActions.length > 0 && (
        <div className="processed-section">
          <h4>{t('agent.rebalance.history', 'History')}</h4>
          <div className="actions-list processed">
            {processedActions.map(action => (
              <div key={action.id} className="action-card">
                <div className={`action-icon ${getActionClass(action.action_type)}`}>
                  {getActionIcon(action.action_type)}
                </div>
                <div className="action-details">
                  <div className="action-symbol">
                    <span className={`type-badge ${getActionClass(action.action_type)}`}>{action.action_type}</span>
                    <strong>{action.symbol}</strong>
                  </div>
                  <div className="action-reason">{action.reason}</div>
                </div>
                <div className={`action-status ${getStatusClass(action.status)}`}>
                  {action.status}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default RebalanceAction
