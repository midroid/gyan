from typing import Union
import json
import logging
from uuid import uuid4
import pandas as pd

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from rag.colpali import search_by_text_and_return_images
from rag.data_set import get_result_ds
from rag.file_converter import convert_pdf_to_images
from rag.vdb_qdrant import create_test_collection, get_collection_items, get_qdrant_collection, index_data_batch, upload_index_test_data

# _log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()

class Query(BaseModel):
    question: str

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/colpali/parse")
def test_docling_parse():
    return {"chunks": "chunks"}

@app.get("/storage/qdrant/collection")
def get_storage_qdrant_collection():
    return get_qdrant_collection()

@app.get("/storage/qdrant/collection/items")
def get_storage_qdrant_collection_items():
    return get_collection_items()

@app.post("/storage/qdrant/collection/create")
def post_storage_qdrant_collection_create():
    create_test_collection()
    return {"result": True}

@app.post("/storage/qdrant/collection/upload_index_test_data")
def post_storage_qdrant_collection_upload_index_test_data():
    index_result = upload_index_test_data()
    return {"result": index_result}

@app.post("/colpali/upload/bulk")
def upload_bulk():
    # TODO: 1. Upload to Qdrant 2. Index the collection
    return {"result": True}

@app.post("/colpali/upload/single")
async def upload_single(file: UploadFile = File(...)):
    # TODO: 1. Convert to Images 2. Upload to Qdrant 3. Index the collection
    file_name = file.filename
    print(f"file_name: {file_name}")
    print(type(file))
    # print(type(await file.read()))
    file_bytes = await file.read()
    print(type(file_bytes))
    file_id = uuid4()
    conversion_result = convert_pdf_to_images(file_bytes, file_id)
    print(f"Conversion Result: {conversion_result}")
    pdf_images_dataset = []
    for page_number, image in enumerate(conversion_result["images"]):
        pdf_data = {
            "file_name": file_name,
            "file_location": conversion_result["output_folder"],
            "uuid4": file_id,
            "image": image,
            "page_number": page_number+1,
        }
        pdf_images_dataset.append(pdf_data)
    print(f"Dataset: {pdf_images_dataset[0]}")
    df = pd.DataFrame(pdf_images_dataset)
    index_data_batch(df, batch_size=2)
    return {
        "filename": file_name,
        "file_id": file_id,
        "image_count": conversion_result["image_count"],
    }
    # return {"result": True}


@app.post("/colpali/query/single/")
def query_single(query: Query):
    print(f"Query: {query}")
    print(query.question)
    row_ids = search_by_text_and_return_images(query.question)
    print(f"Row IDs: {row_ids}")
    results_ds = get_result_ds(row_ids)
    print(f"Results DS: {results_ds}")
    response = []
    for result in results_ds:
        print(result)
        response.append(result["raw_queries"])
    print(type(results_ds))
    # return results_ds
    return {"result": response}