from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Document:
    begdoc: str
    enddoc: str
    begattach: str = ""
    endattach: str = ""
    custodian: str = ""
    date_sent: Optional[date] = None
    date_created: Optional[date] = None
    file_ext: str = ""
    hash_md5: str = ""
    native_path: str = ""
    text_path: str = ""
    confidentiality: str = ""
    privilege_code: str = ""
    tags: dict = field(default_factory=dict)
    source_row: int = 0
    source_file: str = ""


@dataclass
class ParseResult:
    documents: list[Document]
    headers: list[str]
    encoding_detected: str
    row_count: int
    errors: list[str] = field(default_factory=list)
