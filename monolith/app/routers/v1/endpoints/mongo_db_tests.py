"""
A test set of repositories, to see if mongoDB works
"""

from typing import Any, List

from app.utils.database import get_mongo_db
from bson import ObjectId
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

test_router = APIRouter()


def serialize_mongo_doc(doc: dict[str, Any]) -> dict[str, Any]:
    """
    Convert MongoDB document to something JSON-serializable.
    """
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc


@test_router.post("/")
async def create_mongo_item(
    payload: dict,
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Create a document in MongoDB.
    """
    result = await mongo_db["items"].insert_one(payload)
    return {"inserted_id": str(result.inserted_id)}


@test_router.get(
    "/items", summary="Get all items from Mongo 'items' collection"
)
async def list_items(
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> List[dict]:
    cursor = mongo_db["items"].find({})
    items: list[dict[str, Any]] = []
    async for doc in cursor:
        items.append(serialize_mongo_doc(doc))
    return items
