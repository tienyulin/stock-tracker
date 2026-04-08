"""
IPO Service — IPO CRUD and analytics.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.ipo import IPOAlert, IPOAlertType, IPORecord, IPOStatus
from app.models.models import User

logger = logging.getLogger(__name__)


class IPOService:
    def __init__(self, db: Session):
        self.db = db

    def create_ipo(self, user_id: str, data: dict) -> IPORecord:
        ipo = IPORecord(user_id=user_id, **data)
        self.db.add(ipo)
        self.db.commit()
        self.db.refresh(ipo)
        return ipo

    def get_ipo(self, ipo_id: str, user_id: str) -> Optional[IPORecord]:
        return (
            self.db.query(IPORecord)
            .filter(IPORecord.id == ipo_id, IPORecord.user_id == user_id)
            .first()
        )

    def list_ipos(
        self,
        user_id: str,
        status: Optional[str] = None,
        sector: Optional[str] = None,
        upcoming_only: bool = False,
    ) -> list[IPORecord]:
        q = self.db.query(IPORecord).filter(IPORecord.user_id == user_id, IPORecord.is_active)
        if status:
            q = q.filter(IPORecord.status == status)
        if sector:
            q = q.filter(IPORecord.sector == sector)
        if upcoming_only:
            q = q.filter(IPORecord.status.in_([IPOStatus.UPCOMING.value, IPOStatus.FILING.value]))
        return q.order_by(IPORecord.listing_date.asc()).all()

    def update_ipo(self, ipo_id: str, user_id: str, data: dict) -> Optional[IPORecord]:
        ipo = self.get_ipo(ipo_id, user_id)
        if not ipo:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(ipo, key, value)
        self.db.commit()
        self.db.refresh(ipo)
        return ipo

    def delete_ipo(self, ipo_id: str, user_id: str) -> bool:
        ipo = self.get_ipo(ipo_id, user_id)
        if not ipo:
            return False
        ipo.is_active = False
        self.db.commit()
        return True

    def get_upcoming_ipos(self, user_id: str) -> list[IPORecord]:
        return (
            self.db.query(IPORecord)
            .filter(
                IPORecord.user_id == user_id,
                IPORecord.status.in_([IPOStatus.UPCOMING.value, IPOStatus.FILING.value]),
            )
            .order_by(IPORecord.listing_date.asc())
            .all()
        )

    def get_ipo_analysis(self, ipo_id: str, user_id: str) -> dict:
        ipo = self.get_ipo(ipo_id, user_id)
        if not ipo:
            return {}
        return {
            "ipo_id": str(ipo.id),
            "company_name": ipo.company_name,
            "valuation_range": {
                "min": ipo.ipo_price_min,
                "max": ipo.ipo_price_max,
                "final": ipo.final_ipo_price,
            },
            "underwriter_info": {"name": ipo.underwriter},
            "peer_comparison": [],
            "risk_factors": [],
        }

    def compare_with_peers(self, ipo_id: str, user_id: str) -> list[dict]:
        ipo = self.get_ipo(ipo_id, user_id)
        if not ipo:
            return []
        return []

    def get_ipo_performance(self, ipo_id: str, user_id: str) -> dict:
        ipo = self.get_ipo(ipo_id, user_id)
        if not ipo:
            return {}
        return {
            "ipo_id": str(ipo.id),
            "company_name": ipo.company_name,
            "status": ipo.status,
            "listing_date": ipo.listing_date,
            "first_trading_date": ipo.first_trading_date,
        }


class IPOCalendarService:
    def __init__(self, db: Session):
        self.db = db

    def get_calendar(self, user_id: str) -> dict:
        service = IPOService(self.db)
        ipos = service.list_ipos(user_id)
        return {"ipos": ipos, "total": len(ipos)}

    def get_upcoming_deadlines(self, user_id: str) -> list[dict]:
        service = IPOService(self.db)
        ipos = service.list_ipos(user_id)
        now = datetime.utcnow()
        upcoming = []
        for ipo in ipos:
            if ipo.application_deadline and ipo.application_deadline > now:
                days_left = (ipo.application_deadline - now).days
                if days_left <= 14:
                    upcoming.append(
                        {
                            "company_name": ipo.company_name,
                            "deadline": ipo.application_deadline,
                            "days_left": days_left,
                        }
                    )
        return upcoming

    def get_first_day_stats(self, user_id: str) -> dict:
        return {}


class IPOAlertService:
    def __init__(self, db: Session):
        self.db = db

    def create_alert(self, user_id: str, data: dict) -> IPOAlert:
        alert = IPOAlert(user_id=user_id, **data)
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get_alerts(self, user_id: str, active_only: bool = True) -> list[IPOAlert]:
        q = self.db.query(IPOAlert).filter(IPOAlert.user_id == user_id)
        if active_only:
            q = q.filter(IPOAlert.is_active)
        return q.order_by(IPOAlert.created_at.desc()).all()

    def delete_alert(self, alert_id: str, user_id: str) -> bool:
        alert = (
            self.db.query(IPOAlert)
            .filter(IPOAlert.id == alert_id, IPOAlert.user_id == user_id)
            .first()
        )
        if not alert:
            return False
        alert.is_active = False
        self.db.commit()
        return True

    def check_deadline_alerts(self, user_id: str) -> list[dict]:
        service = IPOService(self.db)
        ipos = service.list_ipos(user_id)
        triggered = []
        now = datetime.utcnow()
        for ipo in ipos:
            if not ipo.application_deadline:
                continue
            if 0 < (ipo.application_deadline - now).days <= 3:
                triggered.append(
                    {
                        "ipo_id": str(ipo.id),
                        "company_name": ipo.company_name,
                        "deadline": ipo.application_deadline,
                        "message": f"IPO {ipo.company_name} application deadline in {(ipo.application_deadline - now).days} days",
                    }
                )
        return triggered
