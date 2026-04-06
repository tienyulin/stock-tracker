import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AgentStatusCard } from '../components/AgentStatusCard'
import { GoalSettingPanel } from '../components/GoalSettingPanel'
import { OpenFinanceConnect } from '../components/OpenFinanceConnect'
import { RebalanceActionCard } from '../components/RebalanceActionCard'
import { agentService, type AgentRecommendation, type MonitoringItem } from '../services/agentApi'
import './AgentDashboard.css'

const PRIORITY_COLORS = {
  LOW: '#6b7280',
  MEDIUM: '#eab308',
  HIGH: '#ef4444',
}

const MONITORING_STATUS_COLORS = {
  OK: '#22c55e',
  WARNING: '#f97316',
  CRITICAL: '#ef4444',
}

function RecommendationIcon({ type }: { type: AgentRecommendation['type'] }) {
  switch (type) {
    case 'REBALANCE':
      return <span className="rec-icon" title="Rebalance">⚖️</span>
    case 'GOAL_ADJUSTMENT':
      return <span className="rec-icon" title="Goal Adjustment">🎯</span>
    case 'SALARY_DEPOSIT':
      return <span className="rec-icon" title="Salary Deposit">💰</span>
    case 'RISK_ALERT':
      return <span className="rec-icon" title="Risk Alert">⚠️</span>
    default:
      return <span className="rec-icon">📋</span>
  }
}

export default function AgentDashboard() {
  const { t } = useTranslation()
  const [recommendations, setRecommendations] = useState<AgentRecommendation[]>([])
  const [monitoringItems, setMonitoringItems] = useState<MonitoringItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 60000) // Refresh every minute
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [recs, items] = await Promise.all([
        agentService.getAgentRecommendations(),
        agentService.getMonitoringItems(),
      ])
      setRecommendations(recs)
      setMonitoringItems(items)
    } catch (err) {
      console.error('Failed to load agent dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRecommendationAction = async (id: string, action: 'ACCEPTED' | 'DISMISSED') => {
    // In a full implementation, this would call an API to update the recommendation status
    console.log(`Recommendation ${id} ${action}`)
    // Optimistically update UI
    setRecommendations((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: action } : r))
    )
  }

  const formatTime = (iso: string) => {
    return new Date(iso).toLocaleString()
  }

  if (loading) {
    return (
      <div className="agent-dashboard agent-dashboard-loading">
        <div className="loading-spinner" />
        <span>{t('common.loading', 'Loading AI Agent Dashboard...')}</span>
      </div>
    )
  }

  return (
    <div className="agent-dashboard">
      <div className="agent-dashboard-header">
        <h1>{t('agent.dashboard.title', 'AI Agent Dashboard')}</h1>
        <p className="agent-dashboard-subtitle">
          {t('agent.dashboard.subtitle', 'Your intelligent investment assistant')}
        </p>
      </div>

      <div className="agent-dashboard-grid">
        {/* Agent Status Card */}
        <div className="agent-dashboard-section agent-section-status">
          <AgentStatusCard />
        </div>

        {/* Monitoring Items */}
        <div className="agent-dashboard-section agent-section-monitoring">
          <div className="section-card">
            <h3>{t('agent.monitoring.title', 'Active Monitoring')}</h3>
            {monitoringItems.length === 0 ? (
              <div className="section-empty">
                {t('agent.monitoring.empty', 'No active monitoring items')}
              </div>
            ) : (
              <div className="monitoring-list">
                {monitoringItems.map((item) => (
                  <div key={item.id} className="monitoring-item">
                    <div
                      className="monitoring-status-dot"
                      style={{ backgroundColor: MONITORING_STATUS_COLORS[item.status] }}
                    />
                    <div className="monitoring-content">
                      <span className="monitoring-type">
                        {t(`agent.monitoring.types.${item.type.replace('_', '')}`, item.type)}
                      </span>
                      <span className="monitoring-title">{item.title}</span>
                      <span className="monitoring-details">{item.details}</span>
                    </div>
                    <span className="monitoring-time">
                      {formatTime(item.updated_at)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Rebalance Action Card */}
        <div className="agent-dashboard-section agent-section-rebalance">
          <RebalanceActionCard />
        </div>

        {/* Recommendations */}
        <div className="agent-dashboard-section agent-section-recommendations">
          <div className="section-card">
            <h3>{t('agent.recommendations.title', 'Recent Recommendations')}</h3>
            {recommendations.length === 0 ? (
              <div className="section-empty">
                {t('agent.recommendations.empty', 'No recommendations yet')}
              </div>
            ) : (
              <div className="recommendations-list">
                {recommendations.map((rec) => (
                  <div key={rec.id} className="recommendation-item">
                    <RecommendationIcon type={rec.type} />
                    <div className="recommendation-content">
                      <div className="recommendation-header">
                        <span className="recommendation-title">{rec.title}</span>
                        <span
                          className="recommendation-priority"
                          style={{ color: PRIORITY_COLORS[rec.priority] }}
                        >
                          {t(`agent.recommendations.priority.${rec.priority}`, rec.priority)}
                        </span>
                      </div>
                      <p className="recommendation-description">{rec.description}</p>
                      <div className="recommendation-footer">
                        <span className="recommendation-time">
                          {formatTime(rec.created_at)}
                        </span>
                        {rec.status === 'PENDING' && (
                          <div className="recommendation-actions">
                            <button
                              className="rec-accept-btn"
                              onClick={() => handleRecommendationAction(rec.id, 'ACCEPTED')}
                            >
                              {t('agent.recommendations.accept', 'Accept')}
                            </button>
                            <button
                              className="rec-dismiss-btn"
                              onClick={() => handleRecommendationAction(rec.id, 'DISMISSED')}
                            >
                              {t('agent.recommendations.dismiss', 'Dismiss')}
                            </button>
                          </div>
                        )}
                        {rec.status !== 'PENDING' && (
                          <span className="rec-status">
                            {t(`agent.recommendations.status.${rec.status}`, rec.status)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Goal Setting Panel */}
        <div className="agent-dashboard-section agent-section-goals">
          <GoalSettingPanel />
        </div>

        {/* Open Finance Connect */}
        <div className="agent-dashboard-section agent-section-openfinance">
          <OpenFinanceConnect />
        </div>

        {/* Quick Actions */}
        <div className="agent-dashboard-section agent-section-actions">
          <div className="section-card">
            <h3>{t('agent.quickActions.title', 'Quick Actions')}</h3>
            <div className="quick-actions-grid">
              <button className="quick-action-btn">
                <span className="quick-action-icon">⚖️</span>
                <span>{t('agent.quickActions.rebalance', 'Rebalance')}</span>
              </button>
              <button className="quick-action-btn">
                <span className="quick-action-icon">🎯</span>
                <span>{t('agent.quickActions.setGoal', 'Set Goal')}</span>
              </button>
              <button className="quick-action-btn">
                <span className="quick-action-icon">🏦</span>
                <span>{t('agent.quickActions.connectBank', 'Connect Bank')}</span>
              </button>
              <button className="quick-action-btn">
                <span className="quick-action-icon">📊</span>
                <span>{t('agent.quickActions.viewReport', 'View Report')}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
