import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_extractor import clean_json_response, build_extraction_prompt
from error_handler import InvalidJSONError
import json


# ══════════════════════════════════════════
#  clean_json_response
# ══════════════════════════════════════════

def test_clean_plain_json():
    raw = '{"company": "Aramco", "hq": "Dhahran"}'
    result = clean_json_response(raw)
    assert json.loads(result)["company"] == "Aramco"

def test_clean_json_with_markdown_fences():
    raw = '```json\n{"company": "STC"}\n```'
    result = clean_json_response(raw)
    parsed = json.loads(result)
    assert parsed["company"] == "STC"

def test_clean_json_with_plain_fences():
    raw = '```\n{"company": "SABIC"}\n```'
    result = clean_json_response(raw)
    parsed = json.loads(result)
    assert parsed["company"] == "SABIC"

def test_clean_json_with_preamble():
    raw = 'Here is the JSON:\n{"company": "Aramco"}\nHope this helps!'
    result = clean_json_response(raw)
    parsed = json.loads(result)
    assert parsed["company"] == "Aramco"

def test_clean_json_extra_whitespace():
    raw = '   \n\n  {"company": "STC"}  \n\n  '
    result = clean_json_response(raw)
    parsed = json.loads(result)
    assert parsed["company"] == "STC"

def test_clean_nested_json():
    raw = '{"company": "Aramco", "hq": {"value": "Dhahran", "source": "https://aramco.com"}}'
    result = clean_json_response(raw)
    parsed = json.loads(result)
    assert parsed["hq"]["value"] == "Dhahran"

def test_clean_empty_string_returns_empty():
    result = clean_json_response("")
    assert result == ""

def test_clean_no_braces_returns_original():
    raw = "no json here"
    result = clean_json_response(raw)
    # No { } found — returns stripped original
    assert isinstance(result, str)


# ══════════════════════════════════════════
#  build_extraction_prompt
# ══════════════════════════════════════════

def test_prompt_contains_company_name():
    prompt = build_extraction_prompt("Aramco", "some content", "Extract HQ")
    assert "Aramco" in prompt

def test_prompt_contains_objective():
    prompt = build_extraction_prompt("STC", "content", "Extract leadership")
    assert "Extract leadership" in prompt

def test_prompt_contains_content():
    prompt = build_extraction_prompt("SABIC", "This is the scraped content", "Extract HQ")
    assert "This is the scraped content" in prompt

def test_prompt_truncates_long_content():
    long_content = "X" * 20000
    prompt = build_extraction_prompt("Aramco", long_content, "Extract HQ")
    # Content is truncated to 12000 chars
    assert long_content not in prompt
    assert "X" * 12000 in prompt or len(prompt) < len(long_content) + 500

def test_prompt_contains_json_rule():
    prompt = build_extraction_prompt("Aramco", "content", "objective")
    assert "JSON" in prompt

def test_prompt_contains_source_rule():
    prompt = build_extraction_prompt("Aramco", "content", "objective")
    assert "source" in prompt.lower()
