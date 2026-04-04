"""
Tax Report Service for Annual Tax Summary and Capital Gains Tracking.

Provides comprehensive tax reporting including:
- Capital gains/losses calculation
- Tax lot accounting (FIFO, LIFO, Specific ID)
- Wash sale tracking and adjustments
- IRS Form 8949 data export
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import uuid


class TaxLotMethod(Enum):
    """Tax lot accounting methods."""
    FIFO = "fifo"  # First In, First Out
    LIFO = "lifo"  # Last In, First Out
    SPECIFIC_ID = "specific_id"  # Specific Identification


class GainLossType(Enum):
    """Type of capital gain/loss."""
    SHORT_TERM = "short_term"  # Held < 1 year
    LONG_TERM = "long_term"     # Held >= 1 year


@dataclass
class TaxLot:
    """Individual tax lot for a position."""
    lot_id: str
    symbol: str
    purchase_date: datetime
    quantity: float
    cost_per_share: float
    sale_date: Optional[datetime] = None
    sale_price: Optional[float] = None
    proceeds: float = 0.0
    gain_loss: float = 0.0
    gain_loss_type: GainLossType = GainLossType.SHORT_TERM
    wash_sale_disallowed: float = 0.0
    adjusted_cost_basis: float = 0.0


@dataclass
class Disposition:
    """A sale or disposition of a security."""
    symbol: str
    sale_date: datetime
    quantity: float
    proceeds_per_share: float
    total_proceeds: float
    method: TaxLotMethod = TaxLotMethod.FIFO
    lots: list[TaxLot] = field(default_factory=list)


@dataclass
class WashSaleAdjustment:
    """Wash sale rule adjustment."""
    original_loss: float
    disallowed_amount: float
    replacement_symbol: str
    adjustment_date: datetime
    replacement_lot_id: str


@dataclass
class TaxSummary:
    """Annual tax summary."""
    tax_year: int
    short_term_gains: float = 0.0
    short_term_losses: float = 0.0
    long_term_gains: float = 0.0
    long_term_losses: float = 0.0
    total_realized_gain_loss: float = 0.0
    net_short_term: float = 0.0
    net_long_term: float = 0.0
    total_taxable_gain: float = 0.0
    wash_sale_adjustments: float = 0.0  # Negative = disallowed losses
    
    # Counts
    total_transactions: int = 0
    short_term_count: int = 0
    long_term_count: int = 0
    wash_sale_count: int = 0


@dataclass
class IRS8949Entry:
    """IRS Form 8949 entry data."""
    description: str
    date_acquired: str
    date_sold: str
    proceeds: float
    cost_basis: float
    gain_loss: float
    adjustment_code: Optional[str] = None
    adjustment_amount: float = 0.0
    gain_loss_code: str = "A"  # A = short-term, B = long-term


class TaxReportService:
    """Service for generating tax reports and capital gains calculations."""

    # IRS 2024 Capital Gains Rates
    SHORT_TERM_RATES = [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]
    LONG_TERM_RATES = [0.0, 0.0, 0.15, 0.15, 0.15, 0.18, 0.20]
    
    # Wash sale window (days before and after)
    WASH_SALE_WINDOW = 30
    
    # Holding period thresholds
    SHORT_TERM_DAYS = 365

    def __init__(self, tax_year: Optional[int] = None):
        """
        Initialize Tax Report Service.
        
        Args:
            tax_year: Tax year for the report (default: current year)
        """
        self.tax_year = tax_year or datetime.now().year
        self.tax_lots: dict[str, list[TaxLot]] = {}  # {symbol: [lots]}
        self.wash_sale_adjustments: list[WashSaleAdjustment] = []

    def add_purchase(
        self,
        symbol: str,
        purchase_date: datetime,
        quantity: float,
        cost_per_share: float,
        lot_id: Optional[str] = None
    ) -> TaxLot:
        """
        Record a purchase as a tax lot.
        
        Args:
            symbol: Stock symbol
            purchase_date: Date of purchase
            quantity: Number of shares
            cost_per_share: Cost per share
            lot_id: Optional lot ID (auto-generated if not provided)
            
        Returns:
            Created TaxLot
        """
        if symbol not in self.tax_lots:
            self.tax_lots[symbol] = []
        
        lot = TaxLot(
            lot_id=lot_id or str(uuid.uuid4())[:8],
            symbol=symbol,
            purchase_date=purchase_date,
            quantity=quantity,
            cost_per_share=cost_per_share,
            adjusted_cost_basis=cost_per_share * quantity
        )
        
        self.tax_lots[symbol].append(lot)
        return lot

    def calculate_disposition(
        self,
        symbol: str,
        sale_date: datetime,
        quantity: float,
        proceeds_per_share: float,
        method: TaxLotMethod = TaxLotMethod.FIFO
    ) -> Disposition:
        """
        Calculate gain/loss for a sale using specified tax lot method.
        
        Args:
            symbol: Stock symbol
            sale_date: Date of sale
            quantity: Number of shares sold
            proceeds_per_share: Sale price per share
            method: Tax lot accounting method
            
        Returns:
            Disposition with gain/loss calculations
        """
        if symbol not in self.tax_lots:
            return Disposition(
                symbol=symbol,
                sale_date=sale_date,
                quantity=quantity,
                proceeds_per_share=proceeds_per_share,
                total_proceeds=0.0
            )
        
        lots = self.tax_lots[symbol]
        available_lots = [lot for lot in lots if lot.quantity > 0 and lot.sale_date is None]
        
        if not available_lots:
            return Disposition(
                symbol=symbol,
                sale_date=sale_date,
                quantity=quantity,
                proceeds_per_share=proceeds_per_share,
                total_proceeds=0.0
            )
        
        # Sort lots by date based on method
        if method == TaxLotMethod.FIFO:
            available_lots.sort(key=lambda x: x.purchase_date)
        elif method == TaxLotMethod.LIFO:
            available_lots.sort(key=lambda x: x.purchase_date, reverse=True)
        # SPECIFIC_ID would require explicit lot selection
        
        disposition_lots = []
        remaining_qty = quantity
        total_proceeds = 0.0
        
        for lot in available_lots:
            if remaining_qty <= 0:
                break
            
            lot_qty = min(lot.quantity, remaining_qty)
            lot_proceeds = lot_qty * proceeds_per_share
            lot_cost = lot_qty * lot.cost_per_share
            lot_gain_loss = lot_proceeds - lot_cost
            
            # Calculate holding period
            days_held = (sale_date - lot.purchase_date).days
            is_long_term = days_held >= self.SHORT_TERM_DAYS
            
            # Check for wash sale
            wash_sale_disallowed = 0.0
            if lot_gain_loss < 0:  # Loss
                wash_sale_check = self._check_wash_sale(symbol, lot.purchase_date, sale_date)
                if wash_sale_check:
                    wash_sale_disallowed = abs(lot_gain_loss)
                    lot_gain_loss = 0.0
            
            sold_lot = TaxLot(
                lot_id=lot.lot_id,
                symbol=symbol,
                purchase_date=lot.purchase_date,
                quantity=lot_qty,
                cost_per_share=lot.cost_per_share,
                sale_date=sale_date,
                sale_price=proceeds_per_share,
                proceeds=lot_proceeds,
                gain_loss=lot_gain_loss,
                gain_loss_type=GainLossType.LONG_TERM if is_long_term else GainLossType.SHORT_TERM,
                wash_sale_disallowed=wash_sale_disallowed,
                adjusted_cost_basis=lot_cost + wash_sale_disallowed
            )
            
            disposition_lots.append(sold_lot)
            lot.quantity -= lot_qty
            remaining_qty -= lot_qty
            total_proceeds += lot_proceeds
        
        return Disposition(
            symbol=symbol,
            sale_date=sale_date,
            quantity=quantity,
            proceeds_per_share=proceeds_per_share,
            total_proceeds=total_proceeds,
            method=method,
            lots=disposition_lots
        )

    def _check_wash_sale(self, symbol: str, purchase_date: datetime, sale_date: datetime) -> bool:
        """
        Check if a sale triggers wash sale rules.
        
        Wash sale: Buy substantially identical security within 30 days before or after a loss sale.
        
        Returns:
            True if wash sale applies
        """
        window_start = sale_date - timedelta(days=self.WASH_SALE_WINDOW)
        window_end = sale_date + timedelta(days=self.WASH_SALE_WINDOW)
        
        # Check if any purchases exist within the window (other than the lot being sold)
        if symbol in self.tax_lots:
            for lot in self.tax_lots[symbol]:
                if lot.purchase_date != purchase_date:
                    if window_start <= lot.purchase_date <= window_end:
                        return True
        
        return False

    def calculate_annual_summary(self, dispositions: list[Disposition]) -> TaxSummary:
        """
        Calculate annual tax summary from all dispositions.
        
        Args:
            dispositions: List of all dispositions for the year
            
        Returns:
            TaxSummary with totals
        """
        summary = TaxSummary(tax_year=self.tax_year)
        
        for disp in dispositions:
            for lot in disp.lots:
                gain_loss = lot.gain_loss
                
                if gain_loss > 0:
                    if lot.gain_loss_type == GainLossType.SHORT_TERM:
                        summary.short_term_gains += gain_loss
                        summary.short_term_count += 1
                    else:
                        summary.long_term_gains += gain_loss
                        summary.long_term_count += 1
                else:
                    loss = abs(gain_loss)
                    wash_sale_adj = lot.wash_sale_disallowed
                    
                    if lot.gain_loss_type == GainLossType.SHORT_TERM:
                        summary.short_term_losses += loss
                        summary.short_term_count += 1
                    else:
                        summary.long_term_losses += loss
                        summary.long_term_count += 1
                    
                    if wash_sale_adj > 0:
                        summary.wash_sale_adjustments += wash_sale_adj
                        summary.wash_sale_count += 1
                
                summary.total_transactions += 1
        
        # Calculate net amounts
        summary.net_short_term = summary.short_term_gains - summary.short_term_losses
        summary.net_long_term = summary.long_term_gains - summary.long_term_losses
        summary.total_realized_gain_loss = summary.net_short_term + summary.net_long_term
        
        # Calculate taxable gain (after wash sale adjustments)
        summary.total_taxable_gain = (
            max(0, summary.net_short_term) +
            max(0, summary.net_long_term) -
            summary.wash_sale_adjustments
        )
        
        return summary

    def generate_irs8949_data(
        self,
        dispositions: list[Disposition],
        code: str = "A"  # A = short-term, B = long-term
    ) -> list[IRS8949Entry]:
        """
        Generate IRS Form 8949 data.
        
        Args:
            dispositions: List of dispositions
            code: 'A' for short-term, 'B' for long-term
            
        Returns:
            List of IRS8949Entry for Form 8949
        """
        entries = []
        
        for disp in dispositions:
            for lot in disp.lots:
                # Filter by type based on code
                if code == "A" and lot.gain_loss_type != GainLossType.SHORT_TERM:
                    continue
                if code == "B" and lot.gain_loss_type != GainLossType.LONG_TERM:
                    continue
                
                gain_loss = lot.gain_loss
                adjustment_code = None
                adjustment_amount = 0.0
                
                # Check for wash sale adjustment
                if lot.wash_sale_disallowed > 0:
                    adjustment_code = "W"
                    adjustment_amount = lot.wash_sale_disallowed
                    gain_loss = 0.0  # Loss disallowed
                
                entry = IRS8949Entry(
                    description=f"{lot.symbol} - {lot.quantity} shares",
                    date_acquired=lot.purchase_date.strftime("%m/%d/%Y"),
                    date_sold=lot.sale_date.strftime("%m/%d/%Y") if lot.sale_date else "",
                    proceeds=lot.proceeds,
                    cost_basis=lot.quantity * lot.cost_per_share,
                    gain_loss=gain_loss,
                    adjustment_code=adjustment_code,
                    adjustment_amount=adjustment_amount,
                    gain_loss_code=code
                )
                entries.append(entry)
        
        return entries

    def get_tax_brackets(self, filing_status: str = "single", taxable_income: float = 0) -> dict:
        """
        Get applicable tax brackets for capital gains.
        
        Args:
            filing_status: 'single', 'married_joint', 'married_separate', 'head_of_household'
            taxable_income: Total taxable income to determine applicable bracket
            
        Returns:
            Dict with capital gains tax rates and brackets
        """
        # 2024 Long-term capital gains brackets
        brackets = {
            "single": {
                "rates": [0.00, 0.15, 0.20],
                "thresholds": [47025, 518900]  # 0%, 15%, 20%
            },
            "married_joint": {
                "rates": [0.00, 0.15, 0.20],
                "thresholds": [94050, 583750]
            },
            "married_separate": {
                "rates": [0.00, 0.15, 0.20],
                "thresholds": [47025, 291850]
            },
            "head_of_household": {
                "rates": [0.00, 0.15, 0.20],
                "thresholds": [63000, 551350]
            }
        }
        
        b = brackets.get(filing_status, brackets["single"])
        
        # Determine applicable rate
        rate = 0.0
        if taxable_income >= b["thresholds"][1]:
            rate = b["rates"][2]
        elif taxable_income >= b["thresholds"][0]:
            rate = b["rates"][1]
        
        return {
            "filing_status": filing_status,
            "taxable_income": taxable_income,
            "applicable_rate": rate,
            "brackets": b
        }
