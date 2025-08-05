'''
Main FastAPI application module.
'''

from app.api import app_router
from app.utils import minio_client
from fastapi import FastAPI

app = FastAPI()

REQUIRED_BUCKETS = ['documents']


@app.on_event('startup')
def ensure_bucket():
    for bucket in REQUIRED_BUCKETS:
        if not minio_client.bucket_exists(bucket):
            minio_client.make_bucket(bucket)


app.include_router(app_router)


@app.get('/')
def read_root():
    return {'message': 'Hello, world!'}
