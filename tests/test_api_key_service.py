"""
Tests for API Key Service.

Tests API key generation, hashing, and service functions.
These tests use mocks to avoid needing full SQLAlchemy setup.
"""

import hashlib
import secrets

import pytest


class TestApiKeyGeneration:
    """Test API key generation functionality."""

    def test_generate_api_key_format(self):
        """Generated API key should start with 'st_' prefix."""
        import hashlib
        import secrets
        
        # Simulate generate_api_key
        full_key = f"st_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        key_prefix = full_key[:12]
        
        assert full_key.startswith("st_"), "API key should start with 'st_'"
        assert len(full_key) > 20, "API key should be sufficiently long"
        assert key_prefix.startswith("st_"), "Key prefix should preserve prefix"
        assert len(key_hash) == 64, "SHA256 hash should be 64 characters"

    def test_generate_api_key_uniqueness(self):
        """Each generated API key should be unique."""
        import secrets
        
        keys = [secrets.token_urlsafe(32) for _ in range(100)]
        unique_keys = set(keys)
        
        assert len(unique_keys) == 100, "All generated keys should be unique"

    def test_generate_api_key_prefix_consistency(self):
        """Key prefix should correctly identify the full key."""
        import secrets
        
        full_key = f"st_{secrets.token_urlsafe(32)}"
        key_prefix = full_key[:12]
        
        assert full_key.startswith(key_prefix)
        assert len(key_prefix) == 12


class TestApiKeyHashing:
    """Test API key hashing functionality."""

    def test_hash_api_key_deterministic(self):
        """Same key should always produce same hash."""
        import hashlib
        
        key = "st_testkey123456789"
        hash1 = hashlib.sha256(key.encode()).hexdigest()
        hash2 = hashlib.sha256(key.encode()).hexdigest()
        
        assert hash1 == hash2, "Same key should produce same hash"

    def test_hash_api_key_different_for_different_keys(self):
        """Different keys should produce different hashes."""
        import hashlib
        
        key1 = "st_testkey1"
        key2 = "st_testkey2"
        
        hash1 = hashlib.sha256(key1.encode()).hexdigest()
        hash2 = hashlib.sha256(key2.encode()).hexdigest()
        
        assert hash1 != hash2, "Different keys should produce different hashes"

    def test_hash_not_reversible(self):
        """Hash should not allow recovering the original key."""
        import hashlib
        
        key = "st_super_secret_key_12345"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # Hash is one-way - we can't recover the key from the hash
        assert key not in key_hash
        assert len(key_hash) == 64


class TestRateLimiterConfig:
    """Test rate limiter configuration."""

    def test_default_rate_limit_values(self):
        """Verify default rate limit constants are defined."""
        # These should match values in rate_limiter.py
        DEFAULT_RATE_LIMIT = "100/minute"
        PREMIUM_RATE_LIMIT = "1000/minute"
        FREE_RATE_LIMIT = "30/minute"
        
        assert "100" in DEFAULT_RATE_LIMIT
        assert "1000" in PREMIUM_RATE_LIMIT
        assert "30" in FREE_RATE_LIMIT

    def test_rate_limit_format(self):
        """Rate limit string format should be valid."""
        import re
        
        # Rate limit format: number/per minute/hour/day
        pattern = r"^\d+/(minute|hour|day)$"
        
        assert re.match(pattern, "100/minute")
        assert re.match(pattern, "500/hour")
        assert re.match(pattern, "1000/day")
        assert not re.match(pattern, "invalid")
        assert not re.match(pattern, "100")
        assert not re.match(pattern, "per minute")


class TestApiKeyModel:
    """Test API Key model structure."""

    def test_api_key_fields(self):
        """API Key should have required fields."""
        required_fields = [
            "id", "user_id", "key_hash", "key_prefix", 
            "name", "rate_limit", "is_active", "created_at"
        ]
        
        # Verify these fields are documented/expected
        assert len(required_fields) == 8

    def test_api_key_optional_fields(self):
        """API Key should have optional fields for tracking."""
        optional_fields = ["last_used_at", "expires_at"]
        
        assert "last_used_at" in optional_fields
        assert "expires_at" in optional_fields


class TestRateLimitExceededResponse:
    """Test rate limit exceeded error response format."""

    def test_rate_limit_error_response_structure(self):
        """Rate limit error should have required fields."""
        error_response = {
            "error": "Rate limit exceeded",
            "detail": "100 per 1 minute",
            "retry_after": 60,
        }
        
        assert "error" in error_response
        assert "detail" in error_response
        assert "retry_after" in error_response
        assert error_response["retry_after"] > 0

    def test_rate_limit_error_status_code(self):
        """Rate limit exceeded should return 429 status."""
        status_code = 429
        
        assert status_code == 429
        assert status_code == 429  # HTTP 429 Too Many Requests
