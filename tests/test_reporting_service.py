"""
Tests for Phase 39: Institutional-Grade Reporting & Compliance
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestReportGeneration:
    """Tests for professional report generation."""

    def test_generate_professional_pdf_returns_bytes(self):
        """Test that PDF generation returns bytes."""
        from app.services.report_service import generate_professional_pdf

        # Call the function
        result = generate_professional_pdf(
            user_id="test-user-id",
            report_type="quarterly",
            period_start=datetime.utcnow() - timedelta(days=90),
            period_end=datetime.utcnow(),
            include_holdings=True,
            include_performance=True,
            include_allocation=True,
            include_risk_metrics=True,
            include_gips_disclosure=False,
            template=None,
        )

        # Assert it returns bytes
        assert isinstance(result, bytes)
        # Assert it's a valid PDF (starts with %PDF)
        assert result[:4] == b'%PDF'

    def test_generate_professional_pdf_with_gips(self):
        """Test PDF generation with GIPS disclosure."""
        from app.services.report_service import generate_professional_pdf

        result = generate_professional_pdf(
            user_id="test-user-id",
            report_type="gips",
            period_start=datetime.utcnow() - timedelta(days=365),
            period_end=datetime.utcnow(),
            include_holdings=True,
            include_performance=True,
            include_allocation=True,
            include_risk_metrics=True,
            include_gips_disclosure=True,
            template=None,
        )

        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'

    def test_generate_excel_report_returns_bytes(self):
        """Test that Excel generation returns bytes."""
        from app.services.report_service import generate_excel_report

        result = generate_excel_report(
            user_id="test-user-id",
            report_type="quarterly",
            period_start=datetime.utcnow() - timedelta(days=90),
            period_end=datetime.utcnow(),
            include_holdings=True,
            include_performance=True,
            include_allocation=True,
        )

        assert isinstance(result, bytes)
        # Excel files start with PK (ZIP format)
        assert result[:2] == b'PK'


class TestReportingSchemas:
    """Tests for reporting Pydantic schemas."""

    def test_report_template_create_schema(self):
        """Test ReportTemplateCreate schema validation."""
        from app.schemas.reporting_schemas import ReportTemplateCreate

        template = ReportTemplateCreate(
            name="Quarterly Report",
            template_type="quarterly",
            primary_color="#1a1a2e",
            secondary_color="#16213e",
            company_name="Test Company",
            is_default=True,
        )

        assert template.name == "Quarterly Report"
        assert template.template_type == "quarterly"
        assert template.is_default is True

    def test_report_template_invalid_type(self):
        """Test that invalid template type is rejected."""
        from app.schemas.reporting_schemas import ReportTemplateCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ReportTemplateCreate(
                name="Test",
                template_type="invalid_type",
            )

    def test_kyc_record_create_schema(self):
        """Test KycRecordCreate schema validation."""
        from app.schemas.reporting_schemas import KycRecordCreate

        record = KycRecordCreate(
            client_name="John Doe",
            client_email="john@example.com",
            risk_tolerance="moderate",
            investment_experience="intermediate",
            investment_horizon="long",
            suitability_score=75.5,
            kyc_status="pending",
        )

        assert record.client_name == "John Doe"
        assert record.risk_tolerance == "moderate"
        assert record.suitability_score == 75.5

    def test_filing_reminder_schema(self):
        """Test FilingReminderCreate schema validation."""
        from app.schemas.reporting_schemas import FilingReminderCreate

        reminder = FilingReminderCreate(
            filing_type="quarterly",
            title="Q1 2026 Filing",
            deadline=datetime.utcnow() + timedelta(days=30),
            jurisdiction="SEC",
            status="pending",
        )

        assert reminder.filing_type == "quarterly"
        assert reminder.jurisdiction == "SEC"

    def test_report_generation_request_schema(self):
        """Test ReportGenerationRequest schema."""
        from app.schemas.reporting_schemas import ReportGenerationRequest

        request = ReportGenerationRequest(
            report_type="annual",
            period_start=datetime.utcnow() - timedelta(days=365),
            period_end=datetime.utcnow(),
            include_holdings=True,
            include_performance=True,
            include_allocation=True,
            include_risk_metrics=True,
            include_gips_disclosure=True,
        )

        assert request.report_type == "annual"
        assert request.include_gips_disclosure is True


class TestReportingModels:
    """Tests for reporting SQLAlchemy models."""

    def test_report_template_model_fields(self):
        """Test that ReportTemplate model has required fields."""
        from app.models.models import ReportTemplate

        # Check columns exist
        assert hasattr(ReportTemplate, 'id')
        assert hasattr(ReportTemplate, 'user_id')
        assert hasattr(ReportTemplate, 'name')
        assert hasattr(ReportTemplate, 'template_type')
        assert hasattr(ReportTemplate, 'primary_color')
        assert hasattr(ReportTemplate, 'secondary_color')
        assert hasattr(ReportTemplate, 'is_default')

    def test_kyc_record_model_fields(self):
        """Test that KycRecord model has required fields."""
        from app.models.models import KycRecord

        assert hasattr(KycRecord, 'id')
        assert hasattr(KycRecord, 'user_id')
        assert hasattr(KycRecord, 'client_name')
        assert hasattr(KycRecord, 'risk_tolerance')
        assert hasattr(KycRecord, 'suitability_score')
        assert hasattr(KycRecord, 'kyc_status')

    def test_filing_reminder_model_fields(self):
        """Test that FilingReminder model has required fields."""
        from app.models.models import FilingReminder

        assert hasattr(FilingReminder, 'id')
        assert hasattr(FilingReminder, 'user_id')
        assert hasattr(FilingReminder, 'filing_type')
        assert hasattr(FilingReminder, 'title')
        assert hasattr(FilingReminder, 'deadline')
        assert hasattr(FilingReminder, 'jurisdiction')
        assert hasattr(FilingReminder, 'status')
