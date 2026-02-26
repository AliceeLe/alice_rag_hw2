import requests, re, hashlib, json, datetime, logging, unicodedata, pdfplumber
from trafilatura import fetch_url, extract, extract_metadata
from io import BytesIO
from urllib.parse import urlparse


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

pittsburgh_list_html = [
    "https://en.wikipedia.org/wiki/Pittsburgh", 
    "https://www.pittsburghpa.gov/Home",
    "https://www.britannica.com/place/Pittsburgh",
    "https://www.visitpittsburgh.com",
    "https://pittsburghpa.gov/finance/tax-forms",
    "https://www.cmu.edu/about/"
]

pittsburgh_list_pdf = [
    "https://www.pittsburghpa.gov/files/assets/city/v/4/omb/documents/operating-budgets/2025-operating-budget.pdf"
]

def url_to_id(url):
    return hashlib.sha256(url.encode()).hexdigest()

def normalize_text(text: str) -> str:
    """Unicode normalize, collapse whitespace, limit blank lines."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def read_html(url) -> dict | None:
    try:
        # Extract content 
        html_content = fetch_url(url)
        if not html_content:
            logger.warning(f"Empty response for {url}")
            return None

        text = extract(html_content, output_format="markdown", with_metadata=True)
        if not text:
            logger.warning(f"No extractable text at {url}")
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
        logger.error(f"read_html failed for {url}: {e}")
        return None

def read_pdf(url: str) -> dict | None:
    try:
        logger.info(f"Downloading PDF: {url}")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        text_parts = []
        with pdfplumber.open(BytesIO(resp.content)) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    # Tag page number so we can trace back if needed
                    text_parts.append(f"[Page {i+1}/{total_pages}]\n{page_text}")

        if not text_parts:
            logger.warning(f"No text extracted from PDF: {url}")
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
        logger.error(f"read_pdf failed for {url}: {e}")
        return None

# def chunk_para(text, max_words=300, overlap=50):
#     words = text.split()
#     chunks = []

#     start = 0
#     while start < len(words):
#         end = start + max_words
#         chunk = words[start:end]
#         chunks.append(" ".join(chunk))
#         start += max_words - overlap

#     return chunks

def chunk_para(text, max_words=300, overlap=50):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paragraphs

def chunk_document(doc):
    chunks = chunk_para(doc["text"])

    results = []
    total = len(chunks)

    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.sha256(
            (doc["doc_id"] + str(i)).encode()
        ).hexdigest()

        results.append({
            "id": chunk_id,
            "doc_id": doc["doc_id"],
            "source_url": doc["source_url"],
            "chunk_index": i,
            "total_chunks": total,
            "text": chunk
        })

    return results

def write_chunks(chunks, output_file="documents.jsonl"):
    with open(output_file, "a", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

def process_html(urls: list[str]):
    logger.info(f"\nProcessing {len(urls)} HTML URLs...")
    for url in urls:
        doc = read_html(url)
        if not doc:
            continue

        chunks = chunk_document(doc)
        write_chunks(chunks)
    logger.info("Done")

def process_pdf(urls: list[str]):
    logger.info(f"\nProcessing {len(urls)} PDF URLs...")
    for url in urls:
        doc = read_pdf(url)
        if not doc:
            continue

        chunks = chunk_document(doc)
        write_chunks(chunks)
    logger.info("Done")


if __name__=="__main__":
    # Get starting url 
    # Get a list of relevant urls from web crawler
    # Iterate through the list and call read_html
    # Standardize data???
    process_html(pittsburgh_list_html)
    process_pdf(pittsburgh_list_pdf)
