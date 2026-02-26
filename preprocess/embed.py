import json
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

BATCH_SIZE = 64

def load_chunks() -> list[dict]:
    chunks = []
    with open("documents.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    logger.info(f"Loaded {len(chunks)} chunks from documents.jsonl")
    return chunks


def embed_chunks(chunks: list[dict]) -> np.ndarray:
    model = SentenceTransformer("all-MiniLM-L6-v2")

    texts = [chunk["text"] for chunk in chunks]

    logger.info(f"Embedding {len(texts)} chunks in batches of {BATCH_SIZE}...")
    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    logger.info(f"Done. Embedding matrix shape: {embeddings.shape}")
    return embeddings


def save_embeddings(chunks: list[dict], embeddings: np.ndarray) -> None:
    # Save the vectors
    np.save("embeddings.npy", embeddings)

    # Save the metadata — everything except the text itself
    metadata = []
    for i, chunk in enumerate(chunks):
        metadata.append({
            "index":      i,
            "id":         chunk["id"],
            "doc_id":     chunk["doc_id"],
            "source_url": chunk["source_url"],
            "title":      chunk.get("title", ""),
            "doc_type":   chunk.get("doc_type", "html"),
            "chunk_index": chunk["chunk_index"],
            "total_chunks": chunk["total_chunks"],
            "text":       chunk["text"],
        })

    with open("metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    chunks = load_chunks()
    embeddings = embed_chunks(chunks)
    save_embeddings(chunks, embeddings)
    logger.info("Embedding complete.")