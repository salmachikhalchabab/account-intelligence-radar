import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from robots_checker import (
    is_tos_blocked,
    is_noise_url,
    get_domain,
    filter_allowed_urls
)


# ══════════════════════════════════════════
#  get_domain
# ══════════════════════════════════════════

def test_get_domain_basic():
    assert get_domain("https://www.linkedin.com/company/stc") == "linkedin.com"

def test_get_domain_no_www():
    assert get_domain("https://aramco.com/about") == "aramco.com"

def test_get_domain_subdomain():
    assert get_domain("https://careers.stc.com.sa") == "careers.stc.com.sa"


# ══════════════════════════════════════════
#  is_tos_blocked
# ══════════════════════════════════════════

def test_linkedin_blocked():
    assert is_tos_blocked("https://www.linkedin.com/company/aramco") is True

def test_facebook_blocked():
    assert is_tos_blocked("https://www.facebook.com/stc") is True

def test_twitter_blocked():
    assert is_tos_blocked("https://twitter.com/aramco") is True

def test_x_blocked():
    assert is_tos_blocked("https://x.com/sabic") is True

def test_glassdoor_blocked():
    assert is_tos_blocked("https://www.glassdoor.com/Reviews/aramco") is True

def test_indeed_blocked():
    assert is_tos_blocked("https://www.indeed.com/cmp/aramco") is True

def test_crunchbase_blocked():
    assert is_tos_blocked("https://www.crunchbase.com/organization/aramco") is True

def test_legitimate_site_not_blocked():
    assert is_tos_blocked("https://www.aramco.com/about") is False

def test_stc_not_blocked():
    assert is_tos_blocked("https://www.stc.com.sa") is False

def test_wikipedia_not_blocked():
    assert is_tos_blocked("https://en.wikipedia.org/wiki/Saudi_Aramco") is False


# ══════════════════════════════════════════
#  is_noise_url
# ══════════════════════════════════════════

def test_login_page_is_noise():
    assert is_noise_url("https://example.com/login") is True

def test_signup_page_is_noise():
    assert is_noise_url("https://example.com/signup") is True

def test_cart_is_noise():
    assert is_noise_url("https://example.com/cart") is True

def test_pdf_file_is_noise():
    assert is_noise_url("https://example.com/report.pdf") is True

def test_image_is_noise():
    assert is_noise_url("https://example.com/logo.png") is True

def test_wp_admin_is_noise():
    assert is_noise_url("https://example.com/wp-admin/dashboard") is True

def test_about_page_not_noise():
    assert is_noise_url("https://example.com/about") is False

def test_news_page_not_noise():
    assert is_noise_url("https://example.com/news/2025") is False

def test_homepage_not_noise():
    assert is_noise_url("https://aramco.com") is False


# ══════════════════════════════════════════
#  filter_allowed_urls
# ══════════════════════════════════════════

def test_filter_removes_linkedin():
    urls = ["https://www.linkedin.com/company/stc", "https://www.stc.com.sa"]
    result = filter_allowed_urls(urls)
    assert "https://www.linkedin.com/company/stc" not in result

def test_filter_removes_noise():
    urls = ["https://example.com/login", "https://aramco.com/about"]
    result = filter_allowed_urls(urls)
    assert "https://example.com/login" not in result

def test_filter_empty_list():
    assert filter_allowed_urls([]) == []

def test_filter_all_blocked():
    urls = [
        "https://www.linkedin.com/company/aramco",
        "https://www.facebook.com/stc",
        "https://twitter.com/sabic",
    ]
    result = filter_allowed_urls(urls)
    assert result == []
