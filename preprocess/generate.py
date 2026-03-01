import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

MODEL_ID       = "mistralai/Mistral-7B-Instruct-v0.2"
MAX_NEW_TOKENS = 256
TEMPERATURE    = 0.1

_tokenizer = None
_model     = None


def load_model():
    global _tokenizer, _model

    if _model is not None:
        return _tokenizer, _model

    logger.info(f"Loading {MODEL_ID}...")

    # Clear any leftover GPU memory before loading
    torch.cuda.empty_cache()

    _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    # 4-bit quantization — cuts VRAM from ~14GB to ~4GB
    quantization_config = BitsAndBytesConfig(load_in_4bit=True)

    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=quantization_config,
        device_map="auto"
    )
    _model.eval()
    logger.info("Model loaded.")
    return _tokenizer, _model


def build_prompt(query, chunks):
    context_parts = []
    for i, chunk in enumerate(chunks[:2]):  # top 2 chunks to stay within context limit
        source = chunk.get("title") or chunk.get("source_url", "")
        text = " ".join(chunk["text"].split()[:150])  # trim each chunk to 150 words
        context_parts.append(f"[Source {i+1}: {source}]\n{text}")
    context = "\n\n".join(context_parts)

    prompt = f"""<s>[INST] You are a helpful assistant answering questions about Pittsburgh and CMU.
Use only the context provided below to answer the question.
If the answer is not in the context, say "I don't know".
Keep your answer concise — one or two sentences where possible.

Context:
{context}

Question: {query} [/INST]"""
    return prompt


def call_llm(prompt):
    tokenizer, model = load_model()

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def generate(query, chunks):
    if not chunks:
        return "I don't know — no relevant documents found."

    prompt = build_prompt(query, chunks)
    logger.info(f"Generating answer for: {query}")

    try:
        answer = call_llm(prompt)
        logger.info(f"Answer: {answer[:100]}...")
        return answer
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return f"Error: {e}"


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