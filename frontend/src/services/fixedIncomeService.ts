import { apiClient } from './api'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface Bond {
  id: string
  name: string
  bond_type: string
  ticker: string | null
  face_value: number
  coupon_rate: number
  purchase_price: number
  current_market_value: number | null
  purchase_date: string
  maturity_date: string
  credit_rating: string | null
  unrealized_pnl: number | null
  currency: string
  notes: string | null
}

export interface BondAnalytics {
  bond_id: string
  name: string
  ytm: number
  current_yield: number
  years_to_maturity: number
  macauley_duration: number
  modified_duration: number
  price_change_100bps: number
  price_change_minus_100bps: number
  annual_coupon: number
}

export interface BondSummary {
  total_bonds: number
  total_face_value: number
  total_market_value: number
  total_unrealized_pnl: number
  by_type: Record<string, { count: number; face_value: number; market_value: number }>
}

export interface TermDeposit {
  id: string
  name: string
  bank_name: string
  principal: number
  interest_rate: number
  term_months: number
  start_date: string
  maturity_date: string
  compound_frequency: string
  accrued_interest: number | null
  maturity_value: number | null
  auto_renew: boolean
  notes: string | null
}

export interface MaturityAlert {
  id: string
  name: string
  bank_name: string
  principal: number
  maturity_value: number
  maturity_date: string
  days_until_maturity: number
  auto_renew: boolean
}

export interface TermDepositSummary {
  total_deposits: number
  total_principal: number
  total_maturity_value: number
  total_accrued_interest: number
}

export interface FixedIncomeSummary {
  bonds: BondSummary
  term_deposits: TermDepositSummary
}

// ─── Service ────────────────────────────────────────────────────────────────────

const PATH = '/fixed-income'

export const fixedIncomeService = {
  // Bonds
  async listBonds(): Promise<Bond[]> {
    const res = await apiClient.get(`${PATH}/bonds`)
    return res.data
  },

  async getBond(id: string): Promise<Bond> {
    const res = await apiClient.get(`${PATH}/bonds/${id}`)
    return res.data
  },

  async createBond(data: Omit<Bond, 'id' | 'unrealized_pnl'>): Promise<Bond> {
    const res = await apiClient.post(`${PATH}/bonds`, data)
    return res.data
  },

  async updateBond(id: string, data: Partial<Bond>): Promise<Bond> {
    const res = await apiClient.put(`${PATH}/bonds/${id}`, data)
    return res.data
  },

  async deleteBond(id: string): Promise<void> {
    await apiClient.delete(`${PATH}/bonds/${id}`)
  },

  async getBondAnalytics(id: string): Promise<BondAnalytics> {
    const res = await apiClient.get(`${PATH}/bonds/${id}/analytics`)
    return res.data
  },

  async getBondSummary(): Promise<BondSummary> {
    const res = await apiClient.get(`${PATH}/bonds/summary`)
    return res.data
  },

  // Term Deposits
  async listTermDeposits(): Promise<TermDeposit[]> {
    const res = await apiClient.get(`${PATH}/term-deposits`)
    return res.data
  },

  async getTermDeposit(id: string): Promise<TermDeposit> {
    const res = await apiClient.get(`${PATH}/term-deposits/${id}`)
    return res.data
  },

  async createTermDeposit(
    data: Omit<TermDeposit, 'id' | 'accrued_interest' | 'maturity_value'>
  ): Promise<TermDeposit> {
    const res = await apiClient.post(`${PATH}/term-deposits`, data)
    return res.data
  },

  async updateTermDeposit(id: string, data: Partial<TermDeposit>): Promise<TermDeposit> {
    const res = await apiClient.put(`${PATH}/term-deposits/${id}`, data)
    return res.data
  },

  async deleteTermDeposit(id: string): Promise<void> {
    await apiClient.delete(`${PATH}/term-deposits/${id}`)
  },

  async getMaturityAlerts(daysAhead = 90): Promise<MaturityAlert[]> {
    const res = await apiClient.get(`${PATH}/term-deposits/maturity-alerts`, {
      params: { days_ahead: daysAhead },
    })
    return res.data
  },

  async getTermDepositSummary(): Promise<TermDepositSummary> {
    const res = await apiClient.get(`${PATH}/term-deposits/summary`)
    return res.data
  },

  // Summary
  async getSummary(): Promise<FixedIncomeSummary> {
    const [bonds, term_deposits] = await Promise.all([
      this.getBondSummary(),
      this.getTermDepositSummary(),
    ])
    return { bonds, term_deposits }
  },
}
