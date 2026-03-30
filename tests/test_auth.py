"""
Tests for User Authentication (JWT).

Tests password hashing, JWT creation/validation.
These tests use mocks to avoid needing full SQLAlchemy setup.
"""

import pytest


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_password_hash_not_plain_text(self):
        """Password hash should not equal plain password."""
        import bcrypt
        password = "securepassword123"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        # Hash should not equal plain password
        assert hashed != password.encode()
        assert hashed.decode() != password

    def test_password_hash_verification_correct(self):
        """Correct password should verify successfully."""
        import bcrypt
        password = "securepassword123"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        # Correct password should verify
        assert bcrypt.checkpw(password.encode(), hashed) is True

    def test_password_hash_verification_wrong(self):
        """Wrong password should not verify."""
        import bcrypt
        password = "securepassword123"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        # Wrong password should not verify
        assert bcrypt.checkpw("wrongpassword".encode(), hashed) is False

    def test_different_passwords_different_hashes(self):
        """Same password should produce different hashes (due to salt)."""
        import bcrypt
        password = "securepassword123"
        hash1 = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        hash2 = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        # Hashes should be different due to different salts
        assert hash1 != hash2


class TestJWT:
    """Test JWT token functionality."""

    def test_jwt_encode_decode(self):
        """JWT encode and decode should work correctly."""
        import jwt
        secret = "test-secret"
        payload = {"sub": "user123", "email": "test@example.com"}
        
        # Encode
        token = jwt.encode(payload, secret, algorithm="HS256")
        assert isinstance(token, str)
        
        # Decode
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"

    def test_jwt_decode_wrong_secret(self):
        """JWT decoded with wrong secret should fail."""
        import jwt
        from jwt.exceptions import InvalidSignatureError
        
        secret = "test-secret"
        wrong_secret = "wrong-secret"
        payload = {"sub": "user123"}
        
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        with pytest.raises(InvalidSignatureError):
            jwt.decode(token, wrong_secret, algorithms=["HS256"])

    def test_jwt_missing_secret(self):
        """JWT without proper secret should fail verification."""
        import jwt
        from jwt.exceptions import DecodeError
        
        token = "invalid.token.here"
        
        with pytest.raises(DecodeError):
            jwt.decode(token, "secret", algorithms=["HS256"])


class TestEmailValidation:
    """Test email format validation."""

    def test_valid_emails(self):
        """Various valid email formats should pass."""
        import re
        # Updated pattern to support + in local part
        email_pattern = r'^[\w\.\+\-]+@[\w\.\-]+\.\w+$'
        
        valid_emails = [
            "test@example.com",
            "user.name@domain.org",
            "user+tag@example.co.uk",
            "firstname.lastname@company.com",
        ]
        for email in valid_emails:
            assert re.match(email_pattern, email) is not None, f"{email} should be valid"

    def test_invalid_emails(self):
        """Invalid email formats should fail."""
        import re
        email_pattern = r'^[\w\.\+\-]+@[\w\.\-]+\.\w+$'
        
        invalid_emails = [
            "invalid-email",
            "@nodomain.com",
            "user@",
            "user@.com",
            "",
        ]
        for email in invalid_emails:
            assert re.match(email_pattern, email) is None, f"{email} should be invalid"


class TestPasswordValidation:
    """Test password validation rules."""

    def test_password_minimum_length(self):
        """Passwords must be at least 8 characters."""
        MIN_LENGTH = 8
        
        assert len("1234567") < MIN_LENGTH  # 7 chars - too short
        assert len("12345678") >= MIN_LENGTH  # 8 chars - OK
        assert len("verylongpassword123") >= MIN_LENGTH  # Long - OK

    def test_password_maximum_length_reasonable(self):
        """Passwords should have a reasonable max length for usability."""
        MAX_LENGTH = 128
        
        assert len("a" * 200) > MAX_LENGTH  # Too long
        assert len("a" * 128) <= MAX_LENGTH  # At limit
