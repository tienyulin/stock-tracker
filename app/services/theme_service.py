"""
Theme Service - Phase 13

Provides dark mode and theme management:
- Light/Dark mode switch
- System preference detection
- Persistent theme preference
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ThemeMode(Enum):
    """Theme mode options."""

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass
class ThemePreference:
    """User theme preference."""

    user_id: str
    theme_mode: ThemeMode = ThemeMode.SYSTEM
    updated_at: datetime = field(default_factory=datetime.utcnow)


class ThemeService:
    """Service for managing user theme preferences."""

    def __init__(self):
        """Initialize Theme Service."""
        self._preferences: dict[str, ThemePreference] = {}

    def set_theme_preference(self, user_id: str, theme_mode: ThemeMode) -> bool:
        """
        Set theme preference for a user.

        Args:
            user_id: User identifier
            theme_mode: Desired theme mode

        Returns:
            True if set successfully
        """
        self._preferences[user_id] = ThemePreference(
            user_id=user_id,
            theme_mode=theme_mode,
            updated_at=datetime.utcnow(),
        )
        return True

    def get_theme_preference(self, user_id: str) -> ThemeMode:
        """
        Get theme preference for a user.

        Args:
            user_id: User identifier

        Returns:
            User's theme preference, defaults to SYSTEM
        """
        if user_id not in self._preferences:
            return ThemeMode.SYSTEM
        return self._preferences[user_id].theme_mode

    def delete_theme_preference(self, user_id: str) -> bool:
        """
        Delete theme preference for a user (reset to default).

        Args:
            user_id: User identifier

        Returns:
            True if deleted
        """
        if user_id in self._preferences:
            del self._preferences[user_id]
            return True
        return False

    def is_dark_mode_preferred(self, user_id: str) -> bool:
        """
        Check if dark mode is preferred for a user.
        For SYSTEM mode, caller should check system preference.

        Args:
            user_id: User identifier

        Returns:
            True if dark mode should be used
        """
        theme = self.get_theme_preference(user_id)
        return theme == ThemeMode.DARK

    def get_css_variables(self, user_id: str) -> dict:
        """
        Get CSS variables for the user's theme.

        Args:
            user_id: User identifier

        Returns:
            Dictionary of CSS variables
        """
        theme = self.get_theme_preference(user_id)

        if theme == ThemeMode.DARK:
            return {
                "--bg-primary": "#1a1a2e",
                "--bg-secondary": "#16213e",
                "--text-primary": "#eaeaea",
                "--text-secondary": "#a0a0a0",
                "--accent-color": "#0f3460",
                "--border-color": "#2a2a4a",
                "--success-color": "#4ade80",
                "--error-color": "#f87171",
                "--warning-color": "#fbbf24",
                "--theme-name": "dark",
            }
        elif theme == ThemeMode.LIGHT:
            return {
                "--bg-primary": "#ffffff",
                "--bg-secondary": "#f5f5f5",
                "--text-primary": "#1a1a1a",
                "--text-secondary": "#666666",
                "--accent-color": "#3b82f6",
                "--border-color": "#e5e5e5",
                "--success-color": "#22c55e",
                "--error-color": "#ef4444",
                "--warning-color": "#f59e0b",
                "--theme-name": "light",
            }
        else:  # SYSTEM
            # Return light as default, frontend will handle system preference
            return {
                "--bg-primary": "#ffffff",
                "--bg-secondary": "#f5f5f5",
                "--text-primary": "#1a1a1a",
                "--text-secondary": "#666666",
                "--accent-color": "#3b82f6",
                "--border-color": "#e5e5e5",
                "--success-color": "#22c55e",
                "--error-color": "#ef4444",
                "--warning-color": "#f59e0b",
                "--theme-name": "system",
            }

    def get_theme_statistics(self) -> dict:
        """
        Get theme usage statistics.

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_users": len(self._preferences),
            "light": 0,
            "dark": 0,
            "system": 0,
        }

        for pref in self._preferences.values():
            if pref.theme_mode == ThemeMode.LIGHT:
                stats["light"] += 1
            elif pref.theme_mode == ThemeMode.DARK:
                stats["dark"] += 1
            else:
                stats["system"] += 1

        return stats


# Global service instance
_theme_service: Optional[ThemeService] = None


def get_theme_service() -> ThemeService:
    """Get or create the global theme service instance."""
    global _theme_service
    if _theme_service is None:
        _theme_service = ThemeService()
    return _theme_service
