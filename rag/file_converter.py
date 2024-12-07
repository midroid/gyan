import os
from io import BytesIO
from uuid import uuid4

from pdf2image import convert_from_bytes


def convert_pdf_to_images(bytes_stream: BytesIO, file_id: uuid4) -> dict:
    output_folder = f"./output/pdf_images/{file_id}"
    os.makedirs(output_folder, exist_ok=True)
    images = convert_from_bytes(
        bytes_stream,
        dpi=300,
        output_folder=output_folder,
        fmt='jpeg'
    )
    return {
        "image_count": len(images),
        "output_folder": output_folder,
        "images": images
    }