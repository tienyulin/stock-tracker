"""Family members, entities, and multi-entity account management."""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class FamilyMemberRole(str, Enum):
    ADMIN = "ADMIN"
    VIEWER = "VIEWER"
    MINOR = "MINOR"


class EntityType(str, Enum):
    COMPANY = "COMPANY"
    TRUST = "TRUST"
    PARTNERSHIP = "PARTNERSHIP"
    INDIVIDUAL = "INDIVIDUAL"


class AccountType(str, Enum):
    BROKERAGE = "BROKERAGE"
    BANK = "BANK"
    CRYPTO = "CRYPTO"
    OTHER = "OTHER"


class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(SAEnum(FamilyMemberRole), default=FamilyMemberRole.VIEWER, nullable=False)
    relationship = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="family_members")
    entity_memberships = relationship("EntityMember", back_populates="family_member", cascade="all, delete-orphan")


class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    entity_type = Column(SAEnum(EntityType), nullable=False)
    name = Column(String(255), nullable=False)
    registration_number = Column(String(100), nullable=True)
    jurisdiction = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="entities")
    memberships = relationship("EntityMember", back_populates="entity", cascade="all, delete-orphan")
    accounts = relationship("EntityAccount", back_populates="entity", cascade="all, delete-orphan")


class EntityMember(Base):
    __tablename__ = "entity_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False, index=True)
    family_member_id = Column(UUID(as_uuid=True), ForeignKey("family_members.id"), nullable=False, index=True)
    role = Column(String(100), nullable=False, default="Member")
    ownership_percentage = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    entity = relationship("Entity", back_populates="memberships")
    family_member = relationship("FamilyMember", back_populates="entity_memberships")


class EntityAccount(Base):
    __tablename__ = "entity_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False, index=True)
    account_type = Column(SAEnum(AccountType), nullable=False)
    institution = Column(String(255), nullable=True)
    account_name = Column(String(255), nullable=True)
    account_number_masked = Column(String(50), nullable=True)
    current_value = Column(Float, default=0.0, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entity = relationship("Entity", back_populates="accounts")
