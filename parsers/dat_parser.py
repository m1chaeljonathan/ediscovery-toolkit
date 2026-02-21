import csv
from pathlib import Path

from dateutil import parser as dateparser

from config import load_config
from parsers.schema import Document, ParseResult

CONCORDANCE_DELIMITER = '\x14'   # ASCII 020 — ¶
CONCORDANCE_QUALIFIER = '\xfe'   # ASCII 254 — þ

KNOWN_FIELDS = {
    'BEGDOC', 'ENDDOC', 'BEGATTACH', 'ENDATTACH', 'CUSTODIAN',
    'DATE_SENT', 'DATE_CREATED', 'FILE_EXTENSION', 'MD5_HASH',
    'NATIVE_LINK', 'TEXT_LINK', 'CONFIDENTIALITY', 'PRIVILEGE',
}


def _detect_encoding(filepath: Path) -> str:
    encodings = load_config()['parsing']['encodings']
    for encoding in encodings:
        try:
            with open(filepath, encoding=encoding, errors='strict') as f:
                f.read(4096)
            return encoding
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError(f"Cannot decode {filepath.name} — tried {encodings}")


def _parse_date(value: str):
    if not value or not value.strip():
        return None
    try:
        return dateparser.parse(value.strip()).date()
    except Exception:
        return None


def parse_dat(filepath: str) -> ParseResult:
    path = Path(filepath)
    encoding = _detect_encoding(path)
    documents = []
    errors = []

    with open(path, encoding=encoding) as f:
        reader = csv.DictReader(
            f,
            delimiter=CONCORDANCE_DELIMITER,
            quotechar=CONCORDANCE_QUALIFIER,
        )
        headers = None
        for row_num, row in enumerate(reader, start=2):
            if headers is None:
                headers = list(row.keys())
            try:
                doc = Document(
                    begdoc=row.get('BEGDOC', '').strip(),
                    enddoc=row.get('ENDDOC', '').strip(),
                    begattach=row.get('BEGATTACH', '').strip(),
                    endattach=row.get('ENDATTACH', '').strip(),
                    custodian=row.get('CUSTODIAN', '').strip(),
                    date_sent=_parse_date(row.get('DATE_SENT', '')),
                    date_created=_parse_date(row.get('DATE_CREATED', '')),
                    file_ext=row.get('FILE_EXTENSION', '').strip(),
                    hash_md5=row.get('MD5_HASH', '').strip(),
                    native_path=row.get('NATIVE_LINK', '').strip(),
                    text_path=row.get('TEXT_LINK', '').strip(),
                    confidentiality=row.get('CONFIDENTIALITY', '').strip(),
                    privilege_code=row.get('PRIVILEGE', '').strip(),
                    tags={k: v for k, v in row.items() if k not in KNOWN_FIELDS},
                    source_row=row_num,
                    source_file=path.name,
                )
                documents.append(doc)
            except Exception as e:
                errors.append(f"Row {row_num}: {e}")

    return ParseResult(
        documents=documents,
        headers=headers or [],
        encoding_detected=encoding,
        row_count=len(documents),
        errors=errors,
    )
