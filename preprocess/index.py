import os
os.makedirs("data", exist_ok=True)
import logging, faiss, bm25s
import numpy as np
from embed import load_chunks

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def build_faiss_index():
    vecs = np.load("data/embeddings.npy").astype("float32")
    idx = faiss.IndexFlatL2(vecs.shape[1])
    idx.add(vecs)
    faiss.write_index(idx, "data/faiss.index")
    logger.info(f"FAISS index saved")

def build_bm25_index(chunks):
    corpus = [c["text"] for c in chunks]
    tokens = bm25s.tokenize(corpus)
    bm25 = bm25s.BM25()
    bm25.index(tokens)
    bm25.save("data/bm25_index")
    logger.info(f"BM25 index saved")

if __name__ == "__main__":
    build_faiss_index()
    chunks = load_chunks()
    build_bm25_index(chunks)
    logger.info("Done.")