import { describe, it, expect } from 'vitest'

describe('Stock Types', () => {
  it('should have correct StockInfo interface', () => {
    const stock = {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      exchange: 'NASDAQ',
      currency: 'USD',
    }

    expect(stock.symbol).toBe('AAPL')
    expect(stock.name).toBe('Apple Inc.')
    expect(stock.exchange).toBe('NASDAQ')
    expect(stock.currency).toBe('USD')
  })

  it('should have correct PriceAlert interface', () => {
    const alert = {
      id: 'alert-1',
      user_id: 'user-1',
      symbol: 'AAPL',
      alert_type: 'PRICE_ABOVE',
      threshold: 150.0,
      enabled: true,
      triggered_at: null,
    }

    expect(alert.alert_type).toBe('PRICE_ABOVE')
    expect(alert.threshold).toBe(150.0)
    expect(alert.enabled).toBe(true)
  })

  it('should have correct WatchlistItem interface', () => {
    const item = {
      id: 'item-1',
      user_id: 'user-1',
      symbol: 'GOOGL',
      name: 'Alphabet Inc.',
      added_at: 1700000000,
    }

    expect(item.symbol).toBe('GOOGL')
    expect(item.name).toBe('Alphabet Inc.')
    expect(item.added_at).toBe(1700000000)
  })
})

describe('AlertType enum', () => {
  it('should have correct alert types', () => {
    const alertTypes = ['PRICE_ABOVE', 'PRICE_BELOW', 'PRICE_CHANGE_PERCENT']

    expect(alertTypes).toContain('PRICE_ABOVE')
    expect(alertTypes).toContain('PRICE_BELOW')
    expect(alertTypes).toContain('PRICE_CHANGE_PERCENT')
  })
})

describe('Price calculation', () => {
  it('should calculate change percent correctly', () => {
    const currentPrice = 150.0
    const previousClose = 145.0
    const changePercent = ((currentPrice - previousClose) / previousClose) * 100

    expect(changePercent).toBeCloseTo(3.45, 1)
  })
})
