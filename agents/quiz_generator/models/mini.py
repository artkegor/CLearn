from pydantic import BaseModel, Field
from typing import List


class MiniQuestion(BaseModel):
    question: str
    options: List[str] = Field(..., min_length=2, max_length=4)
    correct: int
    explanation: str


class MiniQuiz(BaseModel):
    topic: str
    type: str = "mini"
    context_snippet: str = ""
    questions: List[MiniQuestion] = Field(..., min_length=1, max_length=7)