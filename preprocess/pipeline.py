import json, logging, os

from retrieve import load_indexes, retrieve
from generate import generate

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def load_questions(path: str = "data/test_set_day_3.txt") -> dict[str, str]:
    questions = {}
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if line:
                questions[str(i)] = line
    logger.info(f"Loaded {len(questions)} questions from {path}")
    return questions


def save_answers(answers: dict[str, str], path: str = "data/output.json") -> None:
    os.makedirs("data", exist_ok=True)
    output = {"andrewid": "anhle"}  
    output.update(answers)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

def run_pipeline(questions_path: str = "data/test_set_day_3.txt", output_path: str = "data/output.json"):
    # Load indexes and models
    faiss_index, bm25_index, metadata, model = load_indexes()

    # Load questions
    questions = load_questions(questions_path)
    total = len(questions)

    answers = {}
    failed = []

    for qid, question in questions.items():
        logger.info(f"[{qid}/{total}] {question}")
        try:
            chunks = retrieve(question, faiss_index, bm25_index, metadata, model, mode="dense")
            answer = generate(question, chunks)
            answers[qid] = answer
            logger.info(f"  → {answer}")
        except Exception as e:
            logger.error(f"  Failed: {e}")
            answers[qid] = "I don't know."
            failed.append(qid)

        # Save after every question in case of crashes
        save_answers(answers, output_path)

    logger.info(f"\nDone. {total - len(failed)}/{total} answered.")
    if failed:
        logger.warning(f"Failed: {failed}")
    logger.info(f"Output saved to {output_path}")


if __name__ == "__main__":
    import sys
    questions_path = sys.argv[1] if len(sys.argv) > 1 else "data/test_set_day_3.txt"
    output_path    = sys.argv[2] if len(sys.argv) > 2 else "data/output.json"
    run_pipeline(questions_path, output_path)