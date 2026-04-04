"""
Tests for Export & Reporting Service - Phase 18
"""

from datetime import datetime


class TestExportFormat:
    """Test export format enum."""

    def test_export_formats(self):
        from app.services.export_reporting_service import ExportFormat
        
        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.EXCEL.value == "excel"
        assert ExportFormat.PDF.value == "pdf"
        assert ExportFormat.JSON.value == "json"


class TestReportType:
    """Test report type enum."""

    def test_report_types(self):
        from app.services.export_reporting_service import ReportType
        
        assert ReportType.PORTFOLIO_SUMMARY.value == "portfolio_summary"
        assert ReportType.MONTHLY_STATEMENT.value == "monthly_statement"
        assert ReportType.TAX_DOCUMENT.value == "tax_document"
        assert ReportType.TRADE_HISTORY.value == "trade_history"


class TestPortfolioExport:
    """Test portfolio export data model."""

    def test_portfolio_export_creation(self):
        from app.services.export_reporting_service import PortfolioExport
        
        export = PortfolioExport(
            user_id="user-123",
            holdings=[
                {"symbol": "AAPL", "quantity": 10, "current_price": 150.0},
                {"symbol": "GOOGL", "quantity": 5, "current_price": 140.0},
            ],
            total_value=2200.0,
            total_gain_loss=200.0,
            total_gain_loss_percent=10.0,
            generated_at=datetime.now(),
        )
        
        assert export.user_id == "user-123"
        assert len(export.holdings) == 2
        assert export.total_value == 2200.0
        assert export.total_gain_loss == 200.0


class TestExportReportingService:
    """Test Export Reporting Service."""

    def test_service_initialization(self):
        from app.services.export_reporting_service import ExportReportingService
        
        service = ExportReportingService()
        assert service._exports == {}

    def test_export_portfolio_csv(self):
        from app.services.export_reporting_service import (
            ExportReportingService,
            ExportFormat,
            PortfolioExport,
        )
        
        service = ExportReportingService()
        
        export_data = PortfolioExport(
            user_id="user-123",
            holdings=[
                {"symbol": "AAPL", "quantity": 10, "current_price": 150.0},
            ],
            total_value=1500.0,
            total_gain_loss=100.0,
            total_gain_loss_percent=7.14,
            generated_at=datetime.now(),
        )
        
        result = service.export_portfolio("user-123", export_data, ExportFormat.CSV)
        
        assert "symbol,quantity,current_price" in result
        assert "AAPL" in result
        assert result.endswith("\n")

    def test_export_portfolio_excel(self):
        from app.services.export_reporting_service import (
            ExportReportingService,
            ExportFormat,
            PortfolioExport,
        )
        
        service = ExportReportingService()
        
        export_data = PortfolioExport(
            user_id="user-123",
            holdings=[{"symbol": "AAPL", "quantity": 10, "current_price": 150.0}],
            total_value=1500.0,
            total_gain_loss=100.0,
            total_gain_loss_percent=7.14,
            generated_at=datetime.now(),
        )
        
        result = service.export_portfolio("user-123", export_data, ExportFormat.EXCEL)
        
        # Excel format should be base64 encoded
        assert result is not None
        assert len(result) > 0

    def test_export_portfolio_json(self):
        from app.services.export_reporting_service import (
            ExportReportingService,
            ExportFormat,
            PortfolioExport,
        )
        
        service = ExportReportingService()
        
        export_data = PortfolioExport(
            user_id="user-123",
            holdings=[{"symbol": "AAPL", "quantity": 10, "current_price": 150.0}],
            total_value=1500.0,
            total_gain_loss=100.0,
            total_gain_loss_percent=7.14,
            generated_at=datetime.now(),
        )
        
        result = service.export_portfolio("user-123", export_data, ExportFormat.JSON)
        
        assert "user_id" in result
        assert "AAPL" in result

    def test_generate_monthly_statement(self):
        from app.services.export_reporting_service import (
            ExportReportingService,
            ReportType,
        )
        
        service = ExportReportingService()
        
        statement = service.generate_report(
            user_id="user-123",
            report_type=ReportType.MONTHLY_STATEMENT,
            period="2026-03",
        )
        
        assert statement.user_id == "user-123"
        assert statement.report_type == ReportType.MONTHLY_STATEMENT
        assert statement.period == "2026-03"
        assert statement.generated_at is not None

    def test_generate_tax_document(self):
        from app.services.export_reporting_service import (
            ExportReportingService,
            ReportType,
        )
        
        service = ExportReportingService()
        
        tax_doc = service.generate_report(
            user_id="user-123",
            report_type=ReportType.TAX_DOCUMENT,
            period="2025",
        )
        
        assert tax_doc.user_id == "user-123"
        assert tax_doc.report_type == ReportType.TAX_DOCUMENT
        assert tax_doc.period == "2025"
        assert tax_doc.realized_gains is not None or tax_doc.realized_gains == 0

    def test_generate_trade_history(self):
        from app.services.export_reporting_service import (
            ExportReportingService,
            ReportType,
        )
        
        service = ExportReportingService()
        
        history = service.generate_report(
            user_id="user-123",
            report_type=ReportType.TRADE_HISTORY,
            start_date="2026-01-01",
            end_date="2026-03-31",
        )
        
        assert history.user_id == "user-123"
        assert history.report_type == ReportType.TRADE_HISTORY
        assert history.start_date == "2026-01-01"
        assert history.end_date == "2026-03-31"

    def test_export_history_recorded(self):
        from app.services.export_reporting_service import (
            ExportReportingService,
            ExportFormat,
            PortfolioExport,
        )
        
        service = ExportReportingService()
        
        export_data = PortfolioExport(
            user_id="user-123",
            holdings=[],
            total_value=0,
            total_gain_loss=0,
            total_gain_loss_percent=0,
            generated_at=datetime.now(),
        )
        
        service.export_portfolio("user-123", export_data, ExportFormat.CSV)
        
        history = service.get_export_history("user-123")
        assert len(history) == 1
        assert history[0].format == ExportFormat.CSV
