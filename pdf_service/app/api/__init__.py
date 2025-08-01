"""
Routers module
"""

from app.api.v1 import v1_router
from app.workers.tasks import parse_pdf_task
from fastapi import APIRouter

# TODO: Add v2 router
# TODO: Add health router

app_router = APIRouter()

app_router.include_router(v1_router, prefix='/v1')


@app_router.post("/parse")
def trigger_parsing(file_key: str):
    parse_pdf_task.delay(file_key)
    return {"status": "queued"}
