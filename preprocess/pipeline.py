import json, logging, sys

from retrieve import load_indexes, retrieve
from generate import generate

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

def load_questions() -> dict[str, str]:
    questions = {}
    with open("data/test_set_day_3.txt", "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            questions[str(i)] = line
    logger.info(f"Loaded questions ")
    return questions

def save_answers(answers: dict[str, str]) -> None:
    import os
    os.makedirs(os.path.dirname("data/output.json"), exist_ok=True)
    with open("data/output.json", "w", encoding="utf-8") as f:
        json.dump(answers, f, ensure_ascii=False, indent=2)


def run_pipeline():
    # Load indices, metadata and model
    faiss_index, bm25_index, metadata, model = load_indexes()

    # Load questions
    questions = load_questions()

    # Process each question
    answers = {}
    failed = []

    for qid, question in questions.items():
        try:
            # Retrieve relevant chunks
            chunks = retrieve(question, faiss_index, bm25_index, metadata, model)

            # Generate answer
            answer = generate(question, chunks)

            answers[qid] = answer
            logger.info(f"  → {answer}")

        except Exception as e:
            logger.error(f"  Failed: {e}")
            answers[qid] = "I don't know."
            failed.append(qid)

        # Save after every question in case of crashes
        save_answers(answers)
        print("Done")

    logger.info(f"Output saved to {"data/output.json"}")


if __name__ == "__main__":
    run_pipeline()