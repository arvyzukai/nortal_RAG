import pytest
import json
import os
from typing import List
from app.rag import get_qa_chain
from tests.evaluation.eval_models import FactualQuestion

# Load questions
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "factual_questions.json")

def load_questions() -> List[FactualQuestion]:
    if not os.path.exists(DATA_FILE):
        pytest.skip(f"Data file not found: {DATA_FILE}")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [FactualQuestion(**q) for q in data]

QUESTIONS = load_questions()

@pytest.fixture(scope="module")
def qa_chain():
    try:
        return get_qa_chain()
    except Exception as e:
        pytest.fail(f"Failed to initialize RAG chain: {e}")

@pytest.mark.parametrize("question", QUESTIONS, ids=[q.question for q in QUESTIONS])
def test_factual_question(qa_chain, question: FactualQuestion):
    """
    Test a factual question against the RAG system.
    """
    result = qa_chain(question.question)
    answer = result.get("answer", "")
    
    assert answer, "RAG returned empty answer"
    
    if question.match_type == "contains":
        assert question.expected_answer.lower() in answer.lower(), \
            f"Expected '{question.expected_answer}' in answer: {answer}"
    elif question.match_type == "exact":
         assert question.expected_answer.lower() == answer.strip().lower(), \
            f"Expected exact match '{question.expected_answer}', got: {answer}"
    elif question.match_type == "number":
        # Basic number extraction/comparison could go here if needed
        assert question.expected_answer in answer, \
             f"Expected number '{question.expected_answer}' in answer: {answer}"

if __name__ == "__main__":
    pytest.main([__file__])
