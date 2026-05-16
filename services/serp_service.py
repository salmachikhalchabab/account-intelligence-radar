import requests
from config import settings

BLOCKED_KEYWORDS = ["linkedin", "careers", "jobs", "glassdoor", "indeed"]

def search_google(query: str, num_results: int = 10):
    params = {
        "engine": "google",
        "q": query,
        "api_key": settings.SERPAPI_KEY,
        "num": num_results,
    }

    response = requests.get(settings.SERPAPI_URL, params=params)

    if response.status_code == 429:
        raise Exception("SerpAPI rate limit exceeded (429)")
    if response.status_code != 200:
        raise Exception(f"SerpAPI error: {response.text}")

    results = response.json().get("organic_results", [])

    filtered = []
    for r in results:
        link = r.get("link", "").lower()
        if any(word in link for word in BLOCKED_KEYWORDS):
            continue
        filtered.append({
            "title": r.get("title"),
            "snippet": r.get("snippet"),
            "link": r.get("link")
        })

    return filtered[:num_results]