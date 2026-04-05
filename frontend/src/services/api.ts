import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// Helper to extract user-friendly error messages from axios errors
export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const axiosErr = err as { response?: { status?: number }, message?: string }
    if (axiosErr.response?.status === 401) return 'Unauthorized. Please login again.'
    if (axiosErr.response?.status === 403) return 'Access forbidden.'
    if (axiosErr.response?.status === 404) return 'Resource not found.'
    if (axiosErr.response?.status === 422) return 'Validation error.'
    if (axiosErr.response?.status === 500) return 'Server error. Please try again later.'
    if (axiosErr.message?.includes('timeout')) return 'Request timed out. Please try again.'
    if (axiosErr.message?.includes('Network Error')) return 'Network error. Check your connection.'
  }
  return 'An unexpected error occurred.'
}

// Stock types
export interface StockQuote {
  symbol: string
  name?: string
  price: number
  volume: number
  timestamp?: number
  market_state?: string | null
  change?: number
  change_percent?: number
}

export interface StockHistory {
  symbol: string
  timestamps: number[]
  opens: number[]
  highs: number[]
  lows: number[]
  closes: number[]
  volumes: number[]
}

// Indicator types
export interface StockIndicators {
  symbol: string
  rsi: number | null | undefined
  macd: {
    macd_line: number
    signal_line: number
    histogram: number
  } | null
  sma: Record<string, number>
  ema: Record<string, number>
  timestamp: string
}

// Signal types
export type SignalType = 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL'

export interface StockSignal {
  symbol: string
  signal: SignalType
  signal_label: string
  confidence: number
  summary: string
  bullish_factors: string[]
  bearish_factors: string[]
  indicators: Array<{
    indicator: string
    value: number
    signal: SignalType
    reasoning: string
  }>
  period: string
  interval: string
}

// AI Signal Score types (Phase 25)
export interface SignalScore {
  symbol: string
  score: number  // 1-100
  verdict: 'Buy' | 'Sell' | 'Hold'
  confidence: 'High' | 'Medium' | 'Low'
  key_drivers: string[]
  indicator_scores: Record<string, number>
  period: string
  interval: string
}

// Watchlist types
export interface WatchlistItem {
  id: string
  symbol: string
  notes?: string
  added_at: string
}

export interface Watchlist {
  id: string
  name: string
  is_default: boolean
  items: WatchlistItem[]
  created_at: string
  updated_at: string
}

// Alert types
export type AlertConditionType = 'above' | 'below' | 'change_pct'

export interface Alert {
  id: string
  symbol: string
  condition_type: AlertConditionType
  threshold: number
  is_active: boolean
  triggered_at?: string
  created_at: string
  updated_at: string
}

export const stockService = {
  async getStockQuote(symbol: string): Promise<StockQuote | null> {
    try {
      const response = await apiClient.get(`/stocks/${symbol}/quote`)
      return response.data
    } catch (err) {
      console.error('Failed to get stock quote:', err)
      return null
    }
  },

  async getStockHistory(
    symbol: string,
    period: string = '1mo',
    interval: string = '1d'
  ): Promise<StockHistory | null> {
    try {
      const response = await apiClient.get(`/stocks/${symbol}/history`, {
        params: { period, interval },
      })
      return response.data
    } catch (err) {
      console.error('Failed to get stock history:', err)
      return null
    }
  },

  async searchStocks(q: string): Promise<{ results: Array<{ symbol: string; name: string }> }> {
    try {
      const response = await apiClient.get('/stocks/search', { params: { q } })
      return response.data
    } catch (err) {
      console.error('Failed to search stocks:', err)
      return { results: [] }
    }
  },

  async getStockIndicators(
    symbol: string,
    period: string = '3mo',
    interval: string = '1d'
  ): Promise<StockIndicators | null> {
    try {
      const response = await apiClient.get(`/stocks/${symbol}/indicators`, {
        params: { period, interval },
      })
      return response.data
    } catch (err) {
      console.error('Failed to get stock indicators:', err)
      if (axios.isAxiosError(err)) {
        console.error('Axios error details:', {
          message: err.message,
          status: err.response?.status,
          statusText: err.response?.statusText,
          data: err.response?.data,
        })
      }
      return null
    }
  },

  async getStockSignal(
    symbol: string,
    period: string = '3mo',
    interval: string = '1d'
  ): Promise<StockSignal | null> {
    try {
      const response = await apiClient.get(`/stocks/${symbol}/signal`, {
        params: { period, interval },
      })
      return response.data
    } catch (err) {
      console.error('Failed to get stock signal:', err)
      if (axios.isAxiosError(err)) {
        console.error('Axios error details:', {
          message: err.message,
          status: err.response?.status,
          statusText: err.response?.statusText,
          data: err.response?.data,
        })
      }
      return null
    }
  },

  async getSignalScore(
    symbol: string,
    period: string = '3mo',
    interval: string = '1d'
  ): Promise<SignalScore | null> {
    try {
      const response = await apiClient.get(`/signals/${symbol}/score`, {
        params: { period, interval },
      })
      return response.data
    } catch (err) {
      console.error('Failed to get signal score:', err)
      if (axios.isAxiosError(err)) {
        console.error('Axios error details:', {
          message: err.message,
          status: err.response?.status,
          statusText: err.response?.statusText,
          data: err.response?.data,
        })
      }
      return null
    }
  },
}

export const watchlistService = {
  async getWatchlists(userId: string): Promise<Watchlist[]> {
    const response = await apiClient.get('/watchlists', { params: { user_id: userId } })
    return response.data
  },

  async createWatchlist(userId: string, name: string, isDefault: boolean = false): Promise<Watchlist> {
    const response = await apiClient.post('/watchlists', { name, is_default: isDefault }, {
      params: { user_id: userId },
    })
    return response.data
  },

  async updateWatchlist(
    userId: string,
    watchlistId: string,
    data: { name?: string; is_default?: boolean }
  ): Promise<Watchlist> {
    const response = await apiClient.put(`/watchlists/${watchlistId}`, data, {
      params: { user_id: userId },
    })
    return response.data
  },

  async deleteWatchlist(userId: string, watchlistId: string): Promise<void> {
    await apiClient.delete(`/watchlists/${watchlistId}`, {
      params: { user_id: userId },
    })
  },

  async addItemToWatchlist(
    userId: string,
    watchlistId: string,
    symbol: string,
    notes?: string
  ): Promise<WatchlistItem> {
    const response = await apiClient.post(
      `/watchlists/${watchlistId}/items`,
      { symbol, notes },
      { params: { user_id: userId } }
    )
    return response.data
  },

  async removeItemFromWatchlist(
    userId: string,
    watchlistId: string,
    itemId: string
  ): Promise<void> {
    await apiClient.delete(`/watchlists/${watchlistId}/items/${itemId}`, {
      params: { user_id: userId },
    })
  },
}

// User type
export interface User {
  id: string
  email: string
  username: string
  created_at?: string
}

// Auth response type
interface AuthResponse {
  access_token: string
  token_type: string
  user_id: string
}

export const alertService = {
  async getAlerts(userId: string): Promise<Alert[]> {
    const response = await apiClient.get('/alerts', { params: { user_id: userId } })
    return response.data
  },

  async createAlert(
    userId: string,
    symbol: string,
    conditionType: AlertConditionType,
    threshold: number
  ): Promise<Alert> {
    const response = await apiClient.post(
      '/alerts',
      { symbol, condition_type: conditionType, threshold },
      { params: { user_id: userId } }
    )
    return response.data
  },

  async updateAlert(
    userId: string,
    alertId: string,
    data: { is_active?: boolean; condition_type?: AlertConditionType; threshold?: number; triggered_at?: number | null }
  ): Promise<Alert> {
    const response = await apiClient.put(`/alerts/${alertId}`, data, {
      params: { user_id: userId },
    })
    return response.data
  },

  async deleteAlert(userId: string, alertId: string): Promise<void> {
    await apiClient.delete(`/alerts/${alertId}`, {
      params: { user_id: userId },
    })
  },

  async triggerAlert(userId: string, alertId: string): Promise<Alert> {
    const response = await apiClient.post(`/alerts/${alertId}/trigger`, {}, {
      params: { user_id: userId },
    })
    return response.data
  },
}

// Portfolio types
export type AssetType = 'STOCK' | 'ETF' | 'BOND' | 'REIT' | 'OTHER'
export type Currency = 'USD' | 'TWD'
export type DividendFrequency = 'QUARTERLY' | 'MONTHLY' | 'ANNUALLY' | 'NONE'

export interface Holding {
  id: string
  symbol: string
  quantity: number
  avg_cost: number
  asset_type: AssetType
  sector: string | null
  dividend_yield: number | null
  currency: Currency
  dividend_frequency: DividendFrequency
  current_price: number | null
  current_value: number | null
  gain_loss: number | null
  gain_loss_pct: number | null
  created_at: string
  updated_at: string
}

export interface PortfolioSummary {
  total_cost: number
  total_current_value: number
  total_gain_loss: number
  total_gain_loss_pct: number
  holdings_count: number
}

export interface PortfolioResponse {
  holdings: Holding[]
  summary: PortfolioSummary
}

export interface AssetAllocation {
  asset_type: AssetType
  holdings_count: number
  total_cost: number
  total_current_value: number
  allocation_pct: number | null
}

export interface SectorAllocation {
  sector: string
  holdings_count: number
  total_cost: number
  total_current_value: number
  allocation_pct: number | null
}

export interface PortfolioAllocationResponse {
  asset_allocation: AssetAllocation[]
  total_portfolio_value: number
}

export interface PortfolioSectorResponse {
  sector_allocation: SectorAllocation[]
  total_portfolio_value: number
}

export interface PortfolioHoldingSignal {
  id: string
  symbol: string
  quantity: number
  avg_cost: number
  current_price: number | null
  current_value: number | null
  gain_loss: number | null
  gain_loss_pct: number | null
}

export interface PortfolioSignal {
  signal: SignalType
  signal_label: string
  confidence: number
  summary: string
  bullish_factors: string[]
  bearish_factors: string[]
  indicators: Array<{
    indicator: string
    value: number
    signal: SignalType
    reasoning: string
  }>
}

export interface HoldingWithSignal {
  holding: PortfolioHoldingSignal
  signal: PortfolioSignal
  is_conflict: boolean
}

export interface PortfolioSignalsResponse {
  holdings: HoldingWithSignal[]
  conflicts: HoldingWithSignal[]
  total_holdings: number
  total_conflicts: number
}

function getAuthHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const portfolioService = {
  async getPortfolio(params?: { asset_type?: string; sector?: string }): Promise<PortfolioResponse> {
    const response = await apiClient.get('/portfolio', {
      headers: getAuthHeaders(),
      params,
    })
    return response.data
  },

  async addHolding(data: {
    symbol: string
    quantity: number
    avg_cost: number
    asset_type?: AssetType
    sector?: string | null
    dividend_yield?: number | null
    currency?: Currency
    dividend_frequency?: DividendFrequency
  }): Promise<Holding> {
    const response = await apiClient.post(
      '/portfolio/holdings',
      data,
      { headers: getAuthHeaders() }
    )
    return response.data
  },

  async updateHolding(holdingId: string, data: {
    quantity?: number
    avg_cost?: number
    asset_type?: AssetType
    sector?: string | null
    dividend_yield?: number | null
    currency?: Currency
    dividend_frequency?: DividendFrequency
  }): Promise<Holding> {
    const response = await apiClient.put(
      `/portfolio/holdings/${holdingId}`,
      data,
      { headers: getAuthHeaders() }
    )
    return response.data
  },

  async deleteHolding(holdingId: string): Promise<void> {
    await apiClient.delete(`/portfolio/holdings/${holdingId}`, {
      headers: getAuthHeaders(),
    })
  },

  async getAllocationByAssetType(): Promise<PortfolioAllocationResponse> {
    const response = await apiClient.get('/portfolio/summary/by-asset-type', {
      headers: getAuthHeaders(),
    })
    return response.data
  },

  async getAllocationBySector(): Promise<PortfolioSectorResponse> {
    const response = await apiClient.get('/portfolio/summary/by-sector', {
      headers: getAuthHeaders(),
    })
    return response.data
  },

  async getPortfolioSignals(): Promise<PortfolioSignalsResponse> {
    const response = await apiClient.get('/portfolio/signals', {
      headers: getAuthHeaders(),
    })
    return response.data
  },

  async downloadPortfolioPdf(): Promise<Blob> {
    const response = await apiClient.get('/portfolio/report/pdf', {
      headers: getAuthHeaders(),
      responseType: 'blob',
    })
    return response.data
  },
}

export const authService = {
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/login', { email, password })
    return response.data
  },

  async signup(email: string, username: string, password: string): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/signup', { email, username, password })
    return response.data
  },

  async getCurrentUser(token: string): Promise<User> {
    const response = await apiClient.get('/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
    return response.data
  },

  logout(): void {
    // Call logout endpoint and clear cookies
    apiClient.post('/auth/logout').catch(console.error)
  },

  async getLineTokenStatus(): Promise<{ line_notify_connected: boolean }> {
    const response = await apiClient.get('/users/me/line-token')
    return response.data
  },

  async updateLineToken(token: string): Promise<{ line_notify_connected: boolean }> {
    const response = await apiClient.put('/users/me/line-token', { line_notify_token: token })
    return response.data
  },

  async deleteLineToken(): Promise<{ line_notify_connected: boolean }> {
    const response = await apiClient.delete('/users/me/line-token')
    return response.data
  },

  async testLineToken(token: string): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/users/me/line-token/test', { line_notify_token: token })
    return response.data
  },
}
