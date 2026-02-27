import requests
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


def is_valid_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    path = parsed.path.lower()
    if any(path.endswith(ext) for ext in SKIP_EXTENSIONS):
        return False
    if any(pat.lower() in url.lower() for pat in SKIP_PATTERNS):
        return False
    return True


def bfs_crawl_domain(start_url):
    """BFS crawl staying within the same domain as start_url."""
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque()

    base_domain = urlparse(start_url).netloc
    queue.append((start_url, 0))
    visited.add(start_url)

    while queue:
        current_url, depth = queue.popleft()

        try:
            resp = requests.get(current_url, timeout=8)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                continue
        except requests.RequestException as e:
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


def crawl_all():
    all_urls = set()

    for seed in SEED_URLS:
        discovered = bfs_crawl_domain(seed)
        all_urls.update(discovered)

    return sorted(all_urls)


if __name__ == "__main__":
    urls = crawl_all()

    output_file = "crawled_urls.json"
    with open(output_file, "w") as f:
        json.dump(urls, f, indent=2)

    print(f"\nSaved {len(urls)} URLs to {output_file}")