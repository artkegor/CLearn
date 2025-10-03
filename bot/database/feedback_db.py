from bot.database.base_db import BaseDB
from logging_config import setup_logging
from pymongo.collection import Collection

# Initialize logger
logger = setup_logging()


# User database operations
class FeedbackDB(BaseDB):
    def __init__(self):
        super().__init__()
        self.feedbacks: Collection = self.db['feedbacks']

    def add_feedback(self, user_id: int, message_id: int, date: str) -> None:
        self.feedbacks.insert_one(
            {
                'user_id': user_id,
                'message_id': message_id,
                'status': 'new',
                'date': date
            }
        )
        logger.info(f"Added feedback from user: {user_id}")

    def mark_feedback_as_answered(self, message_id: int) -> None:
        self.feedbacks.update_one(
            filter={'message_id': message_id},
            update={'$set': {'status': 'answered'}}
        )

    def get_feedback(self, message_id: int) -> dict:
        return self.feedbacks.find_one(
            filter={
                'message_id': message_id
            }
        )
