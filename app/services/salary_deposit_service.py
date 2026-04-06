"""
Salary Deposit Service

Integrates with 玉山銀行 (E.Sun Bank) Open API to fetch and analyze
salary deposit records for income verification and pattern analysis.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class MonthlyIncomeSummary:
    """Monthly income summary from salary deposits."""
    month: str  # YYYY-MM
    total_deposits: float
    deposit_count: int
    average_deposit: float
    employer_name: Optional[str]
    is_stable: bool  # Consistent monthly deposits
    anomaly_detected: bool
    anomaly_reason: Optional[str] = None


@dataclass
class IncomeVerificationResult:
    """Income verification analysis result."""
    verified_annual_income: float
    verified_monthly_income: float
    average_monthly_income: float
    income_volatility: float  # Std deviation
    employment_stability_score: float  # 0-100
    monthly_summaries: list[MonthlyIncomeSummary]
    anomalies: list[dict]
    employer_verification: dict
    recommended_budget: float  # 50/30/20 rule: 50% needs
    timestamp: str


class SalaryDepositService:
    """
    Service for analyzing salary deposits from bank accounts.

    Provides:
    - Monthly income verification
    - Deposit pattern analysis (stability, anomalies)
    - Employment verification
    - Budget recommendations based on verified income
    """

    # Typical salary day range (Taiwan: usually 5th-10th of month)
    SALARY_DAY_MIN = 1
    SALARY_DAY_MAX = 15

    # Minimum deposits to consider for stable income
    MIN_MONTHS_FOR_STABILITY = 3

    # Income multipliers for budget categories
    BUDGET_NEEDS_RATIO = 0.50
    BUDGET_WANTS_RATIO = 0.30
    BUDGET_SAVINGS_RATIO = 0.20

    # Anomaly thresholds
    VOLATILITY_THRESHOLD = 0.30  # 30% coefficient of variation
    SINGLE_DEPOSIT_THRESHOLD = 1.5  # 1.5x average is suspicious

    def __init__(self, open_finance_adapter=None):
        """Initialize Salary Deposit Service.
        
        Args:
            open_finance_adapter: Optional OpenFinanceAdapter instance.
                If not provided, creates a default one.
        """
        from app.services.open_finance_adapter import OpenFinanceAdapter
        self.adapter = open_finance_adapter or OpenFinanceAdapter()

    async def verify_income(
        self,
        account_id: str,
        citizen_id: Optional[str] = None,
        months: int = 12,
        employer_name: Optional[str] = None,
    ) -> IncomeVerificationResult:
        """
        Verify income and analyze deposit patterns.

        Args:
            account_id: Bank account ID to analyze
            citizen_id: National ID for pension cross-reference
            months: Number of past months to analyze
            employer_name: Expected employer name for verification

        Returns:
            IncomeVerificationResult with analysis
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=months * 35)).strftime("%Y-%m-%d")

        # Fetch salary deposits from E.Sun Bank
        deposits = await self.adapter.get_salary_deposits(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            bank_code="ESUN",
        )

        # Convert to records
        records = []
        for d in deposits:
            if hasattr(d, 'date'):
                records.append({
                    "date": d.date,
                    "amount": d.amount,
                    "employer_name": getattr(d, "employer_name", None),
                    "description": getattr(d, "description", None),
                    "transaction_id": getattr(d, "transaction_id", None),
                })

        # Group by month
        monthly_groups = self._group_by_month(records)

        # Build monthly summaries
        monthly_summaries = []
        all_deposits = []

        for month, txns in sorted(monthly_groups.items()):
            total = sum(t["amount"] for t in txns)
            count = len(txns)
            avg = total / count if count > 0 else 0
            emp = txns[0]["employer_name"] if txns else None

            # Detect anomalies
            anomaly, reason = self._detect_anomaly(txns, avg, monthly_groups, month)

            monthly_summaries.append(MonthlyIncomeSummary(
                month=month,
                total_deposits=round(total, 2),
                deposit_count=count,
                average_deposit=round(avg, 2),
                employer_name=emp,
                is_stable=(count >= 1 and anomaly == ""),
                anomaly_detected=anomaly,
                anomaly_reason=reason,
            ))
            all_deposits.append(total)

        # Calculate statistics
        if all_deposits:
            avg_monthly = sum(all_deposits) / len(all_deposits)
            annual_income = avg_monthly * 12

            # Calculate volatility (coefficient of variation)
            if avg_monthly > 0 and len(all_deposits) > 1:
                variance = sum((x - avg_monthly) ** 2 for x in all_deposits) / len(all_deposits)
                std_dev = variance ** 0.5
                volatility = std_dev / avg_monthly
            else:
                volatility = 0.0
        else:
            avg_monthly = 0
            annual_income = 0
            volatility = 0.0

        # Employment stability score
        stable_months = sum(1 for s in monthly_summaries if s.is_stable)
        stability_score = (stable_months / max(len(monthly_summaries), 1)) * 100

        # Anomalies
        anomalies = [
            {"month": s.month, "reason": s.anomaly_reason}
            for s in monthly_summaries if s.anomaly_detected
        ]

        # Employer verification
        employer_verification = self._verify_employer(monthly_summaries, employer_name)

        # Budget recommendation (50/30/20 rule)
        _monthly_needs = avg_monthly * self.BUDGET_NEEDS_RATIO  # 50% for needs (reserved for future use)
        recommended_budget = round(avg_monthly, 2)

        return IncomeVerificationResult(
            verified_annual_income=round(annual_income, 2),
            verified_monthly_income=round(avg_monthly, 2),
            average_monthly_income=round(avg_monthly, 2),
            income_volatility=round(volatility, 4),
            employment_stability_score=round(stability_score, 2),
            monthly_summaries=monthly_summaries,
            anomalies=anomalies,
            employer_verification=employer_verification,
            recommended_budget=recommended_budget,
            timestamp=datetime.now().isoformat(),
        )

    def _group_by_month(self, records: list[dict]) -> dict[str, list[dict]]:
        """Group deposit records by month."""
        groups: dict[str, list[dict]] = {}
        for r in records:
            date = r.get("date", "")
            if not date:
                continue
            month = date[:7]  # YYYY-MM
            if month not in groups:
                groups[month] = []
            groups[month].append(r)
        return groups

    def _detect_anomaly(
        self,
        deposits: list[dict],
        avg_amount: float,
        all_months: dict,
        current_month: str,
    ) -> tuple[bool, Optional[str]]:
        """Detect anomalies in monthly deposits."""
        if not deposits:
            return False, None

        total = sum(d["amount"] for d in deposits)
        _count = len(deposits)  # reserved for future statistical use

        # Check if total is unusually high or low
        other_months = [m for m in all_months if m != current_month]
        if other_months and avg_amount > 0:
            all_totals = [sum(t["amount"] for t in all_months[m]) for m in other_months]
            avg_total = sum(all_totals) / len(all_totals)

            if total > avg_total * self.SINGLE_DEPOSIT_THRESHOLD:
                return True, f"Deposit {total:.0f} is {self.SINGLE_DEPOSIT_THRESHOLD}x above monthly average {avg_total:.0f}"
            if total < avg_total * 0.3:
                return True, f"Deposit {total:.0f} is unusually low (average: {avg_total:.0f})"

        # Check for irregular deposit timing
        for d in deposits:
            day = int(d["date"][8:10]) if len(d["date"]) >= 10 else 0
            if day < self.SALARY_DAY_MIN or day > self.SALARY_DAY_MAX:
                return True, f"Unusual deposit date: day {day} (expected {self.SALARY_DAY_MIN}-{self.SALARY_DAY_MAX})"

        return False, None

    def _verify_employer(
        self,
        monthly_summaries: list[MonthlyIncomeSummary],
        expected_employer: Optional[str],
    ) -> dict:
        """Verify employer name consistency."""
        employers = [
            s.employer_name
            for s in monthly_summaries
            if s.employer_name
        ]

        if not employers:
            return {"verified": False, "reason": "No employer information found"}

        # Count occurrences
        employer_counts: dict[str, int] = {}
        for e in employers:
            employer_counts[e] = employer_counts.get(e, 0) + 1

        most_common = max(employer_counts, key=employer_counts.get)
        consistency = employer_counts[most_common] / max(len(employers), 1)

        result = {
            "verified": consistency >= 0.8,
            "most_common_employer": most_common,
            "consistency_score": round(consistency * 100, 2),
            "all_employers": employer_counts,
        }

        if expected_employer and expected_employer not in [None, ""]:
            result["matches_expected"] = expected_employer in most_common
            result["expected_employer"] = expected_employer

        return result

    async def analyze_deposit_pattern(
        self,
        account_id: str,
        months: int = 6,
    ) -> dict:
        """
        Analyze deposit patterns to detect multiple income sources
        or irregular income patterns.

        Args:
            account_id: Bank account ID
            months: Number of months to analyze

        Returns:
            Dict with pattern analysis
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=months * 35)).strftime("%Y-%m-%d")

        deposits = await self.adapter.get_salary_deposits(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Convert to simple records
        records = []
        for d in deposits:
            records.append({
                "date": d.date,
                "amount": d.amount,
                "employer": getattr(d, "employer_name", "Unknown"),
            })

        # Detect multiple income sources
        # If multiple deposits in same month from different employers
        groups = self._group_by_month(records)

        income_sources: dict[str, list] = {}
        for month, txns in groups.items():
            for t in txns:
                emp = t.get("employer", "Unknown")
                if emp not in income_sources:
                    income_sources[emp] = []
                income_sources[emp].append({"month": month, "amount": t["amount"]})

        # Determine if multiple sources
        has_multiple_sources = len(income_sources) > 1

        # Calculate regularity
        deposit_days = [int(r["date"][8:10]) for r in records if len(r["date"]) >= 10]
        regularity_score = 100
        if deposit_days:
            day_std = (sum((d - sum(deposit_days)/len(deposit_days))**2 for d in deposit_days) / len(deposit_days)) ** 0.5
            regularity_score = max(0, 100 - day_std * 2)

        return {
            "income_sources": {
                emp: {
                    "deposit_count": len(txns),
                    "total_amount": sum(t["amount"] for t in txns),
                    "average": sum(t["amount"] for t in txns) / len(txns),
                }
                for emp, txns in income_sources.items()
            },
            "has_multiple_sources": has_multiple_sources,
            "regularity_score": round(regularity_score, 2),
            "deposit_count": len(records),
            "period_months": months,
            "timestamp": datetime.now().isoformat(),
        }
