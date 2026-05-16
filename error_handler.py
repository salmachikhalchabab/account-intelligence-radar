import requests


class RadarError(Exception):
    """Base error for Account Intelligence Radar."""
    pass


class SerpAPIError(RadarError):
    pass


class LLMError(RadarError):
    pass


class LLMInsufficientBalanceError(LLMError):
    pass


class FirecrawlError(RadarError):
    pass


class InvalidJSONError(RadarError):
    pass


def handle_error(e: Exception):
    """
    Classifies and prints a human-readable error message.
    Called at the top level to avoid crashing the full run.
    """

    if isinstance(e, LLMInsufficientBalanceError):
        print("\n[ERROR] LLM API — Insufficient balance (402).")
        print("→ Top up your OpenRouter/DeepSeek account and retry.\n")

    elif isinstance(e, LLMError):
        print(f"\n[ERROR] LLM API failure: {e}\n")

    elif isinstance(e, SerpAPIError):
        print(f"\n[ERROR] SerpAPI failure: {e}\n")

    elif isinstance(e, FirecrawlError):
        print(f"\n[ERROR] Firecrawl failure: {e}\n")

    elif isinstance(e, InvalidJSONError):
        print(f"\n[ERROR] Could not parse JSON from LLM response: {e}\n")
        print("→ Try again — the model may have returned malformed output.\n")

    elif isinstance(e, requests.exceptions.Timeout):
        print("\n[ERROR] Request timed out.")
        print("→ Check your internet connection or retry later.\n")

    elif isinstance(e, requests.exceptions.ConnectionError):
        print("\n[ERROR] Network connection error.")
        print("→ Check your internet connection.\n")

    else:
        print(f"\n[ERROR] Unexpected error: {type(e).__name__}: {e}\n")