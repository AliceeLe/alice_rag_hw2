import requests, json, logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

URL_LIST = [
    # General info / history
    "https://www.pittsburghpa.gov/Home",
    "https://www.visitpittsburgh.com",
    "https://en.wikipedia.org/wiki/Pittsburgh",
    "https://en.wikipedia.org/wiki/History_of_Pittsburgh",
    "https://en.wikipedia.org/wiki/Carnegie_Mellon_University",
    "https://en.wikipedia.org/wiki/Andrew_Carnegie",
    "https://en.wikipedia.org/wiki/University_of_Pittsburgh",
    "https://en.wikipedia.org/wiki/Carnegie_Steel_Company",
    "https://en.wikipedia.org/wiki/Fort_Pitt_(Pennsylvania)",
    "https://en.wikipedia.org/wiki/Great_Fire_of_Pittsburgh",
    "https://en.wikipedia.org/wiki/Three_Rivers_Stadium",
    "https://en.wikipedia.org/wiki/Acrisure_Stadium",
    "https://en.wikipedia.org/wiki/PNC_Park",
    "https://en.wikipedia.org/wiki/PPG_Paints_Arena",
    "https://en.wikipedia.org/wiki/Roberto_Clemente_Bridge",
    "https://en.wikipedia.org/wiki/Duquesne_Incline",
    "https://en.wikipedia.org/wiki/Ohio_River",
    "https://en.wikipedia.org/wiki/Allegheny_River",
    "https://en.wikipedia.org/wiki/Monongahela_River",
    "https://en.wikipedia.org/wiki/Strip_District,_Pittsburgh",
    "https://en.wikipedia.org/wiki/Squirrel_Hill",
    "https://en.wikipedia.org/wiki/Lawrenceville_(Pittsburgh)",
    "https://en.wikipedia.org/wiki/Allegheny_County,_Pennsylvania",
    "https://en.wikipedia.org/wiki/Mellon_Institute_of_Industrial_Research",
    "https://en.wikipedia.org/wiki/Andrew_Mellon",
    "https://en.wikipedia.org/wiki/Richard_B._Mellon",
    "https://en.wikipedia.org/wiki/Carnegie_Mellon_College_of_Engineering",
    "https://en.wikipedia.org/wiki/Carnegie_Mellon_School_of_Computer_Science",
    "https://en.wikipedia.org/wiki/Dietrich_College_of_Humanities_and_Social_Sciences",
    "https://en.wikipedia.org/wiki/Tepper_School_of_Business",
    "https://en.wikipedia.org/wiki/Downtown_Pittsburgh",
    "https://en.wikipedia.org/wiki/Carnegie_Mellon_University_Africa",
    "https://en.wikipedia.org/wiki/Farnam_Jahanian",
    "https://en.wikipedia.org/wiki/Margaret_Morrison_Carnegie_College",
    "https://en.wikipedia.org/wiki/Pittsburgh_Panthers",
    "https://en.wikipedia.org/wiki/Atlantic_Coast_Conference",
    "https://en.wikipedia.org/wiki/Cathedral_of_Learning",
    "https://en.wikipedia.org/wiki/Phipps_Conservatory_and_Botanical_Gardens",
    "https://en.wikipedia.org/wiki/Pittsburgh_Symphony_Orchestra",
    "https://en.wikipedia.org/wiki/Pittsburgh_Opera",
    "https://en.wikipedia.org/wiki/Pittsburgh_Ballet_Theatre",
    "https://en.wikipedia.org/wiki/Pittsburgh_Cultural_Trust",
    "https://en.wikipedia.org/wiki/Benedum_Center",
    "https://en.wikipedia.org/wiki/Byham_Theater",
    "https://en.wikipedia.org/wiki/Heinz_Hall",
    "https://en.wikipedia.org/wiki/Stage_AE",
    "https://en.wikipedia.org/wiki/August_Wilson_African_American_Cultural_Center",
    "https://en.wikipedia.org/wiki/The_Frick_Pittsburgh",
    "https://en.wikipedia.org/wiki/National_Aviary",
    "https://en.wikipedia.org/wiki/Carnegie_Museums_of_Pittsburgh",
    "https://en.wikipedia.org/wiki/Carnegie_Museum_of_Art",
    "https://en.wikipedia.org/wiki/Carnegie_Museum_of_Natural_History",
    "https://en.wikipedia.org/wiki/The_Andy_Warhol_Museum",
    "https://en.wikipedia.org/wiki/Heinz_History_Center",
    "https://en.wikipedia.org/wiki/Mattress_Factory",
    "https://en.wikipedia.org/wiki/The_Clemente_Museum",
    "https://en.wikipedia.org/wiki/Carnegie_Museum_of_Art#Heinz_Architectural_Center",
    "https://en.wikipedia.org/wiki/Buhl_Planetarium_and_Institute_of_Popular_Science_Building",
    "https://en.wikipedia.org/wiki/Kamin_Science_Center",
    "https://en.wikipedia.org/wiki/Picklesburgh",
    "https://en.wikipedia.org/wiki/Pittsburgh_Vintage_Grand_Prix",
    "https://en.wikipedia.org/wiki/Pittsburgh_Folk_Festival",
    "https://en.wikipedia.org/wiki/Pittsburgh_Steelers",
    "https://en.wikipedia.org/wiki/Pittsburgh_Penguins",
    "https://en.wikipedia.org/wiki/Pittsburgh_Pirates",
    "https://en.wikipedia.org/wiki/Pittsburgh_Riverhounds_SC",
    "https://en.wikipedia.org/wiki/Pittsburgh_Passion",
    "https://en.wikipedia.org/wiki/Pittsburgh_Maulers_(1984)",
    "https://en.wikipedia.org/wiki/Roberto_Clemente",
    "https://en.wikipedia.org/wiki/Chuck_Noll",
    "https://en.wikipedia.org/wiki/Terrible_Towel",
    "https://en.wikipedia.org/wiki/Forbes_Field",
    "https://en.wikipedia.org/wiki/Fort_Duquesne",
    "https://en.wikipedia.org/wiki/Boulevard_of_the_Allies",
    "https://en.wikipedia.org/wiki/Powdermill_Nature_Reserve",
    "https://en.wikipedia.org/wiki/Frick_Park",
    "https://en.wikipedia.org/wiki/Campbell%27s_Soup_Cans",
    "https://en.wikipedia.org/wiki/David_Lynch",
    "https://en.wikipedia.org/wiki/Western_Pennsylvania",
    "https://en.wikipedia.org/wiki/List_of_bridges_of_Pittsburgh"

    # CMU
    "https://www.cmu.edu/about/",
    "https://www.cmu.edu/about/history.shtml",
    "https://www.visitpittsburgh.com/things-to-do/arts-culture/history/",
    
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
    
    # Sports schedules
    "https://www.steelers.com/schedule/",
    "https://www.nhl.com/penguins/schedule",
    "https://www.mlb.com/pirates/schedule",
]

SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg",
    ".css", ".js", ".zip", ".mp3", ".mp4",
    ".doc", ".docx", ".pdf",  
}

SKIP_PATTERNS = [
    "/wp-login", "/wp-admin", "/feed/", "/tag/", "/author/",
    "action=edit", "printable=yes",
    "Special:", "Talk:", "User:", "File:", "Help:", "Template:",
]

def is_valid_url(url, base_domain) -> bool:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        return False
    
    if parsed.netloc != base_domain:
        return False

    path = parsed.path.lower()

    if any(path.endswith(ext) for ext in SKIP_EXTENSIONS):
        return False

    if any(p in url.lower() for p in SKIP_PATTERNS):
        return False

    if "lang=" in parsed or "oc_lang=" in parsed:
        return False

    return True


def crawl_domain(seed_url):
    visited = set()
    base_domain = urlparse(seed_url).netloc

    queue = deque()
    queue.append((seed_url, 0))
    visited.add(seed_url)

    while queue:
        current_url, depth = queue.popleft()

        if depth > 1:
            continue

        try:
            resp = requests.get(current_url, timeout=8)
            resp.raise_for_status()

            if "text/html" not in resp.headers.get("Content-Type", ""):
                continue

        except requests.RequestException:
            continue

        logger.info(f"[Depth {depth}] {current_url}")

        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup.find_all("a", href=True):
            next_url = urljoin(current_url, tag["href"]).split("#")[0]

            if next_url in visited:
                continue

            if is_valid_url(next_url, base_domain):
                visited.add(next_url)
                queue.append((next_url, depth + 1))

    return visited

def crawl_all():
    all_urls = set()
    for seed in URL_LIST:
        discovered = crawl_domain(seed)
        all_urls.update(discovered)
    return sorted(all_urls)

if __name__ == "__main__":
    urls = crawl_all()

    output_file = "data/crawled_urls.json"
    with open(output_file, "w") as f:
        json.dump(urls, f, indent=2)

    print(f"\nSaved {len(urls)} URLs to {output_file}")