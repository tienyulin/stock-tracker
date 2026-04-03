"""
User management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.models.models import User
from app.utils.auth import decode_access_token

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


class LineTokenResponse(BaseModel):
    line_notify_connected: bool


class LineTokenUpdate(BaseModel):
    line_notify_token: str


class LineTokenTestResult(BaseModel):
    success: bool
    message: str


class DiscordWebhookTestResult(BaseModel):
    success: bool
    message: str


class DiscordWebhookUpdate(BaseModel):
    discord_webhook_url: str


class DiscordWebhookResponse(BaseModel):
    discord_webhook_configured: bool


async def get_current_user_id(authorization: str = Header(None)) -> str:
    """Extract user ID from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = parts[1]
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    return user_id


@router.get("/me/line-token", response_model=LineTokenResponse)
async def get_line_token_status(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get LINE Notify token connection status."""
    result = await db.execute(
        select(User.line_notify_token).where(User.id == user_id)
    )
    token = result.scalar_one_or_none()
    
    return LineTokenResponse(line_notify_connected=bool(token))


@router.put("/me/line-token", response_model=LineTokenResponse)
async def update_line_token(
    token_data: LineTokenUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update LINE Notify token for the current user."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.line_notify_token = token_data.line_notify_token
    await db.commit()
    
    logger.info(f"User {user_id} updated LINE Notify token")
    
    return LineTokenResponse(line_notify_connected=bool(token_data.line_notify_token))


@router.delete("/me/line-token", response_model=LineTokenResponse)
async def delete_line_token(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Remove LINE Notify token (disconnect LINE notifications)."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.line_notify_token = None
    await db.commit()
    
    logger.info(f"User {user_id} disconnected LINE Notify")
    
    return LineTokenResponse(line_notify_connected=False)


@router.post("/me/line-token/test", response_model=LineTokenTestResult)
async def test_line_token(
    token_data: LineTokenUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """Test LINE Notify token by sending a test message."""
    from app.services.line_notify_service import send_line_notify
    
    test_message = """
🔔 Stock Tracker LINE Notify Test

Your LINE Notify integration is working! 
You will receive stock alerts here.
    """.strip()
    
    success = await send_line_notify(token_data.line_notify_token, test_message)
    
    if success:
        return LineTokenTestResult(success=True, message="Test message sent! Check your LINE app.")
    else:
        return LineTokenTestResult(
            success=False, 
            message="Failed to send test message. Please check your LINE Notify token."
        )


@router.post("/me/discord-webhook/test", response_model=DiscordWebhookTestResult)
async def test_discord_webhook(
    webhook_data: DiscordWebhookUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """Test Discord webhook by sending a test message."""
    from app.services.discord_notify_service import send_discord_webhook
    
    test_message = """
📢 **Stock Tracker Discord Integration Test**

Your Discord webhook is working! 
You will receive stock alerts here.
    """.strip()
    
    success = await send_discord_webhook(webhook_data.discord_webhook_url, test_message)
    
    if success:
        return DiscordWebhookTestResult(
            success=True, 
            message="Test message sent! Check your Discord channel."
        )
    else:
        return DiscordWebhookTestResult(
            success=False, 
            message="Failed to send test message. Please check your Discord webhook URL."
        )


@router.get("/me/discord-webhook", response_model=DiscordWebhookResponse)
async def get_discord_webhook_status(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get Discord webhook configuration status."""
    result = await db.execute(
        select(User.discord_webhook_url).where(User.id == user_id)
    )
    webhook_url = result.scalar_one_or_none()
    
    return DiscordWebhookResponse(discord_webhook_configured=bool(webhook_url))


@router.put("/me/discord-webhook", response_model=DiscordWebhookResponse)
async def update_discord_webhook(
    webhook_data: DiscordWebhookUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update Discord webhook URL for the current user."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.discord_webhook_url = webhook_data.discord_webhook_url
    await db.commit()
    
    logger.info("User %s updated Discord webhook URL", user_id)
    
    return DiscordWebhookResponse(discord_webhook_configured=bool(webhook_data.discord_webhook_url))


@router.delete("/me/discord-webhook", response_model=DiscordWebhookResponse)
async def delete_discord_webhook(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Remove Discord webhook URL (disconnect Discord notifications)."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.discord_webhook_url = None
    await db.commit()
    
    logger.info("User %s disconnected Discord webhook", user_id)
    
    return DiscordWebhookResponse(discord_webhook_configured=False)
