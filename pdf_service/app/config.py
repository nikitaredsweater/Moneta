import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pdf_service")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "documents")
