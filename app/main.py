import os
import shutil
from typing import Union

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI()
UPLOAD_DIRECTORY = "./uploads"


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.post("/upload-image/")
async def upload_image(image: UploadFile = File(...)):
    file_extension = os.path.splitext(image.filename)[1].lower()
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif"]

    if file_extension not in allowed_extensions:
        return JSONResponse(
            status_code=400,
            content={"message": "지원되지 않는 파일 형식입니다. JPG, JPEG, PNG, GIF 파일만 업로드할 수 있습니다."}
        )

    file_path = os.path.join(UPLOAD_DIRECTORY, image.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    return {"filename": image.filename, "file_path": file_path}


@app.post("/upload-multiple-images/")
async def upload_multiple_images(images: list[UploadFile] = File(...)):
    saved_files = []

    for image in images:
        file_extension = os.path.splitext(image.filename)[1].lower()
        allowed_extensions = [".jpg", ".jpeg", ".png", ".gif"]

        if file_extension not in allowed_extensions:
            continue

        file_path = os.path.join(UPLOAD_DIRECTORY, image.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        saved_files.append({"filename": image.filename, "file_path": file_path})

    return {"uploaded_files": saved_files, "total_count": len(saved_files)}
