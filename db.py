import os
from pymongo import MongoClient

client = MongoClient(os.environ.get("MONGO_URI"))
db = client['consultancy_db']