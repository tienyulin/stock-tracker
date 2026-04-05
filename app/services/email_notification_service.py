"""
Email notification service for alerts.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

# Default SMTP settings - should be configured via environment variables
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"  # Use app-specific password for Gmail


async def send_email_alert(
    to_email: str,
    symbol: str,
    condition_type: str,
    threshold: float,
    current_price: float,
    custom_message: Optional[str] = None,
) -> bool:
    """
    Send a price alert notification via email.

    Args:
        to_email: Recipient email address
        symbol: Stock symbol
        condition_type: Type of alert ('above', 'below', 'change_pct')
        threshold: Alert threshold value
        current_price: Current stock price when alert triggered
        custom_message: Optional custom notification message

    Returns:
        True if email sent successfully, False otherwise
    """
    if not to_email:
        logger.warning("Email address is empty, skipping notification")
        return False

    # Build email content
    condition_labels = {
        "above": f"rose above ${threshold:.2f}",
        "below": f"dropped below ${threshold:.2f}",
        "change_pct": f"changed by {threshold:+.2f}%",
    }

    condition_text = condition_labels.get(condition_type, f"triggered at ${threshold:.2f}")

    subject = f"📈 Stock Alert: {symbol} {condition_text.replace('$', '').replace('%', '')}"

    body = f"""
Stock Price Alert Triggered
==========================

Symbol: {symbol}
Condition: {condition_type.replace('_', ' ').title()}
Threshold: {threshold}
Current Price: ${current_price:.2f}

{"Custom Message: " + custom_message if custom_message else ""}

---
This alert was triggered by Stock Tracker.
To manage your alerts, visit your dashboard.
    """

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email alert sent successfully to {to_email}: {symbol}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(f"Email authentication failed for {to_email}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email to {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email to {to_email}: {e}")
        return False


async def send_test_email(to_email: str) -> bool:
    """
    Send a test email to verify email configuration.

    Args:
        to_email: Recipient email address

    Returns:
        True if email sent successfully, False otherwise
    """
    if not to_email:
        return False

    subject = "Test Email from Stock Tracker"
    body = """
Hello!

This is a test email from Stock Tracker.
If you received this, your email notifications are configured correctly.

---
Stock Tracker
    """

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Test email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send test email to {to_email}: {e}")
        return False
