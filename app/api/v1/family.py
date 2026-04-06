"""API routes for Family Office & Multi-Entity Management."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.family_schemas import (
    EntityAccountCreate,
    EntityAccountResponse,
    EntityAccountUpdate,
    EntityCreate,
    EntityDetailResponse,
    EntityMemberCreate,
    EntityMemberResponse,
    EntityResponse,
    EntityUpdate,
    FamilyMemberCreate,
    FamilyMemberResponse,
    FamilyMemberUpdate,
    FamilyOverviewResponse,
    NetWorthResponse,
)
from app.services import family_service

router = APIRouter(prefix="/api/v1/family", tags=["family"])


# ─── Family Members ───────────────────────────────────────────────────────────


@router.get("/members", response_model=List[FamilyMemberResponse])
def list_family_members(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return family_service.get_family_members(db, user.id)


@router.post("/members", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED)
def create_family_member(
    data: FamilyMemberCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return family_service.create_family_member(db, user.id, data)


@router.get("/members/{member_id}", response_model=FamilyMemberResponse)
def get_family_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    member = family_service.get_family_member(db, member_id, user.id)
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")
    return member


@router.put("/members/{member_id}", response_model=FamilyMemberResponse)
def update_family_member(
    member_id: UUID,
    data: FamilyMemberUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    member = family_service.update_family_member(db, member_id, user.id, data)
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")
    return member


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_family_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    deleted = family_service.delete_family_member(db, member_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Family member not found")


# ─── Entities ────────────────────────────────────────────────────────────────


@router.get("/entities", response_model=List[EntityResponse])
def list_entities(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return family_service.get_entities(db, user.id)


@router.post("/entities", response_model=EntityDetailResponse, status_code=status.HTTP_201_CREATED)
def create_entity(
    data: EntityCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return family_service.create_entity(db, user.id, data)


@router.get("/entities/{entity_id}", response_model=EntityDetailResponse)
def get_entity(
    entity_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    entity = family_service.get_entity_detail(db, entity_id, user.id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.put("/entities/{entity_id}", response_model=EntityResponse)
def update_entity(
    entity_id: UUID,
    data: EntityUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    entity = family_service.update_entity(db, entity_id, user.id, data)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.delete("/entities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity(
    entity_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    deleted = family_service.delete_entity(db, entity_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entity not found")


# ─── Entity Members ───────────────────────────────────────────────────────────


@router.post(
    "/entities/{entity_id}/members",
    response_model=EntityMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_entity_member(
    entity_id: UUID,
    data: EntityMemberCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    member = family_service.add_entity_member(db, entity_id, user.id, data)
    if not member:
        raise HTTPException(status_code=404, detail="Entity not found")
    return member


@router.delete("/entities/{entity_id}/members/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_entity_member(
    entity_id: UUID,
    membership_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    deleted = family_service.remove_entity_member(db, entity_id, membership_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Membership not found")


# ─── Entity Accounts ─────────────────────────────────────────────────────────


@router.get("/entities/{entity_id}/accounts", response_model=List[EntityAccountResponse])
def list_entity_accounts(
    entity_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return family_service.get_entity_accounts(db, entity_id, user.id)


@router.post("/accounts", response_model=EntityAccountResponse, status_code=status.HTTP_201_CREATED)
def create_entity_account(
    data: EntityAccountCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    account = family_service.create_entity_account(db, user.id, data)
    if not account:
        raise HTTPException(status_code=404, detail="Entity not found")
    return account


@router.put("/accounts/{account_id}", response_model=EntityAccountResponse)
def update_entity_account(
    account_id: UUID,
    data: EntityAccountUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    account = family_service.update_entity_account(db, account_id, user.id, data)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entity_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    deleted = family_service.delete_entity_account(db, account_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Account not found")


# ─── Analytics ───────────────────────────────────────────────────────────────


@router.get("/analytics/overview", response_model=FamilyOverviewResponse)
def family_overview(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return family_service.get_family_overview(db, user.id)


@router.get("/analytics/net-worth", response_model=NetWorthResponse)
def net_worth_by_entity(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return family_service.get_net_worth_by_entity(db, user.id)
