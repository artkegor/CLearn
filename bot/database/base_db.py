from config import Config
from pymongo import MongoClient


# Initialize MongoDB client
class BaseDB:
    def __init__(self):
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client['clearn_db']
