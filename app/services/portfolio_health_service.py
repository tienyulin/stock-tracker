"""
Portfolio Health Score calculation service.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional
import math

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import User, UserHolding, PortfolioHealthScore, HealthScoreAlert
from app.models.portfolio_health import PortfolioHealthScore, HealthScoreAlert


class PortfolioHealthService:
    """Service for calculating portfolio health scores."""

    def __init__(self, db: Session, user_id: uuid.UUID):
        self.db = db
        self.user_id = user_id

    def calculate_diversification_score(self) -> float:
        """
        Calculate diversification score (0-100).
        Factors: number of holdings, sector spread, asset type spread
        """
        holdings = self.db.query(UserHolding).filter(
            UserHolding.user_id == self.user_id
        ).all()

        if not holdings:
            return 0.0

        # Number of holdings score (up to 20 points)
        num_holdings = len(holdings)
        holdings_score = min(20.0, num_holdings * 4)  # 5+ holdings = max

        # Sector spread score (up to 40 points)
        sectors = set(h.sector for h in holdings if h.sector)
        sector_score = min(40.0, len(sectors) * 10)  # 4+ sectors = max

        # Asset type spread score (up to 40 points)
        asset_types = set(h.asset_type for h in holdings)
        asset_score = min(40.0, len(asset_types) * 13.3)  # 3+ types = max

        return holdings_score + sector_score + asset_score

    def calculate_risk_score(self) -> float:
        """
        Calculate risk score (0-100).
        Lower risk = higher score. Based on beta, volatility proxies.
        """
        holdings = self.db.query(UserHolding).filter(
            UserHolding.user_id == self.user_id
        ).all()

        if not holdings:
            return 0.0

        # Simplified risk calculation based on beta and dividend yield
        # Higher beta = higher risk = lower score
        # Higher dividend yield = more stable = higher score

        total_invested = sum(h.quantity * h.avg_cost for h in holdings)
        if total_invested <= 0:
            return 50.0  # Neutral

        weighted_beta = 0.0
        weighted_div_yield = 0.0

        for h in holdings:
            value = h.quantity * h.avg_cost
            weight = value / total_invested
            # Assume beta ~1.0 for stocks, 0.5 for dividends
            beta = 1.0 if h.asset_type == "STOCK" else 0.5
            weighted_beta += beta * weight
            weighted_div_yield += (h.dividend_yield or 0) * weight

        # Beta contribution: 1.0 beta = 50 score, lower beta = higher score
        beta_score = max(0, 100 - (weighted_beta - 0.8) * 50)

        # Dividend yield contribution (up to 20 bonus points)
        div_score = min(20, weighted_div_yield * 10)

        return min(100, beta_score + div_score)

    def calculate_performance_score(self) -> float:
        """
        Calculate performance score (0-100).
        Based on risk-adjusted returns (simplified Sharpe ratio proxy).
        """
        holdings = self.db.query(UserHolding).filter(
            UserHolding.user_id == self.user_id
        ).all()

        if not holdings:
            return 0.0

        total_invested = sum(h.quantity * h.avg_cost for h in holdings)
        if total_invested <= 0:
            return 50.0  # Neutral

        # Simplified performance: assume portfolio value is based on cost
        # In real implementation, would compare current value vs cost
        # For now, return a neutral score based on number of positive holdings

        positive_holdings = sum(
            1 for h in holdings
            if h.dividend_yield and h.dividend_yield > 0
        )

        # Base score from positive performers
        perf_score = (positive_holdings / len(holdings)) * 70 if holdings else 0

        # Bonus for consistent dividends (up to 30 points)
        avg_div = sum(h.dividend_yield or 0 for h in holdings) / len(holdings)
        div_bonus = min(30, avg_div * 10)

        return min(100, perf_score + div_bonus)

    def calculate_trend_score(self) -> float:
        """
        Calculate trend score (0-100).
        Based on momentum and recent performance.
        """
        # Get historical scores
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_scores = self.db.query(PortfolioHealthScore).filter(
            PortfolioHealthScore.user_id == self.user_id,
            PortfolioHealthScore.calculated_at >= week_ago
        ).order_by(PortfolioHealthScore.calculated_at.desc()).limit(7).all()

        if not recent_scores:
            return 50.0  # Neutral if no history

        # Calculate trend from recent scores
        if len(recent_scores) >= 2:
            latest = recent_scores[0].score
            oldest = recent_scores[-1].score
            trend_change = latest - oldest
            # Trend score: positive change = higher, negative = lower
            trend_score = 50 + (trend_change * 5)  # Each point change = 5 trend points
        else:
            trend_score = 50.0

        # Average of recent scores (up to 50 points)
        avg_score = sum(s.score for s in recent_scores) / len(recent_scores)
        avg_contribution = avg_score * 0.5

        return min(100, max(0, trend_score + avg_contribution - 50))

    def calculate_health_score(self) -> dict:
        """
        Calculate overall health score with breakdown.
        Returns dict with overall score and component scores.
        """
        div_score = self.calculate_diversification_score()
        risk_score = self.calculate_risk_score()
        perf_score = self.calculate_performance_score()
        trend_score = self.calculate_trend_score()

        # Weighted average (weights sum to 1.0)
        weights = {
            "diversification": 0.25,
            "risk": 0.25,
            "performance": 0.30,
            "trend": 0.20
        }

        overall_score = (
            div_score * weights["diversification"] +
            risk_score * weights["risk"] +
            perf_score * weights["performance"] +
            trend_score * weights["trend"]
        )

        return {
            "score": round(overall_score, 1),
            "diversification_score": round(div_score, 1),
            "risk_score": round(risk_score, 1),
            "performance_score": round(perf_score, 1),
            "trend_score": round(trend_score, 1),
            "calculated_at": datetime.utcnow()
        }

    def save_health_score(self, score_data: dict) -> PortfolioHealthScore:
        """Save a health score record to database."""
        score = PortfolioHealthScore(
            user_id=self.user_id,
            score=score_data["score"],
            diversification_score=score_data["diversification_score"],
            risk_score=score_data["risk_score"],
            performance_score=score_data["performance_score"],
            trend_score=score_data["trend_score"]
        )
        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)
        return score

    def get_health_history(self, days: int = 30) -> list:
        """Get historical health scores for the user."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        scores = self.db.query(PortfolioHealthScore).filter(
            PortfolioHealthScore.user_id == self.user_id,
            PortfolioHealthScore.calculated_at >= cutoff
        ).order_by(PortfolioHealthScore.calculated_at.asc()).all()
        return scores

    def check_score_alerts(self) -> list:
        """Check if any health score alerts should be triggered."""
        alerts = self.db.query(HealthScoreAlert).filter(
            HealthScoreAlert.user_id == self.user_id,
            HealthScoreAlert.is_active == True
        ).all()

        triggered = []
        current_score = self.calculate_health_score()["score"]

        for alert in alerts:
            if current_score < alert.threshold:
                triggered.append({
                    "alert_id": alert.id,
                    "threshold": alert.threshold,
                    "current_score": current_score
                })

        return triggered
