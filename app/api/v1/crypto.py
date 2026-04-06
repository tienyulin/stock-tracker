"""
Crypto & DeFi Portfolio API routes.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import CexAccount, CryptoWallet, DefiPosition
from app.services.crypto_service import CryptoService
from app.services.defi_service import DefiService

router = APIRouter(prefix="/crypto", tags=["crypto"])

CurrentUser = Annotated[UUID, Depends(lambda: UUID("00000000-0000-0000-0000-000000000000"))]


def get_user_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000000")


UserID = Annotated[UUID, Depends(get_user_id)]


# ─── Wallets ──────────────────────────────────────────────────────────────────


@router.post("/wallets", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_wallet(
    name: str,
    blockchain: str,
    address: str,
    user_id: UserID = UserID,
    db: Session = Depends(get_db),
    balance: float = 0.0,
    notes: Optional[str] = None,
):
    service = CryptoService(db)
    wallet = service.create_wallet(
        user_id=user_id,
        name=name,
        blockchain=blockchain,
        address=address,
        balance=balance,
        notes=notes,
    )
    return {"id": str(wallet.id), "name": wallet.name, "blockchain": wallet.blockchain}


@router.get("/wallets", response_model=list[dict])
def list_wallets(user_id: UserID = UserID, db: Session = Depends(get_db)):
    service = CryptoService(db)
    wallets = service.list_wallets(user_id)
    return [
        {
            "id": str(w.id),
            "name": w.name,
            "blockchain": w.blockchain,
            "address": w.address,
            "balance": w.balance,
            "usd_value": w.usd_value,
            "notes": w.notes,
        }
        for w in wallets
    ]


@router.delete("/wallets/{wallet_id}")
def delete_wallet(wallet_id: UUID, user_id: UserID = UserID, db: Session = Depends(get_db)):
    service = CryptoService(db)
    ok = service.delete_wallet(wallet_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return {"ok": True}


# ─── DeFi Positions ──────────────────────────────────────────────────────────


@router.post("/defi-positions", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_defi_position(
    protocol_name: str,
    position_type: str,
    token_symbol: str,
    quantity: float,
    entry_price: float,
    user_id: UserID = UserID,
    db: Session = Depends(get_db),
    wallet_id: Optional[UUID] = None,
    token_address: Optional[str] = None,
    apy: Optional[float] = None,
    rewards_token: Optional[str] = None,
    notes: Optional[str] = None,
):
    service = DefiService(db)
    position = service.create_position(
        user_id=user_id,
        protocol_name=protocol_name,
        position_type=position_type,
        token_symbol=token_symbol,
        quantity=quantity,
        entry_price=entry_price,
        wallet_id=wallet_id,
        token_address=token_address,
        apy=apy,
        rewards_token=rewards_token,
        notes=notes,
    )
    return {"id": str(position.id), "protocol_name": position.protocol_name}


@router.get("/defi-positions", response_model=list[dict])
def list_defi_positions(user_id: UserID = UserID, db: Session = Depends(get_db)):
    service = DefiService(db)
    positions = service.list_positions(user_id)
    return [
        {
            "id": str(p.id),
            "protocol_name": p.protocol_name,
            "position_type": p.position_type,
            "token_symbol": p.token_symbol,
            "quantity": p.quantity,
            "entry_price": p.entry_price,
            "current_price": p.current_price,
            "current_value": p.current_value,
            "pnl": p.pnl,
            "pnl_percentage": p.pnl_percentage,
            "apy": p.apy,
        }
        for p in positions
    ]


@router.put("/defi-positions/{position_id}", response_model=dict)
def update_defi_position(
    position_id: UUID,
    user_id: UserID = UserID,
    db: Session = Depends(get_db),
    quantity: Optional[float] = None,
    current_price: Optional[float] = None,
    apy: Optional[float] = None,
    notes: Optional[str] = None,
):
    service = DefiService(db)
    position = service.update_position(position_id, user_id, quantity, current_price, apy, notes)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return {"id": str(position.id), "current_value": position.current_value, "pnl": position.pnl}


@router.delete("/defi-positions/{position_id}")
def delete_defi_position(position_id: UUID, user_id: UserID = UserID, db: Session = Depends(get_db)):
    service = DefiService(db)
    ok = service.delete_position(position_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Position not found")
    return {"ok": True}


# ─── Portfolio Summary ────────────────────────────────────────────────────────


@router.get("/summary", response_model=dict)
def get_crypto_summary(user_id: UserID = UserID, db: Session = Depends(get_db)):
    service = CryptoService(db)
    summary = service.get_portfolio_summary(user_id)
    return {
        "total_crypto_value": summary["total_crypto_value"],
        "wallet_count": summary["wallet_count"],
        "defi_position_count": summary["defi_position_count"],
    }
