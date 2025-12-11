from datetime import datetime
from typing import Any, Dict, List
import logging
from .db import memory_collection

logger = logging.getLogger(__name__)


class CoordinatorMemoryManager:
    """Coordinates memory management for agent interactions"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memory_collection = memory_collection

    def save_interaction(self,
                         agent_name: str,
                         user_input: str,
                         agent_output: str,
                         metadata: Dict[str, Any] = None):
        """Saves an interaction to memory"""

        if not self.memory_collection:
            logger.warning("⚠️ MongoDB недоступна, памяти не сохранены")
            return

        try:
            interaction = {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "agent_name": agent_name,
                "user_input": user_input,
                "agent_output": agent_output[:500],  # Save only first 500 chars
                "metadata": metadata or {}
            }

            self.memory_collection.insert_one(interaction)
            logger.info(f"💾 Взаимодействие с {agent_name} сохранено в памяти")

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в памяти: {str(e)}")

    def get_recent_context(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves recent interactions from memory"""

        if not self.memory_collection:
            return []

        try:
            recent = list(
                self.memory_collection
                .find({"session_id": self.session_id})
                .sort("timestamp", -1)
                .limit(limit)
            )

            # Delete internal MongoDB ID before returning
            for item in recent:
                item.pop("_id", None)

            return list(reversed(recent))  # Return in chronological order

        except Exception as e:
            logger.error(f"❌ Ошибка получения контекста из памяти: {str(e)}")
            return []

    def get_agent_statistics(self) -> Dict[str, int]:
        """Retrieves statistics of agent interactions"""

        if not self.memory_collection:
            return {}

        try:
            pipeline = [
                {"$match": {"session_id": self.session_id}},
                {"$group": {"_id": "$agent_name", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]

            stats = {item["_id"]: item["count"]
                     for item in self.memory_collection.aggregate(pipeline)}

            return stats

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {str(e)}")
            return {}

