"""
Simulation API endpoints.
"""

from fastapi import APIRouter

from app.schemas.schemas import RetirementSimulationRequest, RetirementSimulationResponse
from app.services.monte_carlo_service import MonteCarloService

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/retirement", response_model=RetirementSimulationResponse)
async def run_retirement_simulation(
    request: RetirementSimulationRequest,
) -> RetirementSimulationResponse:
    """Run Monte Carlo retirement simulation.

    Runs multiple simulations to calculate probability distribution
    of retirement outcomes based on current savings, contributions,
    and portfolio allocation.
    """
    service = MonteCarloService()
    return service.run_retirement_simulation(request)
