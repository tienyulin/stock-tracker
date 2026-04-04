"""
Tests for User Onboarding Service - Phase 17
"""



class TestOnboardingStep:
    """Test onboarding step model."""

    def test_onboarding_step_creation(self):
        from app.services.user_onboarding_service import OnboardingStep, OnboardingStepType
        
        step = OnboardingStep(
            step_type=OnboardingStepType.WELCOME,
            title="Welcome to Stock Tracker",
            description="Let's get you started",
            is_completed=False,
            order=1,
        )
        
        assert step.step_type == OnboardingStepType.WELCOME
        assert step.title == "Welcome to Stock Tracker"
        assert step.order == 1
        assert step.is_completed is False


class TestPortfolioTemplate:
    """Test portfolio template model."""

    def test_portfolio_template_creation(self):
        from app.services.user_onboarding_service import PortfolioTemplate, Allocation
        
        template = PortfolioTemplate(
            name="Conservative",
            description="Low risk, stable returns",
            risk_level="LOW",
            allocations=[
                Allocation(category="bonds", percentage=60, description="60% Bonds"),
                Allocation(category="stocks", percentage=30, description="30% Stocks"),
                Allocation(category="cash", percentage=10, description="10% Cash"),
            ],
        )
        
        assert template.name == "Conservative"
        assert template.risk_level == "LOW"
        assert len(template.allocations) == 3
        assert sum(a.percentage for a in template.allocations) == 100


class TestUserOnboardingService:
    """Test User Onboarding Service."""

    def test_service_initialization(self):
        from app.services.user_onboarding_service import UserOnboardingService
        
        service = UserOnboardingService()
        assert service._user_progress == {}
        assert service._completed_onboarding == set()

    def test_get_onboarding_steps(self):
        from app.services.user_onboarding_service import UserOnboardingService
        
        service = UserOnboardingService()
        steps = service.get_onboarding_steps("user-123")
        
        assert len(steps) == 5  # Welcome, Profile, First Watchlist, First Alert, First Portfolio
        assert steps[0].step_type.value == "welcome"
        assert steps[-1].step_type.value == "first_portfolio"

    def test_complete_step(self):
        from app.services.user_onboarding_service import UserOnboardingService, OnboardingStepType
        
        service = UserOnboardingService()
        result = service.complete_step("user-123", OnboardingStepType.WELCOME)
        
        assert result is True
        progress = service.get_progress("user-123")
        assert progress.completed_steps == 1
        assert progress.total_steps == 5

    def test_complete_step_invalid(self):
        from app.services.user_onboarding_service import UserOnboardingService
        
        service = UserOnboardingService()
        result = service.complete_step("user-123", "invalid_step")
        
        assert result is False

    def test_is_onboarding_complete(self):
        from app.services.user_onboarding_service import UserOnboardingService, OnboardingStepType
        
        service = UserOnboardingService()
        
        # Complete all steps
        for step_type in OnboardingStepType:
            service.complete_step("user-123", step_type)
        
        assert service.is_onboarding_complete("user-123") is True

    def test_get_onboarding_progress(self):
        from app.services.user_onboarding_service import UserOnboardingService, OnboardingStepType
        
        service = UserOnboardingService()
        service.complete_step("user-123", OnboardingStepType.WELCOME)
        service.complete_step("user-123", OnboardingStepType.PROFILE_SETUP)
        
        progress = service.get_progress("user-123")
        
        assert progress.completed_steps == 2
        assert progress.total_steps == 5
        assert progress.percentage == 40

    def test_get_portfolio_templates(self):
        from app.services.user_onboarding_service import UserOnboardingService
        
        service = UserOnboardingService()
        templates = service.get_portfolio_templates()
        
        assert len(templates) == 3  # Conservative, Balanced, Aggressive
        assert templates[0].name == "Conservative"
        assert templates[1].name == "Balanced"
        assert templates[2].name == "Aggressive"

    def test_create_first_portfolio(self):
        from app.services.user_onboarding_service import UserOnboardingService
        
        service = UserOnboardingService()
        
        portfolio = service.create_first_portfolio(
            user_id="user-123",
            template_name="Balanced",
            initial_capital=10000.0,
        )
        
        assert portfolio.user_id == "user-123"
        assert portfolio.initial_capital == 10000.0
        assert len(portfolio.holdings) > 0

    def test_mark_onboarding_complete(self):
        from app.services.user_onboarding_service import UserOnboardingService
        
        service = UserOnboardingService()
        service.mark_onboarding_complete("user-123")
        
        assert service.is_onboarding_complete("user-123") is True
        assert "user-123" in service._completed_onboarding

    def test_get_suggested_watchlists(self):
        from app.services.user_onboarding_service import UserOnboardingService
        
        service = UserOnboardingService()
        suggestions = service.get_suggested_watchlists()
        
        assert len(suggestions) > 0
        assert suggestions[0]["name"] is not None
        assert suggestions[0]["symbols"] is not None


class TestOnboardingProgress:
    """Test onboarding progress tracking."""

    def test_get_encouraging_message(self):
        from app.services.user_onboarding_service import UserOnboardingService
        
        service = UserOnboardingService()
        
        # At 0%
        msg = service.get_encouraging_message("user-123")
        assert msg is not None
        assert len(msg) > 0
        
        # At 50%
        service.complete_step("user-123", "welcome")
        service.complete_step("user-123", "profile_setup")
        
        msg = service.get_encouraging_message("user-123")
        assert msg is not None
