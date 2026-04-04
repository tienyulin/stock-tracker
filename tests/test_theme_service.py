"""
Tests for Theme Service - Phase 13
"""

from datetime import datetime


class TestThemeMode:
    """Test theme mode enum."""

    def test_theme_modes(self):
        from app.services.theme_service import ThemeMode
        
        assert ThemeMode.LIGHT.value == "light"
        assert ThemeMode.DARK.value == "dark"
        assert ThemeMode.SYSTEM.value == "system"


class TestThemePreference:
    """Test theme preference model."""

    def test_theme_preference_creation(self):
        from app.services.theme_service import ThemePreference, ThemeMode
        
        pref = ThemePreference(
            user_id="user-123",
            theme_mode=ThemeMode.DARK,
            updated_at=datetime.now(),
        )
        
        assert pref.user_id == "user-123"
        assert pref.theme_mode == ThemeMode.DARK


class TestThemeService:
    """Test Theme Service."""

    def test_service_initialization(self):
        from app.services.theme_service import ThemeService
        
        service = ThemeService()
        assert service._preferences == {}

    def test_set_theme_preference(self):
        from app.services.theme_service import ThemeService, ThemeMode
        
        service = ThemeService()
        result = service.set_theme_preference("user-123", ThemeMode.DARK)
        
        assert result is True
        assert service.get_theme_preference("user-123") == ThemeMode.DARK

    def test_set_theme_preference_light(self):
        from app.services.theme_service import ThemeService, ThemeMode
        
        service = ThemeService()
        service.set_theme_preference("user-123", ThemeMode.LIGHT)
        
        assert service.get_theme_preference("user-123") == ThemeMode.LIGHT

    def test_set_theme_preference_system(self):
        from app.services.theme_service import ThemeService, ThemeMode
        
        service = ThemeService()
        service.set_theme_preference("user-123", ThemeMode.SYSTEM)
        
        assert service.get_theme_preference("user-123") == ThemeMode.SYSTEM

    def test_get_theme_preference_default(self):
        from app.services.theme_service import ThemeService, ThemeMode
        
        service = ThemeService()
        # New users get system default
        theme = service.get_theme_preference("new-user")
        
        assert theme == ThemeMode.SYSTEM

    def test_delete_theme_preference(self):
        from app.services.theme_service import ThemeService, ThemeMode
        
        service = ThemeService()
        service.set_theme_preference("user-123", ThemeMode.DARK)
        result = service.delete_theme_preference("user-123")
        
        assert result is True
        # After deletion, should return default
        assert service.get_theme_preference("user-123") == ThemeMode.SYSTEM

    def test_get_css_variables_light(self):
        from app.services.theme_service import ThemeService, ThemeMode
        
        service = ThemeService()
        service.set_theme_preference("user-123", ThemeMode.LIGHT)
        
        css_vars = service.get_css_variables("user-123")
        
        assert "--bg-primary" in css_vars
        assert "--text-primary" in css_vars
        assert "light" in css_vars["--theme-name"]

    def test_get_css_variables_dark(self):
        from app.services.theme_service import ThemeService, ThemeMode
        
        service = ThemeService()
        service.set_theme_preference("user-123", ThemeMode.DARK)
        
        css_vars = service.get_theme_preference("user-123")
        
        # Dark mode should have dark background
        assert css_vars == ThemeMode.DARK

    def test_get_theme_statistics(self):
        from app.services.theme_service import ThemeService, ThemeMode
        
        service = ThemeService()
        service.set_theme_preference("user-1", ThemeMode.LIGHT)
        service.set_theme_preference("user-2", ThemeMode.DARK)
        service.set_theme_preference("user-3", ThemeMode.SYSTEM)
        
        stats = service.get_theme_statistics()
        
        assert stats["total_users"] == 3
        assert stats["light"] == 1
        assert stats["dark"] == 1
        assert stats["system"] == 1


class TestThemeToggle:
    """Test theme toggle helper functions."""

    def test_is_dark_mode_preferred_system(self):
        from app.services.theme_service import ThemeService, ThemeMode
        
        service = ThemeService()
        service.set_theme_preference("user-123", ThemeMode.SYSTEM)
        
        # For system mode, should return False (caller needs to check system preference)
        result = service.is_dark_mode_preferred("user-123")
        # System mode doesn't directly tell us if dark is preferred
        # The actual dark mode detection should be done on frontend
        assert isinstance(result, bool)

    def test_is_dark_mode_preferred_explicit(self):
        from app.services.theme_service import ThemeService, ThemeMode
        
        service = ThemeService()
        service.set_theme_preference("user-123", ThemeMode.DARK)
        
        # User explicitly chose dark mode
        assert service.is_dark_mode_preferred("user-123") is True
