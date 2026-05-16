import json
from services.llm_extractor import call_llm, clean_json_response
from error_handler import InvalidJSONError


def extract_company_list(search_results: list, country: str = "", city: str = "", sector: str = "") -> list:

    location_parts = [p for p in [city, country] if p]
    location_str = ", ".join(location_parts) if location_parts else "the specified region"
    sector_str = sector if sector else "the specified sector"

    prompt = f"""
You are a strict business intelligence filter.

TARGET LOCATION: {location_str}
TARGET SECTOR: {sector_str}

Your task: From the search results below, extract up to 5 company names.

STRICT RULES — violating any rule means the company must be EXCLUDED:
1. The company MUST be headquartered OR primarily operating in: {location_str}
2. The company MUST be in the sector: {sector_str}
3. EXCLUDE any company from a different country — even if the name sounds local
4. EXCLUDE news sites, directories, government bodies, NGOs
5. EXCLUDE any company you are not confident is from {location_str}
6. If no qualifying companies are found, return an empty list

When in doubt — EXCLUDE. It is better to return fewer companies than wrong ones.

Return ONLY this JSON format with no explanation:
{{
  "companies": ["Company Name 1", "Company Name 2"]
}}

Search results:
{json.dumps(search_results, indent=2)[:8000]}
"""

    content = call_llm(prompt)
    content = clean_json_response(content)

    try:
        parsed = json.loads(content)
        companies = parsed.get("companies", [])
        # Extra safety: filter empty strings
        return [c for c in companies if isinstance(c, str) and len(c.strip()) > 2]
    except json.JSONDecodeError as e:
        raise InvalidJSONError(f"Company discovery returned invalid JSON: {e}")
