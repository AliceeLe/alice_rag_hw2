import json, logging, faiss, bm25s
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

TOP_K       = 10
FINAL_TOP_K = 5
RRF_K       = 60


def load_indexes():
    # Read faiss and bm25
    idx = faiss.read_index("data/faiss.index")
    bm25 = bm25s.BM25.load("data/bm25_index")
    # Load metadata 
    with open("data/metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return idx, bm25, meta, model


def dense_search(query, faiss_idx, model, top_k=TOP_K):
    vec = model.encode([query], convert_to_numpy=True).astype("float32")
    _, idxs = faiss_idx.search(vec, top_k)
    return idxs[0].tolist()


def sparse_search(query, bm25, top_k=TOP_K):
    tokens = bm25s.tokenize([query])
    results, _ = bm25.retrieve(tokens, k=top_k)
    return results[0].tolist()


def rrf(dense_idxs, sparse_idxs, k=RRF_K):
    scores = {}
    for rank, idx in enumerate(dense_idxs):
        scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank + 1)
    for rank, idx in enumerate(sparse_idxs):
        scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank + 1)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [idx for idx, _ in ranked]


def retrieve(query, faiss_idx, bm25, meta, model, top_k=FINAL_TOP_K, mode="hybrid"):
    if mode == "dense":
        combined = dense_search(query, faiss_idx, model)
    elif mode == "sparse":
        combined = sparse_search(query, bm25)
    else:  # hybrid
        dense_results  = dense_search(query, faiss_idx, model)
        sparse_results = sparse_search(query, bm25)
        combined       = rrf(dense_results, sparse_results)

    chunks = []
    for idx in combined[:top_k]:
        if idx < len(meta):
            chunks.append(meta[idx])

    return chunks

