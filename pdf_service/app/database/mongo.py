from pymongo import MongoClient
from app.config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
collection = db[MONGO_COLLECTION]

def insert_document(doc: dict) -> str:
    result = collection.insert_one(doc)
    return str(result.inserted_id)

def update_document(query: dict, update_data: dict):
    collection.update_one(query, {"$set": update_data})

def get_document(query: dict) -> dict:
    return collection.find_one(query)
