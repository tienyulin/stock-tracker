"""
Crypto & DeFi Portfolio Service.

Handles:
- On-chain wallet balance fetching (Etherscan)
- CEX account balance syncing
- DeFi position tracking
- CoinGecko price data
"""

import logging
from typing import Optional
from uuid import UUID

import requests
from sqlalchemy.orm import Session

from app.models.models import CexAccount, CryptoWallet, DefiPosition

logger = logging.getLogger(__name__)

# ─── Price API ────────────────────────────────────────────────────────────────

COINGECKO_API = "https://api.coingecko.com/api/v3"


def fetch_crypto_price(symbol: str) -> Optional[float]:
    """Fetch current USD price for a crypto symbol via CoinGecko."""
    try:
        # Map common symbols
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "USDT": "tether",
            "USDC": "usd-coin",
            "BNB": "binancecoin",
            "SOL": "solana",
            "XRP": "ripple",
            "ADA": "cardano",
            "DOGE": "dogecoin",
            "MATIC": "matic-network",
        }
        coin_id = symbol_map.get(symbol.upper())
        if not coin_id:
            return None
        url = f"{COINGECKO_API}/simple/price"
        params = {"ids": coin_id, "vs_currencies": "usd"}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get(coin_id, {}).get("usd")
    except Exception as e:
        logger.warning(f"Failed to fetch price for {symbol}: {e}")
        return None


def fetch_eth_balance(address: str, etherscan_api_key: str = "") -> Optional[float]:
    """Fetch ETH balance for an address via Etherscan."""
    try:
        url = "https://api.etherscan.io/api"
        params = {
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
            "apikey": etherscan_api_key,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "1":
            wei = int(data["result"])
            return wei / 1e18
    except Exception as e:
        logger.warning(f"Failed to fetch ETH balance for {address}: {e}")
    return None


# ─── CryptoService ────────────────────────────────────────────────────────────


class CryptoService:
    """Service for managing crypto wallets and portfolio."""

    def __init__(self, db: Session):
        self.db = db

    def create_wallet(
        self,
        user_id: UUID,
        name: str,
        blockchain: str,
        address: str,
        balance: float = 0.0,
        usd_value: float = 0.0,
        notes: Optional[str] = None,
    ) -> CryptoWallet:
        wallet = CryptoWallet(
            user_id=user_id,
            name=name,
            blockchain=blockchain,
            address=address,
            balance=balance,
            usd_value=usd_value,
            notes=notes,
        )
        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)
        return wallet

    def get_wallet(self, wallet_id: UUID, user_id: UUID) -> Optional[CryptoWallet]:
        return (
            self.db.query(CryptoWallet)
            .filter(CryptoWallet.id == wallet_id, CryptoWallet.user_id == user_id)
            .first()
        )

    def list_wallets(self, user_id: UUID) -> list[CryptoWallet]:
        return self.db.query(CryptoWallet).filter(CryptoWallet.user_id == user_id).all()

    def delete_wallet(self, wallet_id: UUID, user_id: UUID) -> bool:
        wallet = self.get_wallet(wallet_id, user_id)
        if not wallet:
            return False
        self.db.delete(wallet)
        self.db.commit()
        return True

    def sync_wallet_value(self, wallet: CryptoWallet, price: Optional[float] = None) -> CryptoWallet:
        """Sync wallet USD value using current ETH price."""
        if price is None:
            price = fetch_crypto_price("ETH") or 0.0
        wallet.balance = wallet.balance or 0.0
        wallet.usd_value = wallet.balance * price
        self.db.commit()
        self.db.refresh(wallet)
        return wallet

    def get_portfolio_summary(self, user_id: UUID) -> dict:
        wallets = self.list_wallets(user_id)
        defi_positions = self.db.query(DefiPosition).filter(DefiPosition.user_id == user_id).all()
        total_wallet_value = sum(w.usd_value or 0 for w in wallets)
        total_defi_value = sum(p.current_value or 0 for p in defi_positions)
        return {
            "total_crypto_value": total_wallet_value + total_defi_value,
            "wallet_count": len(wallets),
            "defi_position_count": len(defi_positions),
            "wallets": wallets,
            "defi_positions": defi_positions,
        }
