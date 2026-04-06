import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { agentService, type AgentStatus, type AgentState } from '../services/agentApi'
import './AgentStatusCard.css'

interface AgentStatusCardProps {
  onStateChange?: (state: AgentState) => void
}

const STATE_COLORS: Record<AgentState, string> = {
  IDLE: '#6b7280',
  MONITORING: '#3b82f6',
  ANALYZING: '#eab308',
  RECOMMENDING: '#f97316',
  ACTING: '#22c55e',
}

const STATE_LABELS: Record<AgentState, string> = {
  IDLE: 'Idle',
  MONITORING: 'Monitoring',
  ANALYZING: 'Analyzing',
  RECOMMENDING: 'Recommending',
  ACTING: 'Acting',
}

function formatTimestamp(iso: string): string {
  const date = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
  return date.toLocaleDateString()
}

export function AgentStatusCard({ onStateChange }: AgentStatusCardProps) {
  const { t } = useTranslation()
  const [status, setStatus] = useState<AgentStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStatus()
    const interval = setInterval(loadStatus, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const loadStatus = async () => {
    try {
      const result = await agentService.getAgentState()
      if (result) {
        setStatus(result)
        onStateChange?.(result.state)
      } else {
        setError('Failed to load agent status')
      }
    } catch (err) {
      setError('Failed to load agent status')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="agent-status-card agent-status-loading">
        <div className="agent-status-pulse" />
        <span>{t('agent.loading', 'Loading agent status...')}</span>
      </div>
    )
  }

  if (error || !status) {
    return (
      <div className="agent-status-card agent-status-error">
        <span>{error || t('agent.error', 'Unable to connect to agent')}</span>
        <button onClick={loadStatus} className="agent-status-retry">
          {t('common.retry', 'Retry')}
        </button>
      </div>
    )
  }

  const stateColor = STATE_COLORS[status.state]

  return (
    <div className="agent-status-card">
      <div className="agent-status-header">
        <div className="agent-status-indicator" style={{ backgroundColor: stateColor }}>
          <div className="agent-status-dot" style={{ backgroundColor: stateColor }} />
        </div>
        <div className="agent-status-info">
          <span className="agent-status-label">{t('agent.title', 'AI Agent')}</span>
          <span
            className="agent-status-state"
            style={{ color: stateColor }}
          >
            {t(`agent.states.${status.state}`, STATE_LABELS[status.state])}
          </span>
        </div>
      </div>

      <div className="agent-status-body">
        <div className="agent-status-activity">
          <span className="agent-activity-text">{status.activity_summary || t('agent.idle', 'Agent is idle')}</span>
        </div>

        <div className="agent-status-meta">
          <span className="agent-last-active">
            {t('agent.lastActive', 'Last active')}: {formatTimestamp(status.last_active)}
          </span>
        </div>

        {status.active_tasks && status.active_tasks.length > 0 && (
          <div className="agent-active-tasks">
            <span className="agent-tasks-label">{t('agent.activeTasks', 'Active Tasks')}:</span>
            <ul className="agent-tasks-list">
              {status.active_tasks.map((task, idx) => (
                <li key={idx} className="agent-task-item">{task}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
