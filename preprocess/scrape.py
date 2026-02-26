import requests, re, hashlib, json, datetime, logging, unicodedata
from trafilatura import fetch_url, extract, extract_metadata
from bs4 import BeautifulSoup
from io import BytesIO
from urllib.parse import urlparse

import unicodedata 
import pdfplumber

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

def read_pdf(file, input_path, output_path):
    pass 

def url_to_id(url):
    return hashlib.sha256(url.encode()).hexdigest()

def read_html(url):
    try:
        # Extract content 
        html_content = fetch_url(url)
        text = extract(html_content, output_format="markdown", with_metadata=True)
        title = extract_metadata(html_content).title

        if not text:
            return None

        # Normalize 
        normalized_text = unicodedata.normalize("NFKC", text)
        # Remove white space
        normalized_text = re.sub(r'[ \t]+', ' ', normalized_text)
        normalized_text = re.sub(r'\n{3,}', '\n\n', normalized_text)

        doc_id = url_to_id(url)

        return {
            "doc_id": doc_id,
            "source_url": url,
            "title": title,
            "text": normalized_text,
            "crawl_timestamp": datetime.datetime.now()
        }
    
    except Exception as e:
        print("An error occurred:", e) 

def chunk_text(text, max_words=300, overlap=50):
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + max_words
        chunk = words[start:end]
        chunks.append(" ".join(chunk))
        start += max_words - overlap

    return chunks

def chunk_document(doc):
    chunks = chunk_text(doc["text"])

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

def process_url(url):
    doc = read_html(url)
    if not doc:
        return

    chunks = chunk_document(doc)
    write_chunks(chunks)
    print("Done")

if __name__=="__main__":
    # Get starting url 
    # Get a list of relevant urls from web crawler
    # Iterate through the list and call read_html
    # Standardize data???
    process_url("https://en.wikipedia.org/wiki/Pittsburgh")
