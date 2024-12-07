from enum import Enum
from pydantic import BaseModel


class FileParseBody(BaseModel):
    file_name: str
    file_bytes: bytes
    file_id: str


# Define parse type with Enum values page, ensemble, and table etc
class ParseType(str, Enum):
    page = "page"
    assembled = "assembled"
    table = "table"
    pictures = "pictures"
    document = "document"
    all = "all"