import json, logging, os

from retrieve import load_indexes, retrieve
from generate import generate, load_model

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def load_questions(path: str = "data/test_set_day_3.txt") -> dict[str, str]:
    questions = {}
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if line:
                questions[str(i)] = line
    return questions


def save_answers(answers: dict[str, str], path: str = "data/output.json") -> None:
    os.makedirs("data", exist_ok=True)
    output = {"andrewid": "anhle"}  
    output.update(answers)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

def run_pipeline(questions_path, output_path, mode="hybrid"):
    faiss_index, bm25_index, metadata, embed_model = load_indexes()
    
    # Load generation model ONCE here
    import torch
    torch.cuda.empty_cache()
    tokenizer, gen_model = load_model()
    
    questions = load_questions(questions_path)
    answers = {}

    for qid, question in questions.items():
        chunks = retrieve(question, faiss_index, bm25_index, metadata, embed_model, mode=mode)
        answer = generate(question, chunks, preloaded_model=gen_model, preloaded_tokenizer=tokenizer)
        answers[qid] = answer
        save_answers(answers, output_path)


if __name__ == "__main__":
    import sys
    questions_path = sys.argv[1] if len(sys.argv) > 1 else "data/leaderboard_queries.txt"
    output_path    = sys.argv[2] if len(sys.argv) > 2 else "data/output.json"
    mode           = sys.argv[3] if len(sys.argv) > 3 else "hybrid"
    run_pipeline(questions_path, output_path, mode)
