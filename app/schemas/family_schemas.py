"""Pydantic schemas for Family Office & Multi-Entity Management."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.family import AccountType, EntityType, FamilyMemberRole


# ─── Family Members ──────────────────────────────────────────────────────────


class FamilyMemberBase(BaseModel):
    name: str = Field(..., max_length=255)
    role: FamilyMemberRole = FamilyMemberRole.VIEWER
    relationship_type: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None


class FamilyMemberCreate(FamilyMemberBase):
    pass


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    role: Optional[FamilyMemberRole] = None
    relationship_type: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None


class FamilyMemberResponse(FamilyMemberBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Entities ────────────────────────────────────────────────────────────────


class EntityMemberBase(BaseModel):
    family_member_id: UUID
    role: str = Field(default="Member", max_length=100)
    ownership_percentage: Optional[float] = None


class EntityMemberCreate(EntityMemberBase):
    pass


class EntityMemberResponse(EntityMemberBase):
    id: UUID
    created_at: datetime
    family_member: Optional[FamilyMemberResponse] = None

    class Config:
        from_attributes = True


class EntityBase(BaseModel):
    entity_type: EntityType
    name: str = Field(..., max_length=255)
    registration_number: Optional[str] = Field(None, max_length=100)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class EntityCreate(EntityBase):
    members: Optional[List[EntityMemberCreate]] = None


class EntityUpdate(BaseModel):
    entity_type: Optional[EntityType] = None
    name: Optional[str] = Field(None, max_length=255)
    registration_number: Optional[str] = Field(None, max_length=100)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class EntityAccountSummary(BaseModel):
    id: UUID
    account_type: AccountType
    institution: Optional[str]
    account_name: Optional[str]
    current_value: float
    currency: str
    is_active: bool

    class Config:
        from_attributes = True


class EntityResponse(EntityBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    total_value: Optional[float] = 0.0
    member_count: Optional[int] = 0

    class Config:
        from_attributes = True


class EntityDetailResponse(EntityResponse):
    members: List[EntityMemberResponse] = []
    accounts: List[EntityAccountSummary] = []

    class Config:
        from_attributes = True


# ─── Entity Accounts ─────────────────────────────────────────────────────────


class EntityAccountBase(BaseModel):
    account_type: AccountType
    institution: Optional[str] = Field(None, max_length=255)
    account_name: Optional[str] = Field(None, max_length=255)
    account_number_masked: Optional[str] = Field(None, max_length=50)
    current_value: float = 0.0
    currency: str = Field(default="USD", max_length=10)
    notes: Optional[str] = None
    is_active: bool = True


class EntityAccountCreate(EntityAccountBase):
    entity_id: UUID


class EntityAccountUpdate(BaseModel):
    account_type: Optional[AccountType] = None
    institution: Optional[str] = Field(None, max_length=255)
    account_name: Optional[str] = Field(None, max_length=255)
    account_number_masked: Optional[str] = Field(None, max_length=50)
    current_value: Optional[float] = None
    currency: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class EntityAccountResponse(EntityAccountBase):
    id: UUID
    entity_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Analytics ───────────────────────────────────────────────────────────────


class EntityNetWorthItem(BaseModel):
    entity_id: UUID
    entity_name: str
    entity_type: EntityType
    total_value: float
    currency: str = "USD"


class FamilyOverviewResponse(BaseModel):
    total_family_net_worth: float
    member_count: int
    entity_count: int
    entity_types_breakdown: dict  # {EntityType: count}
    top_entities_by_value: List[EntityNetWorthItem]


class NetWorthResponse(BaseModel):
    total_net_worth: float
    by_entity: List[EntityNetWorthItem]
    currency: str = "USD"
