"""
Discord webhook notification service.
"""

import re
import httpx
import logging

logger = logging.getLogger(__name__)

DISCORD_MAX_MESSAGE_LENGTH = 2000


async def send_discord_webhook(webhook_url: str, message: str, username: str = "Stock Tracker") -> bool:
    """
    Send a notification via Discord webhook.
    
    Args:
        webhook_url: Discord webhook URL
        message: Message to send (max 2000 chars)
        username: Display name for the webhook bot
        
    Returns:
        True if successful, False otherwise
    """
    if not webhook_url:
        logger.warning("Discord webhook URL is empty")
        return False
    
    # Validate webhook URL is a legitimate Discord webhook (prevents SSRF)
    discord_pattern = re.compile(
        r'^https://(discord\.com|discordapp\.com)/api/webhooks/\d+/[\w-]+$'
    )
    if not discord_pattern.match(webhook_url):
        logger.warning("Discord webhook URL validation failed: %s", webhook_url)
        return False
    
    # Truncate message if too long
    if len(message) > DISCORD_MAX_MESSAGE_LENGTH:
        message = message[:DISCORD_MAX_MESSAGE_LENGTH - 3] + "..."
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json={
                    "username": username,
                    "content": message,
                }
            )
            
            if response.status_code in (200, 204):
                logger.info(f"Discord webhook sent successfully: {message[:50]}...")
                return True
            elif response.status_code == 400:
                logger.error(f"Discord webhook bad request: {response.text}")
                return False
            elif response.status_code == 404:
                logger.error("Discord webhook URL is invalid or expired")
                return False
            elif response.status_code == 429:
                logger.error("Discord webhook rate limited")
                return False
            else:
                logger.error(f"Discord webhook error: {response.status_code} - {response.text}")
                return False
    except httpx.RequestError as e:
        logger.error(f"Discord webhook request failed: {e}")
        return False


def format_stock_alert(symbol: str, signal: str, price: float, confidence: float) -> str:
    """Format a stock alert as a Discord message."""
    emoji = "📈" if signal == "BUY" else "📉" if signal == "SELL" else "➡️"
    return f"""{emoji} **Stock Alert: {symbol}**

**Signal:** {signal}
**Price:** ${price:.2f}
**Confidence:** {confidence:.0f}%
"""


def format_price_alert(symbol: str, condition_type: str, threshold: float, current_price: float) -> str:
    """Format a price alert notification as a Discord message."""
    emoji = "🔔"
    condition_text = {
        "above": f"rose above ${threshold:.2f}",
        "below": f"fell below ${threshold:.2f}",
        "change_pct": f"changed by {threshold:+.2f}%"
    }.get(condition_type, f"triggered at ${threshold:.2f}")
    
    return f"""{emoji} **Price Alert Triggered!**

**{symbol}:** ${current_price:.2f}
**Condition:** {condition_text}
"""


async def notify_discord_alert_triggered(
    webhook_url: str,
    symbol: str,
    condition_type: str,
    threshold: float,
    current_price: float
) -> bool:
    """
    Send Discord notification when a price alert is triggered.
    
    Args:
        webhook_url: Discord webhook URL
        symbol: Stock symbol
        condition_type: 'above', 'below', or 'change_pct'
        threshold: Alert threshold value
        current_price: Current stock price
        
    Returns:
        True if notification sent successfully, False otherwise
    """
    if not webhook_url:
        logger.debug("Discord webhook URL is empty, skipping notification")
        return False
    
    message = format_price_alert(symbol, condition_type, threshold, current_price)
    return await send_discord_webhook(webhook_url, message)
