import axios from './api'

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
    const { data } = await axios.post<RetirementSimulationResponse>(
      '/simulation/retirement',
      request
    )
    return data
  },
}
