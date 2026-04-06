import { apiClient } from './api'

export type AgentState = 'IDLE' | 'MONITORING' | 'ANALYZING' | 'RECOMMENDING' | 'ACTING'

export interface AgentStatus {
  state: AgentState
  last_active: string
  activity_summary: string
  active_tasks: string[]
}

export interface AgentRecommendation {
  id: string
  type: 'REBALANCE' | 'GOAL_ADJUSTMENT' | 'SALARY_DEPOSIT' | 'RISK_ALERT'
  title: string
  description: string
  priority: 'LOW' | 'MEDIUM' | 'HIGH'
  created_at: string
  status: 'PENDING' | 'ACCEPTED' | 'DISMISSED'
}

export interface MonitoringItem {
  id: string
  type: 'PORTFOLIO_DRIFT' | 'GOAL_PROGRESS' | 'SALARY_DEPOSIT'
  title: string
  status: 'OK' | 'WARNING' | 'CRITICAL'
  details: string
  updated_at: string
}

export interface DriftHolding {
  symbol: string
  name: string
  current_weight: number
  target_weight: number
  drift_pct: number
  action: 'BUY' | 'SELL' | 'HOLD'
  suggested_amount?: number
}

export interface RebalanceResult {
  triggerred: boolean
  holdings: DriftHolding[]
  summary: {
    total_drift: number
    buy_count: number
    sell_count: number
    hold_count: number
  }
}

export type GoalType = 'RETIREMENT' | 'HOUSE' | 'EDUCATION' | 'OTHER'

export interface InvestmentGoal {
  id: string
  goal_type: GoalType
  target_amount: number
  target_date: string
  current_progress: number
  status: 'ON_TRACK' | 'BEHIND' | 'AHEAD'
}

export interface OpenFinanceConnection {
  bank_code: string
  bank_name: string
  status: 'CONNECTED' | 'DISCONNECTED' | 'PENDING'
  connected_at?: string
  account_count: number
}

function getAuthHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const agentService = {
  async getAgentState(): Promise<AgentStatus | null> {
    try {
      const response = await apiClient.get('/agent/status', {
        headers: getAuthHeaders(),
      })
      return response.data
    } catch (err) {
      console.error('Failed to get agent state:', err)
      return null
    }
  },

  async getAgentRecommendations(): Promise<AgentRecommendation[]> {
    try {
      const response = await apiClient.get('/agent/recommendations', {
        headers: getAuthHeaders(),
      })
      return response.data
    } catch (err) {
      console.error('Failed to get agent recommendations:', err)
      return []
    }
  },

  async getMonitoringItems(): Promise<MonitoringItem[]> {
    try {
      const response = await apiClient.get('/agent/monitoring', {
        headers: getAuthHeaders(),
      })
      return response.data
    } catch (err) {
      console.error('Failed to get monitoring items:', err)
      return []
    }
  },

  async triggerRebalance(): Promise<RebalanceResult | null> {
    try {
      const response = await apiClient.post('/agent/rebalance', {}, {
        headers: getAuthHeaders(),
      })
      return response.data
    } catch (err) {
      console.error('Failed to trigger rebalance:', err)
      return null
    }
  },

  async setGoal(goalData: Omit<InvestmentGoal, 'id' | 'status'>): Promise<InvestmentGoal | null> {
    try {
      const response = await apiClient.post('/agent/goals', goalData, {
        headers: getAuthHeaders(),
      })
      return response.data
    } catch (err) {
      console.error('Failed to set goal:', err)
      return null
    }
  },

  async getGoals(): Promise<InvestmentGoal[]> {
    try {
      const response = await apiClient.get('/agent/goals', {
        headers: getAuthHeaders(),
      })
      return response.data
    } catch (err) {
      console.error('Failed to get goals:', err)
      return []
    }
  },

  async updateGoal(goalId: string, goalData: Partial<InvestmentGoal>): Promise<InvestmentGoal | null> {
    try {
      const response = await apiClient.put(`/agent/goals/${goalId}`, goalData, {
        headers: getAuthHeaders(),
      })
      return response.data
    } catch (err) {
      console.error('Failed to update goal:', err)
      return null
    }
  },

  async deleteGoal(goalId: string): Promise<boolean> {
    try {
      await apiClient.delete(`/agent/goals/${goalId}`, {
        headers: getAuthHeaders(),
      })
      return true
    } catch (err) {
      console.error('Failed to delete goal:', err)
      return false
    }
  },

  async connectOpenFinance(bankCode: string): Promise<OpenFinanceConnection | null> {
    try {
      const response = await apiClient.post('/agent/openfinance/connect', { bank_code: bankCode }, {
        headers: getAuthHeaders(),
      })
      return response.data
    } catch (err) {
      console.error('Failed to connect open finance:', err)
      return null
    }
  },

  async disconnectOpenFinance(bankCode: string): Promise<boolean> {
    try {
      await apiClient.delete(`/agent/openfinance/${bankCode}`, {
        headers: getAuthHeaders(),
      })
      return true
    } catch (err) {
      console.error('Failed to disconnect open finance:', err)
      return false
    }
  },

  async getOpenFinanceConnections(): Promise<OpenFinanceConnection[]> {
    try {
      const response = await apiClient.get('/agent/openfinance/connections', {
        headers: getAuthHeaders(),
      })
      return response.data
    } catch (err) {
      console.error('Failed to get open finance connections:', err)
      return []
    }
  },

  async getRebalancePreview(): Promise<RebalanceResult | null> {
    try {
      const response = await apiClient.get('/agent/rebalance/preview', {
        headers: getAuthHeaders(),
      })
      return response.data
    } catch (err) {
      console.error('Failed to get rebalance preview:', err)
      return null
    }
  },
}
