"""
Tests for Tax Optimization, Asset Location, and Withdrawal Services.
"""

from datetime import datetime, timedelta

import pytest


class TestTaxOptimizationService:
    """Test Tax Optimization Service."""

    def test_service_initialization(self):
        """Test service initializes with correct rates."""
        from app.services.tax_optimization_service import TaxOptimizationService

        service = TaxOptimizationService(short_term_rate=0.32, long_term_rate=0.15)
        assert service.short_term_rate == 0.32
        assert service.long_term_rate == 0.15

    def test_analyze_portfolio_tax_empty(self):
        """Test analyzing empty portfolio."""
        from app.services.tax_optimization_service import TaxOptimizationService

        service = TaxOptimizationService()
        summary = service.analyze_portfolio_tax([])
        assert summary.total_unrealized_gains == 0.0
        assert summary.total_unrealized_losses == 0.0
        assert summary.net_unrealized == 0.0
        assert len(summary.opportunities) == 0

    def test_analyze_portfolio_with_gain(self):
        """Test analyzing portfolio with unrealized gain."""
        from app.services.tax_optimization_service import TaxOptimizationService

        service = TaxOptimizationService()
        positions = [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "cost_basis": 150.0,
                "current_price": 200.0,
                "purchase_date": datetime(2024, 1, 1),
            }
        ]
        summary = service.analyze_portfolio_tax(positions, current_date=datetime(2025, 6, 1))
        assert summary.total_unrealized_gains == 5000.0  # (200-150)*100
        assert summary.long_term_unrealized_gains == 5000.0

    def test_analyze_portfolio_with_loss_harvest(self):
        """Test loss harvesting opportunity identified."""
        from app.services.tax_optimization_service import TaxOptimizationService, OptimizationType

        service = TaxOptimizationService()
        # Short-term loss
        positions = [
            {
                "symbol": "TSLA",
                "quantity": 50,
                "cost_basis": 250.0,
                "current_price": 180.0,
                "purchase_date": datetime(2025, 1, 1),  # ~5 months ago = short-term
            }
        ]
        summary = service.analyze_portfolio_tax(positions, current_date=datetime(2025, 6, 1))
        assert summary.total_unrealized_losses == 3500.0  # (250-180)*50
        assert summary.short_term_unrealized_losses == 3500.0
        assert len(summary.opportunities) >= 1
        loss_harvest_opps = [o for o in summary.opportunities if o.type == OptimizationType.LOSS_HARVEST]
        assert len(loss_harvest_opps) == 1
        assert loss_harvest_opps[0].symbol == "TSLA"

    def test_loss_harvesting_candidates(self):
        """Test loss harvesting candidates filter."""
        from app.services.tax_optimization_service import TaxOptimizationService

        service = TaxOptimizationService()
        # Use current date to ensure positions are short-term (< 365 days)
        current = datetime(2025, 6, 1)
        positions = [
            {
                "symbol": "TSLA",
                "quantity": 10,
                "cost_basis": 250.0,
                "current_price": 180.0,
                "purchase_date": datetime(2025, 1, 1),  # ~151 days ago = short-term
            },
            {
                "symbol": "NVDA",
                "quantity": 5,
                "cost_basis": 500.0,
                "current_price": 450.0,
                "purchase_date": datetime(2025, 3, 1),  # ~92 days ago = short-term
            },
        ]
        candidates = service.get_loss_harvesting_candidates(positions, min_loss=100, current_date=current)
        assert len(candidates) == 2
        # TSLA: (250-180)*10 = 700, NVDA: (500-450)*5 = 250, total = 950
        total_harvestable = sum(c.details.get("unrealized_loss", 0) for c in candidates)
        assert total_harvestable == 950.0

    def test_holding_period_recommendation(self):
        """Test near long-term threshold generates recommendation."""
        from app.services.tax_optimization_service import TaxOptimizationService, OptimizationType

        service = TaxOptimizationService()
        # 355 days held (just 10 days short of long-term)
        positions = [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "cost_basis": 150.0,
                "current_price": 200.0,
                "purchase_date": datetime(2025, 6, 1) - timedelta(days=355),
            }
        ]
        summary = service.analyze_portfolio_tax(positions, current_date=datetime(2025, 6, 1))
        holding_opps = [o for o in summary.opportunities if o.type == OptimizationType.HOLDING_PERIOD]
        assert len(holding_opps) == 1
        assert holding_opps[0].details["days_to_long_term"] <= 30

    def test_calculate_tax_liability(self):
        """Test tax liability calculation."""
        from app.services.tax_optimization_service import TaxOptimizationService

        service = TaxOptimizationService(short_term_rate=0.24, long_term_rate=0.15)
        result = service.calculate_tax_liability(
            realized_gains=15000,  # total gains
            realized_losses=0,
            short_term_gains=10000,
            long_term_gains=5000,
            long_term_losses=0,
        )
        assert result["short_term_gain"] == 10000
        assert result["long_term_gain"] == 5000
        assert result["short_term_tax"] == 2400  # 10000 * 0.24
        assert result["long_term_tax"] == 750    # 5000 * 0.15
        assert result["total_tax"] == 3150

    def test_calculate_tax_liability_with_losses(self):
        """Test tax liability with losses."""
        from app.services.tax_optimization_service import TaxOptimizationService

        service = TaxOptimizationService(short_term_rate=0.24, long_term_rate=0.15)
        result = service.calculate_tax_liability(
            realized_gains=10000,
            realized_losses=3000,
            short_term_gains=10000,
            short_term_losses=3000,
            long_term_gains=0,
            long_term_losses=0,
        )
        assert result["short_term_gain"] == 7000  # 10000 - 3000
        assert result["short_term_tax"] == 1680    # 7000 * 0.24

    def test_asset_tax_efficiency_ratings(self):
        """Test asset tax efficiency ratings."""
        from app.services.tax_optimization_service import TaxOptimizationService, AssetTaxEfficiency

        service = TaxOptimizationService()
        assert service.get_asset_tax_efficiency("AAPL", "stock") == AssetTaxEfficiency.HIGH
        assert service.get_asset_tax_efficiency("VTI", "ETF") == AssetTaxEfficiency.HIGH
        assert service.get_asset_tax_efficiency("VNQ", "REIT") == AssetTaxEfficiency.LOW
        assert service.get_asset_tax_efficiency("BND", "bond") == AssetTaxEfficiency.LOW


class TestAssetLocationService:
    """Test Asset Location Service."""

    def test_service_initialization(self):
        """Test service initializes empty."""
        from app.services.asset_location_service import AssetLocationService

        service = AssetLocationService()
        assert len(service.accounts) == 0
        assert len(service.positions) == 0

    def test_asset_location_recommendations(self):
        """Test asset location recommendations for tax-inefficient assets."""
        from app.services.asset_location_service import (
            AssetLocationService, AccountType, AssetType, Position
        )

        service = AssetLocationService()
        # annual_distribution is dollar amount of annual distributions per share
        positions = [
            Position(
                symbol="BND",
                asset_type=AssetType.BOND,
                quantity=100,
                current_price=80.0,
                cost_basis=82.0,
                annual_distribution=300.0,  # $300/yr distribution
                turnover_rate=0.1,
            ),
            Position(
                symbol="VNQ",
                asset_type=AssetType.REIT,
                quantity=50,
                current_price=85.0,
                cost_basis=90.0,
                annual_distribution=200.0,  # $200/yr distribution
                turnover_rate=0.2,
            ),
        ]

        recommendations = service.get_recommendations(positions, [])
        assert len(recommendations) >= 1
        # Bond and REIT should recommend moving to tax-deferred
        bond_recs = [r for r in recommendations if r.symbol == "BND"]
        assert len(bond_recs) >= 1
        assert bond_recs[0].recommended_account == AccountType.TRADITIONAL_IRA

    def test_account_allocations(self):
        """Test account allocation recommendations."""
        from app.services.asset_location_service import AssetLocationService, AccountType

        service = AssetLocationService()
        allocations = service.get_account_allocations(100000, risk_profile="moderate")

        assert AccountType.TAXABLE in allocations
        assert AccountType.TRADITIONAL_IRA in allocations
        assert AccountType.ROTH_IRA in allocations
        assert AccountType.PLAN_401K in allocations

        # Taxable should favor stocks/ETFs
        taxable_alloc = allocations[AccountType.TAXABLE]
        assert taxable_alloc.target_allocation.get("stock", 0) >= 0.5

    def test_location_savings_calculation(self):
        """Test savings calculation from recommendations."""
        from app.services.asset_location_service import (
            AssetLocationService, AccountType, AssetType, Position,
            AssetLocationRecommendation
        )

        service = AssetLocationService()
        positions = []
        recommendations = [
            AssetLocationRecommendation(
                symbol="BND",
                current_account=AccountType.TAXABLE,
                recommended_account=AccountType.TRADITIONAL_IRA,
                reason="Bond in taxable",
                estimated_tax_savings=100.0,
                quantity=100,
                priority="high",
            )
        ]

        savings = service.calculate_location_savings(positions, recommendations)
        assert savings["total_annual_tax_savings"] == 100.0
        assert savings["recommendations_count"] == 1


class TestTaxEfficientWithdrawalService:
    """Test Tax-Efficient Withdrawal Service."""

    def test_service_initialization(self):
        """Test service initializes with correct parameters."""
        from app.services.tax_efficient_withdrawal_service import TaxEfficientWithdrawalService

        service = TaxEfficientWithdrawalService(current_age=65, filing_status="married_joint")
        assert service.current_age == 65
        assert service.filing_status == "married_joint"

    def test_marginal_rate_calculation(self):
        """Test marginal tax rate calculation."""
        from app.services.tax_efficient_withdrawal_service import TaxEfficientWithdrawalService

        service = TaxEfficientWithdrawalService(current_age=65, filing_status="single")
        # Low income → 10% bracket
        rate = service.calculate_marginal_rate(5000)
        assert rate == 0.10
        # Mid income → 22% bracket
        rate = service.calculate_marginal_rate(60000)
        assert rate == 0.22

    def test_calculate_tax(self):
        """Test tax calculation."""
        from app.services.tax_efficient_withdrawal_service import TaxEfficientWithdrawalService

        service = TaxEfficientWithdrawalService(current_age=65, filing_status="single")
        result = service.calculate_tax(ordinary_income=50000, capital_gains=10000)
        assert result["ordinary_income"] == 50000
        assert result["capital_gains"] == 10000
        assert result["total_tax"] > 0
        assert "effective_rate" in result
        assert "marginal_rate" in result

    def test_generate_withdrawal_sequence(self):
        """Test withdrawal sequence generation."""
        from app.services.tax_efficient_withdrawal_service import (
            TaxEfficientWithdrawalService, WithdrawalSource, AccountBalance
        )

        service = TaxEfficientWithdrawalService(current_age=65, filing_status="single")
        service.add_account(AccountBalance(
            source=WithdrawalSource.ROTH,
            balance=500000,
            annual_distribution=0,
        ))
        service.add_account(AccountBalance(
            source=WithdrawalSource.TAXABLE,
            balance=300000,
            annual_distribution=0,
        ))

        plan = service.generate_withdrawal_sequence(
            annual_expenses=60000,
            start_year=1,
            years_to_plan=10,
            social_security_annual=24000,
        )

        assert len(plan.years) == 10
        assert plan.total_withdrawn > 0
        # First year should start with Roth
        first_year = plan.years[0]
        assert first_year.year == 1
        assert len(first_year.withdrawal_steps) >= 1

    def test_roth_conversion_analysis(self):
        """Test Roth conversion analysis."""
        from app.services.tax_efficient_withdrawal_service import TaxEfficientWithdrawalService

        service = TaxEfficientWithdrawalService(current_age=60, filing_status="single")
        analysis = service.calculate_roth_conversion_analysis(
            trad_ira_balance=500000,
            current_marginal_rate=0.22,
            target_marginal_rate=0.32,
            years_until_rmd=10,
        )

        assert "cost_to_convert_now" in analysis
        assert "estimated_future_rmd_tax" in analysis
        assert "recommendation" in analysis
        # With higher future rate, conversion recommendation should be "convert"
        assert analysis["recommendation"] in ["convert", "wait"]

    def test_rmd_age_determination(self):
        """Test RMD age determination based on birth year."""
        from app.services.tax_efficient_withdrawal_service import TaxEfficientWithdrawalService

        service = TaxEfficientWithdrawalService(current_age=65)
        # Born 1955 → RMD at 73
        rmd_age = service.get_rmd_age(1955)
        assert rmd_age == 73
        # Born 1967 → RMD at 75
        rmd_age = service.get_rmd_age(1967)
        assert rmd_age == 75
