from typing import Union
import json
import logging
from uuid import uuid4
from io import BytesIO
import base64

from fastapi import FastAPI, File, Response, UploadFile
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
from restruct.parse import docling_parse_export_tables, docling_parse_advanced, get_parser_response_by_type, get_pictures_from_docling_document, plot_page_layout

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
    """
    Upload bulk of files to storage which can be later consumed in batch processing.

    Returns:
        success: True if the upload is successful
    """
    # TODO: Implement Bulk Upload Only
    return {"Result": "NOT IMPLEMENTED"}


@app.post("/upload/single")
def upload_single(file: UploadFile = File(...)):
    """
    Upload a file to storage which can be later consumed in batch processing.

    Returns:
        success: True if the upload is successful
    """
    # TODO: Implement Single Upload Only
    return {"Result": "NOT IMPLEMENTED"}


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
    parse_response_value = get_parser_response_by_type(parse_type, parse_resp)

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


@app.post("/docling/parse/plot")
async def parse_plot(file: UploadFile = File(...)):
    file_name = file.filename
    file_bytes_data = await file.read()
    file_id = uuid4()
    file_parse_body: FileParseBody = {
        "file_name": file_name,
        "file_bytes": file_bytes_data,
        "file_id": file_id,
    }
    conv_res = docling_parse_advanced(file_parse_body)

    # Save page images
    for page_no, page in conv_res.document.pages.items():
        # page_image = page.export_to_image()
        page_image = page.image
        # print(page_image)
        page_image_pil = page.image.pil_image
        print(page_image_pil)
        # page_image.save()
        page_image_filename = f"./page_{page_no}.png"
        bytes_io = BytesIO()
        with open(page_image_filename, "wb") as fp:
            page.image.pil_image.save(fp, format="PNG")
            page_image_pil.save(bytes_io, format="PNG")

    print(type(page_image_pil))
    print(dir(page_image_pil))
    # page_image_pil.show()

    plotted_image_bytes = plot_page_layout(conv_res, 1)

    # page_image_pil_uri = page_image_pil.to_uri()
    page_image_pil_base64 = base64.b64encode(bytes_io.getbuffer()).decode('utf-8')
    page_image_uri = f"data:image/png;base64,{page_image_pil_base64}"
    print(page_image_uri)
    # page_image_markdown = f"![page_image_md]({page_image_uri})"

    # return {
    #     "result": True,
    #     "image_location": f"page_{page_no}.png",
    #     "page_image": page_image_uri,
    #     "page_image_markdown": page_image_markdown
    # }

    # Generate your image here (e.g., using PIL)
    # img_byte_arr = BytesIO()
    # Save your generated image to img_byte_arr
    plotted_image_bytes.seek(0)
    return Response(content=plotted_image_bytes.getvalue(), media_type="image/png")


@app.post("/docling/parse/upload/bulk")
def parse_upload_bulk():
    # TODO: Implement Bulk API
    return {"Response": "NOT IMPLEMENTED"}
