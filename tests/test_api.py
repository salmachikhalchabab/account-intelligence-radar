import pytest
import sys
import os

# TESTING must be set before importing api
os.environ["TESTING"] = "1"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from api import app

client = TestClient(app, raise_server_exceptions=False)


# ══════════════════════════════════════════
#  Module-level shared token
# ══════════════════════════════════════════

def get_token(email, username, password="TestPass1"):
    """Register (if needed) and login — return token."""
    client.post("/api/auth/register", json={
        "email": email, "username": username, "password": password
    })
    r = client.post("/api/auth/login", data={
        "username": username, "password": password
    })
    return r.json().get("access_token", "")


# Create one shared user for all tests that need auth
SHARED_TOKEN = None
SHARED_HEADERS = None


def setup_module(module):
    global SHARED_TOKEN, SHARED_HEADERS
    SHARED_TOKEN = get_token("shared@test.com", "sharedtestuser")
    SHARED_HEADERS = {"Authorization": f"Bearer {SHARED_TOKEN}"}


# ══════════════════════════════════════════
#  AUTH — Register
# ══════════════════════════════════════════

def test_register_success():
    r = client.post("/api/auth/register", json={
        "email": "reg1@test.com",
        "username": "reguser1",
        "password": "TestPass1"
    })
    assert r.status_code == 200
    assert "access_token" in r.json()

def test_register_returns_user_info():
    r = client.post("/api/auth/register", json={
        "email": "reg2@test.com",
        "username": "reguser2",
        "password": "TestPass1"
    })
    assert "user" in r.json()
    assert r.json()["user"]["email"] == "reg2@test.com"

def test_register_duplicate_email():
    client.post("/api/auth/register", json={
        "email": "dup@test.com", "username": "dupuser1", "password": "TestPass1"
    })
    r = client.post("/api/auth/register", json={
        "email": "dup@test.com", "username": "dupuser2", "password": "TestPass1"
    })
    assert r.status_code == 400
    assert "Email" in r.json()["detail"]

def test_register_duplicate_username():
    client.post("/api/auth/register", json={
        "email": "uniq1@test.com", "username": "sameusername", "password": "TestPass1"
    })
    r = client.post("/api/auth/register", json={
        "email": "uniq2@test.com", "username": "sameusername", "password": "TestPass1"
    })
    assert r.status_code == 400

def test_register_weak_password():
    r = client.post("/api/auth/register", json={
        "email": "weak@test.com", "username": "weakuser", "password": "weak"
    })
    assert r.status_code == 400

def test_register_no_uppercase():
    r = client.post("/api/auth/register", json={
        "email": "noup@test.com", "username": "noupuser", "password": "nouppercas1"
    })
    assert r.status_code == 400

def test_register_no_digit():
    r = client.post("/api/auth/register", json={
        "email": "nodig@test.com", "username": "nodiguser", "password": "NoDigitPass"
    })
    assert r.status_code == 400

def test_register_invalid_email():
    r = client.post("/api/auth/register", json={
        "email": "not-an-email", "username": "emailtest", "password": "TestPass1"
    })
    assert r.status_code == 422

def test_register_short_username():
    r = client.post("/api/auth/register", json={
        "email": "short@test.com", "username": "ab", "password": "TestPass1"
    })
    assert r.status_code == 400


# ══════════════════════════════════════════
#  AUTH — Login
# ══════════════════════════════════════════

def test_login_success():
    client.post("/api/auth/register", json={
        "email": "login@test.com", "username": "loginuser", "password": "TestPass1"
    })
    r = client.post("/api/auth/login", data={
        "username": "loginuser", "password": "TestPass1"
    })
    assert r.status_code == 200
    assert "access_token" in r.json()

def test_login_with_email():
    r = client.post("/api/auth/login", data={
        "username": "login@test.com", "password": "TestPass1"
    })
    assert r.status_code == 200

def test_login_wrong_password():
    r = client.post("/api/auth/login", data={
        "username": "loginuser", "password": "WrongPass1"
    })
    assert r.status_code == 401

def test_login_nonexistent_user():
    r = client.post("/api/auth/login", data={
        "username": "nobody", "password": "TestPass1"
    })
    assert r.status_code == 401


# ══════════════════════════════════════════
#  AUTH — /me
# ══════════════════════════════════════════

def test_me_with_valid_token():
    r = client.get("/api/auth/me", headers=SHARED_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "email" in data
    assert "username" in data
    assert "id" in data

def test_me_without_token():
    r = client.get("/api/auth/me")
    assert r.status_code == 401

def test_me_with_invalid_token():
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert r.status_code == 401

def test_me_with_garbage_token():
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer aaa.bbb.ccc"})
    assert r.status_code == 401


# ══════════════════════════════════════════
#  REPORTS
# ══════════════════════════════════════════

def test_reports_without_token():
    r = client.get("/api/reports")
    assert r.status_code == 401

def test_reports_with_token():
    r = client.get("/api/reports", headers=SHARED_HEADERS)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_get_nonexistent_report():
    r = client.get("/api/reports/nonexistent-id", headers=SHARED_HEADERS)
    assert r.status_code == 404

def test_delete_nonexistent_report():
    r = client.delete("/api/reports/nonexistent-id", headers=SHARED_HEADERS)
    assert r.status_code == 404

def test_cannot_access_other_users_report():
    token_b = get_token("userb@test.com", "userbtest2")
    headers_b = {"Authorization": f"Bearer {token_b}"}
    r = client.get("/api/reports/fake-report-id", headers=headers_b)
    assert r.status_code == 404


# ══════════════════════════════════════════
#  COMPANY MODE
# ══════════════════════════════════════════

def test_company_mode_requires_auth():
    r = client.post("/api/company", json={"company_name": "Aramco"})
    assert r.status_code == 401

def test_company_mode_xss_blocked():
    r = client.post("/api/company",
                    json={"company_name": "<script>alert(1)</script>"},
                    headers=SHARED_HEADERS)
    assert r.status_code == 400

def test_company_mode_sql_injection_blocked():
    r = client.post("/api/company",
                    json={"company_name": "DROP TABLE users"},
                    headers=SHARED_HEADERS)
    assert r.status_code == 400

def test_company_mode_path_traversal_blocked():
    r = client.post("/api/company",
                    json={"company_name": "../../etc/passwd"},
                    headers=SHARED_HEADERS)
    assert r.status_code == 400

def test_company_mode_valid_returns_job_id():
    r = client.post("/api/company",
                    json={"company_name": "Aramco"},
                    headers=SHARED_HEADERS)
    assert r.status_code == 200
    assert "job_id" in r.json()


# ══════════════════════════════════════════
#  GEOGRAPHY MODE
# ══════════════════════════════════════════

def test_geography_requires_auth():
    r = client.post("/api/geography", json={"country": "Saudi Arabia", "sector": "energy"})
    assert r.status_code == 401

def test_geography_valid_returns_job_id():
    r = client.post("/api/geography",
                    json={"country": "Saudi Arabia", "city": "Riyadh", "sector": "energy"},
                    headers=SHARED_HEADERS)
    assert r.status_code == 200
    assert "job_id" in r.json()

def test_geography_xss_blocked():
    r = client.post("/api/geography",
                    json={"country": "<script>bad</script>", "sector": "energy"},
                    headers=SHARED_HEADERS)
    assert r.status_code == 400

def test_geography_sql_injection_blocked():
    r = client.post("/api/geography",
                    json={"country": "Saudi Arabia", "sector": "DROP TABLE users"},
                    headers=SHARED_HEADERS)
    assert r.status_code == 400


# ══════════════════════════════════════════
#  SECURITY HEADERS
# ══════════════════════════════════════════

def test_x_content_type_options():
    r = client.get("/api/auth/me")
    headers_lower = {k.lower(): v for k, v in r.headers.items()}
    assert headers_lower.get("x-content-type-options") == "nosniff"

def test_x_frame_options():
    r = client.get("/api/auth/me")
    headers_lower = {k.lower(): v for k, v in r.headers.items()}
    assert headers_lower.get("x-frame-options") == "DENY"

def test_x_xss_protection():
    r = client.get("/api/auth/me")
    headers_lower = {k.lower(): v for k, v in r.headers.items()}
    assert "x-xss-protection" in headers_lower

def test_cache_control():
    r = client.get("/api/auth/me")
    headers_lower = {k.lower(): v for k, v in r.headers.items()}
    assert headers_lower.get("cache-control") == "no-store"
