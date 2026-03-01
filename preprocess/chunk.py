import os
os.makedirs("data", exist_ok=True)
import re, hashlib, logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

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