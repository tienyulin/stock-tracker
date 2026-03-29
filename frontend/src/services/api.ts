import axios from 'axios'
import type { StockInfo, WatchlistItem, PriceAlert, AlertType } from '../types'

const API_BASE_URL = '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

export const stockService = {
  async getStockInfo(symbol: string): Promise<StockInfo | null> {
    try {
      const response = await apiClient.get(`/stocks/${symbol}`)
      return response.data
    } catch (err) {
      console.error('Failed to get stock info:', err)
      return null
    }
  },

  async getPriceData(symbol: string): Promise<any | null> {
    try {
      const response = await apiClient.get(`/stocks/${symbol}/price`)
      return response.data
    } catch (err) {
      console.error('Failed to get price data:', err)
      return null
    }
  },
}

export const watchlistService = {
  async getWatchlist(userId: string): Promise<WatchlistItem[]> {
    const response = await apiClient.get(`/watchlist/${userId}`)
    return response.data
  },

  async addStock(userId: string, symbol: string, name: string): Promise<WatchlistItem> {
    const response = await apiClient.post(`/watchlist/${userId}/items`, {
      symbol,
      name,
    })
    return response.data
  },

  async removeStock(userId: string, symbol: string): Promise<void> {
    await apiClient.delete(`/watchlist/${userId}/items/${symbol}`)
  },
}

export const alertService = {
  async getUserAlerts(userId: string): Promise<PriceAlert[]> {
    const response = await apiClient.get(`/alerts/${userId}`)
    return response.data
  },

  async createAlert(
    userId: string,
    symbol: string,
    alertType: AlertType,
    threshold: number
  ): Promise<PriceAlert> {
    const response = await apiClient.post(`/alerts/${userId}`, {
      symbol,
      alert_type: alertType,
      threshold,
    })
    return response.data
  },

  async toggleAlert(userId: string, alertId: string, enabled: boolean): Promise<PriceAlert> {
    const response = await apiClient.patch(`/alerts/${userId}/${alertId}`, {
      enabled,
    })
    return response.data
  },

  async deleteAlert(userId: string, alertId: string): Promise<void> {
    await apiClient.delete(`/alerts/${userId}/${alertId}`)
  },
}
