from pymongo import MongoClient

client = MongoClient("mongodb+srv://pavanm8919_db_user:pavan123@cluster0.ut6smkz.mongodb.net/?retryWrites=true&w=majority")

db = client["consultancy_db"]