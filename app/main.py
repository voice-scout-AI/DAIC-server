import os
import shutil
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI, File, UploadFile

from app.runnables.code_generator import CodeGenerator
from app.services.process_images import ImageProcessorChain


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    yield
    app.state.redis_client.close()


UPLOAD_DIRECTORY = "./uploads"
app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    value = app.state.redis_client.get("test")

    return {"Hello": value}


@app.post("/upload-images/")
async def upload_images(images: list[UploadFile] = File(...)):
    saved_files = []

    for image in images:
        file_path = os.path.join(UPLOAD_DIRECTORY, image.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        saved_files.append(file_path)

    result = ImageProcessorChain().invoke(saved_files)

    return result


@app.post("/transform/")
async def transform(body: dict):
    result = CodeGenerator().invoke({
        "id": body.get("id"),
        "fromname": body.get("from", {}).get("name"),
        "fromversion": body.get("from", {}).get("version"),
        "toname": body.get("to", {}).get("name"),
        "toversion": body.get("to", {}).get("version")
    })

    return result
