import random
from typing import Optional
from pymongo.collection import Collection
from database.base_db import BaseDB
from logging_config import setup_logging
from models.database_models import UserModel

logger = setup_logging()


# UserDB handles operations related to users in the database.
class UserDB(BaseDB):
    def __init__(self):
        super().__init__()
        self.users: Collection = self.db['users']

    def add_user(self, user: UserModel) -> None:
        if not self.users.find_one({"user_id": user.user_id}):
            self.users.insert_one(user.model_dump(by_alias=True))
            logger.info(f"Added new user: {user.user_id} ({user.username})")

    def get_user(self, user_id: int) -> Optional[UserModel]:
        doc = self.users.find_one({"user_id": user_id})
        return UserModel(**doc) if doc else None

    def delete_user(self, user_id: int) -> None:
        result = self.users.delete_one({"user_id": user_id})
        if result.deleted_count:
            logger.info(f"Deleted user: {user_id}")

    def add_solution(self, user_id: int, task_id: str, solution_code: str, score: int, log: str) -> str:
        solution_id = str(random.randint(100000, 999999))
        self.users.update_one(
            {"user_id": user_id},
            {"$push":
                {"solutions": {
                    "solution_id": solution_id,
                    "task_id": task_id,
                    "solution_code": solution_code,
                    "score": score,
                    "log": log
                }
                }
            }
        )
        logger.info(f"Added solution for user: {user_id}, task: {task_id}")
        return solution_id
