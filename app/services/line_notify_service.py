"""
LINE Notify notification service.
"""

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.models import User

logger = logging.getLogger(__name__)

LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"


async def send_line_notify(token: str, message: str) -> bool:
    """
    Send a notification via LINE Notify.
    
    Args:
        token: LINE Notify token for the user
        message: Message to send
        
    Returns:
        True if successful, False otherwise
    """
    if not token:
        logger.warning("LINE Notify token is empty")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                LINE_NOTIFY_API,
                headers={"Authorization": f"Bearer {token}"},
                data={"message": message}
            )
            
            if response.status_code == 200:
                logger.info(f"LINE Notify sent successfully: {message[:50]}...")
                return True
            elif response.status_code == 401:
                logger.error("LINE Notify token is invalid")
                return False
            elif response.status_code == 403:
                logger.error("LINE Notify token does not have permission")
                return False
            else:
                logger.error(f"LINE Notify API error: {response.status_code} - {response.text}")
                return False
                
    except httpx.TimeoutException:
        logger.error("LINE Notify API timeout")
        return False
    except httpx.RequestError as e:
        logger.error(f"LINE Notify request error: {e}")
        return False
    except Exception as e:
        logger.error(f"LINE Notify unexpected error: {e}")
        return False


async def notify_alert_triggered(
    db: AsyncSession,
    user_id: str,
    symbol: str,
    condition_type: str,
    threshold: float,
    current_price: float
) -> bool:
    """
    Send LINE notification when an alert is triggered.
    
    Args:
        db: Database session
        user_id: User UUID
        symbol: Stock symbol
        condition_type: 'above', 'below', or 'change_pct'
        threshold: Alert threshold value
        current_price: Current stock price
        
    Returns:
        True if notification sent successfully, False otherwise
    """
    # Get user's LINE Notify token
    result = await db.execute(
        select(User.line_notify_token).where(User.id == user_id)
    )
    token = result.scalar_one_or_none()
    
    if not token:
        logger.debug(f"User {user_id} has no LINE Notify token configured")
        return False
    
    # Format message
    condition_text = {
        "above": f"rose above ${threshold:.2f}",
        "below": f"fell below ${threshold:.2f}",
        "change_pct": f"changed by {threshold:+.2f}%"
    }.get(condition_type, f"triggered at ${threshold:.2f}")
    
    message = f"""
🚨 Stock Alert Triggered!

{symbol}: ${current_price:.2f}
Condition: {condition_text}
    """.strip()
    
    return await send_line_notify(token, message)
