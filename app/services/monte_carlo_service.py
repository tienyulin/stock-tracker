"""
Monte Carlo Simulation Service for Retirement Planning.

Provides stochastic simulation of retirement portfolio outcomes.
"""

import random
from dataclasses import dataclass

import numpy as np


@dataclass
class PortfolioAllocation:
    """Portfolio asset allocation."""
    stocks: float = 0.6  # 60% stocks
    bonds: float = 0.3   # 30% bonds
    cash: float = 0.05   # 5% cash
    real_estate: float = 0.05  # 5% REITs


@dataclass
class MarketAssumptions:
    """Historical market assumptions for simulation."""
    stock_return: float = 0.10      # 10% annual return
    stock_volatility: float = 0.18  # 18% annual volatility
    bond_return: float = 0.04       # 4% annual return
    bond_volatility: float = 0.06   # 6% annual volatility
    cash_return: float = 0.02       # 2% annual return
    real_estate_return: float = 0.07  # 7% annual return
    real_estate_volatility: float = 0.12  # 12% annual volatility
    inflation_rate: float = 0.025    # 2.5% annual inflation


@dataclass
class RetirementParams:
    """Parameters for retirement simulation."""
    current_age: int = 30
    retirement_age: int = 65
    life_expectancy: int = 95
    current_portfolio: float = 100000.0
    monthly_contribution: float = 1000.0
    desired_annual_income: float = 60000.0
    social_security_monthly: float = 0.0
    allocation: PortfolioAllocation = None
    
    def __post_init__(self):
        if self.allocation is None:
            self.allocation = PortfolioAllocation()


@dataclass
class SimulationResult:
    """Result of Monte Carlo simulation."""
    success_rate: float  # Percentage of simulations that didn't run out of money
    median_ending_balance: float
    percentile_10: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    yearly_outcomes: list[dict]  # Year-by-year median outcomes
    total_contributions: float
    total_growth: float


class MonteCarloService:
    """Monte Carlo simulation for retirement planning."""

    def __init__(self):
        """Initialize Monte Carlo service."""
        self.market = MarketAssumptions()
        self.num_simulations = 10000
        self.random_seed = 42

    def set_seed(self, seed: int) -> None:
        """Set random seed for reproducibility."""
        self.random_seed = seed
        random.seed(seed)
        np.random.seed(seed)

    async def simulate(self, params: RetirementParams) -> SimulationResult:
        """
        Run Monte Carlo simulation.
        
        Args:
            params: Retirement planning parameters.
            
        Returns:
            SimulationResult with success rate and percentile outcomes.
        """
        # Set seed for reproducibility
        random.seed(self.random_seed)
        np.random.seed(self.random_seed)
        
        years_to_retirement = params.retirement_age - params.current_age
        years_in_retirement = params.life_expectancy - params.retirement_age
        total_years = years_to_retirement + years_in_retirement
        
        # Initialize arrays for all simulations
        ending_balances = np.zeros(self.num_simulations)
        success_count = 0
        
        # Year-by-year tracking for median calculation
        yearly_balances = [[] for _ in range(total_years + 1)]
        
        allocation = params.allocation
        m = self.market
        
        for sim in range(self.num_simulations):
            balance = params.current_portfolio
            
            # Accumulation phase (working years)
            for year in range(years_to_retirement):
                # Generate annual returns using normal distribution
                stock_return = np.random.normal(m.stock_return, m.stock_volatility)
                bond_return = np.random.normal(m.bond_return, m.bond_volatility)
                cash_return = m.cash_return
                re_return = np.random.normal(m.real_estate_return, m.real_estate_volatility)
                
                # Calculate weighted portfolio return
                portfolio_return = (
                    allocation.stocks * stock_return +
                    allocation.bonds * bond_return +
                    allocation.cash * cash_return +
                    allocation.real_estate * re_return
                )
                
                # Monthly contributions (assume annual, adjusted for return)
                annual_contribution = params.monthly_contribution * 12
                balance = balance * (1 + portfolio_return) + annual_contribution
                
                yearly_balances[year].append(balance)
            
            # Withdrawal phase (retirement years)
            for year in range(years_in_retirement):
                # Generate returns
                stock_return = np.random.normal(m.stock_return, m.stock_volatility)
                bond_return = np.random.normal(m.bond_return, m.bond_volatility)
                cash_return = m.cash_return
                re_return = np.random.normal(m.real_estate_return, m.real_estate_volatility)
                
                portfolio_return = (
                    allocation.stocks * stock_return +
                    allocation.bonds * bond_return +
                    allocation.cash * cash_return +
                    allocation.real_estate * re_return
                )
                
                # Calculate annual withdrawal (inflation-adjusted)
                years_in_ret = year + years_to_retirement
                inflation_factor = (1 + m.inflation_rate) ** years_in_ret
                annual_withdrawal = params.desired_annual_income * inflation_factor
                
                # Subtract social security
                annual_withdrawal -= params.social_security_monthly * 12 * inflation_factor
                annual_withdrawal = max(0, annual_withdrawal)
                
                balance = balance * (1 + portfolio_return) - annual_withdrawal
                
                if balance < 0:
                    balance = 0
                    # Record failure
                    for remaining_year in range(year, years_in_retirement):
                        yearly_balances[years_to_retirement + remaining_year].append(0)
                    break
                
                yearly_balances[years_to_retirement + year].append(balance)
            
            ending_balances[sim] = max(0, balance)
            if balance > 0:
                success_count += 1
        
        # Calculate statistics
        success_rate = (success_count / self.num_simulations) * 100
        
        # Sort ending balances for percentiles
        sorted_balances = np.sort(ending_balances)
        
        median_idx = self.num_simulations // 2
        p10_idx = int(self.num_simulations * 0.10)
        p25_idx = int(self.num_simulations * 0.25)
        p75_idx = int(self.num_simulations * 0.75)
        p90_idx = int(self.num_simulations * 0.90)
        
        median_ending = sorted_balances[median_idx]
        p10 = sorted_balances[p10_idx]
        p25 = sorted_balances[p25_idx]
        p75 = sorted_balances[p75_idx]
        p90 = sorted_balances[p90_idx]
        
        # Calculate year-by-year median outcomes
        yearly_outcomes = []
        for year_idx, year_balances in enumerate(yearly_balances):
            if year_balances:
                sorted_year = np.sort(year_balances)
                median = sorted_year[len(sorted_year) // 2]
                yearly_outcomes.append({
                    "year": year_idx,
                    "age": params.current_age + year_idx,
                    "median_balance": round(median, 2),
                    "is_retirement": year_idx >= years_to_retirement
                })
        
        # Calculate totals
        total_contributions = (
            params.current_portfolio +
            params.monthly_contribution * 12 * years_to_retirement
        )
        total_growth = median_ending - total_contributions
        
        return SimulationResult(
            success_rate=round(success_rate, 1),
            median_ending_balance=round(median_ending, 2),
            percentile_10=round(p10, 2),
            percentile_25=round(p25, 2),
            percentile_75=round(p75, 2),
            percentile_90=round(p90, 2),
            yearly_outcomes=yearly_outcomes,
            total_contributions=round(total_contributions, 2),
            total_growth=round(total_growth, 2)
        )


# Global instance
monte_carlo_service = MonteCarloService()
