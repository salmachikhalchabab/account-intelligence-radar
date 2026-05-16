import json
from services.llm_extractor import call_llm, clean_json_response
from error_handler import InvalidJSONError


def build_prompt(company_name: str, search_results: list, objective: str) -> str:
    return f"""
You are a business intelligence analyst.

Objective:
{objective}

Select the best 3 URLs that help achieve this objective.
Avoid job pages and LinkedIn.

Return ONLY valid JSON:

{{
  "selected_urls": ["url1", "url2", "url3"]
}}

Search results:
{json.dumps(search_results, indent=2)}
"""


def select_best_urls(company_name: str, search_results: list, objective: str) -> list:
    prompt = build_prompt(company_name, search_results, objective)

    content = call_llm(prompt)
    content = clean_json_response(content)

    try:
        parsed = json.loads(content)
        return parsed.get("selected_urls", [])
    except json.JSONDecodeError as e:
        raise InvalidJSONError(f"URL selector returned invalid JSON: {e}")