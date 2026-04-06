"""
Tests for Futures API Service
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.futures import FuturesPosition


class TestFuturesPosition:
    """Test FuturesPosition model methods."""

    def test_calculate_unrealized_pnl_long(self):
        """Test P&L calculation for long position."""
        position = FuturesPosition(
            id=uuid4(),
            user_id=uuid4(),
            symbol="ES",
            contract_size=50,
            entry_price=4500,
            current_price=4520,
            quantity=1,
            position_type="LONG",
            entry_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
        )

        pnl = position.calculate_unrealized_pnl()

        # (4520 - 4500) * 50 * 1 = 1000
        assert pnl == 1000

    def test_calculate_unrealized_pnl_short(self):
        """Test P&L calculation for short position."""
        position = FuturesPosition(
            id=uuid4(),
            user_id=uuid4(),
            symbol="ES",
            contract_size=50,
            entry_price=4500,
            current_price=4480,
            quantity=1,
            position_type="SHORT",
            entry_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
        )

        pnl = position.calculate_unrealized_pnl()

        # -(4480 - 4500) * 50 * 1 = 1000
        assert pnl == 1000

    def test_calculate_unrealized_pnl_no_current_price(self):
        """Test P&L calculation when no current price."""
        position = FuturesPosition(
            id=uuid4(),
            user_id=uuid4(),
            symbol="ES",
            contract_size=50,
            entry_price=4500,
            current_price=None,
            quantity=1,
            position_type="LONG",
            entry_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
        )

        pnl = position.calculate_unrealized_pnl()

        assert pnl == 0
