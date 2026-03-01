import logging
from transformers import T5ForConditionalGeneration, T5Tokenizer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

MODEL_ID       = "google/flan-t5-base"
MAX_NEW_TOKENS = 128

_tokenizer = None
_model     = None


def load_model():
    global _tokenizer, _model
    if _model is not None:
        return _tokenizer, _model
    logger.info(f"Loading {MODEL_ID}...")
    _tokenizer = T5Tokenizer.from_pretrained(MODEL_ID)
    _model = T5ForConditionalGeneration.from_pretrained(MODEL_ID)
    _model.eval()
    logger.info("Model loaded.")
    return _tokenizer, _model


def build_prompt(query, chunks):
    context_parts = []
    for i, chunk in enumerate(chunks[:2]):
        text = " ".join(chunk["text"].split()[:100])  # trim to 100 words per chunk
        context_parts.append(text)
    context = " ".join(context_parts)

    return f"Answer the question based on the context. Context: {context} Question: {query} Answer:"


def call_llm(prompt):
    tokenizer, model = load_model()
    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS)
    return tokenizer.decode(outputs[0], skip_special_tokens=True).strip()


def generate(query, chunks):
    if not chunks:
        return "I don't know."
    try:
        prompt = build_prompt(query, chunks)
        answer = call_llm(prompt)
        logger.info(f"Answer: {answer[:100]}")
        return answer
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return "I don't know."


if __name__ == "__main__":
    from retrieve import load_indexes, retrieve

    faiss_idx, bm25, meta, model = load_indexes()

    queries = [
        "When was Pittsburgh founded?",
        "What is Picklesburgh?",
        "Who plays for the Pittsburgh Steelers?",
    ]

    for q in queries:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        chunks = retrieve(q, faiss_idx, bm25, meta, model)
        answer = generate(q, chunks)
        print(f"A: {answer}")