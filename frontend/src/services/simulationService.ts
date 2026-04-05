import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

export interface RetirementSimulationRequest {
  current_age: number
  retirement_age: number
  current_savings: number
  monthly_contribution: number
  desired_monthly_income: number
  portfolio_allocation: Record<string, number>
  num_simulations?: number
  years_to_simulate?: number
}

export interface RetirementSimulationResponse {
  success_probability: number
  median_outcome: number
  percentile_10: number
  percentile_25: number
  percentile_75: number
  percentile_90: number
  average_outcome: number
  worst_outcome: number
  best_outcome: number
  total_simulations: number
  years_until_retirement: number
  assumptions: Record<string, number>
}

export const simulationService = {
  async runRetirementSimulation(
    request: RetirementSimulationRequest
  ): Promise<RetirementSimulationResponse> {
    const { data } = await apiClient.post<RetirementSimulationResponse>(
      '/simulation/retirement',
      request
    )
    return data
  },
}
