from pydantic import BaseModel, Field
from typing import Literal

class FactualQuestion(BaseModel):
    question: str
    expected_answer: str
    match_type: Literal["contains", "exact", "number"] = "contains"

class AbstractQuestion(BaseModel):
    question: str
    reference_answer: str | None = None
    
class EvaluationScore(BaseModel):
    score: int = Field(ge=1, le=10, description="Score from 1 to 10")
    reasoning: str = Field(description="Reasoning for the score")
