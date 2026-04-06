import { apiClient } from './api'

// ─── Types ────────────────────────────────────────────────────────────────────

export type IPOStatus = 'upcoming' | 'filing' | 'allocated' | 'listed' | 'withdrawn'
export type IPOAlertType = 'deadline' | 'allocation' | 'performance'

export interface IPORecord {
  id: string
  user_id: string
  company_name: string
  ticker: string | null
  exchange: string | null
  sector: string | null
  industry: string | null
  ipo_price_min: number | null
  ipo_price_max: number | null
  final_ipo_price: number | null
  shares_offered: number | null
  lot_size: number | null
  oversubscription_ratio: number | null
  application_deadline: string | null
  listing_date: string | null
  first_trading_date: string | null
  underwriter: string | null
  status: IPOStatus
  estimated_market_cap: number | null
  raising_amount: number | null
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface IPOCreate {
  company_name: string
  ticker?: string | null
  exchange?: string | null
  sector?: string | null
  industry?: string | null
  ipo_price_min?: number | null
  ipo_price_max?: number | null
  final_ipo_price?: number | null
  shares_offered?: number | null
  lot_size?: number | null
  oversubscription_ratio?: number | null
  application_deadline?: string | null
  listing_date?: string | null
  first_trading_date?: string | null
  underwriter?: string | null
  status?: IPOStatus
  estimated_market_cap?: number | null
  raising_amount?: number | null
  notes?: string | null
}

export interface IPOUpdate {
  company_name?: string
  ticker?: string | null
  exchange?: string | null
  sector?: string | null
  industry?: string | null
  ipo_price_min?: number | null
  ipo_price_max?: number | null
  final_ipo_price?: number | null
  shares_offered?: number | null
  lot_size?: number | null
  oversubscription_ratio?: number | null
  application_deadline?: string | null
  listing_date?: string | null
  first_trading_date?: string | null
  underwriter?: string | null
  status?: IPOStatus
  estimated_market_cap?: number | null
  raising_amount?: number | null
  notes?: string | null
  is_active?: boolean
}

export interface IPOAlert {
  id: string
  user_id: string
  ipo_id: string
  alert_type: IPOAlertType
  is_active: boolean
  triggered_at: string | null
  message: string | null
  created_at: string
}

export interface IPOAlertCreate {
  ipo_id: string
  alert_type?: IPOAlertType
  message?: string | null
}

export interface IPOAnalysis {
  ipo_id: string
  company_name: string
  valuation_range: {
    min: number | null
    max: number | null
    final: number | null
  }
  underwriter_info: { name: string | null } | null
  peer_comparison: unknown[]
  risk_factors: unknown[]
}

export interface IPOCalendar {
  ipos: IPORecord[]
  total: number
}

export interface DeadlineInfo {
  company_name: string
  deadline: string
  days_left: number
}

// ─── Service ───────────────────────────────────────────────────────────────────

export const ipoService = {
  async listIPOs(params?: {
    status?: IPOStatus
    sector?: string
    upcoming_only?: boolean
  }): Promise<IPORecord[]> {
    const response = await apiClient.get('/ipos/', { params })
    return response.data
  },

  async getIPO(id: string): Promise<IPORecord> {
    const response = await apiClient.get(`/ipos/${id}`)
    return response.data
  },

  async createIPO(data: IPOCreate): Promise<IPORecord> {
    const response = await apiClient.post('/ipos/', data)
    return response.data
  },

  async updateIPO(id: string, data: IPOUpdate): Promise<IPORecord> {
    const response = await apiClient.put(`/ipos/${id}`, data)
    return response.data
  },

  async deleteIPO(id: string): Promise<void> {
    await apiClient.delete(`/ipos/${id}`)
  },

  async getUpcomingIPOs(): Promise<IPORecord[]> {
    const response = await apiClient.get('/ipos/upcoming')
    return response.data
  },

  async getIPOAnalysis(id: string): Promise<IPOAnalysis> {
    const response = await apiClient.get(`/ipos/analysis/${id}`)
    return response.data
  },

  async getIPOPerformance(id: string): Promise<Record<string, unknown>> {
    const response = await apiClient.get(`/ipos/performance/${id}`)
    return response.data
  },

  async getCalendar(): Promise<IPOCalendar> {
    const response = await apiClient.get('/ipos/calendar')
    return response.data
  },

  async getUpcomingDeadlines(): Promise<DeadlineInfo[]> {
    const response = await apiClient.get('/ipos/deadlines')
    return response.data
  },

  async getFirstDayStats(): Promise<Record<string, unknown>> {
    const response = await apiClient.get('/ipos/stats/first-day')
    return response.data
  },

  async listAlerts(activeOnly: boolean = true): Promise<IPOAlert[]> {
    const response = await apiClient.get('/ipos/alerts', { params: { active_only: activeOnly } })
    return response.data
  },

  async createAlert(data: IPOAlertCreate): Promise<IPOAlert> {
    const response = await apiClient.post('/ipos/alerts', data)
    return response.data
  },

  async deleteAlert(id: string): Promise<void> {
    await apiClient.delete(`/ipos/alerts/${id}`)
  },
}
