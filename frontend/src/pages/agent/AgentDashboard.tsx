import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { agentService, getErrorMessage } from '../../services/api'
import type { AgentStateResponse, AgentState } from '../../types/agent'
import GoalSetting from '../../components/agent/GoalSetting'
import AlertList from '../../components/agent/AlertList'
import RebalanceAction from '../../components/agent/RebalanceAction'
import TaxImpact from '../../components/agent/TaxImpact'
import OpenFinanceConnect from '../../components/agent/OpenFinanceConnect'
import './AgentDashboard.css'

const AGENT_STATE_LABELS: Record<AgentState, { label: string; desc: string }> = {
  IDLE: { label: 'Idle', desc: 'Agent is idle and not monitoring' },
  MONITORING: { label: 'Monitoring', desc: 'Actively watching your portfolio' },
  ANALYZING: { label: 'Analyzing', desc: 'Analyzing market conditions and signals' },
  REBALANCING: { label: 'Rebalancing', desc: 'Executing portfolio rebalancing trades' },
  HARVESTING: { label: 'Tax-Loss Harvesting', desc: 'Identifying tax-loss harvesting opportunities' },
  ERROR: { label: 'Error', desc: 'Agent encountered an error' },
}

const STATE_COLORS: Record<AgentState, string> = {
  IDLE: '#9e9e9e',
  MONITORING: '#1565c0',
  ANALYZING: '#6a1b9a',
  REBALANCING: '#e65100',
  HARVESTING: '#2e7d32',
  ERROR: '#c62828',
}

function AgentDashboard() {
  const { t } = useTranslation()
  const [agentState, setAgentState] = useState<AgentStateResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notification, setNotification] = useState<string | null>(null)
  const [toggling, setToggling] = useState(false)

  useEffect(() => {
    loadAgentState()
  }, [])

  const loadAgentState = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await agentService.getState()
      setAgentState(data)
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

  const handleToggleMonitoring = async () => {
    if (!agentState) return
    try {
      setToggling(true)
      if (agentState.is_active) {
        await agentService.stopMonitoring()
        showNotification('Agent monitoring stopped')
      } else {
        await agentService.startMonitoring()
        showNotification('Agent monitoring started')
      }
      await loadAgentState()
    } catch (err) {
      showNotification(getErrorMessage(err))
    } finally {
      setToggling(false)
    }
  }

  const stateInfo = agentState ? AGENT_STATE_LABELS[agentState.state] : null

  if (loading) {
    return (
      <div className="agent-dashboard">
        <div className="loading-state">Loading AI Agent Dashboard...</div>
      </div>
    )
  }

  return (
    <div className="agent-dashboard">
      <div className="page-header">
        <div className="header-title">
          <h1>AI Agent Dashboard</h1>
          <p className="header-subtitle">{t('agent.dashboard.subtitle', 'Your intelligent portfolio assistant')}</p>
        </div>
        <button
          className={`btn-toggle-monitoring ${agentState?.is_active ? 'btn-stop' : 'btn-start'}`}
          onClick={handleToggleMonitoring}
          disabled={toggling}
        >
          {toggling ? '...' : agentState?.is_active
            ? t('agent.dashboard.stopMonitoring', 'Stop Monitoring')
            : t('agent.dashboard.startMonitoring', 'Start Monitoring')}
        </button>
      </div>

      {notification && <div className="notification-banner">{notification}</div>}
      {error && <div className="error-banner">{error}</div>}

      {agentState && (
        <div className="agent-state-card">
          <div className="state-indicator" style={{ borderColor: STATE_COLORS[agentState.state] }}>
            <div className="state-dot" style={{ backgroundColor: STATE_COLORS[agentState.state] }} />
          </div>
          <div className="state-info">
            <div className="state-label">{stateInfo?.label}</div>
            <div className="state-desc">{stateInfo?.desc}</div>
          </div>
          <div className="state-stats">
            <div className="stat-item">
              <div className="stat-value">{agentState.goals_count}</div>
              <div className="stat-label">{t('agent.dashboard.goals', 'Goals')}</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{agentState.alerts_count}</div>
              <div className="stat-label">{t('agent.dashboard.alerts', 'Alerts')}</div>
            </div>
            {agentState.started_at && (
              <div className="stat-item">
                <div className="stat-label">{t('agent.dashboard.startedAt', 'Started')}</div>
                <div className="stat-value-small">
                  {new Date(agentState.started_at).toLocaleDateString()}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="agent-panels">
        <div className="panel-left">
          <GoalSetting />
          <RebalanceAction />
        </div>
        <div className="panel-right">
          <AlertList />
          <TaxImpact />
          <OpenFinanceConnect />
        </div>
      </div>
    </div>
  )
}

export default AgentDashboard
