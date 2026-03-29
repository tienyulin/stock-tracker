"""
Watchlist API routes.
"""
from typing import List, UUID
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Watchlist, WatchlistItem
from app.schemas import (
    WatchlistCreate,
    WatchlistItemCreate,
    WatchlistItemResponse,
    WatchlistResponse,
    WatchlistUpdate,
)

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("", response_model=List[WatchlistResponse])
async def list_watchlists(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> List[WatchlistResponse]:
    """List all watchlists for a user."""
    result = await db.execute(
        select(Watchlist).where(Watchlist.user_id == user_id)
    )
    watchlists = result.scalars().all()

    response_list = []
    for wl in watchlists:
        items_result = await db.execute(
            select(WatchlistItem)
            .where(WatchlistItem.watchlist_id == wl.id)
            .order_by(WatchlistItem.added_at)
        )
        items = items_result.scalars().all()

        response_list.append(
            WatchlistResponse(
                id=wl.id,
                name=wl.name,
                is_default=wl.is_default,
                items=[
                    WatchlistItemResponse(
                        id=item.id,
                        symbol=item.symbol,
                        notes=item.notes,
                        added_at=item.added_at,
                    )
                    for item in items
                ],
                created_at=wl.created_at,
                updated_at=wl.updated_at,
            )
        )

    return response_list


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    watchlist_data: WatchlistCreate,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> WatchlistResponse:
    """Create a new watchlist."""
    if watchlist_data.is_default:
        # Unset other defaults
        result = await db.execute(
            select(Watchlist).where(
                Watchlist.user_id == user_id,
                Watchlist.is_default == True,
            )
        )
        for existing in result.scalars().all():
            existing.is_default = False

    watchlist = Watchlist(
        user_id=user_id,
        name=watchlist_data.name,
        is_default=watchlist_data.is_default,
    )
    db.add(watchlist)
    await db.commit()
    await db.refresh(watchlist)

    return WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        is_default=watchlist.is_default,
        items=[],
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
    )


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> WatchlistResponse:
    """Get a specific watchlist with items."""
    result = await db.execute(
        select(Watchlist).where(Watchlist.id == watchlist_id)
    )
    watchlist = result.scalar_one_or_none()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    items_result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.watchlist_id == watchlist_id)
        .order_by(WatchlistItem.added_at)
    )
    items = items_result.scalars().all()

    return WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        is_default=watchlist.is_default,
        items=[
            WatchlistItemResponse(
                id=item.id,
                symbol=item.symbol,
                notes=item.notes,
                added_at=item.added_at,
            )
            for item in items
        ],
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
    )


@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(
    watchlist_id: UUID,
    watchlist_data: WatchlistUpdate,
    db: AsyncSession = Depends(get_db),
) -> WatchlistResponse:
    """Update a watchlist."""
    result = await db.execute(
        select(Watchlist).where(Watchlist.id == watchlist_id)
    )
    watchlist = result.scalar_one_or_none()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    if watchlist_data.name is not None:
        watchlist.name = watchlist_data.name
    if watchlist_data.is_default is not None:
        if watchlist_data.is_default:
            # Unset other defaults
            other_result = await db.execute(
                select(Watchlist).where(
                    Watchlist.user_id == watchlist.user_id,
                    Watchlist.id != watchlist_id,
                    Watchlist.is_default == True,
                )
            )
            for other in other_result.scalars().all():
                other.is_default = False
        watchlist.is_default = watchlist_data.is_default

    await db.commit()
    await db.refresh(watchlist)

    return WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        is_default=watchlist.is_default,
        items=[],
        created_at=watchlist.created_at,
        updated_at=watchlist.updated_at,
    )


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    watchlist_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a watchlist."""
    result = await db.execute(
        select(Watchlist).where(Watchlist.id == watchlist_id)
    )
    watchlist = result.scalar_one_or_none()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    await db.delete(watchlist)
    await db.commit()


@router.post("/{watchlist_id}/items", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_watchlist(
    watchlist_id: UUID,
    item_data: WatchlistItemCreate,
    db: AsyncSession = Depends(get_db),
) -> WatchlistItemResponse:
    """Add a stock to a watchlist."""
    result = await db.execute(
        select(Watchlist).where(Watchlist.id == watchlist_id)
    )
    watchlist = result.scalar_one_or_none()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    item = WatchlistItem(
        watchlist_id=watchlist_id,
        symbol=item_data.symbol.upper(),
        notes=item_data.notes,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return WatchlistItemResponse(
        id=item.id,
        symbol=item.symbol,
        notes=item.notes,
        added_at=item.added_at,
    )


@router.delete("/{watchlist_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_watchlist(
    watchlist_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove a stock from a watchlist."""
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.id == item_id,
            WatchlistItem.watchlist_id == watchlist_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await db.delete(item)
    await db.commit()
