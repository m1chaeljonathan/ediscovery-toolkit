import csv
from pathlib import Path

from config import load_config
from parsers.schema import Document, ParseResult


def parse_csv(filepath: str, field_map: dict = None) -> ParseResult:
    """Parse a generic CSV export. field_map remaps column names to canonical names."""
    path = Path(filepath)
    field_map = field_map or {}
    encodings = load_config()['parsing']['encodings']

    encoding = encodings[0]
    for enc in encodings:
        try:
            with open(path, encoding=enc, errors='strict') as f:
                f.read(4096)
            encoding = enc
            break
        except (UnicodeDecodeError, LookupError):
            continue

    documents = []
    headers = []
    with open(path, encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            mapped = {field_map.get(k, k): v for k, v in row.items()}
            if not headers:
                headers = list(row.keys())
            documents.append(Document(
                begdoc=mapped.get('BEGDOC', '').strip(),
                enddoc=mapped.get('ENDDOC', '').strip(),
                custodian=mapped.get('CUSTODIAN', '').strip(),
                tags=mapped,
                source_row=row_num,
                source_file=path.name,
            ))

    return ParseResult(
        documents=documents,
        headers=headers,
        encoding_detected=encoding,
        row_count=len(documents),
    )
