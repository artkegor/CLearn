from pydantic import BaseModel, Field
from typing import List


class FullQuestion(BaseModel):
    question: str = Field(..., min_length=10, max_length=500)
    options: List[str] = Field(..., min_length=4, max_length=4)
    correct: int = Field(ge=0, le=3)
    explanation: str = Field(..., min_length=10, max_length=1000)


class FullQuiz(BaseModel):
    topic: str
    type: str = "full"
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    questions: List[FullQuestion] = Field(..., min_length=5, max_length=10)