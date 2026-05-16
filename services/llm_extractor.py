import json
import re
import requests
from config import settings
from error_handler import LLMError, LLMInsufficientBalanceError, InvalidJSONError


# ==============================
# Prompt Builder
# ==============================

def build_extraction_prompt(company_name: str, markdown_content: str, objective: str,
                             expected_country: str = "") -> str:

    location_warning = ""
    if expected_country:
        location_warning = f"""
LOCATION VALIDATION:
- This company is expected to be from: {expected_country}
- If the scraped content clearly belongs to a DIFFERENT company or country, return:
  {{"error": "content_mismatch", "reason": "Content does not match the expected company or location"}}
- Do NOT extract data from the wrong company just because the URL was returned in search results.
"""

    return f"""
You are a business intelligence extraction engine.

Company: {company_name}
{location_warning}
Objective:
{objective}

Rules:
- Use ONLY the provided content.
- Extract only factual information with source URLs.
- Return ONLY valid JSON.
- Do NOT include explanations or commentary.
- Structure the JSON dynamically based on the objective.
- Use meaningful keys.

CONTENT:
{markdown_content[:12000]}
"""


# ==============================
# JSON Cleaner
# ==============================

def clean_json_response(content: str) -> str:
    content = re.sub(r"```json", "", content)
    content = re.sub(r"```", "", content)
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1:
        content = content[start:end + 1]
    return content.strip()


def _build_json_repair_prompt(broken_json: str) -> str:
    return f"""
You are a JSON repair tool.
Fix the following content so it becomes STRICTLY valid JSON.
Do not add commentary, markdown fences, or explanations.
Preserve as much data as possible.
If a value is truncated, replace it with null.

BROKEN_JSON:
{broken_json}
""".strip()


def repair_json_response_via_llm(broken_json: str) -> str:
    prompt = _build_json_repair_prompt(broken_json)
    content = call_llm(prompt)
    return clean_json_response(content)


# ==============================
# Shared LLM Call
# ==============================

def call_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Account Intelligence Radar"
    }

    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": "Return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    response = requests.post(settings.OPENROUTER_URL, headers=headers, json=payload, timeout=30)

    if response.status_code == 402:
        raise LLMInsufficientBalanceError("Insufficient balance — HTTP 402.")
    if response.status_code != 200:
        raise LLMError(f"LLM API Error {response.status_code}: {response.text}")

    data = response.json()
    if "choices" not in data:
        raise LLMError(f"Unexpected LLM response structure: {data}")

    return data["choices"][0]["message"]["content"]


# ==============================
# Main Extraction Function
# ==============================

def extract_structured_json(company_name: str, markdown_content: str, objective: str,
                             expected_country: str = "") -> dict:

    prompt = build_extraction_prompt(company_name, markdown_content, objective, expected_country)
    content = call_llm(prompt)
    cleaned = clean_json_response(content)

    try:
        result = json.loads(cleaned)

        # If LLM detected a content mismatch — raise clear error
        if result.get("error") == "content_mismatch":
            raise InvalidJSONError(
                f"Content mismatch for '{company_name}': {result.get('reason', 'wrong location or company')}"
            )

        return result

    except json.JSONDecodeError as e:
        try:
            repaired = repair_json_response_via_llm(cleaned)
            return json.loads(repaired)
        except Exception:
            raise InvalidJSONError(
                f"Could not parse LLM response as JSON: {e}\nRaw: {cleaned[:300]}"
            )
