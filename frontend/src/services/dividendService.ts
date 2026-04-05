import axios from 'axios'

export interface DividendPayment {
  id: string
  symbol: string
  ex_dividend_date: string
  payment_date: string
  amount_per_share: number
  shares_owned: number
  total_amount: number
  currency: string
}

export interface DividendHolding {
  symbol: string
  shares_owned: number
  cost_basis: number
  annual_dividend: number
  yield_on_cost: number
  dividend_growth_rate: number
}

export interface DividendDashboard {
  total_dividends_received: number
  dividends_this_year: number
  dividends_last_year: number
  year_over_year_growth: number
  portfolio_dividend_yield: number
  yield_on_cost: number
  recent_payments: DividendPayment[]
  upcoming_ex_dividends: DividendCalendarEntry[]
}

export interface DividendCalendarEntry {
  symbol: string
  ex_dividend_date: string
  payment_date: string
  amount_per_share: number
}

export interface DividendGrowth {
  symbol: string
  annual_dividend: number
  previous_annual_dividend: number
  dividend_growth_rate: number
  yield_on_cost: number
  current_yield: number
  years_of_growth: number
}

const getAuthHeader = () => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const dividendService = {
  // Dividend Payments
  async getPayments(params?: { symbol?: string; start_date?: string; end_date?: string; limit?: number }): Promise<DividendPayment[]> {
    const response = await axios.get('/api/v1/dividends/payments', {
      headers: getAuthHeader(),
      params,
    })
    return response.data
  },

  async createPayment(payment: {
    symbol: string
    ex_dividend_date: string
    payment_date: string
    amount_per_share: number
    shares_owned: number
    total_amount?: number
    currency?: string
  }): Promise<DividendPayment> {
    const response = await axios.post('/api/v1/dividends/payments', payment, {
      headers: getAuthHeader(),
    })
    return response.data
  },

  async deletePayment(paymentId: string): Promise<void> {
    await axios.delete(`/api/v1/dividends/payments/${paymentId}`, {
      headers: getAuthHeader(),
    })
  },

  // Dividend Holdings
  async getHoldings(params?: { symbol?: string }): Promise<DividendHolding[]> {
    const response = await axios.get('/api/v1/dividends/holdings', {
      headers: getAuthHeader(),
      params,
    })
    return response.data
  },

  async updateHolding(symbol: string, update: Partial<DividendHolding>): Promise<DividendHolding> {
    const response = await axios.put(`/api/v1/dividends/holdings/${symbol}`, update, {
      headers: getAuthHeader(),
    })
    return response.data
  },

  async deleteHolding(symbol: string): Promise<void> {
    await axios.delete(`/api/v1/dividends/holdings/${symbol}`, {
      headers: getAuthHeader(),
    })
  },

  // Dashboard
  async getDashboard(): Promise<DividendDashboard> {
    const response = await axios.get('/api/v1/dividends/dashboard', {
      headers: getAuthHeader(),
    })
    return response.data
  },

  // Growth Analytics
  async getGrowth(symbol: string): Promise<DividendGrowth> {
    const response = await axios.get(`/api/v1/dividends/growth/${symbol}`, {
      headers: getAuthHeader(),
    })
    return response.data
  },

  // Calendar
  async getCalendar(daysAhead: number = 30): Promise<DividendCalendarEntry[]> {
    const response = await axios.get('/api/v1/dividends/calendar', {
      headers: getAuthHeader(),
      params: { days_ahead: daysAhead },
    })
    return response.data
  },

  async addCalendarEntry(entry: DividendCalendarEntry): Promise<DividendCalendarEntry> {
    const response = await axios.post('/api/v1/dividends/calendar', entry, {
      headers: getAuthHeader(),
    })
    return response.data
  },

  async deleteCalendarEntry(entryId: string): Promise<void> {
    await axios.delete(`/api/v1/dividends/calendar/${entryId}`, {
      headers: getAuthHeader(),
    })
  },
}
