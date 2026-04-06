"""Tests for family service."""

import uuid
from unittest.mock import MagicMock

import pytest

from app.models.family import EntityType, FamilyMemberRole, AccountType
from app.schemas.family_schemas import (
    FamilyMemberCreate,
    FamilyMemberUpdate,
    EntityCreate,
    EntityUpdate,
    EntityAccountCreate,
    EntityAccountUpdate,
    EntityMemberCreate,
)
from app.services import family_service


class TestFamilyMemberService:
    """Tests for family member CRUD operations."""

    def test_get_family_members_returns_empty_list(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        user_id = uuid.uuid4()

        result = family_service.get_family_members(db, user_id)

        assert result == []
        db.query.return_value.filter.return_value.order_by.return_value.all.assert_called_once()

    def test_get_family_member_returns_none_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        user_id = uuid.uuid4()
        member_id = uuid.uuid4()

        result = family_service.get_family_member(db, member_id, user_id)

        assert result is None

    def test_create_family_member(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        user_id = uuid.uuid4()
        data = FamilyMemberCreate(
            name="John Doe",
            role=FamilyMemberRole.ADMIN,
            relationship="Father",
        )

        result = family_service.create_family_member(db, user_id, data)

        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
        assert result.name == "John Doe"

    def test_update_family_member_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        user_id = uuid.uuid4()
        member_id = uuid.uuid4()
        data = FamilyMemberUpdate(name="Updated")

        result = family_service.update_family_member(db, member_id, user_id, data)

        assert result is None

    def test_delete_family_member_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        user_id = uuid.uuid4()
        member_id = uuid.uuid4()

        result = family_service.delete_family_member(db, member_id, user_id)

        assert result is False


class TestEntityService:
    """Tests for entity CRUD operations."""

    def test_get_entities_returns_empty_list(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.query.return_value.filter.return_value.scalar.return_value = 0
        db.query.return_value.filter.return_value.count.return_value = 0
        user_id = uuid.uuid4()

        result = family_service.get_entities(db, user_id)

        assert result == []

    def test_create_entity(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        user_id = uuid.uuid4()
        data = EntityCreate(
            entity_type=EntityType.COMPANY,
            name="Family Corp",
            registration_number="123456",
            jurisdiction="Delaware",
        )

        result = family_service.create_entity(db, user_id, data)

        db.add.assert_called()
        db.flush.assert_called()
        db.commit.assert_called()
        assert result.name == "Family Corp"

    def test_delete_entity_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        user_id = uuid.uuid4()
        entity_id = uuid.uuid4()

        result = family_service.delete_entity(db, entity_id, user_id)

        assert result is False


class TestEntityAccountService:
    """Tests for entity account operations."""

    def test_create_entity_account_entity_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        user_id = uuid.uuid4()
        data = EntityAccountCreate(
            entity_id=uuid.uuid4(),
            account_type=AccountType.BROKERAGE,
            institution="Morgan Stanley",
            current_value=100000.0,
        )

        result = family_service.create_entity_account(db, user_id, data)

        assert result is None

    def test_delete_entity_account_not_found(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.first.return_value = None
        user_id = uuid.uuid4()
        account_id = uuid.uuid4()

        result = family_service.delete_entity_account(db, account_id, user_id)

        assert result is False


class TestAnalyticsService:
    """Tests for family analytics."""

    def test_get_family_overview_empty(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.scalar.return_value = 0
        user_id = uuid.uuid4()

        result = family_service.get_family_overview(db, user_id)

        assert result["member_count"] == 0
        assert result["entity_count"] == 0
        assert result["total_family_net_worth"] == 0.0
        assert result["entity_types_breakdown"] == {}
        assert result["top_entities_by_value"] == []

    def test_get_net_worth_by_entity_empty(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.scalar.return_value = 0
        user_id = uuid.uuid4()

        result = family_service.get_net_worth_by_entity(db, user_id)

        assert result["total_net_worth"] == 0.0
        assert result["by_entity"] == []
        assert result["currency"] == "USD"
