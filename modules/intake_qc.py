import re
from pathlib import Path
from dataclasses import dataclass, asdict

from parsers.dat_parser import parse_dat
from parsers.csv_parser import parse_csv

STANDARD_REQUIRED_FIELDS = ['BEGDOC', 'ENDDOC', 'CUSTODIAN']
ISO_DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}')


@dataclass
class IntakeIssue:
    issue_type: str
    field: str = ""
    doc_id: str = ""
    row: int = 0
    detail: str = ""


def run_intake_qc(filepath: str, required_fields: list[str] = None,
                  output_dir: str = "./reports/output") -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    required_fields = required_fields or STANDARD_REQUIRED_FIELDS
    issues = []

    path = Path(filepath)
    if path.suffix.lower() == '.dat':
        result = parse_dat(filepath)
    else:
        result = parse_csv(filepath)

    docs = result.documents
    headers = result.headers

    # Check required fields present in headers
    for field in required_fields:
        if field not in headers:
            issues.append(IntakeIssue('missing_required_field', field=field,
                detail=f"Required field '{field}' not found in load file headers"))

    seen_begdocs = {}
    for doc in docs:
        # Blank BEGDOC
        if not doc.begdoc:
            issues.append(IntakeIssue('blank_begdoc', row=doc.source_row,
                detail="BEGDOC is blank"))

        # Duplicate BEGDOC
        if doc.begdoc in seen_begdocs:
            issues.append(IntakeIssue('duplicate_begdoc', doc_id=doc.begdoc,
                row=doc.source_row,
                detail=f"Duplicate of row {seen_begdocs[doc.begdoc]}"))
        else:
            seen_begdocs[doc.begdoc] = doc.source_row

        # ISO date format detection (Purview export flag)
        for date_val in [doc.tags.get('DATE_SENT', ''), doc.tags.get('DATE_CREATED', '')]:
            if date_val and ISO_DATE_PATTERN.match(date_val):
                issues.append(IntakeIssue('iso_date_format', doc_id=doc.begdoc,
                    row=doc.source_row,
                    detail=f"ISO 8601 date '{date_val}' — may need conversion for Relativity ingestion"))
                break

    stats = {
        'total_documents': result.row_count,
        'encoding_detected': result.encoding_detected,
        'total_issues': len(issues),
        'passed': len(issues) == 0,
    }

    return {'issues': [asdict(i) for i in issues], 'stats': stats,
            'headers_received': headers}
