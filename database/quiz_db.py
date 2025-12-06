from typing import Optional
from pymongo.collection import Collection
from database.base_db import BaseDB
from logging_config import setup_logging
from models.database_models import QuizModel

logger = setup_logging()


# TaskDB handles tasks in the database.
class QuizDB(BaseDB):
    def __init__(self):
        super().__init__()
        self.tasks: Collection = self.db['quizzes']

    def add_quiz(self, quiz: QuizModel) -> None:
        self.tasks.insert_one(quiz.model_dump(by_alias=True))
        logger.info(f"Added quiz id: {quiz.quiz_id}")

    def get_quiz(self, quiz_id: str) -> Optional[QuizModel]:
        doc = self.tasks.find_one({"quiz_id": quiz_id})
        return QuizModel(**doc) if doc else None