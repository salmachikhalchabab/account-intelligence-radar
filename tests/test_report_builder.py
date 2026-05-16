import pytest
import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from report_builder import save_report, build_markdown


# ── Sample Data ──
SAMPLE_DATA = {
    "company": "Aramco",
    "headquarters": {
        "value": "Dhahran, Saudi Arabia",
        "source": "https://www.aramco.com/en/about-us"
    },
    "business_units": ["Upstream", "Downstream", "Technology"],
    "strategic_initiatives": [
        {
            "title": "AI Transformation",
            "detail": "Investment in AI-driven optimization",
            "source": "https://www.aramco.com/news"
        }
    ]
}


# ══════════════════════════════════════════
#  build_markdown
# ══════════════════════════════════════════

def test_build_markdown_returns_string():
    result = build_markdown("Aramco", SAMPLE_DATA)
    assert isinstance(result, str)

def test_build_markdown_contains_company():
    result = build_markdown("Aramco", SAMPLE_DATA)
    assert "Aramco" in result

def test_build_markdown_contains_keys():
    result = build_markdown("Aramco", SAMPLE_DATA)
    assert "headquarters" in result.lower() or "Headquarters" in result

def test_build_markdown_contains_values():
    result = build_markdown("Aramco", SAMPLE_DATA)
    assert "Dhahran" in result

def test_build_markdown_has_header():
    result = build_markdown("Aramco", SAMPLE_DATA)
    assert result.startswith("#")

def test_build_markdown_empty_data():
    result = build_markdown("TestCo", {})
    assert isinstance(result, str)


# ══════════════════════════════════════════
#  save_report
# ══════════════════════════════════════════

def test_save_report_returns_paths(tmp_path, monkeypatch):
    # Redirect reports to temp folder
    monkeypatch.chdir(tmp_path)
    os.makedirs("reports", exist_ok=True)

    paths = save_report("Aramco", SAMPLE_DATA)

    assert "json" in paths
    assert "markdown" in paths

def test_save_report_json_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs("reports", exist_ok=True)

    paths = save_report("Aramco", SAMPLE_DATA)
    assert os.path.exists(paths["json"])

def test_save_report_markdown_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs("reports", exist_ok=True)

    paths = save_report("Aramco", SAMPLE_DATA)
    assert os.path.exists(paths["markdown"])

def test_save_report_json_valid(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs("reports", exist_ok=True)

    paths = save_report("Aramco", SAMPLE_DATA)

    with open(paths["json"], "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["company"] == "Aramco"

def test_save_report_filename_contains_company(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs("reports", exist_ok=True)

    paths = save_report("STC Group", SAMPLE_DATA)
    assert "STC" in paths["json"] or "stc" in paths["json"].lower()

def test_save_report_markdown_not_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs("reports", exist_ok=True)

    paths = save_report("Aramco", SAMPLE_DATA)

    with open(paths["markdown"], "r", encoding="utf-8") as f:
        content = f.read()
    assert len(content) > 10
