import os
os.makedirs("data", exist_ok=True)
import json, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from scrape import read_pdf, read_html
from chunk import chunk_document

logger = logging.getLogger(__name__)

# Use thread
write_lock = __import__("threading").Lock()

def write_chunks(chunks: list[dict]):
    """Write chunks to JSONL. Lock ensures threads don't interleave writes."""
    with write_lock:
        with open("data/documents.jsonl", "a", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

# Per-URL worker functions 
def process_one_html(url):
    doc = read_html(url)
    if not doc:
        return
    chunks = chunk_document(doc)
    write_chunks(chunks)

def process_one_pdf(url):
    doc = read_pdf(url)
    if not doc:
        return
    chunks = chunk_document(doc)
    write_chunks(chunks)

# Multithreaded batch processors
def process_html(urls: list[str], max_workers: int = 8) -> None:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one_html, url): url for url in urls}
        for future in as_completed(futures):
            try:
                result = future.result()
                logger.info(result)
            except Exception as e:
                logger.error(f"Unexpected error for {futures[future]}: {e}")

    logger.info("HTML done.")


def process_pdf(urls: list[str], max_workers: int = 4) -> None:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one_pdf, url): url for url in urls}

        for future in as_completed(futures):
            try:
                result = future.result()
                logger.info(result)
            except Exception as e:
                logger.error(f"Unexpected error for {futures[future]}: {e}")

    logger.info("PDF done.")


if __name__ == "__main__":
    with open("data/crawled_urls.json") as f:
        all_urls = json.load(f)
    html_urls = [u for u in all_urls if not u.endswith(".pdf")]
    pdf_urls = [u for u in all_urls if u.endswith(".pdf")]

    process_html(html_urls)
    process_pdf(pdf_urls)