import logging, pickle, faiss, bm25s
import numpy as np
from embed import load_chunks

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

EMBEDDINGS_FILE  = "data/embeddings.npy"
METADATA_FILE    = "data/metadata.json"
DOCUMENTS_FILE   = "data/documents.jsonl"
FAISS_INDEX_FILE = "data/faiss.index"
BM25_INDEX_FILE  = "data/bm25.index"


def build_faiss_index() -> faiss.Index:
    embeddings = np.load(EMBEDDINGS_FILE).astype("float32")
    dim = embeddings.shape[1]  
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index


def save_faiss_index(index: faiss.Index):
    faiss.write_index(index, FAISS_INDEX_FILE)
    logger.info(f"Saved FAISS index to {FAISS_INDEX_FILE}")


def build_bm25_index(chunks) -> bm25s.BM25:
    texts = [chunk["text"] for chunk in chunks]
    corpus_tokens = bm25s.tokenize(texts)
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)
    return retriever


def save_bm25_index(retriever: bm25s.BM25):
    with open(BM25_INDEX_FILE, "wb") as f:
        pickle.dump(retriever, f)
    logger.info(f"Saved BM25 index to {BM25_INDEX_FILE}")


if __name__ == "__main__":
    # Build and save FAISS index
    faiss_index = build_faiss_index()
    save_faiss_index(faiss_index)

    # Build and save BM25 index
    chunks = load_chunks()
    bm25_index = build_bm25_index(chunks)
    save_bm25_index(bm25_index)

    logger.info("Indexing complete.")
    logger.info(f"Files created: {FAISS_INDEX_FILE}, {BM25_INDEX_FILE}")