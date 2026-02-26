import json
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 64
INPUT_FILE = "documents.jsonl"
EMBEDDINGS_FILE = "embeddings.npy"
METADATA_FILE = "metadata.json"

def load_chunks(input_file: str = INPUT_FILE) -> list[dict]:
    chunks = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    logger.info(f"Loaded {len(chunks)} chunks from {input_file}")
    return chunks


def embed_chunks(chunks: list[dict]) -> np.ndarray:
    logger.info(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

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