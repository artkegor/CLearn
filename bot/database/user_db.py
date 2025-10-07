from bot.database.base_db import BaseDB
from logging_config import setup_logging
from pymongo.collection import Collection

# Initialize logger
logger = setup_logging()


# User database operations
class UserDB(BaseDB):
    def __init__(self):
        super().__init__()
        self.users: Collection = self.db['users']

    def add_user(self, user_id: int, username: str, register_date: str) -> None:
        if not self.users.find_one({'user_id': user_id}):
            self.users.insert_one(
                {
                    'user_id': user_id,
                    'username': username,
                    'register_date': register_date
                }
            )
            logger.info(f"Added new user: {user_id} with username: {username}")

    def get_user(self, user_id: int) -> dict:
        return self.users.find_one(
            {
                'user_id': user_id
            }
        )

    def delete_user(self, user_id: int) -> None:
        self.users.delete_one(
            {
                'user_id': user_id
            }
        )
