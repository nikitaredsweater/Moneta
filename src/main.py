from fastapi import FastAPI

app = FastAPI()


@app.get('/')
async def root():
    # Test
    return {"message": 'Hello World'}