import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { agentService, type InvestmentGoal, type GoalType } from '../services/agentApi'
import './GoalSettingPanel.css'

interface GoalSettingPanelProps {
  onGoalChange?: (goals: InvestmentGoal[]) => void
}

const GOAL_TYPES: { value: GoalType; label: string }[] = [
  { value: 'RETIREMENT', label: 'Retirement' },
  { value: 'HOUSE', label: 'House Purchase' },
  { value: 'EDUCATION', label: 'Education' },
  { value: 'OTHER', label: 'Other' },
]

const STATUS_COLORS: Record<string, string> = {
  ON_TRACK: '#22c55e',
  BEHIND: '#ef4444',
  AHEAD: '#3b82f6',
}

export function GoalSettingPanel({ onGoalChange }: GoalSettingPanelProps) {
  const { t } = useTranslation()
  const [goals, setGoals] = useState<InvestmentGoal[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingGoal, setEditingGoal] = useState<InvestmentGoal | null>(null)
  const [formData, setFormData] = useState({
    goal_type: 'RETIREMENT' as GoalType,
    target_amount: '',
    target_date: '',
    current_progress: '',
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadGoals()
  }, [])

  const loadGoals = async () => {
    try {
      const result = await agentService.getGoals()
      setGoals(result)
      onGoalChange?.(result)
    } catch (err) {
      console.error('Failed to load goals:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)

    try {
      const goalData = {
        goal_type: formData.goal_type,
        target_amount: parseFloat(formData.target_amount),
        target_date: formData.target_date,
        current_progress: parseFloat(formData.current_progress || '0'),
      }

      if (editingGoal) {
        await agentService.updateGoal(editingGoal.id, goalData)
      } else {
        await agentService.setGoal(goalData)
      }

      await loadGoals()
      resetForm()
    } catch (err) {
      console.error('Failed to save goal:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleEdit = (goal: InvestmentGoal) => {
    setEditingGoal(goal)
    setFormData({
      goal_type: goal.goal_type,
      target_amount: goal.target_amount.toString(),
      target_date: goal.target_date.split('T')[0],
      current_progress: goal.current_progress.toString(),
    })
    setShowForm(true)
  }

  const handleDelete = async (goalId: string) => {
    if (!confirm('Are you sure you want to delete this goal?')) return

    try {
      await agentService.deleteGoal(goalId)
      await loadGoals()
    } catch (err) {
      console.error('Failed to delete goal:', err)
    }
  }

  const resetForm = () => {
    setShowForm(false)
    setEditingGoal(null)
    setFormData({
      goal_type: 'RETIREMENT',
      target_amount: '',
      target_date: '',
      current_progress: '',
    })
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(amount)
  }

  const calculateProgress = (goal: InvestmentGoal) => {
    const progress = (goal.current_progress / goal.target_amount) * 100
    return Math.min(progress, 100)
  }

  if (loading) {
    return (
      <div className="goal-panel goal-panel-loading">
        <span>{t('common.loading', 'Loading...')}</span>
      </div>
    )
  }

  return (
    <div className="goal-panel">
      <div className="goal-panel-header">
        <h3>{t('agent.goals.title', 'Investment Goals')}</h3>
        <button
          className="goal-add-btn"
          onClick={() => setShowForm(true)}
        >
          + {t('agent.goals.add', 'Add Goal')}
        </button>
      </div>

      {showForm && (
        <form className="goal-form" onSubmit={handleSubmit}>
          <div className="goal-form-field">
            <label>{t('agent.goals.goalType', 'Goal Type')}</label>
            <select
              value={formData.goal_type}
              onChange={(e) => setFormData({ ...formData, goal_type: e.target.value as GoalType })}
              required
            >
              {GOAL_TYPES.map((gt) => (
                <option key={gt.value} value={gt.value}>
                  {t(`agent.goals.types.${gt.value}`, gt.label)}
                </option>
              ))}
            </select>
          </div>

          <div className="goal-form-field">
            <label>{t('agent.goals.targetAmount', 'Target Amount')}</label>
            <input
              type="number"
              min="0"
              step="1000"
              value={formData.target_amount}
              onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
              placeholder="100000"
              required
            />
          </div>

          <div className="goal-form-field">
            <label>{t('agent.goals.targetDate', 'Target Date')}</label>
            <input
              type="date"
              value={formData.target_date}
              onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
              required
            />
          </div>

          <div className="goal-form-field">
            <label>{t('agent.goals.currentProgress', 'Current Progress')}</label>
            <input
              type="number"
              min="0"
              step="1000"
              value={formData.current_progress}
              onChange={(e) => setFormData({ ...formData, current_progress: e.target.value })}
              placeholder="0"
            />
          </div>

          <div className="goal-form-actions">
            <button type="button" className="goal-cancel-btn" onClick={resetForm}>
              {t('common.cancel', 'Cancel')}
            </button>
            <button type="submit" className="goal-save-btn" disabled={saving}>
              {saving ? t('common.loading', 'Saving...') : t('common.save', 'Save')}
            </button>
          </div>
        </form>
      )}

      <div className="goal-list">
        {goals.length === 0 && !showForm ? (
          <div className="goal-empty">
            {t('agent.goals.empty', 'No goals set. Add your first investment goal.')}
          </div>
        ) : (
          goals.map((goal) => (
            <div key={goal.id} className="goal-item">
              <div className="goal-item-header">
                <span className="goal-type-badge">
                  {t(`agent.goals.types.${goal.goal_type}`, goal.goal_type)}
                </span>
                <span
                  className="goal-status-badge"
                  style={{ backgroundColor: STATUS_COLORS[goal.status] }}
                >
                  {t(`agent.goals.status.${goal.status}`, goal.status)}
                </span>
              </div>

              <div className="goal-progress-section">
                <div className="goal-amounts">
                  <span className="goal-current">{formatCurrency(goal.current_progress)}</span>
                  <span className="goal-separator">/</span>
                  <span className="goal-target">{formatCurrency(goal.target_amount)}</span>
                </div>
                <div className="goal-progress-bar">
                  <div
                    className="goal-progress-fill"
                    style={{ width: `${calculateProgress(goal)}%` }}
                  />
                </div>
                <span className="goal-progress-pct">
                  {calculateProgress(goal).toFixed(1)}%
                </span>
              </div>

              <div className="goal-item-footer">
                <span className="goal-target-date">
                  {t('agent.goals.targetDate', 'Target')}: {new Date(goal.target_date).toLocaleDateString()}
                </span>
                <div className="goal-actions">
                  <button className="goal-edit-btn" onClick={() => handleEdit(goal)}>
                    {t('common.edit', 'Edit')}
                  </button>
                  <button className="goal-delete-btn" onClick={() => handleDelete(goal.id)}>
                    {t('common.delete', 'Delete')}
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
