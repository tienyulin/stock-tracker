"""
Automated Trading Service — core engine for rule-based and AI-signal trading.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.trading_rule import (
    AutomationLog,
    BrokerConnectionExtended,
    OrderType,
    RuleStatus,
    RuleType,
    TradingRule,
)

logger = logging.getLogger(__name__)


class AutomatedTradingService:
    """Service for automated trading rules and execution."""

    def __init__(self, db: Session):
        self.db = db

    # ─── Trading Rules ────────────────────────────────────────────────────────

    def create_rule(
        self,
        user_id: uuid.UUID,
        name: str,
        rule_type: str,
        symbol: Optional[str] = None,
        target_quantity: Optional[float] = None,
        target_percentage: Optional[float] = None,
        order_type: str = OrderType.MARKET.value,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        max_order_value: Optional[float] = None,
        max_daily_loss: Optional[float] = None,
        broker_connection_id: Optional[str] = None,
        schedule_cron: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        description: Optional[str] = None,
    ) -> TradingRule:
        rule = TradingRule(
            user_id=user_id,
            name=name,
            description=description,
            rule_type=rule_type,
            symbol=symbol,
            target_quantity=target_quantity,
            target_percentage=target_percentage,
            order_type=order_type,
            limit_price=limit_price,
            stop_price=stop_price,
            max_order_value=max_order_value,
            max_daily_loss=max_daily_loss,
            broker_connection_id=broker_connection_id,
            schedule_cron=schedule_cron,
            expires_at=expires_at,
            status=RuleStatus.ACTIVE.value,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_rules(
        self,
        user_id: uuid.UUID,
        active_only: bool = True,
        rule_type: Optional[str] = None,
    ) -> list[TradingRule]:
        query = select(TradingRule).where(TradingRule.user_id == user_id)
        if active_only:
            query = query.where(TradingRule.is_active == True)  # noqa: E712
        if rule_type:
            query = query.where(TradingRule.rule_type == rule_type)
        query = query.order_by(TradingRule.created_at.desc())
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_rule(self, user_id: uuid.UUID, rule_id: uuid.UUID) -> Optional[TradingRule]:
        result = self.db.execute(
            select(TradingRule).where(
                TradingRule.id == rule_id,
                TradingRule.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    def update_rule(
        self,
        rule_id: uuid.UUID,
        user_id: uuid.UUID,
        **kwargs,
    ) -> Optional[TradingRule]:
        rule = self.get_rule(user_id, rule_id)
        if not rule:
            return None
        for key, value in kwargs.items():
            if hasattr(rule, key) and key not in ("id", "user_id", "created_at"):
                setattr(rule, key, value)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def pause_rule(self, user_id: uuid.UUID, rule_id: uuid.UUID) -> Optional[TradingRule]:
        return self.update_rule(rule_id, user_id, status=RuleStatus.PAUSED.value, is_active=False)

    def resume_rule(self, user_id: uuid.UUID, rule_id: uuid.UUID) -> Optional[TradingRule]:
        return self.update_rule(rule_id, user_id, status=RuleStatus.ACTIVE.value, is_active=True)

    def delete_rule(self, user_id: uuid.UUID, rule_id: uuid.UUID) -> bool:
        rule = self.get_rule(user_id, rule_id)
        if not rule:
            return False
        self.db.delete(rule)
        self.db.commit()
        return True

    # ─── Execution ─────────────────────────────────────────────────────────────

    def check_and_trigger_rules(
        self,
        user_id: uuid.UUID,
        trigger_reason: str,
        symbol: Optional[str] = None,
    ) -> list[AutomationLog]:
        """
        Check all active rules and trigger any that match the given conditions.
        Returns list of created execution logs.
        """
        rules = self.get_rules(user_id, active_only=True)
        triggered_logs = []

        for rule in rules:
            if self._rule_matches(rule, trigger_reason, symbol):
                log = self._execute_rule(rule, trigger_reason)
                if log:
                    triggered_logs.append(log)

        return triggered_logs

    def _rule_matches(
        self, rule: TradingRule, trigger_reason: str, symbol: Optional[str]
    ) -> bool:
        """Check if a rule's conditions match the trigger."""
        # Symbol must match if specified
        if rule.symbol and rule.symbol != symbol:
            return False

        # Check rule type-specific matching
        if rule.rule_type == RuleType.AI_SIGNAL.value:
            return "ai_signal" in trigger_reason.lower()
        elif rule.rule_type == RuleType.PRICE_TRIGGER.value:
            return "price" in trigger_reason.lower()
        elif rule.rule_type == RuleType.INDICATOR_SIGNAL.value:
            return any(kw in trigger_reason.lower() for kw in ["rsi", "macd", "ma", "indicator"])
        elif rule.rule_type == RuleType.REBALANCE.value:
            return "rebalance" in trigger_reason.lower()
        elif rule.rule_type == RuleType.SCHEDULE.value:
            return True  # Schedule-based, checked separately

        return True

    def _execute_rule(self, rule: TradingRule, trigger_reason: str) -> Optional[AutomationLog]:
        """Execute a single rule and log the result."""
        try:
            # Check daily loss limit
            if rule.max_daily_loss:
                daily_loss = self._get_daily_loss(rule.user_id)
                if daily_loss >= rule.max_daily_loss:
                    log = self._create_log(
                        rule, "skipped", trigger_reason, notes="Daily loss limit reached"
                    )
                    return log

            # Determine action based on rule type
            if rule.rule_type == RuleType.AI_SIGNAL.value:
                action = self._parse_ai_signal_action(trigger_reason)
            elif rule.rule_type == RuleType.REBALANCE.value:
                action = "rebalance"
            else:
                action = "trade"

            # Execute (mock for now — real implementation would call broker API)
            order_value = self._mock_execute(
                rule, action, rule.symbol, rule.target_quantity, rule.order_type
            )

            log = self._create_log(
                rule, "success", trigger_reason,
                action_taken=action,
                symbol=rule.symbol,
                quantity=rule.target_quantity,
                order_value=order_value,
            )

            # Update rule state
            rule.trigger_count += 1
            rule.last_triggered_at = datetime.utcnow()
            rule.status = RuleStatus.TRIGGERED.value
            self.db.commit()

            return log

        except Exception as e:
            logger.error(f"Rule execution failed for rule {rule.id}: {e}")
            log = self._create_log(
                rule, "failed", trigger_reason, error_message=str(e)
            )
            return log

    def _parse_ai_signal_action(self, trigger_reason: str) -> str:
        """Parse AI signal to determine buy/sell action."""
        reason_lower = trigger_reason.lower()
        if "sell" in reason_lower or "short" in reason_lower:
            return "sell"
        elif "buy" in reason_lower or "long" in reason_lower:
            return "buy"
        return "hold"

    def _mock_execute(
        self,
        rule: TradingRule,
        action: str,
        symbol: Optional[str],
        quantity: Optional[float],
        order_type: str,
    ) -> Optional[float]:
        """Mock order execution — real implementation calls broker API."""
        # In production: call Alpaca/IBKR API
        if not symbol or not quantity:
            return None
        # Mock: assume $100 per share
        mock_price = 100.0
        return quantity * mock_price

    def _get_daily_loss(self, user_id: uuid.UUID) -> float:
        """Get total losses from today's automated trades."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = self.db.execute(
            select(AutomationLog).where(
                AutomationLog.user_id == user_id,
                AutomationLog.triggered_at >= today_start,
                AutomationLog.status == "success",
            )
        )
        logs = list(result.scalars().all())
        return sum(
            log.order_value or 0
            for log in logs
            if log.action_taken in ("sell", "stop_loss") and log.order_value
        )

    def _create_log(
        self,
        rule: TradingRule,
        status: str,
        trigger_reason: str,
        action_taken: str = "trade",
        symbol: Optional[str] = None,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        order_value: Optional[float] = None,
        error_message: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> AutomationLog:
        log = AutomationLog(
            user_id=rule.user_id,
            rule_id=rule.id,
            trigger_reason=trigger_reason,
            action_taken=action_taken,
            symbol=symbol,
            quantity=quantity,
            price=price,
            order_value=order_value,
            status=status,
            error_message=error_message,
            notes=notes,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    # ─── Execution History ─────────────────────────────────────────────────────

    def get_execution_logs(
        self,
        user_id: uuid.UUID,
        rule_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[AutomationLog]:
        query = select(AutomationLog).where(AutomationLog.user_id == user_id)
        if rule_id:
            query = query.where(AutomationLog.rule_id == rule_id)
        if start_date:
            query = query.where(AutomationLog.triggered_at >= start_date)
        if end_date:
            query = query.where(AutomationLog.triggered_at <= end_date)
        query = query.order_by(AutomationLog.triggered_at.desc()).limit(limit)
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_execution_stats(self, user_id: uuid.UUID) -> dict:
        """Get summary statistics for automated trading."""
        logs = self.get_execution_logs(user_id, limit=1000)
        total = len(logs)
        success = sum(1 for l in logs if l.status == "success")
        failed = sum(1 for l in logs if l.status == "failed")
        skipped = sum(1 for l in logs if l.status == "skipped")
        total_value = sum(l.order_value or 0 for l in logs if l.status == "success")
        return {
            "total_executions": total,
            "success": success,
            "failed": failed,
            "skipped": skipped,
            "success_rate": round(success / total * 100, 1) if total > 0 else 0,
            "total_trade_value": round(total_value, 2),
        }

    # ─── AI Signal Trigger ─────────────────────────────────────────────────────

    def trigger_from_ai_signal(
        self,
        user_id: uuid.UUID,
        symbol: str,
        action: str,  # "buy" or "sell"
        confidence: float,
        reason: str,
        quantity: Optional[float] = None,
    ) -> Optional[AutomationLog]:
        """
        Trigger automated trades from AI signal.
        Only executes if user has active AI_SIGNAL rule for this symbol.
        """
        rules = self.get_rules(user_id, rule_type=RuleType.AI_SIGNAL.value)
        matching_rules = [r for r in rules if r.symbol == symbol or r.symbol is None]

        if not matching_rules:
            logger.info(f"No AI signal rules found for user {user_id} symbol {symbol}")
            return None

        rule = matching_rules[0]  # Use first matching rule
        trigger_reason = f"ai_signal: {action} {symbol} (confidence: {confidence}) - {reason}"

        return self._execute_rule(rule, trigger_reason)
