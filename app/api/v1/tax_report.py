"""
Tax Report API endpoints.
"""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.core.rate_limiter import limiter, DEFAULT_RATE_LIMIT
from app.services.tax_report_service import (
    TaxReportService,
    TaxLotMethod,
)
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/tax-report", tags=["Tax Report"])


class TaxLotPurchaseInput(BaseModel):
    """Input for a tax lot purchase."""
    symbol: str
    purchase_date: str  # YYYY-MM-DD
    quantity: float
    cost_per_share: float


class TaxLotSaleInput(BaseModel):
    """Input for a sale/disposition."""
    symbol: str
    sale_date: str  # YYYY-MM-DD
    quantity: float
    proceeds_per_share: float
    method: str = Field(default="fifo", pattern="^(fifo|lifo|specific_id)$")


class DispositionOutput(BaseModel):
    """Output for a single disposition."""
    symbol: str
    sale_date: str
    quantity: float
    proceeds_per_share: float
    total_proceeds: float
    method: str
    lots: list[dict]


class TaxSummaryOutput(BaseModel):
    """Output for annual tax summary."""
    tax_year: int
    short_term_gains: float
    short_term_losses: float
    long_term_gains: float
    long_term_losses: float
    total_realized_gain_loss: float
    net_short_term: float
    net_long_term: float
    total_taxable_gain: float
    wash_sale_adjustments: float
    total_transactions: int
    short_term_count: int
    long_term_count: int
    wash_sale_count: int


class IRS8949EntryOutput(BaseModel):
    """Output for IRS Form 8949 entry."""
    description: str
    date_acquired: str
    date_sold: str
    proceeds: float
    cost_basis: float
    gain_loss: float
    adjustment_code: Optional[str]
    adjustment_amount: float
    gain_loss_code: str


class TaxBracketOutput(BaseModel):
    """Output for tax bracket information."""
    filing_status: str
    taxable_income: float
    applicable_rate: float
    brackets: dict


@router.post("/calculate-disposition", response_model=DispositionOutput)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def calculate_disposition(
    request: Request,
    sale: TaxLotSaleInput,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> DispositionOutput:
    """
    Calculate gain/loss for a sale using specified tax lot method.
    
    Supports FIFO, LIFO, and Specific ID methods.
    Automatically tracks wash sale adjustments.
    """
    service = TaxReportService()
    
    # Parse dates
    sale_date = datetime.strptime(sale.sale_date, "%Y-%m-%d")
    
    # Calculate disposition
    method = TaxLotMethod(sale.method)
    result = service.calculate_disposition(
        symbol=sale.symbol,
        sale_date=sale_date,
        quantity=sale.quantity,
        proceeds_per_share=sale.proceeds_per_share,
        method=method
    )
    
    return DispositionOutput(
        symbol=result.symbol,
        sale_date=result.sale_date.strftime("%Y-%m-%d"),
        quantity=result.quantity,
        proceeds_per_share=result.proceeds_per_share,
        total_proceeds=result.total_proceeds,
        method=result.method.value,
        lots=[
            {
                "lot_id": lot.lot_id,
                "purchase_date": lot.purchase_date.strftime("%Y-%m-%d"),
                "quantity": lot.quantity,
                "cost_per_share": lot.cost_per_share,
                "proceeds": lot.proceeds,
                "gain_loss": lot.gain_loss,
                "gain_loss_type": lot.gain_loss_type.value,
                "wash_sale_disallowed": lot.wash_sale_disallowed,
            }
            for lot in result.lots
        ]
    )


@router.post("/annual-summary", response_model=TaxSummaryOutput)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def calculate_annual_summary(
    request: Request,
    tax_year: int,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> TaxSummaryOutput:
    """
    Calculate annual tax summary for the specified year.
    
    Requires tax lots to be added via add-tax-lot endpoint.
    """
    service = TaxReportService(tax_year=tax_year)
    
    # Return empty summary with year
    summary = service.calculate_annual_summary([])
    
    return TaxSummaryOutput(
        tax_year=summary.tax_year,
        short_term_gains=summary.short_term_gains,
        short_term_losses=summary.short_term_losses,
        long_term_gains=summary.long_term_gains,
        long_term_losses=summary.long_term_losses,
        total_realized_gain_loss=summary.total_realized_gain_loss,
        net_short_term=summary.net_short_term,
        net_long_term=summary.net_long_term,
        total_taxable_gain=summary.total_taxable_gain,
        wash_sale_adjustments=summary.wash_sale_adjustments,
        total_transactions=summary.total_transactions,
        short_term_count=summary.short_term_count,
        long_term_count=summary.long_term_count,
        wash_sale_count=summary.wash_sale_count,
    )


@router.get("/irs-8949", response_model=list[IRS8949EntryOutput])
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_irs8949(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    tax_year: int = 2024,
    code: str = "A",  # A = short-term, B = long-term
) -> list[IRS8949EntryOutput]:
    """
    Get IRS Form 8949 data for tax filing.
    
    Code 'A' returns short-term transactions.
    Code 'B' returns long-term transactions.
    """
    service = TaxReportService(tax_year=tax_year)
    entries = service.generate_irs8949_data([], code=code)
    
    return [
        IRS8949EntryOutput(
            description=e.description,
            date_acquired=e.date_acquired,
            date_sold=e.date_sold,
            proceeds=e.proceeds,
            cost_basis=e.cost_basis,
            gain_loss=e.gain_loss,
            adjustment_code=e.adjustment_code,
            adjustment_amount=e.adjustment_amount,
            gain_loss_code=e.gain_loss_code,
        )
        for e in entries
    ]


@router.get("/tax-brackets", response_model=TaxBracketOutput)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_tax_brackets(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    filing_status: str = "single",
    taxable_income: float = 0,
) -> TaxBracketOutput:
    """
    Get applicable capital gains tax brackets.
    
    Based on IRS 2024 capital gains rates.
    """
    service = TaxReportService()
    brackets = service.get_tax_brackets(filing_status, taxable_income)
    
    return TaxBracketOutput(**brackets)
