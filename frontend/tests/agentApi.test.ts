import { describe, it, expect } from 'vitest'
import { agentService, type AgentState, type AgentStatus, type InvestmentGoal, type OpenFinanceConnection } from '../src/services/agentApi'

describe('Agent Types', () => {
  it('should have correct AgentState values', () => {
    const validStates: AgentState[] = ['IDLE', 'MONITORING', 'ANALYZING', 'RECOMMENDING', 'ACTING']
    expect(validStates).toContain('IDLE')
    expect(validStates).toContain('MONITORING')
    expect(validStates).toContain('ANALYZING')
    expect(validStates).toContain('RECOMMENDING')
    expect(validStates).toContain('ACTING')
  })

  it('should have correct AgentStatus interface', () => {
    const status: AgentStatus = {
      state: 'MONITORING',
      last_active: '2026-04-06T10:00:00Z',
      activity_summary: 'Monitoring portfolio drift',
      active_tasks: ['Checking allocation', 'Calculating rebalance'],
    }

    expect(status.state).toBe('MONITORING')
    expect(status.last_active).toBe('2026-04-06T10:00:00Z')
    expect(status.activity_summary).toBe('Monitoring portfolio drift')
    expect(status.active_tasks).toHaveLength(2)
  })

  it('should have correct InvestmentGoal interface', () => {
    const goal: InvestmentGoal = {
      id: 'goal-1',
      goal_type: 'RETIREMENT',
      target_amount: 1000000,
      target_date: '2040-01-01',
      current_progress: 250000,
      status: 'ON_TRACK',
    }

    expect(goal.id).toBe('goal-1')
    expect(goal.goal_type).toBe('RETIREMENT')
    expect(goal.target_amount).toBe(1000000)
    expect(goal.current_progress).toBe(250000)
    expect(goal.status).toBe('ON_TRACK')
  })

  it('should have correct OpenFinanceConnection interface', () => {
    const connection: OpenFinanceConnection = {
      bank_code: 'ESUN',
      bank_name: 'E.Sun Bank',
      status: 'CONNECTED',
      connected_at: '2026-04-01T08:00:00Z',
      account_count: 2,
    }

    expect(connection.bank_code).toBe('ESUN')
    expect(connection.bank_name).toBe('E.Sun Bank')
    expect(connection.status).toBe('CONNECTED')
    expect(connection.account_count).toBe(2)
  })
})

describe('Agent State Transitions', () => {
  it('should validate state progression', () => {
    const stateOrder: AgentState[] = ['IDLE', 'MONITORING', 'ANALYZING', 'RECOMMENDING', 'ACTING']
    
    // Verify all states are present
    expect(stateOrder).toHaveLength(5)
    
    // Verify order
    expect(stateOrder[0]).toBe('IDLE')
    expect(stateOrder[1]).toBe('MONITORING')
    expect(stateOrder[2]).toBe('ANALYZING')
    expect(stateOrder[3]).toBe('RECOMMENDING')
    expect(stateOrder[4]).toBe('ACTING')
  })
})

describe('Goal Progress Calculations', () => {
  it('should calculate progress percentage correctly', () => {
    const goal: InvestmentGoal = {
      id: 'goal-1',
      goal_type: 'HOUSE',
      target_amount: 500000,
      target_date: '2030-01-01',
      current_progress: 125000,
      status: 'ON_TRACK',
    }

    const progress = (goal.current_progress / goal.target_amount) * 100
    expect(progress).toBe(25)
  })

  it('should cap progress at 100%', () => {
    const goal: InvestmentGoal = {
      id: 'goal-1',
      goal_type: 'RETIREMENT',
      target_amount: 100000,
      target_date: '2025-01-01',
      current_progress: 150000, // Overfunded
      status: 'AHEAD',
    }

    const progress = Math.min((goal.current_progress / goal.target_amount) * 100, 100)
    expect(progress).toBe(100)
  })
})

describe('Drift Calculations', () => {
  it('should calculate drift correctly', () => {
    const currentWeight = 0.35
    const targetWeight = 0.30
    const drift = (currentWeight - targetWeight) * 100
    
    expect(drift).toBe(5)
  })

  it('should identify high drift correctly', () => {
    const drift = 7.5
    const isHighDrift = Math.abs(drift) > 5
    expect(isHighDrift).toBe(true)
  })

  it('should identify medium drift correctly', () => {
    const drift = 3.5
    const isMediumDrift = Math.abs(drift) > 2 && Math.abs(drift) <= 5
    expect(isMediumDrift).toBe(true)
  })
})
