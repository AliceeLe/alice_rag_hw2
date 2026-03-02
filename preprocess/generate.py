import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

MODEL_ID       = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
MAX_NEW_TOKENS = 256
TEMPERATURE    = 0.1

_tokenizer = None
_model     = None


def load_model():
    global _tokenizer, _model
    if _model is not None:
        return _tokenizer, _model
    torch.cuda.empty_cache()  
    logger.info(f"Loading {MODEL_ID}...")
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16    ).to("cuda")
    _model.eval()
    logger.info("Model loaded.")
    return _tokenizer, _model


def build_prompt(query, chunks):
    context_parts = []
    for i, chunk in enumerate(chunks[:2]):
        text = " ".join(chunk["text"].split()[:150])
        context_parts.append(text)
    context = " ".join(context_parts)

    # TinyLlama uses ChatML format
    return f"""<|system|>
You are a helpful assistant answering questions about Pittsburgh and CMU. Use only the context provided. If the answer is not in the context, say "I don't know". Be concise.</s>
<|user|>
Context: {context}

Question: {query}</s>
<|assistant|>"""


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
        return "I don't know."
    try:
        answer = call_llm(build_prompt(query, chunks))
        logger.info(f"Answer: {answer[:100]}")
        return answer
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return "I don't know."