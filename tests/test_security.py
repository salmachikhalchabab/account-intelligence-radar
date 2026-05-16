import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security import sanitize_string, sanitize_dict, safe_log
from fastapi import HTTPException


# ══════════════════════════════════════════
#  sanitize_string
# ══════════════════════════════════════════

def test_clean_input_passes():
    result = sanitize_string("Aramco")
    assert result == "Aramco"

def test_strips_whitespace():
    result = sanitize_string("  Aramco  ")
    assert result == "Aramco"

def test_xss_script_blocked():
    with pytest.raises(HTTPException) as exc:
        sanitize_string("<script>alert(1)</script>")
    assert exc.value.status_code == 400

def test_xss_javascript_blocked():
    with pytest.raises(HTTPException) as exc:
        sanitize_string("javascript:alert(1)")
    assert exc.value.status_code == 400

def test_xss_event_handler_blocked():
    with pytest.raises(HTTPException) as exc:
        sanitize_string("onclick=alert(1)")
    assert exc.value.status_code == 400

def test_sql_drop_blocked():
    with pytest.raises(HTTPException) as exc:
        sanitize_string("DROP TABLE users")
    assert exc.value.status_code == 400

def test_sql_select_blocked():
    with pytest.raises(HTTPException) as exc:
        sanitize_string("SELECT * FROM users")
    assert exc.value.status_code == 400

def test_path_traversal_blocked():
    with pytest.raises(HTTPException) as exc:
        sanitize_string("../../etc/passwd")
    assert exc.value.status_code == 400

def test_too_long_input_blocked():
    with pytest.raises(HTTPException) as exc:
        sanitize_string("A" * 501)
    assert exc.value.status_code == 400

def test_max_length_passes():
    result = sanitize_string("A" * 500)
    assert len(result) == 500

def test_arabic_text_passes():
    result = sanitize_string("أرامكو السعودية")
    assert result == "أرامكو السعودية"

def test_numbers_pass():
    result = sanitize_string("STC 2025")
    assert result == "STC 2025"

def test_special_chars_in_company_name():
    result = sanitize_string("Saudi Aramco & Partners")
    assert "Saudi Aramco" in result


# ══════════════════════════════════════════
#  sanitize_dict
# ══════════════════════════════════════════

def test_clean_dict_passes():
    data = {"company": "Aramco", "sector": "energy"}
    result = sanitize_dict(data)
    assert result == {"company": "Aramco", "sector": "energy"}

def test_dict_with_xss_blocked():
    with pytest.raises(HTTPException):
        sanitize_dict({"company": "<script>alert(1)</script>"})

def test_nested_dict_sanitized():
    with pytest.raises(HTTPException):
        sanitize_dict({"outer": {"inner": "<script>bad</script>"}})

def test_non_string_values_pass():
    data = {"count": 5, "active": True, "score": 3.14}
    result = sanitize_dict(data)
    assert result == data

def test_mixed_dict_sanitized():
    with pytest.raises(HTTPException):
        sanitize_dict({"name": "Aramco", "evil": "DROP TABLE users"})


# ══════════════════════════════════════════
#  safe_log — Key Redaction
# ══════════════════════════════════════════

def test_redacts_groq_key():
    msg = "Using key gsk_abcdefghijklmnopqrstuvwxyz123456"
    result = safe_log(msg)
    assert "gsk_" not in result
    assert "[REDACTED]" in result

def test_redacts_openrouter_key():
    # OpenRouter keys are long — use a realistic length key
    msg = "sk-or-v1-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN"
    result = safe_log(msg)
    assert "[REDACTED]" in result

def test_redacts_openai_style_key():
    msg = "sk-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRST"
    result = safe_log(msg)
    assert "[REDACTED]" in result

def test_clean_log_unchanged():
    msg = "Job started for company: Aramco"
    result = safe_log(msg)
    assert result == msg

def test_redacts_bearer_token():
    msg = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIn0.abcdefgh"
    result = safe_log(msg)
    assert "[REDACTED]" in result

def test_redacts_multiple_keys_in_one_message():
    msg = "key1=gsk_abcdefghijklmnopqrstuvwxyz123 key2=sk-abcdefghijklmnopqrstuvwxyzABC"
    result = safe_log(msg)
    assert "[REDACTED]" in result

def test_short_string_not_redacted():
    # Short strings under 20 chars should not be redacted
    msg = "Error code: 404"
    result = safe_log(msg)
    assert result == msg
