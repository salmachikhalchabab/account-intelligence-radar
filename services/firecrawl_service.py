from firecrawl import Firecrawl
from config import settings
from error_handler import FirecrawlError


def scrape_markdown(urls: list) -> str:
    """
    Scrapes each URL individually.
    Skips failed URLs with a warning instead of crashing the full run.
    Raises FirecrawlError if ALL URLs fail.
    """
    firecrawl = Firecrawl(api_key=settings.FIRECRAWL_API_KEY)

    combined_text = ""
    failed = 0

    for url in urls:
        try:
            doc = firecrawl.scrape(url, formats=["markdown"])
            combined_text += f"\n\nSOURCE: {url}\n"
            combined_text += doc.markdown or ""
        except Exception as e:
            failed += 1
            print(f"⚠ Firecrawl failed for {url}: {e}")

    if failed == len(urls):
        raise FirecrawlError("All URLs failed during Firecrawl extraction.")

    return combined_text