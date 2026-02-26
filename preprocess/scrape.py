import requests, re, hashlib, json, datetime, logging, unicodedata, pdfplumber
from trafilatura import fetch_url, extract, extract_metadata
from io import BytesIO
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

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


# ─────────────────────────────────────────────
# Chunking
# ─────────────────────────────────────────────
def chunk_para(text: str, max_words: int = 300, overlap_paragraphs: int = 1) -> list[str]:
    """
    Paragraph-aware chunking:
    - Split on blank lines first to respect semantic boundaries
    - Merge short paragraphs together until max_words is reached
    - Split long paragraphs (> max_words) by words with overlap
    - Keep last N paragraphs as overlap between chunks
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks = []
    current_paras = []
    current_word_count = 0

    for para in paragraphs:
        para_words = len(para.split())

        # Handle single paragraph that exceeds max_words — split by words
        if para_words > max_words:
            # Flush current accumulation first
            if current_paras:
                chunks.append("\n\n".join(current_paras))
                current_paras = current_paras[-overlap_paragraphs:]
                current_word_count = sum(len(p.split()) for p in current_paras)

            # Word-split the long paragraph with overlap
            words = para.split()
            start = 0
            word_chunks = []
            while start < len(words):
                word_chunks.append(" ".join(words[start:start + max_words]))
                start += max_words - 30  # 30-word overlap within long paragraphs

            # All word-chunks except last go directly to output
            chunks.extend(word_chunks[:-1])
            # Last one becomes start of next chunk for continuity
            current_paras = [word_chunks[-1]] if word_chunks else []
            current_word_count = len(current_paras[0].split()) if current_paras else 0
            continue

        # Normal case: adding this paragraph would exceed max_words — flush
        if current_word_count + para_words > max_words and current_paras:
            chunks.append("\n\n".join(current_paras))
            current_paras = current_paras[-overlap_paragraphs:]
            current_word_count = sum(len(p.split()) for p in current_paras)

        current_paras.append(para)
        current_word_count += para_words

    # Flush whatever's left
    if current_paras:
        chunks.append("\n\n".join(current_paras))

    # Filter out very short chunks (noise)
    return [c for c in chunks if len(c.split()) >= 20]


def chunk_document(doc: dict) -> list[dict]:
    chunks = chunk_para(doc["text"])

    total = len(chunks)
    results = []

    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.sha256((doc["doc_id"] + str(i)).encode()).hexdigest()
        results.append({
            "id": chunk_id,
            "doc_id": doc["doc_id"],
            "source_url": doc["source_url"],
            "title": doc.get("title", ""),
            "doc_type": doc.get("doc_type", "html"),
            "chunk_index": i,
            "total_chunks": total,
            "text": chunk,
        })

    return results

# Use thread
write_lock = __import__("threading").Lock()

def write_chunks(chunks: list[dict], output_file: str = "documents.jsonl") -> None:
    """Write chunks to JSONL. Lock ensures threads don't interleave writes."""
    with write_lock:
        with open(output_file, "a", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


# ─────────────────────────────────────────────
# Per-URL worker functions (run in threads)
# ─────────────────────────────────────────────
def process_one_html(url: str, output_file: str = "documents.jsonl") -> str:
    """Scrape one HTML URL and write its chunks. Returns status string."""
    doc = read_html(url)
    if not doc:
        return f"SKIP  {url}"
    chunks = chunk_document(doc)
    write_chunks(chunks, output_file)
    return f"OK    {url}  ({len(chunks)} chunks)"


def process_one_pdf(url: str, output_file: str = "documents.jsonl") -> str:
    """Download one PDF and write its chunks. Returns status string."""
    doc = read_pdf(url)
    if not doc:
        return f"SKIP  {url}"
    chunks = chunk_document(doc)
    write_chunks(chunks, output_file)
    return f"OK    {url}  ({len(chunks)} chunks)"


# ─────────────────────────────────────────────
# Multithreaded batch processors
# ─────────────────────────────────────────────
def process_html(urls: list[str], output_file: str = "documents.jsonl", max_workers: int = 8) -> None:
    """
    Scrape HTML URLs in parallel using a thread pool.
    max_workers=8 is a good default — enough to saturate network I/O
    without hammering any single server too hard.
    """
    logger.info(f"\nProcessing {len(urls)} HTML URLs with {max_workers} threads...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one_html, url, output_file): url for url in urls}

        for future in as_completed(futures):
            try:
                result = future.result()
                logger.info(result)
            except Exception as e:
                logger.error(f"Unexpected error for {futures[future]}: {e}")

    logger.info("HTML done.")


def process_pdf(urls: list[str], output_file: str = "documents.jsonl", max_workers: int = 4) -> None:
    """
    Download and process PDFs in parallel.
    Fewer workers than HTML (4) since PDFs are larger downloads.
    """
    logger.info(f"\nProcessing {len(urls)} PDF URLs with {max_workers} threads...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one_pdf, url, output_file): url for url in urls}

        for future in as_completed(futures):
            try:
                result = future.result()
                logger.info(result)
            except Exception as e:
                logger.error(f"Unexpected error for {futures[future]}: {e}")

    logger.info("PDF done.")


if __name__ == "__main__":
    with open("crawled_urls.json") as f:
        all_urls = json.load(f)

    html_urls = [u for u in all_urls if not u.endswith(".pdf")]
    pdf_urls = [u for u in all_urls if u.endswith(".pdf")]

    process_html(html_urls)
    process_pdf(pdf_urls)