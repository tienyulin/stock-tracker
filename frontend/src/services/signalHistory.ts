import { type StockSignal } from '../services/api'

const SIGNAL_HISTORY_KEY = 'stock_signal_history'
const MAX_HISTORY = 50

export interface SignalHistoryItem {
  id: string
  symbol: string
  signal: StockSignal
  timestamp: number
}

export function getSignalHistory(): SignalHistoryItem[] {
  try {
    const data = localStorage.getItem(SIGNAL_HISTORY_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

export function addToSignalHistory(symbol: string, signal: StockSignal): void {
  try {
    const history = getSignalHistory()

    // Add new entry
    const newEntry: SignalHistoryItem = {
      id: `${symbol}-${Date.now()}`,
      symbol: symbol.toUpperCase(),
      signal,
      timestamp: Date.now(),
    }

    // Add to beginning
    history.unshift(newEntry)

    // Keep only last MAX_HISTORY entries
    const trimmed = history.slice(0, MAX_HISTORY)

    localStorage.setItem(SIGNAL_HISTORY_KEY, JSON.stringify(trimmed))
  } catch (e) {
    console.error('Failed to save signal history:', e)
  }
}

export function clearSignalHistory(): void {
  try {
    localStorage.removeItem(SIGNAL_HISTORY_KEY)
  } catch (e) {
    console.error('Failed to clear signal history:', e)
  }
}

export function getSignalHistoryBySymbol(symbol: string): SignalHistoryItem[] {
  const history = getSignalHistory()
  return history.filter(item => item.symbol === symbol.toUpperCase())
}
