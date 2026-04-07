"""
Institutional-Grade Reporting & Compliance API endpoints (Phase 39).
"""

from datetime import datetime
from typing import List, Optional
import uuid

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.database import DBSession
from app.core.rate_limiter import limiter, DEFAULT_RATE_LIMIT
from app.api.v1.auth import get_current_user
from app.models.models import (
    ReportTemplate,
    ComplianceDocument,
    KycRecord,
    FilingReminder,
    User,
)
from app.schemas.reporting_schemas import (
    ReportTemplateCreate,
    ReportTemplateUpdate,
    ReportTemplateResponse,
    ComplianceDocumentCreate,
    ComplianceDocumentUpdate,
    ComplianceDocumentResponse,
    KycRecordCreate,
    KycRecordUpdate,
    KycRecordResponse,
    FilingReminderCreate,
    FilingReminderUpdate,
    FilingReminderResponse,
    ReportGenerationRequest,
    ReportGenerationResponse,
)
from app.services.report_service import generate_professional_pdf, generate_excel_report

router = APIRouter(prefix="/reporting", tags=["Reporting & Compliance"])


# === Report Templates ===

@router.post("/templates", response_model=ReportTemplateResponse, status_code=201)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def create_report_template(
    template: ReportTemplateCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Create a new report template."""
    db_template = ReportTemplate(
        user_id=current_user.id,
        **template.model_dump(),
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


@router.get("/templates", response_model=List[ReportTemplateResponse])
@limiter.limit(DEFAULT_RATE_LIMIT)
async def list_report_templates(
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """List all report templates for the current user."""
    templates = db.query(ReportTemplate).filter(
        ReportTemplate.user_id == current_user.id
    ).all()
    return templates


@router.get("/templates/{template_id}", response_model=ReportTemplateResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_report_template(
    template_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Get a specific report template."""
    template = db.query(ReportTemplate).filter(
        ReportTemplate.id == template_id,
        ReportTemplate.user_id == current_user.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/templates/{template_id}", response_model=ReportTemplateResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def update_report_template(
    template_id: uuid.UUID,
    update: ReportTemplateUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Update a report template."""
    template = db.query(ReportTemplate).filter(
        ReportTemplate.id == template_id,
        ReportTemplate.user_id == current_user.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)
    
    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/{template_id}", status_code=204)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def delete_report_template(
    template_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Delete a report template."""
    template = db.query(ReportTemplate).filter(
        ReportTemplate.id == template_id,
        ReportTemplate.user_id == current_user.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()


# === Compliance Documents ===

@router.post("/documents", response_model=ComplianceDocumentResponse, status_code=201)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def create_compliance_document(
    document: ComplianceDocumentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Create a new compliance document."""
    db_document = ComplianceDocument(
        user_id=current_user.id,
        **document.model_dump(),
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


@router.get("/documents", response_model=List[ComplianceDocumentResponse])
@limiter.limit(DEFAULT_RATE_LIMIT)
async def list_compliance_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
):
    """List all compliance documents for the current user."""
    query = db.query(ComplianceDocument).filter(
        ComplianceDocument.user_id == current_user.id
    )
    if document_type:
        query = query.filter(ComplianceDocument.document_type == document_type)
    if status:
        query = query.filter(ComplianceDocument.status == status)
    
    return query.all()


@router.get("/documents/{document_id}", response_model=ComplianceDocumentResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_compliance_document(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Get a specific compliance document."""
    document = db.query(ComplianceDocument).filter(
        ComplianceDocument.id == document_id,
        ComplianceDocument.user_id == current_user.id,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/documents/{document_id}", response_model=ComplianceDocumentResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def update_compliance_document(
    document_id: uuid.UUID,
    update: ComplianceDocumentUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Update a compliance document."""
    document = db.query(ComplianceDocument).filter(
        ComplianceDocument.id == document_id,
        ComplianceDocument.user_id == current_user.id,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(document, key, value)
    
    db.commit()
    db.refresh(document)
    return document


@router.delete("/documents/{document_id}", status_code=204)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def delete_compliance_document(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Delete a compliance document."""
    document = db.query(ComplianceDocument).filter(
        ComplianceDocument.id == document_id,
        ComplianceDocument.user_id == current_user.id,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(document)
    db.commit()


# === KYC Records ===

@router.post("/kyc", response_model=KycRecordResponse, status_code=201)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def create_kyc_record(
    record: KycRecordCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Create a new KYC record."""
    db_record = KycRecord(
        user_id=current_user.id,
        **record.model_dump(),
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.get("/kyc", response_model=List[KycRecordResponse])
@limiter.limit(DEFAULT_RATE_LIMIT)
async def list_kyc_records(
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
    kyc_status: Optional[str] = None,
):
    """List all KYC records for the current user."""
    query = db.query(KycRecord).filter(
        KycRecord.user_id == current_user.id
    )
    if kyc_status:
        query = query.filter(KycRecord.kyc_status == kyc_status)
    
    return query.all()


@router.get("/kyc/{record_id}", response_model=KycRecordResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_kyc_record(
    record_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Get a specific KYC record."""
    record = db.query(KycRecord).filter(
        KycRecord.id == record_id,
        KycRecord.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="KYC record not found")
    return record


@router.put("/kyc/{record_id}", response_model=KycRecordResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def update_kyc_record(
    record_id: uuid.UUID,
    update: KycRecordUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Update a KYC record."""
    record = db.query(KycRecord).filter(
        KycRecord.id == record_id,
        KycRecord.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="KYC record not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)
    
    db.commit()
    db.refresh(record)
    return record


@router.delete("/kyc/{record_id}", status_code=204)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def delete_kyc_record(
    record_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Delete a KYC record."""
    record = db.query(KycRecord).filter(
        KycRecord.id == record_id,
        KycRecord.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="KYC record not found")
    
    db.delete(record)
    db.commit()


@router.post("/kyc/{record_id}/documents")
@limiter.limit(DEFAULT_RATE_LIMIT)
async def upload_kyc_document(
    record_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
    file: UploadFile = File(...),
):
    """Upload a KYC document (ID, proof of address, etc.)."""
    record = db.query(KycRecord).filter(
        KycRecord.id == record_id,
        KycRecord.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="KYC record not found")
    
    # In production, this would upload to S3/GCS and store the URL
    # For now, we simulate with a placeholder
    import json
    existing_urls = json.loads(record.document_urls or "[]")
    file_url = f"/uploads/kyc/{record_id}/{file.filename}"
    existing_urls.append(file_url)
    record.document_urls = json.dumps(existing_urls)
    
    db.commit()
    
    return {"message": "Document uploaded", "url": file_url}


# === Filing Reminders ===

@router.post("/reminders", response_model=FilingReminderResponse, status_code=201)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def create_filing_reminder(
    reminder: FilingReminderCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Create a new filing deadline reminder."""
    db_reminder = FilingReminder(
        user_id=current_user.id,
        **reminder.model_dump(),
    )
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder


@router.get("/reminders", response_model=List[FilingReminderResponse])
@limiter.limit(DEFAULT_RATE_LIMIT)
async def list_filing_reminders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
    jurisdiction: Optional[str] = None,
):
    """List all filing reminders for the current user."""
    query = db.query(FilingReminder).filter(
        FilingReminder.user_id == current_user.id
    )
    if jurisdiction:
        query = query.filter(FilingReminder.jurisdiction == jurisdiction)
    
    return query.order_by(FilingReminder.deadline).all()


@router.get("/reminders/upcoming", response_model=List[FilingReminderResponse])
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_upcoming_reminders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
    days: int = 30,
):
    """Get filing reminders due within the specified number of days."""
    from datetime import timedelta
    now = datetime.utcnow()
    cutoff = now + timedelta(days=days)
    
    reminders = db.query(FilingReminder).filter(
        FilingReminder.user_id == current_user.id,
        FilingReminder.deadline >= now,
        FilingReminder.deadline <= cutoff,
        FilingReminder.status != "completed",
    ).order_by(FilingReminder.deadline).all()
    
    return reminders


@router.put("/reminders/{reminder_id}", response_model=FilingReminderResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def update_filing_reminder(
    reminder_id: uuid.UUID,
    update: FilingReminderUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Update a filing reminder."""
    reminder = db.query(FilingReminder).filter(
        FilingReminder.id == reminder_id,
        FilingReminder.user_id == current_user.id,
    ).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(reminder, key, value)
    
    db.commit()
    db.refresh(reminder)
    return reminder


@router.delete("/reminders/{reminder_id}", status_code=204)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def delete_filing_reminder(
    reminder_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Delete a filing reminder."""
    reminder = db.query(FilingReminder).filter(
        FilingReminder.id == reminder_id,
        FilingReminder.user_id == current_user.id,
    ).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    db.delete(reminder)
    db.commit()


# === Report Generation ===

@router.post("/generate/pdf", response_model=ReportGenerationResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def generate_pdf_report(
    request: ReportGenerationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Generate a professional PDF report."""
    # Get template if specified
    template = None
    if request.template_id:
        template = db.query(ReportTemplate).filter(
            ReportTemplate.id == request.template_id,
            ReportTemplate.user_id == current_user.id,
        ).first()
    
    # Generate PDF
    report_id = str(uuid.uuid4())
    _pdf_bytes = generate_professional_pdf(
        user_id=str(current_user.id),
        report_type=request.report_type,
        period_start=request.period_start,
        period_end=request.period_end,
        include_holdings=request.include_holdings,
        include_performance=request.include_performance,
        include_allocation=request.include_allocation,
        include_risk_metrics=request.include_risk_metrics,
        include_gips_disclosure=request.include_gips_disclosure,
        template=template,
    )
    
    # In production, save to S3 and return URL
    download_url = f"/reports/{report_id}/download"
    
    return ReportGenerationResponse(
        report_id=report_id,
        download_url=download_url,
        report_type=request.report_type,
        generated_at=datetime.utcnow(),
    )


@router.post("/generate/excel")
@limiter.limit(DEFAULT_RATE_LIMIT)
async def generate_excel_report_endpoint(
    request: ReportGenerationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DBSession,
):
    """Generate an Excel report."""
    excel_bytes = generate_excel_report(
        user_id=str(current_user.id),
        report_type=request.report_type,
        period_start=request.period_start,
        period_end=request.period_end,
        include_holdings=request.include_holdings,
        include_performance=request.include_performance,
        include_allocation=request.include_allocation,
    )
    
    return StreamingResponse(
        iter([excel_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=report_{request.report_type}.xlsx"
        },
    )
