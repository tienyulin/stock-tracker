import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// Stock types
export interface StockQuote {
  symbol: string
  price: number
  volume: number
  timestamp?: number
  market_state?: string
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
  rsi: number | null
  macd: {
    macd_line: number
    signal_line: number
    histogram: number
  } | null
  sma: Record<string, number>
  ema: Record<string, number>
  timestamp: string
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
