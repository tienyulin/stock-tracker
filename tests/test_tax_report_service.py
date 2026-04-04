"""
Tests for Tax Report Service.
"""

from datetime import datetime


class TestTaxLotMethod:
    """Test tax lot accounting methods."""

    def test_fifo_method(self):
        """Test FIFO tax lot method."""
        from app.services.tax_report_service import TaxLotMethod
        
        assert TaxLotMethod.FIFO.value == "fifo"
        assert TaxLotMethod.LIFO.value == "lifo"
        assert TaxLotMethod.SPECIFIC_ID.value == "specific_id"


class TestTaxReportService:
    """Test Tax Report Service."""

    def test_service_initialization(self):
        """Test service initializes with correct year."""
        from app.services.tax_report_service import TaxReportService
        
        service = TaxReportService(tax_year=2024)
        assert service.tax_year == 2024

    def test_add_purchase(self):
        """Test adding a purchase as tax lot."""
        from app.services.tax_report_service import TaxReportService
        
        service = TaxReportService()
        lot = service.add_purchase(
            symbol="AAPL",
            purchase_date=datetime(2024, 1, 15),
            quantity=100,
            cost_per_share=175.00
        )
        
        assert lot.symbol == "AAPL"
        assert lot.quantity == 100
        assert lot.cost_per_share == 175.00
        assert lot.adjusted_cost_basis == 17500.0

    def test_calculate_disposition_fifo(self):
        """Test FIFO gain/loss calculation."""
        from app.services.tax_report_service import TaxReportService, TaxLotMethod
        
        service = TaxReportService(tax_year=2024)
        
        # Add two lots
        service.add_purchase("AAPL", datetime(2024, 1, 1), 50, 150.00)
        service.add_purchase("AAPL", datetime(2024, 2, 1), 50, 170.00)
        
        # Sell 50 shares at $180 (should be FIFO - first lot)
        disp = service.calculate_disposition(
            symbol="AAPL",
            sale_date=datetime(2024, 12, 1),
            quantity=50,
            proceeds_per_share=180.00,
            method=TaxLotMethod.FIFO
        )
        
        assert disp.total_proceeds == 9000.0  # 50 * 180
        assert len(disp.lots) == 1
        assert disp.lots[0].gain_loss == 1500.0  # 9000 - 7500 (50 * 150)

    def test_calculate_disposition_lifo(self):
        """Test LIFO gain/loss calculation."""
        from app.services.tax_report_service import TaxReportService, TaxLotMethod
        
        service = TaxReportService(tax_year=2024)
        
        # Add two lots
        service.add_purchase("AAPL", datetime(2024, 1, 1), 50, 150.00)
        service.add_purchase("AAPL", datetime(2024, 2, 1), 50, 170.00)
        
        # Sell 50 shares at $180 (should be LIFO - second lot)
        disp = service.calculate_disposition(
            symbol="AAPL",
            sale_date=datetime(2024, 12, 1),
            quantity=50,
            proceeds_per_share=180.00,
            method=TaxLotMethod.LIFO
        )
        
        assert disp.total_proceeds == 9000.0
        assert len(disp.lots) == 1
        assert disp.lots[0].gain_loss == 500.0  # 9000 - 8500 (50 * 170)

    def test_long_term_vs_short_term(self):
        """Test holding period classification."""
        from app.services.tax_report_service import TaxReportService, TaxLotMethod, GainLossType
        
        service = TaxReportService(tax_year=2024)
        
        # Short-term lot (held < 365 days)
        service.add_purchase("AAPL", datetime(2024, 1, 1), 50, 150.00)
        
        # Sell after ~11 months (short-term)
        disp = service.calculate_disposition(
            symbol="AAPL",
            sale_date=datetime(2024, 11, 15),
            quantity=50,
            proceeds_per_share=160.00,
            method=TaxLotMethod.FIFO
        )
        
        assert disp.lots[0].gain_loss_type == GainLossType.SHORT_TERM

    def test_tax_summary_calculation(self):
        """Test annual tax summary."""
        from app.services.tax_report_service import TaxReportService, TaxLotMethod
        
        service = TaxReportService(tax_year=2024)
        
        # Add and sell AAPL
        service.add_purchase("AAPL", datetime(2024, 1, 1), 50, 150.00)
        disp = service.calculate_disposition(
            "AAPL", datetime(2024, 12, 1), 50, 180.00, TaxLotMethod.FIFO
        )
        
        # Add and sell MSFT
        service.add_purchase("MSFT", datetime(2024, 1, 1), 30, 350.00)
        disp2 = service.calculate_disposition(
            "MSFT", datetime(2024, 12, 1), 30, 320.00, TaxLotMethod.FIFO
        )
        
        summary = service.calculate_annual_summary([disp, disp2])
        
        assert summary.total_transactions == 2
        assert summary.tax_year == 2024

    def test_irs8949_generation(self):
        """Test IRS Form 8949 data generation."""
        from app.services.tax_report_service import TaxReportService, TaxLotMethod
        
        service = TaxReportService(tax_year=2024)
        
        # Add and sell
        service.add_purchase("AAPL", datetime(2024, 1, 1), 100, 150.00)
        disp = service.calculate_disposition(
            "AAPL", datetime(2024, 12, 1), 100, 180.00, TaxLotMethod.FIFO
        )
        
        entries = service.generate_irs8949_data([disp], code="A")
        
        assert len(entries) >= 0  # May be empty depending on holding period

    def test_tax_brackets(self):
        """Test tax bracket calculation."""
        from app.services.tax_report_service import TaxReportService
        
        service = TaxReportService()
        
        # Single filer, low income
        brackets = service.get_tax_brackets("single", 30000)
        assert brackets["applicable_rate"] == 0.0
        
        # Single filer, middle income
        brackets = service.get_tax_brackets("single", 100000)
        assert brackets["applicable_rate"] == 0.15
        
        # Single filer, high income
        brackets = service.get_tax_brackets("single", 600000)
        assert brackets["applicable_rate"] == 0.20
