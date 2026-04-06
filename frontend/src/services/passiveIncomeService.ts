import axios from 'axios'

export interface PassiveIncomeSource {
  id: string
  name: string
  source_type: 'dividend' | 'rental' | 'interest' | 'royalty' | 'pension' | 'social_security' | 'p2p' | 'other'
  description: string | null
  currency: string
  expected_monthly_income: number
  expected_annual_income: number
  yield_on_cost: number | null
  is_active: boolean
  start_date: string | null
  end_date: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface PassiveIncomeRecord {
  id: string
  source_id: string
  amount: number
  currency: string
  record_date: string
  record_type: 'received' | 'expected' | 'missed'
  notes: string | null
  created_at: string
}

export interface PassiveIncomeMonthlySummary {
  total: number
  by_type: Record<string, number>
  currency: string
}

export interface PassiveIncomeAnnualSummary {
  year: number
  monthly: number[]
  total: number
  currency: string
}

export interface FireGoal {
  id: string
  target_annual_income: number
  monthly_expenses: number
  target_date: string | null
  current_passive_income: number
  progress_percentage: number
  currency: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface FireProgress {
  target_annual_income: number
  current_passive_income: number
  progress_percentage: number
  monthly_expenses: number
  monthly_target: number
  months_to_target: number
  target_date: string | null
  currency: string
}

export interface PassiveIncomeDashboard {
  sources: PassiveIncomeSource[]
  monthly_summary: PassiveIncomeMonthlySummary
  annual_summary: PassiveIncomeAnnualSummary
  fire_progress: FireProgress | null
}

const getAuthHeader = () => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

const API = '/api/v1/passive-income'

export const passiveIncomeService = {
  // Dashboard
  async getDashboard(year?: number, month?: number): Promise<PassiveIncomeDashboard> {
    const params: Record<string, number> = {}
    if (year) params.year = year
    if (month) params.month = month
    const response = await axios.get(`${API}/dashboard`, {
      headers: getAuthHeader(),
      params,
    })
    return response.data
  },

  // Sources
  async getSources(activeOnly = true): Promise<PassiveIncomeSource[]> {
    const response = await axios.get(`${API}/sources`, {
      headers: getAuthHeader(),
      params: { active_only: activeOnly },
    })
    return response.data
  },

  async createSource(data: {
    name: string
    source_type: PassiveIncomeSource['source_type']
    description?: string
    currency?: string
    expected_monthly_income?: number
    expected_annual_income?: number
    yield_on_cost?: number
    start_date?: string
    notes?: string
  }): Promise<PassiveIncomeSource> {
    const response = await axios.post(`${API}/sources`, data, {
      headers: getAuthHeader(),
    })
    return response.data
  },

  async updateSource(
    id: string,
    data: Partial<{
      name: string
      source_type: string
      description: string
      currency: string
      expected_monthly_income: number
      expected_annual_income: number
      yield_on_cost: number
      is_active: boolean
      notes: string
    }>
  ): Promise<PassiveIncomeSource> {
    const response = await axios.patch(`${API}/sources/${id}`, data, {
      headers: getAuthHeader(),
    })
    return response.data
  },

  async deleteSource(id: string): Promise<void> {
    await axios.delete(`${API}/sources/${id}`, {
      headers: getAuthHeader(),
    })
  },

  // Records
  async getRecords(params?: {
    source_id?: string
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<PassiveIncomeRecord[]> {
    const response = await axios.get(`${API}/records`, {
      headers: getAuthHeader(),
      params,
    })
    return response.data
  },

  async addRecord(data: {
    source_id: string
    amount: number
    record_date: string
    currency?: string
    record_type?: 'received' | 'expected' | 'missed'
    notes?: string
  }): Promise<PassiveIncomeRecord> {
    const response = await axios.post(`${API}/records`, data, {
      headers: getAuthHeader(),
    })
    return response.data
  },

  // FIRE
  async getFireProgress(): Promise<FireProgress> {
    const response = await axios.get(`${API}/fire`, {
      headers: getAuthHeader(),
    })
    return response.data
  },

  async upsertFireGoal(data: {
    target_annual_income: number
    monthly_expenses: number
    target_date?: string
    currency?: string
  }): Promise<FireGoal> {
    const response = await axios.post(`${API}/fire`, data, {
      headers: getAuthHeader(),
    })
    return response.data
  },

  // Summaries
  async getMonthlySummary(year: number, month: number): Promise<PassiveIncomeMonthlySummary> {
    const response = await axios.get(`${API}/summary/monthly`, {
      headers: getAuthHeader(),
      params: { year, month },
    })
    return response.data
  },

  async getAnnualSummary(year: number): Promise<PassiveIncomeAnnualSummary> {
    const response = await axios.get(`${API}/summary/annual`, {
      headers: getAuthHeader(),
      params: { year },
    })
    return response.data
  },
}
