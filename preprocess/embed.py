import json
import numpy as np
from sentence_transformers import SentenceTransformer

def load_chunks() -> list[dict]:
    chunks = []
    with open("data/documents.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def embed_chunks(chunks: list[dict]) -> np.ndarray:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = []
    for chunk in chunks:
        texts.append(chunk["text"])
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True, convert_to_numpy=True)
    return embeddings


def save_embeddings(chunks: list[dict], embeddings: np.ndarray) -> None:
    # Save the vectors
    np.save("data/embeddings.npy", embeddings)

    # Save the metadata 
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

    with open("data/metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    chunks = load_chunks()
    embeddings = embed_chunks(chunks)
    save_embeddings(chunks, embeddings)