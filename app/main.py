import os
import shutil
from contextlib import asynccontextmanager

import gradio as gr
from fastapi import FastAPI, File, UploadFile

from app.core.state import app_state
from app.ui.gradio_interface import create_gradio_app
from app.services.process_images import ImageProcessorChain
from app.services.transform_code import CodeTransformerChain


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Redis 초기화 (환경 변수 또는 기본값 사용)
    app_state.initialize_redis()
    app_state.initialize_vector_store()

    yield
    app_state.close_redis()


UPLOAD_DIRECTORY = "./uploads"
app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    value = app_state.redis_client.get("test")

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
    result = CodeTransformerChain().invoke({
        "id": body.get("id"),
        "fromname": body.get("from", {}).get("name"),
        "fromversion": body.get("from", {}).get("version"),
        "toname": body.get("to", {}).get("name"),
        "toversion": body.get("to", {}).get("version")
    })

    return result


# Gradio 앱을 FastAPI에 마운트
gradio_app = create_gradio_app(UPLOAD_DIRECTORY)
app = gr.mount_gradio_app(app, gradio_app, path="/gradio")
