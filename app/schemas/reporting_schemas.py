"""
Pydantic schemas for Institutional-Grade Reporting & Compliance (Phase 39).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# === Report Templates ===

class ReportTemplateBase(BaseModel):
    """Base report template schema."""
    name: str
    template_type: str = Field(pattern="^(monthly|quarterly|annual|gips)$")
    logo_url: Optional[str] = None
    primary_color: str = "#1a1a2e"
    secondary_color: str = "#16213e"
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    is_default: bool = False


class ReportTemplateCreate(ReportTemplateBase):
    """Create report template."""
    pass


class ReportTemplateUpdate(BaseModel):
    """Update report template."""
    name: Optional[str] = None
    template_type: Optional[str] = Field(None, pattern="^(monthly|quarterly|annual|gips)$")
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    is_default: Optional[bool] = None


class ReportTemplateResponse(ReportTemplateBase):
    """Report template response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Compliance Documents ===

class ComplianceDocumentBase(BaseModel):
    """Base compliance document schema."""
    document_type: str = Field(pattern="^(sec|fia|twse|gips)$")
    title: str
    content: str
    filing_date: Optional[datetime] = None
    period_covered: Optional[str] = None
    status: str = Field(default="draft", pattern="^(draft|pending|approved|filed)$")
    file_url: Optional[str] = None


class ComplianceDocumentCreate(ComplianceDocumentBase):
    """Create compliance document."""
    pass


class ComplianceDocumentUpdate(BaseModel):
    """Update compliance document."""
    document_type: Optional[str] = Field(None, pattern="^(sec|fia|twse|gips)$")
    title: Optional[str] = None
    content: Optional[str] = None
    filing_date: Optional[datetime] = None
    period_covered: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|pending|approved|filed)$")
    file_url: Optional[str] = None


class ComplianceDocumentResponse(ComplianceDocumentBase):
    """Compliance document response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === KYC Records ===

class KycRecordBase(BaseModel):
    """Base KYC record schema."""
    client_name: str
    client_email: Optional[str] = None
    risk_tolerance: str = Field(pattern="^(conservative|moderate|aggressive)$")
    investment_experience: str = Field(pattern="^(none|basic|intermediate|advanced)$")
    investment_horizon: str = Field(pattern="^(short|medium|long)$")
    annual_income_range: Optional[str] = None
    net_worth_range: Optional[str] = None
    liquidity_needs: str = Field(default="medium", pattern="^(low|medium|high)$")
    suitability_score: float = 0.0
    kyc_status: str = Field(default="pending", pattern="^(pending|approved|rejected)$")
    last_reviewed_at: Optional[datetime] = None
    document_urls: Optional[str] = None  # JSON array
    notes: Optional[str] = None


class KycRecordCreate(KycRecordBase):
    """Create KYC record."""
    pass


class KycRecordUpdate(BaseModel):
    """Update KYC record."""
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    risk_tolerance: Optional[str] = Field(None, pattern="^(conservative|moderate|aggressive)$")
    investment_experience: Optional[str] = Field(None, pattern="^(none|basic|intermediate|advanced)$")
    investment_horizon: Optional[str] = Field(None, pattern="^(short|medium|long)$")
    annual_income_range: Optional[str] = None
    net_worth_range: Optional[str] = None
    liquidity_needs: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    suitability_score: Optional[float] = None
    kyc_status: Optional[str] = Field(None, pattern="^(pending|approved|rejected)$")
    last_reviewed_at: Optional[datetime] = None
    document_urls: Optional[str] = None
    notes: Optional[str] = None


class KycRecordResponse(KycRecordBase):
    """KYC record response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Filing Reminders ===

class FilingReminderBase(BaseModel):
    """Base filing reminder schema."""
    filing_type: str = Field(pattern="^(sec|fia|twse|quarterly|annual)$")
    title: str
    deadline: datetime
    jurisdiction: str = Field(default="TWSE", pattern="^(SEC|FIA|TWSE)$")
    status: str = Field(default="pending", pattern="^(pending|sent|completed)$")


class FilingReminderCreate(FilingReminderBase):
    """Create filing reminder."""
    pass


class FilingReminderUpdate(BaseModel):
    """Update filing reminder."""
    filing_type: Optional[str] = Field(None, pattern="^(sec|fia|twse|quarterly|annual)$")
    title: Optional[str] = None
    deadline: Optional[datetime] = None
    jurisdiction: Optional[str] = Field(None, pattern="^(SEC|FIA|TWSE)$")
    status: Optional[str] = Field(None, pattern="^(pending|sent|completed)$")


class FilingReminderResponse(FilingReminderBase):
    """Filing reminder response."""
    id: str
    user_id: str
    notified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Report Generation ===

class ReportGenerationRequest(BaseModel):
    """Request to generate a professional report."""
    template_id: Optional[str] = None
    report_type: str = Field(pattern="^(monthly|quarterly|annual|gips|custom)$")
    period_start: datetime
    period_end: datetime
    include_holdings: bool = True
    include_performance: bool = True
    include_allocation: bool = True
    include_risk_metrics: bool = True
    include_gips_disclosure: bool = False


class ReportGenerationResponse(BaseModel):
    """Response after generating a report."""
    report_id: str
    download_url: str
    report_type: str
    generated_at: datetime
