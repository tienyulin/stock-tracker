"""
DeFi Position Service.

Handles DeFi positions: LP tokens, staking, lending, yield farming.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.models import DefiPosition
from app.services.crypto_service import fetch_crypto_price

logger = logging.getLogger(__name__)


class DefiService:
    """Service for managing DeFi positions."""

    def __init__(self, db: Session):
        self.db = db

    def create_position(
        self,
        user_id: UUID,
        protocol_name: str,
        position_type: str,
        token_symbol: str,
        quantity: float,
        entry_price: float,
        wallet_id: Optional[UUID] = None,
        token_address: Optional[str] = None,
        apy: Optional[float] = None,
        rewards_token: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> DefiPosition:
        current_price = fetch_crypto_price(token_symbol) or entry_price
        current_value = quantity * current_price
        cost_basis = quantity * entry_price
        pnl = current_value - cost_basis
        pnl_percentage = (pnl / cost_basis * 100) if cost_basis > 0 else 0.0

        position = DefiPosition(
            user_id=user_id,
            wallet_id=wallet_id,
            protocol_name=protocol_name,
            position_type=position_type,
            token_symbol=token_symbol,
            token_address=token_address,
            quantity=quantity,
            entry_price=entry_price,
            current_price=current_price,
            current_value=current_value,
            pnl=pnl,
            pnl_percentage=pnl_percentage,
            apy=apy,
            rewards_token=rewards_token,
            notes=notes,
        )
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        return position

    def get_position(self, position_id: UUID, user_id: UUID) -> Optional[DefiPosition]:
        return (
            self.db.query(DefiPosition)
            .filter(DefiPosition.id == position_id, DefiPosition.user_id == user_id)
            .first()
        )

    def list_positions(self, user_id: UUID) -> list[DefiPosition]:
        return self.db.query(DefiPosition).filter(DefiPosition.user_id == user_id).all()

    def update_position(
        self,
        position_id: UUID,
        user_id: UUID,
        quantity: Optional[float] = None,
        current_price: Optional[float] = None,
        apy: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> Optional[DefiPosition]:
        position = self.get_position(position_id, user_id)
        if not position:
            return None
        if quantity is not None:
            position.quantity = quantity
        if current_price is not None:
            position.current_price = current_price
        elif quantity is not None:
            position.current_price = fetch_crypto_price(position.token_symbol) or position.current_price
        if apy is not None:
            position.apy = apy
        if notes is not None:
            position.notes = notes
        # Recalculate
        position.current_value = position.quantity * position.current_price
        cost_basis = position.quantity * position.entry_price
        position.pnl = position.current_value - cost_basis
        position.pnl_percentage = (position.pnl / cost_basis * 100) if cost_basis > 0 else 0.0
        self.db.commit()
        self.db.refresh(position)
        return position

    def delete_position(self, position_id: UUID, user_id: UUID) -> bool:
        position = self.get_position(position_id, user_id)
        if not position:
            return False
        self.db.delete(position)
        self.db.commit()
        return True

    def calculate_estimated_rewards(self, position: DefiPosition) -> float:
        """Estimate annual rewards based on APY."""
        if not position.apy or position.apy == 0:
            return 0.0
        return position.current_value * (position.apy / 100)
