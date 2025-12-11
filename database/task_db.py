from typing import Optional
from pymongo.collection import Collection
from database.base_db import BaseDB
from logging_config import setup_logging
from models.database_models import TaskModel

logger = setup_logging()


# TaskDB handles tasks in the database.
class TaskDB(BaseDB):
    def __init__(self):
        super().__init__()
        self.tasks: Collection = self.db['tasks']

    def add_task(self, task: TaskModel) -> None:
        self.tasks.insert_one(task.model_dump(by_alias=True))
        logger.info(f"Added task number: {task.task_id}")

    def get_task(self, task_id: int) -> Optional[TaskModel]:
        doc = self.tasks.find_one({"task_id": task_id})
        return TaskModel(**doc) if doc else None

    def update_task_solution(self, task_id: int, solution_code: str) -> None:
        self.tasks.update_one(
            {"task_id": task_id},
            {"$set": {"solution_code": solution_code}}
        )
        logger.info(f"Updated solution for task number: {task_id}")
