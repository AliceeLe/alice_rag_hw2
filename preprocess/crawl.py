import requests
import time
import json
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SEED_URLS = [
    # General info / history
    "https://en.wikipedia.org/wiki/Pittsburgh",
    "https://en.wikipedia.org/wiki/History_of_Pittsburgh",
    "https://www.pittsburghpa.gov/Home",
    "https://www.britannica.com/place/Pittsburgh",
    "https://www.visitpittsburgh.com",
    "https://www.cmu.edu/about/",
    "https://www.cmu.edu/about/history.shtml",

    # Events
    "https://www.visitpittsburgh.com/events/",
    "https://www.downtownpittsburgh.com/events/",
    "https://www.pghcitypaper.com/pittsburgh/EventSearch",
    "https://events.cmu.edu/",
    "https://www.cmu.edu/engage/alumni/events/campus-events/index.html",

    # Music & culture
    "https://pittsburghsymphony.org",
    "https://www.pittsburghopera.org",
    "https://trustarts.org",
    "https://carnegiemuseums.org",
    "https://heinzhistorycenter.org",
    "https://www.thefrickpittsburgh.org",

    # Food events
    "https://www.picklesburgh.com",
    "https://www.pittsburghtacofest.com",
    "https://www.pittsburghrestaurantweek.com",
    "https://www.bananasplitfest.com",

    # Sports
    "https://www.mlb.com/pirates",
    "https://www.steelers.com",
    "https://www.nhl.com/penguins",
    "https://www.visitpittsburgh.com/things-to-do/sports/",
]


# Depth per domain — how many link-hops to follow
DOMAIN_MAX_DEPTH = {
    "en.wikipedia.org": 1,
    "www.visitpittsburgh.com": 2,
    "www.pittsburghpa.gov": 2,
    "events.cmu.edu": 2,
    "www.cmu.edu": 2,
    "pittsburghsymphony.org": 2,
    "carnegiemuseums.org": 2,
    "heinzhistorycenter.org": 2,
    "www.pghcitypaper.com": 1,
    "www.downtownpittsburgh.com": 2,
    "trustarts.org": 2,
}
DEFAULT_MAX_DEPTH = 1

MAX_PAGES_PER_DOMAIN = 50
CRAWL_DELAY = 0.5  # seconds between requests

# ─────────────────────────────────────────────
# URL filtering
# ─────────────────────────────────────────────
SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg",
    ".css", ".js", ".zip", ".mp3", ".mp4",
    ".doc", ".docx", ".pdf",  # PDFs handled separately in scrape.py
}

SKIP_PATTERNS = [
    "/wp-login", "/wp-admin", "/feed/", "/tag/", "/author/",
    "action=edit", "printable=yes",
    "Special:", "Talk:", "User:", "File:", "Help:", "Template:",
]


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    path = parsed.path.lower()
    if any(path.endswith(ext) for ext in SKIP_EXTENSIONS):
        return False
    if any(pat.lower() in url.lower() for pat in SKIP_PATTERNS):
        return False
    return True


# ─────────────────────────────────────────────
# Core BFS crawler (single domain)
# ─────────────────────────────────────────────
def bfs_crawl_domain(start_url: str, max_depth: int, max_pages: int) -> set[str]:
    """BFS crawl staying within the same domain as start_url."""
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque()

    base_domain = urlparse(start_url).netloc
    queue.append((start_url, 0))
    visited.add(start_url)

    while queue:
        current_url, depth = queue.popleft()

        if len(visited) >= max_pages:
            logger.info(f"  Hit page cap ({max_pages}) for {base_domain}")
            break

        logger.info(f"  [depth={depth}] {current_url}")

        try:
            resp = requests.get(current_url, timeout=8)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                continue
        except requests.RequestException as e:
            logger.warning(f"  Request failed: {current_url} — {e}")
            continue

        time.sleep(CRAWL_DELAY)

        if depth >= max_depth:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup.find_all("a", href=True):
            # Strip URL fragments (#section) — they point to the same page
            next_url = urljoin(current_url, tag["href"]).split("#")[0]

            if not is_valid_url(next_url):
                continue
            if urlparse(next_url).netloc != base_domain:
                continue
            if next_url not in visited:
                visited.add(next_url)
                queue.append((next_url, depth + 1))

    return visited


# ─────────────────────────────────────────────
# Crawl all seeds
# ─────────────────────────────────────────────
def crawl_all(seed_urls: list[str] = SEED_URLS) -> list[str]:
    """
    Crawl all seed URLs and return a flat sorted list of discovered HTML URLs.
    """
    all_urls: set[str] = set()

    for seed in seed_urls:
        domain = urlparse(seed).netloc
        max_depth = DEFAULT_MAX_DEPTH

        logger.info(f"\n{'='*60}")
        logger.info(f"Crawling: {seed}  (max_depth={max_depth})")
        logger.info(f"{'='*60}")

        discovered = bfs_crawl_domain(seed, max_depth, MAX_PAGES_PER_DOMAIN)
        all_urls.update(discovered)
        logger.info(f"  Found {len(discovered)} URLs from {domain}")

    return sorted(all_urls)


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    urls = crawl_all()

    output_file = "crawled_urls.json"
    with open(output_file, "w") as f:
        json.dump(urls, f, indent=2)

    print(f"\nSaved {len(urls)} URLs to {output_file}")