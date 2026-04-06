"""
ESG & Sustainable Investing Service.
"""

import uuid
from datetime import date, datetime, timedelta
from typing import Optional


from sqlalchemy.orm import Session

from app.models.esg import (
    ControversyAlert,
    EsgScore,
    EsgTrend,
    ExclusionList,
)


class EsgService:
    """Service for ESG score operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_esg_score(
        self,
        user_id: uuid.UUID,
        ticker: str,
        company_name: str,
        esg_total_score: float,
        environmental_score: float,
        social_score: float,
        governance_score: float,
        rating_date: date,
        carbon_footprint_tons: Optional[float] = None,
        water_usage_m3: Optional[float] = None,
        waste_tons: Optional[float] = None,
        data_source: str = "msci",
    ) -> EsgScore:
        score = EsgScore(
            user_id=user_id,
            ticker=ticker.upper(),
            company_name=company_name,
            esg_total_score=esg_total_score,
            environmental_score=environmental_score,
            social_score=social_score,
            governance_score=governance_score,
            carbon_footprint_tons=carbon_footprint_tons,
            water_usage_m3=water_usage_m3,
            waste_tons=waste_tons,
            data_source=data_source,
            rating_date=rating_date,
        )
        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)
        return score

    def get_esg_score(self, user_id: uuid.UUID, ticker: str) -> Optional[EsgScore]:
        return (
            self.db.query(EsgScore)
            .filter(
                EsgScore.user_id == user_id,
                EsgScore.ticker == ticker.upper(),
            )
            .order_by(EsgScore.rating_date.desc())
            .first()
        )

    def get_portfolio_esg_summary(self, user_id: uuid.UUID) -> dict:
        scores = self.db.query(EsgScore).filter(EsgScore.user_id == user_id).all()
        if not scores:
            return {
                "portfolio_esg_score": 0.0,
                "portfolio_env_score": 0.0,
                "portfolio_social_score": 0.0,
                "portfolio_gov_score": 0.0,
                "total_carbon_tons": 0.0,
                "total_water_m3": 0.0,
                "total_waste_tons": 0.0,
                "holdings_count": 0,
                "screened_count": 0,
                "esg_rating_distribution": {},
            }

        n = len(scores)
        avg_esg = sum(s.esg_total_score for s in scores) / n
        avg_env = sum(s.environmental_score for s in scores) / n
        avg_social = sum(s.social_score for s in scores) / n
        avg_gov = sum(s.governance_score for s in scores) / n

        total_carbon = sum(s.carbon_footprint_tons or 0 for s in scores)
        total_water = sum(s.water_usage_m3 or 0 for s in scores)
        total_waste = sum(s.waste_tons or 0 for s in scores)

        # ESG rating distribution (Morningstar-style)
        rating_dist: dict[str, int] = {}
        for s in scores:
            rating = self._score_to_rating(s.esg_total_score)
            rating_dist[rating] = rating_dist.get(rating, 0) + 1

        exclusions = (
            self.db.query(ExclusionList)
            .filter(ExclusionList.user_id == user_id, ExclusionList.is_active)
            .count()
        )

        return {
            "portfolio_esg_score": round(avg_esg, 2),
            "portfolio_env_score": round(avg_env, 2),
            "portfolio_social_score": round(avg_social, 2),
            "portfolio_gov_score": round(avg_gov, 2),
            "total_carbon_tons": round(total_carbon, 4),
            "total_water_m3": round(total_water, 4),
            "total_waste_tons": round(total_waste, 4),
            "holdings_count": n,
            "screened_count": exclusions,
            "esg_rating_distribution": rating_dist,
        }

    def get_esg_trend(self, user_id: uuid.UUID, ticker: str, months: int = 12) -> list[dict]:
        cutoff = date.today() - timedelta(days=months * 30)
        trends = (
            self.db.query(EsgTrend)
            .filter(
                EsgTrend.user_id == user_id,
                EsgTrend.ticker == ticker.upper(),
                EsgTrend.month >= cutoff,
            )
            .order_by(EsgTrend.month.asc())
            .all()
        )
        return [
            {
                "month": t.month,
                "esg_total_score": float(t.esg_total_score),
                "environmental_score": float(t.environmental_score),
                "social_score": float(t.social_score),
                "governance_score": float(t.governance_score),
            }
            for t in trends
        ]

    def _score_to_rating(self, score: float) -> str:
        if score >= 85:
            return "AAA"
        elif score >= 75:
            return "AA"
        elif score >= 65:
            return "A"
        elif score >= 55:
            return "BBB"
        elif score >= 45:
            return "BB"
        elif score >= 35:
            return "B"
        else:
            return "CCC"


class ControversyAlertService:
    """Service for controversy alerts."""

    # Default screening lists
    WEAPONS_TICKERS = {"LMT", "BA", "NOC", "RTX", "GD", "LHX"}
    TOBACCO_TICKERS = {"MO", "PM", "BTI", "STG"}
    GAMBLING_TICKERS = {"MGM", "WYNN", "LVS", "PENN", "DKNG"}

    def __init__(self, db: Session):
        self.db = db

    def check_controversies(self, user_id: uuid.UUID, ticker: str) -> list[ControversyAlert]:
        ticker_upper = ticker.upper()
        alerts: list[ControversyAlert] = []

        # Check negative screening lists
        if ticker_upper in self.WEAPONS_TICKERS:
            alerts.append(self._create_or_get_alert(user_id, ticker_upper, "Weapons", "high",
                "Company involved in weapons/defense manufacturing",
                "Defense contractor detected in negative screening list"))
        if ticker_upper in self.TOBACCO_TICKERS:
            alerts.append(self._create_or_get_alert(user_id, ticker_upper, "Tobacco", "high",
                "Tobacco product manufacturing", "Tobacco company in exclusion list"))
        if ticker_upper in self.GAMBLING_TICKERS:
            alerts.append(self._create_or_get_alert(user_id, ticker_upper, "Gambling", "medium",
                "Gambling operations", "Gambling sector company detected"))

        return alerts

    def _create_or_get_alert(
        self,
        user_id: uuid.UUID,
        ticker: str,
        controversy_type: str,
        severity: str,
        headline: str,
        description: str,
    ) -> ControversyAlert:
        existing = (
            self.db.query(ControversyAlert)
            .filter(
                ControversyAlert.user_id == user_id,
                ControversyAlert.ticker == ticker,
                ControversyAlert.controversy_type == controversy_type,
                ControversyAlert.status == "active",
            )
            .first()
        )
        if existing:
            return existing

        alert = ControversyAlert(
            user_id=user_id,
            ticker=ticker,
            company_name=ticker,
            controversy_type=controversy_type.lower().replace(" ", "_"),
            severity=severity,
            headline=headline,
            description=description,
            alert_date=date.today(),
            status="active",
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get_active_alerts(self, user_id: uuid.UUID) -> list[ControversyAlert]:
        return (
            self.db.query(ControversyAlert)
            .filter(
                ControversyAlert.user_id == user_id,
                ControversyAlert.status == "active",
            )
            .order_by(ControversyAlert.alert_date.desc())
            .all()
        )

    def dismiss_alert(self, alert_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ControversyAlert]:
        alert = (
            self.db.query(ControversyAlert)
            .filter(ControversyAlert.id == alert_id, ControversyAlert.user_id == user_id)
            .first()
        )
        if not alert:
            return None
        alert.status = "dismissed"
        self.db.commit()
        self.db.refresh(alert)
        return alert


class CarbonFootprintService:
    """Service for carbon footprint calculations."""

    BENCHMARK_CARBON_PER_MILLION_USD = 150.0  # avg tons CO2 per $1M market cap

    def __init__(self, db: Session):
        self.db = db

    def get_portfolio_carbon(self, user_id: uuid.UUID) -> dict:
        scores = self.db.query(EsgScore).filter(EsgScore.user_id == user_id).all()
        total = sum(s.carbon_footprint_tons or 0 for s in scores)

        carbon_by_sector: dict[str, float] = {}
        highest_ticker = ""
        highest_carbon = 0.0
        lowest_ticker = ""
        lowest_carbon = float("inf")

        for s in scores:
            cf = s.carbon_footprint_tons or 0
            if cf > highest_carbon:
                highest_carbon = cf
                highest_ticker = s.ticker
            if cf < lowest_carbon and cf > 0:
                lowest_carbon = cf
                lowest_ticker = s.ticker

        benchmark = len(scores) * self.BENCHMARK_CARBON_PER_MILLION_USD
        vs_benchmark_pct = ((total - benchmark) / benchmark * 100) if benchmark > 0 else 0

        return {
            "total_carbon_tons": round(total, 4),
            "carbon_by_sector": carbon_by_sector,
            "benchmark_average_tons": round(benchmark, 4),
            "vs_benchmark_pct": round(vs_benchmark_pct, 2),
            "highest_carbon_ticker": highest_ticker,
            "lowest_carbon_ticker": lowest_ticker,
        }


class ExclusionListService:
    """Service for managing exclusion lists."""

    def __init__(self, db: Session):
        self.db = db

    def create_entry(
        self,
        user_id: uuid.UUID,
        list_type: str,
        sector: Optional[str] = None,
        ticker: Optional[str] = None,
        company_name: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> ExclusionList:
        entry = ExclusionList(
            user_id=user_id,
            list_type=list_type,
            sector=sector,
            ticker=ticker.upper() if ticker else None,
            company_name=company_name,
            reason=reason,
            is_active=True,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_exclusions(self, user_id: uuid.UUID, list_type: Optional[str] = None) -> list[ExclusionList]:
        q = self.db.query(ExclusionList).filter(ExclusionList.user_id == user_id, ExclusionList.is_active)
        if list_type:
            q = q.filter(ExclusionList.list_type == list_type)
        return q.all()

    def update_entry(
        self,
        entry_id: uuid.UUID,
        user_id: uuid.UUID,
        **kwargs,
    ) -> Optional[ExclusionList]:
        entry = (
            self.db.query(ExclusionList)
            .filter(ExclusionList.id == entry_id, ExclusionList.user_id == user_id)
            .first()
        )
        if not entry:
            return None
        for key, val in kwargs.items():
            if val is not None and hasattr(entry, key):
                setattr(entry, key, val)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete_entry(self, entry_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        entry = (
            self.db.query(ExclusionList)
            .filter(ExclusionList.id == entry_id, ExclusionList.user_id == user_id)
            .first()
        )
        if not entry:
            return False
        entry.is_active = False
        self.db.commit()
        return True


class EsgPortfolioService:
    """High-level ESG portfolio operations."""

    def __init__(self, db: Session):
        self.db = db
        self.esg_service = EsgService(db)
        self.exclusion_service = ExclusionListService(db)

    def get_sustainable_alternatives(
        self, user_id: uuid.UUID, ticker: str
    ) -> list[dict]:
        """Return sustainable alternatives for a given ticker."""
        # Mock alternatives — in production, would query MSCI/Sustainalytics API
        alternatives_map = {
            "XOM": {"ticker": "NEE", "name": "NextEra Energy", "esg_score": 72, "sector": "Utilities"},
            "CVX": {"ticker": "ENPH", "name": "Enphase Energy", "esg_score": 78, "sector": "Clean Tech"},
            "COP": {"ticker": "FSLR", "name": "First Solar", "esg_score": 75, "sector": "Clean Tech"},
            "BA": {"ticker": "HON", "name": "Honeywell", "esg_score": 68, "sector": "Industrials"},
        }

        ticker_upper = ticker.upper()
        if ticker_upper not in alternatives_map:
            return []

        alt = alternatives_map[ticker_upper]
        original_score = self.esg_service.get_esg_score(user_id, ticker_upper)
        orig_score_val = float(original_score.esg_total_score) if original_score else 50.0

        return [
            {
                "original_ticker": ticker_upper,
                "original_esg_score": orig_score_val,
                "alternative_ticker": alt["ticker"],
                "alternative_name": alt["name"],
                "alternative_esg_score": float(alt["esg_score"]),
                "sector": alt["sector"],
                "reason": f"Same sector with higher ESG score ({alt['esg_score']} vs {orig_score_val:.0f})",
            }
        ]

    def screen_portfolio(self, user_id: uuid.UUID) -> dict:
        """Screen portfolio against user's exclusion rules."""
        scores = self.db.query(EsgScore).filter(EsgScore.user_id == user_id).all()
        exclusions = self.exclusion_service.get_exclusions(user_id)

        excluded_tickers = {e.ticker for e in exclusions if e.ticker}
        excluded_sectors = {e.sector for e in exclusions if e.sector}

        flagged = []
        screened = []
        excluded_value = 0.0

        for s in scores:
            if s.ticker in excluded_tickers:
                flagged.append({"ticker": s.ticker, "company_name": s.company_name, "reason": "ticker_excluded"})
            elif any(sec.lower() in s.company_name.lower() for sec in excluded_sectors):
                flagged.append({"ticker": s.ticker, "company_name": s.company_name, "reason": "sector_excluded"})
            else:
                screened.append({"ticker": s.ticker, "company_name": s.company_name, "esg_score": float(s.esg_total_score)})

        compliance_score = (len(screened) / len(scores) * 100) if scores else 100.0

        return {
            "total_holdings": len(scores),
            "flagged_holdings": flagged,
            "screened_holdings": screened,
            "compliance_score": round(compliance_score, 2),
            "excluded_value": excluded_value,
        }
