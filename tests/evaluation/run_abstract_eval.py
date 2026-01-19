import json
import os
import argparse
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.rag import get_qa_chain
from tests.evaluation.eval_models import AbstractQuestion, EvaluationScore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "abstract_questions.json")

def load_questions() -> List[AbstractQuestion]:
    if not os.path.exists(DATA_FILE):
        print(f"Data file not found: {DATA_FILE}")
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [AbstractQuestion(**q) for q in data]

def get_judge_llm():
    # Use GPT-4o or similar high-quality model for judging if available, 
    # falling back to whatever is in env or default.
    return ChatOpenAI(model="gpt-4o", temperature=0)

JUDGE_PROMPT = ChatPromptTemplate.from_template(
    """You are an impartial judge evaluating the quality of an answer given by an AI assistant locally for the company Nortal.
    
    Question: {question}
    Reference Answer: {reference_answer}
    
    Assistant Answer: {assistant_answer}
    
    Score the Assistant Answer on a scale of 1 to 10 based on accuracy, completeness, and relevance compared to the Reference Answer.
    1 is completely wrong or irrelevant.
    10 is perfect.
    
    Provide a score and a short reasoning.
    """
)

def evaluate_abstract_questions():
    questions = load_questions()
    if not questions:
        return

    print(f"Loading RAG chain...")
    try:
        qa_chain = get_qa_chain()
    except Exception as e:
        print(f"Failed to initialize RAG chain: {e}")
        return

    judge = get_judge_llm()
    structured_judge = judge.with_structured_output(EvaluationScore)

    results = []
    print(f"\nStarting evaluation of {len(questions)} abstract questions...\n")

    for q in questions:
        print(f"Q: {q.question}")
        
        # Get RAG answer
        try:
            rag_output = qa_chain(q.question)
            assistant_answer = rag_output.get("answer", "No answer returned.")
        except Exception as e:
            assistant_answer = f"Error during RAG generation: {e}"
        
        print(f"A: {assistant_answer[:100]}...")

        # Judge
        prompt_input = {
            "question": q.question,
            "reference_answer": q.reference_answer or "N/A (Judge based on general knowledge if possible)",
            "assistant_answer": assistant_answer
        }
        
        chain = JUDGE_PROMPT | structured_judge
        try:
            score_result = chain.invoke(prompt_input)
            print(f"-> Score: {score_result.score}/10. Reasoning: {score_result.reasoning}\n")
            results.append({
                "question": q.question,
                "assistant_answer": assistant_answer,
                "score": score_result.score,
                "reasoning": score_result.reasoning
            })
        except Exception as e:
            print(f"-> Evaluation failed: {e}\n")

    # Save logic could go here, for now just printing is fine for the MVP
    print("Evaluation Complete.")

if __name__ == "__main__":
    evaluate_abstract_questions()
