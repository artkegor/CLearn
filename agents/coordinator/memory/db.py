from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

MONGO_URI = "mongodb://localhost:27017"
MONGO_DB_NAME = "coordinator_memory"
MONGO_COLLECTION_NAME = "sessions"

try:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    memory_collection = db[MONGO_COLLECTION_NAME]
    logger.info("MongoDB подключена")
except Exception as e:
    logger.error(f"Ошибка подключения MongoDB: {e}")
    memory_collection = None
