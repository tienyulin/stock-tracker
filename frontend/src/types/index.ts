export interface StockInfo {
  symbol: string
  name: string
  exchange: string
  currency: string
}

export interface PriceData {
  symbol: string
  current_price: number
  open_price: number
  high_price: number
  low_price: number
  previous_close: number
  volume: number
  change_percent: number
}

export interface WatchlistItem {
  id: string
  user_id: string
  symbol: string
  name: string
  added_at: number
}

export type AlertType = 'PRICE_ABOVE' | 'PRICE_BELOW' | 'PRICE_CHANGE_PERCENT'

export interface PriceAlert {
  id: string
  user_id: string
  symbol: string
  alert_type: AlertType
  threshold: number
  enabled: boolean
  triggered_at: number | null
}
