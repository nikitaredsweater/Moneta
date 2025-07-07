"""Main FastAPI application module."""

from fastapi import FastAPI

app = FastAPI()


@app.get('/')
async def root() -> dict[str, str]:
    """
    Test endpoint.

    Returns:
        dict[str, str]: A dictionary with a message key and value.
    """
    return {'message': 'Hello World'}
