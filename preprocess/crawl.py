import requests, json, logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

URL_LIST = [
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
    """Crawl only the seed page and its immediate links (2 levels)."""
    visited: set[str] = set()
    visited.add(start_url)
    to_crawl = [start_url]

    for current_url in to_crawl:
        try:
            resp = requests.get(current_url, timeout=8)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                continue
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch {current_url}: {e}")
            continue
        logger.info(f"Crawling URL: {current_url}")
        soup = BeautifulSoup(resp.text, "html.parser")
        base_domain = urlparse(start_url).netloc
        for tag in soup.find_all("a", href=True):
            next_url = urljoin(current_url, tag["href"]).split("#")[0]
            if not is_valid_url(next_url):
                continue
            if urlparse(next_url).netloc != base_domain:
                continue
            if next_url not in visited:
                # Don't want to store different languages
                if "oc_lang" in next_url:
                    continue
                visited.add(next_url)
                if current_url == start_url:
                    to_crawl.append(next_url)
                logger.info(f"Discovered (2 levels) URL: {next_url}")
    return visited

def crawl_all():
    all_urls = set()
    for seed in URL_LIST:
        discovered = bfs_crawl_domain(seed)
        all_urls.update(discovered)
    return sorted(all_urls)


if __name__ == "__main__":
    urls = crawl_all()

    output_file = "data/crawled_urls.json"
    with open(output_file, "w") as f:
        json.dump(urls, f, indent=2)

    print(f"\nSaved {len(urls)} URLs to {output_file}")