
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from langsmith import evaluate
from langsmith.schemas import Run, Example
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tracers.context import tracing_v2_enabled
from pydantic import BaseModel, Field

from app.rag import get_qa_chain

load_dotenv()

# --- EVALUATORS ---

def factual_evaluator(run: Run, example: Example) -> Dict[str, Any]:
    """
    Heuristic evaluator for factual questions.
    Checks if 'expected_answer' is contained in or matches the prediction.
    """
    prediction = run.outputs.get("answer", "")
    expected = example.outputs.get("expected_answer", "")
    match_type = example.outputs.get("match_type", "contains")
    
    # Normalization
    pred_norm = prediction.strip().lower()
    exp_norm = expected.strip().lower()
    
    score = 0
    comment = ""

    if not prediction:
        return {"key": "correctness", "score": 0, "comment": "Empty prediction"}
    
    if match_type == "exact":
        score = 1 if exp_norm == pred_norm else 0
        if not score:
            comment = f"Expected exact '{expected}', got '{prediction}'"
    else: # contains or default
        score = 1 if exp_norm in pred_norm else 0
        if not score:
            comment = f"Expected '{expected}' in '{prediction}'"
            
    return {"key": "correctness", "score": score, "comment": comment}


# Abstract Evaluator Models
class Grade(BaseModel):
    score: int = Field(description="Score from 1 to 5, where 5 is perfect.")
    explanation: str = Field(description="Short explanation of the score.")

def abstract_evaluator(run: Run, example: Example) -> Dict[str, Any]:
    """
    LLM-as-a-judge evaluator for abstract questions.
    Compares prediction against reference_answer.
    """
    prediction = run.outputs.get("answer", "")
    reference = example.outputs.get("reference_answer", "")
    question = example.inputs.get("question", "")
    
    judge_llm = ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm = judge_llm.with_structured_output(Grade)
    
    system_prompt = """You are an expert evaluator for a RAG system.
    Compare the Assistant's Answer to the Reference Answer for the given Question.
    Grade on a scale of 1-5 based on correctness and completeness.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Question: {question}\nReference: {reference}\nAssistant Answer: {prediction}")
    ])
    
    chain = prompt | structured_llm
    
    try:
        grade = chain.invoke({
            "question": question,
            "reference": reference,
            "prediction": prediction
        })
        return {
            "key": "quality",
            "score": grade.score / 5.0, # Normalize to 0-1
            "comment": grade.explanation
        }
    except Exception as e:
        return {"key": "quality", "score": 0, "comment": f"Judge error: {e}"}

# --- EVALUATION RUNNER ---

def run_evaluation(dataset_name: str, experiment_prefix: str):
    """
    Runs evaluation on a specific dataset. 
    Selects the appropriate evaluator based on the dataset name.
    """
    print(f"\n>>> Starting Evaluation for: {dataset_name}")
    
    # 1. Prepare Target
    try:
        qa_chain = get_qa_chain()
    except Exception as e:
        print(f"Error initializing chain: {e}")
        return

    def target(inputs: Dict) -> Dict:
        res = qa_chain(inputs["question"])
            
        # Format for LangSmith
        return {
            "answer": res.get("answer"),
            "source_documents": [d.page_content for d in res.get("source_documents", [])]
        }

    # 2. Select Evaluators
    evaluators = []
    if "Factual" in dataset_name:
        evaluators = [factual_evaluator]
    elif "Abstract" in dataset_name:
        evaluators = [abstract_evaluator]
    else:
        print(f"Warning: No specific evaluator known for '{dataset_name}'. Using factual default.")
        evaluators = [factual_evaluator]

    # 3. Run
    results = evaluate(
        target,
        data=dataset_name,
        evaluators=evaluators,
        experiment_prefix=experiment_prefix,
        description=f"Automated evaluation for {dataset_name}",
        metadata={
            "dataset": dataset_name
        },
        max_concurrency=4 # Speed things up
    )
    return results
