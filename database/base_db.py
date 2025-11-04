from config import Config
from pymongo import MongoClient
from pymongo.database import Database

# BaseDB sets up the MongoDB connection and provides access to the database.
class BaseDB:
    def __init__(self):
        self.client = MongoClient(Config.MONGO_URI)
        self.db: Database = self.client['clearn_db']