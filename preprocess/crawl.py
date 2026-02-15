import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque


def bfs_crawl(start_url, max_depth=2):
    visited = set()
    queue = deque()

    # (url, depth)
    queue.append((start_url, 0))
    visited.add(start_url)

    base_domain = urlparse(start_url).netloc

    while queue:
        current_url, depth = queue.popleft()

        print(f"[Depth {depth}] Visiting: {current_url}")

        if depth >= max_depth:
            continue

        try:
            response = requests.get(current_url, timeout=5)
            response.raise_for_status()
        except requests.RequestException:
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract all anchor tags
        for tag in soup.find_all("a", href=True):
            href = tag["href"]

            # Convert relative URL to absolute
            next_url = urljoin(current_url, href)

            parsed = urlparse(next_url)

            # Skip non-http links (mailto, javascript, etc.)
            if parsed.scheme not in {"http", "https"}:
                continue

            # Optional: stay within same domain
            if parsed.netloc != base_domain:
                continue

            if next_url not in visited:
                visited.add(next_url)
                queue.append((next_url, depth + 1))

    return visited


if __name__ == "__main__":
    start = "https://www.cmu.edu/"
    result = bfs_crawl(start, max_depth=1)
    print(result)
    print("\nTotal pages visited:", len(result))
