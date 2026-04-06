"""Service layer for Family Office & Multi-Entity Management."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.family import Entity, EntityAccount, EntityMember, FamilyMember
from app.models.family import EntityType as ModelEntityType
from app.schemas.family_schemas import (
    EntityAccountCreate,
    EntityAccountUpdate,
    EntityCreate,
    EntityMemberCreate,
    EntityUpdate,
    FamilyMemberCreate,
    FamilyMemberUpdate,
)


# ─── Family Members ──────────────────────────────────────────────────────────


def get_family_members(db: Session, user_id: UUID) -> List[FamilyMember]:
    return (
        db.query(FamilyMember)
        .filter(FamilyMember.user_id == user_id)
        .order_by(FamilyMember.created_at.desc())
        .all()
    )


def get_family_member(db: Session, member_id: UUID, user_id: UUID) -> Optional[FamilyMember]:
    return (
        db.query(FamilyMember)
        .filter(FamilyMember.id == member_id, FamilyMember.user_id == user_id)
        .first()
    )


def create_family_member(db: Session, user_id: UUID, data: FamilyMemberCreate) -> FamilyMember:
    member = FamilyMember(user_id=user_id, **data.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def update_family_member(
    db: Session, member_id: UUID, user_id: UUID, data: FamilyMemberUpdate
) -> Optional[FamilyMember]:
    member = get_family_member(db, member_id, user_id)
    if not member:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return member


def delete_family_member(db: Session, member_id: UUID, user_id: UUID) -> bool:
    member = get_family_member(db, member_id, user_id)
    if not member:
        return False
    db.delete(member)
    db.commit()
    return True


# ─── Entities ────────────────────────────────────────────────────────────────


def get_entities(db: Session, user_id: UUID) -> List[Entity]:
    entities = (
        db.query(Entity)
        .filter(Entity.user_id == user_id)
        .order_by(Entity.created_at.desc())
        .all()
    )
    for entity in entities:
        total = db.query(func.coalesce(func.sum(EntityAccount.current_value), 0)).filter(
            EntityAccount.entity_id == entity.id
        ).scalar()
        entity.total_value = float(total)
        entity.member_count = (
            db.query(EntityMember).filter(EntityMember.entity_id == entity.id).count()
        )
    return entities


def get_entity(db: Session, entity_id: UUID, user_id: UUID) -> Optional[Entity]:
    entity = (
        db.query(Entity)
        .filter(Entity.id == entity_id, Entity.user_id == user_id)
        .first()
    )
    if entity:
        total = db.query(func.coalesce(func.sum(EntityAccount.current_value), 0)).filter(
            EntityAccount.entity_id == entity.id
        ).scalar()
        entity.total_value = float(total)
        entity.member_count = (
            db.query(EntityMember).filter(EntityMember.entity_id == entity.id).count()
        )
    return entity


def get_entity_detail(db: Session, entity_id: UUID, user_id: UUID) -> Optional[Entity]:
    entity = get_entity(db, entity_id, user_id)
    if entity:
        entity.members = (
            db.query(EntityMember)
            .filter(EntityMember.entity_id == entity_id)
            .all()
        )
        entity.accounts = (
            db.query(EntityAccount)
            .filter(EntityAccount.entity_id == entity_id)
            .order_by(EntityAccount.created_at.desc())
            .all()
        )
    return entity


def create_entity(db: Session, user_id: UUID, data: EntityCreate) -> Entity:
    members_data = data.members or []
    data_dict = data.model_dump(exclude={"members"})

    entity = Entity(user_id=user_id, **data_dict)
    db.add(entity)
    db.flush()

    for m in members_data:
        em = EntityMember(entity_id=entity.id, **m.model_dump())
        db.add(em)

    db.commit()
    db.refresh(entity)
    return entity


def update_entity(db: Session, entity_id: UUID, user_id: UUID, data: EntityUpdate) -> Optional[Entity]:
    entity = get_entity(db, entity_id, user_id)
    if not entity:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(entity, field, value)
    db.commit()
    db.refresh(entity)
    return entity


def delete_entity(db: Session, entity_id: UUID, user_id: UUID) -> bool:
    entity = get_entity(db, entity_id, user_id)
    if not entity:
        return False
    db.delete(entity)
    db.commit()
    return True


# ─── Entity Members ──────────────────────────────────────────────────────────


def add_entity_member(
    db: Session, entity_id: UUID, user_id: UUID, data: EntityMemberCreate
) -> Optional[EntityMember]:
    entity = get_entity(db, entity_id, user_id)
    if not entity:
        return None
    em = EntityMember(entity_id=entity_id, **data.model_dump())
    db.add(em)
    db.commit()
    db.refresh(em)
    return em


def remove_entity_member(db: Session, entity_id: UUID, member_id: UUID, user_id: UUID) -> bool:
    entity = get_entity(db, entity_id, user_id)
    if not entity:
        return False
    em = (
        db.query(EntityMember)
        .filter(EntityMember.id == member_id, EntityMember.entity_id == entity_id)
        .first()
    )
    if not em:
        return False
    db.delete(em)
    db.commit()
    return True


# ─── Entity Accounts ─────────────────────────────────────────────────────────


def get_entity_accounts(db: Session, entity_id: UUID, user_id: UUID) -> List[EntityAccount]:
    entity = get_entity(db, entity_id, user_id)
    if not entity:
        return []
    return (
        db.query(EntityAccount)
        .filter(EntityAccount.entity_id == entity_id)
        .order_by(EntityAccount.created_at.desc())
        .all()
    )


def get_entity_account(db: Session, account_id: UUID, user_id: UUID) -> Optional[EntityAccount]:
    account = (
        db.query(EntityAccount)
        .join(Entity)
        .filter(EntityAccount.id == account_id, Entity.user_id == user_id)
        .first()
    )
    return account


def create_entity_account(
    db: Session, user_id: UUID, data: EntityAccountCreate
) -> Optional[EntityAccount]:
    entity = get_entity(db, data.entity_id, user_id)
    if not entity:
        return None
    account_data = data.model_dump()
    entity_id = account_data.pop("entity_id")
    account = EntityAccount(entity_id=entity_id, **account_data)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_entity_account(
    db: Session, account_id: UUID, user_id: UUID, data: EntityAccountUpdate
) -> Optional[EntityAccount]:
    account = get_entity_account(db, account_id, user_id)
    if not account:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return account


def delete_entity_account(db: Session, account_id: UUID, user_id: UUID) -> bool:
    account = get_entity_account(db, account_id, user_id)
    if not account:
        return False
    db.delete(account)
    db.commit()
    return True


# ─── Analytics ───────────────────────────────────────────────────────────────


def get_family_overview(db: Session, user_id: UUID) -> dict:
    member_count = db.query(FamilyMember).filter(FamilyMember.user_id == user_id).count()
    entities = db.query(Entity).filter(Entity.user_id == user_id).all()

    entity_types_breakdown = {}
    top_entities = []
    total = 0.0

    for entity in entities:
        et = entity.entity_type.value
        entity_types_breakdown[et] = entity_types_breakdown.get(et, 0) + 1

        entity_total = db.query(
            func.coalesce(func.sum(EntityAccount.current_value), 0)
        ).filter(EntityAccount.entity_id == entity.id).scalar()
        entity_total = float(entity_total)
        total += entity_total

        top_entities.append({
            "entity_id": entity.id,
            "entity_name": entity.name,
            "entity_type": entity.entity_type,
            "total_value": entity_total,
            "currency": "USD",
        })

    top_entities.sort(key=lambda x: x["total_value"], reverse=True)

    return {
        "total_family_net_worth": total,
        "member_count": member_count,
        "entity_count": len(entities),
        "entity_types_breakdown": entity_types_breakdown,
        "top_entities_by_value": top_entities[:5],
    }


def get_net_worth_by_entity(db: Session, user_id: UUID) -> dict:
    entities = db.query(Entity).filter(Entity.user_id == user_id).all()
    total = 0.0
    by_entity = []

    for entity in entities:
        entity_total = db.query(
            func.coalesce(func.sum(EntityAccount.current_value), 0)
        ).filter(EntityAccount.entity_id == entity.id).scalar()
        entity_total = float(entity_total)
        total += entity_total
        by_entity.append({
            "entity_id": entity.id,
            "entity_name": entity.name,
            "entity_type": entity.entity_type,
            "total_value": entity_total,
            "currency": "USD",
        })

    by_entity.sort(key=lambda x: x["total_value"], reverse=True)

    return {
        "total_net_worth": total,
        "by_entity": by_entity,
        "currency": "USD",
    }
