from io import BytesIO
import pandas as pd

from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.transforms.chunker import HierarchicalChunker
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling_core.types.doc import TableItem, TextItem, ImageRefMode, PictureItem
from docling.datamodel.document import ConversionResult

from PIL import Image, ImageDraw

from restruct.models import FileParseBody, ParseType

IMAGE_RESOLUTION_SCALE = 2.0

# {
#   "text": "Lately, new types of ML models for document-layout analysis have emerged [...]",
#   "meta": {
#     "doc_items": [{
#       "self_ref": "#/texts/40",
#       "label": "text",
#       "prov": [{
#         "page_no": 2,
#         "bbox": {"l": 317.06, "t": 325.81, "r": 559.18, "b": 239.97, ...},
#       }]
#     }],
#     "headings": ["2 RELATED WORK"],
#   }
# }

def get_document_converter():
    pipeline_options = PdfPipelineOptions(do_table_structure=True)
    # OCR options
    # pipeline_options.do_ocr = True
    # pipeline_options.ocr_options.force_full_page_ocr = True
    # OCR if not properly configured, results in garbled text

    # Image Options
    # pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True

    pipeline_options.table_structure_options.do_cell_matching = True  # uses text cells predicted from table structure model
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE  # use more accurate TableFormer model

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    return doc_converter

def docling_parse(pdf_stream: BytesIO) -> dict:
    buf = BytesIO(pdf_stream)
    source = DocumentStream(name="my_doc.pdf", stream=buf)
    converter = DocumentConverter()
    result = converter.convert(source)
    doc = result.document
    chunks = list(HierarchicalChunker().chunk(doc))
    print(chunks[30])
    return chunks

def docling_parse_test():
    conv_res = DocumentConverter().convert("https://arxiv.org/pdf/2206.01062")
    doc = conv_res.document
    chunks = list(HierarchicalChunker().chunk(doc))
    print(chunks[30])

def get_docling_parse_converter_result(doc_converter, file_parse_body: FileParseBody):
    file_bytes = file_parse_body["file_bytes"]
    buf = BytesIO(file_bytes)
    source = DocumentStream(name=file_parse_body["file_name"], stream=buf)
    print(f"source: {source}")
    conv_res = doc_converter.convert(source)
    return conv_res

def docling_parse_advanced(file_parse_body: FileParseBody):
    doc_converter = get_document_converter()
    conv_result = get_docling_parse_converter_result(doc_converter, file_parse_body)
    ## Inspect the converted document:
    # conv_result.document.print_element_tree()
    return conv_result

def get_tables_from_docling_document(conv_result: ConversionResult, table_output_format="markdown"):
    tables_extracted = []
    # Export tables
    for table_ix, table in enumerate(conv_result.document.tables):
        table_df: pd.DataFrame = table.export_to_dataframe()
        print(f"## Table {table_ix}")
        print(table_df.to_markdown())
        if table_output_format == "markdown":
            tables_extracted.append(table_df.to_markdown())
        elif table_output_format == "json":
            tables_extracted.append(table_df.to_json)
        elif table_output_format == "csv":
            tables_extracted.append(table_df.to_csv(index=False))

    return tables_extracted

def get_pictures_from_docling_document(conv_result: ConversionResult):
    # for picture in conv_result.document.pictures:
    #     print(dir(picture))
    #     # print(picture.export_to_markdown(conv_result.document))
    # for element, _level in conv_result.document.iterate_items():
    #     if isinstance(element, PictureItem):
    #         # element.get_image(conv_result.document).save(, "PNG")
    #         print(element.get_image(conv_result.document))

    return conv_result.document.pictures

def get_parser_response_by_type(parse_type: ParseType, conv_result: ConversionResult):
    conv_result_document = conv_result.document
    parse_response_value = ""
    match parse_type.value:
        case ParseType.page:
            parse_response_value = conv_result.pages
        case ParseType.assembled:
            parse_response_value = conv_result.assembled
        case ParseType.table:
            parse_response_value = conv_result_document.tables
        case ParseType.pictures:
            parse_response_value = get_pictures_from_docling_document(conv_result)
        case ParseType.document:
            parse_response_value = conv_result_document
        case ParseType.all:
            parse_response_value = conv_result_document
        case _:
            parse_response_value = conv_result_document

    return parse_response_value

def docling_parse_export_tables(file_parse_body: FileParseBody):
    doc_converter = get_document_converter()
    conv_res = get_docling_parse_converter_result(doc_converter, file_parse_body)
    tables_md = get_tables_from_docling_document(conv_result=conv_res)
    return tables_md


def draw_plot(image, bbox):
    draw = ImageDraw.Draw(image)

    # Define rectangle coordinates (x0, y0, x1, y1)
    # rectangle_coords = (100, 100, 300, 300)
    # rectangle_coords = (bbox["l"], bbox["t"], bbox["r"], bbox["b"])
    rectangle_coords = bbox
    draw.rectangle(rectangle_coords, outline='red', width=3)
    return image


def plot_page_layout(conv_res: ConversionResult, page_no: int) -> BytesIO:
    target_page = None
    page_layout_cluster = []
    for page in conv_res.pages:
        if page.page_no == page_no - 1:
            target_page = page
            page_layout_cluster = page.predictions.layout.clusters
            break

    page = conv_res.document.pages[1]
    # Save page images
    # for page_no, page in conv_res.document.pages.items():
        # page_image = page.export_to_image()
    page_image = page.image
    # print(page_image)
    page_image_pil = page.image.pil_image
    print(page_image_pil)
    # page_image.save()
    page_image_filename = f"./plot_page_{page_no}.png"


    # plot page layout
    for layout_element in page_layout_cluster:
        label = layout_element.label
        bbox = layout_element.bbox.as_tuple()
        print({
            "label": label,
            "bbox": bbox
        })
        page_image_pil = draw_plot(page_image_pil, bbox)

    bytes_io = BytesIO()
    with open(page_image_filename, "wb") as fp:
        page.image.pil_image.save(fp, format="PNG")
        page_image_pil.save(bytes_io, format="PNG")

    return bytes_io
