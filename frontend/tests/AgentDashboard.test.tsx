import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { I18nextProvider } from 'react-i18next'
import i18n from 'i18next'
import { AgentStatusCard } from '../src/components/AgentStatusCard'
import { GoalSettingPanel } from '../src/components/GoalSettingPanel'
import { OpenFinanceConnect } from '../src/components/OpenFinanceConnect'
import { RebalanceActionCard } from '../src/components/RebalanceActionCard'

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'en' },
  }),
  I18nextProvider: ({ children }: { children: React.ReactNode }) => children,
}))

// Mock agentApi
vi.mock('../src/services/agentApi', () => ({
  agentService: {
    getAgentState: vi.fn(),
    getGoals: vi.fn(),
    getOpenFinanceConnections: vi.fn(),
    getRebalancePreview: vi.fn(),
  },
  type AgentState: 'IDLE' | 'MONITORING' | 'ANALYZING' | 'RECOMMENDING' | 'ACTING',
  type AgentStatus: any,
  type InvestmentGoal: any,
  type OpenFinanceConnection: any,
  type RebalanceResult: any,
}))

describe('AgentStatusCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render loading state initially', () => {
    const { agentService } = require('../src/services/agentApi')
    agentService.getAgentState.mockImplementation(() => new Promise(() => {}))

    render(<AgentStatusCard />)
    expect(screen.getByText('agent.loading')).toBeTruthy()
  })

  it('should render error state when API fails', async () => {
    const { agentService } = require('../src/services/agentApi')
    agentService.getAgentState.mockResolvedValue(null)

    render(<AgentStatusCard />)
    
    await waitFor(() => {
      expect(screen.getByText('agent.error')).toBeTruthy()
    })
  })

  it('should render status when API returns data', async () => {
    const { agentService } = require('../src/services/agentApi')
    agentService.getAgentState.mockResolvedValue({
      state: 'MONITORING',
      last_active: new Date().toISOString(),
      activity_summary: 'Monitoring portfolio',
      active_tasks: [],
    })

    render(<AgentStatusCard />)
    
    await waitFor(() => {
      expect(screen.getByText('agent.states.MONITORING')).toBeTruthy()
    })
  })
})

describe('GoalSettingPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render empty state when no goals exist', async () => {
    const { agentService } = require('../src/services/agentApi')
    agentService.getGoals.mockResolvedValue([])

    render(<GoalSettingPanel />)
    
    await waitFor(() => {
      expect(screen.getByText('agent.goals.empty')).toBeTruthy()
    })
  })

  it('should render goals when API returns data', async () => {
    const { agentService } = require('../src/services/agentApi')
    agentService.getGoals.mockResolvedValue([
      {
        id: 'goal-1',
        goal_type: 'RETIREMENT',
        target_amount: 1000000,
        target_date: '2040-01-01',
        current_progress: 250000,
        status: 'ON_TRACK',
      },
    ])

    render(<GoalSettingPanel />)
    
    await waitFor(() => {
      expect(screen.getByText('agent.goals.types.RETIREMENT')).toBeTruthy()
    })
  })
})

describe('OpenFinanceConnect', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render bank cards', async () => {
    const { agentService } = require('../src/services/agentApi')
    agentService.getOpenFinanceConnections.mockResolvedValue([])

    render(<OpenFinanceConnect />)
    
    await waitFor(() => {
      expect(screen.getByText('E.Sun Bank')).toBeTruthy()
      expect(screen.getByText('Fubon Bank')).toBeTruthy()
    })
  })
})

describe('RebalanceActionCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render rebalance summary', async () => {
    const { agentService } = require('../src/services/agentApi')
    agentService.getRebalancePreview.mockResolvedValue({
      holdings: [],
      summary: {
        total_drift: 0,
        buy_count: 0,
        sell_count: 0,
        hold_count: 0,
      },
    })

    render(<RebalanceActionCard />)
    
    await waitFor(() => {
      expect(screen.getByText('agent.rebalance.totalDrift')).toBeTruthy()
    })
  })
})
