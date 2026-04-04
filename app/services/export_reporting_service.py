"""
Export & Reporting Service - Phase 18

Provides export and reporting capabilities:
- PDF Reports (monthly portfolio statements, tax documents)
- Data Export (CSV/Excel, historical data downloads)
"""

from __future__ import annotations

import base64
import io
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ExportFormat(Enum):
    """Supported export formats."""

    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    JSON = "json"


class ReportType(Enum):
    """Report types supported."""

    PORTFOLIO_SUMMARY = "portfolio_summary"
    MONTHLY_STATEMENT = "monthly_statement"
    TAX_DOCUMENT = "tax_document"
    TRADE_HISTORY = "trade_history"


@dataclass
class PortfolioExport:
    """Portfolio export data."""

    user_id: str
    holdings: list[dict]
    total_value: float
    total_gain_loss: float
    total_gain_loss_percent: float
    generated_at: datetime = field(default_factory=datetime.utcnow)
    portfolio_name: str = "Portfolio"
    currency: str = "USD"


@dataclass
class Report:
    """Report data model."""

    id: str
    user_id: str
    report_type: ReportType
    period: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Portfolio summary fields
    holdings: Optional[list[dict]] = None
    total_value: Optional[float] = None
    total_gain_loss: Optional[float] = None
    total_gain_loss_percent: Optional[float] = None
    
    # Tax document fields
    realized_gains: Optional[float] = None
    unrealized_gains: Optional[float] = None
    dividends: Optional[float] = None
    tax_lot_details: Optional[list[dict]] = None
    
    # Trade history fields
    trades: Optional[list[dict]] = None
    
    # Export fields
    format: ExportFormat = ExportFormat.JSON
    file_path: Optional[str] = None


@dataclass
class ExportRecord:
    """Record of an export operation."""

    id: str
    user_id: str
    export_type: str  # "portfolio", "report"
    format: ExportFormat
    generated_at: datetime = field(default_factory=datetime.utcnow)
    file_size: int = 0


class ExportReportingService:
    """Service for export and reporting operations."""

    def __init__(self):
        """Initialize Export Reporting Service."""
        self._exports: dict[str, list[ExportRecord]] = {}

    def export_portfolio(
        self,
        user_id: str,
        data: PortfolioExport,
        format: ExportFormat,
    ) -> str:
        """
        Export portfolio data in the specified format.

        Args:
            user_id: User identifier
            data: Portfolio export data
            format: Export format (CSV, Excel, PDF, JSON)

        Returns:
            Exported data as string or base64 encoded bytes for binary formats
        """
        if format == ExportFormat.CSV:
            return self._export_csv(data)
        elif format == ExportFormat.EXCEL:
            return self._export_excel(data)
        elif format == ExportFormat.JSON:
            return self._export_json(data)
        elif format == ExportFormat.PDF:
            return self._export_pdf(data)
        
        return ""

    def _export_csv(self, data: PortfolioExport) -> str:
        """Export portfolio as CSV."""
        output = io.StringIO()
        
        # Write header
        output.write("symbol,quantity,current_price,total_value,gain_loss,gain_loss_percent\n")
        
        for holding in data.holdings:
            symbol = holding.get("symbol", "")
            quantity = holding.get("quantity", 0)
            current_price = holding.get("current_price", 0)
            total_value = quantity * current_price
            gain_loss = holding.get("gain_loss", 0)
            gain_loss_percent = holding.get("gain_loss_percent", 0)
            
            output.write(
                f"{symbol},{quantity},{current_price:.2f},{total_value:.2f},"
                f"{gain_loss:.2f},{gain_loss_percent:.2f}\n"
            )
        
        # Add summary
        output.write("\n")
        output.write(f"Total Value,{data.total_value:.2f}\n")
        output.write(f"Total Gain/Loss,{data.total_gain_loss:.2f}\n")
        output.write(f"Total Gain/Loss %,{data.total_gain_loss_percent:.2f}\n")
        
        result = output.getvalue()
        
        # Record export
        self._record_export(data.user_id, "portfolio", ExportFormat.CSV, len(result))
        
        return result

    def _export_excel(self, data: PortfolioExport) -> str:
        """
        Export portfolio as Excel (base64 encoded).
        
        Note: In production, this would use openpyxl to create actual Excel files.
        For now, returns base64 encoded CSV as a placeholder.
        """
        csv_data = self._export_csv(data)
        return base64.b64encode(csv_data.encode()).decode()

    def _export_json(self, data: PortfolioExport) -> str:
        """Export portfolio as JSON."""
        export_dict = {
            "user_id": data.user_id,
            "portfolio_name": data.portfolio_name,
            "currency": data.currency,
            "holdings": data.holdings,
            "summary": {
                "total_value": data.total_value,
                "total_gain_loss": data.total_gain_loss,
                "total_gain_loss_percent": data.total_gain_loss_percent,
            },
            "generated_at": data.generated_at.isoformat(),
        }
        
        result = json.dumps(export_dict, indent=2)
        
        # Record export
        self._record_export(data.user_id, "portfolio", ExportFormat.JSON, len(result))
        
        return result

    def _export_pdf(self, data: PortfolioExport) -> str:
        """
        Export portfolio as PDF.
        
        Note: In production, this would use a PDF library like reportlab
        or would call an external PDF generation service.
        Returns base64 encoded placeholder for now.
        """
        # Create a simple text-based representation
        content = f"""
Stock Tracker - Portfolio Statement
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Portfolio: {data.portfolio_name}
Currency: {data.currency}

SUMMARY
-------
Total Value: ${data.total_value:,.2f}
Total Gain/Loss: ${data.total_gain_loss:,.2f} ({data.total_gain_loss_percent:+.2f}%)

HOLDINGS
---------
"""
        for h in data.holdings:
            content += f"  {h.get('symbol')}: {h.get('quantity')} shares @ ${h.get('current_price', 0):.2f}\n"
        
        # Return base64 encoded PDF placeholder
        return base64.b64encode(content.encode()).decode()

    def generate_report(
        self,
        user_id: str,
        report_type: ReportType,
        period: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Report:
        """
        Generate a report.

        Args:
            user_id: User identifier
            report_type: Type of report to generate
            period: Reporting period (e.g., "2026-03" for monthly)
            start_date: Start date for trade history
            end_date: End date for trade history

        Returns:
            Generated report
        """
        report_id = str(uuid.uuid4())
        
        report = Report(
            id=report_id,
            user_id=user_id,
            report_type=report_type,
            period=period,
            start_date=start_date,
            end_date=end_date,
        )
        
        if report_type == ReportType.MONTHLY_STATEMENT:
            self._populate_monthly_statement(report)
        elif report_type == ReportType.TAX_DOCUMENT:
            self._populate_tax_document(report)
        elif report_type == ReportType.TRADE_HISTORY:
            self._populate_trade_history(report)
        elif report_type == ReportType.PORTFOLIO_SUMMARY:
            self._populate_portfolio_summary(report)
        
        return report

    def _populate_monthly_statement(self, report: Report) -> None:
        """Populate monthly statement report."""
        # In production, this would fetch actual portfolio data
        report.holdings = [
            {"symbol": "AAPL", "quantity": 10, "current_price": 175.0, "total_value": 1750.0},
            {"symbol": "GOOGL", "quantity": 5, "current_price": 140.0, "total_value": 700.0},
        ]
        report.total_value = 2450.0
        report.total_gain_loss = 150.0
        report.total_gain_loss_percent = 6.52

    def _populate_tax_document(self, report: Report) -> None:
        """Populate tax document report."""
        # In production, this would calculate actual tax data
        report.realized_gains = 1250.0
        report.unrealized_gains = 3500.0
        report.dividends = 45.50
        report.tax_lot_details = [
            {
                "symbol": "AAPL",
                "purchase_date": "2025-06-15",
                "quantity": 10,
                "cost_basis": 1500.0,
                "sale_proceeds": 1750.0,
                "gain": 250.0,
            }
        ]

    def _populate_trade_history(self, report: Report) -> None:
        """Populate trade history report."""
        # In production, this would fetch actual trade data
        report.trades = [
            {
                "date": "2026-03-15",
                "action": "BUY",
                "symbol": "AAPL",
                "quantity": 5,
                "price": 170.0,
                "total": 850.0,
            },
            {
                "date": "2026-02-20",
                "action": "BUY",
                "symbol": "GOOGL",
                "quantity": 5,
                "price": 135.0,
                "total": 675.0,
            },
        ]

    def _populate_portfolio_summary(self, report: Report) -> None:
        """Populate portfolio summary report."""
        report.holdings = [
            {"symbol": "AAPL", "quantity": 10, "current_price": 175.0, "total_value": 1750.0},
            {"symbol": "GOOGL", "quantity": 5, "current_price": 140.0, "total_value": 700.0},
        ]
        report.total_value = 2450.0
        report.total_gain_loss = 150.0
        report.total_gain_loss_percent = 6.52

    def _record_export(
        self,
        user_id: str,
        export_type: str,
        format: ExportFormat,
        file_size: int,
    ) -> None:
        """Record an export operation."""
        record = ExportRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            export_type=export_type,
            format=format,
            file_size=file_size,
        )
        
        if user_id not in self._exports:
            self._exports[user_id] = []
        
        self._exports[user_id].append(record)
        
        # Keep last 100 exports per user
        if len(self._exports[user_id]) > 100:
            self._exports[user_id] = self._exports[user_id][-100:]

    def get_export_history(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[ExportRecord]:
        """Get export history for a user."""
        if user_id not in self._exports:
            return []
        return self._exports[user_id][-limit:]


# Global service instance
_export_reporting_service: Optional[ExportReportingService] = None


def get_export_reporting_service() -> ExportReportingService:
    """Get or create the global export reporting service instance."""
    global _export_reporting_service
    if _export_reporting_service is None:
        _export_reporting_service = ExportReportingService()
    return _export_reporting_service
