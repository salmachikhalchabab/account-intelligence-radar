import urllib.robotparser
import urllib.request
import time
from urllib.parse import urlparse

# ── Bot Identity ──
# Identify your bot properly — required for ethical compliance
BOT_USER_AGENT = "AccountIntelligenceRadar/1.0 (+https://github.com/salma-sheikhalshabab/account-intelligence-radar)"

# ── ToS Block List ──
# Sites that explicitly prohibit scraping via Terms of Service
# regardless of what robots.txt says
TOS_BLOCKED_DOMAINS = {
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "snapchat.com",
    "pinterest.com",
    "glassdoor.com",
    "indeed.com",
    "crunchbase.com",
    "zoominfo.com",
}

# ── Noise URL Patterns ──
# URLs that contain no business intelligence value
NOISE_PATTERNS = [
    "/login", "/signin", "/signup", "/register",
    "/cart", "/checkout", "/payment",
    "/cdn-cgi/", "/wp-admin/",
    ".pdf", ".zip", ".exe",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".mp4", ".mp3"
]


def get_domain(url: str) -> str:
    return urlparse(url).netloc.lower().replace("www.", "")


def is_tos_blocked(url: str) -> bool:
    domain = get_domain(url)
    return any(blocked in domain for blocked in TOS_BLOCKED_DOMAINS)


def is_noise_url(url: str) -> bool:
    return any(p in url.lower() for p in NOISE_PATTERNS)


def get_robots_parser(url: str) -> urllib.robotparser.RobotFileParser:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)

    try:
        req = urllib.request.Request(
            robots_url,
            headers={"User-Agent": BOT_USER_AGENT}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            rp.parse(content.splitlines())
    except Exception:
        pass  # Assume allowed if robots.txt unreachable

    return rp


def get_crawl_delay(rp: urllib.robotparser.RobotFileParser) -> float:
    """Respect Crawl-delay directive from robots.txt."""
    try:
        delay = rp.crawl_delay(BOT_USER_AGENT) or rp.crawl_delay("*")
        if delay:
            return float(delay)
    except Exception:
        pass
    return 1.0  # Default: 1 second minimum between requests


def filter_allowed_urls(urls: list) -> list:
    """
    3-layer URL filter:

    Layer 1 — ToS Block List
        Blocks domains that explicitly prohibit scraping in their Terms of Service.
        robots.txt alone is not enough — ToS is legally binding in many jurisdictions.

    Layer 2 — Noise Filter
        Removes URLs with no intelligence value (login pages, media files, etc.)

    Layer 3 — robots.txt Compliance
        Checks robots.txt using an identified User-Agent (not anonymous).
        Respects Crawl-delay between requests to the same domain.
    """
    allowed_urls = []
    last_request_time: dict[str, float] = {}

    for url in urls:

        # ── Layer 1: ToS ──
        if is_tos_blocked(url):
            print(f"⛔ ToS blocked [{get_domain(url)}]: {url}")
            continue

        # ── Layer 2: Noise ──
        if is_noise_url(url):
            print(f"⚠  Noise URL skipped: {url}")
            continue

        # ── Layer 3: robots.txt ──
        try:
            rp = get_robots_parser(url)
            allowed = rp.can_fetch(BOT_USER_AGENT, url)
            crawl_delay = get_crawl_delay(rp)
        except Exception:
            allowed = True
            crawl_delay = 1.0

        if not allowed:
            print(f"🤖 Blocked by robots.txt: {url}")
            continue

        # ── Crawl-delay: respect timing per domain ──
        domain = get_domain(url)
        now = time.time()

        if domain in last_request_time:
            elapsed = now - last_request_time[domain]
            if elapsed < crawl_delay:
                wait_time = crawl_delay - elapsed
                print(f"⏱  Crawl-delay: waiting {wait_time:.1f}s for {domain}")
                time.sleep(wait_time)

        last_request_time[domain] = time.time()
        allowed_urls.append(url)
        print(f"✅ Approved: {url}")

    return allowed_urls
