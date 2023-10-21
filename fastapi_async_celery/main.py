from fastapi import FastAPI

from .s3_char_count.router import router as s3_char_count_router

app = FastAPI()

app.include_router(s3_char_count_router, prefix="/v1")


@app.get("/")
async def read_root():
    return {"msg": "Hello World"}
