from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Literal, Optional, List, Dict, Any


# Model representing user feedback
class FeedbackModel(BaseModel):
    user_id: int
    message_id: int
    status: Literal["new", "answered"] = "new"
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("date", mode="before")
    def parse_custom_date(cls, value):
        if isinstance(value, str):
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%d.%m.%Y %H:%M:%S"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            raise ValueError(
                "Invalid date format. Expected ISO (YYYY-MM-DDTHH:MM:SS) "
                "or European (DD.MM.YYYY HH:MM:SS)"
            )
        return value


# Model representing a user
class UserModel(BaseModel):
    user_id: int
    username: str
    register_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    solutions: List[Dict[str, Any]] = []

    @field_validator("register_date", mode="before")
    def parse_custom_date(cls, value):
        if isinstance(value, str):
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%d.%m.%Y %H:%M:%S"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            raise ValueError(
                "Invalid date format. Expected ISO (YYYY-MM-DDTHH:MM:SS) "
                "or European (DD.MM.YYYY HH:MM:SS)"
            )
        return value


# Model representing a task
class TaskModel(BaseModel):
    task_id: str
    topic_id: str
    difficulty: int
    task_text: str
    test_cases: List[Dict[str, Any]]
    solution_code: str


# Base model for MongoDB documents
class MongoModel(BaseModel):
    id: Optional[str] = Field(alias="_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda v: v.isoformat()}
