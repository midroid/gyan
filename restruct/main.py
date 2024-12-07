from typing import Union
import json
import logging
from uuid import uuid4
from io import BytesIO

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import pandas as pd

from docling.datamodel.base_models import DocumentStream
from docling.datamodel.document import ConversionResult
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HierarchicalChunker
from docling_core.types.doc import TableItem, TextItem

from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

from restruct.models import FileParseBody, ParseType
from restruct.parse import docling_parse_export_tables, docling_parse_advanced, get_pictures_from_docling_document

# from src.restruct.parse import docling_parse_test

# _log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


def print_parsed_doc_tree(doc):
    doc.print_element_tree()
    for item, level in doc.iterate_items():
        if isinstance(item, TextItem):
            print(item.text)
        elif isinstance(item, TableItem):
            table_df: pd.DataFrame = item.export_to_dataframe()
            print(table_df.to_markdown())
        elif ...:
            pass

def docling_parse_test():
    conv_res = DocumentConverter().convert("https://arxiv.org/pdf/2206.01062")
    doc = conv_res.document
    
    print_parsed_doc_tree(doc)

    chunks = list(HierarchicalChunker().chunk(doc))
    print(chunks[30])
    # print(json.dumps(chunks, indent=4))
    return doc
    # return chunks


@app.get("/test/docling/parse")
def test_docling_parse():
    chunks = docling_parse_test()
    return {"chunks": chunks}


@app.post("/upload/bulk")
def upload_bulk():
    return {"Hello": "World"}


@app.post("/upload/single")
def upload_single(file: UploadFile = File(...)):
    return {"Hello": "World"}


@app.post("/docling/parse/upload/single")
async def parse_upload_single(file: UploadFile = File(...), parse_type: ParseType = ParseType.all):
    file_name = file.filename
    file_bytes_data = await file.read()
    file_id = uuid4()
    file_parse_body: FileParseBody = {
        "file_name": file_name,
        "file_bytes": file_bytes_data,
        "file_id": file_id,
    }
    parse_resp = docling_parse_advanced(file_parse_body)
    parse_response_value = ""
    parse_response_document =  parse_resp.document
    
    match parse_type.value:
        case ParseType.page:
            parse_response_value = parse_resp.pages
        case ParseType.assembled:
            parse_response_value = parse_resp.assembled
        case ParseType.table:
            parse_response_value = parse_response_document.tables
        case ParseType.pictures:
            parse_response_value = get_pictures_from_docling_document(parse_resp)
        case ParseType.document:
            parse_response_value = parse_response_document
        case ParseType.all:
            parse_response_value = parse_response_document
        case _:
            parse_response_value = parse_response_document

    return {
        "result": True,
        "parse_type": parse_type.value,
        "parse_resp": parse_response_value
    }


@app.post("/docling/parse/single/export/tables")
async def parse_single_export_tables(file: UploadFile = File(...)):
    file_name = file.filename
    file_bytes_data = await file.read()
    file_id = uuid4()
    file_parse_body: FileParseBody = {
        "file_name": file_name,
        "file_bytes": file_bytes_data,
        "file_id": file_id,
    }
    parse_resp = docling_parse_export_tables(file_parse_body)
    return {
        "result": True,
        "parse_resp": parse_resp
    }

@app.post("/docling/parse/upload/bulk")
def parse_upload_bulk():
    return {"Hello": "World"}
