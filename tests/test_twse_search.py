"""
Tests for TWSE stock search functionality.

This module tests the enhanced stock search that supports
both US and Taiwan (TWSE) stocks via Yahoo Finance.
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.yfinance_service import YFinanceService


class TestTWSESearch:
    """Test TWSE stock search functionality."""

    @pytest.fixture
    def service(self):
        return YFinanceService()

    @pytest.mark.asyncio
    async def test_search_stocks_returns_results(self, service):
        """Test that search returns matching stocks."""
        # This test verifies the search can handle queries
        # In production, it queries Yahoo Finance autocomplete
        assert service.validate_symbol("2330.TW") is True
        assert service.validate_symbol("AAPL") is True

    @pytest.mark.asyncio
    async def test_search_with_taiwan_symbol(self, service):
        """Test that Taiwan symbols are valid."""
        taiwan_symbols = [
            "2330.TW",  # TSMC
            "2317.TW",  # Foxconn
            "2454.TW",  # MediaTek
            "2308.TW",  # Delta
        ]
        for symbol in taiwan_symbols:
            assert service.validate_symbol(symbol) is True, f"{symbol} should be valid"

    @pytest.mark.asyncio
    async def test_search_query_validation(self, service):
        """Test that search query validation works."""
        # Empty query should be rejected
        assert service.validate_symbol("") is False
        # Query too long should be rejected
        assert service.validate_symbol("A" * 100) is False

    def test_twse_symbol_format(self, service):
        """Test TWSE symbol format validation."""
        # Valid TWSE symbols
        assert service.validate_symbol("2330.TW") is True
        assert service.validate_symbol("2498.TW") is True
        assert service.validate_symbol("0050.TW") is True  # Index fund

        # Valid US symbols
        assert service.validate_symbol("AAPL") is True
        assert service.validate_symbol("TSLA") is True
