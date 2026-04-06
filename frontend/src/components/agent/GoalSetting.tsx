import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { agentService, getErrorMessage } from '../../services/api'
import type { Goal, GoalCreate } from '../../types/agent'
import './GoalSetting.css'

function GoalSetting() {
  const { t } = useTranslation()
  const [goals, setGoals] = useState<Goal[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notification, setNotification] = useState<string | null>(null)

  // Form state
  const [showForm, setShowForm] = useState(false)
  const [formName, setFormName] = useState('')
  const [formTarget, setFormTarget] = useState('')
  const [formCurrent, setFormCurrent] = useState('')
  const [formThreshold, setFormThreshold] = useState('5')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadGoals()
  }, [])

  const loadGoals = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await agentService.getGoals()
      setGoals(data)
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formName || !formTarget || !formCurrent) return

    try {
      setSubmitting(true)
      const goalData: GoalCreate = {
        name: formName,
        target_value: parseFloat(formTarget),
        current_value: parseFloat(formCurrent),
        threshold_pct: parseFloat(formThreshold) || 5,
      }
      const created = await agentService.createGoal(goalData)
      setGoals([...goals, created])
      setShowForm(false)
      setFormName('')
      setFormTarget('')
      setFormCurrent('')
      setFormThreshold('5')
      showNotification('Goal added successfully')
    } catch (err) {
      showNotification(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (goalId: string) => {
    try {
      await agentService.deleteGoal(goalId)
      setGoals(goals.filter(g => g.id !== goalId))
      showNotification('Goal deleted')
    } catch (err) {
      showNotification(getErrorMessage(err))
    }
  }

  const getProgressPct = (goal: Goal) => {
    if (goal.target_value === 0) return 0
    return Math.min(100, (goal.current_value / goal.target_value) * 100)
  }

  const isAtRisk = (goal: Goal) => {
    const diff = goal.target_value - goal.current_value
    const threshold = goal.target_value * (goal.threshold_pct / 100)
    return diff > 0 && diff <= threshold
  }

  if (loading) {
    return <div className="goal-setting-loading">Loading goals...</div>
  }

  return (
    <div className="goal-setting">
      <div className="goal-setting-header">
        <h3>{t('agent.goals.title', 'Investment Goals')}</h3>
        <button
          className="btn-add-goal"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? t('common.cancel', 'Cancel') : t('agent.goals.add', '+ Add Goal')}
        </button>
      </div>

      {notification && <div className="notification">{notification}</div>}
      {error && <div className="error">{error}</div>}

      {showForm && (
        <form className="goal-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>{t('agent.goals.name', 'Goal Name')}</label>
            <input
              type="text"
              value={formName}
              onChange={e => setFormName(e.target.value)}
              placeholder={t('agent.goals.namePlaceholder', 'e.g., 退休儲蓄')}
              required
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>{t('agent.goals.targetValue', 'Target Value')}</label>
              <input
                type="number"
                value={formTarget}
                onChange={e => setFormTarget(e.target.value)}
                placeholder="100000"
                min="0"
                step="0.01"
                required
              />
            </div>
            <div className="form-group">
              <label>{t('agent.goals.currentValue', 'Current Value')}</label>
              <input
                type="number"
                value={formCurrent}
                onChange={e => setFormCurrent(e.target.value)}
                placeholder="50000"
                min="0"
                step="0.01"
                required
              />
            </div>
            <div className="form-group">
              <label>{t('agent.goals.threshold', 'Threshold %')}</label>
              <input
                type="number"
                value={formThreshold}
                onChange={e => setFormThreshold(e.target.value)}
                placeholder="5"
                min="0.1"
                max="100"
                step="0.1"
              />
            </div>
          </div>
          <button type="submit" className="btn-submit-goal" disabled={submitting}>
            {submitting ? t('common.saving', 'Saving...') : t('agent.goals.save', 'Save Goal')}
          </button>
        </form>
      )}

      <div className="goals-list">
        {goals.length === 0 && !showForm && (
          <div className="no-goals">{t('agent.goals.empty', 'No goals set yet. Add your first goal!')}</div>
        )}
        {goals.map(goal => (
          <div key={goal.id} className={`goal-card ${isAtRisk(goal) ? 'at-risk' : ''}`}>
            <div className="goal-info">
              <div className="goal-name">{goal.name}</div>
              <div className="goal-values">
                {t('agent.goals.current', 'Current')}: ${goal.current_value.toLocaleString()} / {t('agent.goals.target', 'Target')}: ${goal.target_value.toLocaleString()}
              </div>
              <div className="goal-threshold">
                {t('agent.goals.thresholdLabel', 'Threshold')}: ±{goal.threshold_pct}%
              </div>
            </div>
            <div className="goal-progress-container">
              <div className="goal-progress-bar">
                <div
                  className="goal-progress-fill"
                  style={{ width: `${getProgressPct(goal)}%` }}
                />
              </div>
              <span className="goal-progress-pct">{getProgressPct(goal).toFixed(1)}%</span>
            </div>
            <button
              className="btn-delete-goal"
              onClick={() => handleDelete(goal.id)}
              title={t('common.delete', 'Delete')}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default GoalSetting
