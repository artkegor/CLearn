from typing import Optional
from pymongo.collection import Collection
from database.base_db import BaseDB
from logging_config import setup_logging
from models.database_models import FeedbackModel

logger = setup_logging()


# FeedbackDB handles operations related to user feedback in the database.
class FeedbackDB(BaseDB):
    def __init__(self):
        super().__init__()
        self.feedbacks: Collection = self.db['feedbacks']

    def add_feedback(self, feedback: FeedbackModel) -> None:
        self.feedbacks.insert_one(feedback.model_dump(by_alias=True))
        logger.info(f"Added feedback from user: {feedback.user_id}")

    def mark_feedback_as_answered(self, message_id: int) -> None:
        result = self.feedbacks.update_one(
            {"message_id": message_id},
            {"$set": {"status": "answered"}}
        )
        if result.modified_count:
            logger.info(f"Marked feedback {message_id} as answered")

    def get_feedback(self, message_id: int) -> Optional[FeedbackModel]:
        doc = self.feedbacks.find_one({"message_id": message_id})
        return FeedbackModel(**doc) if doc else None
