import { apiClient } from './api'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface CommodityPosition {
  id: string
  user_id: string
  name: string
  commodity_type: string
  ticker: string | null
  quantity: number
  unit: string
  purchase_price: number
  current_price: number | null
  market_value: number | null
  unrealized_pnl: number | null
  purchase_date: string
  currency: string
  notes: string | null
  created_at: string
  updated_at: string
}

export interface FuturesContract {
  id: string
  user_id: string
  name: string
  commodity_type: string
  ticker: string | null
  contract_size: number
  contract_month: string
  expiration_date: string
  position_type: string
  entry_price: number
  current_price: number | null
  market_value: number | null
  margin_required: number | null
  realized_pnl: number | null
  unrealized_pnl: number | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface CommoditySummary {
  total_positions: number
  total_market_value: number
  total_unrealized_pnl: number
  by_type: Record<string, { count: number; market_value: number; unrealized_pnl: number }>
}

export interface FuturesSummary {
  total_contracts: number
  total_market_value: number
  total_unrealized_pnl: number
  total_margin_required: number
}

export interface ExpirationAlert {
  id: string
  name: string
  commodity_type: string
  contract_month: string
  expiration_date: string
  days_until_expiration: number
  position_type: string
  entry_price: number
  current_price: number | null
  unrealized_pnl: number | null
}

export interface PreciousMetalsPrices {
  gold: number | null
  silver: number | null
  platinum: number | null
}

export interface InflationHedgeMetrics {
  gold_price: number | null
  dxy_index: number | null
  tips_price: number | null
  gold_change_1m_pct: number | null
  gold_change_1y_pct: number | null
  inflation_hedge_signal: string
}

export interface SyncResult {
  updated: { id: string; name: string; current_price: number }[]
  errors: { id: string; name: string; error: string }[]
}

// ─── Position CRUD ────────────────────────────────────────────────────────────

export const commodityService = {
  async listPositions(): Promise<CommodityPosition[]> {
    const res = await apiClient.get<CommodityPosition[]>('/commodities/positions')
    return res.data
  },

  async getPosition(id: string): Promise<CommodityPosition> {
    const res = await apiClient.get<CommodityPosition>(`/commodities/positions/${id}`)
    return res.data
  },

  async createPosition(data: Partial<CommodityPosition>): Promise<CommodityPosition> {
    const res = await apiClient.post<CommodityPosition>('/commodities/positions', data)
    return res.data
  },

  async updatePosition(id: string, data: Partial<CommodityPosition>): Promise<CommodityPosition> {
    const res = await apiClient.put<CommodityPosition>(`/commodities/positions/${id}`, data)
    return res.data
  },

  async deletePosition(id: string): Promise<void> {
    await apiClient.delete(`/commodities/positions/${id}`)
  },

  async getSummary(): Promise<CommoditySummary> {
    const res = await apiClient.get<CommoditySummary>('/commodities/positions/summary')
    return res.data
  },

  async syncPrices(): Promise<SyncResult> {
    const res = await apiClient.get<SyncResult>('/commodities/positions/sync-prices')
    return res.data
  },
}

// ─── Futures CRUD ──────────────────────────────────────────────────────────────

export const futuresService = {
  async listContracts(): Promise<FuturesContract[]> {
    const res = await apiClient.get<FuturesContract[]>('/commodities/futures')
    return res.data
  },

  async getContract(id: string): Promise<FuturesContract> {
    const res = await apiClient.get<FuturesContract>(`/commodities/futures/${id}`)
    return res.data
  },

  async createContract(data: Partial<FuturesContract>): Promise<FuturesContract> {
    const res = await apiClient.post<FuturesContract>('/commodities/futures', data)
    return res.data
  },

  async updateContract(id: string, data: Partial<FuturesContract>): Promise<FuturesContract> {
    const res = await apiClient.put<FuturesContract>(`/commodities/futures/${id}`, data)
    return res.data
  },

  async deleteContract(id: string): Promise<void> {
    await apiClient.delete(`/commodities/futures/${id}`)
  },

  async getSummary(): Promise<FuturesSummary> {
    const res = await apiClient.get<FuturesSummary>('/commodities/futures/summary')
    return res.data
  },

  async getExpirationAlerts(): Promise<ExpirationAlert[]> {
    const res = await apiClient.get<ExpirationAlert[]>('/commodities/futures/expiration-alerts')
    return res.data
  },
}

// ─── Precious Metals ───────────────────────────────────────────────────────────

export const preciousMetalsService = {
  async getPrices(): Promise<PreciousMetalsPrices> {
    const res = await apiClient.get<PreciousMetalsPrices>('/commodities/precious-metals/prices')
    return res.data
  },

  async getHistory(metal: string, days = 365): Promise<{ metal: string; data: { date: string; close: number }[] }> {
    const res = await apiClient.get(`/commodities/precious-metals/history?metal=${metal}&days=${days}`)
    return res.data
  },

  async getInflationHedgeMetrics(): Promise<InflationHedgeMetrics> {
    const res = await apiClient.get<InflationHedgeMetrics>('/commodities/precious-metals/inflation-hedge')
    return res.data
  },
}
