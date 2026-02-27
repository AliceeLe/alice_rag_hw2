import requests, re, hashlib, datetime, logging, unicodedata, pdfplumber
from trafilatura import fetch_url, extract, extract_metadata
from io import BytesIO
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

def url_to_id(url):
    return hashlib.sha256(url.encode()).hexdigest()

def normalize_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def read_html(url):
    try:
        html_content = fetch_url(url)
        if not html_content:
            logger.warning(f"Empty response for {url}")
            return None

        text = extract(html_content, output_format="markdown", with_metadata=True)
        if not text:
            return None

        meta = extract_metadata(html_content)
        title = meta.title if meta else None

        return {
            "doc_id": url_to_id(url),
            "source_url": url,
            "title": title or "",
            "text": normalize_text(text),
            "doc_type": "html",
            "crawl_timestamp": datetime.datetime.now().isoformat(),
        }
    
    except Exception as e:
        return None

def read_pdf(url: str):
    try:
        resp = requests.get(url, timeout=30)

        text_parts = []
        with pdfplumber.open(BytesIO(resp.content)) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    # Tag page number so we can trace back if needed
                    text_parts.append(f"[Page {i+1}/{total_pages}]\n{page_text}")

        if not text_parts:
            return None

        raw_text = "\n\n".join(text_parts)
        # Derive a simple title from the URL filename
        filename = urlparse(url).path.rstrip("/").split("/")[-1]
        title = filename.replace("-", " ").replace("_", " ").replace(".pdf", "").title()

        return {
            "doc_id": url_to_id(url),
            "source_url": url,
            "title": title,
            "text": normalize_text(raw_text),
            "doc_type": "pdf",
            "crawl_timestamp": datetime.datetime.now().isoformat(),
        }
 
    except Exception as e:
        return None
