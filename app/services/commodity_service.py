"""
Commodity & Precious Metals Service.

Handles:
- Commodity position CRUD
- Futures contract tracking
- Precious metals price fetching
- Inflation hedge metrics
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.commodities import CommodityPosition, FuturesContract

logger = logging.getLogger(__name__)

# ─── Commodity Ticker Map ────────────────────────────────────────────────────
COMMODITY_TICKERS = {
    "gold": "GC=F",
    "silver": "SI=F",
    "platinum": "PL=F",
    "oil": "CL=F",
    "natural_gas": "NG=F",
    "agricultural": "Z=F",
}

COMMODITY_ETF_TICKERS = {
    "gold": "GLD",
    "silver": "SLV",
    "oil": "USO",
    "agricultural": "DBA",
}


# ─── Price Fetching ──────────────────────────────────────────────────────────

def fetch_commodity_price(ticker: str) -> Optional[float]:
    """Fetch current price for a commodity ticker using yfinance."""
    try:
        import yfinance as yf

        data = yf.Ticker(ticker).history(period="1d", auto_adjust=True)
        if not data.empty:
            return round(float(data["Close"].iloc[-1]), 4)
    except Exception as e:
        logger.warning(f"Failed to fetch price for {ticker}: {e}")
    return None


def fetch_precious_metals_prices() -> dict:
    """Fetch prices for gold, silver, platinum."""
    result = {}
    for metal, ticker in [("gold", "GC=F"), ("silver", "SI=F"), ("platinum", "PL=F")]:
        price = fetch_commodity_price(ticker)
        result[metal] = price
    return result


def fetch_commodity_history(ticker: str, days: int = 365) -> Optional[list]:
    """Fetch historical prices for a commodity."""
    try:
        import yfinance as yf

        data = yf.Ticker(ticker).history(period=f"{days}d", auto_adjust=True)
        if not data.empty:
            return [
                {"date": str(idx.date()), "close": round(float(row["Close"]), 4)}
                for idx, row in data.iterrows()
            ]
    except Exception as e:
        logger.warning(f"Failed to fetch history for {ticker}: {e}")
    return None


# ─── P&L Calculations ────────────────────────────────────────────────────────

def calculate_position_pnl(position: CommodityPosition) -> tuple[float, float]:
    """Calculate unrealized P&L for a commodity position."""
    if position.current_price is None:
        return 0.0, 0.0
    market_value = float(position.quantity) * float(position.current_price)
    cost_basis = float(position.quantity) * float(position.purchase_price)
    unrealized_pnl = market_value - cost_basis
    return round(market_value, 4), round(unrealized_pnl, 4)


def calculate_futures_pnl(
    contract: FuturesContract,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Calculate realized and unrealized P&L for a futures contract."""
    if contract.current_price is None:
        return contract.realized_pnl, 0.0, 0.0
    multiplier = float(contract.contract_size)
    if contract.position_type == "long":
        unrealized = (float(contract.current_price) - float(contract.entry_price)) * multiplier
    else:
        unrealized = (float(contract.entry_price) - float(contract.current_price)) * multiplier
    market_value = float(contract.current_price) * multiplier
    return contract.realized_pnl, round(unrealized, 4), round(market_value, 4)


def calculate_margin_requirement(
    contract_size: float, entry_price: float, margin_rate: float = 0.05
) -> float:
    """Calculate margin requirement (default 5% of contract value)."""
    return round(float(contract_size) * float(entry_price) * margin_rate, 4)


# ─── Services ────────────────────────────────────────────────────────────────


class CommodityService:
    """Service for commodity position operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_position(
        self,
        user_id: UUID,
        name: str,
        commodity_type: str,
        quantity: float,
        purchase_price: float,
        purchase_date: date,
        unit: str = "shares",
        ticker: Optional[str] = None,
        current_price: Optional[float] = None,
        currency: str = "USD",
        notes: Optional[str] = None,
    ) -> CommodityPosition:
        market_value = None
        unrealized_pnl = None
        if current_price is not None:
            market_value = round(quantity * current_price, 4)
            unrealized_pnl = round(quantity * (current_price - purchase_price), 4)

        position = CommodityPosition(
            user_id=user_id,
            name=name,
            commodity_type=commodity_type,
            ticker=ticker,
            quantity=quantity,
            unit=unit,
            purchase_price=purchase_price,
            current_price=current_price,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl,
            purchase_date=purchase_date,
            currency=currency,
            notes=notes,
        )
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        return position

    def get_position(self, position_id: UUID, user_id: UUID) -> Optional[CommodityPosition]:
        return (
            self.db.query(CommodityPosition)
            .filter(CommodityPosition.id == position_id, CommodityPosition.user_id == user_id)
            .first()
        )

    def list_positions(self, user_id: UUID) -> list[CommodityPosition]:
        return (
            self.db.query(CommodityPosition)
            .filter(CommodityPosition.user_id == user_id)
            .all()
        )

    def update_position(
        self, position_id: UUID, user_id: UUID, **kwargs
    ) -> Optional[CommodityPosition]:
        position = self.get_position(position_id, user_id)
        if not position:
            return None
        for key, value in kwargs.items():
            if hasattr(position, key) and key not in ("id", "user_id"):
                setattr(position, key, value)
        # Recalculate P&L if price changed
        if "current_price" in kwargs and kwargs["current_price"] is not None:
            position.market_value, position.unrealized_pnl = calculate_position_pnl(position)
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

    def sync_prices(self, user_id: UUID) -> dict:
        """Sync current prices for all positions from Yahoo Finance."""
        positions = self.list_positions(user_id)
        updated = []
        errors = []
        for p in positions:
            ticker = p.ticker or COMMODITY_TICKERS.get(p.commodity_type)
            if ticker:
                price = fetch_commodity_price(ticker)
                if price:
                    p.current_price = price
                    p.market_value, p.unrealized_pnl = calculate_position_pnl(p)
                    self.db.commit()
                    updated.append({"id": str(p.id), "name": p.name, "current_price": price})
                else:
                    errors.append({"id": str(p.id), "name": p.name, "error": "Failed to fetch price"})
        return {"updated": updated, "errors": errors}

    def get_commodity_summary(self, user_id: UUID) -> dict:
        """Aggregate statistics across all commodity positions."""
        positions = self.list_positions(user_id)
        if not positions:
            return {
                "total_positions": 0,
                "total_market_value": 0.0,
                "total_unrealized_pnl": 0.0,
                "by_type": {},
            }

        total_value = sum(float(p.market_value or 0) for p in positions)
        total_pnl = sum(float(p.unrealized_pnl or 0) for p in positions)

        by_type: dict[str, dict] = {}
        for p in positions:
            t = p.commodity_type
            if t not in by_type:
                by_type[t] = {"count": 0, "market_value": 0.0, "unrealized_pnl": 0.0}
            by_type[t]["count"] += 1
            by_type[t]["market_value"] += float(p.market_value or 0)
            by_type[t]["unrealized_pnl"] += float(p.unrealized_pnl or 0)

        return {
            "total_positions": len(positions),
            "total_market_value": round(total_value, 4),
            "total_unrealized_pnl": round(total_pnl, 4),
            "by_type": by_type,
        }


class FuturesContractService:
    """Service for futures contract operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_contract(
        self,
        user_id: UUID,
        name: str,
        commodity_type: str,
        contract_size: float,
        contract_month: str,
        expiration_date: date,
        entry_price: float,
        position_type: str = "long",
        ticker: Optional[str] = None,
        margin_required: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> FuturesContract:
        if margin_required is None:
            margin_required = calculate_margin_requirement(contract_size, entry_price)

        contract = FuturesContract(
            user_id=user_id,
            name=name,
            commodity_type=commodity_type,
            ticker=ticker,
            contract_size=contract_size,
            contract_month=contract_month,
            expiration_date=expiration_date,
            position_type=position_type,
            entry_price=entry_price,
            margin_required=margin_required,
        )
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def get_contract(self, contract_id: UUID, user_id: UUID) -> Optional[FuturesContract]:
        return (
            self.db.query(FuturesContract)
            .filter(FuturesContract.id == contract_id, FuturesContract.user_id == user_id)
            .first()
        )

    def list_contracts(self, user_id: UUID) -> list[FuturesContract]:
        return (
            self.db.query(FuturesContract)
            .filter(FuturesContract.user_id == user_id)
            .all()
        )

    def update_contract(
        self, contract_id: UUID, user_id: UUID, **kwargs
    ) -> Optional[FuturesContract]:
        contract = self.get_contract(contract_id, user_id)
        if not contract:
            return None
        for key, value in kwargs.items():
            if hasattr(contract, key) and key not in ("id", "user_id"):
                setattr(contract, key, value)
        if "current_price" in kwargs and kwargs["current_price"] is not None:
            _, contract.unrealized_pnl, contract.market_value = calculate_futures_pnl(contract)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def delete_contract(self, contract_id: UUID, user_id: UUID) -> bool:
        contract = self.get_contract(contract_id, user_id)
        if not contract:
            return False
        self.db.delete(contract)
        self.db.commit()
        return True

    def get_expiration_alerts(
        self, user_id: UUID, days_ahead: int = 90
    ) -> list[dict]:
        """Get futures contracts expiring within `days_ahead`."""
        contracts = self.list_contracts(user_id)
        today = date.today()
        deadline = today + timedelta(days=days_ahead)
        alerts = []
        for c in contracts:
            if today <= c.expiration_date <= deadline:
                days_left = (c.expiration_date - today).days
                alerts.append(
                    {
                        "id": str(c.id),
                        "name": c.name,
                        "commodity_type": c.commodity_type,
                        "contract_month": c.contract_month,
                        "expiration_date": str(c.expiration_date),
                        "days_until_expiration": days_left,
                        "position_type": c.position_type,
                        "entry_price": float(c.entry_price),
                        "current_price": float(c.current_price) if c.current_price else None,
                        "unrealized_pnl": float(c.unrealized_pnl) if c.unrealized_pnl else None,
                    }
                )
        return sorted(alerts, key=lambda x: x["days_until_expiration"])

    def get_futures_summary(self, user_id: UUID) -> dict:
        """Aggregate futures contract statistics."""
        contracts = self.list_contracts(user_id)
        if not contracts:
            return {
                "total_contracts": 0,
                "total_market_value": 0.0,
                "total_unrealized_pnl": 0.0,
                "total_margin_required": 0.0,
            }
        total_value = sum(float(c.market_value or 0) for c in contracts)
        total_pnl = sum(float(c.unrealized_pnl or 0) for c in contracts)
        total_margin = sum(float(c.margin_required or 0) for c in contracts)
        return {
            "total_contracts": len(contracts),
            "total_market_value": round(total_value, 4),
            "total_unrealized_pnl": round(total_pnl, 4),
            "total_margin_required": round(total_margin, 4),
        }


class PreciousMetalsService:
    """Service for precious metals analytics."""

    def __init__(self, db: Session):
        self.db = db

    def get_precious_metals_prices(self) -> dict:
        """Get current gold, silver, platinum prices."""
        return fetch_precious_metals_prices()

    def get_historical_data(self, metal: str, days: int = 365) -> Optional[list]:
        """Get historical data for a precious metal."""
        ticker = COMMODITY_TICKERS.get(metal.lower())
        if not ticker:
            return None
        return fetch_commodity_history(ticker, days)

    def get_inflation_hedge_metrics(self) -> dict:
        """Compute inflation hedge metrics: gold vs USD, real rates."""
        try:
            import yfinance as yf

            gold = fetch_commodity_price("GC=F")
            dxy = fetch_commodity_price("DX-Y.NYB")
            # Proxy for 10-year real yield (TIPS)
            tips = fetch_commodity_price("TIP")

            gold_change_1m = None
            gold_change_1y = None
            try:
                gold_data = yf.Ticker("GC=F").history(period="1mo", auto_adjust=True)
                if not gold_data.empty and len(gold_data) >= 2:
                    gold_change_1m = round(
                        (gold_data["Close"].iloc[-1] - gold_data["Close"].iloc[0])
                        / gold_data["Close"].iloc[0]
                        * 100,
                        2,
                    )
                gold_data_y = yf.Ticker("GC=F").history(period="1y", auto_adjust=True)
                if not gold_data_y.empty and len(gold_data_y) >= 2:
                    gold_change_1y = round(
                        (gold_data_y["Close"].iloc[-1] - gold_data_y["Close"].iloc[0])
                        / gold_data_y["Close"].iloc[0]
                        * 100,
                        2,
                    )
            except Exception:
                pass

            return {
                "gold_price": gold,
                "dxy_index": dxy,
                "tips_price": tips,
                "gold_change_1m_pct": gold_change_1m,
                "gold_change_1y_pct": gold_change_1y,
                "inflation_hedge_signal": "strong" if (gold and dxy and gold > 0 and dxy > 0 and gold / dxy > 0.01) else "neutral",
            }
        except Exception as e:
            logger.warning(f"Failed to compute inflation hedge metrics: {e}")
            return {}
