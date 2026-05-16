import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    validate_password
)
from fastapi import HTTPException


# ══════════════════════════════════════════
#  Password Hashing
# ══════════════════════════════════════════

def test_hash_password_returns_string():
    hashed = hash_password("TestPass1")
    assert isinstance(hashed, str)
    assert len(hashed) > 20

def test_hash_is_not_plaintext():
    hashed = hash_password("TestPass1")
    assert "TestPass1" not in hashed

def test_same_password_different_hashes():
    # Argon2 uses random salt — same password = different hash
    h1 = hash_password("TestPass1")
    h2 = hash_password("TestPass1")
    assert h1 != h2

def test_verify_correct_password():
    hashed = hash_password("TestPass1")
    assert verify_password("TestPass1", hashed) is True

def test_verify_wrong_password():
    hashed = hash_password("TestPass1")
    assert verify_password("WrongPass1", hashed) is False

def test_verify_empty_password():
    hashed = hash_password("TestPass1")
    assert verify_password("", hashed) is False


# ══════════════════════════════════════════
#  JWT Token
# ══════════════════════════════════════════

def test_create_token_returns_string():
    token = create_access_token({"sub": "user-123"})
    assert isinstance(token, str)
    assert len(token) > 20

def test_decode_valid_token():
    token = create_access_token({"sub": "user-abc"})
    user_id = decode_token(token)
    assert user_id == "user-abc"

def test_decode_invalid_token():
    result = decode_token("this.is.invalid")
    assert result is None

def test_decode_empty_token():
    result = decode_token("")
    assert result is None

def test_decode_tampered_token():
    token = create_access_token({"sub": "user-123"})
    tampered = token[:-5] + "XXXXX"
    result = decode_token(tampered)
    assert result is None


# ══════════════════════════════════════════
#  Password Validation
# ══════════════════════════════════════════

def test_valid_password_passes():
    # Should not raise
    validate_password("TestPass1")

def test_short_password_fails():
    with pytest.raises(HTTPException) as exc:
        validate_password("Ab1")
    assert exc.value.status_code == 400
    assert "8 characters" in exc.value.detail

def test_no_uppercase_fails():
    with pytest.raises(HTTPException) as exc:
        validate_password("testpass1")
    assert exc.value.status_code == 400
    assert "uppercase" in exc.value.detail

def test_no_digit_fails():
    with pytest.raises(HTTPException) as exc:
        validate_password("TestPassword")
    assert exc.value.status_code == 400
    assert "number" in exc.value.detail

def test_empty_password_fails():
    with pytest.raises(HTTPException):
        validate_password("")
