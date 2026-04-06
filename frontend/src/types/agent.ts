// Agent State types
export type AgentState = 'IDLE' | 'MONITORING' | 'ANALYZING' | 'REBALANCING' | 'HARVESTING' | 'ERROR'

export interface AgentStateResponse {
  state: AgentState
  is_active: boolean
  started_at: string | null
  goals_count: number
  alerts_count: number
  last_event_at: string | null
}

export interface Goal {
  id: string
  name: string
  target_value: number
  current_value: number
  threshold_pct: number
  created_at: string
  updated_at: string
}

export interface GoalCreate {
  name: string
  target_value: number
  current_value: number
  threshold_pct: number
}

export interface Alert {
  id: string
  alert_type: 'PRICE' | 'ALLOCATION' | 'DIVERSIFICATION' | 'REBALANCE' | 'TAX_LOSS'
  severity: 'INFO' | 'WARNING' | 'CRITICAL'
  message: string
  acknowledged: boolean
  created_at: string
}

export interface RebalanceAction {
  id: string
  action_type: 'BUY' | 'SELL' | 'SWAP'
  symbol: string
  quantity: number | null
  amount: number | null
  reason: string
  status: 'PROPOSED' | 'APPROVED' | 'REJECTED'
  created_at: string
}

export interface TaxImpactSummary {
  estimated_savings: number
  harvested_losses: number
  wash_sale_risk: boolean
  calculated_at: string
}

export interface OpenFinanceAccount {
  id: string
  bank_code: string
  bank_name: string
  account_type: 'CHECKING' | 'SAVINGS' | 'INVESTMENT'
  account_masked: string
  connected_at: string
}

export interface OpenFinanceConnection {
  id: string
  bank_code: string
  bank_name: string
  status: 'CONNECTED' | 'PENDING' | 'ERROR' | 'DISCONNECTED'
  last_sync_at: string | null
}
