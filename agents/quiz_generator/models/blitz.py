from pydantic import BaseModel, Field
from typing import List


class BlitzQuestion(BaseModel):
    question: str = Field(..., min_length=1, max_length=200)
    options: List[str] = Field(..., min_length=3, max_length=3)
    correct: int = Field(ge=0, le=2)


class BlitzQuiz(BaseModel):
    topic: str
    type: str = "blitz"
    time_per_question: int = 30
    questions: List[BlitzQuestion] = Field(..., min_length=3, max_length=5)