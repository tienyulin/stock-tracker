import { apiClient } from './api'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface EsgScore {
  id: string
  user_id: string
  ticker: string
  company_name: string
  esg_total_score: number
  environmental_score: number
  social_score: number
  governance_score: number
  carbon_footprint_tons: number | null
  water_usage_m3: number | null
  waste_tons: number | null
  data_source: string
  rating_date: string
  last_updated: string
}

export interface PortfolioEsgSummary {
  portfolio_esg_score: number
  portfolio_env_score: number
  portfolio_social_score: number
  portfolio_gov_score: number
  total_carbon_tons: number
  total_water_m3: number
  total_waste_tons: number
  holdings_count: number
  screened_count: number
  esg_rating_distribution: Record<string, number>
}

export interface ControversyAlert {
  id: string
  user_id: string
  ticker: string
  company_name: string
  controversy_type: string
  severity: string
  headline: string
  description: string | null
  source_url: string | null
  alert_date: string
  status: string
  created_at: string
}

export interface ExclusionListEntry {
  id: string
  user_id: string
  list_type: string
  sector: string | null
  ticker: string | null
  company_name: string | null
  reason: string | null
  is_active: boolean
  created_at: string
}

export interface SustainableAlternative {
  original_ticker: string
  original_esg_score: number
  alternative_ticker: string
  alternative_name: string
  alternative_esg_score: number
  sector: string
  reason: string
}

export interface PortfolioCarbon {
  total_carbon_tons: number
  carbon_by_sector: Record<string, number>
  benchmark_average_tons: number
  vs_benchmark_pct: number
  highest_carbon_ticker: string
  lowest_carbon_ticker: string
}

export interface PortfolioScreen {
  total_holdings: number
  flagged_holdings: Array<{ ticker: string; company_name: string; reason: string }>
  screened_holdings: Array<{ ticker: string; company_name: string; esg_score: number }>
  compliance_score: number
  excluded_value: number
}

export interface EsgTrend {
  month: string
  esg_total_score: number
  environmental_score: number
  social_score: number
  governance_score: number
}

// ─── Service ──────────────────────────────────────────────────────────────────

export const esgService = {
  // ESG Scores
  async getEsgScore(ticker: string): Promise<EsgScore> {
    const res = await apiClient.get<EsgScore>(`/esg/scores/${ticker}`)
    return res.data
  },

  async createEsgScore(data: Partial<EsgScore> & { ticker: string; company_name: string; esg_total_score: number }): Promise<EsgScore> {
    const res = await apiClient.post<EsgScore>('/esg/scores', data)
    return res.data
  },

  async getPortfolioSummary(): Promise<PortfolioEsgSummary> {
    const res = await apiClient.get<PortfolioEsgSummary>('/esg/scores/portfolio/summary')
    return res.data
  },

  async getEsgTrend(ticker: string, months = 12): Promise<EsgTrend[]> {
    const res = await apiClient.get<EsgTrend[]>(`/esg/scores/portfolio/trend/${ticker}?months=${months}`)
    return res.data
  },

  // Carbon Footprint
  async getPortfolioCarbon(): Promise<PortfolioCarbon> {
    const res = await apiClient.get<PortfolioCarbon>('/esg/portfolio/carbon')
    return res.data
  },

  // Controversy Alerts
  async getActiveAlerts(): Promise<ControversyAlert[]> {
    const res = await apiClient.get<ControversyAlert[]>('/esg/alerts')
    return res.data
  },

  async checkControversies(ticker: string): Promise<{ ticker: string; has_controversies: boolean; alerts: ControversyAlert[] }> {
    const res = await apiClient.get(`/esg/alerts/check/${ticker}`)
    return res.data
  },

  async dismissAlert(alertId: string): Promise<ControversyAlert> {
    const res = await apiClient.post<ControversyAlert>(`/esg/alerts/${alertId}/dismiss`)
    return res.data
  },

  // Exclusion List
  async getExclusions(listType?: string): Promise<ExclusionListEntry[]> {
    const params = listType ? { list_type: listType } : {}
    const res = await apiClient.get<ExclusionListEntry[]>('/esg/exclusions', { params })
    return res.data
  },

  async createExclusion(data: { list_type: string; ticker?: string; sector?: string; company_name?: string; reason?: string }): Promise<ExclusionListEntry> {
    const res = await apiClient.post<ExclusionListEntry>('/esg/exclusions', data)
    return res.data
  },

  async deleteExclusion(entryId: string): Promise<void> {
    await apiClient.delete(`/esg/exclusions/${entryId}`)
  },

  // Portfolio
  async getAlternatives(ticker: string): Promise<SustainableAlternative[]> {
    const res = await apiClient.get<SustainableAlternative[]>(`/esg/portfolio/alternatives/${ticker}`)
    return res.data
  },

  async screenPortfolio(): Promise<PortfolioScreen> {
    const res = await apiClient.get<PortfolioScreen>('/esg/portfolio/screen')
    return res.data
  },
}
